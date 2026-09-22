"""Read contracts for the external-public-source layer."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from ksc_api.models.enums import VerificationState
from ksc_api.schemas.citation import CitationRead
from ksc_api.schemas.common import ReadModel

CourtMediaStatus = Literal[
    "external_only",
    "mentioned",
    "tendered",
    "admitted",
    "rejected",
    "discussed",
    "relied_upon",
    "unknown",
]


class ExternalSourceRead(ReadModel):
    id: uuid.UUID
    platform: str
    source_type: str
    publisher: str
    account: str | None
    canonical_url: str
    language: str
    access_method: str
    terms_note: str
    coverage_note: str
    verification_state: VerificationState


class MediaStatementRead(ReadModel):
    id: uuid.UUID
    sequence: int
    speaker: str | None
    text: str
    exact_quote: bool
    char_from: int | None
    char_to: int | None
    timecode_start_ms: int | None
    timecode_end_ms: int | None
    transcript_origin: str | None
    verification_state: VerificationState


class CourtMediaLinkRead(ReadModel):
    id: uuid.UUID
    court_status: CourtMediaStatus
    note: str
    citation: CitationRead | None
    document_ref: str | None
    exhibit_ref: str | None
    finding_key: str | None
    verification_state: VerificationState


class MediaItemRead(ReadModel):
    id: uuid.UUID
    title: str
    publisher: str
    canonical_url: str
    original_url: str
    published_at: datetime | None
    captured_at: datetime
    language: str
    item_kind: str
    content_sha256: str
    transcript_origin: str | None
    archive_url: str | None
    verification_state: VerificationState
    source: ExternalSourceRead
    statements: list[MediaStatementRead]
    court_links: list[CourtMediaLinkRead]


class MediaItemSummary(ReadModel):
    id: uuid.UUID
    title: str
    publisher: str
    canonical_url: str
    published_at: datetime | None
    captured_at: datetime
    source_type: str
    language: str
    court_statuses: list[CourtMediaStatus]
    verification_state: VerificationState


class MediaComparisonRead(ReadModel):
    id: uuid.UUID
    comparison_key: str
    title: str
    classification: str
    statement_a: MediaStatementRead
    statement_b: MediaStatementRead | None
    court_citation_b: CitationRead | None
    explanation: str
    verification_state: VerificationState


class MediaCoverageRead(ReadModel):
    sources: int = Field(ge=0)
    items: int = Field(ge=0)
    statements: int = Field(ge=0)
    court_links: int = Field(ge=0)
    citation_backed_court_links: int = Field(ge=0)
    comparisons: int = Field(ge=0)


class MediaWorkspaceRead(ReadModel):
    items: list[MediaItemSummary]
    comparisons: list[MediaComparisonRead]
    coverage: MediaCoverageRead
    court_status_taxonomy: list[CourtMediaStatus]
    limitations: list[str]


class MediaTimelineEvent(ReadModel):
    id: uuid.UUID
    media_item_id: uuid.UUID
    title: str
    publisher: str
    occurred_at: datetime
    date_basis: Literal["published", "captured"]
    source_layer: Literal["external_public_source"] = "external_public_source"
    court_statuses: list[CourtMediaStatus]


class MediaNetworkNode(ReadModel):
    id: str
    kind: Literal["external_media", "court_record"]
    label: str


class MediaNetworkEdge(ReadModel):
    id: uuid.UUID
    from_node_id: str
    to_node_id: str
    court_status: CourtMediaStatus
    citation: CitationRead
    verification_state: VerificationState


class MediaNetworkRead(ReadModel):
    nodes: list[MediaNetworkNode]
    edges: list[MediaNetworkEdge]
