"""Reproducible Phase 17 corpus inventory and structured-data coverage report.

The report is deliberately metadata-only.  It inventories what has actually
been discovered and persisted; it does not claim that records absent from the
database are absent from the official public record.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ksc_api.models import (
    ArtifactStatus,
    Case,
    Citation,
    Document,
    DocumentPage,
    DocumentParagraph,
    DocumentVersion,
    Event,
    Exhibit,
    Hearing,
    Organization,
    Person,
    Relationship,
    ResolutionState,
    SourceRecord,
    Transcript,
    TranscriptSegment,
    Witness,
)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InventoryRecord(_Model):
    source_record_id: str
    official_reference: str | None
    title: str | None
    record_date: date | None
    party: str | None
    document_type: str
    language: str | None
    public_status: str
    official_detail_url: str
    official_pdf_url: str | None
    version_reference: str | None
    version_states: list[str]
    acquisition_state: str
    parse_state: str
    index_state: str


class CorpusCounts(_Model):
    source_records: int = Field(ge=0)
    documents: int = Field(ge=0)
    versions: int = Field(ge=0)
    pdfs: int = Field(ge=0)
    pages: int = Field(ge=0)
    paragraphs: int = Field(ge=0)
    transcript_segments: int = Field(ge=0)
    parsed_versions: int = Field(ge=0)
    indexed_versions: int = Field(ge=0)
    citations: int = Field(ge=0)
    citations_resolved: int = Field(ge=0)
    citations_ambiguous: int = Field(ge=0)
    citations_unresolved: int = Field(ge=0)
    citations_invalid: int = Field(ge=0)


class StructuredProjectionAudit(_Model):
    category: str
    model: str
    real_rows: int = Field(ge=0)
    source_backed_rows: int = Field(ge=0)
    extraction_pipeline: str
    api: str
    ui: str
    missing: str | None


class NextBatch(_Model):
    target_size: int = 75
    genuinely_new_inventory_records: int = Field(ge=0)
    inventory_supports_acquisition: bool
    status: Literal["ready", "requires_new_official_inventory"]
    priorities: list[str]
    rule: str


class Phase17PassAReport(_Model):
    schema_version: int = 1
    phase: str = "17A"
    generated_at: date
    case_number: str
    declared_scope: str
    completeness_claim: str
    inventory_first_seen: datetime | None
    inventory_last_seen: datetime | None
    official_inventory_count: int = Field(ge=0)
    held_corpus_count: int = Field(ge=0)
    counts: CorpusCounts
    languages: dict[str, int]
    years: dict[str, int]
    document_types: dict[str, int]
    parties: dict[str, int]
    version_states: dict[str, int]
    inventory: list[InventoryRecord]
    structured_data: list[StructuredProjectionAudit]
    missing_historical_strata: list[str]
    next_batch: NextBatch


def _count(session: Session, model: type[Any], *where: Any) -> int:
    return int(session.scalar(select(func.count()).select_from(model).where(*where)) or 0)


def _metadata(record: SourceRecord) -> dict[str, Any]:
    return record.raw_metadata if isinstance(record.raw_metadata, dict) else {}


def _official_reference(record: SourceRecord, document: Document | None) -> str | None:
    if document is not None:
        return document.official_ref
    metadata = _metadata(record).get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get("official_ref")
        return value if isinstance(value, str) else None
    return None


def _version_states(version: DocumentVersion | None) -> list[str]:
    if version is None:
        return []
    upper = version.official_version_ref.upper()
    states: list[str] = []
    for marker in ("CORRED", "RED2", "COR", "RED"):
        if f"/{marker}" in upper:
            states.append(marker)
    if "/A" in upper:
        states.append("ANNEX")
    if version.version_type.value.upper() not in states:
        states.append(version.version_type.value.upper())
    return states


def _distribution(values: Sequence[str | None]) -> dict[str, int]:
    counts = Counter(value or "UNSPECIFIED" for value in values)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def build_phase17_pass_a_report(
    session: Session, *, case_number: str, generated_at: date
) -> Phase17PassAReport:
    case = session.scalar(select(Case).where(Case.case_number == case_number))
    if case is None:
        raise LookupError(f"case {case_number} is not seeded")

    source_rows = session.scalars(
        select(SourceRecord)
        .where(SourceRecord.case_id == case.id)
        .order_by(SourceRecord.external_record_id)
    ).all()
    documents = session.scalars(
        select(Document).where(Document.case_id == case.id).order_by(Document.official_ref)
    ).all()
    document_by_id = {row.id: row for row in documents}
    versions = session.scalars(
        select(DocumentVersion)
        .join(Document)
        .where(Document.case_id == case.id)
        .order_by(DocumentVersion.official_version_ref)
    ).all()
    version_by_id = {row.id: row for row in versions}

    inventory: list[InventoryRecord] = []
    for source in source_rows:
        document = document_by_id.get(source.document_id) if source.document_id else None
        version = (
            version_by_id.get(source.document_version_id) if source.document_version_id else None
        )
        record_date = None
        party = None
        index_state = "not_indexed"
        if document is not None:
            record_date = document.document_date or document.filing_date or document.public_date
            party = document.filing_party.value if document.filing_party else None
            index_state = document.ingestion_state.value
        parse_state = "not_parsed"
        acquisition_state = "not_fetched"
        if version is not None:
            acquisition_state = version.artifact_status.value
            if version.parsed_at is not None:
                parse_state = "review_required" if version.parse_requires_review else "parsed"
        inventory.append(
            InventoryRecord(
                source_record_id=source.external_record_id,
                official_reference=_official_reference(source, document),
                title=source.title,
                record_date=record_date,
                party=party,
                document_type=source.record_type,
                language=source.language,
                public_status=source.visibility.value,
                official_detail_url=source.canonical_source_url or source.discovery_url,
                official_pdf_url=version.source_url if version else None,
                version_reference=version.official_version_ref if version else None,
                version_states=_version_states(version),
                acquisition_state=acquisition_state,
                parse_state=parse_state,
                index_state=index_state,
            )
        )

    source_backed_hearings = _count(
        session,
        Hearing,
        Hearing.case_id == case.id,
        Hearing.id.in_(select(SourceRecord.hearing_id).where(SourceRecord.hearing_id.is_not(None))),
    )
    source_backed_events = _count(
        session,
        Event,
        Event.case_id == case.id,
        (Event.source_record_id.is_not(None) | Event.citation_id.is_not(None)),
    )
    source_backed_relationships = _count(
        session,
        Relationship,
        Relationship.case_id == case.id,
        Relationship.citation_id.in_(
            select(Citation.id).where(
                Citation.source_document_version_id.is_not(None),
                Citation.resolution_state == ResolutionState.RESOLVED,
                (
                    Citation.source_page.is_not(None)
                    | Citation.source_para.is_not(None)
                    | Citation.source_pdf_page_index.is_not(None)
                    | Citation.source_transcript_segment_id.is_not(None)
                ),
            )
        ),
    )
    segment_stmt = (
        select(TranscriptSegment.id)
        .join(Transcript)
        .join(Hearing)
        .where(
            Hearing.case_id == case.id,
            Transcript.document_version_id.is_not(None),
            (
                TranscriptSegment.pdf_page_index.is_not(None)
                | TranscriptSegment.page_number.is_not(None)
                | TranscriptSegment.line_from.is_not(None)
            ),
        )
    )
    statement_rows = _count(
        session,
        TranscriptSegment,
        TranscriptSegment.id.in_(segment_stmt),
    )

    citation_states = {
        state.value: _count(
            session, Citation, Citation.case_id == case.id, Citation.resolution_state == state
        )
        for state in ResolutionState
    }
    counts = CorpusCounts(
        source_records=len(source_rows),
        documents=len(documents),
        versions=len(versions),
        pdfs=sum(
            version.artifact_status == ArtifactStatus.FETCHED
            and version.mime_type == "application/pdf"
            for version in versions
        ),
        pages=_count(
            session,
            DocumentPage,
            DocumentPage.document_version_id.in_(
                select(DocumentVersion.id).join(Document).where(Document.case_id == case.id)
            ),
        ),
        paragraphs=_count(
            session,
            DocumentParagraph,
            DocumentParagraph.document_version_id.in_(
                select(DocumentVersion.id).join(Document).where(Document.case_id == case.id)
            ),
        ),
        transcript_segments=statement_rows,
        parsed_versions=sum(version.parsed_at is not None for version in versions),
        indexed_versions=sum(
            document_by_id[version.document_id].ingestion_state.value == "indexed"
            for version in versions
        ),
        citations=sum(citation_states.values()),
        citations_resolved=citation_states.get("resolved", 0),
        citations_ambiguous=citation_states.get("ambiguous", 0),
        citations_unresolved=citation_states.get("unresolved", 0),
        citations_invalid=citation_states.get("invalid", 0),
    )

    structured = [
        StructuredProjectionAudit(
            category="people",
            model="persons",
            real_rows=_count(session, Person, Person.case_id == case.id),
            source_backed_rows=0,
            extraction_pipeline="missing",
            api="GET /api/v1/people",
            ui="/people and /people/{slug}",
            missing="No reviewed source-backed projection pipeline; ambiguous names must remain unresolved.",
        ),
        StructuredProjectionAudit(
            category="witness_codes",
            model="witnesses",
            real_rows=_count(session, Witness, Witness.case_id == case.id),
            source_backed_rows=0,
            extraction_pipeline="missing",
            api="GET /api/v1/witnesses",
            ui="/witnesses and /witnesses/{code}",
            missing="No reviewed public-code projection pipeline; protected identities must never be inferred.",
        ),
        StructuredProjectionAudit(
            category="organizations",
            model="organizations",
            real_rows=_count(session, Organization, Organization.case_id == case.id),
            source_backed_rows=0,
            extraction_pipeline="missing",
            api="missing",
            ui="missing",
            missing="Projection pipeline and read surface are absent.",
        ),
        StructuredProjectionAudit(
            category="exhibits",
            model="exhibits",
            real_rows=_count(session, Exhibit, Exhibit.case_id == case.id),
            source_backed_rows=0,
            extraction_pipeline="missing",
            api="GET /api/v1/exhibits",
            ui="/exhibits",
            missing="No official exhibit-status projection pipeline; filing annexes are not treated as exhibits.",
        ),
        StructuredProjectionAudit(
            category="hearings",
            model="hearings + transcripts",
            real_rows=_count(session, Hearing, Hearing.case_id == case.id),
            source_backed_rows=source_backed_hearings,
            extraction_pipeline="capture normalization",
            api="transcript detail and event APIs",
            ui="reader and timeline",
            missing="Direct hearing list API is absent.",
        ),
        StructuredProjectionAudit(
            category="statements",
            model="transcript_segments",
            real_rows=statement_rows,
            source_backed_rows=statement_rows,
            extraction_pipeline="PDF transcript parser",
            api="GET /api/v1/transcripts/{official_ref}",
            ui="document reader",
            missing="No separate semantic statement/testimony classification; segments remain exact source fragments.",
        ),
        StructuredProjectionAudit(
            category="events",
            model="events",
            real_rows=_count(session, Event, Event.case_id == case.id),
            source_backed_rows=source_backed_events,
            extraction_pipeline="deterministic evidence projection",
            api="GET /api/v1/events",
            ui="/timeline",
            missing=None,
        ),
        StructuredProjectionAudit(
            category="relationships",
            model="relationships",
            real_rows=_count(session, Relationship, Relationship.case_id == case.id),
            source_backed_rows=source_backed_relationships,
            extraction_pipeline="deterministic resolved-citation projection",
            api="network, path and relationship APIs",
            ui="/network and /evidence/path",
            missing=None,
        ),
    ]

    year_values = [
        str(value.year) if value else "UNSPECIFIED"
        for document in documents
        for value in [document.document_date or document.filing_date or document.public_date]
    ]
    version_markers = [marker for version in versions for marker in _version_states(version)]
    first_seen = min((row.discovered_at for row in source_rows), default=None)
    last_seen = max((row.last_seen_at for row in source_rows), default=None)
    held_count = sum(version.artifact_status == ArtifactStatus.FETCHED for version in versions)
    return Phase17PassAReport(
        generated_at=generated_at,
        case_number=case_number,
        declared_scope=(
            "Officially discovered public records for KSC-BC-2020-06 in EN and SQ, "
            "with held artifacts and structured projections reported separately."
        ),
        completeness_claim=f"Known public corpus indexed as of {generated_at.isoformat()}; not a complete-corpus claim.",
        inventory_first_seen=first_seen,
        inventory_last_seen=last_seen,
        official_inventory_count=len(source_rows),
        held_corpus_count=held_count,
        counts=counts,
        languages=_distribution([row.language for row in source_rows]),
        years=_distribution(year_values),
        document_types=_distribution([row.record_type for row in source_rows]),
        parties=_distribution(
            [
                document.filing_party.value if document.filing_party else None
                for document in documents
            ]
        ),
        version_states={
            key: Counter(version_markers).get(key, 0)
            for key in (
                "RED",
                "RED2",
                "COR",
                "CORRED",
                "ANNEX",
                "ORIGINAL",
                "PUBLIC_REDACTED",
                "RECLASSIFIED",
                "TRANSLATION",
            )
        },
        inventory=inventory,
        structured_data=structured,
        missing_historical_strata=[
            "2021-2024 are absent from the held logical-document date distribution.",
            "Trial-period transcripts before the three February 2026 hearing dates are absent.",
            "Broad pre-trial, trial, appeals, Registrar, Victims' Counsel, public annex and exhibit coverage is not inventoried exhaustively.",
            "EN/SQ counterpart coverage is incomplete and has not been reconciled against an exhaustive official listing.",
        ],
        next_batch=NextBatch(
            genuinely_new_inventory_records=0,
            inventory_supports_acquisition=False,
            status="requires_new_official_inventory",
            priorities=[
                "2021-2022 pre-trial decisions, orders and party filings",
                "2023-2025 public trial transcripts, including EN/SQ counterparts",
                "SPO, all Defence teams, Registrar and Victims' Counsel filings",
                "appeals material and public corrected/reclassified versions",
                "public annexes and exhibits whose official identity/status is explicit",
            ],
            rule=(
                "Run a lawful operator-assisted official discovery pass capped at 75 genuinely new records; "
                "do not acquire until the metadata-only inventory validates and excludes known records."
            ),
        ),
    )


def write_phase17_pass_a_report(report: Phase17PassAReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
