"""Audited citation-first AI research endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.config import Settings, get_settings
from ksc_api.db.session import get_session
from ksc_api.models import Case
from ksc_api.schemas.ai import (
    AiNoteCreate,
    AiNoteRead,
    AiQuestionCreate,
    AiRunRead,
    AiRunSummary,
    run_read,
)
from ksc_api.services.ai_providers import ProviderError
from ksc_api.services.ai_research import AiResearchService

router = APIRouter(prefix="/api/v1/ai", tags=["ai-research"])


def get_ai_service(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AiResearchService:
    case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
    if case is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "configured case is not seeded")
    try:
        return AiResearchService(session, case, settings)
    except ProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


Service = Annotated[AiResearchService, Depends(get_ai_service)]


@router.post("/runs", response_model=AiRunRead, status_code=status.HTTP_201_CREATED)
def create_ai_run(payload: AiQuestionCreate, service: Service) -> AiRunRead:
    try:
        return run_read(service.create_run(payload.question))
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("/runs/{run_id}", response_model=AiRunRead)
def read_ai_run(run_id: uuid.UUID, service: Service) -> AiRunRead:
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "AI run not found")
    return run_read(run)


@router.get("/runs", response_model=list[AiRunSummary])
def list_ai_runs(
    service: Service, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> list[AiRunSummary]:
    return [
        AiRunSummary(
            id=run.id,
            question=run.question or "",
            status=run.status,
            answer_withheld=run.answer_withheld,
            created_at=run.created_at,
        )
        for run in service.list_runs(limit)
    ]


@router.post("/runs/{run_id}/notes", response_model=AiNoteRead, status_code=status.HTTP_201_CREATED)
def save_ai_research_note(run_id: uuid.UUID, payload: AiNoteCreate, service: Service) -> AiNoteRead:
    try:
        note = service.save_research_note(run_id, payload.title)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return AiNoteRead(
        id=note.id,
        title=note.title,
        provenance="ai_assisted",
        origin_ai_run_id=run_id,
    )
