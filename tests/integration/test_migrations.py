"""Migration path: 0001 → 0002 → 0003 preserves Phase 4 data; downgrade and
re-upgrade are clean; the models match the migrated schema exactly.

Runs last among the data tests (file name) and leaves the database at head.
"""

from __future__ import annotations

import uuid

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from tests.integration.conftest import API_DIR

pytestmark = pytest.mark.integration


def _alembic() -> Config:
    return Config(str(API_DIR / "alembic.ini"))


def test_upgrade_from_phase4_preserves_case_document_and_audit_rows(migrated_database_url):
    cfg = _alembic()
    engine = create_engine(migrated_database_url, isolation_level="AUTOCOMMIT")
    try:
        command.downgrade(cfg, "0001")
        case_id, document_id = uuid.uuid4(), uuid.uuid4()
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM documents"))
            conn.execute(text("DELETE FROM cases"))
            conn.execute(
                text(
                    "INSERT INTO cases (id, case_number, title, court) "
                    "VALUES (:id, 'KSC-MIG-TEST', 'migration test', 'test court')"
                ),
                {"id": case_id},
            )
            conn.execute(
                text(
                    "INSERT INTO documents (id, case_id, official_ref, title, document_type, "
                    "public_state, ingestion_state) VALUES (:id, :case_id, 'KSC-MIG-TEST/F1', "
                    "'doc', 'filing', 'not_held', 'discovered')"
                ),
                {"id": document_id, "case_id": case_id},
            )
            conn.execute(
                text("INSERT INTO audit_log (id, action) VALUES (:id, 'migration.test')"),
                {"id": uuid.uuid4()},
            )

        command.upgrade(cfg, "head")

        with engine.connect() as conn:
            assert conn.execute(text("SELECT count(*) FROM cases")).scalar() == 1
            assert (
                conn.execute(
                    text("SELECT visibility FROM documents WHERE id = :id"), {"id": document_id}
                ).scalar()
                == "not_public"
            )
            assert (
                conn.execute(
                    text("SELECT count(*) FROM audit_log WHERE action = 'migration.test'")
                ).scalar()
                == 1
            )
            columns = {c["name"] for c in inspect(engine).get_columns("documents")}
            assert {"visibility", "filing_party", "public_date"} <= columns
            assert not {"public_state", "storage_key", "sha256", "page_count"} & columns
            conn.execute(text("DELETE FROM documents"))
            conn.execute(text("DELETE FROM cases WHERE case_number = 'KSC-MIG-TEST'"))
    finally:
        engine.dispose()


def test_models_match_the_migrated_schema(engine):
    import ksc_api.models  # noqa: F401
    from ksc_api.db.base import Base

    with engine.connect() as conn:
        context = MigrationContext.configure(conn, opts={"compare_type": True})
        diff = compare_metadata(context, Base.metadata)
    assert diff == [], diff


def test_downgrade_to_base_and_reupgrade(migrated_database_url):
    cfg = _alembic()
    engine = create_engine(migrated_database_url)
    try:
        command.downgrade(cfg, "base")
        assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
        with engine.connect() as conn:
            enum_types = (
                conn.execute(text("SELECT typname FROM pg_type WHERE typtype = 'e'"))
                .scalars()
                .all()
            )
        assert enum_types == []
        command.upgrade(cfg, "head")
        assert {"cases", "documents", "audit_log", "citations", "relationships"} <= set(
            inspect(engine).get_table_names()
        )
        with engine.connect() as conn:
            assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0003"
    finally:
        engine.dispose()
