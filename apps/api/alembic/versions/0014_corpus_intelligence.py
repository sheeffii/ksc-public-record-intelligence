"""corpus intelligence: resolution rules, appearances, status events, edge evidence (Phase 19B)

Revision ID: 0014
Revises: 0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # -- citations: machine-readable resolution rule (HOW it was resolved or not)
    op.add_column("citations", sa.Column("resolution_rule", sa.String(length=64)))
    op.create_index(op.f("ix_citations_resolution_rule"), "citations", ["resolution_rule"])

    # -- person aliases: kind + exact source provenance
    op.add_column(
        "person_aliases",
        sa.Column(
            "alias_kind", sa.String(length=16), server_default="speaker_label", nullable=False
        ),
    )
    for column, type_ in (
        ("source_document_version_id", _UUID),
        ("source_pdf_page_index", sa.Integer()),
        ("source_char_start", sa.Integer()),
        ("source_char_end", sa.Integer()),
        ("rule_id", sa.String(length=64)),
    ):
        op.add_column("person_aliases", sa.Column(column, type_))
    op.create_foreign_key(
        op.f("fk_person_aliases_source_document_version_id_document_versions"),
        "person_aliases",
        "document_versions",
        ["source_document_version_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        op.f("ck_person_aliases_alias_kind_allowed"),
        "person_aliases",
        "alias_kind IN ('speaker_label', 'full_name')",
    )
    op.create_check_constraint(
        op.f("ck_person_aliases_full_name_has_provenance"),
        "person_aliases",
        "alias_kind <> 'full_name' OR (source_document_version_id IS NOT NULL "
        "AND source_char_start IS NOT NULL AND source_char_end IS NOT NULL "
        "AND rule_id IS NOT NULL)",
    )

    # -- witness appearances: subject is a code witness OR a publicly named person;
    #    one row per transcript version, with the structural signal's provenance.
    op.alter_column("witness_appearances", "witness_id", nullable=True)
    op.add_column("witness_appearances", sa.Column("person_id", _UUID))
    op.create_foreign_key(
        op.f("fk_witness_appearances_person_id_persons"),
        "witness_appearances",
        "persons",
        ["person_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_witness_appearances_person_id"), "witness_appearances", ["person_id"])
    for column, type_ in (
        ("document_version_id", _UUID),
        ("signal_pdf_page_index", sa.Integer()),
        ("signal_page_number", sa.Integer()),
        ("signal_char_start", sa.Integer()),
        ("signal_char_end", sa.Integer()),
        ("signal_text", sa.Text()),
        ("header_pages", sa.Integer()),
        ("open_session_pages", sa.Integer()),
        ("private_session_pages", sa.Integer()),
        ("closed_session_pages", sa.Integer()),
        ("examinations", postgresql.JSONB()),
        ("rule_id", sa.String(length=64)),
        ("rule_version", sa.Integer()),
        ("projection_run_id", _UUID),
    ):
        op.add_column("witness_appearances", sa.Column(column, type_))
    op.create_foreign_key(
        op.f("fk_witness_appearances_document_version_id_document_versions"),
        "witness_appearances",
        "document_versions",
        ["document_version_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_witness_appearances_projection_run_id_processing_runs"),
        "witness_appearances",
        "processing_runs",
        ["projection_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        op.f("ck_witness_appearances_exactly_one_subject"),
        "witness_appearances",
        "num_nonnulls(witness_id, person_id) = 1",
    )
    op.create_check_constraint(
        op.f("ck_witness_appearances_rule_has_signal"),
        "witness_appearances",
        "rule_id IS NULL OR (document_version_id IS NOT NULL AND signal_text IS NOT NULL "
        "AND signal_char_start IS NOT NULL AND signal_char_end IS NOT NULL)",
    )
    op.drop_constraint(
        "uq_witness_appearances_witness_hearing", "witness_appearances", type_="unique"
    )
    op.create_unique_constraint(
        "uq_witness_appearances_subject_transcript",
        "witness_appearances",
        ["witness_id", "person_id", "hearing_id", "transcript_id"],
        postgresql_nulls_not_distinct=True,
    )

    # -- exhibit status history: explicit, source-backed court-record events only
    op.create_table(
        "exhibit_status_events",
        sa.Column("case_id", _UUID, nullable=False),
        sa.Column("exhibit_id", _UUID),
        sa.Column("exhibit_identifier", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("classification", sa.String(length=32)),
        sa.Column("event_date", sa.Date()),
        sa.Column("hearing_id", _UUID),
        sa.Column("document_version_id", _UUID, nullable=False),
        sa.Column("transcript_segment_id", _UUID),
        sa.Column("page_number", sa.Integer()),
        sa.Column("pdf_page_index", sa.Integer()),
        sa.Column("line_from", sa.Integer()),
        sa.Column("line_to", sa.Integer()),
        sa.Column("char_anchor", sa.String(length=32), nullable=False),
        sa.Column("char_start", sa.Integer(), nullable=False),
        sa.Column("char_end", sa.Integer(), nullable=False),
        sa.Column("occurrence_text", sa.Text(), nullable=False),
        sa.Column("speaker", sa.String(length=255)),
        sa.Column("language", sa.String(length=16)),
        sa.Column("rule_id", sa.String(length=64), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("projection_run_id", _UUID),
        sa.Column("id", _UUID, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "event_type IN ('number_assigned', 'admitted', 'rejected', "
            "'marked_for_identification', 'withdrawn')",
            name=op.f("ck_exhibit_status_events_event_type_allowed"),
        ),
        sa.CheckConstraint(
            "char_anchor IN ('transcript_segment_text', 'document_page_text')",
            name=op.f("ck_exhibit_status_events_char_anchor_allowed"),
        ),
        sa.CheckConstraint(
            "char_start >= 0 AND char_end > char_start",
            name=op.f("ck_exhibit_status_events_char_range"),
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["exhibit_id"], ["exhibits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hearing_id"], ["hearings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["transcript_segment_id"], ["transcript_segments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["projection_run_id"], ["processing_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_version_id",
            "transcript_segment_id",
            "pdf_page_index",
            "char_start",
            "char_end",
            "exhibit_identifier",
            "event_type",
            name="uq_exhibit_status_events_source",
            postgresql_nulls_not_distinct=True,
        ),
    )
    for column in ("case_id", "exhibit_id"):
        op.create_index(
            op.f(f"ix_exhibit_status_events_{column}"), "exhibit_status_events", [column]
        )
    op.add_column("exhibits", sa.Column("status_event_id", _UUID))
    op.create_foreign_key(
        op.f("fk_exhibits_status_event_id_exhibit_status_events"),
        "exhibits",
        "exhibit_status_events",
        ["status_event_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # -- relationships: exactly one evidence anchor (citation | occurrence | appearance)
    op.execute("ALTER TYPE relationship_origin ADD VALUE IF NOT EXISTS 'deterministic_occurrence'")
    op.alter_column("relationships", "citation_id", nullable=True)
    op.add_column("relationships", sa.Column("entity_occurrence_id", _UUID))
    op.add_column("relationships", sa.Column("witness_appearance_id", _UUID))
    op.add_column(
        "relationships",
        sa.Column("evidence_count", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_foreign_key(
        op.f("fk_relationships_entity_occurrence_id_entity_occurrences"),
        "relationships",
        "entity_occurrences",
        ["entity_occurrence_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_relationships_witness_appearance_id_witness_appearances"),
        "relationships",
        "witness_appearances",
        ["witness_appearance_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        op.f("ck_relationships_exactly_one_evidence"),
        "relationships",
        "num_nonnulls(citation_id, entity_occurrence_id, witness_appearance_id) = 1",
    )
    op.create_check_constraint(
        op.f("ck_relationships_evidence_count_positive"), "relationships", "evidence_count >= 1"
    )
    for column in ("entity_occurrence_id", "witness_appearance_id", "relationship_type"):
        op.create_index(op.f(f"ix_relationships_{column}"), "relationships", [column])


def downgrade() -> None:
    for column in ("relationship_type", "witness_appearance_id", "entity_occurrence_id"):
        op.drop_index(op.f(f"ix_relationships_{column}"), table_name="relationships")
    op.execute("DELETE FROM relationships WHERE citation_id IS NULL")
    op.drop_constraint(
        op.f("ck_relationships_evidence_count_positive"), "relationships", type_="check"
    )
    op.drop_constraint(
        op.f("ck_relationships_exactly_one_evidence"), "relationships", type_="check"
    )
    op.drop_constraint(
        op.f("fk_relationships_witness_appearance_id_witness_appearances"),
        "relationships",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_relationships_entity_occurrence_id_entity_occurrences"),
        "relationships",
        type_="foreignkey",
    )
    for column in ("evidence_count", "witness_appearance_id", "entity_occurrence_id"):
        op.drop_column("relationships", column)
    op.alter_column("relationships", "citation_id", nullable=False)
    # PostgreSQL cannot drop an enum value; 'deterministic_occurrence' stays unused.

    op.drop_constraint(
        op.f("fk_exhibits_status_event_id_exhibit_status_events"), "exhibits", type_="foreignkey"
    )
    op.drop_column("exhibits", "status_event_id")
    op.drop_table("exhibit_status_events")

    op.drop_constraint(
        "uq_witness_appearances_subject_transcript", "witness_appearances", type_="unique"
    )
    op.execute("DELETE FROM witness_appearances WHERE person_id IS NOT NULL OR rule_id IS NOT NULL")
    op.create_unique_constraint(
        "uq_witness_appearances_witness_hearing",
        "witness_appearances",
        ["witness_id", "hearing_id"],
    )
    for name in ("rule_has_signal", "exactly_one_subject"):
        op.drop_constraint(
            op.f(f"ck_witness_appearances_{name}"), "witness_appearances", type_="check"
        )
    for name in (
        "fk_witness_appearances_projection_run_id_processing_runs",
        "fk_witness_appearances_document_version_id_document_versions",
        "fk_witness_appearances_person_id_persons",
    ):
        op.drop_constraint(op.f(name), "witness_appearances", type_="foreignkey")
    op.drop_index(op.f("ix_witness_appearances_person_id"), table_name="witness_appearances")
    for column in (
        "projection_run_id",
        "rule_version",
        "rule_id",
        "examinations",
        "closed_session_pages",
        "private_session_pages",
        "open_session_pages",
        "header_pages",
        "signal_text",
        "signal_char_end",
        "signal_char_start",
        "signal_page_number",
        "signal_pdf_page_index",
        "document_version_id",
        "person_id",
    ):
        op.drop_column("witness_appearances", column)
    op.alter_column("witness_appearances", "witness_id", nullable=False)

    op.execute("DELETE FROM person_aliases WHERE alias_kind = 'full_name'")
    for name in ("full_name_has_provenance", "alias_kind_allowed"):
        op.drop_constraint(op.f(f"ck_person_aliases_{name}"), "person_aliases", type_="check")
    op.drop_constraint(
        op.f("fk_person_aliases_source_document_version_id_document_versions"),
        "person_aliases",
        type_="foreignkey",
    )
    for column in (
        "rule_id",
        "source_char_end",
        "source_char_start",
        "source_pdf_page_index",
        "source_document_version_id",
        "alias_kind",
    ):
        op.drop_column("person_aliases", column)

    op.drop_index(op.f("ix_citations_resolution_rule"), table_name="citations")
    op.drop_column("citations", "resolution_rule")
