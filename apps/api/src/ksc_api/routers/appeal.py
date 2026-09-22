"""Neutral Phase 12 appeal research and statement-comparison endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.config import Settings, get_settings
from ksc_api.db.session import get_session
from ksc_api.models import Case, VerificationState
from ksc_api.schemas.appeal import (
    AppealIssueDetail,
    AppealIssueSummary,
    AppealWorkspaceRead,
    ArgumentLabRead,
    ResearchNoteCreate,
    ResearchNoteCreated,
    ReviewStateUpdate,
    StatementComparisonRead,
)
from ksc_api.security import Researcher, Verifier
from ksc_api.services.appeal_research import AppealResearchService

router = APIRouter(prefix="/api/v1", tags=["appeal-research"])


def get_appeal_service(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AppealResearchService:
    case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
    if case is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "configured case is not seeded")
    return AppealResearchService(session, case)


Service = Annotated[AppealResearchService, Depends(get_appeal_service)]


@router.get("/appeal/issues", response_model=AppealWorkspaceRead)
def list_appeal_issues(
    service: Service,
    category: str | None = None,
    verification_state: VerificationState | None = None,
) -> AppealWorkspaceRead:
    return service.workspace(category=category, verification_state=verification_state)


@router.get("/appeal/issues/{issue_key}", response_model=AppealIssueDetail)
def read_appeal_issue(issue_key: str, service: Service) -> AppealIssueDetail:
    issue = service.get_issue(issue_key)
    if issue is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "appeal issue not found")
    return issue


@router.patch("/appeal/issues/{issue_key}/review", response_model=AppealIssueSummary)
def review_appeal_issue(
    issue_key: str, payload: ReviewStateUpdate, _: Verifier, service: Service
) -> AppealIssueSummary:
    issue = service.update_review_state(
        issue_key, VerificationState(payload.verification_state), payload.reviewer
    )
    if issue is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "appeal issue not found")
    return issue


@router.get("/appeal/issues/{issue_key}/argument-lab", response_model=ArgumentLabRead)
def read_argument_lab(issue_key: str, service: Service) -> ArgumentLabRead:
    lab = service.argument_lab(issue_key)
    if lab is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "appeal issue not found")
    return lab


@router.post(
    "/appeal/issues/{issue_key}/notes",
    response_model=ResearchNoteCreated,
    status_code=status.HTTP_201_CREATED,
)
def save_appeal_note(
    issue_key: str, payload: ResearchNoteCreate, _: Researcher, service: Service
) -> ResearchNoteCreated:
    try:
        note = service.save_note(issue_key, payload)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return ResearchNoteCreated(id=note.id, provenance="human")


@router.get("/statement-comparisons", response_model=list[StatementComparisonRead])
def list_statement_comparisons(
    service: Service,
    issue_key: Annotated[str | None, Query(max_length=64)] = None,
) -> list[StatementComparisonRead]:
    if issue_key is None:
        return service.comparisons()
    issue = service.get_issue(issue_key)
    if issue is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "appeal issue not found")
    return issue.statement_comparisons
