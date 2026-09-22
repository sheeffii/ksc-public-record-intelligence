"""Internal data-status endpoint (Phase 7). Not part of the public research
surface; shows what ingestion holds, refused and failed, with provenance."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ksc_api.repositories.ingestion import IngestionStatusRepository, get_ingestion_repository
from ksc_api.schemas.ingestion import IngestionStatusRead
from ksc_api.security import Verifier

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])

Repo = Annotated[IngestionStatusRepository, Depends(get_ingestion_repository)]


@router.get("/status", response_model=IngestionStatusRead)
def read_ingestion_status(
    _: Verifier, repo: Repo, jobs: Annotated[int, Query(ge=1, le=100)] = 20
) -> IngestionStatusRead:
    return repo.status(job_limit=jobs)
