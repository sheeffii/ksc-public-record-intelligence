"""RecordRepository — typed, case-scoped, public-only reads.

Rules applied to every query:
- scoped to the configured case (the case is never a route segment);
- documents / versions / exhibits / hearings / transcripts: PUBLIC or
  PUBLIC_REDACTED only, except that a document known to exist but not public
  is *stated* by `get_document` with no versions (ROUTE_MAP.md §8);
- human-rejected facts and anything depending on an unresolved citation are
  withheld;
- protected witnesses serialise as code only.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from ksc_api.config import Settings, get_settings
from ksc_api.db.session import get_session
from ksc_api.models import (
    Argument,
    Case,
    Citation,
    Claim,
    ClaimMention,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentVersion,
    EntityKind,
    Event,
    Exhibit,
    Finding,
    FindingEvidenceLink,
    GraphNode,
    Hearing,
    Incident,
    Location,
    Organization,
    Person,
    RecordIdentifier,
    Relationship,
    ResolutionState,
    Transcript,
    TranscriptSegment,
    Witness,
    normalize_identifier,
)
from ksc_api.repositories import mappers
from ksc_api.repositories.filters import (
    citation_resolved,
    node_is_public,
    not_rejected,
    public_visibility,
)
from ksc_api.schemas.citation import CitationRead, IdentifierMatch, ResolveResult
from ksc_api.schemas.common import Page
from ksc_api.schemas.records import (
    ArgumentRead,
    CaseRead,
    ClaimRead,
    DocumentChunkRead,
    DocumentDetail,
    DocumentPageRead,
    DocumentSummary,
    EventRead,
    ExhibitRead,
    FindingDetail,
    FindingSummary,
    GraphNodeRead,
    IncidentRead,
    NetworkRead,
    PersonRead,
    ReferenceCounts,
    RelationshipRead,
    SearchHit,
    SearchRead,
    TranscriptRead,
    WitnessRead,
)

# Eager-load everything `mappers.to_citation` touches, so serialisation never
# lazy-loads after the session is gone.
CITATION_LOAD = (
    selectinload(Citation.target_document),
    selectinload(Citation.target_document_version).selectinload(DocumentVersion.document),
    selectinload(Citation.target_transcript)
    .selectinload(Transcript.document_version)
    .selectinload(DocumentVersion.document),
    selectinload(Citation.target_exhibit)
    .selectinload(Exhibit.document_version)
    .selectinload(DocumentVersion.document),
    selectinload(Citation.target_witness),
    selectinload(Citation.target_finding).selectinload(Finding.judgment_document),
)


class CaseNotConfiguredError(LookupError):
    """The configured case number has no row. Seed first."""


class RecordRepository:
    def __init__(self, session: Session, case: Case) -> None:
        self.session = session
        self.case = case

    # ------------------------------------------------------------ helpers --
    def _paginate[T](
        self, stmt: Select[tuple[T]], limit: int, offset: int
    ) -> tuple[Sequence[T], int]:
        total = self.session.scalar(
            select(func.count()).select_from(stmt.order_by(None).subquery())
        )
        rows = self.session.scalars(stmt.limit(limit).offset(offset)).all()
        return rows, int(total or 0)

    def _counts(
        self, kind: EntityKind, ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, ReferenceCounts]:
        """Reference counts (counts only — never a score). See `ReferenceCounts`."""
        if not ids:
            return {}
        id_list = list(ids)
        node_fk = getattr(GraphNode, _NODE_FK[kind])
        edges = self._public_edges_stmt().subquery()
        other = aliased(GraphNode)
        # (entity id, neighbouring node kind) -> number of public edges.
        by_kind: dict[tuple[uuid.UUID, EntityKind], int] = {}
        totals: dict[uuid.UUID, int] = {}
        rows = self.session.execute(
            select(node_fk, other.entity_kind, func.count(edges.c.id))
            .select_from(GraphNode)
            .join(
                edges,
                or_(edges.c.from_node_id == GraphNode.id, edges.c.to_node_id == GraphNode.id),
            )
            .join(
                other,
                or_(
                    and_(edges.c.from_node_id == GraphNode.id, edges.c.to_node_id == other.id),
                    and_(edges.c.to_node_id == GraphNode.id, edges.c.from_node_id == other.id),
                ),
            )
            .where(node_fk.in_(id_list))
            .group_by(node_fk, other.entity_kind)
        ).all()
        for entity_id, other_kind, count in rows:
            by_kind[(entity_id, EntityKind(other_kind))] = int(count)
            totals[entity_id] = totals.get(entity_id, 0) + int(count)

        segment_counts: dict[uuid.UUID, int] = {}
        if kind == EntityKind.WITNESS:
            segment_counts = {
                row[0]: int(row[1])
                for row in self.session.execute(
                    select(TranscriptSegment.witness_id, func.count(TranscriptSegment.id))
                    .join(Transcript, TranscriptSegment.transcript_id == Transcript.id)
                    .where(
                        TranscriptSegment.witness_id.in_(id_list),
                        TranscriptSegment.closed_session.is_(False),
                        public_visibility(Transcript.visibility),
                    )
                    .group_by(TranscriptSegment.witness_id)
                ).all()
            }

        citation_counts: dict[uuid.UUID, int] = {}
        citation_fk = _CITATION_FK.get(kind)
        if citation_fk is not None:
            column = getattr(Citation, citation_fk)
            citation_counts = {
                row[0]: int(row[1])
                for row in self.session.execute(
                    select(column, func.count(Citation.id))
                    .where(column.in_(id_list), citation_resolved())
                    .group_by(column)
                ).all()
            }

        def _n(entity_id: uuid.UUID, other_kind: EntityKind) -> int:
            return by_kind.get((entity_id, other_kind), 0)

        return {
            entity_id: ReferenceCounts(
                relationships=totals.get(entity_id, 0),
                document_mentions=_n(entity_id, EntityKind.DOCUMENT),
                transcript_mentions=_n(entity_id, EntityKind.HEARING)
                + segment_counts.get(entity_id, 0),
                exhibit_refs=_n(entity_id, EntityKind.EXHIBIT),
                findings=_n(entity_id, EntityKind.FINDING),
                witnesses_who_referred=_n(entity_id, EntityKind.WITNESS),
                incidents=_n(entity_id, EntityKind.INCIDENT),
                citations_resolved=citation_counts.get(entity_id, 0),
            )
            for entity_id in id_list
        }

    def _public_edges_stmt(self) -> Select[tuple[Relationship]]:
        from_node = aliased(GraphNode)
        to_node = aliased(GraphNode)
        from_doc, to_doc = aliased(Document), aliased(Document)
        from_ex, to_ex = aliased(Exhibit), aliased(Exhibit)
        from_hearing, to_hearing = aliased(Hearing), aliased(Hearing)
        return (
            select(Relationship)
            .join(Citation, Relationship.citation_id == Citation.id)
            .join(from_node, Relationship.from_node_id == from_node.id)
            .join(to_node, Relationship.to_node_id == to_node.id)
            .outerjoin(from_doc, from_node.document_id == from_doc.id)
            .outerjoin(to_doc, to_node.document_id == to_doc.id)
            .outerjoin(from_ex, from_node.exhibit_id == from_ex.id)
            .outerjoin(to_ex, to_node.exhibit_id == to_ex.id)
            .outerjoin(from_hearing, from_node.hearing_id == from_hearing.id)
            .outerjoin(to_hearing, to_node.hearing_id == to_hearing.id)
            .where(
                Relationship.case_id == self.case.id,
                not_rejected(Relationship),
                citation_resolved(),
                node_is_public(from_node, from_doc, from_ex, from_hearing),
                node_is_public(to_node, to_doc, to_ex, to_hearing),
            )
        )

    # --------------------------------------------------------------- case --
    def get_case(self) -> CaseRead:
        return mappers.to_case(self.case)

    # ---------------------------------------------------------- documents --
    def list_documents(
        self, *, limit: int, offset: int, document_type: str | None = None, q: str | None = None
    ) -> Page[DocumentSummary]:
        stmt = (
            select(Document)
            .where(Document.case_id == self.case.id, public_visibility(Document.visibility))
            .order_by(Document.filing_date.desc().nulls_last(), Document.official_ref)
        )
        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if q:
            stmt = stmt.where(
                _ilike_any(q, Document.title, Document.official_ref, Document.filing_number)
            )
        rows, total = self._paginate(stmt, limit, offset)
        counts = self._counts(EntityKind.DOCUMENT, [d.id for d in rows])
        items = [
            mappers.to_document_summary(d, counts.get(d.id, mappers.ZERO_COUNTS)) for d in rows
        ]
        return Page(items=items, total=total, limit=limit, offset=offset)

    def get_document(self, ref: str) -> DocumentDetail | None:
        """Any visibility: a not-public document is returned with no versions
        so the UI can say "exists, not public" instead of 404. UNKNOWN and
        PRIVATE_AUTHORIZED are treated the same way — stated, never shown."""
        document = self.session.scalar(
            select(Document)
            .options(selectinload(Document.versions).selectinload(DocumentVersion.supersedes))
            .where(
                Document.case_id == self.case.id,
                or_(Document.official_ref == ref, Document.filing_number == ref),
            )
        )
        if document is None:
            return None
        public_versions = (
            [v for v in document.versions if v.visibility in _PUBLIC]
            if document.visibility in _PUBLIC
            else []
        )
        counts = self._counts(EntityKind.DOCUMENT, [document.id]).get(
            document.id, mappers.ZERO_COUNTS
        )
        return mappers.to_document_detail(document, counts, public_versions)

    def list_document_pages(
        self, version_ref: str, *, limit: int, offset: int
    ) -> Page[DocumentPageRead] | None:
        version = self._public_version(version_ref)
        if version is None:
            return None
        stmt = (
            select(DocumentPage)
            .where(DocumentPage.document_version_id == version.id)
            .order_by(DocumentPage.page_number)
        )
        rows, total = self._paginate(stmt, limit, offset)
        return Page(
            items=[mappers.to_document_page(p) for p in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def list_document_chunks(
        self, version_ref: str, *, limit: int, offset: int
    ) -> Page[DocumentChunkRead] | None:
        version = self._public_version(version_ref)
        if version is None:
            return None
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_version_id == version.id)
            .order_by(DocumentChunk.sequence)
        )
        rows, total = self._paginate(stmt, limit, offset)
        return Page(
            items=[mappers.to_document_chunk(c) for c in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def _public_version(self, version_ref: str) -> DocumentVersion | None:
        return self.session.scalar(
            select(DocumentVersion)
            .join(Document)
            .where(
                Document.case_id == self.case.id,
                DocumentVersion.official_version_ref == version_ref,
                public_visibility(DocumentVersion.visibility),
                public_visibility(Document.visibility),
            )
        )

    # ------------------------------------------------------------- people --
    def list_persons(self, *, limit: int, offset: int, q: str | None = None) -> Page[PersonRead]:
        stmt = (
            select(Person)
            .options(selectinload(Person.aliases))
            .where(Person.case_id == self.case.id)
            .order_by(Person.display_name)
        )
        if q:
            stmt = stmt.where(_ilike_any(q, Person.display_name, Person.slug))
        rows, total = self._paginate(stmt, limit, offset)
        counts = self._counts(EntityKind.PERSON, [p.id for p in rows])
        items = [mappers.to_person(p, counts.get(p.id, mappers.ZERO_COUNTS)) for p in rows]
        return Page(items=items, total=total, limit=limit, offset=offset)

    def get_person(self, slug: str) -> PersonRead | None:
        person = self.session.scalar(
            select(Person)
            .options(selectinload(Person.aliases))
            .where(Person.case_id == self.case.id, Person.slug == slug)
        )
        if person is None:
            return None
        counts = self._counts(EntityKind.PERSON, [person.id]).get(person.id, mappers.ZERO_COUNTS)
        return mappers.to_person(person, counts)

    # ---------------------------------------------------------- witnesses --
    def list_witnesses(self, *, limit: int, offset: int) -> Page[WitnessRead]:
        stmt = select(Witness).where(Witness.case_id == self.case.id).order_by(Witness.code)
        rows, total = self._paginate(stmt, limit, offset)
        counts = self._counts(EntityKind.WITNESS, [w.id for w in rows])
        items = [mappers.to_witness(w, counts.get(w.id, mappers.ZERO_COUNTS)) for w in rows]
        return Page(items=items, total=total, limit=limit, offset=offset)

    def get_witness(self, code: str) -> WitnessRead | None:
        witness = self.session.scalar(
            select(Witness).where(Witness.case_id == self.case.id, Witness.code == code)
        )
        if witness is None:
            return None
        counts = self._counts(EntityKind.WITNESS, [witness.id]).get(witness.id, mappers.ZERO_COUNTS)
        return mappers.to_witness(witness, counts)

    # ----------------------------------------------------------- exhibits --
    def list_exhibits(self, *, limit: int, offset: int) -> Page[ExhibitRead]:
        stmt = (
            select(Exhibit)
            .options(
                selectinload(Exhibit.through_witness),
                selectinload(Exhibit.document_version),
            )
            .where(Exhibit.case_id == self.case.id, public_visibility(Exhibit.visibility))
            .order_by(Exhibit.official_exhibit_id)
        )
        rows, total = self._paginate(stmt, limit, offset)
        counts = self._counts(EntityKind.EXHIBIT, [e.id for e in rows])
        items = [mappers.to_exhibit(e, counts.get(e.id, mappers.ZERO_COUNTS)) for e in rows]
        return Page(items=items, total=total, limit=limit, offset=offset)

    def get_exhibit(self, official_exhibit_id: str) -> ExhibitRead | None:
        exhibit = self.session.scalar(
            select(Exhibit)
            .options(
                selectinload(Exhibit.through_witness),
                selectinload(Exhibit.document_version),
            )
            .where(
                Exhibit.case_id == self.case.id,
                Exhibit.official_exhibit_id == official_exhibit_id,
                public_visibility(Exhibit.visibility),
            )
        )
        if exhibit is None:
            return None
        counts = self._counts(EntityKind.EXHIBIT, [exhibit.id]).get(exhibit.id, mappers.ZERO_COUNTS)
        return mappers.to_exhibit(exhibit, counts)

    # ---------------------------------------------------------- incidents --
    def list_incidents(self, *, limit: int, offset: int) -> Page[IncidentRead]:
        stmt = (
            select(Incident)
            .options(selectinload(Incident.location))
            .where(Incident.case_id == self.case.id)
            .order_by(Incident.date_from.nulls_last(), Incident.slug)
        )
        rows, total = self._paginate(stmt, limit, offset)
        counts = self._counts(EntityKind.INCIDENT, [i.id for i in rows])
        items = [mappers.to_incident(i, counts.get(i.id, mappers.ZERO_COUNTS)) for i in rows]
        return Page(items=items, total=total, limit=limit, offset=offset)

    def get_incident(self, slug: str) -> IncidentRead | None:
        incident = self.session.scalar(
            select(Incident)
            .options(selectinload(Incident.location))
            .where(Incident.case_id == self.case.id, Incident.slug == slug)
        )
        if incident is None:
            return None
        counts = self._counts(EntityKind.INCIDENT, [incident.id]).get(
            incident.id, mappers.ZERO_COUNTS
        )
        return mappers.to_incident(incident, counts)

    # ----------------------------------------------------------- findings --
    def _findings_stmt(self) -> Select[tuple[Finding]]:
        return (
            select(Finding)
            .options(
                selectinload(Finding.judgment_document),
                selectinload(Finding.person),
                selectinload(Finding.incident),
                selectinload(Finding.citation).options(*CITATION_LOAD),
            )
            .join(Document, Finding.judgment_document_id == Document.id)
            .where(
                Finding.case_id == self.case.id,
                not_rejected(Finding),
                public_visibility(Document.visibility),
            )
        )

    def list_findings(self, *, limit: int, offset: int) -> Page[FindingSummary]:
        stmt = self._findings_stmt().order_by(Finding.para_from, Finding.finding_key)
        rows, total = self._paginate(stmt, limit, offset)
        counts = self._counts(EntityKind.FINDING, [f.id for f in rows])
        items = [mappers.to_finding_summary(f, counts.get(f.id, mappers.ZERO_COUNTS)) for f in rows]
        return Page(items=items, total=total, limit=limit, offset=offset)

    def get_finding(self, finding_key: str) -> FindingDetail | None:
        finding = self.session.scalar(
            self._findings_stmt().where(Finding.finding_key == finding_key)
        )
        if finding is None:
            return None
        links = self.session.scalars(
            select(FindingEvidenceLink)
            .options(selectinload(FindingEvidenceLink.citation).options(*CITATION_LOAD))
            .join(Citation, FindingEvidenceLink.citation_id == Citation.id)
            .where(
                FindingEvidenceLink.finding_id == finding.id,
                not_rejected(FindingEvidenceLink),
                citation_resolved(),
            )
            .order_by(FindingEvidenceLink.link_type, FindingEvidenceLink.created_at)
        ).all()
        arguments = self.session.scalars(
            select(Argument)
            .options(
                selectinload(Argument.document),
                selectinload(Argument.citation).options(*CITATION_LOAD),
            )
            .where(Argument.finding_id == finding.id, not_rejected(Argument))
            .order_by(Argument.party, Argument.argument_key)
        ).all()
        counts = self._counts(EntityKind.FINDING, [finding.id]).get(finding.id, mappers.ZERO_COUNTS)
        return mappers.to_finding_detail(finding, counts, list(links), list(arguments))

    # ------------------------------------------------------------- claims --
    def list_claims(self, *, limit: int, offset: int) -> Page[ClaimRead]:
        stmt = (
            select(Claim)
            .options(selectinload(Claim.source_citation).options(*CITATION_LOAD))
            .where(Claim.case_id == self.case.id, not_rejected(Claim))
            .order_by(Claim.claim_key)
        )
        rows, total = self._paginate(stmt, limit, offset)
        items = [mappers.to_claim(c, self._public_mentions(c.id)) for c in rows]
        return Page(items=items, total=total, limit=limit, offset=offset)

    def get_claim(self, claim_key: str) -> ClaimRead | None:
        claim = self.session.scalar(
            select(Claim)
            .options(selectinload(Claim.source_citation).options(*CITATION_LOAD))
            .where(Claim.case_id == self.case.id, Claim.claim_key == claim_key, not_rejected(Claim))
        )
        if claim is None:
            return None
        return mappers.to_claim(claim, self._public_mentions(claim.id))

    def _public_mentions(self, claim_id: uuid.UUID) -> list[ClaimMention]:
        return list(
            self.session.scalars(
                select(ClaimMention)
                .options(selectinload(ClaimMention.citation).options(*CITATION_LOAD))
                .join(Citation, ClaimMention.citation_id == Citation.id)
                .where(
                    ClaimMention.claim_id == claim_id,
                    not_rejected(ClaimMention),
                    citation_resolved(),
                )
                .order_by(ClaimMention.stance, ClaimMention.created_at)
            ).all()
        )

    # ---------------------------------------------------------- arguments --
    def list_arguments(self, *, limit: int, offset: int) -> Page[ArgumentRead]:
        stmt = (
            select(Argument)
            .options(
                selectinload(Argument.document),
                selectinload(Argument.citation).options(*CITATION_LOAD),
            )
            .where(Argument.case_id == self.case.id, not_rejected(Argument))
            .order_by(Argument.argument_key)
        )
        rows, total = self._paginate(stmt, limit, offset)
        return Page(
            items=[mappers.to_argument(a) for a in rows], total=total, limit=limit, offset=offset
        )

    # ------------------------------------------------------------- events --
    def list_events(self, *, limit: int, offset: int) -> Page[EventRead]:
        stmt = (
            select(Event, Incident, Document)
            .options(selectinload(Event.citation).options(*CITATION_LOAD))
            .outerjoin(Incident, Event.incident_id == Incident.id)
            .outerjoin(Document, Event.document_id == Document.id)
            .where(
                Event.case_id == self.case.id,
                or_(Event.document_id.is_(None), public_visibility(Document.visibility)),
            )
            .order_by(Event.date_from.nulls_last(), Event.date_type, Event.title)
        )
        total = self.session.scalar(
            select(func.count()).select_from(stmt.order_by(None).subquery())
        )
        rows = self.session.execute(stmt.limit(limit).offset(offset)).all()
        items = [mappers.to_event(event, incident, document) for event, incident, document in rows]
        return Page(items=items, total=int(total or 0), limit=limit, offset=offset)

    # -------------------------------------------------------- transcripts --
    def get_transcript(self, official_ref: str) -> TranscriptRead | None:
        transcript = self.session.scalar(
            select(Transcript)
            .options(
                selectinload(Transcript.hearing),
                selectinload(Transcript.document_version),
            )
            .join(Hearing, Transcript.hearing_id == Hearing.id)
            .where(
                Hearing.case_id == self.case.id,
                Transcript.official_ref == official_ref,
                public_visibility(Transcript.visibility),
                public_visibility(Hearing.visibility),
            )
        )
        if transcript is None:
            return None
        segments = self.session.scalars(
            select(TranscriptSegment)
            .options(selectinload(TranscriptSegment.witness))
            .where(TranscriptSegment.transcript_id == transcript.id)
            .order_by(TranscriptSegment.sequence)
        ).all()
        return mappers.to_transcript(transcript, list(segments))

    # ---------------------------------------------------------- citations --
    def get_citation(self, citation_id: uuid.UUID) -> CitationRead | None:
        citation = self.session.scalar(
            select(Citation)
            .options(*CITATION_LOAD)
            .where(Citation.case_id == self.case.id, Citation.id == citation_id)
        )
        return mappers.to_citation(citation) if citation is not None else None

    def resolve_identifier(self, raw: str) -> ResolveResult:
        """Lookup foundation: exact normalized match in the identifier index.
        Several matches are reported as AMBIGUOUS; nothing is auto-picked."""
        normalized = normalize_identifier(raw)
        rows = self.session.scalars(
            select(RecordIdentifier)
            .where(
                RecordIdentifier.case_id == self.case.id,
                RecordIdentifier.normalized_identifier == normalized,
            )
            .order_by(RecordIdentifier.entity_kind)
        ).all()
        matches = [
            IdentifierMatch(
                identifier=row.identifier,
                entity_kind=row.entity_kind.value,
                entity_id=_identifier_target(row),
                ref=row.identifier,
            )
            for row in rows
        ]
        if not matches:
            state = ResolutionState.UNRESOLVED
        elif len(matches) == 1:
            state = ResolutionState.RESOLVED
        else:
            state = ResolutionState.AMBIGUOUS
        return ResolveResult(query=raw, normalized=normalized, state=state, matches=matches)

    # ------------------------------------------------------------ network --
    def network(self, *, limit: int = 500) -> NetworkRead:
        edges = self.session.scalars(
            self._public_edges_stmt()
            .options(selectinload(Relationship.citation).options(*CITATION_LOAD))
            .order_by(Relationship.created_at)
            .limit(limit)
        ).all()
        node_ids = {e.from_node_id for e in edges} | {e.to_node_id for e in edges}
        nodes = self._nodes(node_ids)
        return NetworkRead(nodes=nodes, edges=[mappers.to_relationship(e) for e in edges])

    def list_relationships(
        self, *, node_id: uuid.UUID | None, limit: int, offset: int
    ) -> Page[RelationshipRead]:
        stmt = self._public_edges_stmt().options(
            selectinload(Relationship.citation).options(*CITATION_LOAD)
        )
        if node_id is not None:
            stmt = stmt.where(
                or_(Relationship.from_node_id == node_id, Relationship.to_node_id == node_id)
            )
        stmt = stmt.order_by(Relationship.created_at)
        rows, total = self._paginate(stmt, limit, offset)
        return Page(
            items=[mappers.to_relationship(e) for e in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    def _nodes(self, node_ids: set[uuid.UUID]) -> list[GraphNodeRead]:
        if not node_ids:
            return []
        nodes = self.session.scalars(
            select(GraphNode).where(GraphNode.id.in_(list(node_ids))).order_by(GraphNode.label)
        ).all()
        result: list[GraphNodeRead] = []
        for node in nodes:
            ref, protected = self._node_ref(node)
            result.append(mappers.to_graph_node(node, ref, protected))
        return result

    def _node_ref(self, node: GraphNode) -> tuple[str, bool]:
        kind = node.entity_kind
        entity_id = node.entity_id
        if kind == EntityKind.WITNESS:
            witness = self.session.get(Witness, entity_id)
            protected = witness is None or witness.is_protected
            # A protected witness node carries only its code, whatever the label says.
            return (witness.code if witness else node.label), protected
        model = _NODE_MODEL[kind]
        entity = self.session.get(model, entity_id)
        if entity is None:
            return node.label, False
        return str(getattr(entity, _NODE_REF_ATTR[kind])), False

    # ------------------------------------------------------------- search --
    def search(self, q: str, *, per_category: int = 10) -> SearchRead:
        """Minimal identifier/title search. Real search is Phase 8."""
        hits: list[SearchHit] = []
        if not q.strip():
            return SearchRead(query=q, hits=hits)
        for document in self.session.scalars(
            select(Document)
            .where(
                Document.case_id == self.case.id,
                public_visibility(Document.visibility),
                _ilike_any(q, Document.title, Document.official_ref, Document.filing_number),
            )
            .order_by(Document.official_ref)
            .limit(per_category)
        ):
            hits.append(
                SearchHit(
                    category="documents",
                    ref=document.official_ref,
                    title=document.title,
                    context=document.document_type,
                )
            )
        for person in self.session.scalars(
            select(Person)
            .where(Person.case_id == self.case.id, _ilike_any(q, Person.display_name, Person.slug))
            .order_by(Person.display_name)
            .limit(per_category)
        ):
            hits.append(
                SearchHit(
                    category="people",
                    ref=person.slug,
                    title=person.display_name,
                    context=person.public_role,
                )
            )
        for witness in self.session.scalars(
            select(Witness)
            .where(Witness.case_id == self.case.id, Witness.code.ilike(f"%{q}%"))
            .order_by(Witness.code)
            .limit(per_category)
        ):
            hits.append(
                SearchHit(
                    category="witnesses",
                    ref=witness.code,
                    title=witness.code,
                    context=None,
                    protected=witness.is_protected,
                )
            )
        for exhibit in self.session.scalars(
            select(Exhibit)
            .where(
                Exhibit.case_id == self.case.id,
                public_visibility(Exhibit.visibility),
                _ilike_any(q, Exhibit.official_exhibit_id, Exhibit.title),
            )
            .order_by(Exhibit.official_exhibit_id)
            .limit(per_category)
        ):
            hits.append(
                SearchHit(
                    category="exhibits",
                    ref=exhibit.official_exhibit_id,
                    title=exhibit.title,
                    context=exhibit.official_exhibit_id,
                )
            )
        for incident in self.session.scalars(
            select(Incident)
            .where(Incident.case_id == self.case.id, _ilike_any(q, Incident.title, Incident.slug))
            .order_by(Incident.slug)
            .limit(per_category)
        ):
            hits.append(
                SearchHit(
                    category="incidents",
                    ref=incident.slug,
                    title=incident.title,
                    context=incident.summary,
                )
            )
        for finding in self.session.scalars(
            self._findings_stmt()
            .where(_ilike_any(q, Finding.finding_key, Finding.text))
            .order_by(Finding.finding_key)
            .limit(per_category)
        ):
            hits.append(
                SearchHit(
                    category="findings",
                    ref=finding.finding_key,
                    title=finding.finding_key,
                    context=finding.text,
                )
            )
        for location in self.session.scalars(
            select(Location)
            .where(Location.case_id == self.case.id, _ilike_any(q, Location.name, Location.slug))
            .order_by(Location.name)
            .limit(per_category)
        ):
            hits.append(
                SearchHit(
                    category="locations",
                    ref=location.slug,
                    title=location.name,
                    context=location.kind,
                )
            )
        return SearchRead(query=q, hits=hits)


# ---------------------------------------------------------------- tables --
_PUBLIC = frozenset({"public", "public_redacted"})

_NODE_FK: dict[EntityKind, str] = {
    EntityKind.PERSON: "person_id",
    EntityKind.WITNESS: "witness_id",
    EntityKind.ORGANIZATION: "organization_id",
    EntityKind.LOCATION: "location_id",
    EntityKind.DOCUMENT: "document_id",
    EntityKind.EXHIBIT: "exhibit_id",
    EntityKind.INCIDENT: "incident_id",
    EntityKind.EVENT: "event_id",
    EntityKind.CLAIM: "claim_id",
    EntityKind.FINDING: "finding_id",
    EntityKind.ARGUMENT: "argument_id",
    EntityKind.HEARING: "hearing_id",
}
_CITATION_FK: dict[EntityKind, str] = {
    EntityKind.DOCUMENT: "target_document_id",
    EntityKind.EXHIBIT: "target_exhibit_id",
    EntityKind.WITNESS: "target_witness_id",
    EntityKind.FINDING: "target_finding_id",
}
_NODE_MODEL: dict[EntityKind, type[Any]] = {
    EntityKind.PERSON: Person,
    EntityKind.WITNESS: Witness,
    EntityKind.ORGANIZATION: Organization,
    EntityKind.LOCATION: Location,
    EntityKind.DOCUMENT: Document,
    EntityKind.EXHIBIT: Exhibit,
    EntityKind.INCIDENT: Incident,
    EntityKind.EVENT: Event,
    EntityKind.CLAIM: Claim,
    EntityKind.FINDING: Finding,
    EntityKind.ARGUMENT: Argument,
    EntityKind.HEARING: Hearing,
}
_NODE_REF_ATTR: dict[EntityKind, str] = {
    EntityKind.PERSON: "slug",
    EntityKind.WITNESS: "code",
    EntityKind.ORGANIZATION: "slug",
    EntityKind.LOCATION: "slug",
    EntityKind.DOCUMENT: "official_ref",
    EntityKind.EXHIBIT: "official_exhibit_id",
    EntityKind.INCIDENT: "slug",
    EntityKind.EVENT: "id",
    EntityKind.CLAIM: "claim_key",
    EntityKind.FINDING: "finding_key",
    EntityKind.ARGUMENT: "argument_key",
    EntityKind.HEARING: "hearing_date",
}


def _identifier_target(row: RecordIdentifier) -> uuid.UUID:
    for column in (
        row.document_id,
        row.document_version_id,
        row.exhibit_id,
        row.witness_id,
        row.transcript_id,
        row.finding_id,
    ):
        if column is not None:
            return column
    raise AssertionError("record_identifiers CHECK guarantees exactly one target")


def _ilike_any(q: str, *columns: Any) -> Any:
    pattern = f"%{q.strip()}%"
    return or_(*[c.ilike(pattern) for c in columns])


# ------------------------------------------------------------ dependency --
def get_repository(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RecordRepository:
    case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
    if case is None:
        raise CaseNotConfiguredError(settings.case_id)
    return RecordRepository(session, case)
