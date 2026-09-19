"""Unit tests for /health, /version and the /ready aggregation logic.

No infrastructure is contacted: readiness checks are replaced with stubs.
"""

from __future__ import annotations

import pytest

from ksc_api import __version__
from ksc_api.services import readiness
from ksc_api.services.readiness import ComponentStatus


def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_reports_package_and_case(client):
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "ksc-api"
    assert body["version"] == __version__
    assert body["case_id"] == "KSC-BC-2020-06"
    assert "git_sha" in body
    assert body["environment"] == "test"


def test_ready_reports_ready_when_all_components_ok(client, monkeypatch: pytest.MonkeyPatch):
    def fake_run_checks(settings, checks=None):
        return [
            ComponentStatus("database", True),
            ComponentStatus("pgvector", True, "vector 0.8.0"),
            ComponentStatus("redis", True),
            ComponentStatus("minio", True),
        ]

    monkeypatch.setattr(readiness, "run_checks", fake_run_checks)
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert [c["name"] for c in body["components"]] == ["database", "pgvector", "redis", "minio"]


def test_ready_returns_503_and_names_failing_component(client, monkeypatch: pytest.MonkeyPatch):
    def fake_run_checks(settings, checks=None):
        return [
            ComponentStatus("database", True),
            ComponentStatus("pgvector", False, "extension not installed"),
            ComponentStatus("redis", True),
            ComponentStatus("minio", False, "bucket 'ksc-documents' missing"),
        ]

    monkeypatch.setattr(readiness, "run_checks", fake_run_checks)
    response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    failing = {c["name"]: c["detail"] for c in body["components"] if not c["ok"]}
    assert failing == {
        "pgvector": "extension not installed",
        "minio": "bucket 'ksc-documents' missing",
    }


def test_cors_allows_configured_frontend_origin(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
