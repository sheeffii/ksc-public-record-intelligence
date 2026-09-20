"""parsing coordinates, citation audit detail and lexical search

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-20

Phase 8 keeps PDF indices separate from printed/source coordinates, persists
numbered paragraphs and parse provenance, and adds PostgreSQL full-text indexes
for public parsed chunks and transcript segments. No embedding column or model
provider is introduced.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- parse provenance -------------------------------------------------
    op.add_column(
        "document_versions", sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "document_versions", sa.Column("parser_name", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "document_versions", sa.Column("parser_version", sa.String(length=32), nullable=True)
    )
    op.add_column(
        "document_versions",
        sa.Column("parse_requires_review", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "document_versions",
        sa.Column("parse_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # --- documents/pages/paragraphs/chunks -------------------------------
    op.add_column(
        "documents",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('simple', coalesce(title, '') || ' ' || "
                "coalesce(official_ref, '') || ' ' || coalesce(filing_number, ''))",
                persisted=True,
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_documents_search_vector",
        "documents",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )

    op.add_column("document_pages", sa.Column("pdf_page_index", sa.Integer(), nullable=True))
    op.add_column(
        "document_pages", sa.Column("printed_page_label", sa.String(length=64), nullable=True)
    )
    # Existing rows are synthetic fixture data whose page_number was created
    # from the fixture's known one-based sequence. This backfill preserves it;
    # new parses never derive a printed page from this index.
    op.execute("UPDATE document_pages SET pdf_page_index = page_number - 1")
    op.alter_column("document_pages", "pdf_page_index", nullable=False)
    op.alter_column("document_pages", "page_number", nullable=True)
    op.create_check_constraint(
        "pdf_page_index_non_negative", "document_pages", "pdf_page_index >= 0"
    )
    op.create_unique_constraint(
        "uq_document_pages_version_pdf_index",
        "document_pages",
        ["document_version_id", "pdf_page_index"],
    )

    op.create_table(
        "document_paragraphs",
        sa.Column("document_version_id", sa.UUID(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("paragraph_number", sa.Integer(), nullable=False),
        sa.Column("pdf_page_index_from", sa.Integer(), nullable=False),
        sa.Column("pdf_page_index_to", sa.Integer(), nullable=False),
        sa.Column("page_from", sa.Integer(), nullable=True),
        sa.Column("page_to", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "pdf_page_index_from >= 0",
            name=op.f("ck_document_paragraphs_pdf_page_index_from_non_negative"),
        ),
        sa.CheckConstraint(
            "pdf_page_index_to >= pdf_page_index_from",
            name=op.f("ck_document_paragraphs_pdf_page_index_range"),
        ),
        sa.CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from",
            name=op.f("ck_document_paragraphs_page_range"),
        ),
        sa.CheckConstraint(
            "paragraph_number >= 1",
            name=op.f("ck_document_paragraphs_paragraph_number_positive"),
        ),
        sa.CheckConstraint(
            "sequence >= 0", name=op.f("ck_document_paragraphs_sequence_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_document_paragraphs_document_version_id_document_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_paragraphs")),
        sa.UniqueConstraint(
            "document_version_id",
            "paragraph_number",
            name="uq_document_paragraphs_version_number",
        ),
        sa.UniqueConstraint(
            "document_version_id", "sequence", name="uq_document_paragraphs_version_sequence"
        ),
    )

    op.add_column(
        "document_chunks",
        sa.Column("chunk_kind", sa.String(length=32), server_default="page", nullable=False),
    )
    op.add_column("document_chunks", sa.Column("pdf_page_index_from", sa.Integer(), nullable=True))
    op.add_column("document_chunks", sa.Column("pdf_page_index_to", sa.Integer(), nullable=True))
    op.add_column(
        "document_chunks",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple', coalesce(text, ''))", persisted=True),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "chunk_kind_known",
        "document_chunks",
        "chunk_kind IN ('paragraph', 'page', 'section', 'transcript_page')",
    )
    op.create_check_constraint(
        "pdf_page_index_range",
        "document_chunks",
        "pdf_page_index_to IS NULL OR pdf_page_index_from IS NULL OR "
        "pdf_page_index_to >= pdf_page_index_from",
    )
    op.create_index(
        "ix_document_chunks_search_vector",
        "document_chunks",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )

    # --- transcript coordinates/search -----------------------------------
    op.add_column("transcript_segments", sa.Column("pdf_page_index", sa.Integer(), nullable=True))
    op.add_column(
        "transcript_segments",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple', coalesce(text, ''))", persisted=True),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "pdf_page_index_non_negative",
        "transcript_segments",
        "pdf_page_index IS NULL OR pdf_page_index >= 0",
    )
    op.create_index(
        "ix_transcript_segments_search_vector",
        "transcript_segments",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )

    # --- citation audit coordinates --------------------------------------
    op.add_column("citations", sa.Column("source_pdf_page_index", sa.Integer(), nullable=True))
    op.add_column("citations", sa.Column("source_char_start", sa.Integer(), nullable=True))
    op.add_column("citations", sa.Column("source_char_end", sa.Integer(), nullable=True))
    op.add_column("citations", sa.Column("target_pdf_page_index", sa.Integer(), nullable=True))
    op.add_column("citations", sa.Column("resolution_detail", sa.Text(), nullable=True))
    op.add_column(
        "citations",
        sa.Column("candidate_identifiers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_check_constraint(
        "source_pdf_page_index_non_negative",
        "citations",
        "source_pdf_page_index IS NULL OR source_pdf_page_index >= 0",
    )
    op.create_check_constraint(
        "source_char_start_non_negative",
        "citations",
        "source_char_start IS NULL OR source_char_start >= 0",
    )
    op.create_check_constraint(
        "source_char_range",
        "citations",
        "source_char_end IS NULL OR source_char_start IS NULL OR "
        "source_char_end >= source_char_start",
    )
    op.create_check_constraint(
        "target_pdf_page_index_non_negative",
        "citations",
        "target_pdf_page_index IS NULL OR target_pdf_page_index >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_citations_target_pdf_page_index_non_negative"), "citations", type_="check"
    )
    op.drop_constraint(
        op.f("ck_citations_source_pdf_page_index_non_negative"), "citations", type_="check"
    )
    op.drop_constraint(op.f("ck_citations_source_char_range"), "citations", type_="check")
    op.drop_constraint(
        op.f("ck_citations_source_char_start_non_negative"), "citations", type_="check"
    )
    op.drop_column("citations", "candidate_identifiers")
    op.drop_column("citations", "resolution_detail")
    op.drop_column("citations", "target_pdf_page_index")
    op.drop_column("citations", "source_pdf_page_index")
    op.drop_column("citations", "source_char_end")
    op.drop_column("citations", "source_char_start")

    op.drop_index("ix_transcript_segments_search_vector", table_name="transcript_segments")
    op.drop_constraint(
        op.f("ck_transcript_segments_pdf_page_index_non_negative"),
        "transcript_segments",
        type_="check",
    )
    op.drop_column("transcript_segments", "search_vector")
    op.drop_column("transcript_segments", "pdf_page_index")

    op.drop_index("ix_document_chunks_search_vector", table_name="document_chunks")
    op.drop_constraint(
        op.f("ck_document_chunks_pdf_page_index_range"), "document_chunks", type_="check"
    )
    op.drop_constraint(
        op.f("ck_document_chunks_chunk_kind_known"), "document_chunks", type_="check"
    )
    op.drop_column("document_chunks", "search_vector")
    op.drop_column("document_chunks", "pdf_page_index_to")
    op.drop_column("document_chunks", "pdf_page_index_from")
    op.drop_column("document_chunks", "chunk_kind")

    op.drop_table("document_paragraphs")
    op.drop_constraint("uq_document_pages_version_pdf_index", "document_pages", type_="unique")
    op.drop_constraint(
        op.f("ck_document_pages_pdf_page_index_non_negative"), "document_pages", type_="check"
    )
    op.alter_column("document_pages", "page_number", nullable=False)
    op.drop_column("document_pages", "printed_page_label")
    op.drop_column("document_pages", "pdf_page_index")

    op.drop_index("ix_documents_search_vector", table_name="documents")
    op.drop_column("documents", "search_vector")

    op.drop_column("document_versions", "parse_notes")
    op.drop_column("document_versions", "parse_requires_review")
    op.drop_column("document_versions", "parser_version")
    op.drop_column("document_versions", "parser_name")
    op.drop_column("document_versions", "parsed_at")
