"""Phase 22B neutral passage-comparison review semantics.

Revision ID: 0018
Revises: 0017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("ck_statement_comparisons_classification_allowed"),
        "statement_comparisons",
        type_="check",
    )
    op.add_column(
        "statement_comparisons",
        sa.Column(
            "candidate_origin", sa.String(24), nullable=False, server_default="source_derived"
        ),
    )
    op.add_column(
        "statement_comparisons", sa.Column("review_process", sa.String(128), nullable=True)
    )
    op.execute(
        "UPDATE statement_comparisons SET classification = CASE classification "
        "WHEN 'possible_contradiction' THEN 'potential_tension' "
        "WHEN 'qualification' THEN 'potential_qualification' "
        "WHEN 'timeline_difference' THEN 'potential_difference' ELSE classification END, "
        "review_process = CASE WHEN verified_by IS NOT NULL THEN verified_by ELSE NULL END"
    )
    op.create_check_constraint(
        op.f("ck_statement_comparisons_classification_allowed"),
        "statement_comparisons",
        "classification IN ('potential_tension','potential_difference',"
        "'potential_qualification','contradiction','consistent','not_comparable')",
    )
    op.create_check_constraint(
        op.f("ck_statement_comparisons_candidate_origin_allowed"),
        "statement_comparisons",
        "candidate_origin IN ('source_derived','human_defined','ai_suggested')",
    )
    op.create_check_constraint(
        op.f("ck_statement_comparisons_contradiction_requires_human_review"),
        "statement_comparisons",
        "classification != 'contradiction' OR (verification_state = 'human_verified' "
        "AND verified_by IS NOT NULL)",
    )
    op.create_check_constraint(
        op.f("ck_statement_comparisons_ai_suggestion_not_verified"),
        "statement_comparisons",
        "candidate_origin != 'ai_suggested' OR verification_state IN "
        "('unreviewed','ai_flagged','needs_more_evidence','unresolved')",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_statement_comparisons_ai_suggestion_not_verified"),
        "statement_comparisons",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_statement_comparisons_contradiction_requires_human_review"),
        "statement_comparisons",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_statement_comparisons_candidate_origin_allowed"),
        "statement_comparisons",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_statement_comparisons_classification_allowed"),
        "statement_comparisons",
        type_="check",
    )
    op.execute(
        "UPDATE statement_comparisons SET classification = CASE classification "
        "WHEN 'potential_tension' THEN 'possible_contradiction' "
        "WHEN 'potential_qualification' THEN 'qualification' "
        "WHEN 'potential_difference' THEN 'timeline_difference' "
        "WHEN 'contradiction' THEN 'possible_contradiction' ELSE classification END"
    )
    op.drop_column("statement_comparisons", "review_process")
    op.drop_column("statement_comparisons", "candidate_origin")
    op.create_check_constraint(
        op.f("ck_statement_comparisons_classification_allowed"),
        "statement_comparisons",
        "classification IN ('possible_contradiction','qualification','timeline_difference',"
        "'consistent','not_comparable')",
    )
