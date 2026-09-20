"""Internal data-status contracts (roadmap Phase 7 — UI integration).

These describe ingestion *state*: jobs, items, counts and provenance of what
is held. They never carry document text. Everything is scoped to the
configured case.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from ksc_api.models.enums import (
    ArtifactStatus,
    IngestionItemStatus,
    IngestionJobStatus,
    SourceSystem,
    Visibility,
)
from ksc_api.schemas.common import ReadModel


class IngestionItemRead(ReadModel):
    item_key: str
    sequence: int
    status: IngestionItemStatus
    reason: str | None
    detail: dict[str, Any] | None
    official_ref: str | None
    started_at: datetime | None
    finished_at: datetime | None


class IngestionJobRead(ReadModel):
    id: uuid.UUID
    job_type: str
    source_system: SourceSystem
    status: IngestionJobStatus
    cursor: dict[str, Any] | None
    checkpoint: dict[str, Any] | None
    discovered_count: int = Field(ge=0)
    downloaded_count: int = Field(ge=0)
    processed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    started_at: datetime | None
    finished_at: datetime | None
    error_summary: str | None
    items: list[IngestionItemRead]


class HeldVersionRead(ReadModel):
    """One version with its provenance — the quality-gate view."""

    official_ref: str
    official_version_ref: str
    title: str
    document_type: str
    visibility: Visibility
    artifact_status: ArtifactStatus
    source_url: str | None
    detail_page_url: str | None
    discovery_url: str | None
    source_system: SourceSystem | None
    external_record_id: str | None
    metadata_source: str | None
    sha256: str | None
    byte_size: int | None
    page_count: int | None
    fetched_at: datetime | None
    fetch_method: str | None


class IngestionCounts(ReadModel):
    source_records: int = Field(ge=0)
    documents: int = Field(ge=0)
    documents_public: int = Field(ge=0)
    documents_not_public: int = Field(ge=0)
    versions: int = Field(ge=0)
    versions_fetched: int = Field(ge=0)
    versions_not_fetched: int = Field(ge=0)
    versions_failed: int = Field(ge=0)
    versions_parsed: int = Field(ge=0)
    documents_indexed: int = Field(ge=0)
    pages_parsed: int = Field(ge=0)
    paragraphs_parsed: int = Field(ge=0)
    transcript_segments_parsed: int = Field(ge=0)
    citations: int = Field(ge=0)
    citations_resolved: int = Field(ge=0)
    citations_ambiguous: int = Field(ge=0)
    citations_unresolved: int = Field(ge=0)
    citations_invalid: int = Field(ge=0)
    hearings: int = Field(ge=0)
    transcripts: int = Field(ge=0)
    jobs: int = Field(ge=0)
    items_failed: int = Field(ge=0)


class IngestionStatusRead(ReadModel):
    case_number: str
    counts: IngestionCounts
    jobs: list[IngestionJobRead]
    held: list[HeldVersionRead]
