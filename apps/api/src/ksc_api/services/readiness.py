"""Readiness checks for the infrastructure the API depends on.

Each check returns a `ComponentStatus`. `/ready` aggregates them and answers
503 if any required component is down. Checks are deliberately cheap.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from minio import Minio
from redis import Redis
from sqlalchemy import text

from ksc_api.config import Settings
from ksc_api.db.session import get_engine

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ComponentStatus:
    name: str
    ok: bool
    detail: str | None = None


def check_database(_: Settings) -> ComponentStatus:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return ComponentStatus("database", True)
    except Exception as exc:  # noqa: BLE001 - report any failure as not-ready
        log.warning("database readiness check failed: %s", type(exc).__name__)
        return ComponentStatus("database", False, type(exc).__name__)


def check_pgvector(_: Settings) -> ComponentStatus:
    try:
        with get_engine().connect() as conn:
            row = conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            ).first()
        if row is None:
            return ComponentStatus("pgvector", False, "extension not installed")
        return ComponentStatus("pgvector", True, f"vector {row[0]}")
    except Exception as exc:  # noqa: BLE001
        log.warning("pgvector readiness check failed: %s", type(exc).__name__)
        return ComponentStatus("pgvector", False, type(exc).__name__)


def check_redis(settings: Settings) -> ComponentStatus:
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        try:
            pong = client.ping()
        finally:
            client.close()
        return ComponentStatus("redis", bool(pong))
    except Exception as exc:  # noqa: BLE001
        log.warning("redis readiness check failed: %s", type(exc).__name__)
        return ComponentStatus("redis", False, type(exc).__name__)


def check_minio(settings: Settings) -> ComponentStatus:
    try:
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        exists = client.bucket_exists(settings.minio_bucket_documents)
        detail = None if exists else f"bucket '{settings.minio_bucket_documents}' missing"
        return ComponentStatus("minio", exists, detail)
    except Exception as exc:  # noqa: BLE001
        log.warning("minio readiness check failed: %s", type(exc).__name__)
        return ComponentStatus("minio", False, type(exc).__name__)


ReadinessCheck = Callable[[Settings], ComponentStatus]

DEFAULT_CHECKS: tuple[ReadinessCheck, ...] = (
    check_database,
    check_pgvector,
    check_redis,
    check_minio,
)


def run_checks(
    settings: Settings, checks: tuple[ReadinessCheck, ...] = DEFAULT_CHECKS
) -> list[ComponentStatus]:
    return [check(settings) for check in checks]
