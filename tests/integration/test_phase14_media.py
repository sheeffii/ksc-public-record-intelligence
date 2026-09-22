from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ksc_api.db.session import get_sessionmaker, session_scope
from ksc_api.models import Case, CourtMediaLink, MediaItem, VerificationState
from ksc_ingestion.external_media import import_media_manifest, run_phase14_gate

pytestmark = pytest.mark.integration
MANIFEST = Path("docs/ingestion/manifests/phase14-external-media.json")


@pytest.fixture
def phase14_demo(demo_settings: Any) -> None:
    with session_scope() as session:
        case = session.scalar(select(Case).where(Case.case_number == demo_settings.case_id))
        assert case is not None
        result = import_media_manifest(session, case, MANIFEST)
        assert result.items == 3


def test_media_api_keeps_external_and_court_layers_separate(
    phase14_demo: None, demo_client: Any
) -> None:
    workspace = demo_client.get("/api/v1/media").json()
    assert workspace["coverage"] == {
        "sources": 2,
        "items": 3,
        "statements": 3,
        "court_links": 3,
        "citation_backed_court_links": 0,
        "comparisons": 1,
    }
    assert {status for item in workspace["items"] for status in item["court_statuses"]} == {
        "external_only"
    }
    assert len(workspace["limitations"]) >= 4

    item = demo_client.get(f"/api/v1/media/{workspace['items'][0]['id']}").json()
    assert item["source"]["access_method"] == "manual_url"
    assert item["statements"][0]["exact_quote"] is True
    assert item["court_links"][0]["citation"] is None


def test_media_search_timeline_network_and_comparison_are_explicit(
    phase14_demo: None, demo_client: Any
) -> None:
    searched = demo_client.get("/api/v1/media", params={"q": "Zyrapi"}).json()
    assert len(searched["items"]) == 1
    timeline = demo_client.get("/api/v1/media/timeline").json()
    assert len(timeline) == 3
    assert all(event["source_layer"] == "external_public_source" for event in timeline)
    assert {event["date_basis"] for event in timeline} == {"published"}
    # EXTERNAL_ONLY does not produce a graph edge into the court graph.
    assert demo_client.get("/api/v1/media/network").json() == {"nodes": [], "edges": []}
    comparisons = demo_client.get("/api/v1/media/comparisons").json()
    assert comparisons[0]["classification"] == "not_comparable"
    assert comparisons[0]["statement_a"]["exact_quote"] is True
    assert comparisons[0]["statement_b"]["exact_quote"] is True


def test_real_data_gate_rejects_no_boundary_or_access_violation(
    phase14_demo: None, demo_settings: Any
) -> None:
    with session_scope() as session:
        case = session.scalar(select(Case).where(Case.case_number == demo_settings.case_id))
        assert case is not None
        report = run_phase14_gate(session, case, MANIFEST, "2026-09-22")
    assert report.passed is True
    assert report.invalid_court_links == 0
    assert report.manifest_item_mismatches == 0
    assert report.verification_violations == 0
    assert report.access_violations == 0
    assert report.ai_external_retrieval_sources == 0


def test_non_external_status_cannot_be_created_without_court_provenance(
    phase14_demo: None, demo_settings: Any
) -> None:
    session = get_sessionmaker()()
    try:
        case = session.scalar(select(Case).where(Case.case_number == demo_settings.case_id))
        item = (
            session.scalar(select(MediaItem).where(MediaItem.case_id == case.id)) if case else None
        )
        assert case is not None and item is not None
        session.add(
            CourtMediaLink(
                case_id=case.id,
                media_item_id=item.id,
                court_status="admitted",
                note="Missing exact court provenance.",
                verification_state=VerificationState.UNREVIEWED,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()
