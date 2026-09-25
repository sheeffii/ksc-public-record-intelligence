"""Public read API, v1. Every route reads through `RecordRepository`, which
scopes to the configured case and fails closed on visibility."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response, status
from minio import Minio
from minio.error import S3Error
from starlette.responses import StreamingResponse

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
    EdgePageRead,
    EntityMentionRead,
    EventRead,
    EvidencePathRead,
    ExhibitRead,
    ExhibitStatusEventRead,
    FindingDetail,
    FindingSummary,
    IncidentRead,
    LocalSearchRead,
    NetworkRead,
    OrganizationRead,
    PageContextRead,
    PersonRead,
    ReaderSegmentPage,
    RelationshipRead,
    SearchRead,
    SourceAnchorRead,
    TranscriptOutlineRead,
    TranscriptRead,
    WitnessAppearanceRead,
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


def _byte_range(value: str | None, size: int) -> tuple[int, int] | None:
    if value is None:
        return None
    if not value.startswith("bytes=") or "," in value:
        raise ValueError("only one byte range is supported")
    start_text, separator, end_text = value[6:].partition("-")
    if not separator:
        raise ValueError("invalid byte range")
    if not start_text:
        length = int(end_text)
        if length <= 0:
            raise ValueError("invalid byte range")
        return max(0, size - length), size - 1
    start = int(start_text)
    end = min(int(end_text), size - 1) if end_text else size - 1
    if start < 0 or start >= size or end < start:
        raise ValueError("invalid byte range")
    return start, end


@router.get("/document-versions/{version_ref:path}/artifact")
@router.head("/document-versions/{version_ref:path}/artifact", include_in_schema=False)
def read_document_artifact(version_ref: str, request: Request, repo: Repo) -> Response:
    """Range-serve only the exact stored bytes of one public version."""
    version = repo.public_version(version_ref)
    if (
        version is None
        or version.artifact_status.value != "fetched"
        or version.storage_key is None
        or version.sha256 is None
        or version.byte_size is None
        or version.byte_size <= 0
        or version.mime_type != "application/pdf"
        or not version.storage_key.endswith(f"/{version.sha256}.pdf")
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="public PDF artifact not found")
    from ksc_api.config import get_settings

    settings = get_settings()
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    try:
        stored = client.stat_object(settings.minio_bucket_documents, version.storage_key)
        if stored.size != version.byte_size or stored.content_type != "application/pdf":
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="stored PDF identity does not match its record"
            )
        selected = _byte_range(request.headers.get("range"), version.byte_size)
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="public PDF artifact not found"
            ) from exc
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail="PDF storage unavailable") from exc
    except (ValueError, TypeError):
        return Response(status_code=416, headers={"Content-Range": f"bytes */{version.byte_size}"})
    start, end = selected or (0, version.byte_size - 1)
    length = end - start + 1
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "Content-Disposition": "inline",
        "ETag": f'"{version.sha256}"',
        "Cache-Control": "public, max-age=31536000, immutable",
        "Access-Control-Expose-Headers": "Accept-Ranges, Content-Range, Content-Length, ETag",
    }
    response_status = 206 if selected is not None else 200
    if selected is not None:
        headers["Content-Range"] = f"bytes {start}-{end}/{version.byte_size}"
    if request.method == "HEAD":
        return Response(status_code=response_status, media_type="application/pdf", headers=headers)

    stream = client.get_object(
        settings.minio_bucket_documents, version.storage_key, offset=start, length=length
    )

    def body() -> Iterator[bytes]:
        try:
            yield from stream.stream(64 * 1024)
        finally:
            stream.close()
            stream.release_conn()

    return StreamingResponse(
        body(), status_code=response_status, media_type="application/pdf", headers=headers
    )


# ------------------------------------------------ Phase 20B Reader reads --
@router.get(
    "/document-versions/{version_ref:path}/transcript", response_model=TranscriptOutlineRead
)
def read_transcript_outline(version_ref: str, repo: Repo) -> TranscriptOutlineRead:
    """Hearing/session, printed page-header subjects/examinations and speakers
    of one exact transcript version. Bounded by that version's own pages."""
    return _or_404(repo.transcript_outline(version_ref), "transcript version")


@router.get(
    "/document-versions/{version_ref:path}/transcript/segments", response_model=ReaderSegmentPage
)
def list_transcript_segments(
    version_ref: str,
    repo: Repo,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Offset = 0,
    pdf_page_index: Annotated[int | None, Query(ge=0)] = None,
    page: Annotated[int | None, Query(ge=1)] = None,
    line: Annotated[int | None, Query(ge=1)] = None,
    segment: uuid.UUID | None = None,
    speaker: Annotated[str | None, Query(max_length=255)] = None,
    subject: Annotated[str | None, Query(max_length=255)] = None,
    examination: Annotated[str | None, Query(max_length=255)] = None,
    q: Annotated[str | None, Query(min_length=2, max_length=200)] = None,
) -> ReaderSegmentPage:
    return _or_404(
        repo.transcript_segments(
            version_ref,
            limit=limit,
            offset=offset,
            pdf_page_index=pdf_page_index,
            page=page,
            line=line,
            segment_id=segment,
            speaker=speaker,
            subject=subject,
            examination=examination,
            q=q,
        ),
        "transcript version",
    )


@router.get(
    "/document-versions/{version_ref:path}/pages/{pdf_page_index}/context",
    response_model=PageContextRead,
)
def read_page_context(
    version_ref: str,
    pdf_page_index: Annotated[int, Path(ge=0)],
    repo: Repo,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> PageContextRead:
    """Source-anchored research objects on one PDF page of one exact version."""
    return _or_404(repo.page_context(version_ref, pdf_page_index, limit=limit), "document page")


@router.get("/document-versions/{version_ref:path}/source-search", response_model=LocalSearchRead)
def search_version_source(
    version_ref: str,
    repo: Repo,
    q: Annotated[str, Query(max_length=200)] = "",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> LocalSearchRead:
    """Lexical matches inside one version. Every hit is a SEARCH_MATCH."""
    return _or_404(repo.local_search(version_ref, q, limit=limit), "document version")


@router.get("/source-anchors/{anchor_id}", response_model=SourceAnchorRead)
def read_source_anchor(anchor_id: uuid.UUID, repo: Repo) -> SourceAnchorRead:
    return _or_404(repo.get_source_anchor(anchor_id), "source anchor")


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


@router.get("/network/edges", response_model=EdgePageRead)
def list_network_edges(
    repo: Repo,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    cursor: uuid.UUID | None = None,
    focus_ref: str | None = None,
    relationship_type: RelationshipType | None = None,
    entity_kind: EntityKind | None = None,
    evidence_kind: Literal["citation", "entity_occurrence", "witness_appearance"] | None = None,
    document_ref: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> EdgePageRead:
    """Bounded, cursor-paginated evidence edges with one exact provenance each."""
    return repo.network_edges(
        limit=limit,
        cursor=str(cursor) if cursor else None,
        focus_ref=focus_ref,
        relationship_type=relationship_type,
        entity_kind=entity_kind,
        evidence_kind=evidence_kind,
        document_ref=document_ref,
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


# ------------------------------------------------ appearances / status --
@router.get("/witnesses/{code}/appearances", response_model=list[WitnessAppearanceRead])
def list_witness_appearances(code: str, repo: Repo) -> list[WitnessAppearanceRead]:
    return _or_404(repo.list_appearances("witness", code), "witness")


@router.get("/people/{slug}/appearances", response_model=list[WitnessAppearanceRead])
def list_person_appearances(slug: str, repo: Repo) -> list[WitnessAppearanceRead]:
    return _or_404(repo.list_appearances("person", slug), "person")


@router.get("/exhibits/{exhibit_id}/status-events", response_model=list[ExhibitStatusEventRead])
def list_exhibit_status_events(exhibit_id: str, repo: Repo) -> list[ExhibitStatusEventRead]:
    return _or_404(repo.list_exhibit_status_events(exhibit_id), "exhibit")
