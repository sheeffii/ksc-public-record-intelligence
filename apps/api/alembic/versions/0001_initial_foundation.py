"""initial foundation: pgvector, cases, documents, audit_log

Revision ID: 0001
Revises:
Create Date: 2026-09-19

Phase 4 minimal schema. The full evidence schema (witnesses, exhibits,
findings, citations, resolution index, …) is planned in docs/DATA_MODEL.md and
is intentionally absent here.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pgvector is enabled now so later phases can add embedding columns without
    # a privileged migration step. No vector column exists yet.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_number", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("court", sa.String(length=255), nullable=False),
        sa.Column("seat", sa.String(length=255), nullable=True),
        sa.Column("official_source_url", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cases")),
        sa.UniqueConstraint("case_number", name=op.f("uq_cases_case_number")),
    )

    document_public_state = postgresql.ENUM(
        "public", "public_redacted", "not_held", name="document_public_state", create_type=False
    )
    document_public_state.create(op.get_bind(), checkfirst=True)
    document_ingestion_state = postgresql.ENUM(
        "discovered",
        "downloaded",
        "parsed",
        "indexed",
        "failed",
        name="document_ingestion_state",
        create_type=False,
    )
    document_ingestion_state.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("official_ref", sa.String(length=128), nullable=False),
        sa.Column("filing_number", sa.String(length=32), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        # Two separate dates. Never merged, never inferred from one another.
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("filing_date", sa.Date(), nullable=True),
        sa.Column("public_state", document_public_state, nullable=False),
        sa.Column("ingestion_state", document_ingestion_state, nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_documents_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint("case_id", "official_ref", name="uq_documents_case_official_ref"),
    )
    op.create_index(op.f("ix_documents_case_id"), "documents", ["case_id"])
    op.create_index(op.f("ix_documents_filing_number"), "documents", ["filing_number"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("actor", sa.String(length=128), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log")),
    )
    op.create_index(op.f("ix_audit_log_occurred_at"), "audit_log", ["occurred_at"])
    op.create_index(op.f("ix_audit_log_action"), "audit_log", ["action"])


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_log_action"), table_name="audit_log")
    op.drop_index(op.f("ix_audit_log_occurred_at"), table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index(op.f("ix_documents_filing_number"), table_name="documents")
    op.drop_index(op.f("ix_documents_case_id"), table_name="documents")
    op.drop_table("documents")
    op.execute("DROP TYPE IF EXISTS document_ingestion_state")
    op.execute("DROP TYPE IF EXISTS document_public_state")
    op.drop_table("cases")
    # The extension is left in place on downgrade; dropping it could affect
    # other schemas in a shared database.
