"""Let an appeal missing-material entry be resolved by a held source.

Revision ID: 0022
Revises: 0021
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "appeal_missing_material", sa.Column("resolved_source_ref", sa.String(255), nullable=True)
    )
    op.drop_constraint("state_allowed", "appeal_missing_material", type_="check")
    op.create_check_constraint(
        "state_allowed",
        "appeal_missing_material",
        "state IN ('source_unavailable', 'court_treatment_not_located', 'unresolved', 'resolved')",
    )
    op.create_check_constraint(
        "resolved_has_source",
        "appeal_missing_material",
        "(state = 'resolved') = (resolved_source_ref IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("resolved_has_source", "appeal_missing_material", type_="check")
    op.execute(
        "UPDATE appeal_missing_material SET state = 'source_unavailable' WHERE state = 'resolved'"
    )
    op.drop_constraint("state_allowed", "appeal_missing_material", type_="check")
    op.create_check_constraint(
        "state_allowed",
        "appeal_missing_material",
        "state IN ('source_unavailable', 'court_treatment_not_located', 'unresolved')",
    )
    op.drop_column("appeal_missing_material", "resolved_source_ref")
