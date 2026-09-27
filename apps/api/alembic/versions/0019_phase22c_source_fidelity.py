"""Phase 22C conservative Court-citation correction.

Revision ID: 0019
Revises: 0018
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FINDING_KEY = "FD-F03752-P12-16"
_CITATION_NOTE = (
    "The Panel's paragraph 12 expressly identifies the corrected SPO brief while describing "
    "its exhibit-reference substitutions. This records an exact Court citation, not Court "
    "reliance or endorsement."
)
_OLD_NOTE = (
    "The Panel's paragraphs 12\N{EN DASH}16 reasoning uses the corrected SPO brief and its "
    "exhibit-reference substitutions. This records source-backed Court reliance for that "
    "reasoning; it does not imply endorsement or evidential weight beyond the cited passage."
)


def upgrade() -> None:
    bind = op.get_bind()
    op.drop_constraint(
        op.f("ck_appeal_issue_sources_role_allowed"),
        "appeal_issue_sources",
        type_="check",
    )
    bind.execute(
        sa.text(
            "UPDATE finding_evidence_links fel SET link_type = 'court_cites', "
            "relationship_basis = 'explicit_court_citation', note = :note "
            "FROM findings f WHERE fel.finding_id = f.id AND "
            "f.finding_key = :key AND fel.link_type = 'court_relies_on'"
        ),
        {"note": _CITATION_NOTE, "key": _FINDING_KEY},
    )
    bind.execute(
        sa.text(
            "UPDATE relationships r SET relationship_type = 'cited_in', "
            "note = 'Phase 22C source-fidelity audit: court_cites' FROM "
            "finding_evidence_links fel JOIN findings f ON f.id = fel.finding_id "
            "WHERE r.citation_id = fel.citation_id AND "
            "f.finding_key = :key AND r.relationship_type = 'relies_on'"
        ),
        {"key": _FINDING_KEY},
    )
    bind.execute(
        sa.text(
            "UPDATE appeal_issue_sources ais SET role = 'court_cited_material', "
            "note = 'Exact material expressly identified by the Court; reliance is not inferred.' "
            "FROM appeal_issues ai JOIN findings f ON f.id = ai.finding_id "
            "WHERE ais.issue_id = ai.id AND "
            "f.finding_key = :key AND ais.role = 'evidence_relied'"
        ),
        {"key": _FINDING_KEY},
    )
    op.create_check_constraint(
        op.f("ck_appeal_issue_sources_role_allowed"),
        "appeal_issue_sources",
        "role IN ('court_reasoning','applicable_standard','court_cited_material',"
        "'defence_position','spo_position','court_response','supporting','contrary',"
        "'qualifying')",
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_constraint(
        op.f("ck_appeal_issue_sources_role_allowed"),
        "appeal_issue_sources",
        type_="check",
    )
    bind.execute(
        sa.text(
            "UPDATE appeal_issue_sources ais SET role = 'evidence_relied', "
            "note = 'Exact source expressly identified by the Court.' "
            "FROM appeal_issues ai JOIN findings f ON f.id = ai.finding_id "
            "WHERE ais.issue_id = ai.id AND "
            "f.finding_key = :key AND ais.role = 'court_cited_material'"
        ),
        {"key": _FINDING_KEY},
    )
    bind.execute(
        sa.text(
            "UPDATE relationships r SET relationship_type = 'relies_on', "
            "note = 'Phase 22A matrix projection: court_relies_on' FROM "
            "finding_evidence_links fel JOIN findings f ON f.id = fel.finding_id "
            "WHERE r.citation_id = fel.citation_id AND "
            "f.finding_key = :key AND r.relationship_type = 'cited_in'"
        ),
        {"key": _FINDING_KEY},
    )
    bind.execute(
        sa.text(
            "UPDATE finding_evidence_links fel SET link_type = 'court_relies_on', "
            "relationship_basis = 'explicit_court_reliance', note = :note "
            "FROM findings f WHERE fel.finding_id = f.id AND "
            "f.finding_key = :key AND fel.link_type = 'court_cites'"
        ),
        {"note": _OLD_NOTE, "key": _FINDING_KEY},
    )
    op.create_check_constraint(
        op.f("ck_appeal_issue_sources_role_allowed"),
        "appeal_issue_sources",
        "role IN ('court_reasoning','applicable_standard','evidence_relied',"
        "'defence_position','spo_position','court_response','supporting','contrary',"
        "'qualifying')",
    )
