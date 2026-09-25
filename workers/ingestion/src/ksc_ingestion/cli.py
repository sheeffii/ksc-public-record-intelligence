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
import json
import logging
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import select

from ksc_api.config import get_settings
from ksc_api.db.session import get_sessionmaker
from ksc_api.logging_config import configure_logging
from ksc_api.models import Case
from ksc_api.repositories.ingestion import IngestionStatusRepository
from ksc_ingestion.acquisition import (
    AcquisitionQueue,
    AutomatedAcquirer,
    OfficialHttpAdapter,
    write_browser_plan,
)
from ksc_ingestion.ai_quality_gate import run_phase11_gate, write_phase11_report
from ksc_ingestion.appeal_pipeline import Phase12Pipeline
from ksc_ingestion.appeal_quality_gate import run_phase12_gate, write_phase12_report
from ksc_ingestion.capture import BundleError, load_bundle, load_inventory
from ksc_ingestion.capture_import import SourceImportError, import_capture
from ksc_ingestion.corpus_manifest import build_manifest, validate_manifest_file, write_manifest
from ksc_ingestion.evidence_pipeline import Phase9Pipeline
from ksc_ingestion.external_media import (
    MediaManifestError,
    import_media_manifest,
    run_phase14_gate,
    write_phase14_report,
)
from ksc_ingestion.fetch import HttpFetcher
from ksc_ingestion.findings_pipeline import Phase10Pipeline
from ksc_ingestion.findings_quality_gate import run_phase10_gate, write_phase10_report
from ksc_ingestion.parse_pipeline import Phase8Pipeline
from ksc_ingestion.phase13_quality_gate import run_phase13_gate, write_phase13_report
from ksc_ingestion.phase17_report import build_phase17_pass_a_report, write_phase17_pass_a_report
from ksc_ingestion.phase19b import Phase19BPipeline
from ksc_ingestion.phase19b_report import run_phase19b_report
from ksc_ingestion.phase19b_report import write_report as write_phase19b_report
from ksc_ingestion.pipeline import CaseNotSeededError, Ingestor, RunOutcome
from ksc_ingestion.probe import probe, record_probe
from ksc_ingestion.quality_gate import report_to_table, run_gate, write_report
from ksc_ingestion.source_geometry import SourceGeometryProjector
from ksc_ingestion.sources import NotOfficialSourceError
from ksc_ingestion.storage import InMemoryObjectStore, MinioObjectStore, ObjectStore
from ksc_ingestion.structured_projection import Phase17StructuredPipeline
from ksc_ingestion.structured_quality_gate import run_phase17c_gate, write_phase17c_report
from ksc_ingestion.transcript_sync import TranscriptSyncProjector
from ksc_ingestion.verified_mentions import Phase19MentionProjector
from ksc_ingestion.verified_mentions_gate import run_phase19a_gate, write_phase19a_report

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


def cmd_inventory(args: argparse.Namespace) -> int:
    """Synchronize an operator-exported, metadata-only official inventory."""

    try:
        inventory = load_inventory(Path(args.path))
        outcome = _ingestor(dry_run=args.dry_run).run_inventory(
            inventory, resume=not args.no_resume, dry_run=args.dry_run
        )
    except (BundleError, CaseNotSeededError) as exc:
        print(f"inventory rejected: {exc}", file=sys.stderr)
        return 2
    _print_outcome(outcome)
    if not args.dry_run:
        settings = get_settings()
        with get_sessionmaker()() as session:
            case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
            assert case is not None
            queued = AcquisitionQueue(session, case).enqueue_missing()
            session.commit()
        print(f"queued_missing_artifacts={queued}")
    return 0


def cmd_phase17_report(args: argparse.Namespace) -> int:
    settings = get_settings()
    with get_sessionmaker()() as session:
        report = build_phase17_pass_a_report(
            session, case_number=settings.case_id, generated_at=args.generated_at
        )
    write_phase17_pass_a_report(report, Path(args.out))
    print(
        f"official_inventory={report.official_inventory_count} "
        f"held={report.held_corpus_count} parsed={report.counts.parsed_versions} "
        f"indexed={report.counts.indexed_versions} out={args.out}"
    )
    return 0


def cmd_build_structured(args: argparse.Namespace) -> int:
    settings = get_settings()
    result = Phase17StructuredPipeline(get_sessionmaker(), case_number=settings.case_id).run()
    print(
        f"people={result.people} witnesses={result.witnesses} "
        f"organizations={result.organizations} exhibits={result.exhibits} "
        f"occurrences={result.occurrences} review_required={result.review_required}"
    )
    return 0


def cmd_gate_phase17c(args: argparse.Namespace) -> int:
    settings = get_settings()
    with get_sessionmaker()() as session:
        case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
        if case is None:
            print(f"case {settings.case_id} is not seeded", file=sys.stderr)
            return 2
        report = run_phase17c_gate(session, case, args.generated_at)
    if args.json:
        write_phase17c_report(report, Path(args.json))
    print(
        f"people={report.people} witnesses={report.witnesses} organizations={report.organizations} "
        f"exhibits={report.exhibits} occurrences={report.occurrences} "
        f"review_required={report.review_required} passed={str(report.passed).lower()}"
    )
    return 0 if report.passed else 1


def cmd_project_mentions(args: argparse.Namespace) -> int:
    settings = get_settings()
    result = Phase19MentionProjector(get_sessionmaker(), case_number=settings.case_id).run()
    states = " ".join(f"{key}={value}" for key, value in result.by_kind_state.items())
    print(
        f"run={result.run_id} rows={result.rows} {states} "
        f"unregistered_witness_codes={result.unregistered_witness_codes} "
        f"unregistered_exhibit_ids={result.unregistered_exhibit_ids} "
        f"legacy_removed={result.legacy_rows_removed}"
    )
    return 0


def cmd_project_source_geometry(args: argparse.Namespace) -> int:
    """Extract geometry from held bytes and project reusable source anchors."""
    settings = get_settings()
    store = MinioObjectStore(settings)
    result = SourceGeometryProjector(get_sessionmaker(), store, case_number=settings.case_id).run()
    print(
        json.dumps(
            {
                "run_id": str(result.run_id),
                "versions": result.versions,
                "native_pages": result.native_pages,
                "ocr_required_pages": result.ocr_required_pages,
                "geometry_words": result.geometry_words,
                "anchors": result.anchors,
                "precision": result.precision,
                "by_object_type": result.by_object_type,
            },
            indent=2,
        )
    )
    return 0


def cmd_project_transcript_sync(args: argparse.Namespace) -> int:
    """Project transcript-segment anchors and printed page-header context."""
    settings = get_settings()
    result = TranscriptSyncProjector(get_sessionmaker(), case_number=settings.case_id).run()
    print(
        json.dumps(
            {
                "run_id": str(result.run_id),
                "versions": result.versions,
                "segments": result.segments,
                "precision": result.precision,
                "reasons": result.reasons,
                "page_contexts": result.page_contexts,
            },
            indent=2,
        )
    )
    return 0


def cmd_build_intelligence(args: argparse.Namespace) -> int:
    settings = get_settings()
    result = Phase19BPipeline(get_sessionmaker(), case_number=settings.case_id).run()
    print(json.dumps({"run_id": str(result.run_id), **result.detail}, indent=2, default=str))
    return 0


def cmd_report_phase19b(args: argparse.Namespace) -> int:
    settings = get_settings()
    with get_sessionmaker()() as session:
        case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
        if case is None:
            print(f"case {settings.case_id} is not seeded", file=sys.stderr)
            return 2
        report = run_phase19b_report(session, case, args.generated_at)
    if args.json:
        write_phase19b_report(report, Path(args.json))
    print(json.dumps({"passed": report["passed"], "checks": report["checks"]}, indent=2))
    return 0 if report["passed"] else 1


def cmd_gate_phase19a(args: argparse.Namespace) -> int:
    settings = get_settings()
    with get_sessionmaker()() as session:
        case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
        if case is None:
            print(f"case {settings.case_id} is not seeded", file=sys.stderr)
            return 2
        report = run_phase19a_gate(session, case, args.generated_at)
    if args.json:
        write_phase19a_report(report, Path(args.json))
    print(
        f"rows={report.total_rows} verified={report.total_verified} "
        f"review_required={report.total_review_required} "
        f"provenance_violations={report.provenance_violations} "
        f"dedup_conflicts={report.dedup_conflicts} passed={str(report.passed).lower()}"
    )
    return 0 if report.passed else 1


def cmd_queue_artifacts(args: argparse.Namespace) -> int:
    settings = get_settings()
    with get_sessionmaker()() as session:
        case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
        if case is None:
            print(f"case {settings.case_id} is not seeded", file=sys.stderr)
            return 2
        queued = AcquisitionQueue(session, case).enqueue_missing()
        session.commit()
    print(f"queued_missing_artifacts={queued}")
    return 0


def cmd_browser_plan(args: argparse.Namespace) -> int:
    settings = get_settings()
    with get_sessionmaker()() as session:
        case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
        if case is None:
            print(f"case {settings.case_id} is not seeded", file=sys.stderr)
            return 2
        queue = AcquisitionQueue(session, case)
        queue.enqueue_missing()
        items = queue.browser_plan(limit=args.limit)
        write_browser_plan(items, Path(args.out), case_number=case.case_number)
        session.commit()
    print(f"wrote {args.out}: {len(items)} public artifact requests")
    return 0


def cmd_acquire_http(args: argparse.Namespace) -> int:
    """Consume one bounded queue batch through ordinary identified HTTP."""

    settings = get_settings()
    store = MinioObjectStore(settings)
    store.ensure_bucket()
    with HttpFetcher(min_interval=args.min_interval) as fetcher:
        result = AutomatedAcquirer(
            get_sessionmaker(), store, case_number=settings.case_id
        ).run_batch(
            OfficialHttpAdapter(fetcher),
            owner=args.owner,
            batch_size=args.batch_size,
            lease_seconds=args.lease_seconds,
        )
    print(
        f"claimed={result.claimed} fetched={result.fetched} blocked={result.blocked} "
        f"failed={result.failed} quarantined={result.quarantined}"
    )
    return 0 if result.blocked == result.failed == result.quarantined == 0 else 1


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
        f"items_failed={c.items_failed} duplicates={c.items_duplicate} "
        f"verified_bytes={c.verified_artifact_bytes} parse_review={c.parse_review_required} "
        f"metadata_snapshots={c.source_metadata_snapshots} "
        f"queue=(pending={c.acquisition_pending} leased={c.acquisition_leased} "
        f"blocked={c.acquisition_blocked} failed={c.acquisition_failed}) "
        f"quarantine_open={c.quarantine_open} processing_runs={c.processing_runs}"
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
    result = Phase8Pipeline(get_sessionmaker(), store, case_number=settings.case_id).run(
        force=args.force
    )
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


def cmd_reresolve(args: argparse.Namespace) -> int:
    """Rebuild identifier mappings and re-resolve held citations without network access."""

    settings = get_settings()
    store = MinioObjectStore(settings)
    result = Phase8Pipeline(get_sessionmaker(), store, case_number=settings.case_id).reresolve()
    print(
        f"identifiers={result['identifiers']} resolved={result['resolved']} "
        f"ambiguous={result['ambiguous']} unresolved={result['unresolved']} "
        f"invalid={result['invalid']} retired={result['retired']}"
    )
    return 0


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


def cmd_build_appeal(args: argparse.Namespace) -> int:
    """Build the reviewed Phase 12 benchmark; performs no network access."""
    settings = get_settings()
    result = Phase12Pipeline(get_sessionmaker(), case_number=settings.case_id).run()
    print(
        f"issues={result.issues} source_backed_links={result.source_backed_links} "
        f"comparisons={result.comparisons} red_team_reviews={result.red_team_reviews} "
        f"red_team_findings={result.red_team_findings} missing_sources={result.missing_sources}"
    )
    return 0


def cmd_gate_appeal(args: argparse.Namespace) -> int:
    """Audit the Phase 12 benchmark and fail-closed corpus limitations."""
    settings = get_settings()
    with get_sessionmaker()() as session:
        report = run_phase12_gate(
            session, case_number=settings.case_id, generated_at=args.generated_at
        )
    print(
        f"issues={report.issues} source_backed_links={report.source_backed_links} "
        f"comparisons={report.comparisons} red_team_findings={report.red_team_findings} "
        f"resolved_citations={report.resolved_citations} abstentions={report.abstentions} "
        f"authoritative_records_unchanged={str(report.authoritative_records_unchanged).lower()} "
        f"passed={str(report.passed).lower()}"
    )
    for item in report.missing_sources:
        print(f"  missing: {item}")
    if args.json:
        write_phase12_report(report, Path(args.json))
        print(f"report written to {args.json}")
    return 0 if report.passed else 1


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


def cmd_gate_ai(args: argparse.Namespace) -> int:
    """Evaluate citation-first AI against the held controlled corpus."""
    settings = get_settings()
    with get_sessionmaker()() as session:
        report = run_phase11_gate(
            session,
            settings,
            manifest_path=Path(args.manifest),
            evaluation_path=Path(args.evaluation),
            generated_at=args.generated_at,
        )
    print(
        f"cases={report.evaluation_cases} sources={report.retrieved_sources} "
        f"claim_source_links={report.validated_claim_source_links} "
        f"abstentions={report.correctly_abstained_cases} "
        f"source_records_unchanged={str(report.source_records_unchanged).lower()} "
        f"passed={str(report.passed).lower()}"
    )
    if args.json:
        write_phase11_report(report, Path(args.json))
        print(f"report written to {args.json}")
    return 0 if report.passed else 1


def cmd_gate_phase13(args: argparse.Namespace) -> int:
    """Measure the real held corpus; synthetic fixtures never satisfy scale."""

    settings = get_settings()
    store = MinioObjectStore(settings)
    with get_sessionmaker()() as session:
        report = run_phase13_gate(
            session,
            store,
            case_number=settings.case_id,
            generated_at=args.generated_at,
            required_real_records=args.minimum_records,
        )
    print(
        f"accepted={report.accepted_real_records}/{report.required_real_records} "
        f"source_records={report.source_records} documents={report.documents} "
        f"versions={report.versions} fetched={report.fetched_versions} "
        f"bytes={report.verified_artifact_bytes} citations={report.citations} "
        f"integrity_ready={str(report.integrity_ready).lower()} "
        f"performance_ready={str(report.performance_ready).lower()} "
        f"real_scale_ready={str(report.real_scale_ready).lower()} "
        f"completion_ready={str(report.completion_ready).lower()}"
    )
    if report.limitation:
        print(f"  limitation: {report.limitation}")
    if args.json:
        write_phase13_report(report, Path(args.json))
        print(f"report written to {args.json}")
    return 0 if report.completion_ready else 1


def cmd_import_media(args: argparse.Namespace) -> int:
    """Import a reviewed manifest of manually submitted public URLs; no network access."""
    settings = get_settings()
    try:
        with get_sessionmaker()() as session:
            case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
            if case is None:
                print(f"case {settings.case_id} is not seeded", file=sys.stderr)
                return 2
            result = import_media_manifest(session, case, Path(args.manifest))
    except MediaManifestError as exc:
        print(f"media manifest rejected: {exc}", file=sys.stderr)
        return 2
    print(
        f"sources={result.sources} items={result.items} statements={result.statements} "
        f"court_links={result.court_links} comparisons={result.comparisons}"
    )
    return 0


def cmd_gate_phase14(args: argparse.Namespace) -> int:
    """Audit the controlled real external-source set and the court/source boundary."""
    settings = get_settings()
    with get_sessionmaker()() as session:
        case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
        if case is None:
            print(f"case {settings.case_id} is not seeded", file=sys.stderr)
            return 2
        report = run_phase14_gate(session, case, Path(args.manifest), args.generated_at)
    print(
        f"sources={report.real_public_sources} items={report.real_public_items} "
        f"statements={report.exact_statements} links={report.court_links} "
        f"invalid_links={report.invalid_court_links} comparisons={report.comparisons} "
        f"manifest_mismatches={report.manifest_item_mismatches} "
        f"verification_violations={report.verification_violations} "
        f"passed={str(report.passed).lower()}"
    )
    if args.json:
        write_phase14_report(report, Path(args.json))
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

    p_inventory = sub.add_parser(
        "inventory", help="sync a metadata-only inventory exported from an official surface"
    )
    p_inventory.add_argument("path")
    p_inventory.add_argument("--dry-run", action="store_true")
    p_inventory.add_argument("--no-resume", action="store_true")
    p_inventory.set_defaults(func=cmd_inventory)

    p_phase17_report = sub.add_parser(
        "report-phase17a", help="write the metadata-only Phase 17A inventory and coverage report"
    )
    p_phase17_report.add_argument("--generated-at", type=date.fromisoformat, default=date.today())
    p_phase17_report.add_argument("--out", required=True)
    p_phase17_report.set_defaults(func=cmd_phase17_report)
    p_structured = sub.add_parser(
        "build-structured", help="build deterministic Phase 17 actor and exhibit projections"
    )
    p_structured.set_defaults(func=cmd_build_structured)
    p_structured_gate = sub.add_parser(
        "gate-phase17c", help="audit structured projections and exact provenance"
    )
    p_structured_gate.add_argument("--generated-at", type=date.fromisoformat, default=date.today())
    p_structured_gate.add_argument("--json")
    p_structured_gate.set_defaults(func=cmd_gate_phase17c)
    p_mentions = sub.add_parser(
        "project-mentions", help="project Phase 19A deterministic verified entity mentions"
    )
    p_mentions.set_defaults(func=cmd_project_mentions)
    p_source_geometry = sub.add_parser(
        "project-source-geometry",
        help="extract native geometry from held PDFs and project SourceAnchors",
    )
    p_source_geometry.set_defaults(func=cmd_project_source_geometry)
    p_transcript_sync = sub.add_parser(
        "project-transcript-sync",
        help="project transcript-segment SourceAnchors and printed page-header context",
    )
    p_transcript_sync.set_defaults(func=cmd_project_transcript_sync)
    p_intelligence = sub.add_parser(
        "build-intelligence",
        help="project Phase 19B aliases, appearances, exhibit status events, mentions and typed edges",
    )
    p_intelligence.set_defaults(func=cmd_build_intelligence)
    p_phase19b = sub.add_parser(
        "report-phase19b", help="Phase 19B corpus-depth analysis and reconciliation gate"
    )
    p_phase19b.add_argument("--generated-at", type=date.fromisoformat, default=date.today())
    p_phase19b.add_argument("--json")
    p_phase19b.set_defaults(func=cmd_report_phase19b)
    p_mentions_gate = sub.add_parser(
        "gate-phase19a", help="reconcile and audit Phase 19A verified mentions"
    )
    p_mentions_gate.add_argument("--generated-at", type=date.fromisoformat, default=date.today())
    p_mentions_gate.add_argument("--json")
    p_mentions_gate.set_defaults(func=cmd_gate_phase19a)

    p_queue = sub.add_parser(
        "queue-artifacts", help="enqueue missing bytes for already-known public versions"
    )
    p_queue.set_defaults(func=cmd_queue_artifacts)

    p_plan = sub.add_parser(
        "browser-plan", help="write a lawful operator-capture plan for missing public artifacts"
    )
    p_plan.add_argument("--out", required=True)
    p_plan.add_argument("--limit", type=int, default=100)
    p_plan.set_defaults(func=cmd_browser_plan)

    p_acquire = sub.add_parser(
        "acquire-http", help="consume one bounded artifact batch via identified official HTTP"
    )
    p_acquire.add_argument("--owner", required=True)
    p_acquire.add_argument("--batch-size", type=int, default=10)
    p_acquire.add_argument("--lease-seconds", type=int, default=300)
    p_acquire.add_argument("--min-interval", type=float, default=5.0)
    p_acquire.set_defaults(func=cmd_acquire_http)

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
    p_parse.add_argument(
        "--force", action="store_true", help="deterministically rebuild all held parser output"
    )
    p_parse.set_defaults(func=cmd_parse)
    p_reresolve = sub.add_parser(
        "reresolve", help="rebuild the identifier index and re-resolve all held citations"
    )
    p_reresolve.set_defaults(func=cmd_reresolve)
    p_evidence = sub.add_parser(
        "build-evidence", help="build citation-backed graph edges and source-backed timeline events"
    )
    p_evidence.set_defaults(func=cmd_build_evidence)
    p_findings = sub.add_parser(
        "build-findings",
        help="build the hand-reviewed finding/evidence benchmark from held public records",
    )
    p_findings.set_defaults(func=cmd_build_findings)
    p_appeal = sub.add_parser(
        "build-appeal", help="build the hand-reviewed Phase 12 appeal-research benchmark"
    )
    p_appeal.set_defaults(func=cmd_build_appeal)
    p_appeal_gate = sub.add_parser(
        "gate-appeal", help="audit the Phase 12 controlled-corpus benchmark"
    )
    p_appeal_gate.add_argument("--generated-at", default="2026-09-21")
    p_appeal_gate.add_argument("--json")
    p_appeal_gate.set_defaults(func=cmd_gate_appeal)
    p_findings_gate = sub.add_parser(
        "gate-findings", help="audit the Phase 10 finding matrix against the controlled corpus"
    )
    p_findings_gate.add_argument(
        "--manifest", default="docs/ingestion/manifests/phase7-controlled-corpus.json"
    )
    p_findings_gate.add_argument("--generated-at", default="2026-09-21")
    p_findings_gate.add_argument("--json")
    p_findings_gate.set_defaults(func=cmd_gate_findings)
    p_ai_gate = sub.add_parser(
        "gate-ai", help="evaluate Phase 11 citation-first AI on the controlled corpus"
    )
    p_ai_gate.add_argument(
        "--manifest", default="docs/ingestion/manifests/phase7-controlled-corpus.json"
    )
    p_ai_gate.add_argument("--evaluation", default="tests/evaluation/phase11_questions.json")
    p_ai_gate.add_argument("--generated-at", default="2026-09-21")
    p_ai_gate.add_argument("--json")
    p_ai_gate.set_defaults(func=cmd_gate_ai)
    p_phase13_gate = sub.add_parser(
        "gate-phase13", help="real-corpus scale, integrity and performance gate"
    )
    p_phase13_gate.add_argument("--generated-at", type=date.fromisoformat, default=date.today())
    p_phase13_gate.add_argument("--minimum-records", type=int, default=50)
    p_phase13_gate.add_argument("--json")
    p_phase13_gate.set_defaults(func=cmd_gate_phase13)
    p_media = sub.add_parser(
        "import-media", help="import reviewed external public URLs from a Phase 14 manifest"
    )
    p_media.add_argument("manifest")
    p_media.set_defaults(func=cmd_import_media)
    p_phase14_gate = sub.add_parser(
        "gate-phase14", help="audit real external sources and the court-record boundary"
    )
    p_phase14_gate.add_argument(
        "--manifest", default="docs/ingestion/manifests/phase14-external-media.json"
    )
    p_phase14_gate.add_argument("--generated-at", default="2026-09-22")
    p_phase14_gate.add_argument("--json")
    p_phase14_gate.set_defaults(func=cmd_gate_phase14)
    return parser


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    args = build_parser().parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
