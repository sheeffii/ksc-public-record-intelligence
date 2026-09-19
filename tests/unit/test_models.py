"""Model-level invariants that hold without a database."""

from __future__ import annotations

from sqlalchemy import CheckConstraint

from ksc_api.db.base import Base
from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    Case,
    Citation,
    Document,
    DocumentIngestionState,
    GraphNode,
    RecordIdentifier,
    Relationship,
    VerificationState,
    Visibility,
    Witness,
)

PHASE4_TABLES = {"cases", "documents", "audit_log"}
PHASE6_TABLES = {
    "source_records",
    "document_versions",
    "document_pages",
    "document_sections",
    "document_chunks",
    "hearings",
    "transcripts",
    "transcript_segments",
    "witness_appearances",
    "persons",
    "person_aliases",
    "witnesses",
    "organizations",
    "locations",
    "exhibits",
    "incidents",
    "events",
    "claims",
    "claim_mentions",
    "findings",
    "finding_evidence_links",
    "arguments",
    "argument_responses",
    "citations",
    "record_identifiers",
    "graph_nodes",
    "relationships",
    "research_notes",
    "research_note_citations",
    "prompt_versions",
    "ai_runs",
    "ai_outputs",
    "ai_output_citations",
    "ingestion_jobs",
}


def _checks(table_name: str) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {c.name for c in table.constraints if isinstance(c, CheckConstraint)}


def test_schema_contains_phase4_foundation_and_phase6_evidence_model():
    assert set(Base.metadata.tables) == PHASE4_TABLES | PHASE6_TABLES


def test_document_keeps_the_three_date_types_separate():
    cols = Document.__table__.columns
    for name in ("document_date", "filing_date", "public_date"):
        assert name in cols
        # Independently nullable; none is derived from another.
        assert cols[name].nullable


def test_no_model_carries_a_score_rank_or_weight_field():
    """DESIGN_DECISIONS.md §2 — no score of any person exists in the data model."""
    forbidden = {"score", "rank", "rating", "weight", "priority", "probability", "likelihood"}
    for table in Base.metadata.tables.values():
        for column in table.columns:
            name = column.name.lower()
            assert not any(word in name for word in forbidden), f"{table.name}.{column.name}"


def test_visibility_can_state_not_public_and_defaults_fail_closed():
    """ROUTE_MAP.md §8 — 'exists but is not public' must be distinguishable from 404,
    and only the two public states are ever returned by default."""
    assert Visibility.NOT_PUBLIC.value == "not_public"
    assert PUBLIC_VISIBILITIES == {Visibility.PUBLIC, Visibility.PUBLIC_REDACTED}
    assert Visibility.UNKNOWN not in PUBLIC_VISIBILITIES
    assert Visibility.PRIVATE_AUTHORIZED not in PUBLIC_VISIBILITIES
    assert DocumentIngestionState.FAILED.value == "failed"


def test_case_official_ref_is_the_case_number():
    assert Case.__table__.columns["case_number"].unique


def test_enum_columns_persist_lower_case_values_not_member_names():
    column = Document.__table__.columns["visibility"]
    assert column.type.enums == [member.value for member in Visibility]


def test_protected_witness_cannot_carry_identity():
    checks = _checks("witnesses")
    assert "ck_witnesses_protected_code_has_no_identity" in checks
    assert "ck_witnesses_public_name_requires_public" in checks
    cols = Witness.__table__.columns
    assert cols["person_id"].nullable and cols["public_name"].nullable
    # Nothing identity-bearing beyond the guarded columns.
    assert not {"name", "image", "location", "occupation", "age", "address"} & set(cols.keys())


def test_relationships_require_provenance():
    cols = Relationship.__table__.columns
    assert cols["citation_id"].nullable is False
    fk = next(iter(cols["citation_id"].foreign_keys))
    assert fk.ondelete == "RESTRICT"
    assert "ck_relationships_no_self_loop" in _checks("relationships")


def test_graph_nodes_use_real_foreign_keys_with_exactly_one_target():
    checks = _checks("graph_nodes")
    assert "ck_graph_nodes_exactly_one_entity" in checks
    assert "ck_graph_nodes_kind_matches_entity" in checks
    fk_columns = [c for c in GraphNode.__table__.columns if c.foreign_keys and c.name != "case_id"]
    assert len(fk_columns) == 12
    assert all(next(iter(c.foreign_keys)).ondelete == "CASCADE" for c in fk_columns)


def test_citation_targets_are_foreign_keys_and_match_resolution_state():
    checks = _checks("citations")
    assert "ck_citations_targets_match_resolution_state" in checks
    assert "ck_citations_unresolved_display_literal" in checks
    targets = [
        c
        for c in Citation.__table__.columns
        if c.name.startswith("target_") and c.name.endswith("_id")
    ]
    assert len(targets) == 7
    assert all(c.foreign_keys for c in targets)
    assert Citation.__table__.columns["display"].server_default.arg == "UNRESOLVED"


def test_identifier_index_maps_one_string_to_exactly_one_record():
    assert "ck_record_identifiers_exactly_one_target" in _checks("record_identifiers")
    unique = {c.name for c in RecordIdentifier.__table__.constraints}
    assert "uq_record_identifiers_lookup" in unique


def test_human_verification_states_require_a_named_reviewer_everywhere():
    fact_tables = [
        name
        for name, table in Base.metadata.tables.items()
        if "verification_state" in table.columns
    ]
    assert {
        "citations",
        "claims",
        "claim_mentions",
        "findings",
        "finding_evidence_links",
        "relationships",
        "arguments",
        "ai_outputs",
    } <= set(fact_tables)
    for name in fact_tables:
        assert f"ck_{name}_human_verification_has_reviewer" in _checks(name), name
        assert Base.metadata.tables[name].columns["verification_state"].server_default.arg == (
            VerificationState.UNREVIEWED.value
        )


def test_research_notes_are_labelled_human():
    assert "ck_research_notes_provenance_is_human" in _checks("research_notes")


def test_transcript_segments_never_invent_lines_or_closed_session_text():
    checks = _checks("transcript_segments")
    assert {
        "ck_transcript_segments_line_range",
        "ck_transcript_segments_line_to_needs_line_from",
        "ck_transcript_segments_closed_session_has_no_text",
    } <= checks
