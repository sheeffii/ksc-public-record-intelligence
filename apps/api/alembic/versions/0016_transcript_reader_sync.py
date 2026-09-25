"""transcript page-header context and transcript-segment anchors (Phase 20B)

Revision ID: 0016
Revises: 0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UUID = postgresql.UUID(as_uuid=True)
_OBJECT_TYPES_20A = "('entity_occurrence','citation','relationship','finding')"
_OBJECT_TYPES_20B = "('entity_occurrence','citation','relationship','finding','transcript_segment')"


def upgrade() -> None:
    op.create_table(
        "transcript_page_contexts",
        sa.Column("id", _UUID, primary_key=True),
        sa.Column("document_version_id", _UUID, nullable=False),
        sa.Column("pdf_page_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer()),
        sa.Column("header_text", sa.Text(), nullable=False),
        sa.Column("header_char_start", sa.Integer(), nullable=False),
        sa.Column("header_char_end", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("subject_is_code", sa.Boolean(), nullable=False),
        sa.Column("session_state", sa.String(16), nullable=False),
        sa.Column("examination", sa.String(255)),
        sa.Column("rule_id", sa.String(64), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("processing_run_id", _UUID),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id", "pdf_page_index"],
            ["document_pages.document_version_id", "document_pages.pdf_page_index"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["processing_run_id"],
            ["processing_runs.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "document_version_id", "pdf_page_index", name="uq_transcript_page_contexts_page"
        ),
        sa.CheckConstraint("pdf_page_index >= 0", name="pdf_page_index_non_negative"),
        sa.CheckConstraint(
            "header_char_start >= 0 AND header_char_end > header_char_start",
            name="header_char_range",
        ),
        sa.CheckConstraint(
            "session_state IN ('open','private','closed')",
            name="session_state_allowed",
        ),
    )
    op.drop_constraint("ck_source_anchors_object_type_allowed", "source_anchors", type_="check")
    op.create_check_constraint(
        "ck_source_anchors_object_type_allowed",
        "source_anchors",
        f"object_type IN {_OBJECT_TYPES_20B}",
    )
    op.create_index(
        "ix_source_spans_transcript_segment_id", "source_spans", ["transcript_segment_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_source_spans_transcript_segment_id", table_name="source_spans")
    op.execute(
        "DELETE FROM source_spans WHERE id IN (SELECT source_span_id FROM source_anchors "
        "WHERE object_type = 'transcript_segment')"
    )
    op.drop_constraint("ck_source_anchors_object_type_allowed", "source_anchors", type_="check")
    op.create_check_constraint(
        "ck_source_anchors_object_type_allowed",
        "source_anchors",
        f"object_type IN {_OBJECT_TYPES_20A}",
    )
    op.drop_table("transcript_page_contexts")
