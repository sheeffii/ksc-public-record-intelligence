"""Model-level invariants that hold without a database."""

from __future__ import annotations

from ksc_api.db.base import Base
from ksc_api.models import Case, Document, DocumentIngestionState, DocumentPublicState


def test_phase4_schema_contains_only_minimal_tables():
    assert set(Base.metadata.tables) == {"cases", "documents", "audit_log"}


def test_document_keeps_document_and_filing_dates_separate():
    cols = Document.__table__.columns
    assert "document_date" in cols
    assert "filing_date" in cols
    # Neither column may be derived from the other; both are independently nullable.
    assert cols["document_date"].nullable
    assert cols["filing_date"].nullable


def test_no_model_carries_a_score_rank_or_weight_field():
    """DESIGN_DECISIONS.md §2 — no score of any person exists in the data model."""
    forbidden = {"score", "rank", "rating", "weight", "priority", "probability", "likelihood"}
    for table in Base.metadata.tables.values():
        for column in table.columns:
            name = column.name.lower()
            assert not any(word in name for word in forbidden), f"{table.name}.{column.name}"


def test_document_public_state_can_express_not_held():
    """ROUTE_MAP.md §8 — 'exists but is not public' must be distinguishable from 404."""
    assert DocumentPublicState.NOT_HELD.value == "not_held"
    assert DocumentIngestionState.FAILED.value == "failed"


def test_case_official_ref_is_the_case_number():
    assert Case.__table__.columns["case_number"].unique
