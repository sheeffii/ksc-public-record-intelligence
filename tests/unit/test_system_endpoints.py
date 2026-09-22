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


def test_api_responses_have_security_headers_and_request_limit(client):
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]

    refused = client.get("/health", headers={"content-length": str(10 * 1024 * 1024 + 1)})
    assert refused.status_code == 413


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


def test_metrics_exposes_request_counters_latency_and_build_info(client):
    from ksc_api.observability import request_metrics

    request_metrics.reset()
    client.get("/health")
    client.get("/version")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain; version=0.0.4")
    body = response.text
    assert 'ksc_http_requests_total{method="GET",route="/health",status="200"} 1' in body
    assert 'ksc_http_requests_total{method="GET",route="/version",status="200"} 1' in body
    assert (
        'ksc_http_request_duration_seconds_bucket{method="GET",route="/health",le="+Inf"} 1' in body
    )
    assert 'ksc_http_request_duration_seconds_count{method="GET",route="/health"} 1' in body
    assert f'ksc_build_info{{version="{__version__}",git_sha=' in body
    assert "ksc_process_uptime_seconds " in body
    # The DB-backed gauges either scraped (1) or were skipped without failing (0).
    assert "ksc_metrics_db_scrape_ok 0" in body or "ksc_metrics_db_scrape_ok 1" in body
    if "ksc_metrics_db_scrape_ok 1" in body:
        assert "ksc_source_records " in body and 'ksc_quarantine{state="open"} ' in body
    assert "X-Request-ID" in response.headers or "x-request-id" in response.headers


def test_metrics_labels_use_route_templates_not_raw_paths(client):
    from ksc_api.observability import request_metrics

    request_metrics.reset()
    client.get("/api/v1/documents/KSC-BC-2020-06%2FF00001")
    body = client.get("/metrics").text
    assert "F00001" not in body
    assert 'route="unmatched"' in body or 'route="/api/v1/documents/{' in body


def test_json_log_formatter_emits_structured_fields_only(caplog):
    import json
    import logging

    from ksc_api.logging_config import JsonFormatter

    record = logging.LogRecord("ksc_api.access", logging.INFO, __file__, 1, "request", (), None)
    record.request_id = "abc"
    record.route = "/api/v1/search"
    record.status = 200
    record.duration_ms = 1.5
    payload = json.loads(JsonFormatter().format(record))
    assert payload["msg"] == "request" and payload["level"] == "INFO"
    assert payload["route"] == "/api/v1/search" and payload["status"] == 200
    assert payload["request_id"] == "abc" and "ts" in payload
    assert "args" not in payload and "query" not in payload
