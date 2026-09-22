#!/usr/bin/env python3
"""Fail-closed post-capture check of a capture-v0 bundle's PDFs.

For every record in `manifest.json` the held file must exist, start with
`%PDF-`, hash to the declared SHA-256 and byte size, name the bundle's case on
page 1, and carry a page-1 classification the project may hold: `Public`,
`Publike`/`Publik`, or a non-public stamp accompanied by the court's own
"Reclassified as Public" stamp. Anything else is reported as FLAGGED so the
collector can quarantine it before the bundle is compared or imported. No
network, no database.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from ksc_ingestion.capture_import import pdf_header_references

PUBLIC_STAMPS = {"Public", "Publike", "Publik"}
# Markings the court prints when a document is not public (English / Albanian).
_NON_PUBLIC_RE = re.compile(
    r"strictly\s+confidential|confidential|ex\s+parte|rrept[ëe]sisht|konfidencial", re.IGNORECASE
)
# A stamp the court adds when it makes such a document public.
_MADE_PUBLIC_RE = re.compile(
    r"\bPUBLIC\b\s*(?:Reclassified as Public|As per instruction|Pursuant to|Per instruction)[^.]{0,160}",
    re.IGNORECASE,
)
_PUBLIC_STAMP_RE = re.compile(r"\bPUBLIC\b|\bPublic\b|\bPublike\b|\bPublik\b")
_OPEN_SESSION_RE = re.compile(
    r"open\s+session|seanc[ëe]\s+e\s+hapur|javna\s+sednica", re.IGNORECASE
)


def page1_text(data: bytes) -> str:
    try:
        return " ".join(
            (PdfReader(io.BytesIO(data), strict=False).pages[0].extract_text() or "").split()
        )
    except Exception:  # noqa: BLE001 - any unreadable page fails closed below
        return ""


def visibility_verdict(
    record: dict[str, Any], header: Any, text: str
) -> tuple[str | None, list[str]]:
    """Return (evidence, problems). Empty problems means the page-1 markings show a
    public record: a Public classification line; a non-public line or marking
    followed by the court's own made-public stamp; a bare PUBLIC stamp with no
    non-public marking; or, for transcripts, an open-session heading."""
    if header.classification in PUBLIC_STAMPS:
        return header.classification, []
    if header.classification is not None:
        note = header.reclassification_note or (
            m.group(0) if (m := _MADE_PUBLIC_RE.search(text)) else None
        )
        if note:
            return f"{header.classification} → {note}", []
        return header.classification, [
            f"page-1 classification {header.classification!r} without a made-public stamp"
        ]
    if (record.get("record_type") or "").lower() == "transcript":
        if _OPEN_SESSION_RE.search(text):
            return "transcript: open session heading", []
        return None, ["transcript page 1 has no open-session heading"]
    non_public = _NON_PUBLIC_RE.search(text)
    made_public = _MADE_PUBLIC_RE.search(text)
    if non_public and header.reclassification_note:
        return f"{non_public.group(0)} → {header.reclassification_note}", []
    if non_public and made_public and made_public.start() > non_public.start():
        return f"{non_public.group(0)} → {made_public.group(0)}", []
    if non_public:
        return non_public.group(0), [
            f"page-1 marking {non_public.group(0)!r} without a made-public stamp"
        ]
    if _PUBLIC_STAMP_RE.search(text):
        return "PUBLIC stamp", []
    return None, ["no classification stamp on page 1"]


def check(root: Path) -> dict[str, Any]:
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "bundle" not in manifest and (root / "source_manifest.json").is_file():
        # An imported project bundle keeps the capture-v0 manifest beside it.
        manifest = json.loads((root / "source_manifest.json").read_text(encoding="utf-8"))
    case = manifest["bundle"]["case_number"]
    rows = []
    for record in manifest["records"]:
        rid = record["record_id"]
        path = root / record["local_file"]
        if not path.is_file() and (root / "files" / f"{rid}.pdf").is_file():
            path = root / "files" / f"{rid}.pdf"
        problems: list[str] = []
        classification = reclassified = None
        header_refs: list[str] = []
        if not path.is_file():
            problems.append("file missing")
        else:
            data = path.read_bytes()
            if data[:5] != b"%PDF-":
                problems.append("not a PDF (magic bytes)")
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                problems.append("sha256 differs from manifest")
            if len(data) != record["bytes"]:
                problems.append("byte size differs from manifest")
            if not problems:
                header = pdf_header_references(data, case)
                classification = header.classification
                reclassified = header.reclassification_note
                header_refs = list(header.refs)
                if header.pages < 1:
                    problems.append("no pages")
                evidence, visibility_problems = visibility_verdict(record, header, page1_text(data))
                problems.extend(visibility_problems)
                classification = evidence
                if header_refs and not any(ref.startswith(case) for ref in header_refs):
                    problems.append(f"page-1 references name another case: {header_refs[:2]}")
        rows.append(
            {
                "record_id": rid,
                "document_id": record.get("document_id"),
                "classification": classification,
                "reclassification_note": reclassified,
                "header_refs": header_refs[:3],
                "status": "FLAGGED" if problems else "OK",
                "problems": problems,
            }
        )
    return {
        "case_number": case,
        "checked": len(rows),
        "flagged": [r for r in rows if r["problems"]],
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("bundle", type=Path, help="capture-v0 bundle directory")
    parser.add_argument("--json", type=Path, help="write the full report here")
    args = parser.parse_args()
    report = check(args.bundle)
    for row in report["rows"]:
        note = (
            f" — reclassified: {row['reclassification_note']}"
            if row["reclassification_note"]
            else ""
        )
        flag = "  !! " + "; ".join(row["problems"]) if row["problems"] else ""
        print(f"  {row['record_id']} {row['status']:7} {row['classification']!s:28}{note}{flag}")
    print(f"checked={report['checked']} flagged={len(report['flagged'])}")
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if report["flagged"] else 0


if __name__ == "__main__":
    sys.exit(main())
