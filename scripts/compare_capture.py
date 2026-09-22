#!/usr/bin/env python3
"""Compare an operator capture (format v0 manifest) against the tracked corpus.

Runs before `ksc-ingest import-capture`, needs no PDFs, no database and no
network. It answers the pre-ingestion questions of the Phase 13 acquisition
protocol: which selected records are already held, which are language or
redaction/correction counterparts of a held filing, and which are new filings.
Identity is compared on official repository `doc_id`, SHA-256 and the published
filing id only; titles are never used for matching.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

DEFAULT_CORPUS = Path("docs/ingestion/manifests/phase7-controlled-corpus.json")
_FILING_RE = re.compile(r"^(?:(?P<ia>IA\d{3})-)?(?P<filing>F\d{5})(?P<suffix>[A-Z0-9]*)$")
_OFFICIAL_HOSTS = ("repository.scp-ks.org", "www.scp-ks.org")


def _doc_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname not in _OFFICIAL_HOSTS:
        return None
    values = parse_qs(parsed.query).get("doc_id")
    return values[0] if values else None


def _filing_key(document_id: str | None) -> str | None:
    """`F03668RED2` → `F03668`; `IA012-F00005` → `IA012-F00005`; else None."""
    if not document_id:
        return None
    m = _FILING_RE.match(document_id.strip().upper())
    if m is None:
        return None
    return f"{m['ia']}-{m['filing']}" if m["ia"] else m["filing"]


def _load_corpus(path: Path) -> dict[str, set[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    known: dict[str, set[str]] = {
        "doc_id": set(),
        "sha256": set(),
        "version": set(),
        "filing": set(),
    }
    for record in data["records"]:
        known["doc_id"].add(record["external_record_id"])
        known["sha256"].add(record["sha256"])
        known["version"].add(record["official_version_ref"])
        key = _filing_key(record.get("published_document_id"))
        if key:
            known["filing"].add(key)
    return known


def compare(capture: dict[str, Any], known: dict[str, set[str]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    seen_doc: dict[str, str] = {}
    seen_sha: dict[str, str] = {}
    for record in capture["records"]:
        rid = record.get("record_id", "?")
        doc_id = _doc_id(record.get("detail_page_url", ""))
        sha = (record.get("sha256") or "").lower() or None
        filing = _filing_key(record.get("document_id"))
        problems: list[str] = []
        if doc_id is None:
            problems.append("detail_page_url is not an official repository detail URL")
        if record.get("public_status", "").lower().startswith(("conf", "strict", "ex")):
            problems.append("not public: must not be captured")
        if doc_id and doc_id in seen_doc:
            problems.append(f"same doc_id as {seen_doc[doc_id]} inside this capture")
        if sha and sha in seen_sha:
            problems.append(f"same sha256 as {seen_sha[sha]} inside this capture")
        if doc_id:
            seen_doc.setdefault(doc_id, rid)
        if sha:
            seen_sha.setdefault(sha, rid)

        if (doc_id and doc_id in known["doc_id"]) or (sha and sha in known["sha256"]):
            status = "duplicate"
        elif filing and filing in known["filing"]:
            status = "counterpart"  # new language/redaction/correction version of a held filing
        elif filing:
            status = "new"
        else:
            status = "new_unnumbered"  # transcripts and other records without a filing id
        rows.append(
            {
                "record_id": rid,
                "document_id": record.get("document_id"),
                "language": (record.get("language") or {}).get("code")
                if isinstance(record.get("language"), dict)
                else record.get("language"),
                "record_type": record.get("record_type"),
                "public_status": record.get("public_status"),
                "doc_id": doc_id,
                "sha256_present": bool(sha),
                "status": status,
                "problems": problems,
            }
        )

    # Language/version pairs inside the capture: same filing key, >1 record.
    by_filing: dict[str, list[str]] = {}
    for record, row in zip(capture["records"], rows, strict=True):
        key = _filing_key(record.get("document_id"))
        if key:
            by_filing.setdefault(key, []).append(row["record_id"])
    pairs = {key: ids for key, ids in by_filing.items() if len(ids) > 1}

    counts = Counter(row["status"] for row in rows)
    unique_new_filings = {
        _filing_key(r.get("document_id"))
        for r, row in zip(capture["records"], rows, strict=True)
        if row["status"] == "new"
    }
    return {
        "total_selected": len(rows),
        "duplicates_against_corpus": counts["duplicate"],
        "counterparts_of_held_filings": counts["counterpart"],
        "new_records": counts["new"] + counts["new_unnumbered"],
        "unique_new_filing_numbers": len(unique_new_filings),
        "unnumbered_new_records": counts["new_unnumbered"],
        "language_version_pairs_in_capture": pairs,
        "hashes_recorded": sum(row["sha256_present"] for row in rows),
        "records_with_problems": [row for row in rows if row["problems"]],
        "type_coverage": dict(Counter(f"{row['record_type']}" for row in rows)),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("manifest", type=Path, help="capture-v0 manifest.json")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--json", type=Path, help="write the full comparison here")
    args = parser.parse_args()

    capture = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = compare(capture, _load_corpus(args.corpus))
    for row in report["rows"]:
        flag = "  !! " + "; ".join(row["problems"]) if row["problems"] else ""
        print(
            f"  {row['record_id']} {row['status']:14} {row['document_id']!s:16} "
            f"{row['language']!s:4} {row['record_type']}{flag}"
        )
    print(
        f"selected={report['total_selected']} duplicates={report['duplicates_against_corpus']} "
        f"counterparts={report['counterparts_of_held_filings']} new={report['new_records']} "
        f"unique_new_filings={report['unique_new_filing_numbers']} "
        f"hashes={report['hashes_recorded']} problems={len(report['records_with_problems'])}"
    )
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if report["records_with_problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
