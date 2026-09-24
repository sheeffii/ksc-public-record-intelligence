"""structured entity occurrences

Revision ID: 0012
Revises: 0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "exhibits",
        sa.Column("status", sa.String(length=32), server_default="unknown", nullable=False),
    )
    op.create_table(
        "entity_occurrences",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("witness_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exhibit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transcript_segment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("pdf_page_index", sa.Integer(), nullable=True),
        sa.Column("line_from", sa.Integer(), nullable=True),
        sa.Column("line_to", sa.Integer(), nullable=True),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("occurrence_text", sa.Text(), nullable=False),
        sa.Column(
            "extraction_origin",
            sa.String(length=32),
            server_default="deterministic",
            nullable=False,
        ),
        sa.Column("review_required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "num_nonnulls(person_id, witness_id, organization_id, exhibit_id) = 1",
            name=op.f("ck_entity_occurrences_exactly_one_entity"),
        ),
        sa.CheckConstraint(
            "char_start >= 0", name=op.f("ck_entity_occurrences_char_start_non_negative")
        ),
        sa.CheckConstraint("char_end >= char_start", name=op.f("ck_entity_occurrences_char_range")),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["witness_id"], ["witnesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exhibit_id"], ["exhibits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["transcript_segment_id"], ["transcript_segments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_version_id",
            "transcript_segment_id",
            "char_start",
            "char_end",
            "person_id",
            "witness_id",
            "organization_id",
            "exhibit_id",
            name="uq_entity_occurrences_source_entity",
        ),
    )
    for column in ("case_id", "person_id", "witness_id", "organization_id", "exhibit_id"):
        op.create_index(op.f(f"ix_entity_occurrences_{column}"), "entity_occurrences", [column])


def downgrade() -> None:
    op.drop_table("entity_occurrences")
    op.drop_column("exhibits", "status")
