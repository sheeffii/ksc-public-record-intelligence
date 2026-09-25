"""Phase 8 deterministic resolver failure and ambiguity cases."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime

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


def test_identifier_after_another_courts_case_number_is_invalid(
    session: Session, case: Case
) -> None:
    # Phase 19C: "IT-04-84bis, P00119" names ICTY Haradinaj's exhibit, never this case's.
    foreign = ExtractedCitation(
        raw_text="P-DEMO-001",
        normalized_identifier="F-DEMO-001",
        citation_type=CitationType.DOCUMENT,
        preceding_case="IT-04-84bis",
    )
    result = resolve_extracted(session, case, foreign, source_version_ref="F-DEMO-001/RED")
    assert result.state is ResolutionState.INVALID
    assert result.rule == "invalid.other_case"
    own = ExtractedCitation(
        raw_text="F-DEMO-001",
        normalized_identifier="F-DEMO-001",
        citation_type=CitationType.DOCUMENT,
        preceding_case=case.case_number,
    )
    own_result = resolve_extracted(session, case, own, source_version_ref="F-DEMO-001/RED")
    assert own_result.state is ResolutionState.RESOLVED


def test_stale_citations_are_retired_only_when_unreviewed_and_unreferenced(
    session: Session, case: Case
) -> None:
    from ksc_api.models import AuditLog, Citation, Relationship, VerificationState
    from ksc_ingestion.parse_pipeline import Phase8Pipeline

    def stale(state: VerificationState = VerificationState.UNREVIEWED) -> Citation:
        row = Citation(
            case_id=case.id,
            raw_text="F99999",
            normalized_text="F99999",
            citation_type=CitationType.DOCUMENT,
            resolution_state=ResolutionState.UNRESOLVED,
            display="UNRESOLVED",
            verification_state=state,
            **(
                {"verified_by": "reviewer", "verified_at": datetime.now(UTC)}
                if state is not VerificationState.UNREVIEWED
                else {}
            ),
        )
        session.add(row)
        return row

    orphan, reviewed = stale(), stale(VerificationState.HUMAN_VERIFIED)
    referenced = session.scalar(
        select(Citation).join(Relationship, Relationship.citation_id == Citation.id).limit(1)
    )
    assert referenced is not None
    session.flush()

    retired = Phase8Pipeline._retire_stale_citations(session, [orphan, reviewed, referenced])
    session.flush()

    assert retired == [orphan.id]
    assert session.get(Citation, orphan.id) is None
    assert session.get(Citation, reviewed.id) is not None
    assert session.get(Citation, referenced.id) is not None
    audit = session.scalar(
        select(AuditLog).where(
            AuditLog.action == "citation.retired", AuditLog.entity_id == str(orphan.id)
        )
    )
    assert audit is not None and audit.detail["raw_text"] == "F99999"
