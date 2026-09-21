"""citation-first AI retrieval and validation audit

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE answer_block_kind ADD VALUE IF NOT EXISTS 'court_response'")
    op.execute("ALTER TYPE answer_block_kind ADD VALUE IF NOT EXISTS 'human_note'")
    op.add_column("ai_runs", sa.Column("question", sa.Text(), nullable=True))
    op.add_column("ai_runs", sa.Column("system_prompt_sha256", sa.String(64), nullable=True))
    op.add_column(
        "ai_runs", sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column(
        "ai_runs",
        sa.Column("structured_output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "ai_runs",
        sa.Column("validation_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "ai_runs",
        sa.Column("answer_withheld", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "ai_runs",
        sa.Column("insufficient_evidence", sa.Boolean(), server_default="false", nullable=False),
    )

    op.drop_constraint(
        op.f("ck_research_notes_provenance_is_human"), "research_notes", type_="check"
    )
    op.add_column("research_notes", sa.Column("origin_ai_run_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_research_notes_origin_ai_run_id_ai_runs"),
        "research_notes",
        "ai_runs",
        ["origin_ai_run_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_research_notes_origin_ai_run_id"),
        "research_notes",
        ["origin_ai_run_id"],
    )
    op.create_check_constraint(
        op.f("ck_research_notes_provenance_allowed"),
        "research_notes",
        "provenance IN ('human', 'ai_assisted')",
    )
    op.create_check_constraint(
        op.f("ck_research_notes_ai_origin_matches_provenance"),
        "research_notes",
        "(provenance = 'ai_assisted') = (origin_ai_run_id IS NOT NULL)",
    )

    op.add_column(
        "ai_outputs",
        sa.Column(
            "content_type", sa.String(32), server_default="source_paraphrase", nullable=False
        ),
    )
    op.add_column("ai_outputs", sa.Column("claim_key", sa.String(128), nullable=True))
    op.create_check_constraint(
        op.f("ck_ai_outputs_content_type_allowed"),
        "ai_outputs",
        "content_type IN ('verbatim_quote', 'source_paraphrase', 'ai_analysis', 'abstention')",
    )

    op.create_table(
        "ai_retrieval_sources",
        sa.Column("ai_run_id", sa.UUID(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("retrieval_method", sa.String(32), nullable=False),
        sa.Column("retrieval_score", sa.Numeric(12, 8), nullable=False),
        sa.Column("source_category", sa.String(32), nullable=False),
        sa.Column("source_visibility", sa.String(32), nullable=False),
        sa.Column("source_ref", sa.String(255), nullable=False),
        sa.Column("version_ref", sa.String(128), nullable=True),
        sa.Column("display", sa.String(255), nullable=False),
        sa.Column("target_path", sa.String(1024), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("excerpt_sha256", sa.String(64), nullable=False),
        sa.Column("page_from", sa.Integer(), nullable=True),
        sa.Column("page_to", sa.Integer(), nullable=True),
        sa.Column("pdf_page_index", sa.Integer(), nullable=True),
        sa.Column("para_from", sa.Integer(), nullable=True),
        sa.Column("para_to", sa.Integer(), nullable=True),
        sa.Column("line_from", sa.Integer(), nullable=True),
        sa.Column("line_to", sa.Integer(), nullable=True),
        sa.Column("verification_state", sa.String(32), server_default="unreviewed", nullable=False),
        sa.Column("verification_reviewed_by", sa.String(128), nullable=True),
        sa.Column("verification_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("document_version_id", sa.UUID(), nullable=True),
        sa.Column("document_paragraph_id", sa.UUID(), nullable=True),
        sa.Column("document_chunk_id", sa.UUID(), nullable=True),
        sa.Column("transcript_segment_id", sa.UUID(), nullable=True),
        sa.Column("finding_id", sa.UUID(), nullable=True),
        sa.Column("argument_id", sa.UUID(), nullable=True),
        sa.Column("research_note_id", sa.UUID(), nullable=True),
        sa.Column("citation_id", sa.UUID(), nullable=True),
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
        sa.CheckConstraint("rank >= 1", name=op.f("ck_ai_retrieval_sources_rank_positive")),
        sa.CheckConstraint(
            "retrieval_score >= 0",
            name=op.f("ck_ai_retrieval_sources_retrieval_score_non_negative"),
        ),
        sa.CheckConstraint(
            "source_category IN ('court_finding', 'witness_testimony', 'spo_argument', "
            "'defence_argument', 'document_exhibit', 'court_response', 'human_note')",
            name=op.f("ck_ai_retrieval_sources_source_category_allowed"),
        ),
        sa.CheckConstraint(
            "source_visibility IN ('public', 'public_redacted', 'private_authorized')",
            name=op.f("ck_ai_retrieval_sources_source_visibility_allowed"),
        ),
        sa.CheckConstraint(
            "num_nonnulls(document_paragraph_id, document_chunk_id, transcript_segment_id, "
            "finding_id, argument_id, research_note_id) = 1",
            name=op.f("ck_ai_retrieval_sources_exactly_one_source_anchor"),
        ),
        sa.CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from",
            name=op.f("ck_ai_retrieval_sources_page_range"),
        ),
        sa.CheckConstraint(
            "para_to IS NULL OR para_from IS NULL OR para_to >= para_from",
            name=op.f("ck_ai_retrieval_sources_para_range"),
        ),
        sa.CheckConstraint(
            "line_to IS NULL OR line_from IS NULL OR line_to >= line_from",
            name=op.f("ck_ai_retrieval_sources_line_range"),
        ),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') "
            "OR (verification_reviewed_by IS NOT NULL AND verification_reviewed_at IS NOT NULL)",
            name=op.f("ck_ai_retrieval_sources_human_verification_has_reviewer"),
        ),
        sa.ForeignKeyConstraint(
            ["ai_run_id"],
            ["ai_runs.id"],
            ondelete="CASCADE",
            name=op.f("fk_ai_retrieval_sources_ai_run_id_ai_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            ondelete="RESTRICT",
            name=op.f("fk_ai_retrieval_sources_document_version_id_document_versions"),
        ),
        sa.ForeignKeyConstraint(
            ["document_paragraph_id"],
            ["document_paragraphs.id"],
            ondelete="RESTRICT",
            name=op.f("fk_ai_retrieval_sources_document_paragraph_id_document_paragraphs"),
        ),
        sa.ForeignKeyConstraint(
            ["document_chunk_id"],
            ["document_chunks.id"],
            ondelete="RESTRICT",
            name=op.f("fk_ai_retrieval_sources_document_chunk_id_document_chunks"),
        ),
        sa.ForeignKeyConstraint(
            ["transcript_segment_id"],
            ["transcript_segments.id"],
            ondelete="RESTRICT",
            name=op.f("fk_ai_retrieval_sources_transcript_segment_id_transcript_segments"),
        ),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            ondelete="RESTRICT",
            name=op.f("fk_ai_retrieval_sources_finding_id_findings"),
        ),
        sa.ForeignKeyConstraint(
            ["argument_id"],
            ["arguments.id"],
            ondelete="RESTRICT",
            name=op.f("fk_ai_retrieval_sources_argument_id_arguments"),
        ),
        sa.ForeignKeyConstraint(
            ["research_note_id"],
            ["research_notes.id"],
            ondelete="RESTRICT",
            name=op.f("fk_ai_retrieval_sources_research_note_id_research_notes"),
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            ondelete="RESTRICT",
            name=op.f("fk_ai_retrieval_sources_citation_id_citations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_retrieval_sources")),
        sa.UniqueConstraint("ai_run_id", "rank", name="uq_ai_retrieval_sources_run_rank"),
    )
    op.create_index(
        op.f("ix_ai_retrieval_sources_ai_run_id"),
        "ai_retrieval_sources",
        ["ai_run_id"],
    )
    op.create_index(
        op.f("ix_ai_retrieval_sources_document_version_id"),
        "ai_retrieval_sources",
        ["document_version_id"],
    )

    op.create_table(
        "ai_output_sources",
        sa.Column("ai_output_id", sa.UUID(), nullable=False),
        sa.Column("retrieval_source_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ai_output_id"],
            ["ai_outputs.id"],
            ondelete="CASCADE",
            name=op.f("fk_ai_output_sources_ai_output_id_ai_outputs"),
        ),
        sa.ForeignKeyConstraint(
            ["retrieval_source_id"],
            ["ai_retrieval_sources.id"],
            ondelete="CASCADE",
            name=op.f("fk_ai_output_sources_retrieval_source_id_ai_retrieval_sources"),
        ),
        sa.PrimaryKeyConstraint(
            "ai_output_id", "retrieval_source_id", name=op.f("pk_ai_output_sources")
        ),
    )


def downgrade() -> None:
    op.drop_table("ai_output_sources")
    op.drop_index(
        op.f("ix_ai_retrieval_sources_document_version_id"),
        table_name="ai_retrieval_sources",
    )
    op.drop_index(op.f("ix_ai_retrieval_sources_ai_run_id"), table_name="ai_retrieval_sources")
    op.drop_table("ai_retrieval_sources")

    op.drop_constraint(op.f("ck_ai_outputs_content_type_allowed"), "ai_outputs", type_="check")
    op.drop_column("ai_outputs", "claim_key")
    op.drop_column("ai_outputs", "content_type")

    op.drop_column("ai_runs", "insufficient_evidence")
    op.drop_column("ai_runs", "answer_withheld")
    op.drop_column("ai_runs", "validation_errors")
    op.drop_column("ai_runs", "structured_output")
    op.drop_column("ai_runs", "parameters")
    op.drop_column("ai_runs", "system_prompt_sha256")
    op.drop_column("ai_runs", "question")

    op.drop_constraint(
        op.f("ck_research_notes_ai_origin_matches_provenance"),
        "research_notes",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_research_notes_provenance_allowed"), "research_notes", type_="check"
    )
    # Revision 0006 only supports human notes. A deliberate schema rollback
    # therefore converts saved AI-assisted notes to ordinary notes after their
    # origin column is removed, rather than leaving rows that violate 0006.
    op.execute("UPDATE research_notes SET provenance = 'human' WHERE provenance = 'ai_assisted'")
    op.drop_index(op.f("ix_research_notes_origin_ai_run_id"), table_name="research_notes")
    op.drop_constraint(
        op.f("fk_research_notes_origin_ai_run_id_ai_runs"),
        "research_notes",
        type_="foreignkey",
    )
    op.drop_column("research_notes", "origin_ai_run_id")
    op.create_check_constraint(
        op.f("ck_research_notes_provenance_is_human"),
        "research_notes",
        "provenance = 'human'",
    )
