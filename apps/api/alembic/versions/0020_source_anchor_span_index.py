"""Index source_anchors.source_span_id.

Deleting a SourceSpan cascades to its anchors; without this index every
cascaded delete scanned the whole anchor table.

Revision ID: 0020
Revises: 0019
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_source_anchors_source_span_id", "source_anchors", ["source_span_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_source_anchors_source_span_id", table_name="source_anchors")
