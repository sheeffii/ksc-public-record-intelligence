"""Citation-first AI research API contracts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from ksc_api.models import AiRun, AiRunStatus
from ksc_api.schemas.common import ReadModel

AiSourceCategory = Literal[
    "court_finding",
    "witness_testimony",
    "spo_argument",
    "defence_argument",
    "document_exhibit",
    "court_response",
    "human_note",
]
AiBlockKind = Literal[
    "court",
    "evidence",
    "testimony",
    "spo",
    "defence",
    "court_response",
    "human_note",
    "ai",
]


class AiQuestionCreate(ReadModel):
    question: str = Field(min_length=3, max_length=2000)


class AiNoteCreate(ReadModel):
    title: str = Field(min_length=1, max_length=300)


class AiNoteRead(ReadModel):
    id: uuid.UUID
    title: str
    provenance: Literal["ai_assisted"]
    origin_ai_run_id: uuid.UUID


class AiValidationErrorRead(ReadModel):
    code: str
    detail: str
    claim_index: int | None = None


class AiSourceRead(ReadModel):
    id: uuid.UUID
    rank: int = Field(ge=1)
    retrieval_method: str
    retrieval_score: float = Field(ge=0)
    category: AiSourceCategory
    visibility: str
    ref: str
    version_ref: str | None
    display: str
    target_path: str
    source_url: str | None
    excerpt: str
    excerpt_sha256: str
    page_from: int | None
    page_to: int | None
    pdf_page_index: int | None
    para_from: int | None
    para_to: int | None
    line_from: int | None
    line_to: int | None
    verification_state: str
    verification_reviewed_by: str | None
    verification_reviewed_at: datetime | None
    metadata: dict[str, Any] | None


class AiAnswerBlockRead(ReadModel):
    id: uuid.UUID
    sequence: int = Field(ge=0)
    kind: AiBlockKind
    content_type: str
    text: str
    verification_state: str
    sources: list[AiSourceRead]


class AiCitationStatusRead(ReadModel):
    produced: int = Field(ge=0)
    resolved: int = Field(ge=0)
    quotations_matched: int = Field(ge=0)
    unresolved: int = Field(ge=0)
    human_verified_sources: int = Field(ge=0)
    unreviewed_sources: int = Field(ge=0)


class AiRunRead(ReadModel):
    id: uuid.UUID
    question: str
    provider: str
    model: str
    prompt_name: str
    prompt_version: int
    system_prompt_sha256: str
    parameters: dict[str, Any]
    status: AiRunStatus
    created_at: datetime
    finished_at: datetime | None
    answer_withheld: bool
    insufficient_evidence: bool
    sources: list[AiSourceRead]
    blocks: list[AiAnswerBlockRead]
    citation_status: AiCitationStatusRead
    validation_errors: list[AiValidationErrorRead]
    gaps: list[str]


class AiRunSummary(ReadModel):
    id: uuid.UUID
    question: str
    status: AiRunStatus
    answer_withheld: bool
    created_at: datetime


def source_read(source: Any) -> AiSourceRead:
    return AiSourceRead(
        id=source.id,
        rank=source.rank,
        retrieval_method=source.retrieval_method,
        retrieval_score=float(source.retrieval_score),
        category=source.source_category,
        visibility=source.source_visibility,
        ref=source.source_ref,
        version_ref=source.version_ref,
        display=source.display,
        target_path=source.target_path,
        source_url=source.source_url,
        excerpt=source.excerpt,
        excerpt_sha256=source.excerpt_sha256,
        page_from=source.page_from,
        page_to=source.page_to,
        pdf_page_index=source.pdf_page_index,
        para_from=source.para_from,
        para_to=source.para_to,
        line_from=source.line_from,
        line_to=source.line_to,
        verification_state=source.verification_state,
        verification_reviewed_by=source.verification_reviewed_by,
        verification_reviewed_at=source.verification_reviewed_at,
        metadata=source.source_metadata,
    )


def run_read(run: AiRun) -> AiRunRead:
    sources = [source_read(source) for source in run.retrieval_sources]
    by_id = {source.id: source for source in sources}
    blocks = (
        []
        if run.answer_withheld
        else [
            AiAnswerBlockRead(
                id=output.id,
                sequence=output.sequence,
                kind=output.kind.value,
                content_type=output.content_type,
                text=output.text,
                verification_state=output.verification_state.value,
                sources=[by_id[source.id] for source in output.sources],
            )
            for output in run.outputs
        ]
    )
    errors = [AiValidationErrorRead.model_validate(error) for error in run.validation_errors or []]
    matched = sum(block.content_type == "verbatim_quote" for block in blocks)
    gaps = [error.detail for error in errors]
    return AiRunRead(
        id=run.id,
        question=run.question or "",
        provider=run.provider,
        model=run.model,
        prompt_name=run.prompt_version.name if run.prompt_version else "unknown",
        prompt_version=run.prompt_version.version if run.prompt_version else 0,
        system_prompt_sha256=run.system_prompt_sha256 or "",
        parameters=run.parameters or {},
        status=run.status,
        created_at=run.created_at,
        finished_at=run.finished_at,
        answer_withheld=run.answer_withheld,
        insufficient_evidence=run.insufficient_evidence,
        sources=sources,
        blocks=blocks,
        citation_status=AiCitationStatusRead(
            produced=sum(len(block.sources) for block in blocks),
            resolved=sum(len(block.sources) for block in blocks),
            quotations_matched=matched,
            unresolved=0 if not run.answer_withheld else len(errors),
            human_verified_sources=sum(
                source.verification_state == "human_verified" for source in sources
            ),
            unreviewed_sources=sum(
                source.verification_state != "human_verified" for source in sources
            ),
        ),
        validation_errors=errors,
        gaps=gaps,
    )
