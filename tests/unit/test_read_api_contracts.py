"""Read-API contracts that need no database: pagination bounds, route
registration, and the 503 when the configured case is not seeded."""

from __future__ import annotations

from ksc_api.repositories import records
from ksc_api.schemas.common import MAX_PAGE_SIZE, Page
from ksc_api.schemas.records import DocumentSummary


def test_page_rejects_out_of_range_limits():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Page[DocumentSummary](items=[], total=0, limit=0, offset=0)
    with pytest.raises(ValidationError):
        Page[DocumentSummary](items=[], total=0, limit=MAX_PAGE_SIZE + 1, offset=0)
    with pytest.raises(ValidationError):
        Page[DocumentSummary](items=[], total=0, limit=10, offset=-1)


def test_read_routes_are_registered_under_v1(client):
    # Read the OpenAPI schema: FastAPI now mounts included routers lazily.
    paths = set(client.get("/openapi.json").json()["paths"])
    expected = {
        "/api/v1/case",
        "/api/v1/documents",
        "/api/v1/documents/{ref}",
        "/api/v1/document-versions/{version_ref}/pages",
        "/api/v1/document-versions/{version_ref}/chunks",
        "/api/v1/document-versions/{version_ref}/paragraphs",
        "/api/v1/people",
        "/api/v1/people/{slug}",
        "/api/v1/witnesses",
        "/api/v1/witnesses/{code}",
        "/api/v1/exhibits",
        "/api/v1/exhibits/{exhibit_id}",
        "/api/v1/incidents",
        "/api/v1/incidents/{slug}",
        "/api/v1/findings",
        "/api/v1/findings/{finding_key}",
        "/api/v1/claims",
        "/api/v1/claims/{claim_key}",
        "/api/v1/arguments",
        "/api/v1/events",
        "/api/v1/transcripts/{official_ref}",
        "/api/v1/citations/resolve",
        "/api/v1/citations/{citation_id}",
        "/api/v1/network",
        "/api/v1/relationships",
        "/api/v1/search",
    }
    assert expected <= paths


def test_pagination_query_bounds_are_enforced(client):
    client.app.dependency_overrides[records.get_repository] = lambda: None
    assert client.get("/api/v1/documents?limit=0").status_code == 422
    assert client.get(f"/api/v1/documents?limit={MAX_PAGE_SIZE + 1}").status_code == 422
    assert client.get("/api/v1/documents?offset=-1").status_code == 422


def test_unseeded_case_is_a_503_not_a_crash(client):
    def missing_case() -> None:
        raise records.CaseNotConfiguredError("KSC-BC-2020-06")

    client.app.dependency_overrides[records.get_repository] = missing_case
    try:
        response = client.get("/api/v1/case")
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 503
    assert "not seeded" in response.json()["detail"]
