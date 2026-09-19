"""Integration fixtures: a throwaway, migrated `ksc_test` database.

Requires a reachable PostgreSQL (with the pgvector extension available) at the
host/credentials in DATABASE_URL. The test database is created if missing and
migrated to head with Alembic. It is not dropped afterwards so failures can be
inspected; `make reset-db` removes everything.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, make_url, text

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DIR = REPO_ROOT / "apps" / "api"


def _test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit
    base = make_url(os.environ["DATABASE_URL"])
    return base.set(database="ksc_test").render_as_string(hide_password=False)


def _ensure_database_exists(url: str) -> None:
    parsed = make_url(url)
    admin_url = parsed.set(database="postgres")
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": parsed.database},
            ).first()
            if exists is None:
                conn.execute(text(f'CREATE DATABASE "{parsed.database}"'))
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def migrated_database_url() -> str:
    url = _test_database_url()
    try:
        _ensure_database_exists(url)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            f"PostgreSQL is not reachable for integration tests ({type(exc).__name__}). "
            "Start it with `make up` or set DATABASE_URL."
        )

    os.environ["ALEMBIC_DATABASE_URL"] = url
    cfg = Config(str(API_DIR / "alembic.ini"))
    command.upgrade(cfg, "head")
    return url


@pytest.fixture(scope="session")
def engine(migrated_database_url: str):
    eng = create_engine(migrated_database_url, pool_pre_ping=True)
    yield eng
    eng.dispose()


def _reset_caches() -> None:
    from ksc_api import config
    from ksc_api.db import session as session_module

    config.get_settings.cache_clear()
    session_module.get_engine.cache_clear()
    session_module.get_sessionmaker.cache_clear()


@pytest.fixture
def integration_settings(migrated_database_url: str, monkeypatch: pytest.MonkeyPatch):
    """Point the application at the test database and clear cached engines."""
    from ksc_api import config

    monkeypatch.setenv("DATABASE_URL", migrated_database_url)
    _reset_caches()
    yield config.get_settings()
    _reset_caches()


@pytest.fixture
def demo_settings(migrated_database_url: str, monkeypatch: pytest.MonkeyPatch):
    """Like `integration_settings`, but the configured case is the synthetic
    demo case and its fixture is loaded (idempotently)."""
    from ksc_api import config
    from ksc_api.db.session import session_scope
    from ksc_api.fixtures.demo import DEMO_CASE_NUMBER, load_demo_fixture

    monkeypatch.setenv("DATABASE_URL", migrated_database_url)
    monkeypatch.setenv("CASE_ID", DEMO_CASE_NUMBER)
    _reset_caches()
    with session_scope() as session:
        load_demo_fixture(session)
    yield config.get_settings()
    _reset_caches()


@pytest.fixture
def demo_client(demo_settings):
    from fastapi.testclient import TestClient

    from ksc_api.main import create_app

    with TestClient(create_app()) as client:
        yield client
