"""Phase 19B structured-intelligence reads.

One provenance contract (`ProvenanceRead`) for every evidence kind, so
dossiers, the Reader, network, timeline and future retrieval consume the same
shape: document version → page / paragraph / line → character range → text.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, aliased

from ksc_api.models import (
    Case,
    Citation,
    Document,
    DocumentVersion,
    EntityKind,
    EntityOccurrence,
    Exhibit,
    ExhibitStatusEvent,
    GraphNode,
    Hearing,
    Person,
    Relationship,
    RelationshipType,
    Transcript,
    TranscriptSegment,
    Witness,
    WitnessAppearance,
    version_language,
)
from ksc_api.repositories.filters import (
    citation_resolved,
    node_is_public,
    not_rejected,
    public_visibility,
)
from ksc_api.schemas.records import (
    EdgePageRead,
    EdgeRead,
    EvidenceKind,
    ExhibitStatusEventRead,
    GraphNodeRead,
    ProvenanceRead,
    WitnessAppearanceRead,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

MAX_EDGE_PAGE = 200


class IntelligenceReadsMixin:
    """Mixed into `RecordRepository`; relies on its session, case and node helpers."""

    session: Session
    case: Case

    if TYPE_CHECKING:

        def _focus_node_ids(self, ref: str) -> list[uuid.UUID]: ...
        def _nodes(self, node_ids: set[uuid.UUID]) -> list[GraphNodeRead]: ...

    # ------------------------------------------------------------ helpers --
    def _public_version_ids(self) -> Any:
        return (
            select(DocumentVersion.id)
            .join(Document, Document.id == DocumentVersion.document_id)
            .where(
                Document.case_id == self.case.id,
                public_visibility(Document.visibility),
                public_visibility(DocumentVersion.visibility),
            )
        )

    def _versions(
        self, ids: set[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[DocumentVersion, Document, Transcript | None]]:
        if not ids:
            return {}
        rows = self.session.execute(
            select(DocumentVersion, Document, Transcript)
            .join(Document, Document.id == DocumentVersion.document_id)
            .outerjoin(Transcript, Transcript.document_version_id == DocumentVersion.id)
            .where(DocumentVersion.id.in_(list(ids)))
        ).all()
        return {
            version.id: (version, document, transcript) for version, document, transcript in rows
        }

    @staticmethod
    def _provenance(
        kind: EvidenceKind,
        rule: str | None,
        version: DocumentVersion,
        document: Document,
        transcript: Transcript | None,
        *,
        pdf_page_index: int | None,
        page: int | None,
        paragraph: int | None,
        line_from: int | None,
        line_to: int | None,
        char_anchor: str | None,
        char_start: int | None,
        char_end: int | None,
        text: str,
        language: str | None,
    ) -> ProvenanceRead:
        from ksc_api.repositories.records import _document_target_path

        return ProvenanceRead(
            kind=kind,
            rule=rule,
            document_ref=document.official_ref,
            document_title=document.title,
            version_ref=version.official_version_ref,
            language=language
            or version_language(
                version.official_version_ref,
                transcript.language if transcript else document.language,
            ),
            pdf_page_index=pdf_page_index,
            page=page,
            paragraph=paragraph,
            line_from=line_from,
            line_to=line_to,
            char_anchor=char_anchor,
            char_start=char_start,
            char_end=char_end,
            text=text,
            source_url=version.source_url,
            target_path=_document_target_path(
                document,
                version,
                pdf_page_index=pdf_page_index,
                paragraph=paragraph,
                page=page,
                line=line_from,
            ),
        )

    def _edge_provenance(self, edges: Sequence[Relationship]) -> dict[uuid.UUID, ProvenanceRead]:
        citation_ids = {e.citation_id for e in edges if e.citation_id}
        occurrence_ids = {e.entity_occurrence_id for e in edges if e.entity_occurrence_id}
        appearance_ids = {e.witness_appearance_id for e in edges if e.witness_appearance_id}
        citations = {
            row.id: row
            for row in self.session.scalars(
                select(Citation).where(Citation.id.in_(list(citation_ids)))
            )
        }
        occurrences = {
            row.id: row
            for row in self.session.scalars(
                select(EntityOccurrence).where(EntityOccurrence.id.in_(list(occurrence_ids)))
            )
        }
        appearances = {
            row.id: row
            for row in self.session.scalars(
                select(WitnessAppearance).where(WitnessAppearance.id.in_(list(appearance_ids)))
            )
        }
        segment_ids = {
            c.source_transcript_segment_id
            for c in citations.values()
            if c.source_transcript_segment_id
        }
        segments = {
            row.id: row
            for row in self.session.scalars(
                select(TranscriptSegment).where(TranscriptSegment.id.in_(list(segment_ids)))
            )
        }
        versions = self._versions(
            {
                c.source_document_version_id
                for c in citations.values()
                if c.source_document_version_id
            }
            | {o.document_version_id for o in occurrences.values()}
            | {a.document_version_id for a in appearances.values() if a.document_version_id}
        )
        result: dict[uuid.UUID, ProvenanceRead] = {}
        for edge in edges:
            if edge.citation_id and edge.citation_id in citations:
                citation = citations[edge.citation_id]
                if citation.source_document_version_id not in versions:
                    continue
                version, document, transcript = versions[citation.source_document_version_id]
                segment = segments.get(citation.source_transcript_segment_id)  # type: ignore[arg-type]
                result[edge.id] = self._provenance(
                    "citation",
                    citation.resolution_rule,
                    version,
                    document,
                    transcript,
                    pdf_page_index=citation.source_pdf_page_index,
                    page=citation.source_page,
                    paragraph=citation.source_para,
                    line_from=segment.line_from if segment else None,
                    line_to=segment.line_to if segment else None,
                    char_anchor=(
                        "transcript_segment_text" if segment is not None else "document_page_text"
                    ),
                    char_start=citation.source_char_start,
                    char_end=citation.source_char_end,
                    text=citation.raw_text,
                    language=None,
                )
            elif edge.entity_occurrence_id and edge.entity_occurrence_id in occurrences:
                occurrence = occurrences[edge.entity_occurrence_id]
                version, document, transcript = versions[occurrence.document_version_id]
                result[edge.id] = self._provenance(
                    "entity_occurrence",
                    occurrence.rule_id,
                    version,
                    document,
                    transcript,
                    pdf_page_index=occurrence.pdf_page_index,
                    page=occurrence.page_number,
                    paragraph=occurrence.paragraph_number,
                    line_from=occurrence.line_from,
                    line_to=occurrence.line_to,
                    char_anchor=occurrence.char_anchor,
                    char_start=occurrence.char_start,
                    char_end=occurrence.char_end,
                    text=occurrence.occurrence_text,
                    language=occurrence.language,
                )
            elif edge.witness_appearance_id and edge.witness_appearance_id in appearances:
                appearance = appearances[edge.witness_appearance_id]
                assert appearance.document_version_id is not None
                version, document, transcript = versions[appearance.document_version_id]
                result[edge.id] = self._appearance_provenance(
                    appearance, version, document, transcript
                )
        return result

    def _appearance_provenance(
        self,
        appearance: WitnessAppearance,
        version: DocumentVersion,
        document: Document,
        transcript: Transcript | None,
    ) -> ProvenanceRead:
        return self._provenance(
            "witness_appearance",
            appearance.rule_id,
            version,
            document,
            transcript,
            pdf_page_index=appearance.signal_pdf_page_index,
            page=appearance.signal_page_number,
            paragraph=None,
            line_from=None,
            line_to=None,
            char_anchor="document_page_text",
            char_start=appearance.signal_char_start,
            char_end=appearance.signal_char_end,
            text=appearance.signal_text or "",
            language=None,
        )

    # --------------------------------------------------- network edges --
    def _typed_edges_stmt(self) -> tuple[Any, Any, Any]:
        """Public, non-rejected edges whose evidence is a resolved citation, a
        verified rule-lineaged mention or a header-backed appearance."""
        from_node, to_node = aliased(GraphNode), aliased(GraphNode)
        from_doc, to_doc = aliased(Document), aliased(Document)
        from_ex, to_ex = aliased(Exhibit), aliased(Exhibit)
        from_h, to_h = aliased(Hearing), aliased(Hearing)
        public_versions = self._public_version_ids()
        stmt = (
            select(Relationship)
            .join(from_node, Relationship.from_node_id == from_node.id)
            .join(to_node, Relationship.to_node_id == to_node.id)
            .outerjoin(from_doc, from_node.document_id == from_doc.id)
            .outerjoin(to_doc, to_node.document_id == to_doc.id)
            .outerjoin(from_ex, from_node.exhibit_id == from_ex.id)
            .outerjoin(to_ex, to_node.exhibit_id == to_ex.id)
            .outerjoin(from_h, from_node.hearing_id == from_h.id)
            .outerjoin(to_h, to_node.hearing_id == to_h.id)
            .outerjoin(Citation, Relationship.citation_id == Citation.id)
            .outerjoin(EntityOccurrence, Relationship.entity_occurrence_id == EntityOccurrence.id)
            .outerjoin(
                WitnessAppearance, Relationship.witness_appearance_id == WitnessAppearance.id
            )
            .where(
                Relationship.case_id == self.case.id,
                not_rejected(Relationship),
                node_is_public(from_node, from_doc, from_ex, from_h),
                node_is_public(to_node, to_doc, to_ex, to_h),
                or_(
                    and_(Relationship.citation_id.is_not(None), citation_resolved()),
                    and_(
                        Relationship.entity_occurrence_id.is_not(None),
                        EntityOccurrence.mention_state == "verified",
                        EntityOccurrence.rule_id.is_not(None),
                        EntityOccurrence.document_version_id.in_(public_versions),
                    ),
                    and_(
                        Relationship.witness_appearance_id.is_not(None),
                        WitnessAppearance.rule_id.is_not(None),
                        WitnessAppearance.document_version_id.in_(public_versions),
                    ),
                ),
            )
        )
        return stmt, from_node, to_node

    def network_edges(
        self,
        *,
        limit: int,
        cursor: str | None = None,
        focus_ref: str | None = None,
        relationship_type: RelationshipType | None = None,
        entity_kind: EntityKind | None = None,
        evidence_kind: EvidenceKind | None = None,
        document_ref: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> EdgePageRead:
        """Bounded, cursor-paginated edges of every evidence kind; never the whole graph."""
        limit = max(1, min(limit, MAX_EDGE_PAGE))
        stmt, from_node, to_node = self._typed_edges_stmt()
        if focus_ref:
            focus = self._focus_node_ids(focus_ref)
            if not focus:
                return EdgePageRead(items=[], nodes=[], total=0, by_type={}, next_cursor=None)
            stmt = stmt.where(
                or_(Relationship.from_node_id.in_(focus), Relationship.to_node_id.in_(focus))
            )
        if relationship_type:
            stmt = stmt.where(Relationship.relationship_type == relationship_type)
        if entity_kind:
            stmt = stmt.where(
                or_(from_node.entity_kind == entity_kind, to_node.entity_kind == entity_kind)
            )
        if evidence_kind:
            column = {
                "citation": Relationship.citation_id,
                "entity_occurrence": Relationship.entity_occurrence_id,
                "witness_appearance": Relationship.witness_appearance_id,
            }[evidence_kind]
            stmt = stmt.where(column.is_not(None))
        if document_ref:
            versions = (
                select(DocumentVersion.id)
                .join(Document, Document.id == DocumentVersion.document_id)
                .where(
                    Document.case_id == self.case.id,
                    Document.official_ref.in_(
                        [document_ref, f"{self.case.case_number}/{document_ref}"]
                    ),
                )
            )
            stmt = stmt.where(
                or_(
                    Citation.source_document_version_id.in_(versions),
                    EntityOccurrence.document_version_id.in_(versions),
                    WitnessAppearance.document_version_id.in_(versions),
                )
            )
        if date_from:
            stmt = stmt.where(Relationship.relationship_date >= date_from)
        if date_to:
            stmt = stmt.where(Relationship.relationship_date <= date_to)

        filtered = stmt.subquery()
        total = int(self.session.scalar(select(func.count()).select_from(filtered)) or 0)
        by_type = {
            str(getattr(kind, "value", kind)): int(count)
            for kind, count in self.session.execute(
                select(filtered.c.relationship_type, func.count()).group_by(
                    filtered.c.relationship_type
                )
            ).all()
        }
        if cursor:
            stmt = stmt.where(Relationship.id > uuid.UUID(cursor))
        edges = list(self.session.scalars(stmt.order_by(Relationship.id).limit(limit + 1)).all())
        next_cursor = str(edges[limit - 1].id) if len(edges) > limit else None
        edges = edges[:limit]
        provenance = self._edge_provenance(edges)
        items = [
            EdgeRead(
                id=edge.id,
                from_node_id=edge.from_node_id,
                to_node_id=edge.to_node_id,
                relationship_type=edge.relationship_type,
                extraction_origin=edge.extraction_origin,
                verification_state=edge.verification_state,
                source_category=edge.source_category,
                relationship_date=edge.relationship_date,
                evidence_count=edge.evidence_count,
                provenance=provenance[edge.id],
            )
            for edge in edges
            if edge.id in provenance
        ]
        node_ids = {item.from_node_id for item in items} | {item.to_node_id for item in items}
        return EdgePageRead(
            items=items,
            nodes=self._nodes(node_ids),
            total=total,
            by_type=by_type,
            next_cursor=next_cursor,
        )

    # --------------------------------------------------- appearances --
    def list_appearances(self, kind: str, key: str) -> list[WitnessAppearanceRead] | None:
        """Header-backed appearances for a witness code or a publicly named person."""
        if kind == "witness":
            subject = self.session.scalar(
                select(Witness.id).where(Witness.case_id == self.case.id, Witness.code == key)
            )
            column = WitnessAppearance.witness_id
        else:
            subject = self.session.scalar(
                select(Person.id).where(Person.case_id == self.case.id, Person.slug == key)
            )
            column = WitnessAppearance.person_id
        if subject is None:
            return None
        rows = self.session.execute(
            select(WitnessAppearance, Hearing)
            .join(Hearing, Hearing.id == WitnessAppearance.hearing_id)
            .where(
                column == subject,
                WitnessAppearance.rule_id.is_not(None),
                WitnessAppearance.document_version_id.in_(self._public_version_ids()),
                public_visibility(Hearing.visibility),
            )
            .order_by(Hearing.hearing_date, WitnessAppearance.document_version_id)
        ).all()
        versions = self._versions(
            {row.document_version_id for row, _ in rows if row.document_version_id}
        )
        result: list[WitnessAppearanceRead] = []
        for appearance, hearing in rows:
            assert appearance.document_version_id is not None
            version, document, transcript = versions[appearance.document_version_id]
            provenance = self._appearance_provenance(appearance, version, document, transcript)
            result.append(
                WitnessAppearanceRead(
                    hearing_date=hearing.hearing_date,
                    session_label=hearing.session_label,
                    transcript_ref=transcript.official_ref if transcript else None,
                    version_ref=version.official_version_ref,
                    language=provenance.language,
                    page_from=appearance.page_from,
                    page_to=appearance.page_to,
                    header_pages=appearance.header_pages or 0,
                    open_session_pages=appearance.open_session_pages or 0,
                    private_session_pages=appearance.private_session_pages or 0,
                    closed_session_pages=appearance.closed_session_pages or 0,
                    examinations=list(appearance.examinations or []),
                    rule_id=appearance.rule_id or "",
                    provenance=provenance,
                )
            )
        return result

    # ------------------------------------------------- exhibit status --
    def list_exhibit_status_events(
        self, official_exhibit_id: str
    ) -> list[ExhibitStatusEventRead] | None:
        exhibit_id = self.session.scalar(
            select(Exhibit.id).where(
                Exhibit.case_id == self.case.id,
                Exhibit.official_exhibit_id == official_exhibit_id,
                public_visibility(Exhibit.visibility),
            )
        )
        if exhibit_id is None:
            return None
        events = self.session.scalars(
            select(ExhibitStatusEvent)
            .where(
                ExhibitStatusEvent.exhibit_id == exhibit_id,
                ExhibitStatusEvent.document_version_id.in_(self._public_version_ids()),
            )
            .order_by(
                ExhibitStatusEvent.event_date.nulls_last(),
                ExhibitStatusEvent.document_version_id,
                ExhibitStatusEvent.page_number.nulls_last(),
                ExhibitStatusEvent.line_from.nulls_last(),
            )
        ).all()
        versions = self._versions({event.document_version_id for event in events})
        result: list[ExhibitStatusEventRead] = []
        for event in events:
            version, document, transcript = versions[event.document_version_id]
            result.append(
                ExhibitStatusEventRead(
                    exhibit_identifier=event.exhibit_identifier,
                    event_type=event.event_type,
                    classification=event.classification,
                    statement_date=event.event_date,
                    speaker=event.speaker,
                    rule_id=event.rule_id,
                    provenance=self._provenance(
                        "exhibit_status_event",
                        event.rule_id,
                        version,
                        document,
                        transcript,
                        pdf_page_index=event.pdf_page_index,
                        page=event.page_number,
                        paragraph=None,
                        line_from=event.line_from,
                        line_to=event.line_to,
                        char_anchor=event.char_anchor,
                        char_start=event.char_start,
                        char_end=event.char_end,
                        text=event.occurrence_text,
                        language=event.language,
                    ),
                )
            )
        return result
