#!/usr/bin/env python3
"""Download public KSC records from the Legal Tools Database mirror (ADR-030).

Produces capture-v0 bundles — the same format the browser collector writes —
so the rest of the path is unchanged:

    check_capture_pdfs (run here, flagged records quarantined)
      → ksc-ingest import-capture → bundle → parse → reresolve → …

Only the mirror is contacted: its search API (legal-tools.org, paced to its
robots.txt crawl-delay) and the object store its PDFs live in. The official
site is never requested. Records already held (by official URL or SHA-256) are
skipped. Everything is resumable: PDFs are cached by mirror slug and a re-run
only downloads what is missing.

    .venv/bin/python scripts/ksc_legal_tools_harvest.py \\
        --permission "CILRAP written permission, <date>" --inventory-only
    .venv/bin/python scripts/ksc_legal_tools_harvest.py \\
        --permission "CILRAP written permission, <date>" [--limit 20]

Output (default ~/Downloads/ksc-bc-2020-06-legal-tools/):

    inventory.json        every mirror hit for the case (API responses, trimmed)
    plan.json             selected / skipped records with reasons
    _pdfs/<slug>.pdf      download cache
    <bundle-id>/          capture-v0 bundles of at most 99 records
    summary.json          what happened
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import robotparser
from urllib.parse import urlsplit

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_capture_pdfs import check, page1_text  # type: ignore[import-not-found]  # noqa: E402
from ksc_ingestion import legal_tools as lt  # noqa: E402
from ksc_ingestion.fetch import (  # noqa: E402
    DEFAULT_USER_AGENT,
    AccessControlBlockedError,
    FetchError,
    looks_like_challenge,
)

BATCH_LIMIT = 99  # capture-v0 record ids are r01…r99
_ENGLISH_STAMPS = {"Public"}
_ALBANIAN_STAMPS = {"Publike", "Publik"}


def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


class MirrorClient:
    """Identified, paced client for the mirror hosts only. A challenge or a
    robots refusal stops the run; nothing is retried with other headers."""

    def __init__(self, *, api_interval: float, pdf_interval: float) -> None:
        self.intervals = {"legal-tools.org": api_interval, "www.legal-tools.org": api_interval}
        self.default_interval = pdf_interval
        self.last: dict[str, float] = {}
        self.client = httpx.Client(
            headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=120, follow_redirects=False
        )
        self.robots = self._robots()

    def _robots(self) -> robotparser.RobotFileParser:
        response = self._get("https://legal-tools.org/robots.txt")
        parser = robotparser.RobotFileParser()
        if response.status_code == 200:
            parser.parse(response.text.splitlines())
        elif response.status_code == 404:
            parser.parse([])
        else:
            raise AccessControlBlockedError(
                "https://legal-tools.org/robots.txt", f"HTTP {response.status_code}"
            )
        delay = parser.crawl_delay(DEFAULT_USER_AGENT)
        if delay:
            for host in self.intervals:
                self.intervals[host] = max(self.intervals[host], float(delay))
        return parser

    def _get(self, url: str, params: dict[str, str] | None = None) -> httpx.Response:
        lt.require_mirror(url)
        host = (urlsplit(url).hostname or "").lower()
        wait = self.intervals.get(host, self.default_interval) - (
            time.monotonic() - self.last.get(host, -1e9)
        )
        if wait > 0:
            time.sleep(wait)
        self.last[host] = time.monotonic()
        try:
            response = self.client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise FetchError(f"{type(exc).__name__} fetching {url}") from exc
        evidence = looks_like_challenge(response.status_code, response.headers, response.content)
        if evidence:
            raise AccessControlBlockedError(url, evidence)
        return response

    def get(self, url: str, params: dict[str, str] | None = None) -> httpx.Response:
        if urlsplit(url).hostname in self.intervals and not self.robots.can_fetch(
            DEFAULT_USER_AGENT, url
        ):
            raise FetchError(f"robots.txt disallows {url}")
        for attempt in range(3):
            response = self._get(url, params)
            if response.status_code < 500:
                return response
            log(f"HTTP {response.status_code} from {url}; retry {attempt + 1}/2")
            time.sleep(30)
        return response

    def close(self) -> None:
        self.client.close()


# ------------------------------------------------------------- inventory --
def fetch_inventory(client: MirrorClient, case: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    total = None
    while total is None or len(hits) < total:
        filt = {"where": {"caseNumber": case}, "from": len(hits), "limit": lt.PAGE_SIZE}
        response = client.get(lt.SEARCH_URL, {"filter": json.dumps(filt)})
        if response.status_code != 200:
            raise FetchError(f"search HTTP {response.status_code}")
        data = response.json()
        page = [r.get("hit", r) for r in data.get("results", [])]
        total = int(data.get("total", 0))
        if not page:
            break
        hits.extend(page)
        log(f"inventory {len(hits)}/{total}")
    return hits


def held_from_manifests(paths: list[Path]) -> tuple[set[str], set[str]]:
    """Official artifact URLs and SHA-256s of everything already captured."""

    urls: set[str] = set()
    shas: set[str] = set()
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for record in data.get("records", []) if isinstance(data, dict) else []:
            for artifact in record.get("artifacts", []) or [record]:
                url = artifact.get("url") or artifact.get("artifact_url") or artifact.get("pdf_url")
                if url:
                    urls.add(url)
                if artifact.get("sha256"):
                    shas.add(artifact["sha256"])
    return urls, shas


# -------------------------------------------------------------- download --
def download(
    client: MirrorClient, record: lt.MirrorRecord, cache: Path
) -> tuple[Path, str, int] | str:
    """(path, sha256, size) of the cached PDF, or a failure reason."""

    path = cache / f"{record.slug}.pdf"
    if not path.is_file():
        response = client.get(record.pdf_url)
        if response.status_code != 200:
            return f"mirror PDF HTTP {response.status_code}"
        if not response.content.startswith(b"%PDF-"):
            return "mirror file is not a PDF"
        tmp = path.with_suffix(".part")
        tmp.write_bytes(response.content)
        tmp.replace(path)
    data = path.read_bytes()
    return path, hashlib.sha256(data).hexdigest(), len(data)


# ---------------------------------------------------------------- bundle --
def write_bundle(
    out: Path,
    bundle_id: str,
    entries: list[tuple[dict[str, Any], Path]],
    args: argparse.Namespace,
) -> Path:
    root = out / bundle_id
    if root.exists():
        shutil.rmtree(root)
    (root / "files").mkdir(parents=True)
    (root / "pages").mkdir()
    sums = []
    for entry, pdf in entries:
        shutil.copy2(pdf, root / entry["local_file"])
        (root / entry["local_page_snapshot"]).write_text(lt.snapshot_html(entry), encoding="utf-8")
        sums.append(f"{entry['sha256']}  {entry['local_file']}")
    _write_manifest(root, bundle_id, [e for e, _ in entries], args)
    (root / "files" / "sha256sums.txt").write_text("\n".join(sums) + "\n")
    (root / "CAPTURE_NOTES.md").write_text(
        f"# {bundle_id}\n\nDownloaded from the {lt.MIRROR_NAME} (https://www.legal-tools.org) "
        f"by scripts/ksc_legal_tools_harvest.py under ADR-030.\n\nPermission: {args.permission}\n\n"
        "Each record keeps its Legal Tools PURL (`mirror.purl`) for attribution and the official "
        "repository URL the mirror recorded. Public status is decided by the PDF's page-1 "
        "markings (scripts/check_capture_pdfs.py), not by the mirror.\n",
        encoding="utf-8",
    )
    return root


def _write_manifest(
    root: Path, bundle_id: str, records: list[dict[str, Any]], args: argparse.Namespace
) -> None:
    manifest = {
        "bundle": {
            "name": f"ksc-bc-2020-06-{bundle_id}",
            "project": "KSC Public Record Intelligence",
            "phase": "ADR-030 Legal Tools mirror acquisition",
            "bundle_id": bundle_id,
            "case_number": args.case,
            "capture_date": datetime.now(UTC).date().isoformat(),
            "captured_by": args.captured_by,
            "capture_method": (
                f"Downloaded from the {lt.MIRROR_NAME} public API and object store by an "
                "identified, paced client (scripts/ksc_legal_tools_harvest.py), with written "
                "CILRAP permission. The official site was not contacted; official URLs are as "
                "the mirror recorded them."
            ),
            "fetch_method": lt.FETCH_METHOD,
            "permission": args.permission,
            "sources": ["https://www.legal-tools.org/"],
            "record_count": len(records),
        },
        "records": records,
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def quarantine(root: Path, args: argparse.Namespace) -> tuple[int, list[dict[str, Any]]]:
    """Page-1 stamp check plus a language check (the page-1 classification
    line is English or Albanian wording); flagged records leave the bundle."""

    report = check(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    by_id = {r["record_id"]: r for r in manifest["records"]}
    flagged = {row["record_id"]: row for row in report["flagged"]}
    for row in report["rows"]:
        stamp = row["classification"]
        lang = by_id[row["record_id"]]["language"]["code"]
        if (lang == "eng" and stamp in _ALBANIAN_STAMPS) or (
            lang == "sqi" and stamp in _ENGLISH_STAMPS
        ):
            flagged.setdefault(row["record_id"], {**row, "problems": []})["problems"].append(
                f"page-1 classification {stamp!r} contradicts mirror language {lang!r}"
            )
        record = by_id[row["record_id"]]
        if record["record_type"].lower() == "transcript":
            text = page1_text((root / record["local_file"]).read_bytes())
            if lt.looks_serbian(f"{record['title']} {text}"):
                flagged.setdefault(row["record_id"], {**row, "problems": []})["problems"].append(
                    "Serbian transcript content is outside the EN/SQ acquisition scope"
                )
    if flagged:
        qdir = root / "quarantine"
        qdir.mkdir(exist_ok=True)
        for rid in flagged:
            for sub, ext in (("files", "pdf"), ("pages", "html")):
                src = root / sub / f"{rid}.{ext}"
                if src.exists():
                    src.rename(qdir / f"{rid}.{sub}.{ext}")
        (qdir / "flagged.json").write_text(
            json.dumps(list(flagged.values()), indent=2, ensure_ascii=False) + "\n"
        )
        kept = [r for r in manifest["records"] if r["record_id"] not in flagged]
        _write_manifest(root, manifest["bundle"]["bundle_id"], kept, args)
        (root / "files" / "sha256sums.txt").write_text(
            "".join(f"{r['sha256']}  {r['local_file']}\n" for r in kept)
        )
    (root / "pdf_check.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report["checked"], list(flagged.values())


# ------------------------------------------------------------------ main --
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case", default="KSC-BC-2020-06")
    parser.add_argument(
        "--out", type=Path, default=Path.home() / "Downloads" / "ksc-bc-2020-06-legal-tools"
    )
    parser.add_argument("--bundle-prefix", default=f"{datetime.now().date().isoformat()}-ltd")
    parser.add_argument(
        "--held",
        type=Path,
        action="append",
        help="manifest(s) of records already held (default: data/captures/*/manifest.json)",
    )
    parser.add_argument("--permission", required=True, help="the written CILRAP permission, cited")
    parser.add_argument("--captured-by", default="Shefqet Salihu")
    parser.add_argument("--limit", type=int, help="download at most N new records")
    parser.add_argument(
        "--pilot-size",
        type=int,
        help="deterministically select a stratified filing pilot of this size",
    )
    parser.add_argument("--batch-size", type=int, default=BATCH_LIMIT)
    parser.add_argument("--api-interval", type=float, default=10.0)
    parser.add_argument("--pdf-interval", type=float, default=3.0)
    parser.add_argument("--inventory-only", action="store_true", help="list and plan; no PDFs")
    parser.add_argument("--reuse-inventory", action="store_true")
    args = parser.parse_args()
    if args.limit and args.pilot_size:
        parser.error("--limit and --pilot-size are mutually exclusive")
    if not 1 <= args.batch_size <= BATCH_LIMIT:
        parser.error(f"--batch-size must be 1..{BATCH_LIMIT}")

    out: Path = args.out.expanduser()
    cache = out / "_pdfs"
    cache.mkdir(parents=True, exist_ok=True)
    client = MirrorClient(api_interval=args.api_interval, pdf_interval=args.pdf_interval)
    try:
        inventory_path = out / "inventory.json"
        if args.reuse_inventory and inventory_path.is_file():
            hits = json.loads(inventory_path.read_text(encoding="utf-8"))
        else:
            hits = fetch_inventory(client, args.case)
            inventory_path.write_text(json.dumps(hits, ensure_ascii=False) + "\n", encoding="utf-8")

        held_paths = args.held or sorted((ROOT / "data" / "captures").glob("*/manifest.json"))
        held_urls, held_shas = held_from_manifests(held_paths)
        planned = lt.plan(hits, case_number=args.case, held_official_urls=held_urls)
        pilot = lt.select_pilot(planned.selected, size=args.pilot_size) if args.pilot_size else []
        skip_counts = Counter(s.reason for s in planned.skipped)
        (out / "plan.json").write_text(
            json.dumps(
                {
                    "mirror_hits": len(hits),
                    "held_manifests": [str(p) for p in held_paths],
                    "selected": [
                        {
                            "slug": r.slug,
                            "external_id": r.external_id,
                            "title": r.title,
                            "language": r.language_code,
                            "official_url": r.official_url,
                        }
                        for r in planned.selected
                    ],
                    "skipped_counts": dict(skip_counts),
                    "skipped": [s.__dict__ for s in planned.skipped],
                    "pilot": [
                        {
                            "slug": r.slug,
                            "external_id": r.external_id,
                            "title": r.title,
                            "language": r.language_code,
                            "category": lt.pilot_category(r),
                            "official_url": r.official_url,
                        }
                        for r in pilot
                    ],
                    "pilot_distribution": {
                        "categories": dict(Counter(lt.pilot_category(r) for r in pilot)),
                        "languages": dict(Counter(r.language_code for r in pilot)),
                    },
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        log(
            f"mirror hits {len(hits)}; selected {len(planned.selected)}; skipped {dict(skip_counts)}"
        )
        if args.inventory_only:
            return 0

        entries: list[tuple[dict[str, Any], Path]] = []
        failures: list[dict[str, str]] = []
        seen_shas = set(held_shas)
        todo = pilot or (planned.selected[: args.limit] if args.limit else planned.selected)
        for index, record in enumerate(todo, 1):
            result = download(client, record, cache)
            if isinstance(result, str):
                failures.append({"slug": record.slug, "title": record.title, "why": result})
                continue
            path, digest, size = result
            if digest in seen_shas:
                failures.append(
                    {
                        "slug": record.slug,
                        "title": record.title,
                        "why": "already held or duplicate (sha256)",
                    }
                )
                continue
            seen_shas.add(digest)
            slot = len(entries) % args.batch_size + 1
            try:
                entry = lt.source_entry(
                    record,
                    record_id=f"r{slot:02d}",
                    sha256=digest,
                    byte_size=size,
                    permission=args.permission,
                )
            except lt.MirrorError as exc:
                failures.append({"slug": record.slug, "title": record.title, "why": str(exc)})
                continue
            entries.append((entry, path))
            if index % 25 == 0:
                log(f"downloaded {index}/{len(todo)}")

        bundles = []
        for n, start in enumerate(range(0, len(entries), args.batch_size), 1):
            bundle_id = f"{args.bundle_prefix}-{n:02d}"
            root = write_bundle(out, bundle_id, entries[start : start + args.batch_size], args)
            checked, flagged = quarantine(root, args)
            bundles.append(
                {
                    "bundle_id": bundle_id,
                    "path": str(root),
                    "checked": checked,
                    "quarantined": len(flagged),
                }
            )
            log(f"{bundle_id}: {checked} records, {len(flagged)} quarantined")
        summary = {
            "finished_at": datetime.now(UTC).isoformat(),
            "mirror_hits": len(hits),
            "selected": len(planned.selected),
            "attempted": len(todo),
            "bundled": len(entries),
            "failures": failures,
            "bundles": bundles,
        }
        (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
        log(f"bundled {len(entries)} in {len(bundles)} bundle(s); {len(failures)} not taken")
        return 0
    except AccessControlBlockedError as exc:
        log(f"STOPPED — access control: {exc}")
        return 2
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
