"""Phase 8 deterministic resolver failure and ambiguity cases."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.models import Case, CitationType, Hearing, ResolutionState, Transcript
from ksc_ingestion.citation_resolution import ExtractedCitation, resolve_extracted

pytestmark = pytest.mark.integration


@pytest.fixture
def session(demo_settings) -> Iterator[Session]:
    from ksc_api.db.session import get_sessionmaker

    value = get_sessionmaker()()
    try:
        yield value
    finally:
        value.rollback()
        value.close()


@pytest.fixture
def case(session: Session) -> Case:
    value = session.scalar(select(Case).where(Case.case_number == "KSC-DEMO-0000"))
    assert value is not None
    return value


def _resolve(session: Session, case: Case, identifier: str, **coordinates: int) -> ResolutionState:
    citation = ExtractedCitation(
        raw_text=identifier,
        normalized_identifier=identifier,
        citation_type=CitationType.DOCUMENT,
        **coordinates,
    )
    return resolve_extracted(session, case, citation, source_version_ref="F-DEMO-001/RED").state


def test_fake_citations_never_resolve(session: Session, case: Case) -> None:
    assert _resolve(session, case, "KSC-WRONG-9999-99/F00001") is ResolutionState.INVALID
    assert _resolve(session, case, "F99999") is ResolutionState.UNRESOLVED
    assert _resolve(session, case, "W99999") is ResolutionState.UNRESOLVED
    assert _resolve(session, case, "F-DEMO-001/RED2") is ResolutionState.UNRESOLVED
    assert _resolve(session, case, "F-DEMO-001", target_page=999) is ResolutionState.INVALID
    assert (
        _resolve(
            session,
            case,
            "T.101",
            target_page=101,
            target_line_from=24,
            target_line_to=26,
        )
        is ResolutionState.INVALID
    )


def test_overlapping_transcript_pages_are_explicitly_ambiguous(
    session: Session, case: Case
) -> None:
    hearings = [
        Hearing(
            case_id=case.id,
            hearing_date=date(2025, 1, day),
            session_sequence=1,
            visibility="public",
        )
        for day in (1, 2)
    ]
    session.add_all(hearings)
    session.flush()
    session.add_all(
        [
            Transcript(
                hearing_id=hearing.id,
                official_ref=f"T-AMBIG-{index}",
                visibility="public",
                page_from=777,
                page_to=777,
            )
            for index, hearing in enumerate(hearings, start=1)
        ]
    )
    session.flush()

    citation = ExtractedCitation(
        raw_text="T. 777",
        normalized_identifier="T.777",
        citation_type=CitationType.TRANSCRIPT,
        target_page=777,
    )
    result = resolve_extracted(session, case, citation, source_version_ref="F-DEMO-001/RED")

    assert result.state is ResolutionState.AMBIGUOUS
    assert result.display == "UNRESOLVED"
    assert result.candidate_identifiers == ["T-AMBIG-1", "T-AMBIG-2"]
