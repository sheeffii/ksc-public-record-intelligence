"""Typed, evidence-backed graph edges beyond citations (Phase 19B).

Every edge answers "why does this exist?" with one exact source anchor:

- ``TESTIFIED_AT`` (witness or publicly named person → hearing): a
  header-backed ``witness_appearances`` row. One edge per subject and hearing;
  ``evidence_count`` counts the transcript versions whose headers state it.
- ``MENTIONED_IN`` (person or organization → document): verified body-text
  ``entity_occurrences``. One edge per entity and document; the evidence
  anchor is the first verified occurrence and ``evidence_count`` counts them.

Speaker labels are not mentions of the document's subject and produce no edge.
Witness codes and exhibits already have citation-backed ``CITED_IN`` edges and
are not duplicated. Co-occurrence never produces an edge, and an edge never
implies responsibility, agreement or wrongdoing.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    Case,
    DatePrecision,
    Document,
    DocumentVersion,
    EntityKind,
    EntityOccurrence,
    GraphNode,
    Hearing,
    Organization,
    Person,
    Relationship,
    RelationshipOrigin,
    RelationshipType,
    Witness,
    WitnessAppearance,
)
from ksc_ingestion.evidence_pipeline import Phase9Pipeline, _id
from ksc_ingestion.verified_mentions import PAGE_TEXT, SEGMENT_TEXT, VERIFIED


@dataclass(frozen=True)
class TypedEdgeResult:
    testified_at: int
    mentioned_in: int
    nodes_created: int


class _Nodes:
    def __init__(self, session: Session, case: Case) -> None:
        self.session = session
        self.case = case
        self.cache: dict[tuple[str, uuid.UUID], GraphNode] = {}
        self.created = 0

    def get(self, kind: EntityKind, column: str, entity_id: uuid.UUID, label: str) -> GraphNode:
        key = (column, entity_id)
        node = self.cache.get(key)
        if node is None:
            node = self.session.scalar(
                select(GraphNode).where(getattr(GraphNode, column) == entity_id)
            )
            if node is None:
                node = GraphNode(
                    id=_id(f"{kind.value}-node", entity_id),
                    case_id=self.case.id,
                    entity_kind=kind,
                    label=label[:255],
                    **{column: entity_id},
                )
                self.session.add(node)
                self.session.flush()
                self.created += 1
            self.cache[key] = node
        return node


def project_typed_edges(session: Session, case: Case) -> TypedEdgeResult:
    session.execute(
        delete(Relationship).where(
            Relationship.case_id == case.id,
            Relationship.extraction_origin == RelationshipOrigin.DETERMINISTIC_OCCURRENCE,
        )
    )
    nodes = _Nodes(session, case)

    # TESTIFIED_AT from header-backed appearances.
    appearances = session.execute(
        select(WitnessAppearance, Hearing, DocumentVersion)
        .join(Hearing, Hearing.id == WitnessAppearance.hearing_id)
        .join(DocumentVersion, DocumentVersion.id == WitnessAppearance.document_version_id)
        .where(Hearing.case_id == case.id, WitnessAppearance.rule_id.is_not(None))
        .order_by(DocumentVersion.official_version_ref)
    ).all()
    by_subject: dict[tuple[uuid.UUID, uuid.UUID], list[WitnessAppearance]] = defaultdict(list)
    hearings: dict[uuid.UUID, Hearing] = {}
    for appearance, hearing, _version in appearances:
        subject = appearance.witness_id or appearance.person_id
        assert subject is not None  # CHECK exactly_one_subject
        by_subject[(subject, hearing.id)].append(appearance)
        hearings[hearing.id] = hearing
    testified = 0
    for (_subject, hearing_id), subject_rows in sorted(
        by_subject.items(), key=lambda item: str(item[0])
    ):
        appearance_first = subject_rows[0]
        hearing = hearings[hearing_id]
        if appearance_first.witness_id is not None:
            witness = session.get(Witness, appearance_first.witness_id)
            assert witness is not None
            source = nodes.get(EntityKind.WITNESS, "witness_id", witness.id, witness.code)
        else:
            subject_person = session.get(Person, appearance_first.person_id)
            assert subject_person is not None
            source = nodes.get(
                EntityKind.PERSON, "person_id", subject_person.id, subject_person.display_name
            )
        target = nodes.get(
            EntityKind.HEARING,
            "hearing_id",
            hearing.id,
            hearing.session_label or hearing.hearing_date.isoformat(),
        )
        session.add(
            Relationship(
                id=_id("appearance-edge", source.id, target.id),
                case_id=case.id,
                from_node_id=source.id,
                to_node_id=target.id,
                relationship_type=RelationshipType.TESTIFIED_AT,
                witness_appearance_id=appearance_first.id,
                evidence_count=len(subject_rows),
                source_category="witness",
                extraction_origin=RelationshipOrigin.DETERMINISTIC_OCCURRENCE,
                relationship_date=hearing.hearing_date,
                date_precision=DatePrecision.EXACT,
                note="The official transcript page header states this witness for this hearing.",
            )
        )
        testified += 1

    # MENTIONED_IN from verified body-text mentions of people and organizations.
    occurrences = session.execute(
        select(EntityOccurrence, DocumentVersion, Document)
        .join(DocumentVersion, DocumentVersion.id == EntityOccurrence.document_version_id)
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(
            EntityOccurrence.case_id == case.id,
            EntityOccurrence.mention_state == VERIFIED,
            EntityOccurrence.rule_id.is_not(None),
            EntityOccurrence.char_anchor.in_([SEGMENT_TEXT, PAGE_TEXT]),
            EntityOccurrence.witness_id.is_(None),
            EntityOccurrence.exhibit_id.is_(None),
            Document.visibility.in_(tuple(PUBLIC_VISIBILITIES)),
            DocumentVersion.visibility.in_(tuple(PUBLIC_VISIBILITIES)),
        )
        .order_by(
            DocumentVersion.official_version_ref,
            EntityOccurrence.pdf_page_index.nulls_last(),
            EntityOccurrence.line_from.nulls_last(),
            EntityOccurrence.char_start,
            EntityOccurrence.id,
        )
    ).all()
    grouped: dict[tuple[uuid.UUID, uuid.UUID], list[EntityOccurrence]] = defaultdict(list)
    documents: dict[uuid.UUID, Document] = {}
    for occurrence, _version, document in occurrences:
        entity = occurrence.person_id or occurrence.organization_id
        assert entity is not None
        grouped[(entity, document.id)].append(occurrence)
        documents[document.id] = document
    mentioned = 0
    for (_entity, document_id), rows in sorted(grouped.items(), key=lambda item: str(item[0])):
        first = rows[0]
        document = documents[document_id]
        if first.person_id is not None:
            person = session.get(Person, first.person_id)
            assert person is not None
            source = nodes.get(EntityKind.PERSON, "person_id", person.id, person.display_name)
        else:
            organization = session.get(Organization, first.organization_id)
            assert organization is not None
            source = nodes.get(
                EntityKind.ORGANIZATION, "organization_id", organization.id, organization.name
            )
        target = nodes.get(EntityKind.DOCUMENT, "document_id", document.id, document.official_ref)
        session.add(
            Relationship(
                id=_id("mention-edge", source.id, target.id),
                case_id=case.id,
                from_node_id=source.id,
                to_node_id=target.id,
                relationship_type=RelationshipType.MENTIONED_IN,
                entity_occurrence_id=first.id,
                evidence_count=len(rows),
                source_category=Phase9Pipeline._source_category(document),
                extraction_origin=RelationshipOrigin.DETERMINISTIC_OCCURRENCE,
                relationship_date=document.document_date,
                date_precision=(
                    DatePrecision.EXACT if document.document_date else DatePrecision.UNKNOWN
                ),
                note="The document contains verified mentions of this entity; presence only.",
            )
        )
        mentioned += 1
    session.flush()
    return TypedEdgeResult(
        testified_at=testified, mentioned_in=mentioned, nodes_created=nodes.created
    )
