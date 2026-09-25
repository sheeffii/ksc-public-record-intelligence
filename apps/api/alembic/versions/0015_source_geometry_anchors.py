"""source-native PDF geometry and reusable SourceAnchor contract (Phase 20A)

Revision ID: 0015
Revises: 0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UUID = postgresql.UUID(as_uuid=True)
_NUM = sa.Numeric(12, 4)


def upgrade() -> None:
    precision = postgresql.ENUM(
        "exact_geometry",
        "ocr_geometry",
        "page_and_line",
        "page_only",
        "text_only",
        "unavailable",
        name="source_precision",
    )
    precision.create(op.get_bind())
    for name, type_, default in (
        ("width_points", _NUM, None),
        ("height_points", _NUM, None),
        ("rotation", sa.Integer(), None),
        ("geometry_text", sa.Text(), None),
        ("geometry_extraction_method", sa.String(32), None),
        ("geometry_state", sa.String(16), "unavailable"),
        ("geometry_extractor", sa.String(64), None),
        ("geometry_extractor_version", sa.String(32), None),
    ):
        op.add_column(
            "document_pages",
            sa.Column(name, type_, nullable=default is None, server_default=default),
        )
    op.alter_column("document_pages", "geometry_state", nullable=False)
    op.add_column("document_pages", sa.Column("geometry_processing_run_id", _UUID, nullable=True))
    op.create_foreign_key(
        "fk_document_pages_geometry_processing_run_id_processing_runs",
        "document_pages",
        "processing_runs",
        ["geometry_processing_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_document_pages_width_points_positive",
        "document_pages",
        "width_points IS NULL OR width_points > 0",
    )
    op.create_check_constraint(
        "ck_document_pages_height_points_positive",
        "document_pages",
        "height_points IS NULL OR height_points > 0",
    )
    op.create_check_constraint(
        "ck_document_pages_rotation_valid",
        "document_pages",
        "rotation IS NULL OR rotation IN (0,90,180,270)",
    )
    op.create_check_constraint(
        "ck_document_pages_geometry_state_allowed",
        "document_pages",
        "geometry_state IN ('native','ocr','ocr_required','unavailable')",
    )

    op.create_table(
        "page_text_geometry",
        sa.Column("document_version_id", _UUID, nullable=False),
        sa.Column("pdf_page_index", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_basis", sa.String(32), nullable=False, server_default="page_geometry_text"),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("x", _NUM, nullable=False),
        sa.Column("y", _NUM, nullable=False),
        sa.Column("width", _NUM, nullable=False),
        sa.Column("height", _NUM, nullable=False),
        sa.Column(
            "extraction_method",
            postgresql.ENUM(name="text_extraction_method", create_type=False),
            nullable=False,
        ),
        sa.Column("extraction_state", sa.String(24), nullable=False),
        sa.Column("id", _UUID, primary_key=True),
        sa.ForeignKeyConstraint(
            ["document_version_id", "pdf_page_index"],
            ["document_pages.document_version_id", "document_pages.pdf_page_index"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "document_version_id", "pdf_page_index", "sequence", name="uq_page_geometry_sequence"
        ),
        sa.CheckConstraint(
            "pdf_page_index >= 0", name="ck_page_text_geometry_pdf_page_index_non_negative"
        ),
        sa.CheckConstraint("sequence >= 0", name="ck_page_text_geometry_sequence_non_negative"),
        sa.CheckConstraint(
            "char_start >= 0 AND char_end > char_start", name="ck_page_text_geometry_char_range"
        ),
        sa.CheckConstraint(
            "x >= 0 AND y >= 0 AND width > 0 AND height > 0",
            name="ck_page_text_geometry_positive_rectangle",
        ),
        sa.CheckConstraint(
            "extraction_state IN ('usable','review_required')",
            name="ck_page_text_geometry_extraction_state_allowed",
        ),
    )
    op.create_index(
        "ix_page_text_geometry_version_page",
        "page_text_geometry",
        ["document_version_id", "pdf_page_index"],
    )

    op.create_table(
        "source_spans",
        sa.Column("document_version_id", _UUID, nullable=False),
        sa.Column("pdf_page_index", sa.Integer()),
        sa.Column("page_number", sa.Integer()),
        sa.Column("paragraph_number", sa.Integer()),
        sa.Column("transcript_segment_id", _UUID),
        sa.Column("line_from", sa.Integer()),
        sa.Column("line_to", sa.Integer()),
        sa.Column("exact_text", sa.Text()),
        sa.Column("text_basis", sa.String(32)),
        sa.Column("char_start", sa.Integer()),
        sa.Column("char_end", sa.Integer()),
        sa.Column(
            "extraction_method",
            postgresql.ENUM(name="text_extraction_method", create_type=False),
            nullable=False,
        ),
        sa.Column("extractor_version", sa.String(32), nullable=False),
        sa.Column(
            "precision", postgresql.ENUM(name="source_precision", create_type=False), nullable=False
        ),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("failure_reason", sa.String(128)),
        sa.Column("processing_run_id", _UUID),
        sa.Column("id", _UUID, primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id", "pdf_page_index"],
            ["document_pages.document_version_id", "document_pages.pdf_page_index"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["transcript_segment_id"], ["transcript_segments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["processing_run_id"], ["processing_runs.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "pdf_page_index IS NULL OR pdf_page_index >= 0",
            name="ck_source_spans_pdf_page_index_non_negative",
        ),
        sa.CheckConstraint(
            "page_number IS NULL OR page_number >= 1", name="ck_source_spans_page_number_positive"
        ),
        sa.CheckConstraint(
            "char_start IS NULL OR (char_end IS NOT NULL AND char_end >= char_start)",
            name="ck_source_spans_char_range",
        ),
        sa.CheckConstraint(
            "line_to IS NULL OR (line_from IS NOT NULL AND line_to >= line_from)",
            name="ck_source_spans_line_range",
        ),
        sa.CheckConstraint(
            "state IN ('verified','review_required','unavailable')",
            name="ck_source_spans_state_allowed",
        ),
    )
    op.create_index(
        "ix_source_spans_version_page", "source_spans", ["document_version_id", "pdf_page_index"]
    )
    op.create_index("ix_source_spans_precision", "source_spans", ["precision"])

    op.create_table(
        "source_regions",
        sa.Column(
            "source_span_id",
            _UUID,
            sa.ForeignKey("source_spans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("x", _NUM, nullable=False),
        sa.Column("y", _NUM, nullable=False),
        sa.Column("width", _NUM, nullable=False),
        sa.Column("height", _NUM, nullable=False),
        sa.Column(
            "coordinate_space", sa.String(32), nullable=False, server_default="pdf_points_top_left"
        ),
        sa.Column("id", _UUID, primary_key=True),
        sa.UniqueConstraint("source_span_id", "sequence", name="uq_source_regions_span_sequence"),
        sa.CheckConstraint("sequence >= 0", name="ck_source_regions_sequence_non_negative"),
        sa.CheckConstraint(
            "x >= 0 AND y >= 0 AND width > 0 AND height > 0",
            name="ck_source_regions_positive_rectangle",
        ),
    )
    op.create_table(
        "source_anchors",
        sa.Column(
            "source_span_id",
            _UUID,
            sa.ForeignKey("source_spans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("object_type", sa.String(32), nullable=False),
        sa.Column("object_id", _UUID, nullable=False),
        sa.Column("anchor_role", sa.String(32), nullable=False),
        sa.Column("source_verification_state", sa.String(32), nullable=False),
        sa.Column("id", _UUID, primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "object_type", "object_id", "anchor_role", name="uq_source_anchors_object_role"
        ),
        sa.CheckConstraint(
            "object_type IN ('entity_occurrence','citation','relationship','finding')",
            name="ck_source_anchors_object_type_allowed",
        ),
    )
    op.create_index("ix_source_anchors_object_type", "source_anchors", ["object_type"])
    op.create_index("ix_source_anchors_object_id", "source_anchors", ["object_id"])


def downgrade() -> None:
    op.drop_table("source_anchors")
    op.drop_table("source_regions")
    op.drop_table("source_spans")
    op.drop_table("page_text_geometry")
    op.drop_constraint(
        "fk_document_pages_geometry_processing_run_id_processing_runs",
        "document_pages",
        type_="foreignkey",
    )
    op.drop_column("document_pages", "geometry_processing_run_id")
    for name in (
        "geometry_extractor_version",
        "geometry_extractor",
        "geometry_state",
        "geometry_extraction_method",
        "geometry_text",
        "rotation",
        "height_points",
        "width_points",
    ):
        op.drop_column("document_pages", name)
    postgresql.ENUM(name="source_precision").drop(op.get_bind())
