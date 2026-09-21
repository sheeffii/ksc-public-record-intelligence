"""Phase 9 deterministic evidence projection and provenance invariants."""

from __future__ import annotations

import pytest
from sqlalchemy import delete, select

from ksc_api.models import Event, Relationship, RelationshipOrigin, ResolutionState
from ksc_ingestion.evidence_pipeline import Phase9Pipeline

pytestmark = pytest.mark.integration


def test_phase9_projection_is_idempotent_and_every_edge_is_auditable(demo_settings) -> None:
    from ksc_api.db.session import get_sessionmaker

    sessions = get_sessionmaker()
    pipeline = Phase9Pipeline(sessions, case_number="KSC-DEMO-0000")
    try:
        first = pipeline.run()
        second = pipeline.run()
        assert second == first
        assert first.edges > 0
        assert first.events > 0

        with sessions() as session:
            edges = session.scalars(
                select(Relationship).where(
                    Relationship.extraction_origin == RelationshipOrigin.DETERMINISTIC_CITATION
                )
            ).all()
            assert len(edges) == first.edges
            assert all(edge.citation.resolution_state == ResolutionState.RESOLVED for edge in edges)
            assert all(edge.citation_id and edge.source_category and edge.note for edge in edges)
            assert all(edge.from_node_id != edge.to_node_id for edge in edges)
            events = session.scalars(
                select(Event).where(Event.extraction_origin == "source_metadata")
            ).all()
            assert len(events) == first.events
            assert all(event.date_from is not None for event in events)
            assert all(event.document_id or event.hearing_id for event in events)
    finally:
        with sessions.begin() as session:
            session.execute(
                delete(Relationship).where(
                    Relationship.extraction_origin == RelationshipOrigin.DETERMINISTIC_CITATION
                )
            )
            session.execute(delete(Event).where(Event.extraction_origin == "source_metadata"))
