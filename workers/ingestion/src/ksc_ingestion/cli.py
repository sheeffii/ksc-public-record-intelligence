"""`ksc-ingest` — operator entry point for the Phase 7 pipeline.

    ksc-ingest bundle data/captures/<bundle-id> [--dry-run] [--no-resume]
    ksc-ingest probe <official-url> [--record]
    ksc-ingest status [--limit N]

Every command is scoped to the configured case (CASE_ID). `bundle` ingests an
operator capture bundle; `probe` performs one identified request and reports
a challenge as a visible failure; `status` prints jobs, items and record counts.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from sqlalchemy import select

from ksc_api.config import get_settings
from ksc_api.db.session import get_sessionmaker
from ksc_api.logging_config import configure_logging
from ksc_api.models import Case
from ksc_api.repositories.ingestion import IngestionStatusRepository
from ksc_ingestion.capture import BundleError, load_bundle
from ksc_ingestion.fetch import HttpFetcher
from ksc_ingestion.pipeline import CaseNotSeededError, Ingestor, RunOutcome
from ksc_ingestion.probe import probe, record_probe
from ksc_ingestion.sources import NotOfficialSourceError
from ksc_ingestion.storage import InMemoryObjectStore, MinioObjectStore, ObjectStore

log = logging.getLogger(__name__)


def _ingestor(*, dry_run: bool) -> Ingestor:
    settings = get_settings()
    store: ObjectStore
    if dry_run:
        store = InMemoryObjectStore()
    else:
        minio = MinioObjectStore(settings)
        minio.ensure_bucket()
        store = minio
    return Ingestor(get_sessionmaker(), store, case_number=settings.case_id)


def _print_outcome(outcome: RunOutcome) -> None:
    print(
        f"job {outcome.job_id} {outcome.status.value}"
        f"{' (resumed)' if outcome.resumed else ''}{' [dry run]' if outcome.dry_run else ''}"
    )
    for item in outcome.items:
        flag = " (already done)" if item.skipped_as_done else ""
        print(f"  {item.status.value:26} {item.item_key}{flag}")
        if item.reason:
            print(f"  {'':26} reason: {item.reason}")
        for v in item.versions:
            sha = f" sha256={v.sha256[:12]}…" if v.sha256 else ""
            print(f"  {'':26} - {v.official_version_ref}: {v.status.value}{sha}")
    print(
        f"items={len(outcome.items)} downloaded_artifacts={outcome.downloaded_artifacts} "
        f"failed={sum(1 for i in outcome.items if i.status.value in _FAILURES)}"
    )


_FAILURES = {
    "failed_download",
    "blocked_by_access_control",
    "invalid_metadata",
    "unsupported_artifact",
    "ambiguous_mapping",
}


def cmd_bundle(args: argparse.Namespace) -> int:
    try:
        bundle = load_bundle(Path(args.path))
    except BundleError as exc:
        print(f"bundle rejected: {exc}", file=sys.stderr)
        return 2
    try:
        outcome = _ingestor(dry_run=args.dry_run).run_bundle(
            bundle, resume=not args.no_resume, dry_run=args.dry_run
        )
    except CaseNotSeededError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    _print_outcome(outcome)
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    try:
        with HttpFetcher() as fetcher:
            result = probe(args.url, fetcher)
    except NotOfficialSourceError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    state = "reachable" if result.reachable else (result.status.value if result.status else "?")
    print(f"{state}: {result.url}\n  {result.evidence}")
    if args.record and not result.reachable:
        job_id = record_probe(_ingestor(dry_run=False), result)
        print(f"  recorded as job {job_id}")
    return 0 if result.reachable else 1


def cmd_status(args: argparse.Namespace) -> int:
    settings = get_settings()
    with get_sessionmaker()() as session:
        case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
        if case is None:
            print(f"case {settings.case_id} is not seeded", file=sys.stderr)
            return 2
        status = IngestionStatusRepository(session, case).status(job_limit=args.limit)
    c = status.counts
    print(f"case {status.case_number}")
    print(
        f"source_records={c.source_records} documents={c.documents} "
        f"(public={c.documents_public} not_public={c.documents_not_public}) "
        f"versions={c.versions} fetched={c.versions_fetched} "
        f"not_fetched={c.versions_not_fetched} failed={c.versions_failed} "
        f"hearings={c.hearings} transcripts={c.transcripts} jobs={c.jobs} "
        f"items_failed={c.items_failed}"
    )
    for job in status.jobs:
        print(
            f"job {job.id} {job.job_type} {job.status.value} "
            f"discovered={job.discovered_count} downloaded={job.downloaded_count} "
            f"processed={job.processed_count} failed={job.failed_count} cursor={job.cursor}"
        )
        for item in job.items:
            print(f"    {item.status.value:26} {item.item_key}")
            if item.reason:
                print(f"    {'':26} {item.reason}")
    for held in status.held:
        sha = f" sha256={held.sha256[:12]}…" if held.sha256 else ""
        print(
            f"held {held.official_version_ref:40} {held.artifact_status.value:12} "
            f"{held.visibility.value:16}{sha}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ksc-ingest", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_bundle = sub.add_parser("bundle", help="ingest an operator capture bundle")
    p_bundle.add_argument("path")
    p_bundle.add_argument("--dry-run", action="store_true")
    p_bundle.add_argument("--no-resume", action="store_true")
    p_bundle.set_defaults(func=cmd_bundle)

    p_probe = sub.add_parser("probe", help="one identified request to an official URL")
    p_probe.add_argument("url")
    p_probe.add_argument("--record", action="store_true", help="persist a blocked/failed probe")
    p_probe.set_defaults(func=cmd_probe)

    p_status = sub.add_parser("status", help="jobs, items and record counts")
    p_status.add_argument("--limit", type=int, default=10)
    p_status.set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    args = build_parser().parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
