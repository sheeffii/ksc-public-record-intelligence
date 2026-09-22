"""Quality gate for an ingested capture bundle (roadmap Phase 7 — "manually
inspect the first corpus").

For every record in the bundle it checks, against the database and the object
store, that what was persisted is exactly what the official source published
and the operator captured: case, official reference, title, type, language,
visibility, official detail and artifact URLs, declared vs stored SHA-256 and
byte size, stored object bytes (re-hashed from MinIO), PDF validity and page
count, source record, document, version, hearing / transcript rows, job item
state, and that nothing outside the public set was stored. It writes a table
and a JSON report; it changes nothing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from minio import Minio
from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.config import Settings
from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    ArtifactQuarantine,
    ArtifactStatus,
    Case,
    Document,
    DocumentVersion,
    Hearing,
    IngestionItemStatus,
    IngestionJob,
    IngestionJobItem,
    SourceRecord,
    Transcript,
)
from ksc_ingestion.artifacts import UnsupportedArtifactError, inspect, sha256_hex
from ksc_ingestion.capture import CaptureBundle, discover
from ksc_ingestion.discovery import DiscoveredRecord, visibility_from_classification
from ksc_ingestion.normalize import NormalizationError, normalize
from ksc_ingestion.sources import canonicalize, classify


@dataclass
class GateRow:
    record_id: str
    item_key: str
    official_ref: str | None
    official_version_ref: str | None
    language: str | None
    visibility: str | None
    checks: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(self.checks.values())


@dataclass
class GateReport:
    bundle_id: str
    case_number: str
    generated_at: str
    rows: list[GateRow]
    summary: dict[str, Any]

    @property
    def passed(self) -> bool:
        return all(row.passed for row in self.rows) and bool(self.rows)


def _stored_bytes(client: Minio, bucket: str, key: str) -> bytes | None:
    try:
        response = client.get_object(bucket, key)
    except Exception:  # noqa: BLE001 - reported as a failed check
        return None
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def run_gate(
    session: Session, settings: Settings, bundle: CaptureBundle, *, bucket: str | None = None
) -> GateReport:
    case = session.scalar(select(Case).where(Case.case_number == bundle.manifest.case_number))
    if case is None:
        raise RuntimeError(f"case {bundle.manifest.case_number} not seeded")
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    bucket = bucket or settings.minio_bucket_documents
    rows: list[GateRow] = []
    seen_sha: set[str] = set()

    for record in discover(bundle):
        rid = (
            record.raw_metadata.get("metadata", {}).get("extra", {}).get("source_record_id", "?")
            if isinstance(record, DiscoveredRecord)
            else "?"
        )
        if not isinstance(record, DiscoveredRecord):
            rows.append(
                GateRow(
                    rid,
                    record.item_key,
                    None,
                    None,
                    None,
                    None,
                    {"discovered": False},
                    [record.reason],
                )
            )
            continue
        row = GateRow(rid, record.item_key, record.official_ref, None, record.language, None)
        c = row.checks
        try:
            normalized = normalize(record, expected_case_number=case.case_number)
        except NormalizationError as exc:
            # Not accepted by ingestion. The gate passes such a record only when
            # the pipeline recorded the refusal in an open quarantine row, i.e.
            # nothing was stored and a human review is pending.
            item_status = (
                IngestionItemStatus.AMBIGUOUS_MAPPING
                if exc.ambiguous
                else IngestionItemStatus.INVALID_METADATA
            )
            c["refusal_quarantined"] = (
                session.scalar(
                    select(ArtifactQuarantine.id).where(
                        ArtifactQuarantine.case_id == case.id,
                        ArtifactQuarantine.state == "open",
                        ArtifactQuarantine.reason_code == item_status.value,
                        ArtifactQuarantine.reason == str(exc),
                    )
                )
                is not None
            )
            c["nothing_stored"] = (
                session.scalar(
                    select(DocumentVersion.id)
                    .join(Document)
                    .where(
                        Document.case_id == case.id,
                        DocumentVersion.source_url.in_(
                            [artifact.url for artifact in record.artifacts]
                        ),
                    )
                )
                is None
            )
            row.notes.append(f"not accepted: {exc}")
            rows.append(row)
            continue
        c["case_number_matches"] = record.case_number == case.case_number
        c["detail_url_official"] = (
            classify(record.detail_page_url).source_system.value == record.source_system.value
        )
        expected_visibility = visibility_from_classification(record.classification)
        c["classification_public"] = expected_visibility in PUBLIC_VISIBILITIES
        row.visibility = expected_visibility.value

        source = session.scalar(
            select(SourceRecord).where(
                SourceRecord.case_id == case.id,
                SourceRecord.source_system == record.source_system,
                SourceRecord.external_record_id == record.external_record_id,
            )
        )
        c["source_record_exists"] = source is not None
        if source is not None:
            c["source_record_urls"] = (
                source.canonical_source_url == canonicalize(record.detail_page_url)
                and classify(source.discovery_url) is not None
            )
            c["source_metadata_source_recorded"] = (source.raw_metadata or {}).get(
                "metadata_source"
            ) == record.metadata_source.value
            c["source_visibility"] = source.visibility is expected_visibility

        document = session.scalar(
            select(Document).where(
                Document.case_id == case.id, Document.official_ref == normalized.official_ref
            )
        )
        c["document_exists"] = document is not None
        (nv,) = normalized.versions
        row.official_version_ref = nv.official_version_ref
        if document is None:
            rows.append(row)
            continue
        c["document_type"] = document.document_type == normalized.document_type
        c["document_visibility_public"] = document.visibility in PUBLIC_VISIBILITIES
        is_translation = nv.version_type.value == "translation"
        c["document_title"] = True if is_translation else document.title == normalized.title
        if is_translation:
            row.notes.append("translation record: document title stays in the original language")
        if is_translation:
            # The shared document points at the original-language detail page; the
            # translation's own detail URL is on its source record (checked above).
            c["document_source_url_official"] = (
                bool(document.source_url)
                and classify(document.source_url or "").kind.value == "pcr_detail"
            )
        else:
            c["document_source_url"] = document.source_url == canonicalize(record.detail_page_url)
        c["source_record_linked_to_document"] = (
            source is not None and source.document_id == document.id
        )

        version = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.document_id == document.id,
                DocumentVersion.official_version_ref == nv.official_version_ref,
            )
        )
        c["version_exists"] = version is not None
        if version is None:
            rows.append(row)
            continue
        c["version_type"] = version.version_type is nv.version_type
        c["version_visibility"] = (
            version.visibility is nv.visibility and version.visibility in PUBLIC_VISIBILITIES
        )
        c["version_artifact_fetched"] = version.artifact_status is ArtifactStatus.FETCHED
        c["version_source_url_is_official_pdf"] = (
            version.source_url == nv.source_url
            and classify(nv.source_url).kind.value == "pcr_artifact"
        )
        c["version_fetch_method"] = version.fetch_method == "operator_browser_capture"
        c["version_fetched_at"] = version.fetched_at is not None
        declared_sha = nv.artifact.declared_sha256
        c["declared_sha256_equals_stored"] = (
            declared_sha is not None and version.sha256 == declared_sha
        )
        c["declared_bytes_equal_stored"] = (
            nv.artifact.declared_byte_size is not None
            and version.byte_size == nv.artifact.declared_byte_size
        )
        c["sha256_unique_in_bundle"] = version.sha256 not in seen_sha
        if version.sha256:
            seen_sha.add(version.sha256)

        local = nv.artifact.local_file.read_bytes() if nv.artifact.local_file else b""
        c["local_file_hash_equals_stored"] = bool(local) and sha256_hex(local) == version.sha256
        try:
            info = inspect(local)
            c["pdf_valid"] = True
            c["page_count_matches_pdf"] = version.page_count == info.page_count
            c["pdf_first_page_names_case"] = (
                not info.case_numbers_on_first_page
                or case.case_number in info.case_numbers_on_first_page
            )
        except UnsupportedArtifactError as exc:
            c["pdf_valid"] = False
            row.notes.append(str(exc))

        stored = (
            _stored_bytes(client, bucket, version.storage_key or "")
            if version.storage_key
            else None
        )
        c["minio_object_exists"] = stored is not None
        c["minio_object_hash_equals_declared"] = (
            stored is not None and sha256_hex(stored) == declared_sha
        )
        c["minio_key_is_hash_addressed"] = bool(version.storage_key) and (version.sha256 or "") in (
            version.storage_key or ""
        )

        if record.hearing is not None:
            hearing = session.scalar(
                select(Hearing).where(
                    Hearing.case_id == case.id,
                    Hearing.hearing_date == record.hearing.hearing_date,
                    Hearing.session_sequence == record.hearing.session_sequence,
                )
            )
            transcript = session.scalar(
                select(Transcript).where(Transcript.document_version_id == version.id)
            )
            c["hearing_exists"] = hearing is not None
            c["transcript_linked_to_version_and_hearing"] = (
                transcript is not None
                and hearing is not None
                and transcript.hearing_id == hearing.id
            )
            c["source_record_linked_to_transcript"] = (
                source is not None
                and transcript is not None
                and source.transcript_id == transcript.id
            )

        item = session.scalar(
            select(IngestionJobItem)
            .join(IngestionJob, IngestionJob.id == IngestionJobItem.job_id)
            .where(
                IngestionJob.case_id == case.id,
                IngestionJob.cursor["bundle_id"].astext == bundle.manifest.bundle_id,
                IngestionJobItem.item_key == record.item_key,
            )
            .order_by(IngestionJobItem.created_at)
        )
        c["job_item_downloaded"] = (
            item is not None and item.status is IngestionItemStatus.DOWNLOADED
        )
        c["job_item_links_version"] = item is not None and item.document_version_id == version.id
        rows.append(row)

    summary = {
        "records": len(rows),
        "passed": sum(1 for r in rows if r.passed),
        "failed": [r.record_id for r in rows if not r.passed],
        "failed_checks": {
            r.record_id: [k for k, v in r.checks.items() if not v] for r in rows if not r.passed
        },
        "documents": len({r.official_ref for r in rows}),
        "versions": len({r.official_version_ref for r in rows}),
    }
    return GateReport(
        bundle_id=bundle.manifest.bundle_id,
        case_number=case.case_number,
        generated_at=datetime.now(UTC).isoformat(),
        rows=rows,
        summary=summary,
    )


def report_to_json(report: GateReport) -> str:
    return json.dumps(
        {
            "bundle_id": report.bundle_id,
            "case_number": report.case_number,
            "generated_at": report.generated_at,
            "passed": report.passed,
            "summary": report.summary,
            "rows": [
                {
                    "record_id": r.record_id,
                    "item_key": r.item_key,
                    "official_ref": r.official_ref,
                    "official_version_ref": r.official_version_ref,
                    "language": r.language,
                    "visibility": r.visibility,
                    "passed": r.passed,
                    "checks": r.checks,
                    "notes": r.notes,
                }
                for r in report.rows
            ],
        },
        indent=2,
        ensure_ascii=False,
    )


def report_to_table(report: GateReport) -> str:
    lines = [f"quality gate — bundle {report.bundle_id} — case {report.case_number}", ""]
    lines.append(f"{'rec':4} {'version ref':40} {'lang':4} {'visibility':16} {'checks':7} result")
    for r in report.rows:
        total, ok = len(r.checks), sum(1 for v in r.checks.values() if v)
        result = "PASS" if r.passed else "FAIL " + ",".join(k for k, v in r.checks.items() if not v)
        lines.append(
            f"{r.record_id:4} {r.official_version_ref!s:40} {r.language!s:4} "
            f"{r.visibility!s:16} {ok:>3}/{total:<3} {result}"
        )
    s = report.summary
    lines.append("")
    lines.append(
        f"records={s['records']} passed={s['passed']} failed={len(s['failed'])} "
        f"documents={s['documents']} versions={s['versions']} → {'PASS' if report.passed else 'FAIL'}"
    )
    return "\n".join(lines)


def write_report(report: GateReport, path: Path) -> None:
    path.write_text(report_to_json(report) + "\n", encoding="utf-8")
