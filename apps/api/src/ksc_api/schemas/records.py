"""Entity read contracts."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import Field, SerializerFunctionWrapHandler, model_serializer

from ksc_api.models.enums import (
    ArtifactStatus,
    ClaimOrigin,
    ClaimStance,
    DatePrecision,
    DateType,
    DocumentVersionType,
    EntityKind,
    ExaminationType,
    FindingLinkType,
    Party,
    RelationshipOrigin,
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
    # NOT_FETCHED: the official URLs are known but the bytes are not held.
    artifact_status: ArtifactStatus
    sha256: str | None
    mime_type: str | None
    page_count: int | None
    fetched_at: datetime | None
    text_extraction_method: str
    parsed_at: datetime | None
    parser_name: str | None
    parser_version: str | None
    parse_requires_review: bool
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
    pdf_page_index: int = Field(ge=0)
    page_number: int | None
    printed_page_label: str | None
    text: str | None
    running_head: str | None
    has_redactions: bool
    redaction_extents: list[dict[str, Any]] | None


class DocumentChunkRead(ReadModel):
    """A structural span (section / paragraph range) of a public version."""

    sequence: int
    chunk_kind: str
    pdf_page_index_from: int | None
    pdf_page_index_to: int | None
    page_from: int | None
    page_to: int | None
    para_from: int | None
    para_to: int | None
    text: str


class DocumentParagraphRead(ReadModel):
    sequence: int
    paragraph_number: int = Field(ge=1)
    pdf_page_index_from: int = Field(ge=0)
    pdf_page_index_to: int = Field(ge=0)
    page_from: int | None
    page_to: int | None
    text: str


class PersonRead(ReadModel):
    slug: str
    display_name: str
    public_role: str | None
    description: str | None
    aliases: list[str]
    counts: ReferenceCounts


class OrganizationRead(ReadModel):
    slug: str
    name: str
    kind: str | None
    name_variants: list[str]
    description: str | None
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
    status: str
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
    hearing_ref: str | None
    source_system: str | None
    source_url: str | None
    extraction_origin: str


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
    relationship_basis: Literal["explicit_court_citation", "related_public_record"]
    source_category: str
    note: str | None
    verification_state: VerificationState
    citation: CitationRead


class ArgumentRead(ReadModel):
    argument_key: str
    party: Party
    title: str
    text: str
    document_ref: str | None
    document_version_ref: str | None
    para_from: int | None
    para_to: int | None
    source_scope: Literal["direct_source", "court_summary", "source_missing"]
    underlying_source_ref: str | None
    verification_state: VerificationState
    citation: CitationRead | None


class ArgumentResponseRead(ReadModel):
    response_kind: str
    argument: ArgumentRead
    verification_state: VerificationState
    citation: CitationRead | None


class JudgmentSectionRead(ReadModel):
    heading: str
    level: int = Field(ge=0)
    para_from: int | None
    para_to: int | None


class JudgmentParagraphRead(ReadModel):
    paragraph_number: int = Field(ge=1)
    page_from: int | None
    pdf_page_index_from: int = Field(ge=0)
    text: str


class JudgmentStructureRead(ReadModel):
    document_ref: str
    document_title: str
    document_type: str
    version_ref: str | None
    visibility: Visibility
    source_url: str | None
    sections: list[JudgmentSectionRead]
    paragraphs: list[JudgmentParagraphRead]


class HumanNoteRead(ReadModel):
    author: str
    title: str
    body: str
    provenance: Literal["human"]
    citations: list[CitationRead]


class SourceAuditIssueRead(ReadModel):
    code: str
    detail: str


class FindingSourceAuditRead(ReadModel):
    citations_total: int = Field(ge=0)
    citations_resolved: int = Field(ge=0)
    citations_unresolved: int = Field(ge=0)
    citations_ambiguous: int = Field(ge=0)
    citations_invalid: int = Field(ge=0)
    sources_missing: int = Field(ge=0)
    ambiguous_versions: int = Field(ge=0)
    transcript_coordinates_missing: int = Field(ge=0)
    relationships_unverified: int = Field(ge=0)
    public_redacted_sources: int = Field(ge=0)
    explicitly_cited_by_court: int = Field(ge=0)
    related_not_explicit: int = Field(ge=0)
    issues: list[SourceAuditIssueRead]


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
    court_responses: list[ArgumentResponseRead]
    judgment: JudgmentStructureRead
    human_notes: list[HumanNoteRead]
    source_audit: FindingSourceAuditRead
    corroboration_categories: dict[str, int]
    corroboration_note: str


class TranscriptSegmentRead(ReadModel):
    sequence: int
    pdf_page_index: int | None
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
    source_category: str
    extraction_origin: RelationshipOrigin
    relationship_date: date | None
    date_precision: DatePrecision


class NetworkRead(ReadModel):
    nodes: list[GraphNodeRead]
    edges: list[RelationshipRead]


class EvidencePathRead(ReadModel):
    found: bool
    nodes: list[GraphNodeRead]
    hops: list[RelationshipRead]


SearchCategory = Literal[
    "documents",
    "transcripts",
    "people",
    "organizations",
    "witnesses",
    "exhibits",
    "incidents",
    "findings",
    "locations",
]


MentionClass = Literal["VERIFIED_MENTION", "REVIEW_REQUIRED", "SEARCH_MATCH"]


class SearchHit(ReadModel):
    category: SearchCategory
    ref: str
    title: str
    context: str | None
    protected: bool = False
    # A lexical hit is never a verified mention; see `EntityMentionRead`.
    match_class: Literal["SEARCH_MATCH"] = "SEARCH_MATCH"
    match_kind: Literal["exact_identifier", "title", "phrase", "keyword"] = "keyword"
    version_ref: str | None = None
    pdf_page_index: int | None = None
    page: int | None = None
    para_from: int | None = None
    para_to: int | None = None
    line_from: int | None = None
    line_to: int | None = None
    source_url: str | None = None
    target_path: str | None = None


class EntityMentionRead(ReadModel):
    """A persisted Phase 19A deterministic mention. `char_start`/`char_end`
    index into the text named by `char_anchor`. Rejected rows are never served."""

    id: uuid.UUID
    entity_kind: Literal["person", "witness", "organization", "exhibit"]
    match_class: Literal["VERIFIED_MENTION", "REVIEW_REQUIRED"]
    rule_id: str
    rule_version: int
    occurrence_text: str
    document_ref: str
    document_title: str
    version_ref: str
    version_superseded: bool
    language: str | None
    char_anchor: Literal[
        "transcript_segment_text", "transcript_speaker_label", "document_page_text"
    ]
    char_start: int
    char_end: int
    pdf_page_index: int | None
    page: int | None
    paragraph: int | None
    line_from: int | None
    line_to: int | None
    source_url: str | None
    target_path: str


class SearchRead(ReadModel):
    query: str
    hits: list[SearchHit]
