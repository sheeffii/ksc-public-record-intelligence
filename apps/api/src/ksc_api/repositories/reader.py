"""Phase 20B source-native Reader reads.

Everything is scoped to one exact public document version and, for research
context, to one PDF page. Nothing here loads a whole document's anchors, the
graph or cross-version coordinates. Transcript text is served verbatim; closed
or private-session segments carry no text.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

from ksc_api.models import (
    Case,
    Citation,
    DocumentPage,
    DocumentVersion,
    EntityOccurrence,
    Exhibit,
    Finding,
    Hearing,
    Organization,
    Person,
    Relationship,
    ResolutionState,
    SourceAnchor,
    SourcePrecision,
    SourceRegion,
    SourceSpan,
    Transcript,
    TranscriptPageContext,
    TranscriptSegment,
    VerificationState,
    Witness,
    WitnessIdentityStatus,
    version_language,
)
from ksc_api.repositories import mappers
from ksc_api.repositories.filters import not_rejected, public_visibility
from ksc_api.schemas.records import (
    GraphNodeRead,
    LocalSearchHitRead,
    LocalSearchRead,
    OverlayState,
    PageContextRead,
    PageOverlayRead,
    ProvenanceRead,
    ReaderAnchorRead,
    ReaderSegmentPage,
    ReaderSegmentRead,
    SourceRegionRead,
    TranscriptExaminationRead,
    TranscriptOutlineRead,
    TranscriptPageContextRead,
    TranscriptSpeakerRead,
    TranscriptSubjectRead,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

MAX_OVERLAYS_PER_KIND = 200
MAX_SEGMENT_PAGE = 200
MAX_LOCAL_SEARCH = 100
SEGMENT_OBJECT = "transcript_segment"
_RESEARCH_OBJECTS = ("entity_occurrence", "citation", "relationship", "finding")
_EXCERPT_WIDTH = 240


def _like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _verbatim_excerpt(text: str, query: str) -> str:
    """A window of the stored text around the first match; never normalized."""
    index = text.casefold().find(query.casefold())
    if len(text) <= _EXCERPT_WIDTH or index < 0:
        return text if len(text) <= _EXCERPT_WIDTH else text[:_EXCERPT_WIDTH] + "…"
    start = max(0, index - _EXCERPT_WIDTH // 3)
    end = min(len(text), start + _EXCERPT_WIDTH)
    return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")


def _verification_overlay(state: VerificationState) -> OverlayState:
    if state is VerificationState.HUMAN_VERIFIED:
        return "VERIFIED"
    if state in (VerificationState.AI_FLAGGED, VerificationState.NEEDS_MORE_EVIDENCE):
        return "REVIEW_REQUIRED"
    if state is VerificationState.UNRESOLVED:
        return "UNRESOLVED"
    return "UNKNOWN"


def _citation_overlay(state: ResolutionState) -> OverlayState:
    if state is ResolutionState.RESOLVED:
        return "VERIFIED"
    if state is ResolutionState.AMBIGUOUS:
        return "AMBIGUOUS"
    return "UNRESOLVED"


def _page_context(row: TranscriptPageContext) -> TranscriptPageContextRead:
    return TranscriptPageContextRead(
        pdf_page_index=row.pdf_page_index,
        page_number=row.page_number,
        header_text=row.header_text,
        subject=row.subject,
        subject_is_code=row.subject_is_code,
        session_state=row.session_state,
        examination=row.examination,
        rule=f"{row.rule_id}/{row.rule_version}",
    )


class ReaderReadsMixin:
    """Mixed into `RecordRepository`; relies on its session, case and helpers."""

    session: Session
    case: Case

    if TYPE_CHECKING:

        def _public_version(self, version_ref: str) -> DocumentVersion | None: ...
        def _nodes(self, node_ids: set[uuid.UUID]) -> list[GraphNodeRead]: ...
        def _typed_edges_stmt(self) -> tuple[Any, Any, Any]: ...
        def _edge_provenance(
            self, edges: Sequence[Relationship]
        ) -> dict[uuid.UUID, ProvenanceRead]: ...

    # ------------------------------------------------------------ helpers --
    def _version_transcript(self, version: DocumentVersion) -> Transcript | None:
        return self.session.scalar(
            select(Transcript)
            .options(selectinload(Transcript.hearing))
            .join(Hearing, Hearing.id == Transcript.hearing_id)
            .where(
                Transcript.document_version_id == version.id,
                Hearing.case_id == self.case.id,
                public_visibility(Transcript.visibility),
                public_visibility(Hearing.visibility),
            )
        )

    def _regions(self, span_ids: Iterable[uuid.UUID]) -> dict[uuid.UUID, list[SourceRegionRead]]:
        ids = list(set(span_ids))
        regions: dict[uuid.UUID, list[SourceRegionRead]] = defaultdict(list)
        if not ids:
            return regions
        for region in self.session.scalars(
            select(SourceRegion)
            .where(SourceRegion.source_span_id.in_(ids))
            .order_by(SourceRegion.source_span_id, SourceRegion.sequence)
        ):
            regions[region.source_span_id].append(SourceRegionRead.model_validate(region))
        return regions

    # -------------------------------------------------------- transcripts --
    def transcript_outline(self, version_ref: str) -> TranscriptOutlineRead | None:
        version = self._public_version(version_ref)
        if version is None:
            return None
        transcript = self._version_transcript(version)
        if transcript is None:
            return None
        segment_filter = TranscriptSegment.transcript_id == transcript.id
        segment_count, closed = self.session.execute(
            select(
                func.count(TranscriptSegment.id),
                func.count(TranscriptSegment.id).filter(TranscriptSegment.closed_session),
            ).where(segment_filter)
        ).one()
        precision = {
            str(level.value): int(count)
            for level, count in self.session.execute(
                select(SourceSpan.precision, func.count())
                .join(SourceAnchor, SourceAnchor.source_span_id == SourceSpan.id)
                .join(TranscriptSegment, TranscriptSegment.id == SourceAnchor.object_id)
                .where(SourceAnchor.object_type == SEGMENT_OBJECT, segment_filter)
                .group_by(SourceSpan.precision)
            ).all()
        }
        speakers = [
            TranscriptSpeakerRead(label=label, segments=int(count))
            for label, count in self.session.execute(
                select(TranscriptSegment.speaker, func.count())
                .where(segment_filter, TranscriptSegment.speaker.is_not(None))
                .group_by(TranscriptSegment.speaker)
                .order_by(func.count().desc(), TranscriptSegment.speaker)
                .limit(MAX_SEGMENT_PAGE)
            ).all()
        ]
        contexts = list(
            self.session.scalars(
                select(TranscriptPageContext)
                .where(TranscriptPageContext.document_version_id == version.id)
                .order_by(TranscriptPageContext.pdf_page_index)
            ).all()
        )
        subjects: dict[str, TranscriptSubjectRead] = {}
        examinations: dict[tuple[str, str], TranscriptExaminationRead] = {}
        for row in contexts:
            subject = subjects.get(row.subject)
            if subject is None:
                subjects[row.subject] = TranscriptSubjectRead(
                    subject=row.subject,
                    subject_is_code=row.subject_is_code,
                    pages=1,
                    first_pdf_page_index=row.pdf_page_index,
                    first_page_number=row.page_number,
                )
            else:
                subject.pages += 1
            if row.examination:
                key = (row.subject, row.examination)
                exam = examinations.get(key)
                if exam is None:
                    examinations[key] = TranscriptExaminationRead(
                        examination=row.examination,
                        subject=row.subject,
                        subject_is_code=row.subject_is_code,
                        pages=1,
                        first_pdf_page_index=row.pdf_page_index,
                        first_page_number=row.page_number,
                    )
                else:
                    exam.pages += 1
        hearing = transcript.hearing
        return TranscriptOutlineRead(
            official_version_ref=version.official_version_ref,
            document_ref=transcript.official_ref or version.official_version_ref,
            language=version_language(version.official_version_ref, transcript.language),
            hearing_date=hearing.hearing_date,
            session_label=hearing.session_label,
            hearing_type=hearing.hearing_type,
            page_from=transcript.page_from,
            page_to=transcript.page_to,
            segment_count=int(segment_count),
            closed_session_segments=int(closed),
            precision=precision,
            speakers=speakers,
            subjects=list(subjects.values()),
            examinations=list(examinations.values()),
            pages=[_page_context(row) for row in contexts],
        )

    def transcript_segments(
        self,
        version_ref: str,
        *,
        limit: int,
        offset: int,
        pdf_page_index: int | None = None,
        page: int | None = None,
        line: int | None = None,
        segment_id: uuid.UUID | None = None,
        speaker: str | None = None,
        subject: str | None = None,
        examination: str | None = None,
        q: str | None = None,
    ) -> ReaderSegmentPage | None:
        version = self._public_version(version_ref)
        if version is None:
            return None
        transcript = self._version_transcript(version)
        if transcript is None:
            return None
        limit = max(1, min(limit, MAX_SEGMENT_PAGE))
        stmt = (
            select(TranscriptSegment, SourceAnchor, SourceSpan, Witness.code)
            .outerjoin(
                SourceAnchor,
                and_(
                    SourceAnchor.object_type == SEGMENT_OBJECT,
                    SourceAnchor.object_id == TranscriptSegment.id,
                ),
            )
            .outerjoin(SourceSpan, SourceSpan.id == SourceAnchor.source_span_id)
            .outerjoin(Witness, Witness.id == TranscriptSegment.witness_id)
            .where(TranscriptSegment.transcript_id == transcript.id)
        )
        if segment_id is not None:
            stmt = stmt.where(TranscriptSegment.id == segment_id)
        if pdf_page_index is not None:
            stmt = stmt.where(TranscriptSegment.pdf_page_index == pdf_page_index)
        if page is not None:
            stmt = stmt.where(TranscriptSegment.page_number == page)
        if line is not None:
            stmt = stmt.where(
                TranscriptSegment.line_from <= line,
                func.coalesce(TranscriptSegment.line_to, TranscriptSegment.line_from) >= line,
            )
        if speaker:
            stmt = stmt.where(TranscriptSegment.speaker == speaker)
        header_pages = select(TranscriptPageContext.pdf_page_index).where(
            TranscriptPageContext.document_version_id == version.id
        )
        if subject:
            stmt = stmt.where(
                TranscriptSegment.pdf_page_index.in_(
                    header_pages.where(TranscriptPageContext.subject == subject)
                )
            )
        if examination:
            stmt = stmt.where(
                TranscriptSegment.pdf_page_index.in_(
                    header_pages.where(TranscriptPageContext.examination == examination)
                )
            )
        if q:
            stmt = stmt.where(
                ~TranscriptSegment.closed_session,
                TranscriptSegment.text.ilike(_like(q), escape="\\"),
            )
        total = int(
            self.session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
            or 0
        )
        rows = self.session.execute(
            stmt.order_by(TranscriptSegment.sequence).limit(limit).offset(offset)
        ).all()
        regions = self._regions(span.id for _, _, span, _ in rows if span is not None)
        items = [
            ReaderSegmentRead(
                id=segment.id,
                sequence=segment.sequence,
                pdf_page_index=segment.pdf_page_index,
                page_number=segment.page_number,
                line_from=segment.line_from,
                line_to=segment.line_to,
                speaker=segment.speaker,
                witness_code=code,
                closed_session=segment.closed_session,
                text=None if segment.closed_session else segment.text,
                anchor=ReaderAnchorRead(
                    id=anchor.id,
                    precision=span.precision,
                    failure_reason=span.failure_reason,
                    pdf_page_index=span.pdf_page_index,
                    line_from=span.line_from,
                    line_to=span.line_to,
                    regions=regions.get(span.id, []),
                )
                if anchor is not None and span is not None
                else None,
            )
            for segment, anchor, span, code in rows
        ]
        return ReaderSegmentPage(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            filtered=bool(speaker or subject or examination or q),
        )

    # ------------------------------------------------------- page context --
    def page_context(
        self, version_ref: str, pdf_page_index: int, *, limit: int = 100
    ) -> PageContextRead | None:
        version = self._public_version(version_ref)
        if version is None:
            return None
        page = self.session.scalar(
            select(DocumentPage).where(
                DocumentPage.document_version_id == version.id,
                DocumentPage.pdf_page_index == pdf_page_index,
            )
        )
        if page is None:
            return None
        limit = max(1, min(limit, MAX_OVERLAYS_PER_KIND))
        header = self.session.scalar(
            select(TranscriptPageContext).where(
                TranscriptPageContext.document_version_id == version.id,
                TranscriptPageContext.pdf_page_index == pdf_page_index,
            )
        )
        anchored = self.session.execute(
            select(SourceAnchor, SourceSpan)
            .join(SourceSpan, SourceSpan.id == SourceAnchor.source_span_id)
            .where(
                SourceSpan.document_version_id == version.id,
                SourceSpan.pdf_page_index == pdf_page_index,
                SourceAnchor.object_type.in_(_RESEARCH_OBJECTS),
            )
        ).all()
        by_type: dict[str, dict[uuid.UUID, tuple[SourceAnchor, SourceSpan]]] = defaultdict(dict)
        for anchor, span in anchored:
            by_type[anchor.object_type][anchor.object_id] = (anchor, span)
        regions = self._regions(span.id for _, span in anchored)
        overlays: list[PageOverlayRead] = []

        def overlay(anchor: SourceAnchor, span: SourceSpan, **fields: Any) -> PageOverlayRead:
            return PageOverlayRead(
                anchor_id=anchor.id,
                object_id=anchor.object_id,
                precision=span.precision,
                failure_reason=span.failure_reason,
                line_from=span.line_from,
                line_to=span.line_to,
                transcript_segment_id=span.transcript_segment_id,
                exact_text=span.exact_text,
                regions=regions.get(span.id, []),
                **fields,
            )

        overlays += self._occurrence_overlays(by_type["entity_occurrence"], overlay)
        overlays += self._citation_overlays(by_type["citation"], overlay)
        overlays += self._relationship_overlays(by_type["relationship"], overlay)
        overlays += self._finding_overlays(by_type["finding"], overlay)

        totals: dict[str, int] = defaultdict(int)
        kept: list[PageOverlayRead] = []
        kept_per_kind: dict[str, int] = defaultdict(int)
        overlays.sort(
            key=lambda item: (
                item.line_from if item.line_from is not None else 1_000_000,
                item.regions[0].y if item.regions else 1_000_000.0,
                item.kind,
                item.label,
            )
        )
        for item in overlays:
            totals[item.kind] += 1
            if kept_per_kind[item.kind] < limit:
                kept_per_kind[item.kind] += 1
                kept.append(item)
        return PageContextRead(
            official_version_ref=version.official_version_ref,
            pdf_page_index=page.pdf_page_index,
            page_number=page.page_number,
            geometry_state=page.geometry_state,
            page_width=float(page.width_points) if page.width_points else None,
            page_height=float(page.height_points) if page.height_points else None,
            page_rotation=page.rotation,
            transcript_header=_page_context(header) if header is not None else None,
            overlays=kept,
            totals=dict(totals),
            truncated=len(kept) < len(overlays),
        )

    def _occurrence_overlays(
        self, anchors: dict[uuid.UUID, tuple[SourceAnchor, SourceSpan]], overlay: Any
    ) -> list[PageOverlayRead]:
        if not anchors:
            return []
        occurrences = self.session.scalars(
            select(EntityOccurrence).where(
                EntityOccurrence.id.in_(list(anchors)),
                EntityOccurrence.rule_id.is_not(None),
                EntityOccurrence.mention_state.in_(["verified", "review_required"]),
            )
        ).all()

        def lookup(
            model: Any, ids: set[uuid.UUID | None], *columns: Any
        ) -> dict[uuid.UUID, tuple[Any, ...]]:
            wanted = [value for value in ids if value is not None]
            if not wanted:
                return {}
            stmt = select(model.id, *columns).where(model.id.in_(wanted))
            if model is Exhibit:
                stmt = stmt.where(public_visibility(Exhibit.visibility))
            return {row[0]: tuple(row[1:]) for row in self.session.execute(stmt).all()}

        persons = lookup(
            Person, {o.person_id for o in occurrences}, Person.display_name, Person.slug
        )
        witnesses = lookup(
            Witness, {o.witness_id for o in occurrences}, Witness.code, Witness.identity_status
        )
        organizations = lookup(
            Organization,
            {o.organization_id for o in occurrences},
            Organization.name,
            Organization.slug,
        )
        exhibits = lookup(
            Exhibit,
            {o.exhibit_id for o in occurrences},
            Exhibit.official_exhibit_id,
            Exhibit.status,
        )
        items: list[PageOverlayRead] = []
        for occurrence in occurrences:
            anchor, span = anchors[occurrence.id]
            state: OverlayState = (
                "VERIFIED" if occurrence.mention_state == "verified" else "REVIEW_REQUIRED"
            )
            rule = f"{occurrence.rule_id}/{occurrence.rule_version}"
            if occurrence.person_id and occurrence.person_id in persons:
                name, slug = persons[occurrence.person_id]
                items.append(
                    overlay(
                        anchor,
                        span,
                        kind="person",
                        label=name,
                        state=state,
                        rule=rule,
                        target_path=f"/people/{slug}",
                    )
                )
            elif occurrence.witness_id and occurrence.witness_id in witnesses:
                code, status = witnesses[occurrence.witness_id]
                items.append(
                    overlay(
                        anchor,
                        span,
                        kind="witness",
                        # Code only, public or not; identity is never expanded here.
                        label=code,
                        protected=status != WitnessIdentityStatus.PUBLIC,
                        state=state,
                        rule=rule,
                        target_path=f"/witnesses/{code}",
                    )
                )
            elif occurrence.organization_id and occurrence.organization_id in organizations:
                name, slug = organizations[occurrence.organization_id]
                items.append(
                    overlay(
                        anchor,
                        span,
                        kind="organization",
                        label=name,
                        state=state,
                        rule=rule,
                        target_path=f"/organizations/{slug}",
                    )
                )
            elif occurrence.exhibit_id and occurrence.exhibit_id in exhibits:
                official_id, status = exhibits[occurrence.exhibit_id]
                items.append(
                    overlay(
                        anchor,
                        span,
                        kind="exhibit",
                        label=official_id,
                        state=state,
                        rule=rule,
                        exhibit_status=status or "unknown",
                        target_path=f"/exhibits/{official_id}",
                    )
                )
        return items

    def _citation_overlays(
        self, anchors: dict[uuid.UUID, tuple[SourceAnchor, SourceSpan]], overlay: Any
    ) -> list[PageOverlayRead]:
        if not anchors:
            return []
        from ksc_api.repositories.records import CITATION_LOAD

        citations = self.session.scalars(
            select(Citation)
            .options(*CITATION_LOAD)
            .where(
                Citation.id.in_(list(anchors)),
                Citation.case_id == self.case.id,
                not_rejected(Citation),
            )
        ).all()
        items: list[PageOverlayRead] = []
        for citation in citations:
            anchor, span = anchors[citation.id]
            read = mappers.to_citation(citation)
            resolved = citation.resolution_state is ResolutionState.RESOLVED
            items.append(
                overlay(
                    anchor,
                    span,
                    kind="citation",
                    label=citation.raw_text,
                    state=_citation_overlay(citation.resolution_state),
                    resolution_state=citation.resolution_state.value,
                    verification_state=citation.verification_state.value,
                    # Fail closed: only a resolved citation links to a target.
                    target_path=read.target_path if resolved else None,
                )
            )
        return items

    def _relationship_overlays(
        self, anchors: dict[uuid.UUID, tuple[SourceAnchor, SourceSpan]], overlay: Any
    ) -> list[PageOverlayRead]:
        if not anchors:
            return []
        stmt, _, _ = self._typed_edges_stmt()
        edges = list(
            self.session.scalars(stmt.where(Relationship.id.in_(list(anchors)))).unique().all()
        )
        provenance = self._edge_provenance(edges)
        nodes = {
            node.id: node
            for node in self._nodes(
                {edge.from_node_id for edge in edges} | {edge.to_node_id for edge in edges}
            )
        }
        items: list[PageOverlayRead] = []
        for edge in edges:
            if edge.id not in provenance:
                continue
            anchor, span = anchors[edge.id]
            from_node, to_node = nodes.get(edge.from_node_id), nodes.get(edge.to_node_id)
            items.append(
                overlay(
                    anchor,
                    span,
                    kind="relationship",
                    label=edge.relationship_type.value,
                    # Only edges whose evidence passes the public typed-edge rule
                    # (resolved citation / verified mention / header appearance).
                    state="VERIFIED",
                    verification_state=edge.verification_state.value,
                    relationship_type=edge.relationship_type,
                    evidence_count=edge.evidence_count,
                    # Graph node labels are already code-only for protected witnesses.
                    from_label=from_node.label if from_node else None,
                    to_label=to_node.label if to_node else None,
                    provenance=provenance[edge.id],
                    target_path=provenance[edge.id].target_path,
                )
            )
        return items

    def _finding_overlays(
        self, anchors: dict[uuid.UUID, tuple[SourceAnchor, SourceSpan]], overlay: Any
    ) -> list[PageOverlayRead]:
        if not anchors:
            return []
        findings = self.session.scalars(
            select(Finding).where(
                Finding.id.in_(list(anchors)),
                Finding.case_id == self.case.id,
                not_rejected(Finding),
            )
        ).all()
        return [
            overlay(
                *anchors[finding.id],
                kind="finding",
                label=finding.finding_key,
                state=_verification_overlay(finding.verification_state),
                verification_state=finding.verification_state.value,
                target_path=f"/findings/{finding.finding_key}",
            )
            for finding in findings
        ]

    # ------------------------------------------------------ local search --
    def local_search(self, version_ref: str, q: str, *, limit: int) -> LocalSearchRead | None:
        version = self._public_version(version_ref)
        if version is None:
            return None
        query = q.strip()
        limit = max(1, min(limit, MAX_LOCAL_SEARCH))
        if len(query) < 2:
            return LocalSearchRead(query=query, items=[], total=0, truncated=False)
        needle = query.casefold()
        transcript = self._version_transcript(version)
        items: list[LocalSearchHitRead] = []
        if transcript is not None:
            stmt = select(TranscriptSegment).where(
                TranscriptSegment.transcript_id == transcript.id,
                ~TranscriptSegment.closed_session,
                TranscriptSegment.text.ilike(_like(query), escape="\\"),
            )
            total = int(self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
            for segment in self.session.scalars(
                stmt.order_by(TranscriptSegment.sequence).limit(limit)
            ):
                items.append(
                    LocalSearchHitRead(
                        pdf_page_index=segment.pdf_page_index,
                        page_number=segment.page_number,
                        line_from=segment.line_from,
                        line_to=segment.line_to,
                        transcript_segment_id=segment.id,
                        speaker=segment.speaker,
                        excerpt=_verbatim_excerpt(segment.text, query),
                        occurrences=segment.text.casefold().count(needle),
                        precision=SourcePrecision.PAGE_AND_LINE
                        if segment.pdf_page_index is not None and segment.line_from is not None
                        else SourcePrecision.PAGE_ONLY
                        if segment.pdf_page_index is not None
                        else SourcePrecision.TEXT_ONLY,
                    )
                )
        else:
            pages = select(DocumentPage).where(
                DocumentPage.document_version_id == version.id,
                DocumentPage.text.ilike(_like(query), escape="\\"),
            )
            total = int(
                self.session.scalar(select(func.count()).select_from(pages.subquery())) or 0
            )
            for page in self.session.scalars(
                pages.order_by(DocumentPage.pdf_page_index).limit(limit)
            ):
                text = page.text or ""
                items.append(
                    LocalSearchHitRead(
                        pdf_page_index=page.pdf_page_index,
                        page_number=page.page_number,
                        line_from=None,
                        line_to=None,
                        transcript_segment_id=None,
                        speaker=None,
                        excerpt=_verbatim_excerpt(text, query),
                        occurrences=text.casefold().count(needle),
                        precision=SourcePrecision.PAGE_ONLY,
                    )
                )
        return LocalSearchRead(query=query, items=items, total=total, truncated=total > len(items))
