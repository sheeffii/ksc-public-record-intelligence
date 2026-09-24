"""Deterministic Phase 9 projection of resolved citations and structured dates.

Only already-persisted public controlled-corpus data is read. No relationship
is inferred from text or co-mention: one resolved citation creates one
``CITED_IN`` edge from the cited document to the citing document.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    Case,
    Citation,
    DatePrecision,
    DateType,
    Document,
    DocumentVersion,
    EntityKind,
    Event,
    Exhibit,
    GraphNode,
    Hearing,
    Party,
    Relationship,
    RelationshipOrigin,
    RelationshipType,
    ResolutionState,
    SourceRecord,
    Transcript,
    Witness,
)

_NS = uuid.UUID("8d01c04f-6f4d-4f81-8eef-1d6160634a9f")


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NS, ":".join(str(part) for part in parts))


@dataclass(frozen=True)
class EvidenceBuildResult:
    nodes: int
    edges: int
    events: int
    skipped_self_citations: int


class Phase9Pipeline:
    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def run(self) -> EvidenceBuildResult:
        with self.sessions() as session, session.begin():
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise RuntimeError(f"case {self.case_number} is not seeded")

            session.execute(
                delete(Relationship).where(
                    Relationship.case_id == case.id,
                    Relationship.extraction_origin == RelationshipOrigin.DETERMINISTIC_CITATION,
                )
            )
            session.execute(
                delete(Event).where(
                    Event.case_id == case.id, Event.extraction_origin == "source_metadata"
                )
            )
            session.flush()
            existing_edge_keys: set[tuple[uuid.UUID, uuid.UUID, RelationshipType, uuid.UUID]] = {
                (from_id, to_id, relationship_type, citation_id)
                for from_id, to_id, relationship_type, citation_id in session.execute(
                    select(
                        Relationship.from_node_id,
                        Relationship.to_node_id,
                        Relationship.relationship_type,
                        Relationship.citation_id,
                    ).where(Relationship.case_id == case.id)
                ).all()
            }

            node_cache: dict[uuid.UUID, GraphNode] = {}

            def node(document: Document) -> GraphNode:
                cached = node_cache.get(document.id)
                if cached is not None:
                    return cached
                existing = session.scalar(
                    select(GraphNode).where(GraphNode.document_id == document.id)
                )
                if existing is None:
                    existing = GraphNode(
                        id=_id("document-node", document.id),
                        case_id=case.id,
                        entity_kind=EntityKind.DOCUMENT,
                        document_id=document.id,
                        label=document.official_ref,
                    )
                    session.add(existing)
                    session.flush()
                node_cache[document.id] = existing
                return existing

            def target_node(citation: Citation) -> GraphNode | None:
                target_document = self._target_document(session, citation)
                if target_document is not None:
                    if target_document.visibility not in PUBLIC_VISIBILITIES:
                        return None
                    return node(target_document)
                entity: Exhibit | Witness | None
                kind: EntityKind
                column: str
                label: str
                if citation.target_exhibit_id is not None:
                    entity = session.get(Exhibit, citation.target_exhibit_id)
                    if entity is None or entity.visibility not in PUBLIC_VISIBILITIES:
                        return None
                    kind, column, label = (
                        EntityKind.EXHIBIT,
                        "exhibit_id",
                        entity.official_exhibit_id,
                    )
                elif citation.target_witness_id is not None:
                    entity = session.get(Witness, citation.target_witness_id)
                    if entity is None:
                        return None
                    kind, column, label = EntityKind.WITNESS, "witness_id", entity.code
                else:
                    return None
                cached = node_cache.get(entity.id)
                if cached is not None:
                    return cached
                existing = session.scalar(
                    select(GraphNode).where(getattr(GraphNode, column) == entity.id)
                )
                if existing is None:
                    existing = GraphNode(
                        id=_id(f"{kind.value}-node", entity.id),
                        case_id=case.id,
                        entity_kind=kind,
                        label=label,
                        **{column: entity.id},
                    )
                    session.add(existing)
                    session.flush()
                node_cache[entity.id] = existing
                return existing

            citations = session.scalars(
                select(Citation)
                .where(
                    Citation.case_id == case.id,
                    Citation.resolution_state == ResolutionState.RESOLVED,
                    Citation.source_document_version_id.is_not(None),
                )
                .order_by(Citation.id)
            ).all()
            edges = 0
            skipped = 0
            for citation in citations:
                source_version = session.get(DocumentVersion, citation.source_document_version_id)
                source_doc = (
                    session.get(Document, source_version.document_id) if source_version else None
                )
                if source_doc is None:
                    continue
                if source_doc.visibility not in PUBLIC_VISIBILITIES:
                    continue
                target_doc = self._target_document(session, citation)
                if target_doc is not None and source_doc.id == target_doc.id:
                    skipped += 1
                    continue
                source_node = node(source_doc)
                cited_node = target_node(citation)
                if cited_node is None:
                    continue
                edge_key = (
                    cited_node.id,
                    source_node.id,
                    RelationshipType.CITED_IN,
                    citation.id,
                )
                if edge_key in existing_edge_keys:
                    continue
                category = self._source_category(source_doc)
                session.add(
                    Relationship(
                        id=_id("citation-edge", citation.id),
                        case_id=case.id,
                        from_node_id=cited_node.id,
                        to_node_id=source_node.id,
                        relationship_type=RelationshipType.CITED_IN,
                        citation_id=citation.id,
                        source_category=category,
                        extraction_origin=RelationshipOrigin.DETERMINISTIC_CITATION,
                        relationship_date=source_doc.document_date,
                        date_precision=(
                            DatePrecision.EXACT
                            if source_doc.document_date
                            else DatePrecision.UNKNOWN
                        ),
                        note="The source record contains this exact resolved citation.",
                    )
                )
                existing_edge_keys.add(edge_key)
                edges += 1

            events = 0
            documents = session.scalars(
                select(Document)
                .where(
                    Document.case_id == case.id,
                    Document.visibility.in_(tuple(PUBLIC_VISIBILITIES)),
                    Document.document_date.is_not(None),
                )
                .order_by(Document.official_ref)
            ).all()
            for document in documents:
                source_record = session.scalar(
                    select(SourceRecord)
                    .where(
                        SourceRecord.case_id == case.id,
                        SourceRecord.document_id == document.id,
                    )
                    .order_by(SourceRecord.created_at)
                    .limit(1)
                )
                date_type = (
                    DateType.DECISION
                    if document.document_type.lower() in {"decision", "order", "judgment"}
                    else DateType.DOCUMENT
                )
                session.add(
                    Event(
                        id=_id("document-date", document.id),
                        case_id=case.id,
                        title=document.title,
                        description=f"Document date recorded for {document.official_ref}.",
                        date_type=date_type,
                        date_from=document.document_date,
                        date_precision=DatePrecision.EXACT,
                        document_id=document.id,
                        source_record_id=source_record.id if source_record else None,
                        extraction_origin="source_metadata",
                    )
                )
                events += 1

            hearings = session.scalars(
                select(Hearing)
                .where(
                    Hearing.case_id == case.id,
                    Hearing.visibility.in_(tuple(PUBLIC_VISIBILITIES)),
                )
                .order_by(Hearing.hearing_date, Hearing.session_sequence)
            ).all()
            for hearing in hearings:
                transcript = session.scalar(
                    select(Transcript)
                    .where(Transcript.hearing_id == hearing.id)
                    .order_by(Transcript.created_at)
                    .limit(1)
                )
                document_id = None
                if transcript and transcript.document_version_id:
                    version = session.get(DocumentVersion, transcript.document_version_id)
                    document_id = version.document_id if version else None
                source_record = session.scalar(
                    select(SourceRecord)
                    .where(
                        SourceRecord.case_id == case.id,
                        SourceRecord.hearing_id == hearing.id,
                    )
                    .order_by(SourceRecord.created_at)
                    .limit(1)
                )
                session.add(
                    Event(
                        id=_id("hearing-date", hearing.id),
                        case_id=case.id,
                        title=f"Hearing {hearing.official_ref or hearing.hearing_date.isoformat()}",
                        description="Public hearing/testimony date from the official source record.",
                        date_type=DateType.TESTIMONY,
                        date_from=hearing.hearing_date,
                        date_precision=DatePrecision.EXACT,
                        document_id=document_id,
                        hearing_id=hearing.id,
                        source_record_id=source_record.id if source_record else None,
                        extraction_origin="source_metadata",
                    )
                )
                events += 1
            session.flush()
            return EvidenceBuildResult(
                nodes=len(node_cache), edges=edges, events=events, skipped_self_citations=skipped
            )

    @staticmethod
    def _target_document(session: Session, citation: Citation) -> Document | None:
        if citation.target_document_id:
            return session.get(Document, citation.target_document_id)
        if citation.target_document_version_id:
            version = session.get(DocumentVersion, citation.target_document_version_id)
            return session.get(Document, version.document_id) if version else None
        transcript_id = citation.target_transcript_id
        if citation.target_transcript_segment_id:
            from ksc_api.models import TranscriptSegment

            segment = session.get(TranscriptSegment, citation.target_transcript_segment_id)
            transcript_id = segment.transcript_id if segment else None
        if transcript_id:
            transcript = session.get(Transcript, transcript_id)
            version = (
                session.get(DocumentVersion, transcript.document_version_id)
                if transcript and transcript.document_version_id
                else None
            )
            return session.get(Document, version.document_id) if version else None
        return None

    @staticmethod
    def _source_category(document: Document) -> str:
        if document.document_type.lower() == "transcript":
            return "witness"
        if document.filing_party == Party.SPO:
            return "spo"
        if document.filing_party == Party.DEFENCE:
            return "defence"
        return "court"
