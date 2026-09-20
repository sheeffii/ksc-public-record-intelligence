"""Machine-readable manifest of a verified controlled corpus.

`docs/ingestion/manifests/<name>.json` is the tracked reproducibility record of
what Phase 7 holds: one entry per ingested record with the values *as
persisted* after the quality gate — identifiers, official URLs, hashes, sizes,
page counts, hearing identity and gate result. Metadata only: no document text,
no bytes. The PDFs and captured pages stay out of Git (data/captures/ is
ignored); the bytes live in object storage under the listed key; the official
KSC URLs remain the canonical provenance.

`CorpusManifest` is the schema. `build_manifest` reads the database for a
bundle and refuses to invent anything: a field the source did not publish is
null. `validate_manifest_file` is what the test suite runs on the committed file.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.models import (
    Case,
    Document,
    DocumentVersion,
    Hearing,
    SourceRecord,
    Transcript,
)
from ksc_ingestion.capture import CaptureBundle, discover
from ksc_ingestion.discovery import DiscoveredRecord
from ksc_ingestion.sources import CASE_NUMBER_PATTERN, require_official

SCHEMA_VERSION = 1


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HearingIdentity(_Model):
    hearing_date: date
    session_sequence: int = Field(ge=1)
    session_label: str | None
    transcript_official_ref: str | None


class QualityGateResult(_Model):
    status: Literal["PASS", "FAIL", "NOT_RUN"]
    checks_passed: int | None = Field(default=None, ge=0)
    checks_total: int | None = Field(default=None, ge=0)


class CorpusRecord(_Model):
    record_id: str = Field(pattern=r"^r\d{2}$")
    case_number: str = Field(pattern=rf"^{CASE_NUMBER_PATTERN}$")
    published_document_id: str | None
    document_official_ref: str
    official_version_ref: str
    version_type: str
    title: str
    record_type: str
    document_type: str
    language: str | None
    filing_party_label: str | None
    filing_party: str | None
    court_level: str | None
    published_status: str
    visibility: str
    published_date: str | None
    document_date: date | None
    detail_page_url: str
    artifact_url: str
    source_system: str
    external_record_id: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_size: int = Field(ge=1)
    page_count: int | None = Field(default=None, ge=0)
    artifact_status: str
    object_key: str
    fetch_method: str | None
    metadata_source: str
    reference_source: str | None
    hearing: HearingIdentity | None
    quality_gate: QualityGateResult

    @field_validator("detail_page_url", "artifact_url")
    @classmethod
    def _official(cls, value: str) -> str:
        return require_official(value)


class CorpusManifest(_Model):
    schema_version: int
    case_number: str = Field(pattern=rf"^{CASE_NUMBER_PATTERN}$")
    bundle_id: str
    generated_at: datetime
    source: str
    note: str
    record_count: int = Field(ge=1)
    document_count: int = Field(ge=1)
    version_count: int = Field(ge=1)
    total_bytes: int = Field(ge=1)
    records: list[CorpusRecord]

    @field_validator("records")
    @classmethod
    def _consistent(cls, records: list[CorpusRecord]) -> list[CorpusRecord]:
        refs = [r.official_version_ref for r in records]
        if len(set(refs)) != len(refs):
            raise ValueError("official_version_ref must be unique")
        hashes = [r.sha256 for r in records]
        if len(set(hashes)) != len(hashes):
            raise ValueError("sha256 must be unique")
        return records


class ManifestBuildError(RuntimeError):
    pass


def build_manifest(
    session: Session, bundle: CaptureBundle, *, gate_report: Path | None
) -> CorpusManifest:
    """Read the persisted state for every record of `bundle`. Raises if a
    record is not fully held (this manifest describes verified corpora only)."""

    case = session.scalar(select(Case).where(Case.case_number == bundle.manifest.case_number))
    if case is None:
        raise ManifestBuildError(f"case {bundle.manifest.case_number} not seeded")
    gate: dict[str, Any] = {}
    if gate_report is not None and gate_report.is_file():
        data = json.loads(gate_report.read_text(encoding="utf-8"))
        gate = {row["record_id"]: row for row in data.get("rows", [])}

    records: list[CorpusRecord] = []
    for discovered in discover(bundle):
        if not isinstance(discovered, DiscoveredRecord):
            raise ManifestBuildError(f"{discovered.item_key}: {discovered.reason}")
        extra = discovered.raw_metadata.get("metadata", {}).get("extra", {})
        record_id = extra.get("source_record_id")
        source = session.scalar(
            select(SourceRecord).where(
                SourceRecord.case_id == case.id,
                SourceRecord.source_system == discovered.source_system,
                SourceRecord.external_record_id == discovered.external_record_id,
            )
        )
        if source is None or source.document_id is None or source.document_version_id is None:
            raise ManifestBuildError(f"{discovered.item_key}: not persisted")
        document = session.get(Document, source.document_id)
        version = session.get(DocumentVersion, source.document_version_id)
        if (
            document is None
            or version is None
            or version.sha256 is None
            or version.storage_key is None
        ):
            raise ManifestBuildError(f"{discovered.item_key}: version not held")
        if version.byte_size is None:
            raise ManifestBuildError(f"{discovered.item_key}: byte size missing")

        hearing_identity = None
        if source.hearing_id is not None:
            hearing = session.get(Hearing, source.hearing_id)
            transcript = (
                session.get(Transcript, source.transcript_id) if source.transcript_id else None
            )
            if hearing is not None:
                hearing_identity = HearingIdentity(
                    hearing_date=hearing.hearing_date,
                    session_sequence=hearing.session_sequence,
                    session_label=hearing.session_label,
                    transcript_official_ref=transcript.official_ref if transcript else None,
                )

        g = gate.get(record_id or "")
        if g:
            checks = g.get("checks", {})
            gate_result = QualityGateResult(
                status="PASS" if g.get("passed") else "FAIL",
                checks_passed=sum(1 for v in checks.values() if v),
                checks_total=len(checks),
            )
        else:
            gate_result = QualityGateResult(status="NOT_RUN")

        records.append(
            CorpusRecord(
                record_id=record_id or "r00",
                case_number=case.case_number,
                published_document_id=extra.get("published_document_id"),
                document_official_ref=document.official_ref,
                official_version_ref=version.official_version_ref,
                version_type=version.version_type.value,
                title=source.title or discovered.title,
                record_type=extra.get("published_record_type") or source.record_type,
                document_type=document.document_type,
                language=source.language,
                filing_party_label=discovered.filing_party_label,
                filing_party=document.filing_party.value if document.filing_party else None,
                court_level=extra.get("published_court_level"),
                published_status=extra.get("published_public_status") or version.visibility.value,
                visibility=version.visibility.value,
                published_date=extra.get("published_date"),
                document_date=document.document_date,
                detail_page_url=source.canonical_source_url or discovered.detail_page_url,
                artifact_url=version.source_url or "",
                source_system=source.source_system.value,
                external_record_id=source.external_record_id,
                sha256=version.sha256,
                byte_size=version.byte_size,
                page_count=version.page_count,
                artifact_status=version.artifact_status.value,
                object_key=version.storage_key,
                fetch_method=version.fetch_method,
                metadata_source=discovered.metadata_source.value,
                reference_source=(extra.get("reference") or {}).get("source"),
                hearing=hearing_identity,
                quality_gate=gate_result,
            )
        )

    records.sort(key=lambda r: r.record_id)
    return CorpusManifest(
        schema_version=SCHEMA_VERSION,
        case_number=case.case_number,
        bundle_id=bundle.manifest.bundle_id,
        generated_at=datetime.now(UTC),
        source="database state after ingestion and quality gate; official KSC URLs are the canonical provenance",
        note=(
            "Metadata only. PDFs and captured pages are intentionally not committed "
            "(data/captures/ is git-ignored); artifact bytes live in object storage under "
            "object_key and are identified by sha256."
        ),
        record_count=len(records),
        document_count=len({r.document_official_ref for r in records}),
        version_count=len({r.official_version_ref for r in records}),
        total_bytes=sum(r.byte_size for r in records),
        records=records,
    )


def write_manifest(manifest: CorpusManifest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")


def validate_manifest_file(path: Path) -> CorpusManifest:
    manifest = CorpusManifest.model_validate_json(path.read_text(encoding="utf-8"))
    if manifest.record_count != len(manifest.records):
        raise ValueError("record_count disagrees with records")
    if manifest.document_count != len({r.document_official_ref for r in manifest.records}):
        raise ValueError("document_count disagrees with records")
    if manifest.version_count != len({r.official_version_ref for r in manifest.records}):
        raise ValueError("version_count disagrees with records")
    if manifest.total_bytes != sum(r.byte_size for r in manifest.records):
        raise ValueError("total_bytes disagrees with records")
    for r in manifest.records:
        if r.case_number != manifest.case_number:
            raise ValueError(f"{r.record_id}: case number differs from the manifest")
        # An annex version may interleave its suffixes (…/F03668/RED/A01/RED under
        # …/F03668/A01), so require every document segment to appear, in order.
        doc_parts, ver_parts = r.document_official_ref.split("/"), r.official_version_ref.split("/")
        it = iter(ver_parts)
        if not all(part in it for part in doc_parts):
            raise ValueError(f"{r.record_id}: version ref is not under its document ref")
        if r.sha256 not in r.object_key:
            raise ValueError(f"{r.record_id}: object key is not hash-addressed")
        if r.record_type.lower() == "transcript" and r.hearing is None:
            raise ValueError(f"{r.record_id}: transcript without hearing identity")
    return manifest
