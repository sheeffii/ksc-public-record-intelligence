"""Phase 22A source-anchor and Evidence Path projection.

This projector only organises already-reviewed structured records. It does not
extract new facts, classify evidence, or acquire source material.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    AppealIssueSource,
    Argument,
    ArgumentResponse,
    Case,
    Citation,
    Document,
    DocumentPage,
    DocumentParagraph,
    EntityKind,
    Finding,
    FindingEvidenceLink,
    FindingLinkType,
    GraphNode,
    Incident,
    IncidentSource,
    PageTextGeometry,
    ProcessingRun,
    Relationship,
    RelationshipOrigin,
    RelationshipType,
    ResolutionState,
    SourceAnchor,
    SourcePrecision,
    SourceRegion,
    SourceSpan,
    TextExtractionMethod,
    VerificationState,
)
from ksc_ingestion.source_geometry import _matches

PROCESSOR = "phase22a-legal-matrix"
PROCESSOR_VERSION = "1"
_NAMESPACE = uuid.UUID("8ea79f25-5723-43c5-8e0a-c9e45cf387a2")


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NAMESPACE, "|".join(str(part) for part in parts))


@dataclass(frozen=True)
class LegalMatrixProjectionResult:
    run_id: uuid.UUID
    finding_links: int
    arguments: int
    issue_sources: int
    graph_nodes: int
    graph_relationships: int
    source_anchors: int
    precision: dict[str, int]


class Phase22ALegalMatrixProjector:
    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def run(self) -> LegalMatrixProjectionResult:
        started = datetime.now(UTC)
        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise RuntimeError(f"case {self.case_number} is not seeded")
            selected = int(
                session.scalar(
                    select(func.count(FindingEvidenceLink.id))
                    .join(Finding)
                    .where(Finding.case_id == case.id)
                )
                or 0
            )
            run = ProcessingRun(
                case_id=case.id,
                processor=PROCESSOR,
                processor_version=PROCESSOR_VERSION,
                status="running",
                selected_count=selected,
                processed_count=0,
                failed_count=0,
                started_at=started,
                detail={"scope": "existing verified structured records only"},
            )
            session.add(run)
            session.commit()
            run_id = run.id

        try:
            result = self._project(run_id)
        except Exception:
            with self.sessions() as session:
                failed_run = session.get(ProcessingRun, run_id)
                assert failed_run is not None
                failed_run.status = "failed"
                failed_run.failed_count = 1
                failed_run.finished_at = datetime.now(UTC)
                session.commit()
            raise

        with self.sessions() as session:
            completed_run = session.get(ProcessingRun, run_id)
            assert completed_run is not None
            completed_run.status = "completed"
            completed_run.processed_count = result.source_anchors
            completed_run.finished_at = datetime.now(UTC)
            completed_run.detail = {
                "finding_links": result.finding_links,
                "arguments": result.arguments,
                "issue_sources": result.issue_sources,
                "graph_nodes": result.graph_nodes,
                "graph_relationships": result.graph_relationships,
                "source_anchors": result.source_anchors,
                "precision": result.precision,
            }
            session.commit()
        return result

    def _project(self, run_id: uuid.UUID) -> LegalMatrixProjectionResult:
        precision: dict[str, int] = {}
        with self.sessions() as session, session.begin():
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            assert case is not None
            self._clear(session, case.id)

            findings = list(
                session.scalars(select(Finding).where(Finding.case_id == case.id)).all()
            )
            finding_ids = [finding.id for finding in findings]
            links = (
                list(
                    session.scalars(
                        select(FindingEvidenceLink)
                        .where(FindingEvidenceLink.finding_id.in_(finding_ids))
                        .order_by(FindingEvidenceLink.created_at)
                    ).all()
                )
                if finding_ids
                else []
            )
            arguments = list(
                session.scalars(
                    select(Argument)
                    .where(Argument.case_id == case.id)
                    .order_by(Argument.argument_key)
                ).all()
            )
            issue_sources = list(
                session.scalars(
                    select(AppealIssueSource)
                    .join(AppealIssueSource.issue)
                    .where(AppealIssueSource.issue.has(case_id=case.id))
                    .order_by(AppealIssueSource.issue_id, AppealIssueSource.sequence)
                ).all()
            )

            argument_anchors: dict[uuid.UUID, SourceAnchor] = {}
            for argument in arguments:
                if argument.document_version_id is None:
                    continue
                paragraph = self._paragraph(
                    session, argument.document_version_id, argument.para_from
                )
                anchor = self._new_anchor(
                    session,
                    run_id=run_id,
                    object_type="argument",
                    object_id=argument.id,
                    role="argument_passage",
                    version_id=argument.document_version_id,
                    pdf_page_index=paragraph.pdf_page_index_from if paragraph else None,
                    page_number=paragraph.page_from if paragraph else None,
                    paragraph_number=argument.para_from,
                    exact_text=argument.text,
                    verification=argument.verification_state.value,
                    precision_counts=precision,
                )
                argument.source_anchor_id = anchor.id
                argument_anchors[argument.id] = anchor

            link_anchors: dict[uuid.UUID, SourceAnchor] = {}
            for link in links:
                citation_anchor = session.scalar(
                    select(SourceAnchor).where(
                        SourceAnchor.object_type == "citation",
                        SourceAnchor.object_id == link.citation_id,
                        SourceAnchor.anchor_role == "citation_source",
                    )
                )
                if citation_anchor is not None:
                    anchor = self._share_anchor(
                        session,
                        source=citation_anchor,
                        object_type="finding_evidence_link",
                        object_id=link.id,
                        role="relationship_basis",
                        verification=link.verification_state.value,
                        precision_counts=precision,
                    )
                else:
                    citation = session.get(Citation, link.citation_id)
                    if citation is None or citation.source_document_version_id is None:
                        continue
                    anchor = self._new_anchor(
                        session,
                        run_id=run_id,
                        object_type="finding_evidence_link",
                        object_id=link.id,
                        role="relationship_basis",
                        version_id=citation.source_document_version_id,
                        pdf_page_index=citation.source_pdf_page_index,
                        page_number=citation.source_page,
                        paragraph_number=citation.source_para,
                        exact_text=citation.raw_text,
                        verification=link.verification_state.value,
                        precision_counts=precision,
                    )
                link.source_anchor_id = anchor.id
                link_anchors[link.id] = anchor

            finding_anchors = {
                anchor.object_id: anchor
                for anchor in session.scalars(
                    select(SourceAnchor).where(
                        SourceAnchor.object_type == "finding",
                        SourceAnchor.object_id.in_(finding_ids),
                    )
                ).all()
            }
            for finding in findings:
                if finding.id in finding_anchors or finding.judgment_version_id is None:
                    continue
                paragraph = self._paragraph(session, finding.judgment_version_id, finding.para_from)
                finding_anchors[finding.id] = self._new_anchor(
                    session,
                    run_id=run_id,
                    object_type="finding",
                    object_id=finding.id,
                    role="finding_passage",
                    version_id=finding.judgment_version_id,
                    pdf_page_index=paragraph.pdf_page_index_from if paragraph else None,
                    page_number=paragraph.page_from if paragraph else None,
                    paragraph_number=finding.para_from,
                    exact_text=finding.text,
                    verification=finding.verification_state.value,
                    precision_counts=precision,
                )
            for source in issue_sources:
                basis = (
                    argument_anchors.get(source.argument_id)
                    if source.argument_id is not None
                    else link_anchors.get(source.finding_evidence_link_id)
                    if source.finding_evidence_link_id is not None
                    else None
                )
                if basis is None and source.role == "court_reasoning":
                    basis = finding_anchors.get(source.issue.finding_id)
                if basis is not None:
                    anchor = self._share_anchor(
                        session,
                        source=basis,
                        object_type="appeal_issue_source",
                        object_id=source.id,
                        role="issue_source",
                        verification=source.verification_state.value,
                        precision_counts=precision,
                    )
                else:
                    citation = session.get(Citation, source.citation_id)
                    if citation is None or citation.target_document_version_id is None:
                        continue
                    anchor = self._new_anchor(
                        session,
                        run_id=run_id,
                        object_type="appeal_issue_source",
                        object_id=source.id,
                        role="issue_source",
                        version_id=citation.target_document_version_id,
                        pdf_page_index=citation.target_pdf_page_index,
                        page_number=citation.target_page,
                        paragraph_number=citation.target_para_from,
                        exact_text=source.excerpt,
                        verification=source.verification_state.value,
                        precision_counts=precision,
                    )
                source.source_anchor_id = anchor.id

            # Reviewed incidents quote their operative source paragraphs verbatim.
            incident_sources = list(
                session.scalars(
                    select(IncidentSource)
                    .join(Incident)
                    .where(Incident.case_id == case.id, IncidentSource.role == "operative")
                    .order_by(IncidentSource.incident_id, IncidentSource.sequence)
                ).all()
            )
            for incident_source in incident_sources:
                paragraph = self._paragraph(
                    session, incident_source.document_version_id, incident_source.paragraph_number
                )
                incident_anchor = self._new_anchor(
                    session,
                    run_id=run_id,
                    object_type="incident_source",
                    object_id=incident_source.id,
                    role="incident_source",
                    version_id=incident_source.document_version_id,
                    pdf_page_index=paragraph.pdf_page_index_from if paragraph else None,
                    page_number=paragraph.page_from if paragraph else None,
                    paragraph_number=incident_source.paragraph_number,
                    exact_text=incident_source.excerpt,
                    verification=incident_source.verification_state.value,
                    precision_counts=precision,
                )
                session.flush()  # no ORM relationship orders the anchor insert first
                incident_source.source_anchor_id = incident_anchor.id

            node_count, relationship_count = self._project_graph(
                session, case.id, findings, arguments, links, link_anchors, precision
            )
            return LegalMatrixProjectionResult(
                run_id=run_id,
                finding_links=len(links),
                arguments=len(arguments),
                issue_sources=len(issue_sources),
                graph_nodes=node_count,
                graph_relationships=relationship_count,
                source_anchors=sum(precision.values()),
                precision=precision,
            )

    @staticmethod
    def _clear(session: Session, case_id: uuid.UUID) -> None:
        link_ids = select(FindingEvidenceLink.id).join(Finding).where(Finding.case_id == case_id)
        argument_ids = select(Argument.id).where(Argument.case_id == case_id)
        issue_source_ids = (
            select(AppealIssueSource.id)
            .join(AppealIssueSource.issue)
            .where(AppealIssueSource.issue.has(case_id=case_id))
        )
        # Edges this projection owns: by note, and by their deterministic ids, so
        # an edge whose note a later migration rewrote (0019) is still replaced.
        owned_ids = [
            *(_id("relationship", link_id) for link_id in session.scalars(link_ids)),
            *(
                _id("argument-response", response_id)
                for response_id in session.scalars(
                    select(ArgumentResponse.id).where(
                        ArgumentResponse.argument_id.in_(argument_ids)
                    )
                )
            ),
        ]
        owned = or_(
            Relationship.note.like("Phase 22A matrix projection:%"),
            Relationship.id.in_(owned_ids),
        )
        relationship_ids = select(Relationship.id).where(Relationship.case_id == case_id, owned)
        incident_source_ids = (
            select(IncidentSource.id).join(Incident).where(Incident.case_id == case_id)
        )
        legal_anchors = list(
            session.scalars(
                select(SourceAnchor).where(
                    or_(
                        (
                            (SourceAnchor.object_type == "finding_evidence_link")
                            & SourceAnchor.object_id.in_(link_ids)
                        ),
                        (
                            (SourceAnchor.object_type == "argument")
                            & SourceAnchor.object_id.in_(argument_ids)
                        ),
                        (
                            (SourceAnchor.object_type == "appeal_issue_source")
                            & SourceAnchor.object_id.in_(issue_source_ids)
                        ),
                        (
                            (SourceAnchor.object_type == "relationship")
                            & SourceAnchor.object_id.in_(relationship_ids)
                        ),
                        (
                            (SourceAnchor.object_type == "incident_source")
                            & SourceAnchor.object_id.in_(incident_source_ids)
                        ),
                    )
                )
            ).all()
        )
        span_ids = {anchor.source_span_id for anchor in legal_anchors}
        anchor_ids = [anchor.id for anchor in legal_anchors]
        if anchor_ids:
            session.execute(delete(SourceAnchor).where(SourceAnchor.id.in_(anchor_ids)))
        session.flush()
        for span_id in span_ids:
            still_used = session.scalar(
                select(SourceAnchor.id).where(SourceAnchor.source_span_id == span_id).limit(1)
            )
            if still_used is None:
                session.execute(delete(SourceSpan).where(SourceSpan.id == span_id))
        session.execute(delete(Relationship).where(Relationship.case_id == case_id, owned))
        session.flush()

    @staticmethod
    def _paragraph(
        session: Session, version_id: uuid.UUID, paragraph_number: int | None
    ) -> DocumentParagraph | None:
        if paragraph_number is None:
            return None
        return session.scalar(
            select(DocumentParagraph).where(
                DocumentParagraph.document_version_id == version_id,
                DocumentParagraph.paragraph_number == paragraph_number,
            )
        )

    def _new_anchor(
        self,
        session: Session,
        *,
        run_id: uuid.UUID,
        object_type: str,
        object_id: uuid.UUID,
        role: str,
        version_id: uuid.UUID,
        pdf_page_index: int | None,
        page_number: int | None,
        paragraph_number: int | None,
        exact_text: str | None,
        verification: str,
        precision_counts: dict[str, int],
    ) -> SourceAnchor:
        page = (
            session.scalar(
                select(DocumentPage).where(
                    DocumentPage.document_version_id == version_id,
                    DocumentPage.pdf_page_index == pdf_page_index,
                )
            )
            if pdf_page_index is not None
            else None
        )
        words = (
            list(
                session.scalars(
                    select(PageTextGeometry)
                    .where(
                        PageTextGeometry.document_version_id == version_id,
                        PageTextGeometry.pdf_page_index == pdf_page_index,
                    )
                    .order_by(PageTextGeometry.sequence)
                ).all()
            )
            if page is not None
            else []
        )
        matches = _matches(words, exact_text or "") if exact_text else []
        selected = matches[0] if len(matches) == 1 else None
        if selected is not None:
            precision = SourcePrecision.EXACT_GEOMETRY
            failure = None
        elif pdf_page_index is not None:
            precision = SourcePrecision.PAGE_ONLY
            failure = "geometry_text_not_unique" if len(matches) > 1 else "geometry_text_not_found"
        elif exact_text:
            precision = SourcePrecision.TEXT_ONLY
            failure = "pdf_page_unavailable"
        else:
            precision = SourcePrecision.UNAVAILABLE
            failure = "source_coordinate_unavailable"
        span = SourceSpan(
            id=_id("span", object_type, object_id, role),
            document_version_id=version_id,
            pdf_page_index=pdf_page_index,
            page_number=page_number,
            paragraph_number=paragraph_number,
            exact_text=exact_text,
            text_basis="document_page_text" if exact_text else None,
            extraction_method=(
                TextExtractionMethod.NATIVE_TEXT
                if precision is not SourcePrecision.UNAVAILABLE
                else TextExtractionMethod.NONE
            ),
            extractor_version=PROCESSOR_VERSION,
            precision=precision,
            state="verified" if selected is not None else "unavailable",
            failure_reason=failure,
            processing_run_id=run_id,
        )
        session.add(span)
        for sequence, word in enumerate(selected or []):
            span.regions.append(
                SourceRegion(
                    id=_id(span.id, "region", sequence),
                    sequence=sequence,
                    x=word.x,
                    y=word.y,
                    width=word.width,
                    height=word.height,
                )
            )
        anchor = SourceAnchor(
            id=_id("anchor", object_type, object_id, role),
            source_span_id=span.id,
            object_type=object_type,
            object_id=object_id,
            anchor_role=role,
            source_verification_state=verification,
        )
        session.add(anchor)
        precision_counts[precision.value] = precision_counts.get(precision.value, 0) + 1
        return anchor

    @staticmethod
    def _share_anchor(
        session: Session,
        *,
        source: SourceAnchor,
        object_type: str,
        object_id: uuid.UUID,
        role: str,
        verification: str,
        precision_counts: dict[str, int],
    ) -> SourceAnchor:
        anchor = SourceAnchor(
            id=_id("anchor", object_type, object_id, role),
            source_span_id=source.source_span_id,
            object_type=object_type,
            object_id=object_id,
            anchor_role=role,
            source_verification_state=verification,
        )
        session.add(anchor)
        precision_counts[source.span.precision.value] = (
            precision_counts.get(source.span.precision.value, 0) + 1
        )
        return anchor

    def _project_graph(
        self,
        session: Session,
        case_id: uuid.UUID,
        findings: list[Finding],
        arguments: list[Argument],
        links: list[FindingEvidenceLink],
        link_anchors: dict[uuid.UUID, SourceAnchor],
        precision_counts: dict[str, int],
    ) -> tuple[int, int]:
        created_nodes = 0
        created_relationships = 0

        def entity_node(kind: EntityKind, entity_id: uuid.UUID, label: str) -> GraphNode:
            nonlocal created_nodes
            column = {
                EntityKind.FINDING: GraphNode.finding_id,
                EntityKind.ARGUMENT: GraphNode.argument_id,
                EntityKind.DOCUMENT: GraphNode.document_id,
            }[kind]
            node = session.scalar(select(GraphNode).where(column == entity_id))
            if node is None:
                node = GraphNode(
                    id=_id("node", kind.value, entity_id),
                    case_id=case_id,
                    entity_kind=kind,
                    label=label,
                    **{f"{kind.value}_id": entity_id},
                )
                session.add(node)
                session.flush()
                created_nodes += 1
            return node

        finding_nodes = {
            finding.id: entity_node(EntityKind.FINDING, finding.id, finding.finding_key)
            for finding in findings
        }
        argument_nodes = {
            argument.id: entity_node(EntityKind.ARGUMENT, argument.id, argument.argument_key)
            for argument in arguments
        }
        for link in links:
            if link.link_type not in {
                FindingLinkType.COURT_RELIES_ON,
                FindingLinkType.COURT_CITES,
            }:
                continue
            citation = session.get(Citation, link.citation_id)
            if (
                citation is None
                or citation.resolution_state is not ResolutionState.RESOLVED
                or citation.target_document_id is None
            ):
                continue
            document = session.get(Document, citation.target_document_id)
            if document is None:
                continue
            target = entity_node(EntityKind.DOCUMENT, document.id, document.official_ref)
            relationship = Relationship(
                id=_id("relationship", link.id),
                case_id=case_id,
                from_node_id=finding_nodes[link.finding_id].id,
                to_node_id=target.id,
                relationship_type=(
                    RelationshipType.RELIES_ON
                    if link.link_type is FindingLinkType.COURT_RELIES_ON
                    else RelationshipType.CITED_IN
                ),
                citation_id=link.citation_id,
                evidence_count=1,
                note=f"Phase 22A matrix projection: {link.link_type.value}",
                source_category=link.source_category,
                extraction_origin=RelationshipOrigin.SOURCE_DOCUMENTED,
                verification_state=link.verification_state,
                verified_by=link.verified_by,
                verified_at=link.verified_at,
            )
            session.add(relationship)
            session.flush()
            basis = link_anchors.get(link.id)
            if basis is not None:
                self._share_anchor(
                    session,
                    source=basis,
                    object_type="relationship",
                    object_id=relationship.id,
                    role="relationship_evidence",
                    verification=relationship.verification_state.value,
                    precision_counts=precision_counts,
                )
            created_relationships += 1

        responses = session.scalars(
            select(ArgumentResponse).where(
                ArgumentResponse.argument_id.in_(argument_nodes),
                ArgumentResponse.response_argument_id.in_(argument_nodes),
                ArgumentResponse.verification_state == VerificationState.HUMAN_VERIFIED,
                ArgumentResponse.citation_id.is_not(None),
            )
        ).all()
        for response in responses:
            relationship = Relationship(
                id=_id("argument-response", response.id),
                case_id=case_id,
                from_node_id=argument_nodes[response.response_argument_id].id,
                to_node_id=argument_nodes[response.argument_id].id,
                relationship_type=RelationshipType.RESPONDS_TO,
                citation_id=response.citation_id,
                evidence_count=1,
                note="Phase 22A matrix projection: explicit Court response",
                source_category="court_response",
                extraction_origin=RelationshipOrigin.SOURCE_DOCUMENTED,
                verification_state=response.verification_state,
                verified_by=response.verified_by,
                verified_at=response.verified_at,
            )
            session.add(relationship)
            created_relationships += 1
        return created_nodes, created_relationships
