"""Phase 22A evidence-matrix and legal-issue semantics

Revision ID: 0017
Revises: 0016
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UUID = postgresql.UUID(as_uuid=True)
_RELATIONS = (
    "court_relies_on",
    "court_cites",
    "party_cites",
    "supports",
    "qualifies",
    "contrary",
    "context",
)
_SOURCE_CATEGORIES = (
    "court_finding",
    "spo_argument",
    "defence_argument",
    "victims_counsel_argument",
    "witness_testimony",
    "document_exhibit",
    "court_response",
    "human_note",
    "ai_analysis",
    "external_public_source",
    "public_authority",
    "other",
)
_ANCHOR_TYPES_22A = (
    "entity_occurrence",
    "citation",
    "relationship",
    "finding",
    "transcript_segment",
    "finding_evidence_link",
    "argument",
    "appeal_issue_source",
)


def _quoted(values: tuple[str, ...]) -> str:
    return "(" + ",".join(f"'{value}'" for value in values) + ")"


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(*_RELATIONS, name="evidence_matrix_relation").create(bind, checkfirst=False)

    op.drop_constraint(
        op.f("ck_finding_evidence_links_court_cited_matches_basis"),
        "finding_evidence_links",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_finding_evidence_links_relationship_basis_allowed"),
        "finding_evidence_links",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_finding_evidence_links_source_category_allowed"),
        "finding_evidence_links",
        type_="check",
    )
    op.execute(
        "ALTER TABLE finding_evidence_links ALTER COLUMN link_type TYPE "
        "evidence_matrix_relation USING (CASE "
        "WHEN link_type::text = 'relies_on' THEN 'court_relies_on' "
        "WHEN link_type::text = 'supports' AND court_cited THEN 'court_cites' "
        "ELSE link_type::text END)::evidence_matrix_relation"
    )
    op.execute("DROP TYPE finding_link_type")

    op.add_column(
        "finding_evidence_links",
        sa.Column(
            "classification_origin",
            sa.String(24),
            nullable=False,
            server_default="source_derived",
        ),
    )
    op.add_column(
        "finding_evidence_links", sa.Column("review_process", sa.String(128), nullable=True)
    )
    op.add_column("finding_evidence_links", sa.Column("source_anchor_id", _UUID, nullable=True))
    op.create_foreign_key(
        op.f("fk_finding_evidence_links_source_anchor_id_source_anchors"),
        "finding_evidence_links",
        "source_anchors",
        ["source_anchor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_finding_evidence_links_source_anchor_id",
        "finding_evidence_links",
        ["source_anchor_id"],
    )
    op.execute(
        "UPDATE finding_evidence_links SET relationship_basis = CASE "
        "WHEN link_type = 'court_relies_on' THEN 'explicit_court_reliance' "
        "WHEN link_type = 'court_cites' THEN 'explicit_court_citation' "
        "ELSE 'human_classification' END, "
        "classification_origin = CASE WHEN link_type IN "
        "('court_relies_on','court_cites','party_cites') THEN 'source_derived' "
        "ELSE 'human_defined' END, "
        "review_process = CASE WHEN link_type IN "
        "('supports','qualifies','contrary','context') THEN "
        "COALESCE(verified_by, 'legacy_human_review') ELSE NULL END"
    )
    op.execute(
        "UPDATE finding_evidence_links SET note = "
        "'The Panel''s paragraphs 12-16 reasoning uses the corrected SPO brief and its "
        "exhibit-reference substitutions. This records source-backed Court reliance for that "
        "reasoning; it does not imply endorsement or evidential weight beyond the cited passage.' "
        "WHERE link_type = 'court_relies_on' AND note = "
        "'The Panel''s reasoning expressly identifies the corrected SPO brief. This link records "
        "citation, not endorsement or evidential weight.'"
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_relationship_basis_allowed"),
        "finding_evidence_links",
        "relationship_basis IN ('explicit_court_reliance','explicit_court_citation',"
        "'explicit_party_citation','human_classification','ai_suggestion',"
        "'related_public_record')",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_court_cited_matches_relation"),
        "finding_evidence_links",
        "(link_type IN ('court_relies_on','court_cites') AND court_cited) OR "
        "(link_type NOT IN ('court_relies_on','court_cites') AND NOT court_cited)",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_relation_matches_basis"),
        "finding_evidence_links",
        "(link_type = 'court_relies_on' AND relationship_basis = "
        "'explicit_court_reliance') OR "
        "(link_type = 'court_cites' AND relationship_basis = "
        "'explicit_court_citation') OR "
        "(link_type = 'party_cites' AND relationship_basis = "
        "'explicit_party_citation') OR "
        "(link_type IN ('supports','qualifies','contrary','context') AND "
        "relationship_basis IN ('human_classification','ai_suggestion',"
        "'related_public_record'))",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_relation_matches_origin"),
        "finding_evidence_links",
        "(link_type IN ('court_relies_on','court_cites','party_cites') AND "
        "classification_origin = 'source_derived') OR "
        "(link_type IN ('supports','qualifies','contrary','context') AND "
        "classification_origin IN ('human_defined','ai_suggested'))",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_research_relation_has_process"),
        "finding_evidence_links",
        "link_type NOT IN ('supports','qualifies','contrary','context') OR "
        "review_process IS NOT NULL",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_ai_suggestion_not_verified"),
        "finding_evidence_links",
        "classification_origin != 'ai_suggested' OR "
        "(relationship_basis = 'ai_suggestion' AND verification_state IN "
        "('unreviewed','ai_flagged','needs_more_evidence','unresolved'))",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_source_category_allowed"),
        "finding_evidence_links",
        f"source_category IN {_quoted(_SOURCE_CATEGORIES)}",
    )

    op.add_column("arguments", sa.Column("party_attribution", sa.String(255), nullable=True))
    op.execute(
        "UPDATE arguments SET party_attribution = CASE party::text "
        "WHEN 'spo' THEN 'SPO' WHEN 'defence' THEN 'Defence' "
        "WHEN 'victims_counsel' THEN 'Victims'' Counsel' WHEN 'court' THEN 'Court' "
        "ELSE 'Other' END"
    )
    op.add_column("arguments", sa.Column("source_anchor_id", _UUID, nullable=True))
    op.create_foreign_key(
        op.f("fk_arguments_source_anchor_id_source_anchors"),
        "arguments",
        "source_anchors",
        ["source_anchor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_arguments_source_anchor_id", "arguments", ["source_anchor_id"])

    op.add_column(
        "appeal_issues",
        sa.Column(
            "definition_origin",
            sa.String(24),
            nullable=False,
            server_default="human_defined",
        ),
    )
    op.create_check_constraint(
        op.f("ck_appeal_issues_definition_origin_allowed"),
        "appeal_issues",
        "definition_origin IN ('human_defined','source_derived','ai_suggested')",
    )

    op.drop_constraint(
        op.f("ck_appeal_issue_sources_source_category_allowed"),
        "appeal_issue_sources",
        type_="check",
    )
    op.add_column(
        "appeal_issue_sources",
        sa.Column(
            "classification_origin",
            sa.String(24),
            nullable=False,
            server_default="source_derived",
        ),
    )
    op.add_column(
        "appeal_issue_sources", sa.Column("review_process", sa.String(128), nullable=True)
    )
    op.add_column("appeal_issue_sources", sa.Column("source_anchor_id", _UUID, nullable=True))
    op.create_foreign_key(
        op.f("fk_appeal_issue_sources_source_anchor_id_source_anchors"),
        "appeal_issue_sources",
        "source_anchors",
        ["source_anchor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_appeal_issue_sources_source_anchor_id",
        "appeal_issue_sources",
        ["source_anchor_id"],
    )
    op.create_check_constraint(
        op.f("ck_appeal_issue_sources_source_category_allowed"),
        "appeal_issue_sources",
        "source_category IN ('court_finding','spo_argument','defence_argument',"
        "'victims_counsel_argument','witness_testimony','document_exhibit',"
        "'court_response','public_authority','human_note','ai_analysis',"
        "'external_public_source')",
    )
    op.create_check_constraint(
        op.f("ck_appeal_issue_sources_classification_origin_allowed"),
        "appeal_issue_sources",
        "classification_origin IN ('source_derived','human_defined','ai_suggested')",
    )
    op.create_check_constraint(
        op.f("ck_appeal_issue_sources_research_role_has_process"),
        "appeal_issue_sources",
        "role NOT IN ('supporting','contrary','qualifying') OR "
        "(classification_origin IN ('human_defined','ai_suggested') AND "
        "review_process IS NOT NULL)",
    )
    op.create_check_constraint(
        op.f("ck_appeal_issue_sources_ai_suggestion_not_verified"),
        "appeal_issue_sources",
        "classification_origin != 'ai_suggested' OR verification_state IN "
        "('unreviewed','ai_flagged','needs_more_evidence','unresolved')",
    )

    op.drop_constraint(
        op.f("ck_source_anchors_ck_source_anchors_object_type_allowed"),
        "source_anchors",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_source_anchors_object_type_allowed"),
        "source_anchors",
        f"object_type IN {_quoted(_ANCHOR_TYPES_22A)}",
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.execute(
        "DELETE FROM source_anchors WHERE object_type IN "
        "('finding_evidence_link','argument','appeal_issue_source')"
    )
    op.execute(
        "DELETE FROM source_spans s WHERE NOT EXISTS "
        "(SELECT 1 FROM source_anchors a WHERE a.source_span_id = s.id) AND EXISTS "
        "(SELECT 1 FROM processing_runs r WHERE r.id = s.processing_run_id "
        "AND r.processor = 'phase22a-legal-matrix')"
    )
    op.drop_constraint(
        op.f("ck_source_anchors_object_type_allowed"), "source_anchors", type_="check"
    )
    op.create_check_constraint(
        op.f("ck_source_anchors_ck_source_anchors_object_type_allowed"),
        "source_anchors",
        "object_type IN ('entity_occurrence','citation','relationship','finding',"
        "'transcript_segment')",
    )

    op.drop_constraint(
        op.f("ck_appeal_issue_sources_ai_suggestion_not_verified"),
        "appeal_issue_sources",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_appeal_issue_sources_research_role_has_process"),
        "appeal_issue_sources",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_appeal_issue_sources_classification_origin_allowed"),
        "appeal_issue_sources",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_appeal_issue_sources_source_category_allowed"),
        "appeal_issue_sources",
        type_="check",
    )
    op.drop_index("ix_appeal_issue_sources_source_anchor_id", table_name="appeal_issue_sources")
    op.drop_constraint(
        op.f("fk_appeal_issue_sources_source_anchor_id_source_anchors"),
        "appeal_issue_sources",
        type_="foreignkey",
    )
    op.drop_column("appeal_issue_sources", "source_anchor_id")
    op.drop_column("appeal_issue_sources", "review_process")
    op.drop_column("appeal_issue_sources", "classification_origin")
    op.create_check_constraint(
        op.f("ck_appeal_issue_sources_source_category_allowed"),
        "appeal_issue_sources",
        "source_category IN ('court_finding','spo_argument','defence_argument',"
        "'witness_testimony','document_exhibit','court_response','public_authority')",
    )

    op.drop_constraint(
        op.f("ck_appeal_issues_definition_origin_allowed"), "appeal_issues", type_="check"
    )
    op.drop_column("appeal_issues", "definition_origin")

    op.drop_index("ix_arguments_source_anchor_id", table_name="arguments")
    op.drop_constraint(
        op.f("fk_arguments_source_anchor_id_source_anchors"),
        "arguments",
        type_="foreignkey",
    )
    op.drop_column("arguments", "source_anchor_id")
    op.drop_column("arguments", "party_attribution")

    for name in (
        "ai_suggestion_not_verified",
        "research_relation_has_process",
        "relation_matches_origin",
        "relation_matches_basis",
        "court_cited_matches_relation",
        "relationship_basis_allowed",
        "source_category_allowed",
    ):
        op.drop_constraint(
            op.f(f"ck_finding_evidence_links_{name}"),
            "finding_evidence_links",
            type_="check",
        )
    op.drop_index("ix_finding_evidence_links_source_anchor_id", table_name="finding_evidence_links")
    op.drop_constraint(
        op.f("fk_finding_evidence_links_source_anchor_id_source_anchors"),
        "finding_evidence_links",
        type_="foreignkey",
    )
    op.drop_column("finding_evidence_links", "source_anchor_id")
    op.drop_column("finding_evidence_links", "review_process")
    op.drop_column("finding_evidence_links", "classification_origin")

    op.execute(
        "UPDATE finding_evidence_links SET note = "
        "'The Panel''s reasoning expressly identifies the corrected SPO brief. This link records "
        "citation, not endorsement or evidential weight.' WHERE link_type = 'court_relies_on' "
        "AND note = 'The Panel''s paragraphs 12-16 reasoning uses the corrected SPO brief and its "
        "exhibit-reference substitutions. This records source-backed Court reliance for that "
        "reasoning; it does not imply endorsement or evidential weight beyond the cited passage.'"
    )
    postgresql.ENUM(
        "relies_on", "supports", "qualifies", "contrary", "context", name="finding_link_type"
    ).create(bind, checkfirst=False)
    op.execute(
        "ALTER TABLE finding_evidence_links ALTER COLUMN link_type TYPE finding_link_type "
        "USING (CASE WHEN link_type::text = 'court_relies_on' THEN 'relies_on' "
        "WHEN link_type::text = 'court_cites' THEN 'supports' "
        "WHEN link_type::text = 'party_cites' THEN 'context' "
        "ELSE link_type::text END)::finding_link_type"
    )
    postgresql.ENUM(name="evidence_matrix_relation").drop(bind, checkfirst=False)
    op.execute(
        "UPDATE finding_evidence_links SET relationship_basis = CASE WHEN court_cited "
        "THEN 'explicit_court_citation' ELSE 'related_public_record' END"
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_relationship_basis_allowed"),
        "finding_evidence_links",
        "relationship_basis IN ('explicit_court_citation','related_public_record')",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_court_cited_matches_basis"),
        "finding_evidence_links",
        "court_cited = (relationship_basis = 'explicit_court_citation')",
    )
    op.create_check_constraint(
        op.f("ck_finding_evidence_links_source_category_allowed"),
        "finding_evidence_links",
        "source_category IN ('court_finding','spo_argument','defence_argument',"
        "'witness_testimony','document_exhibit','court_response','human_note',"
        "'ai_analysis','other')",
    )
