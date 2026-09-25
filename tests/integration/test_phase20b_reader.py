"""Phase 20B Reader reads against the synthetic fixture: version-scoped,
bounded, fail-closed, and honest about precision."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

pytestmark = pytest.mark.integration

V1 = "/api/v1"
T = f"{V1}/document-versions/T-DEMO-001"


def test_transcript_outline_and_segments_are_version_scoped(demo_client):
    outline = demo_client.get(f"{T}/transcript").json()
    assert outline["official_version_ref"] == "T-DEMO-001"
    assert outline["segment_count"] == 4 and outline["closed_session_segments"] == 1
    assert {s["label"] for s in outline["speakers"]} == {"Presiding Judge", "W-DEMO-001"}

    page = demo_client.get(f"{T}/transcript/segments").json()
    assert page["filtered"] is False and page["total"] == 4
    closed = page["items"][3]
    assert closed["closed_session"] is True and closed["text"] is None
    assert page["items"][1]["witness_code"] == "W-DEMO-001"

    located = demo_client.get(f"{T}/transcript/segments?page=101&line=7").json()
    assert [item["sequence"] for item in located["items"]] == [1]

    filtered = demo_client.get(f"{T}/transcript/segments?speaker=W-DEMO-001").json()
    assert filtered["filtered"] is True and filtered["total"] == 2


def test_reader_reads_fail_closed(demo_client):
    # Not public, unknown, and a non-transcript version.
    assert demo_client.get(f"{V1}/document-versions/F-DEMO-001/transcript").status_code == 404
    assert demo_client.get(f"{V1}/document-versions/NOPE/pages/0/context").status_code == 404
    assert demo_client.get(f"{V1}/document-versions/F-DEMO-001/RED/transcript").status_code == 404
    assert (
        demo_client.get(f"{V1}/document-versions/F-DEMO-001/RED/pages/999/context").status_code
        == 404
    )


def test_page_context_is_page_scoped(demo_client):
    body = demo_client.get(f"{V1}/document-versions/F-DEMO-001/RED/pages/0/context").json()
    assert body["official_version_ref"] == "F-DEMO-001/RED"
    assert body["pdf_page_index"] == 0
    assert body["truncated"] is False
    assert all(item["state"] != "SEARCH_MATCH" for item in body["overlays"])


def test_local_search_is_search_match_only_and_never_exact(demo_client):
    body = demo_client.get(f"{T}/source-search?q=solemn").json()
    assert body["total"] == 1
    hit = body["items"][0]
    assert hit["match_type"] == "SEARCH_MATCH"
    assert hit["precision"] not in {"exact_geometry", "ocr_geometry"}
    assert "solemn" in hit["excerpt"]
    # Closed-session segments carry no text and are never matched.
    assert demo_client.get(f"{T}/source-search?q=%25").json()["total"] == 0
    assert demo_client.get(f"{T}/source-search?q=x").json()["total"] == 0


def test_transcript_sync_projection_is_idempotent_and_never_boxes_without_geometry(
    demo_settings,
):
    from ksc_api.db.session import get_sessionmaker
    from ksc_api.fixtures.demo import DEMO_CASE_NUMBER
    from ksc_api.models import SourceAnchor, SourceRegion, SourceSpan
    from ksc_ingestion.transcript_sync import TranscriptSyncProjector

    sessions = get_sessionmaker()
    first = TranscriptSyncProjector(sessions, case_number=DEMO_CASE_NUMBER).run()
    second = TranscriptSyncProjector(sessions, case_number=DEMO_CASE_NUMBER).run()
    assert first.segments == second.segments == 4
    assert first.precision == second.precision
    assert "exact_geometry" not in first.precision
    with sessions() as session:
        owned = select(SourceAnchor.source_span_id).where(
            SourceAnchor.object_type == "transcript_segment"
        )
        assert session.scalar(select(func.count()).select_from(owned.subquery())) == 4
        assert (
            session.scalar(
                select(func.count(SourceRegion.id)).where(SourceRegion.source_span_id.in_(owned))
            )
            == 0
        )
        closed = session.scalars(
            select(SourceSpan).where(SourceSpan.id.in_(owned), SourceSpan.exact_text.is_(None))
        ).all()
        assert len(closed) == 1 and closed[0].precision.value in {"unavailable", "page_and_line"}
