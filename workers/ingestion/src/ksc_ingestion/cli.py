"""`ksc-ingest` — operator entry point for the Phase 7 pipeline.

    ksc-ingest import-capture <source-dir> <dest-dir> --pdf-dir DIR [--pdf-dir DIR] \
        --bundle-id ID --captured-by NAME [--browser TEXT]
    ksc-ingest bundle data/captures/<bundle-id> [--dry-run] [--no-resume]
    ksc-ingest gate data/captures/<bundle-id> [--json PATH]
    ksc-ingest export-corpus data/captures/<bundle-id> --out docs/ingestion/manifests/<name>.json
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
from ksc_ingestion.capture_import import SourceImportError, import_capture
from ksc_ingestion.corpus_manifest import build_manifest, validate_manifest_file, write_manifest
from ksc_ingestion.evidence_pipeline import Phase9Pipeline
from ksc_ingestion.fetch import HttpFetcher
from ksc_ingestion.findings_pipeline import Phase10Pipeline
from ksc_ingestion.findings_quality_gate import run_phase10_gate, write_phase10_report
from ksc_ingestion.parse_pipeline import Phase8Pipeline
from ksc_ingestion.pipeline import CaseNotSeededError, Ingestor, RunOutcome
from ksc_ingestion.probe import probe, record_probe
from ksc_ingestion.quality_gate import report_to_table, run_gate, write_report
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


def cmd_import_capture(args: argparse.Namespace) -> int:
    try:
        report = import_capture(
            Path(args.source),
            Path(args.dest),
            pdf_dirs=[Path(d) for d in args.pdf_dir],
            bundle_id=args.bundle_id,
            captured_by=args.captured_by,
            browser=args.browser,
        )
    except SourceImportError as exc:
        print(f"import refused: {exc}", file=sys.stderr)
        return 2
    for rec in report["records"]:
        print(
            f"  {rec['record_id']} {rec['match_status']:8} {rec['version_ref']!s:48} "
            f"{rec['ref_source']}"
        )
    print(f"matched {report['matched']}/{report['total']} → {report['dest']}")
    return 0


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


def cmd_gate(args: argparse.Namespace) -> int:
    try:
        bundle = load_bundle(Path(args.path))
    except BundleError as exc:
        print(f"bundle rejected: {exc}", file=sys.stderr)
        return 2
    settings = get_settings()
    with get_sessionmaker()() as session:
        report = run_gate(session, settings, bundle)
    print(report_to_table(report))
    if args.json:
        write_report(report, Path(args.json))
        print(f"report written to {args.json}")
    return 0 if report.passed else 1


def cmd_export_corpus(args: argparse.Namespace) -> int:
    try:
        bundle = load_bundle(Path(args.path))
    except BundleError as exc:
        print(f"bundle rejected: {exc}", file=sys.stderr)
        return 2
    gate_report = (
        Path(args.gate_report) if args.gate_report else Path(args.path) / "quality_gate_report.json"
    )
    with get_sessionmaker()() as session:
        manifest = build_manifest(session, bundle, gate_report=gate_report)
    out = Path(args.out)
    write_manifest(manifest, out)
    validate_manifest_file(out)
    print(
        f"wrote {out}: {manifest.record_count} records, {manifest.document_count} documents, "
        f"{manifest.version_count} versions, {manifest.total_bytes:,} bytes"
    )
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
        f"parsed={c.versions_parsed} indexed={c.documents_indexed} "
        f"pages={c.pages_parsed} paragraphs={c.paragraphs_parsed} "
        f"segments={c.transcript_segments_parsed} citations={c.citations} "
        f"(resolved={c.citations_resolved} ambiguous={c.citations_ambiguous} "
        f"unresolved={c.citations_unresolved} invalid={c.citations_invalid}) "
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


def cmd_parse(args: argparse.Namespace) -> int:
    """Parse every fetched version in the configured controlled corpus.

    This reads only already-held object bytes. It performs no discovery,
    download, crawl or external request.
    """
    settings = get_settings()
    store = MinioObjectStore(settings)
    result = Phase8Pipeline(get_sessionmaker(), store, case_number=settings.case_id).run()
    for version in result.versions:
        review = " REVIEW" if version.requires_review else ""
        print(
            f"  {version.official_version_ref:48} pages={version.pages:4} "
            f"paragraphs={version.paragraphs:4} chunks={version.chunks:4} "
            f"segments={version.transcript_segments:4}{review}"
        )
    print(
        f"versions={len(result.versions)} identifiers={result.identifiers} "
        f"citations={result.citations} resolved={result.resolved} "
        f"ambiguous={result.ambiguous} unresolved={result.unresolved} invalid={result.invalid}"
    )
    return 0 if not any(version.requires_review for version in result.versions) else 1


def cmd_build_evidence(args: argparse.Namespace) -> int:
    """Project already-resolved citations and source dates; performs no network access."""
    settings = get_settings()
    result = Phase9Pipeline(get_sessionmaker(), case_number=settings.case_id).run()
    print(
        f"nodes={result.nodes} edges={result.edges} events={result.events} "
        f"self_citations_skipped={result.skipped_self_citations}"
    )
    return 0


def cmd_build_findings(args: argparse.Namespace) -> int:
    """Build the hand-reviewed real finding benchmark; performs no network access."""
    settings = get_settings()
    result = Phase10Pipeline(get_sessionmaker(), case_number=settings.case_id).run()
    print(
        f"findings={result.findings} evidence_links={result.evidence_links} "
        f"party_arguments={result.party_arguments} court_responses={result.court_responses} "
        f"missing_underlying_party_sources={result.missing_underlying_party_sources}"
    )
    return 0


def cmd_gate_findings(args: argparse.Namespace) -> int:
    """Audit the Phase 10 real-data benchmark and its known source gaps."""
    settings = get_settings()
    manifest = Path(args.manifest)
    with get_sessionmaker()() as session:
        report = run_phase10_gate(
            session,
            case_number=settings.case_id,
            manifest_path=manifest,
            generated_at=args.generated_at,
        )
    print(
        f"findings={report.findings} exact_mappings={report.exact_paragraph_mappings} "
        f"explicit_links={report.explicit_court_cited_links} "
        f"party_positions={report.party_positions} court_responses={report.court_responses} "
        f"trial_judgment_present={str(report.trial_judgment_present).lower()} "
        f"passed={str(report.passed).lower()}"
    )
    for item in report.missing_official_material:
        print(f"  missing: {item}")
    if args.json:
        write_phase10_report(report, Path(args.json))
        print(f"report written to {args.json}")
    return 0 if report.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ksc-ingest", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser(
        "import-capture", help="turn the operator's raw capture + downloaded PDFs into a bundle"
    )
    p_import.add_argument("source")
    p_import.add_argument("dest")
    p_import.add_argument("--pdf-dir", action="append", required=True)
    p_import.add_argument("--bundle-id", required=True)
    p_import.add_argument("--captured-by", required=True)
    p_import.add_argument("--browser")
    p_import.set_defaults(func=cmd_import_capture)

    p_bundle = sub.add_parser("bundle", help="ingest an operator capture bundle")
    p_bundle.add_argument("path")
    p_bundle.add_argument("--dry-run", action="store_true")
    p_bundle.add_argument("--no-resume", action="store_true")
    p_bundle.set_defaults(func=cmd_bundle)

    p_gate = sub.add_parser("gate", help="quality gate: verify an ingested bundle end to end")
    p_gate.add_argument("path")
    p_gate.add_argument("--json", help="write the full report to this path")
    p_gate.set_defaults(func=cmd_gate)

    p_export = sub.add_parser(
        "export-corpus", help="write the tracked metadata manifest of a verified bundle"
    )
    p_export.add_argument("path")
    p_export.add_argument("--out", required=True)
    p_export.add_argument("--gate-report", help="default: <bundle>/quality_gate_report.json")
    p_export.set_defaults(func=cmd_export_corpus)

    p_probe = sub.add_parser("probe", help="one identified request to an official URL")
    p_probe.add_argument("url")
    p_probe.add_argument("--record", action="store_true", help="persist a blocked/failed probe")
    p_probe.set_defaults(func=cmd_probe)

    p_status = sub.add_parser("status", help="jobs, items and record counts")
    p_status.add_argument("--limit", type=int, default=10)
    p_status.set_defaults(func=cmd_status)

    p_parse = sub.add_parser(
        "parse", help="parse held PDFs, persist exact coordinates, citations and search text"
    )
    p_parse.set_defaults(func=cmd_parse)
    p_evidence = sub.add_parser(
        "build-evidence", help="build citation-backed graph edges and source-backed timeline events"
    )
    p_evidence.set_defaults(func=cmd_build_evidence)
    p_findings = sub.add_parser(
        "build-findings",
        help="build the hand-reviewed finding/evidence benchmark from held public records",
    )
    p_findings.set_defaults(func=cmd_build_findings)
    p_findings_gate = sub.add_parser(
        "gate-findings", help="audit the Phase 10 finding matrix against the controlled corpus"
    )
    p_findings_gate.add_argument(
        "--manifest", default="docs/ingestion/manifests/phase7-controlled-corpus.json"
    )
    p_findings_gate.add_argument("--generated-at", default="2026-09-21")
    p_findings_gate.add_argument("--json")
    p_findings_gate.set_defaults(func=cmd_gate_findings)
    return parser


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    args = build_parser().parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
