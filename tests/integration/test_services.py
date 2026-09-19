"""Redis and MinIO connectivity through the readiness checks."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_redis_readiness(integration_settings):
    from ksc_api.services.readiness import check_redis

    status = check_redis(integration_settings)
    assert status.ok, status.detail


def test_minio_readiness(integration_settings):
    from ksc_api.services.readiness import check_minio

    status = check_minio(integration_settings)
    assert status.ok, status.detail


def test_ready_endpoint_end_to_end(integration_settings):
    from fastapi.testclient import TestClient

    from ksc_api.main import create_app

    with TestClient(create_app()) as client:
        response = client.get("/ready")
    assert response.status_code == 200, response.json()
    assert response.json()["status"] == "ready"
