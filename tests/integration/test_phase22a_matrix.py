"""Phase 22A semantic guardrails at the database boundary."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("link_type", "court_cited", "basis", "origin", "process", "state"),
    [
        (
            "court_relies_on",
            False,
            "explicit_court_reliance",
            "source_derived",
            None,
            "unreviewed",
        ),
        (
            "supports",
            False,
            "human_classification",
            "source_derived",
            "test review",
            "unreviewed",
        ),
        (
            "supports",
            False,
            "ai_suggestion",
            "ai_suggested",
            "AI suggestion pending human review",
            "human_verified",
        ),
    ],
)
def test_matrix_rejects_semantically_invalid_relationships(
    demo_settings,
    engine,
    link_type: str,
    court_cited: bool,
    basis: str,
    origin: str,
    process: str | None,
    state: str,
) -> None:
    with engine.connect() as conn:
        finding_id, citation_id = conn.execute(
            text("SELECT f.id, f.citation_id FROM findings f WHERE f.finding_key = 'FD-DEMO-001'")
        ).one()
        transaction = conn.begin_nested()
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO finding_evidence_links "
                    "(id, finding_id, citation_id, link_type, court_cited, "
                    "relationship_basis, source_category, classification_origin, "
                    "review_process, verification_state, verified_by, verified_at) "
                    "VALUES (:id, :finding_id, :citation_id, :link_type, :court_cited, "
                    ":basis, 'other', :origin, :process, :state, :reviewer, now())"
                ),
                {
                    "id": uuid.uuid4(),
                    "finding_id": finding_id,
                    "citation_id": citation_id,
                    "link_type": link_type,
                    "court_cited": court_cited,
                    "basis": basis,
                    "origin": origin,
                    "process": process,
                    "state": state,
                    "reviewer": "test-reviewer" if state == "human_verified" else None,
                },
            )
        transaction.rollback()


def test_matrix_filter_and_pagination_are_bounded(demo_client) -> None:
    response = demo_client.get(
        "/api/v1/findings/FD-DEMO-001/matrix",
        params={"source_category": "witness_testimony", "limit": 1, "offset": 0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["matrix_total"] == 1
    assert len(body["matrix_rows"]) == 1
    assert body["matrix_rows"][0]["source_category"] == "witness_testimony"
    assert (
        demo_client.get("/api/v1/findings/FD-DEMO-001/matrix", params={"limit": 101}).status_code
        == 422
    )


def test_matrix_projection_replaces_its_own_edges_whatever_their_note(demo_settings) -> None:
    """A later migration (0019) rewrote the note of a projected edge; the
    projection must still replace that edge instead of colliding with it."""
    from sqlalchemy import select

    from ksc_api.db.session import get_sessionmaker
    from ksc_api.fixtures.demo import DEMO_CASE_NUMBER
    from ksc_api.models import Relationship
    from ksc_ingestion.legal_matrix import Phase22ALegalMatrixProjector

    sessions = get_sessionmaker()
    projector = Phase22ALegalMatrixProjector(sessions, case_number=DEMO_CASE_NUMBER)
    first = projector.run()
    assert first.graph_relationships > 0

    def projected() -> list[tuple[uuid.UUID, str, str]]:
        with sessions() as session:
            return [
                (r.id, r.relationship_type.value, r.verification_state.value)
                for r in session.scalars(
                    select(Relationship)
                    .where(Relationship.note.like("Phase 22A matrix projection:%"))
                    .order_by(Relationship.id)
                )
            ]

    before = projected()
    with sessions() as session:
        edge = session.get(Relationship, before[0][0])
        assert edge is not None
        edge.note = "Phase 22C source-fidelity audit: court_cites"
        session.commit()

    second = projector.run()
    assert second.graph_relationships == first.graph_relationships
    assert projected() == before
