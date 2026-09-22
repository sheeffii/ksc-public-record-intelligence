"""Real-corpus scale, integrity and performance gate for Phase 13."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    ArtifactQuarantine,
    ArtifactStatus,
    Case,
    Document,
    DocumentVersion,
)
from ksc_api.repositories.ingestion import IngestionStatusRepository
from ksc_ingestion.storage import ObjectStore


class Phase13GateReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 2
    phase: int = 13
    generated_at: date
    case_number: str
    required_real_records: int = Field(ge=1)
    source_records: int = Field(ge=0)
    documents: int = Field(ge=0)
    # Public versions whose held bytes re-hash to the immutable version row and
    # that are not under open quarantine: the only thing the scale gate counts.
    accepted_real_records: int = Field(ge=0)
    versions: int = Field(ge=0)
    fetched_versions: int = Field(ge=0)
    verified_artifact_bytes: int = Field(ge=0)
    pages: int = Field(ge=0)
    paragraphs: int = Field(ge=0)
    transcript_segments: int = Field(ge=0)
    citations: int = Field(ge=0)
    citations_resolved: int = Field(ge=0)
    citations_ambiguous: int = Field(ge=0)
    citations_unresolved: int = Field(ge=0)
    citations_invalid: int = Field(ge=0)
    duplicate_items: int = Field(ge=0)
    failed_items: int = Field(ge=0)
    open_quarantine: int = Field(ge=0)
    missing_objects: list[str]
    hash_mismatches: list[str]
    fetched_non_public_versions: int = Field(ge=0)
    quarantined_parsed_versions: int = Field(ge=0)
    search_latency_ms: float = Field(ge=0)
    exact_lookup_latency_ms: float = Field(ge=0)
    network_latency_ms: float = Field(ge=0)
    performance_threshold_ms: float = Field(gt=0)
    integrity_ready: bool
    performance_ready: bool
    architecture_ready: bool
    real_scale_ready: bool
    completion_ready: bool
    limitation: str | None


def _timed(session: Session, statement: str, params: dict[str, object]) -> float:
    started = time.perf_counter()
    session.execute(text(statement), params).all()
    return round((time.perf_counter() - started) * 1000, 3)


def run_phase13_gate(
    session: Session,
    store: ObjectStore,
    *,
    case_number: str,
    generated_at: date,
    required_real_records: int = 50,
    performance_threshold_ms: float = 500.0,
) -> Phase13GateReport:
    case = session.scalar(select(Case).where(Case.case_number == case_number))
    if case is None:
        raise LookupError(f"case {case_number} is not seeded")
    counts = IngestionStatusRepository(session, case).counts()

    held = session.scalars(
        select(DocumentVersion)
        .join(Document)
        .where(
            Document.case_id == case.id,
            DocumentVersion.artifact_status == ArtifactStatus.FETCHED,
        )
        .order_by(DocumentVersion.official_version_ref)
    ).all()
    missing_objects: list[str] = []
    hash_mismatches: list[str] = []
    for version in held:
        if not version.storage_key or not store.exists(version.storage_key):
            missing_objects.append(version.official_version_ref)
            continue
        body = store.get(version.storage_key)
        if hashlib.sha256(body).hexdigest() != version.sha256:
            hash_mismatches.append(version.official_version_ref)

    fetched_non_public = int(
        session.scalar(
            select(func.count())
            .select_from(DocumentVersion)
            .join(Document)
            .where(
                Document.case_id == case.id,
                DocumentVersion.artifact_status == ArtifactStatus.FETCHED,
                DocumentVersion.visibility.notin_(PUBLIC_VISIBILITIES),
            )
        )
        or 0
    )
    quarantined_parsed = int(
        session.scalar(
            select(func.count())
            .select_from(ArtifactQuarantine)
            .join(DocumentVersion, DocumentVersion.id == ArtifactQuarantine.document_version_id)
            .where(
                ArtifactQuarantine.case_id == case.id,
                ArtifactQuarantine.state == "open",
                DocumentVersion.parsed_at.is_not(None),
            )
        )
        or 0
    )

    search_ms = _timed(
        session,
        "SELECT id FROM documents WHERE case_id = :case_id "
        "AND search_vector @@ plainto_tsquery('simple', :query) LIMIT 50",
        {"case_id": case.id, "query": "judgment"},
    )
    exact_ms = _timed(
        session,
        "SELECT id FROM record_identifiers WHERE case_id = :case_id "
        "AND normalized_identifier = :identifier LIMIT 10",
        {"case_id": case.id, "identifier": f"{case_number}/F00001"},
    )
    network_ms = _timed(
        session,
        "SELECT r.id FROM relationships r JOIN graph_nodes n ON n.id = r.from_node_id "
        "WHERE n.case_id = :case_id LIMIT 100",
        {"case_id": case.id},
    )

    open_quarantined_version_ids = set(
        session.scalars(
            select(ArtifactQuarantine.document_version_id).where(
                ArtifactQuarantine.case_id == case.id,
                ArtifactQuarantine.state == "open",
                ArtifactQuarantine.document_version_id.is_not(None),
            )
        ).all()
    )
    accepted_real_records = sum(
        1
        for version in held
        if version.visibility in PUBLIC_VISIBILITIES
        and version.official_version_ref not in missing_objects
        and version.official_version_ref not in hash_mismatches
        and version.id not in open_quarantined_version_ids
    )
    integrity_ready = not (
        missing_objects or hash_mismatches or fetched_non_public or quarantined_parsed
    )
    performance_ready = max(search_ms, exact_ms, network_ms) <= performance_threshold_ms
    # These tables/metrics being queryable and artifact verification succeeding
    # prove the operational path is installed. Real scale remains separate.
    architecture_ready = integrity_ready and performance_ready
    # Synthetic fixtures live in another case; unaccepted, quarantined or
    # duplicate material never reaches `held` with a verified hash.
    real_scale_ready = accepted_real_records >= required_real_records
    completion_ready = architecture_ready and real_scale_ready
    limitation = None
    if not real_scale_ready:
        limitation = (
            f"lawful real corpus has {accepted_real_records} accepted records; "
            f"Phase 13 requires at least {required_real_records} before completion"
        )

    return Phase13GateReport(
        generated_at=generated_at,
        case_number=case_number,
        required_real_records=required_real_records,
        source_records=counts.source_records,
        documents=counts.documents,
        accepted_real_records=accepted_real_records,
        versions=counts.versions,
        fetched_versions=counts.versions_fetched,
        verified_artifact_bytes=counts.verified_artifact_bytes,
        pages=counts.pages_parsed,
        paragraphs=counts.paragraphs_parsed,
        transcript_segments=counts.transcript_segments_parsed,
        citations=counts.citations,
        citations_resolved=counts.citations_resolved,
        citations_ambiguous=counts.citations_ambiguous,
        citations_unresolved=counts.citations_unresolved,
        citations_invalid=counts.citations_invalid,
        duplicate_items=counts.items_duplicate,
        failed_items=counts.items_failed,
        open_quarantine=counts.quarantine_open,
        missing_objects=missing_objects,
        hash_mismatches=hash_mismatches,
        fetched_non_public_versions=fetched_non_public,
        quarantined_parsed_versions=quarantined_parsed,
        search_latency_ms=search_ms,
        exact_lookup_latency_ms=exact_ms,
        network_latency_ms=network_ms,
        performance_threshold_ms=performance_threshold_ms,
        integrity_ready=integrity_ready,
        performance_ready=performance_ready,
        architecture_ready=architecture_ready,
        real_scale_ready=real_scale_ready,
        completion_ready=completion_ready,
        limitation=limitation,
    )


def write_phase13_report(report: Phase13GateReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
