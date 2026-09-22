"""External public sources: read-only, case-scoped and separate from court records."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.config import Settings, get_settings
from ksc_api.db.session import get_session
from ksc_api.models import COURT_MEDIA_STATUSES, Case
from ksc_api.schemas.media import (
    MediaComparisonRead,
    MediaItemRead,
    MediaNetworkRead,
    MediaTimelineEvent,
    MediaWorkspaceRead,
)
from ksc_api.services.media_research import MediaResearchService

router = APIRouter(prefix="/api/v1/media", tags=["external-public-sources"])


def get_media_service(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MediaResearchService:
    case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
    if case is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "configured case is not seeded")
    return MediaResearchService(session, case)


Service = Annotated[MediaResearchService, Depends(get_media_service)]


@router.get("", response_model=MediaWorkspaceRead)
def list_media(
    service: Service,
    q: Annotated[str | None, Query(max_length=200)] = None,
    court_status: Annotated[str | None, Query()] = None,
    source_type: Annotated[str | None, Query(max_length=64)] = None,
    language: Annotated[str | None, Query(max_length=16)] = None,
) -> MediaWorkspaceRead:
    if court_status is not None and court_status not in COURT_MEDIA_STATUSES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown court status")
    return service.workspace(
        q=q, court_status=court_status, source_type=source_type, language=language
    )


@router.get("/timeline", response_model=list[MediaTimelineEvent])
def media_timeline(service: Service) -> list[MediaTimelineEvent]:
    return service.timeline()


@router.get("/network", response_model=MediaNetworkRead)
def media_network(service: Service) -> MediaNetworkRead:
    return service.network()


@router.get("/comparisons", response_model=list[MediaComparisonRead])
def media_comparisons(service: Service) -> list[MediaComparisonRead]:
    return service.comparisons()


@router.get("/{item_id}", response_model=MediaItemRead)
def read_media_item(item_id: uuid.UUID, service: Service) -> MediaItemRead:
    item = service.item(item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "external media item not found")
    return item
