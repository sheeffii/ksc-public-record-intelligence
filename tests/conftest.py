"""Shared pytest configuration.

Unit tests never touch the network. Integration tests (tests/integration)
require a live PostgreSQL with pgvector, Redis and MinIO — normally the
docker-compose stack. They create and migrate a throwaway `ksc_test` database.
"""

from __future__ import annotations

import os

import pytest

# Force predictable settings before the app imports them. Values can be
# overridden by the environment (e.g. docker-compose or CI).
os.environ["APP_ENV"] = "test"
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://ksc:ksc_dev_password@localhost:5432/ksc"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from ksc_api.main import create_app

    with TestClient(create_app()) as c:
        yield c
