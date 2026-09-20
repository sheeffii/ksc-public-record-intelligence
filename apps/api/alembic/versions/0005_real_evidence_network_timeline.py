"""real evidence-network and timeline provenance

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RELATIONSHIP_ORIGIN = postgresql.ENUM(
    "source_documented",
    "deterministic_citation",
    "analytical",
    name="relationship_origin",
    create_type=False,
)


def upgrade() -> None:
    RELATIONSHIP_ORIGIN.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "relationships",
        sa.Column("source_category", sa.String(32), server_default="court", nullable=False),
    )
    op.add_column(
        "relationships",
        sa.Column(
            "extraction_origin",
            RELATIONSHIP_ORIGIN,
            server_default="source_documented",
            nullable=False,
        ),
    )
    op.add_column("relationships", sa.Column("relationship_date", sa.Date(), nullable=True))
    date_precision = postgresql.ENUM(
        "exact",
        "month_only",
        "year_only",
        "range",
        "approximate",
        "unknown",
        name="date_precision",
        create_type=False,
    )
    op.add_column(
        "relationships",
        sa.Column("date_precision", date_precision, server_default="unknown", nullable=False),
    )
    op.add_column("events", sa.Column("source_record_id", sa.UUID(), nullable=True))
    op.add_column(
        "events",
        sa.Column("extraction_origin", sa.String(32), server_default="manual", nullable=False),
    )
    op.create_foreign_key(
        "fk_events_source_record_id_source_records",
        "events",
        "source_records",
        ["source_record_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_events_source_record_id", "events", ["source_record_id"])


def downgrade() -> None:
    op.drop_index("ix_events_source_record_id", table_name="events")
    op.drop_constraint("fk_events_source_record_id_source_records", "events", type_="foreignkey")
    op.drop_column("events", "extraction_origin")
    op.drop_column("events", "source_record_id")
    op.drop_column("relationships", "date_precision")
    op.drop_column("relationships", "relationship_date")
    op.drop_column("relationships", "extraction_origin")
    op.drop_column("relationships", "source_category")
    RELATIONSHIP_ORIGIN.drop(op.get_bind(), checkfirst=True)
