"""Database, migration, pgvector and seed verification against a live PostgreSQL."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, select, text

pytestmark = pytest.mark.integration


def test_database_connectivity(engine):
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1


def test_pgvector_extension_is_enabled(engine):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).first()
    assert row is not None, "pgvector extension is not installed in the test database"


def test_pgvector_can_compute_a_distance(engine):
    with engine.connect() as conn:
        distance = conn.execute(text("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector")).scalar()
    assert distance == pytest.approx(1.0)


def test_migration_created_minimal_tables(engine):
    names = set(inspect(engine).get_table_names())
    assert {"cases", "documents", "audit_log", "alembic_version"} <= names


def test_migration_is_at_head(engine):
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version == "0010"


def test_seed_case_is_idempotent(integration_settings):
    from ksc_api.db.session import session_scope
    from ksc_api.models import Case, Document
    from ksc_api.seed import seed_case

    with session_scope() as session:
        first, _ = seed_case(session)
        first_id = first.id
    with session_scope() as session:
        second, created = seed_case(session)
        assert created is False
        assert second.id == first_id
        real_cases = session.scalars(select(Case).where(Case.case_number == "KSC-BC-2020-06")).all()
        assert len(real_cases) == 1
        # Nothing is ingested for the real case before Phase 7.
        assert session.scalars(select(Document).where(Document.case_id == first_id)).all() == []


def test_seed_writes_an_audit_entry(integration_settings):
    from ksc_api.db.session import session_scope
    from ksc_api.models import AuditLog
    from ksc_api.seed import seed_case

    with session_scope() as session:
        seed_case(session)
    with session_scope() as session:
        entries = (
            session.execute(select(AuditLog).where(AuditLog.action == "case.seeded"))
            .scalars()
            .all()
        )
    assert len(entries) == 1
    assert entries[0].entity_id == "KSC-BC-2020-06"


def test_database_readiness_check_passes(integration_settings):
    from ksc_api.services.readiness import check_database, check_pgvector

    assert check_database(integration_settings).ok
    assert check_pgvector(integration_settings).ok
