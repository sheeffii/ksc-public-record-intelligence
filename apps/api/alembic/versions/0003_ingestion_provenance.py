"""ingestion provenance: artifact status, fetch provenance, job items

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-20

Phase 7 additions:

- `document_versions.artifact_status` (not_fetched | fetched | failed) so a
  version can exist as metadata only — official detail URL + official
  artifact URL — without its PDF having been fetched. FETCHED is tied to
  `sha256` and `storage_key` by a CHECK. Existing rows holding a hash are
  backfilled to `fetched`.
- `document_versions.byte_size`, `fetched_at`, `fetch_method`: provenance of
  the bytes themselves (discovery provenance stays on `source_records`).
- `ingestion_job_items`: one row per record touched by a job with a terminal
  status, so failures are visible and re-runs resume.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ARTIFACT_STATUS = postgresql.ENUM(
    "not_fetched", "fetched", "failed", name="artifact_status", create_type=False
)
INGESTION_ITEM_STATUS = postgresql.ENUM(
    "pending",
    "downloaded",
    "metadata_only",
    "skipped_duplicate",
    "not_public",
    "failed_download",
    "blocked_by_access_control",
    "invalid_metadata",
    "unsupported_artifact",
    "ambiguous_mapping",
    name="ingestion_item_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    ARTIFACT_STATUS.create(bind, checkfirst=True)
    INGESTION_ITEM_STATUS.create(bind, checkfirst=True)

    # --- document_versions -------------------------------------------------
    op.add_column(
        "document_versions",
        sa.Column("artifact_status", ARTIFACT_STATUS, server_default="not_fetched", nullable=False),
    )
    op.add_column("document_versions", sa.Column("byte_size", sa.BigInteger(), nullable=True))
    op.add_column(
        "document_versions", sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "document_versions", sa.Column("fetch_method", sa.String(length=64), nullable=True)
    )
    op.execute(
        "UPDATE document_versions SET artifact_status = 'fetched' "
        "WHERE sha256 IS NOT NULL AND storage_key IS NOT NULL"
    )
    op.create_check_constraint(
        "fetched_has_hash_and_object",
        "document_versions",
        "(artifact_status = 'fetched') = (sha256 IS NOT NULL AND storage_key IS NOT NULL)",
    )
    op.create_check_constraint(
        "byte_size_non_negative", "document_versions", "byte_size IS NULL OR byte_size >= 0"
    )

    # --- ingestion_job_items -----------------------------------------------
    op.create_table(
        "ingestion_job_items",
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("item_key", sa.String(length=512), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", INGESTION_ITEM_STATUS, server_default="pending", nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_record_id", sa.UUID(), nullable=True),
        sa.Column("document_id", sa.UUID(), nullable=True),
        sa.Column("document_version_id", sa.UUID(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
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
        sa.CheckConstraint(
            "sequence >= 0", name=op.f("ck_ingestion_job_items_sequence_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["ingestion_jobs.id"],
            name=op.f("fk_ingestion_job_items_job_id_ingestion_jobs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_record_id"],
            ["source_records.id"],
            name=op.f("fk_ingestion_job_items_source_record_id_source_records"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_ingestion_job_items_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_ingestion_job_items_document_version_id_document_versions"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_job_items")),
        sa.UniqueConstraint("job_id", "item_key", name="uq_ingestion_job_items_job_key"),
    )
    op.create_index(
        op.f("ix_ingestion_job_items_job_id"), "ingestion_job_items", ["job_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ingestion_job_items_job_id"), table_name="ingestion_job_items")
    op.drop_table("ingestion_job_items")
    op.drop_constraint(
        op.f("ck_document_versions_byte_size_non_negative"), "document_versions", type_="check"
    )
    op.drop_constraint(
        op.f("ck_document_versions_fetched_has_hash_and_object"),
        "document_versions",
        type_="check",
    )
    op.drop_column("document_versions", "fetch_method")
    op.drop_column("document_versions", "fetched_at")
    op.drop_column("document_versions", "byte_size")
    op.drop_column("document_versions", "artifact_status")
    bind = op.get_bind()
    INGESTION_ITEM_STATUS.drop(bind, checkfirst=True)
    ARTIFACT_STATUS.drop(bind, checkfirst=True)
