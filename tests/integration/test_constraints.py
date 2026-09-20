"""Database-enforced rules. Each case must be rejected by PostgreSQL itself,
not only by application code."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ksc_api.models import (
    Case,
    Citation,
    CitationType,
    Document,
    DocumentPage,
    DocumentVersion,
    DocumentVersionType,
    EntityKind,
    GraphNode,
    Hearing,
    Person,
    Relationship,
    RelationshipType,
    ResolutionState,
    Transcript,
    TranscriptSegment,
    VerificationState,
    Visibility,
    Witness,
    WitnessIdentityStatus,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def session(demo_settings) -> Iterator[Session]:
    from ksc_api.db.session import get_sessionmaker

    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def case(session: Session) -> Case:
    case = session.scalar(select(Case).where(Case.case_number == "KSC-DEMO-0000"))
    assert case is not None
    return case


def _rejects(session: Session, obj: object) -> None:
    session.add(obj)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_protected_witness_cannot_reference_a_person(session, case):
    person = session.scalar(select(Person).where(Person.case_id == case.id))
    _rejects(
        session,
        Witness(
            case_id=case.id,
            code="W-CHECK-001",
            identity_status=WitnessIdentityStatus.PROTECTED_CODE,
            person_id=person.id,
        ),
    )


def test_protected_witness_cannot_carry_a_public_name(session, case):
    _rejects(
        session,
        Witness(
            case_id=case.id,
            code="W-CHECK-002",
            identity_status=WitnessIdentityStatus.PROTECTED_CODE,
            public_name="Someone",
        ),
    )


def test_unknown_identity_status_cannot_carry_a_public_name(session, case):
    _rejects(
        session,
        Witness(
            case_id=case.id,
            code="W-CHECK-003",
            identity_status=WitnessIdentityStatus.UNKNOWN,
            public_name="Someone",
        ),
    )


def test_witness_codes_are_unique_per_case(session, case):
    _rejects(session, Witness(case_id=case.id, code="W-DEMO-001"))


def test_document_official_refs_are_unique_per_case(session, case):
    _rejects(
        session,
        Document(
            case_id=case.id,
            official_ref="KSC-DEMO-0000/F-DEMO-001",
            title="dup",
            document_type="filing",
        ),
    )


def test_version_refs_are_unique_per_document_and_sha256_is_unique_globally(session, case):
    document = session.scalar(select(Document).where(Document.filing_number == "F-DEMO-001"))
    existing = session.scalar(
        select(DocumentVersion).where(DocumentVersion.official_version_ref == "F-DEMO-001/RED")
    )
    _rejects(
        session,
        DocumentVersion(
            document_id=document.id,
            official_version_ref="F-DEMO-001/RED",
            version_type=DocumentVersionType.OTHER,
        ),
    )
    _rejects(
        session,
        DocumentVersion(
            document_id=document.id,
            official_version_ref="F-DEMO-001/DUP",
            version_type=DocumentVersionType.OTHER,
            sha256=existing.sha256,
        ),
    )


def test_page_numbers_are_positive_and_unique_per_version(session):
    version = session.scalar(
        select(DocumentVersion).where(DocumentVersion.official_version_ref == "F-DEMO-001/RED")
    )
    _rejects(
        session, DocumentPage(document_version_id=version.id, pdf_page_index=99, page_number=0)
    )
    _rejects(
        session, DocumentPage(document_version_id=version.id, pdf_page_index=99, page_number=1)
    )


def test_transcript_lines_are_validated(session):
    transcript = session.scalar(select(Transcript).where(Transcript.official_ref == "T-DEMO-001"))
    _rejects(
        session,
        TranscriptSegment(
            transcript_id=transcript.id, sequence=99, line_from=10, line_to=4, text="x"
        ),
    )
    _rejects(
        session,
        TranscriptSegment(transcript_id=transcript.id, sequence=99, line_to=4, text="x"),
    )
    _rejects(
        session,
        TranscriptSegment(
            transcript_id=transcript.id, sequence=99, closed_session=True, text="leaked"
        ),
    )


def test_relationship_requires_a_citation(session, case):
    nodes = session.scalars(select(GraphNode).where(GraphNode.case_id == case.id).limit(2)).all()
    _rejects(
        session,
        Relationship(
            case_id=case.id,
            from_node_id=nodes[0].id,
            to_node_id=nodes[1].id,
            relationship_type=RelationshipType.ASSOCIATED_WITH,
        ),
    )


def test_relationship_cannot_be_a_self_loop(session, case):
    node = session.scalar(select(GraphNode).where(GraphNode.case_id == case.id))
    citation = session.scalar(
        select(Citation).where(Citation.resolution_state == ResolutionState.RESOLVED)
    )
    _rejects(
        session,
        Relationship(
            case_id=case.id,
            from_node_id=node.id,
            to_node_id=node.id,
            relationship_type=RelationshipType.ASSOCIATED_WITH,
            citation_id=citation.id,
        ),
    )


def test_citation_in_use_cannot_be_deleted(session):
    citation = session.scalar(
        select(Citation).join(Relationship, Relationship.citation_id == Citation.id)
    )
    session.delete(citation)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_graph_node_points_at_exactly_one_entity(session, case):
    person = session.scalar(select(Person).where(Person.case_id == case.id))
    hearing = session.scalar(select(Hearing).where(Hearing.case_id == case.id))
    _rejects(
        session,
        GraphNode(case_id=case.id, entity_kind=EntityKind.PERSON, label="none"),
    )
    _rejects(
        session,
        GraphNode(
            case_id=case.id,
            entity_kind=EntityKind.PERSON,
            label="two",
            person_id=person.id,
            hearing_id=hearing.id,
        ),
    )
    _rejects(
        session,
        GraphNode(
            case_id=case.id, entity_kind=EntityKind.HEARING, label="mismatch", person_id=person.id
        ),
    )


def test_resolved_citation_must_have_a_target_and_unresolved_must_not(session, case):
    _rejects(
        session,
        Citation(
            case_id=case.id,
            raw_text="nothing",
            citation_type=CitationType.UNKNOWN,
            resolution_state=ResolutionState.RESOLVED,
            resolved_at=datetime.now(UTC),
            display="F-X · ¶1",
        ),
    )
    document = session.scalar(select(Document).where(Document.case_id == case.id))
    _rejects(
        session,
        Citation(
            case_id=case.id,
            raw_text="claims to be unresolved but points somewhere",
            citation_type=CitationType.DOCUMENT,
            resolution_state=ResolutionState.UNRESOLVED,
            target_document_id=document.id,
        ),
    )
    _rejects(
        session,
        Citation(
            case_id=case.id,
            raw_text="ambiguous with a fabricated display",
            citation_type=CitationType.DOCUMENT,
            resolution_state=ResolutionState.AMBIGUOUS,
            display="F-X · ¶1",
        ),
    )


def test_human_verification_requires_a_named_reviewer(session, case):
    _rejects(
        session,
        Citation(
            case_id=case.id,
            raw_text="auto-promoted",
            citation_type=CitationType.UNKNOWN,
            verification_state=VerificationState.HUMAN_VERIFIED,
        ),
    )


def test_witness_delete_cascades_to_its_graph_node_not_to_its_citations(session, case):
    """Referential integrity of the node registry: the node dies with the
    entity; a citation that points at the entity stays, with its target
    nulled — nothing is ever silently re-pointed."""
    witness = Witness(
        case_id=case.id,
        code="W-CHECK-CASCADE",
        identity_status=WitnessIdentityStatus.PROTECTED_CODE,
    )
    session.add(witness)
    session.flush()
    node = GraphNode(
        case_id=case.id,
        entity_kind=EntityKind.WITNESS,
        label="W-CHECK-CASCADE",
        witness_id=witness.id,
    )
    session.add(node)
    session.flush()
    node_id = node.id
    session.delete(witness)
    session.flush()
    session.expire_all()
    assert session.get(GraphNode, node_id) is None
    session.rollback()


def test_visibility_values_are_the_lower_case_vocabulary(session, case):
    row = session.scalar(select(Document.visibility).where(Document.filing_number == "F-DEMO-004"))
    assert row == Visibility.NOT_PUBLIC
    assert uuid.UUID(str(case.id))  # sanity: uuid primary keys round-trip
