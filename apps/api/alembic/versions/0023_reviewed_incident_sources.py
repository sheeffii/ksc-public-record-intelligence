"""Reviewed incidents: source category, human review and exact sources.

An incident records what a source alleges or describes, never a determination.
`source_category` says whose account it is (the first reviewed batch is SPO
allegations from the operative Amended Indictment); the verification columns
record the human review; `incident_sources` binds the incident to exact source
paragraphs (operative text, version history, withdrawal review). Operative
sources carry a SourceAnchor, rebuilt by the legal-matrix projection. A
location may name the municipality it lies in; no coordinates are added.

Revision ID: 0023
Revises: 0022
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ANCHOR_TYPES = (
    "entity_occurrence",
    "citation",
    "relationship",
    "finding",
    "transcript_segment",
    "finding_evidence_link",
    "argument",
    "appeal_issue_source",
)


def _quoted(values: Sequence[str]) -> str:
    return "(" + ",".join(f"'{value}'" for value in values) + ")"


def upgrade() -> None:
    verification = postgresql.ENUM(name="verification_state", create_type=False)
    op.add_column("incidents", sa.Column("source_category", sa.String(32), nullable=True))
    op.add_column(
        "incidents",
        sa.Column("verification_state", verification, nullable=False, server_default="unreviewed"),
    )
    op.add_column("incidents", sa.Column("verified_by", sa.String(128), nullable=True))
    op.add_column("incidents", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("incidents", sa.Column("date_as_pleaded", sa.Text(), nullable=True))
    op.add_column("incidents", sa.Column("review_decision", postgresql.JSONB(), nullable=True))
    op.add_column(
        "incidents",
        sa.Column("extraction_origin", sa.String(32), nullable=False, server_default="manual"),
    )
    op.create_check_constraint(
        "source_category_allowed", "incidents", "source_category IN ('spo_allegation')"
    )
    op.create_check_constraint(
        "human_verification_has_reviewer",
        "incidents",
        "verification_state NOT IN ('human_verified', 'human_rejected') "
        "OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
    )

    op.add_column(
        "locations",
        sa.Column(
            "parent_location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "not_own_parent", "locations", "parent_location_id IS NULL OR parent_location_id <> id"
    )

    op.create_table(
        "incident_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("source_ref", sa.String(255), nullable=False),
        sa.Column(
            "document_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_versions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("paragraph_number", sa.Integer(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "source_anchor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_anchors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verification_state", verification, nullable=False, server_default="unreviewed"),
        sa.Column("verified_by", sa.String(128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("incident_id", "sequence", name="uq_incident_sources_sequence"),
        sa.CheckConstraint("sequence >= 1", name="sequence_positive"),
        sa.CheckConstraint(
            "role IN ('operative', 'version_history', 'withdrawal_review')", name="role_allowed"
        ),
        # Only the operative text is quoted and anchored; the others are provenance.
        sa.CheckConstraint(
            "(role = 'operative') = (excerpt IS NOT NULL)", name="excerpt_only_operative"
        ),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') "
            "OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name="human_verification_has_reviewer",
        ),
    )

    op.drop_constraint(
        op.f("ck_source_anchors_object_type_allowed"), "source_anchors", type_="check"
    )
    op.create_check_constraint(
        op.f("ck_source_anchors_object_type_allowed"),
        "source_anchors",
        f"object_type IN {_quoted((*_ANCHOR_TYPES, 'incident_source'))}",
    )


def downgrade() -> None:
    op.execute("DELETE FROM source_anchors WHERE object_type = 'incident_source'")
    op.drop_constraint(
        op.f("ck_source_anchors_object_type_allowed"), "source_anchors", type_="check"
    )
    op.create_check_constraint(
        op.f("ck_source_anchors_object_type_allowed"),
        "source_anchors",
        f"object_type IN {_quoted(_ANCHOR_TYPES)}",
    )
    op.drop_table("incident_sources")
    op.drop_constraint("not_own_parent", "locations", type_="check")
    op.drop_column("locations", "parent_location_id")
    op.drop_constraint("human_verification_has_reviewer", "incidents", type_="check")
    op.drop_constraint("source_category_allowed", "incidents", type_="check")
    for column in (
        "extraction_origin",
        "review_decision",
        "date_as_pleaded",
        "verified_at",
        "verified_by",
        "verification_state",
        "source_category",
    ):
        op.drop_column("incidents", column)
