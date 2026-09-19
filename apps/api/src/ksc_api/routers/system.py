"""System endpoints: /health, /ready, /version."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from ksc_api import __version__
from ksc_api.config import Settings, get_settings
from ksc_api.services import readiness

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str = "ok"


class ComponentReport(BaseModel):
    name: str
    ok: bool
    detail: str | None = None


class ReadyResponse(BaseModel):
    status: str
    components: list[ComponentReport]


class VersionResponse(BaseModel):
    name: str
    version: str
    git_sha: str
    case_id: str
    environment: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness. Answers as long as the process is up; touches nothing."""
    return HealthResponse()


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadyResponse}},
)
def ready(
    response: Response, settings: Annotated[Settings, Depends(get_settings)]
) -> ReadyResponse:
    """Readiness. Checks PostgreSQL, pgvector, Redis and MinIO."""
    results = readiness.run_checks(settings)
    all_ok = all(r.ok for r in results)
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(
        status="ready" if all_ok else "degraded",
        components=[ComponentReport(name=r.name, ok=r.ok, detail=r.detail) for r in results],
    )


@router.get("/version", response_model=VersionResponse)
def version(settings: Annotated[Settings, Depends(get_settings)]) -> VersionResponse:
    return VersionResponse(
        name="ksc-api",
        version=__version__,
        git_sha=settings.git_sha,
        case_id=settings.case_id,
        environment=settings.app_env,
    )
