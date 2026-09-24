"""Public read API, v1. Every route reads through `RecordRepository`, which
scopes to the configured case and fails closed on visibility."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ksc_api.models import EntityKind, Party, RelationshipType, VerificationState
from ksc_api.repositories import RecordRepository, get_repository
from ksc_api.schemas.citation import CitationRead, ResolveResult
from ksc_api.schemas.common import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, Page
from ksc_api.schemas.records import (
    ArgumentRead,
    CaseRead,
    ClaimRead,
    DocumentChunkRead,
    DocumentDetail,
    DocumentPageRead,
    DocumentParagraphRead,
    DocumentSummary,
    EntityMentionRead,
    EventRead,
    EvidencePathRead,
    ExhibitRead,
    FindingDetail,
    FindingSummary,
    IncidentRead,
    NetworkRead,
    OrganizationRead,
    PersonRead,
    RelationshipRead,
    SearchRead,
    TranscriptRead,
    WitnessRead,
)

router = APIRouter(prefix="/api/v1", tags=["records"])

Repo = Annotated[RecordRepository, Depends(get_repository)]
Limit = Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)]
Offset = Annotated[int, Query(ge=0)]


def _or_404[T](value: T | None, what: str) -> T:
    if value is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{what} not found")
    return value


@router.get("/case", response_model=CaseRead)
def read_case(repo: Repo) -> CaseRead:
    return repo.get_case()


# ------------------------------------------------------------- documents --
@router.get("/documents", response_model=Page[DocumentSummary])
def list_documents(
    repo: Repo,
    limit: Limit = DEFAULT_PAGE_SIZE,
    offset: Offset = 0,
    document_type: str | None = None,
    q: str | None = None,
) -> Page[DocumentSummary]:
    return repo.list_documents(limit=limit, offset=offset, document_type=document_type, q=q)


@router.get("/documents/{ref:path}", response_model=DocumentDetail)
def read_document(ref: str, repo: Repo) -> DocumentDetail:
    """A document that exists but is not public is returned with
    `visibility` stating so and no versions — not a 404 (ROUTE_MAP.md §8)."""
    return _or_404(repo.get_document(ref), "document")


@router.get("/document-versions/{version_ref:path}/pages", response_model=Page[DocumentPageRead])
def list_document_pages(
    version_ref: str, repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
) -> Page[DocumentPageRead]:
    return _or_404(
        repo.list_document_pages(version_ref, limit=limit, offset=offset), "document version"
    )


@router.get("/document-versions/{version_ref:path}/chunks", response_model=Page[DocumentChunkRead])
def list_document_chunks(
    version_ref: str,
    repo: Repo,
    limit: Limit = DEFAULT_PAGE_SIZE,
    offset: Offset = 0,
    page: Annotated[int | None, Query(ge=1)] = None,
    pdf_page_index: Annotated[int | None, Query(ge=0)] = None,
) -> Page[DocumentChunkRead]:
    return _or_404(
        repo.list_document_chunks(
            version_ref,
            limit=limit,
            offset=offset,
            page=page,
            pdf_page_index=pdf_page_index,
        ),
        "document version",
    )


@router.get(
    "/document-versions/{version_ref:path}/paragraphs",
    response_model=Page[DocumentParagraphRead],
)
def list_document_paragraphs(
    version_ref: str, repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
) -> Page[DocumentParagraphRead]:
    return _or_404(
        repo.list_document_paragraphs(version_ref, limit=limit, offset=offset),
        "document version",
    )


# ---------------------------------------------------------------- people --
@router.get("/people", response_model=Page[PersonRead])
def list_people(
    repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0, q: str | None = None
) -> Page[PersonRead]:
    return repo.list_persons(limit=limit, offset=offset, q=q)


@router.get("/people/{slug}", response_model=PersonRead)
def read_person(slug: str, repo: Repo) -> PersonRead:
    return _or_404(repo.get_person(slug), "person")


@router.get("/organizations", response_model=Page[OrganizationRead])
def list_organizations(
    repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0, q: str | None = None
) -> Page[OrganizationRead]:
    return repo.list_organizations(limit=limit, offset=offset, q=q)


@router.get("/organizations/{slug}", response_model=OrganizationRead)
def read_organization(slug: str, repo: Repo) -> OrganizationRead:
    return _or_404(repo.get_organization(slug), "organization")


# ------------------------------------------------------------- witnesses --
@router.get("/witnesses", response_model=Page[WitnessRead])
def list_witnesses(
    repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
) -> Page[WitnessRead]:
    return repo.list_witnesses(limit=limit, offset=offset)


@router.get("/witnesses/{code}", response_model=WitnessRead)
def read_witness(code: str, repo: Repo) -> WitnessRead:
    return _or_404(repo.get_witness(code), "witness")


# -------------------------------------------------------------- exhibits --
@router.get("/exhibits", response_model=Page[ExhibitRead])
def list_exhibits(
    repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
) -> Page[ExhibitRead]:
    return repo.list_exhibits(limit=limit, offset=offset)


@router.get("/exhibits/{exhibit_id}", response_model=ExhibitRead)
def read_exhibit(exhibit_id: str, repo: Repo) -> ExhibitRead:
    return _or_404(repo.get_exhibit(exhibit_id), "exhibit")


# -------------------------------------------------------------- mentions --
MentionState = Annotated[Literal["verified", "review_required"] | None, Query()]


@router.get("/people/{slug}/mentions", response_model=Page[EntityMentionRead])
def list_person_mentions(
    slug: str,
    repo: Repo,
    limit: Limit = DEFAULT_PAGE_SIZE,
    offset: Offset = 0,
    state: MentionState = None,
) -> Page[EntityMentionRead]:
    return _or_404(
        repo.list_entity_mentions("person", slug, limit=limit, offset=offset, state=state),
        "person",
    )


@router.get("/organizations/{slug}/mentions", response_model=Page[EntityMentionRead])
def list_organization_mentions(
    slug: str,
    repo: Repo,
    limit: Limit = DEFAULT_PAGE_SIZE,
    offset: Offset = 0,
    state: MentionState = None,
) -> Page[EntityMentionRead]:
    return _or_404(
        repo.list_entity_mentions("organization", slug, limit=limit, offset=offset, state=state),
        "organization",
    )


@router.get("/witnesses/{code}/mentions", response_model=Page[EntityMentionRead])
def list_witness_mentions(
    code: str,
    repo: Repo,
    limit: Limit = DEFAULT_PAGE_SIZE,
    offset: Offset = 0,
    state: MentionState = None,
) -> Page[EntityMentionRead]:
    return _or_404(
        repo.list_entity_mentions("witness", code, limit=limit, offset=offset, state=state),
        "witness",
    )


@router.get("/exhibits/{exhibit_id}/mentions", response_model=Page[EntityMentionRead])
def list_exhibit_mentions(
    exhibit_id: str,
    repo: Repo,
    limit: Limit = DEFAULT_PAGE_SIZE,
    offset: Offset = 0,
    state: MentionState = None,
) -> Page[EntityMentionRead]:
    return _or_404(
        repo.list_entity_mentions("exhibit", exhibit_id, limit=limit, offset=offset, state=state),
        "exhibit",
    )


# ------------------------------------------------------------- incidents --
@router.get("/incidents", response_model=Page[IncidentRead])
def list_incidents(
    repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
) -> Page[IncidentRead]:
    return repo.list_incidents(limit=limit, offset=offset)


@router.get("/incidents/{slug}", response_model=IncidentRead)
def read_incident(slug: str, repo: Repo) -> IncidentRead:
    return _or_404(repo.get_incident(slug), "incident")


# -------------------------------------------------------------- findings --
@router.get("/findings", response_model=Page[FindingSummary])
def list_findings(
    repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
) -> Page[FindingSummary]:
    return repo.list_findings(limit=limit, offset=offset)


@router.get("/findings/{finding_key}", response_model=FindingDetail)
def read_finding(finding_key: str, repo: Repo) -> FindingDetail:
    return _or_404(repo.get_finding(finding_key), "finding")


@router.get("/findings/{finding_key}/matrix", response_model=FindingDetail)
def read_finding_matrix(finding_key: str, repo: Repo) -> FindingDetail:
    """Queryable finding/evidence matrix with the same fail-closed public view."""
    return _or_404(repo.get_finding(finding_key), "finding")


# ---------------------------------------------------------------- claims --
@router.get("/claims", response_model=Page[ClaimRead])
def list_claims(
    repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
) -> Page[ClaimRead]:
    return repo.list_claims(limit=limit, offset=offset)


@router.get("/claims/{claim_key}", response_model=ClaimRead)
def read_claim(claim_key: str, repo: Repo) -> ClaimRead:
    return _or_404(repo.get_claim(claim_key), "claim")


@router.get("/arguments", response_model=Page[ArgumentRead])
def list_arguments(
    repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
) -> Page[ArgumentRead]:
    return repo.list_arguments(limit=limit, offset=offset)


# ---------------------------------------------------------------- events --
@router.get("/events", response_model=Page[EventRead])
def list_events(
    repo: Repo, limit: Limit = DEFAULT_PAGE_SIZE, offset: Offset = 0
) -> Page[EventRead]:
    return repo.list_events(limit=limit, offset=offset)


# ----------------------------------------------------------- transcripts --
@router.get("/transcripts/{official_ref:path}", response_model=TranscriptRead)
def read_transcript(official_ref: str, repo: Repo) -> TranscriptRead:
    return _or_404(repo.get_transcript(official_ref), "transcript")


# ------------------------------------------------------------- citations --
@router.get("/citations/resolve", response_model=ResolveResult)
def resolve_identifier(
    repo: Repo, ref: Annotated[str, Query(min_length=1, max_length=128)]
) -> ResolveResult:
    return repo.resolve_identifier(ref)


@router.get("/citations/{citation_id}", response_model=CitationRead)
def read_citation(citation_id: uuid.UUID, repo: Repo) -> CitationRead:
    return _or_404(repo.get_citation(citation_id), "citation")


# --------------------------------------------------------------- network --
@router.get("/network", response_model=NetworkRead)
def read_network(
    repo: Repo,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
    focus_ref: Annotated[str | None, Query(max_length=255)] = None,
    source_category: str | None = None,
    verification_state: VerificationState | None = None,
    relationship_type: RelationshipType | None = None,
    entity_kind: EntityKind | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> NetworkRead:
    return repo.network(
        limit=limit,
        focus_ref=focus_ref,
        source_category=source_category,
        verification_state=verification_state,
        relationship_type=relationship_type,
        entity_kind=entity_kind,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/network/path", response_model=EvidencePathRead)
def read_evidence_path(
    repo: Repo,
    from_node_id: uuid.UUID,
    to_node_id: uuid.UUID,
    max_hops: Annotated[int, Query(ge=1, le=8)] = 6,
) -> EvidencePathRead:
    return repo.evidence_path(from_node_id=from_node_id, to_node_id=to_node_id, max_hops=max_hops)


@router.get("/relationships", response_model=Page[RelationshipRead])
def list_relationships(
    repo: Repo,
    node_id: uuid.UUID | None = None,
    limit: Limit = DEFAULT_PAGE_SIZE,
    offset: Offset = 0,
) -> Page[RelationshipRead]:
    return repo.list_relationships(node_id=node_id, limit=limit, offset=offset)


# ---------------------------------------------------------------- search --
@router.get("/search", response_model=SearchRead)
def search(
    repo: Repo,
    q: Annotated[str, Query(max_length=200)] = "",
    mode: Annotated[str, Query(pattern="^(auto|exact|phrase|keyword)$")] = "auto",
    document_type: str | None = None,
    language: str | None = None,
    filing_party: Party | None = None,
    source_type: Annotated[
        str | None, Query(pattern="^(document|transcript|court|spo|defence)$")
    ] = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> SearchRead:
    return repo.search(
        q,
        mode=mode,
        document_type=document_type,
        language=language,
        filing_party=filing_party,
        source_type=source_type,
        date_from=date_from,
        date_to=date_to,
    )
