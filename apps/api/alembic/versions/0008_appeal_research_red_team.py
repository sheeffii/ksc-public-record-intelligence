"""appeal research, red team and statement comparison

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _verification_columns() -> list[sa.Column[object]]:
    verification_state = postgresql.ENUM(
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
        sa.Column(
            "verification_state", verification_state, server_default="unreviewed", nullable=False
        ),
        sa.Column("verified_by", sa.String(128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _timestamps() -> list[sa.Column[object]]:
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
        "appeal_issues",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("issue_key", sa.String(64), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("context", sa.String(16), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("finding_id", sa.UUID(), nullable=False),
        sa.Column("court_treatment", sa.String(24), nullable=False),
        sa.Column("court_treatment_note", sa.Text(), nullable=False),
        sa.Column("red_team_result", sa.String(32), nullable=False),
        sa.Column("extraction_origin", sa.String(64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_verification_columns(),
        *_timestamps(),
        sa.CheckConstraint(
            "category IN ('error_of_law','error_of_fact','sentencing','procedural_fairness',"
            "'evidence_assessment','reasoning','disclosure','legal_standard','causation',"
            "'mode_of_liability','other')",
            name=op.f("ck_appeal_issues_category_allowed"),
        ),
        sa.CheckConstraint(
            "context IN ('legal','factual','sentencing','procedural','other')",
            name=op.f("ck_appeal_issues_context_allowed"),
        ),
        sa.CheckConstraint(
            "court_treatment IN ('addressed','accepted','rejected','distinguished','qualified','not_located','unresolved')",
            name=op.f("ck_appeal_issues_court_treatment_allowed"),
        ),
        sa.CheckConstraint(
            "red_team_result IN ('supported_for_review','qualified','countered','insufficient_record')",
            name=op.f("ck_appeal_issues_red_team_result_allowed"),
        ),
        _human_check("appeal_issues"),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            ondelete="RESTRICT",
            name=op.f("fk_appeal_issues_case_id_cases"),
        ),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            ondelete="RESTRICT",
            name=op.f("fk_appeal_issues_finding_id_findings"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appeal_issues")),
        sa.UniqueConstraint("case_id", "issue_key", name="uq_appeal_issues_case_key"),
    )
    op.create_index(op.f("ix_appeal_issues_case_id"), "appeal_issues", ["case_id"])
    op.create_index(op.f("ix_appeal_issues_finding_id"), "appeal_issues", ["finding_id"])

    op.create_table(
        "appeal_issue_sources",
        sa.Column("issue_id", sa.UUID(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("source_category", sa.String(32), nullable=False),
        sa.Column("citation_id", sa.UUID(), nullable=False),
        sa.Column("argument_id", sa.UUID(), nullable=True),
        sa.Column("finding_evidence_link_id", sa.UUID(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_verification_columns(),
        *_timestamps(),
        sa.CheckConstraint("sequence >= 1", name=op.f("ck_appeal_issue_sources_sequence_positive")),
        sa.CheckConstraint(
            "role IN ('court_reasoning','applicable_standard','evidence_relied','defence_position','spo_position','court_response','supporting','contrary','qualifying')",
            name=op.f("ck_appeal_issue_sources_role_allowed"),
        ),
        sa.CheckConstraint(
            "source_category IN ('court_finding','spo_argument','defence_argument','witness_testimony','document_exhibit','court_response','public_authority')",
            name=op.f("ck_appeal_issue_sources_source_category_allowed"),
        ),
        _human_check("appeal_issue_sources"),
        sa.ForeignKeyConstraint(
            ["issue_id"],
            ["appeal_issues.id"],
            ondelete="CASCADE",
            name=op.f("fk_appeal_issue_sources_issue_id_appeal_issues"),
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            ondelete="RESTRICT",
            name=op.f("fk_appeal_issue_sources_citation_id_citations"),
        ),
        sa.ForeignKeyConstraint(
            ["argument_id"],
            ["arguments.id"],
            ondelete="RESTRICT",
            name=op.f("fk_appeal_issue_sources_argument_id_arguments"),
        ),
        sa.ForeignKeyConstraint(
            ["finding_evidence_link_id"],
            ["finding_evidence_links.id"],
            ondelete="RESTRICT",
            name=op.f("fk_appeal_issue_sources_finding_evidence_link_id_finding_evidence_links"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appeal_issue_sources")),
        sa.UniqueConstraint("issue_id", "sequence", name="uq_appeal_issue_sources_sequence"),
    )
    op.create_index(op.f("ix_appeal_issue_sources_issue_id"), "appeal_issue_sources", ["issue_id"])
    op.create_index(
        op.f("ix_appeal_issue_sources_citation_id"), "appeal_issue_sources", ["citation_id"]
    )

    op.create_table(
        "appeal_missing_material",
        sa.Column("issue_id", sa.UUID(), nullable=False),
        sa.Column("reference", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "state IN ('source_unavailable','court_treatment_not_located','unresolved')",
            name=op.f("ck_appeal_missing_material_state_allowed"),
        ),
        sa.ForeignKeyConstraint(
            ["issue_id"],
            ["appeal_issues.id"],
            ondelete="CASCADE",
            name=op.f("fk_appeal_missing_material_issue_id_appeal_issues"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_appeal_missing_material")),
        sa.UniqueConstraint("issue_id", "reference", name="uq_appeal_missing_material_reference"),
    )
    op.create_index(
        op.f("ix_appeal_missing_material_issue_id"), "appeal_missing_material", ["issue_id"]
    )

    op.create_table(
        "statement_comparisons",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("comparison_key", sa.String(64), nullable=False),
        sa.Column("issue_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("comparison_type", sa.String(40), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("statement_a_citation_id", sa.UUID(), nullable=False),
        sa.Column("statement_b_citation_id", sa.UUID(), nullable=False),
        sa.Column("statement_a_excerpt", sa.Text(), nullable=False),
        sa.Column("statement_b_excerpt", sa.Text(), nullable=False),
        sa.Column("statement_a_speaker", sa.String(128), nullable=True),
        sa.Column("statement_b_speaker", sa.String(128), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("extraction_origin", sa.String(64), nullable=False),
        *_verification_columns(),
        *_timestamps(),
        sa.CheckConstraint(
            "classification IN ('possible_contradiction','qualification','timeline_difference','consistent','not_comparable')",
            name=op.f("ck_statement_comparisons_classification_allowed"),
        ),
        sa.CheckConstraint(
            "comparison_type IN ('witness_statement_testimony','testimony_testimony','party_filing_court_summary','court_characterization_source','source_source')",
            name=op.f("ck_statement_comparisons_comparison_type_allowed"),
        ),
        sa.CheckConstraint(
            "statement_a_citation_id <> statement_b_citation_id",
            name=op.f("ck_statement_comparisons_distinct_sources"),
        ),
        _human_check("statement_comparisons"),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            ondelete="RESTRICT",
            name=op.f("fk_statement_comparisons_case_id_cases"),
        ),
        sa.ForeignKeyConstraint(
            ["issue_id"],
            ["appeal_issues.id"],
            ondelete="SET NULL",
            name=op.f("fk_statement_comparisons_issue_id_appeal_issues"),
        ),
        sa.ForeignKeyConstraint(
            ["statement_a_citation_id"],
            ["citations.id"],
            ondelete="RESTRICT",
            name=op.f("fk_statement_comparisons_statement_a_citation_id_citations"),
        ),
        sa.ForeignKeyConstraint(
            ["statement_b_citation_id"],
            ["citations.id"],
            ondelete="RESTRICT",
            name=op.f("fk_statement_comparisons_statement_b_citation_id_citations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_statement_comparisons")),
        sa.UniqueConstraint("case_id", "comparison_key", name="uq_statement_comparisons_case_key"),
    )
    op.create_index(op.f("ix_statement_comparisons_case_id"), "statement_comparisons", ["case_id"])
    op.create_index(
        op.f("ix_statement_comparisons_issue_id"), "statement_comparisons", ["issue_id"]
    )

    op.create_table(
        "red_team_reviews",
        sa.Column("issue_id", sa.UUID(), nullable=False),
        sa.Column("result", sa.String(32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("ai_run_id", sa.UUID(), nullable=True),
        *_verification_columns(),
        *_timestamps(),
        sa.CheckConstraint(
            "result IN ('supported_for_review','qualified','countered','insufficient_record')",
            name=op.f("ck_red_team_reviews_result_allowed"),
        ),
        sa.CheckConstraint(
            "origin IN ('human','ai_assisted')", name=op.f("ck_red_team_reviews_origin_allowed")
        ),
        sa.CheckConstraint(
            "(origin = 'ai_assisted') = (ai_run_id IS NOT NULL)",
            name=op.f("ck_red_team_reviews_ai_origin_matches_run"),
        ),
        _human_check("red_team_reviews"),
        sa.ForeignKeyConstraint(
            ["issue_id"],
            ["appeal_issues.id"],
            ondelete="CASCADE",
            name=op.f("fk_red_team_reviews_issue_id_appeal_issues"),
        ),
        sa.ForeignKeyConstraint(
            ["ai_run_id"],
            ["ai_runs.id"],
            ondelete="RESTRICT",
            name=op.f("fk_red_team_reviews_ai_run_id_ai_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_red_team_reviews")),
    )
    op.create_index(op.f("ix_red_team_reviews_issue_id"), "red_team_reviews", ["issue_id"])

    op.create_table(
        "red_team_findings",
        sa.Column("review_id", sa.UUID(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("perspective", sa.String(24), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("citation_id", sa.UUID(), nullable=True),
        *_verification_columns(),
        *_timestamps(),
        sa.CheckConstraint("sequence >= 1", name=op.f("ck_red_team_findings_sequence_positive")),
        sa.CheckConstraint(
            "perspective IN ('defence_analyst','spo_red_team','neutral_reviewer')",
            name=op.f("ck_red_team_findings_perspective_allowed"),
        ),
        sa.CheckConstraint(
            "category IN ('unsupported','missing_citation','ignored_evidence','unanswered','factual_dispute','legal_question','well_supported','human_required','counter_material','source_limitation')",
            name=op.f("ck_red_team_findings_category_allowed"),
        ),
        sa.CheckConstraint(
            "citation_id IS NOT NULL OR category IN ('missing_citation','legal_question','human_required','source_limitation')",
            name=op.f("ck_red_team_findings_uncited_only_for_explicit_gap"),
        ),
        _human_check("red_team_findings"),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["red_team_reviews.id"],
            ondelete="CASCADE",
            name=op.f("fk_red_team_findings_review_id_red_team_reviews"),
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            ondelete="RESTRICT",
            name=op.f("fk_red_team_findings_citation_id_citations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_red_team_findings")),
        sa.UniqueConstraint("review_id", "sequence", name="uq_red_team_findings_sequence"),
    )
    op.create_index(op.f("ix_red_team_findings_review_id"), "red_team_findings", ["review_id"])

    op.add_column("research_notes", sa.Column("appeal_issue_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_research_notes_appeal_issue_id_appeal_issues"),
        "research_notes",
        "appeal_issues",
        ["appeal_issue_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_research_notes_appeal_issue_id"), "research_notes", ["appeal_issue_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_research_notes_appeal_issue_id"), table_name="research_notes")
    op.drop_constraint(
        op.f("fk_research_notes_appeal_issue_id_appeal_issues"),
        "research_notes",
        type_="foreignkey",
    )
    op.drop_column("research_notes", "appeal_issue_id")
    op.drop_table("red_team_findings")
    op.drop_table("red_team_reviews")
    op.drop_table("statement_comparisons")
    op.drop_table("appeal_missing_material")
    op.drop_table("appeal_issue_sources")
    op.drop_table("appeal_issues")
