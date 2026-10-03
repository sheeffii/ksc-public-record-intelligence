"""Align the benchmark finding's text with its parsed paragraphs.

Parser v4 keeps the section heading "B. THIRD AMENDMENT" out of paragraph
text (it is a `document_sections` heading). The hand-verified finding
FD-F03752-P12-16 still carried that heading after paragraph 16. Its text is
set to paragraphs 12-16 exactly as `build-findings` composes them; the
verification state, reviewer and date are unchanged and the previous text is
kept in the audit log.

Revision ID: 0021
Revises: 0020
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FINDING_KEY = "FD-F03752-P12-16"
_ACTION = "finding.text_aligned_to_parsed_paragraphs"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            WITH aligned AS (
                SELECT f.id, f.text AS old_text,
                       string_agg(p.text, E'\\n\\n' ORDER BY p.paragraph_number) AS new_text,
                       count(*) AS paragraphs
                FROM findings f
                JOIN document_paragraphs p
                  ON p.document_version_id = f.judgment_version_id
                 AND p.paragraph_number BETWEEN f.para_from AND f.para_to
                WHERE f.finding_key = :key
                GROUP BY f.id, f.text, f.para_from, f.para_to
                HAVING count(*) = f.para_to - f.para_from + 1
            ),
            audited AS (
                INSERT INTO audit_log (id, occurred_at, actor, action, entity_type, entity_id,
                                       detail)
                SELECT gen_random_uuid(), now(), 'migration:0021', :action, 'finding', :key,
                       jsonb_build_object('from', old_text, 'to', new_text,
                                          'reason', 'parser v4 keeps the section heading '
                                          'outside paragraph text')
                FROM aligned WHERE old_text <> new_text
                RETURNING entity_id
            )
            UPDATE findings f SET text = a.new_text
            FROM aligned a WHERE f.id = a.id AND a.old_text <> a.new_text
            """
        ).bindparams(key=_FINDING_KEY, action=_ACTION)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE findings f SET text = l.detail->>'from'
            FROM (
                SELECT DISTINCT ON (entity_id) entity_id, detail FROM audit_log
                WHERE action = :action AND entity_id = :key
                ORDER BY entity_id, occurred_at DESC
            ) l
            WHERE f.finding_key = l.entity_id
            """
        ).bindparams(key=_FINDING_KEY, action=_ACTION)
    )
