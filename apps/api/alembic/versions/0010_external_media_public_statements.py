"""external media and public statements

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _verification_columns() -> list[sa.Column[object]]:
    state = postgresql.ENUM(
        "unreviewed",
        "ai_flagged",
        "human_verified",
        "human_rejected",
        "needs_more_evidence",
        "unresolved",
        name="verification_state",
        create_type=False,
    )
    return [
        sa.Column("verification_state", state, server_default="unreviewed", nullable=False),
        sa.Column("verified_by", sa.String(128)),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
    ]


def _identity() -> list[sa.Column[object]]:
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


def _human_check(table: str) -> sa.CheckConstraint:
    return sa.CheckConstraint(
        "verification_state NOT IN ('human_verified', 'human_rejected') OR "
        "(verified_by IS NOT NULL AND verified_at IS NOT NULL)",
        name=op.f(f"ck_{table}_human_verification_has_reviewer"),
    )


def upgrade() -> None:
    op.create_table(
        "external_sources",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("publisher", sa.String(255), nullable=False),
        sa.Column("account", sa.String(255)),
        sa.Column("canonical_url", sa.String(2048), nullable=False),
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("access_method", sa.String(32), nullable=False),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("terms_note", sa.Text(), nullable=False),
        sa.Column("coverage_note", sa.Text(), nullable=False),
        *_verification_columns(),
        *_identity(),
        sa.CheckConstraint("visibility = 'public'", name=op.f("ck_external_sources_public_only")),
        sa.CheckConstraint(
            "access_method IN ('manual_url','public_webpage','official_api','operator_capture')",
            name=op.f("ck_external_sources_access_method_allowed"),
        ),
        _human_check("external_sources"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "canonical_url", name="uq_external_sources_case_url"),
    )
    op.create_index(op.f("ix_external_sources_case_id"), "external_sources", ["case_id"])

    op.create_table(
        "media_items",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("external_source_id", sa.UUID(), nullable=False),
        sa.Column("canonical_url", sa.String(2048), nullable=False),
        sa.Column("original_url", sa.String(2048), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("publisher", sa.String(255), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("transcript_origin", sa.String(64)),
        sa.Column("item_kind", sa.String(16), nullable=False),
        sa.Column("archive_url", sa.String(2048)),
        sa.Column("access_status", sa.String(16), nullable=False),
        sa.Column("captured_text", sa.Text(), nullable=False),
        sa.Column("source_metadata", postgresql.JSONB(), nullable=False),
        *_verification_columns(),
        *_identity(),
        sa.CheckConstraint(
            "access_status IN ('public','restricted','rejected')",
            name=op.f("ck_media_items_access_status_allowed"),
        ),
        sa.CheckConstraint(
            "item_kind IN ('original','repost','clip','embedded')",
            name=op.f("ck_media_items_item_kind_allowed"),
        ),
        sa.CheckConstraint(
            "captured_at >= published_at OR published_at IS NULL",
            name=op.f("ck_media_items_capture_not_before_publication"),
        ),
        sa.CheckConstraint(
            "access_status = 'public'", name=op.f("ck_media_items_held_items_public_only")
        ),
        _human_check("media_items"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["external_source_id"], ["external_sources.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "canonical_url", name="uq_media_items_case_url"),
    )
    op.create_index(op.f("ix_media_items_case_id"), "media_items", ["case_id"])
    op.create_index(
        op.f("ix_media_items_external_source_id"), "media_items", ["external_source_id"]
    )

    op.create_table(
        "media_statements",
        sa.Column("media_item_id", sa.UUID(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("speaker", sa.String(255)),
        sa.Column("person_id", sa.UUID()),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_sha256", sa.String(64), nullable=False),
        sa.Column("exact_quote", sa.Boolean(), nullable=False),
        sa.Column("char_from", sa.Integer()),
        sa.Column("char_to", sa.Integer()),
        sa.Column("timecode_start_ms", sa.BigInteger()),
        sa.Column("timecode_end_ms", sa.BigInteger()),
        sa.Column("transcript_origin", sa.String(64)),
        *_verification_columns(),
        *_identity(),
        sa.CheckConstraint("sequence >= 1", name=op.f("ck_media_statements_sequence_positive")),
        sa.CheckConstraint(
            "char_from IS NULL OR char_from >= 0",
            name=op.f("ck_media_statements_char_from_non_negative"),
        ),
        sa.CheckConstraint(
            "char_to IS NULL OR char_to > char_from",
            name=op.f("ck_media_statements_char_range_valid"),
        ),
        sa.CheckConstraint(
            "timecode_start_ms IS NULL OR timecode_start_ms >= 0",
            name=op.f("ck_media_statements_timecode_non_negative"),
        ),
        _human_check("media_statements"),
        sa.ForeignKeyConstraint(["media_item_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("media_item_id", "sequence", name="uq_media_statements_item_sequence"),
    )
    op.create_index(
        op.f("ix_media_statements_media_item_id"), "media_statements", ["media_item_id"]
    )
    op.create_index(op.f("ix_media_statements_person_id"), "media_statements", ["person_id"])

    op.create_table(
        "court_media_links",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("media_item_id", sa.UUID(), nullable=False),
        sa.Column("court_status", sa.String(24), nullable=False),
        sa.Column("citation_id", sa.UUID()),
        sa.Column("document_id", sa.UUID()),
        sa.Column("exhibit_id", sa.UUID()),
        sa.Column("finding_id", sa.UUID()),
        sa.Column("note", sa.Text(), nullable=False),
        *_verification_columns(),
        *_identity(),
        sa.CheckConstraint(
            "court_status IN ('external_only','mentioned','tendered','admitted','rejected','discussed','relied_upon','unknown')",
            name=op.f("ck_court_media_links_court_status_allowed"),
        ),
        sa.CheckConstraint(
            "court_status IN ('external_only','unknown') OR citation_id IS NOT NULL",
            name=op.f("ck_court_media_links_court_status_requires_citation"),
        ),
        sa.CheckConstraint(
            "court_status IN ('external_only','unknown') OR verification_state = 'human_verified'",
            name=op.f("ck_court_media_links_court_status_requires_human_verification"),
        ),
        _human_check("court_media_links"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["media_item_id"], ["media_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["exhibit_id"], ["exhibits.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["finding_id"], ["findings.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "media_item_id",
            "court_status",
            "citation_id",
            name="uq_court_media_links_status_citation",
        ),
    )
    op.create_index(op.f("ix_court_media_links_case_id"), "court_media_links", ["case_id"])
    op.create_index(
        op.f("ix_court_media_links_media_item_id"), "court_media_links", ["media_item_id"]
    )
    op.create_index(op.f("ix_court_media_links_citation_id"), "court_media_links", ["citation_id"])

    op.create_table(
        "media_statement_comparisons",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("comparison_key", sa.String(64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("statement_a_id", sa.UUID(), nullable=False),
        sa.Column("statement_b_id", sa.UUID()),
        sa.Column("court_citation_b_id", sa.UUID()),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("extraction_origin", sa.String(64), nullable=False),
        *_verification_columns(),
        *_identity(),
        sa.CheckConstraint(
            "classification IN ('possible_contradiction','qualification','timeline_difference','consistent','not_comparable')",
            name=op.f("ck_media_statement_comparisons_classification_allowed"),
        ),
        sa.CheckConstraint(
            "statement_b_id IS NOT NULL OR court_citation_b_id IS NOT NULL",
            name=op.f("ck_media_statement_comparisons_second_source_required"),
        ),
        sa.CheckConstraint(
            "NOT (statement_b_id IS NOT NULL AND court_citation_b_id IS NOT NULL)",
            name=op.f("ck_media_statement_comparisons_second_source_exactly_one_kind"),
        ),
        _human_check("media_statement_comparisons"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["statement_a_id"], ["media_statements.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["statement_b_id"], ["media_statements.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["court_citation_b_id"], ["citations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "case_id", "comparison_key", name="uq_media_statement_comparisons_case_key"
        ),
    )
    op.create_index(
        op.f("ix_media_statement_comparisons_case_id"), "media_statement_comparisons", ["case_id"]
    )


def downgrade() -> None:
    op.drop_table("media_statement_comparisons")
    op.drop_table("court_media_links")
    op.drop_table("media_statements")
    op.drop_table("media_items")
    op.drop_table("external_sources")
