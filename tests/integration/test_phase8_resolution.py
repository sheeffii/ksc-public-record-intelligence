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


def test_exhibit_sub_numbers_resolve_exactly_or_stay_unresolved(
    session: Session, case: Case
) -> None:
    from ksc_api.models import EntityKind, Exhibit, IdentifierKind, RecordIdentifier

    def register(official: str) -> Exhibit:
        exhibit = Exhibit(
            case_id=case.id,
            official_exhibit_id=official,
            title=f"Exhibit {official}",
            status="unknown",
            visibility="public",
        )
        session.add(exhibit)
        session.flush()
        session.add(
            RecordIdentifier(
                case_id=case.id,
                identifier=official,
                normalized_identifier=official,
                identifier_kind=IdentifierKind.EXHIBIT,
                entity_kind=EntityKind.EXHIBIT,
                is_primary=True,
                exhibit_id=exhibit.id,
            )
        )
        session.flush()
        return exhibit

    base, part = register("P09099"), register("P09136.2")
    register("P09136")

    def resolve(identifier: str):
        citation = ExtractedCitation(
            raw_text=identifier,
            normalized_identifier=identifier,
            citation_type=CitationType.EXHIBIT,
        )
        return resolve_extracted(session, case, citation, source_version_ref="F-DEMO-001/RED")

    assert resolve("P09099").exhibit_id == base.id
    # No prefix fallback: the base exists, the exact sub-number does not.
    missing = resolve("P09099.1")
    assert missing.state is ResolutionState.UNRESOLVED and missing.exhibit_id is None
    assert missing.rule == "unresolved.exhibit_part_not_registered"
    # An exact sub-number resolves to itself, never to its registered base.
    exact = resolve("P09136.2")
    assert exact.state is ResolutionState.RESOLVED and exact.exhibit_id == part.id
    padded = resolve("P9136.2")
    assert padded.exhibit_id == part.id and padded.rule == "identifier.zero_padded"
    for other in ("P09136.1", "P09136.3", "P09136.4"):
        assert resolve(other).state is ResolutionState.UNRESOLVED


def test_stale_citation_retires_with_its_derived_edge_only(session: Session, case: Case) -> None:
    from ksc_api.models import (
        AuditLog,
        Citation,
        GraphNode,
        Relationship,
        RelationshipOrigin,
        RelationshipType,
        VerificationState,
    )
    from ksc_ingestion.parse_pipeline import Phase8Pipeline

    nodes = session.scalars(select(GraphNode).where(GraphNode.case_id == case.id).limit(2)).all()
    assert len(nodes) == 2

    def stale_with_edge(origin: RelationshipOrigin) -> tuple[Citation, Relationship]:
        citation = Citation(
            case_id=case.id,
            raw_text="P09099",
            normalized_text="P09099",
            citation_type=CitationType.EXHIBIT,
            resolution_state=ResolutionState.UNRESOLVED,
            display="UNRESOLVED",
        )
        session.add(citation)
        session.flush()
        edge = Relationship(
            case_id=case.id,
            from_node_id=nodes[0].id,
            to_node_id=nodes[1].id,
            relationship_type=RelationshipType.CITED_IN,
            citation_id=citation.id,
            verification_state=VerificationState.UNREVIEWED,
            source_category="court",
            extraction_origin=origin,
        )
        session.add(edge)
        session.flush()
        return citation, edge

    derived, derived_edge = stale_with_edge(RelationshipOrigin.DETERMINISTIC_CITATION)
    curated, curated_edge = stale_with_edge(RelationshipOrigin.SOURCE_DOCUMENTED)
    retired = Phase8Pipeline._retire_stale_citations(session, [derived, curated])
    session.flush()

    # Only the citation whose sole reference is its own derived edge goes.
    assert retired == [derived.id]
    assert session.get(Relationship, derived_edge.id) is None
    assert session.get(Citation, curated.id) is not None
    assert session.get(Relationship, curated_edge.id) is not None
    audit = session.scalar(
        select(AuditLog).where(
            AuditLog.action == "citation.retired", AuditLog.entity_id == str(derived.id)
        )
    )
    assert audit is not None and audit.detail["derived_edges_removed"] == [str(derived_edge.id)]
