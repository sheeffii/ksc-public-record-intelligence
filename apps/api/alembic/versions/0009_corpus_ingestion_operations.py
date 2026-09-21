"""corpus ingestion operations

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _identity_and_timestamps() -> list[sa.Column[object]]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "source_record_snapshots",
        sa.Column("source_record_id", sa.UUID(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_sha256", sa.String(64), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_identity_and_timestamps(),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_record_id", "metadata_sha256", name="uq_source_record_snapshots_hash"
        ),
    )
    op.create_index(
        op.f("ix_source_record_snapshots_source_record_id"),
        "source_record_snapshots",
        ["source_record_id"],
    )

    op.create_table(
        "artifact_acquisitions",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("document_version_id", sa.UUID(), nullable=False),
        sa.Column("official_url", sa.String(1024), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="4", nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_owner", sa.String(128), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_class", sa.String(64), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        *_identity_and_timestamps(),
        sa.CheckConstraint(
            "status IN ('pending','leased','captured','blocked','failed','quarantined')",
            name=op.f("ck_artifact_acquisitions_status_allowed"),
        ),
        sa.CheckConstraint(
            "attempt_count >= 0", name=op.f("ck_artifact_acquisitions_attempt_count_non_negative")
        ),
        sa.CheckConstraint(
            "max_attempts >= 1", name=op.f("ck_artifact_acquisitions_max_attempts_positive")
        ),
        sa.CheckConstraint(
            "(status = 'leased') = (lease_owner IS NOT NULL AND lease_expires_at IS NOT NULL)",
            name=op.f("ck_artifact_acquisitions_lease_matches_status"),
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_version_id", name="uq_artifact_acquisitions_version"),
    )
    op.create_index(op.f("ix_artifact_acquisitions_case_id"), "artifact_acquisitions", ["case_id"])
    op.create_index(
        op.f("ix_artifact_acquisitions_document_version_id"),
        "artifact_acquisitions",
        ["document_version_id"],
    )
    op.create_index(
        "ix_artifact_acquisitions_claim",
        "artifact_acquisitions",
        ["status", "available_at", "created_at"],
    )

    op.create_table(
        "artifact_quarantine",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("document_version_id", sa.UUID(), nullable=True),
        sa.Column("ingestion_job_item_id", sa.UUID(), nullable=True),
        sa.Column("reason_code", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("artifact_sha256", sa.String(64), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("reviewed_by", sa.String(128), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        *_identity_and_timestamps(),
        sa.CheckConstraint(
            "state IN ('open','released','rejected')",
            name=op.f("ck_artifact_quarantine_state_allowed"),
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_job_item_id"], ["ingestion_job_items.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artifact_quarantine_case_id"), "artifact_quarantine", ["case_id"])
    op.create_index(
        op.f("ix_artifact_quarantine_document_version_id"),
        "artifact_quarantine",
        ["document_version_id"],
    )

    op.create_table(
        "processing_runs",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("processor", sa.String(64), nullable=False),
        sa.Column("processor_version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("forced", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("selected_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_identity_and_timestamps(),
        sa.CheckConstraint(
            "status IN ('running','completed','failed')",
            name=op.f("ck_processing_runs_status_allowed"),
        ),
        sa.CheckConstraint(
            "selected_count >= 0 AND processed_count >= 0 AND failed_count >= 0",
            name=op.f("ck_processing_runs_counts_non_negative"),
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_processing_runs_case_id"), "processing_runs", ["case_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_processing_runs_case_id"), table_name="processing_runs")
    op.drop_table("processing_runs")
    op.drop_index(
        op.f("ix_artifact_quarantine_document_version_id"), table_name="artifact_quarantine"
    )
    op.drop_index(op.f("ix_artifact_quarantine_case_id"), table_name="artifact_quarantine")
    op.drop_table("artifact_quarantine")
    op.drop_index("ix_artifact_acquisitions_claim", table_name="artifact_acquisitions")
    op.drop_index(
        op.f("ix_artifact_acquisitions_document_version_id"), table_name="artifact_acquisitions"
    )
    op.drop_index(op.f("ix_artifact_acquisitions_case_id"), table_name="artifact_acquisitions")
    op.drop_table("artifact_acquisitions")
    op.drop_index(
        op.f("ix_source_record_snapshots_source_record_id"),
        table_name="source_record_snapshots",
    )
    op.drop_table("source_record_snapshots")
