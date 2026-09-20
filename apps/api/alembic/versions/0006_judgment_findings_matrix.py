"""judgment findings and evidence matrix provenance

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE finding_link_type ADD VALUE IF NOT EXISTS 'contrary'")

    op.add_column("findings", sa.Column("judgment_version_id", sa.UUID(), nullable=True))
    op.add_column(
        "findings",
        sa.Column("extraction_origin", sa.String(32), server_default="manual", nullable=False),
    )
    op.create_foreign_key(
        "fk_findings_judgment_version_id_document_versions",
        "findings",
        "document_versions",
        ["judgment_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_findings_judgment_version_id", "findings", ["judgment_version_id"])

    op.add_column(
        "finding_evidence_links",
        sa.Column(
            "relationship_basis",
            sa.String(32),
            server_default="related_public_record",
            nullable=False,
        ),
    )
    op.execute(
        "UPDATE finding_evidence_links SET relationship_basis = "
        "CASE WHEN court_cited THEN 'explicit_court_citation' ELSE 'related_public_record' END"
    )
    op.add_column(
        "finding_evidence_links",
        sa.Column("source_category", sa.String(32), server_default="other", nullable=False),
    )
    op.add_column(
        "finding_evidence_links",
        sa.Column("extraction_origin", sa.String(32), server_default="manual", nullable=False),
    )
    op.add_column("finding_evidence_links", sa.Column("note", sa.Text(), nullable=True))
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_relationship_basis_allowed"),
        "finding_evidence_links",
        "relationship_basis IN ('explicit_court_citation', 'related_public_record')",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_court_cited_matches_basis"),
        "finding_evidence_links",
        "court_cited = (relationship_basis = 'explicit_court_citation')",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_source_category_allowed"),
        "finding_evidence_links",
        "source_category IN ('court_finding', 'spo_argument', 'defence_argument', "
        "'witness_testimony', 'document_exhibit', 'court_response', 'human_note', "
        "'ai_analysis', 'other')",
    )

    op.add_column("arguments", sa.Column("document_version_id", sa.UUID(), nullable=True))
    op.add_column(
        "arguments",
        sa.Column("source_scope", sa.String(32), server_default="direct_source", nullable=False),
    )
    op.add_column("arguments", sa.Column("underlying_source_ref", sa.String(255), nullable=True))
    op.add_column(
        "arguments",
        sa.Column("extraction_origin", sa.String(32), server_default="manual", nullable=False),
    )
    op.create_foreign_key(
        "fk_arguments_document_version_id_document_versions",
        "arguments",
        "document_versions",
        ["document_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_arguments_document_version_id", "arguments", ["document_version_id"])
    op.create_check_constraint(
        op.f("ck_arguments_source_scope_allowed"),
        "arguments",
        "source_scope IN ('direct_source', 'court_summary', 'source_missing')",
    )

    verification_state = sa.Enum(
        "unreviewed",
        "ai_flagged",
        "human_verified",
        "human_rejected",
        "needs_more_evidence",
        "unresolved",
        name="verification_state",
        create_type=False,
    )
    op.add_column(
        "argument_responses",
        sa.Column(
            "verification_state",
            verification_state,
            server_default="unreviewed",
            nullable=False,
        ),
    )
    op.add_column("argument_responses", sa.Column("verified_by", sa.String(128), nullable=True))
    op.add_column(
        "argument_responses", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "argument_responses",
        sa.Column("extraction_origin", sa.String(32), server_default="manual", nullable=False),
    )
    op.create_check_constraint(
        op.f("ck_argument_responses_human_verification_has_reviewer"),
        "argument_responses",
        "verification_state NOT IN ('human_verified', 'human_rejected') "
        "OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
    )

    op.add_column("research_notes", sa.Column("finding_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_research_notes_finding_id_findings",
        "research_notes",
        "findings",
        ["finding_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_research_notes_finding_id", "research_notes", ["finding_id"])


def downgrade() -> None:
    op.drop_index("ix_research_notes_finding_id", table_name="research_notes")
    op.drop_constraint(
        "fk_research_notes_finding_id_findings", "research_notes", type_="foreignkey"
    )
    op.drop_column("research_notes", "finding_id")

    op.drop_column("argument_responses", "extraction_origin")
    op.drop_column("argument_responses", "verified_at")
    op.drop_column("argument_responses", "verified_by")
    op.drop_column("argument_responses", "verification_state")

    op.drop_index("ix_arguments_document_version_id", table_name="arguments")
    op.drop_constraint(
        "fk_arguments_document_version_id_document_versions", "arguments", type_="foreignkey"
    )
    op.drop_column("arguments", "extraction_origin")
    op.drop_column("arguments", "underlying_source_ref")
    op.drop_column("arguments", "source_scope")
    op.drop_column("arguments", "document_version_id")

    op.drop_column("finding_evidence_links", "note")
    op.drop_column("finding_evidence_links", "extraction_origin")
    op.drop_column("finding_evidence_links", "source_category")
    op.drop_column("finding_evidence_links", "relationship_basis")

    op.drop_index("ix_findings_judgment_version_id", table_name="findings")
    op.drop_constraint(
        "fk_findings_judgment_version_id_document_versions", "findings", type_="foreignkey"
    )
    op.drop_column("findings", "extraction_origin")
    op.drop_column("findings", "judgment_version_id")
    # PostgreSQL enum values are intentionally retained on downgrade.
