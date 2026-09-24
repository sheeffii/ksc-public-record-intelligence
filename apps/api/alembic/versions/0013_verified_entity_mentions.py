"""verified entity mention lineage (Phase 19A)

Revision ID: 0013
Revises: 0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNIQUE_COLUMNS = (
    "document_version_id",
    "char_anchor",
    "transcript_segment_id",
    "pdf_page_index",
    "char_start",
    "char_end",
    "person_id",
    "witness_id",
    "organization_id",
    "exhibit_id",
    "rule_id",
)


def upgrade() -> None:
    op.add_column(
        "entity_occurrences",
        sa.Column("mention_state", sa.String(length=16), server_default="verified", nullable=False),
    )
    # Legacy Phase 17C rows carry the old boolean; keep the two consistent.
    op.execute(
        "UPDATE entity_occurrences SET mention_state = 'review_required' WHERE review_required"
    )
    op.add_column("entity_occurrences", sa.Column("rule_id", sa.String(length=64)))
    op.add_column("entity_occurrences", sa.Column("rule_version", sa.Integer()))
    op.add_column(
        "entity_occurrences",
        sa.Column("projection_run_id", postgresql.UUID(as_uuid=True)),
    )
    op.add_column("entity_occurrences", sa.Column("char_anchor", sa.String(length=32)))
    op.add_column("entity_occurrences", sa.Column("paragraph_number", sa.Integer()))
    op.add_column("entity_occurrences", sa.Column("language", sa.String(length=16)))
    op.create_foreign_key(
        op.f("fk_entity_occurrences_projection_run_id_processing_runs"),
        "entity_occurrences",
        "processing_runs",
        ["projection_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        op.f("ck_entity_occurrences_mention_state_allowed"),
        "entity_occurrences",
        "mention_state IN ('verified', 'review_required', 'rejected')",
    )
    op.create_check_constraint(
        op.f("ck_entity_occurrences_review_flag_matches_state"),
        "entity_occurrences",
        "review_required = (mention_state = 'review_required')",
    )
    op.create_check_constraint(
        op.f("ck_entity_occurrences_char_anchor_allowed"),
        "entity_occurrences",
        "char_anchor IS NULL OR char_anchor IN "
        "('transcript_segment_text', 'transcript_speaker_label', 'document_page_text')",
    )
    op.create_check_constraint(
        op.f("ck_entity_occurrences_rule_lineage_complete"),
        "entity_occurrences",
        "rule_id IS NULL OR (rule_version IS NOT NULL AND char_anchor IS NOT NULL)",
    )
    op.drop_constraint("uq_entity_occurrences_source_entity", "entity_occurrences", type_="unique")
    op.create_unique_constraint(
        "uq_entity_occurrences_source_rule",
        "entity_occurrences",
        list(_UNIQUE_COLUMNS),
        postgresql_nulls_not_distinct=True,
    )
    op.create_index(
        op.f("ix_entity_occurrences_mention_state"), "entity_occurrences", ["mention_state"]
    )
    op.create_index(op.f("ix_entity_occurrences_rule_id"), "entity_occurrences", ["rule_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_entity_occurrences_rule_id"), table_name="entity_occurrences")
    op.drop_index(op.f("ix_entity_occurrences_mention_state"), table_name="entity_occurrences")
    op.drop_constraint("uq_entity_occurrences_source_rule", "entity_occurrences", type_="unique")
    # Phase 19 rows may share a span with legacy rows under a different rule;
    # the pre-19 constraint cannot hold them, so they are dropped on downgrade.
    op.execute("DELETE FROM entity_occurrences WHERE rule_id IS NOT NULL")
    op.create_unique_constraint(
        "uq_entity_occurrences_source_entity",
        "entity_occurrences",
        [
            "document_version_id",
            "transcript_segment_id",
            "char_start",
            "char_end",
            "person_id",
            "witness_id",
            "organization_id",
            "exhibit_id",
        ],
    )
    for name in (
        "rule_lineage_complete",
        "char_anchor_allowed",
        "review_flag_matches_state",
        "mention_state_allowed",
    ):
        op.drop_constraint(
            op.f(f"ck_entity_occurrences_{name}"), "entity_occurrences", type_="check"
        )
    op.drop_constraint(
        op.f("fk_entity_occurrences_projection_run_id_processing_runs"),
        "entity_occurrences",
        type_="foreignkey",
    )
    for column in (
        "language",
        "paragraph_number",
        "char_anchor",
        "projection_run_id",
        "rule_version",
        "rule_id",
        "mention_state",
    ):
        op.drop_column("entity_occurrences", column)
