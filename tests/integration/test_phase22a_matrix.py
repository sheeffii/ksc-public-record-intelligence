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
