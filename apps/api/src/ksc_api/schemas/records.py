"""Entity read contracts."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Literal

from pydantic import Field, SerializerFunctionWrapHandler, model_serializer

from ksc_api.models.enums import (
    ClaimOrigin,
    ClaimStance,
    DatePrecision,
    DateType,
    DocumentVersionType,
    EntityKind,
    ExaminationType,
    FindingLinkType,
    Party,
    RelationshipType,
    VerificationState,
    Visibility,
)
from ksc_api.schemas.citation import CitationRead
from ksc_api.schemas.common import ReadModel


class CaseRead(ReadModel):
    case_number: str
    title: str
    court: str
    seat: str | None
    official_source_url: str | None
    description: str | None


class ReferenceCounts(ReadModel):
    """Counts only — never a score, weight, rank, centrality or priority.
    Mirrors `ReferenceCounts` in packages/shared (HANDOFF.md §9); each count is
    the number of public, provenance-backed edges between the entity's graph
    node and nodes of the named kind, except `transcript_mentions` (public
    transcript segments attributed to a witness, plus hearing edges) and
    `citations_resolved` (resolved citations targeting the entity)."""

    relationships: int = Field(ge=0)
    document_mentions: int = Field(ge=0)
    transcript_mentions: int = Field(ge=0)
    exhibit_refs: int = Field(ge=0)
    findings: int = Field(ge=0)
    witnesses_who_referred: int = Field(ge=0)
    incidents: int = Field(ge=0)
    citations_resolved: int = Field(ge=0)


class DocumentVersionRead(ReadModel):
    official_version_ref: str
    version_type: DocumentVersionType
    version_label: str | None
    visibility: Visibility
    public_date: date | None
    source_url: str | None
    sha256: str | None
    mime_type: str | None
    page_count: int | None
    supersedes_version_ref: str | None


class DocumentSummary(ReadModel):
    official_ref: str
    filing_number: str | None
    title: str
    document_type: str
    language: str | None
    filing_party: Party | None
    document_date: date | None
    filing_date: date | None
    public_date: date | None
    visibility: Visibility
    counts: ReferenceCounts


class DocumentDetail(DocumentSummary):
    source_url: str | None
    # Empty when the document is not public: existence is stated, content is not.
    versions: list[DocumentVersionRead]


class DocumentPageRead(ReadModel):
    page_number: int
    text: str | None
    running_head: str | None
    has_redactions: bool
    redaction_extents: list[dict[str, Any]] | None


class DocumentChunkRead(ReadModel):
    """A structural span (section / paragraph range) of a public version."""

    sequence: int
    page_from: int | None
    page_to: int | None
    para_from: int | None
    para_to: int | None
    text: str


class PersonRead(ReadModel):
    slug: str
    display_name: str
    public_role: str | None
    description: str | None
    aliases: list[str]
    counts: ReferenceCounts


class WitnessPublic(ReadModel):
    display_name: str
    called_by: Party | None


class WitnessRead(ReadModel):
    """Protection is structural: `public` is absent — not null-filled — unless
    an official public source identifies the witness. Anything that is not
    explicitly public serialises as protected."""

    code: str
    protected: bool
    protective_measures: list[str]
    counts: ReferenceCounts
    public: WitnessPublic | None = None

    @model_serializer(mode="wrap")
    def _omit_public_when_protected(self, handler: SerializerFunctionWrapHandler) -> Any:
        data = handler(self)
        if self.protected or data.get("public") is None:
            data.pop("public", None)
        return data


class ExhibitRead(ReadModel):
    official_exhibit_id: str
    title: str
    description: str | None
    tendered_by: Party | None
    through_witness_code: str | None
    admitted_date: date | None
    document_date: date | None
    document_version_ref: str | None
    visibility: Visibility
    counts: ReferenceCounts


class IncidentRead(ReadModel):
    slug: str
    title: str
    summary: str | None
    location: str | None
    date_from: date | None
    date_to: date | None
    date_precision: DatePrecision
    charges_pleaded: list[dict[str, Any]] | None
    counts: ReferenceCounts


class EventRead(ReadModel):
    id: uuid.UUID
    title: str
    description: str | None
    date_type: DateType
    date_from: date | None
    date_to: date | None
    date_precision: DatePrecision
    incident_slug: str | None
    document_ref: str | None
    citation: CitationRead | None


class ClaimMentionRead(ReadModel):
    stance: ClaimStance
    quote_text: str | None
    note: str | None
    verification_state: VerificationState
    citation: CitationRead


class ClaimRead(ReadModel):
    claim_key: str
    text: str
    origin: ClaimOrigin
    verification_state: VerificationState
    source_citation: CitationRead | None
    mentions: list[ClaimMentionRead]


class FindingEvidenceLinkRead(ReadModel):
    link_type: FindingLinkType
    court_cited: bool
    court_cited_para: int | None
    verification_state: VerificationState
    citation: CitationRead


class ArgumentRead(ReadModel):
    argument_key: str
    party: Party
    title: str
    text: str
    document_ref: str | None
    para_from: int | None
    para_to: int | None
    verification_state: VerificationState
    citation: CitationRead | None


class ArgumentResponseRead(ReadModel):
    response_kind: str
    argument: ArgumentRead
    citation: CitationRead | None


class FindingSummary(ReadModel):
    finding_key: str
    judgment_ref: str
    text: str
    para_from: int
    para_to: int | None
    person_slug: str | None
    incident_slug: str | None
    charge_ref: str | None
    verification_state: VerificationState
    citation: CitationRead | None
    counts: ReferenceCounts


class FindingDetail(FindingSummary):
    legal_element: str | None
    mode_of_liability: str | None
    evidence_links: list[FindingEvidenceLinkRead]
    arguments: list[ArgumentRead]


class TranscriptSegmentRead(ReadModel):
    sequence: int
    page_number: int | None
    line_from: int | None
    line_to: int | None
    speaker: str | None
    speaker_role: str | None
    witness_code: str | None
    examination_type: ExaminationType
    closed_session: bool
    # Absent for closed session: the segment states that content exists and
    # is not public.
    text: str | None


class TranscriptRead(ReadModel):
    official_ref: str | None
    hearing_date: date
    session_label: str | None
    language: str | None
    visibility: Visibility
    page_from: int | None
    page_to: int | None
    document_version_ref: str | None
    segments: list[TranscriptSegmentRead]


class GraphNodeRead(ReadModel):
    id: uuid.UUID
    entity_kind: EntityKind
    label: str
    # Route-facing key of the entity (slug / code / official ref).
    ref: str
    protected: bool = False


class RelationshipRead(ReadModel):
    id: uuid.UUID
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    relationship_type: RelationshipType
    verification_state: VerificationState
    citation: CitationRead
    note: str | None


class NetworkRead(ReadModel):
    nodes: list[GraphNodeRead]
    edges: list[RelationshipRead]


SearchCategory = Literal[
    "documents", "people", "witnesses", "exhibits", "incidents", "findings", "locations"
]


class SearchHit(ReadModel):
    category: SearchCategory
    ref: str
    title: str
    context: str | None
    protected: bool = False


class SearchRead(ReadModel):
    query: str
    hits: list[SearchHit]
