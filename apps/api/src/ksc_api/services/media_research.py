"""Case-scoped reads for external public sources and their verified court bridge."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from ksc_api.models import (
    COURT_MEDIA_STATUSES,
    Case,
    CourtMediaLink,
    ExternalSource,
    MediaItem,
    MediaStatement,
    MediaStatementComparison,
    ResolutionState,
    VerificationState,
)
from ksc_api.repositories import mappers
from ksc_api.repositories.records import CITATION_LOAD
from ksc_api.schemas.media import (
    CourtMediaLinkRead,
    ExternalSourceRead,
    MediaComparisonRead,
    MediaCoverageRead,
    MediaItemRead,
    MediaItemSummary,
    MediaNetworkEdge,
    MediaNetworkNode,
    MediaNetworkRead,
    MediaStatementRead,
    MediaTimelineEvent,
    MediaWorkspaceRead,
)

LIMITATIONS = [
    "Coverage is a small, curated set of manually submitted public URLs; it is not comprehensive.",
    "Private, login-gated, paywalled, deleted and access-controlled material is excluded.",
    "An external item is not court evidence unless a human-verified link has an exact resolved court citation.",
    "Facebook, TikTok and X are not comprehensively collected.",
]


class MediaResearchService:
    def __init__(self, session: Session, case: Case) -> None:
        self.session = session
        self.case = case

    def _items_stmt(self) -> Select[tuple[MediaItem]]:
        return (
            select(MediaItem)
            .join(ExternalSource)
            .options(
                selectinload(MediaItem.source),
                selectinload(MediaItem.statements),
                selectinload(MediaItem.court_links)
                .selectinload(CourtMediaLink.citation)
                .options(*CITATION_LOAD),
                selectinload(MediaItem.court_links).selectinload(CourtMediaLink.document),
                selectinload(MediaItem.court_links).selectinload(CourtMediaLink.exhibit),
                selectinload(MediaItem.court_links).selectinload(CourtMediaLink.finding),
            )
            .where(
                MediaItem.case_id == self.case.id,
                MediaItem.access_status == "public",
                MediaItem.verification_state != VerificationState.HUMAN_REJECTED,
                ExternalSource.visibility == "public",
                ExternalSource.verification_state != VerificationState.HUMAN_REJECTED,
            )
        )

    @staticmethod
    def _statement(row: MediaStatement) -> MediaStatementRead:
        return MediaStatementRead.model_validate(row)

    @staticmethod
    def _valid_link(row: CourtMediaLink) -> bool:
        if row.court_status in {"external_only", "unknown"}:
            return True
        return bool(
            row.verification_state == VerificationState.HUMAN_VERIFIED
            and row.citation is not None
            and row.citation.case_id == row.case_id
            and row.citation.resolution_state == ResolutionState.RESOLVED
        )

    @classmethod
    def _link(cls, row: CourtMediaLink) -> CourtMediaLinkRead | None:
        if not cls._valid_link(row):
            return None
        return CourtMediaLinkRead(
            id=row.id,
            court_status=row.court_status,
            note=row.note,
            citation=mappers.to_citation(row.citation) if row.citation is not None else None,
            document_ref=row.document.official_ref if row.document is not None else None,
            exhibit_ref=row.exhibit.official_exhibit_id if row.exhibit is not None else None,
            finding_key=row.finding.finding_key if row.finding is not None else None,
            verification_state=row.verification_state,
        )

    @classmethod
    def _summary(cls, row: MediaItem) -> MediaItemSummary:
        links = [link for link in row.court_links if cls._valid_link(link)]
        return MediaItemSummary(
            id=row.id,
            title=row.title,
            publisher=row.publisher,
            canonical_url=row.canonical_url,
            published_at=row.published_at,
            captured_at=row.captured_at,
            source_type=row.source.source_type,
            language=row.language,
            court_statuses=[link.court_status for link in links],
            verification_state=row.verification_state,
        )

    def workspace(
        self,
        *,
        q: str | None = None,
        court_status: str | None = None,
        source_type: str | None = None,
        language: str | None = None,
    ) -> MediaWorkspaceRead:
        stmt = self._items_stmt()
        if q:
            pattern = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    MediaItem.title.ilike(pattern),
                    MediaItem.publisher.ilike(pattern),
                    MediaItem.captured_text.ilike(pattern),
                )
            )
        if source_type:
            stmt = stmt.where(ExternalSource.source_type == source_type)
        if language:
            stmt = stmt.where(MediaItem.language == language)
        if court_status:
            stmt = stmt.where(
                MediaItem.id.in_(
                    select(CourtMediaLink.media_item_id).where(
                        CourtMediaLink.court_status == court_status
                    )
                )
            )
        items = list(
            self.session.scalars(stmt.order_by(MediaItem.published_at.desc().nulls_last()))
        )
        item_ids = [item.id for item in items]
        source_ids = {item.external_source_id for item in items}
        statements = sum(len(item.statements) for item in items)
        valid_links = [
            link for item in items for link in item.court_links if self._valid_link(link)
        ]
        comparisons = int(
            self.session.scalar(
                select(func.count())
                .select_from(MediaStatementComparison)
                .where(MediaStatementComparison.case_id == self.case.id)
            )
            or 0
        )
        return MediaWorkspaceRead(
            items=[self._summary(item) for item in items],
            comparisons=self.comparisons(),
            coverage=MediaCoverageRead(
                sources=len(source_ids),
                items=len(item_ids),
                statements=statements,
                court_links=len(valid_links),
                citation_backed_court_links=sum(
                    link.citation_id is not None for link in valid_links
                ),
                comparisons=comparisons,
            ),
            court_status_taxonomy=list(COURT_MEDIA_STATUSES),
            limitations=LIMITATIONS,
        )

    def item(self, item_id: uuid.UUID) -> MediaItemRead | None:
        row = self.session.scalar(self._items_stmt().where(MediaItem.id == item_id))
        if row is None:
            return None
        links = [mapped for link in row.court_links if (mapped := self._link(link)) is not None]
        return MediaItemRead(
            id=row.id,
            title=row.title,
            publisher=row.publisher,
            canonical_url=row.canonical_url,
            original_url=row.original_url,
            published_at=row.published_at,
            captured_at=row.captured_at,
            language=row.language,
            item_kind=row.item_kind,
            content_sha256=row.content_sha256,
            transcript_origin=row.transcript_origin,
            archive_url=row.archive_url,
            verification_state=row.verification_state,
            source=ExternalSourceRead.model_validate(row.source),
            statements=[self._statement(statement) for statement in row.statements],
            court_links=links,
        )

    def timeline(self) -> list[MediaTimelineEvent]:
        items = list(self.session.scalars(self._items_stmt().order_by(MediaItem.captured_at)))
        return [
            MediaTimelineEvent(
                id=item.id,
                media_item_id=item.id,
                title=item.title,
                publisher=item.publisher,
                occurred_at=item.published_at or item.captured_at,
                date_basis="published" if item.published_at else "captured",
                court_statuses=[
                    link.court_status for link in item.court_links if self._valid_link(link)
                ],
            )
            for item in items
        ]

    def network(self) -> MediaNetworkRead:
        items = list(self.session.scalars(self._items_stmt()))
        nodes: dict[str, MediaNetworkNode] = {}
        edges: list[MediaNetworkEdge] = []
        for item in items:
            external_id = f"media:{item.id}"
            for link in item.court_links:
                if link.citation is None or not self._valid_link(link):
                    continue
                court_id = f"court:{link.citation.id}"
                nodes[external_id] = MediaNetworkNode(
                    id=external_id, kind="external_media", label=item.title
                )
                nodes[court_id] = MediaNetworkNode(
                    id=court_id, kind="court_record", label=link.citation.display
                )
                edges.append(
                    MediaNetworkEdge(
                        id=link.id,
                        from_node_id=external_id,
                        to_node_id=court_id,
                        court_status=link.court_status,
                        citation=mappers.to_citation(link.citation),
                        verification_state=link.verification_state,
                    )
                )
        return MediaNetworkRead(nodes=list(nodes.values()), edges=edges)

    def comparisons(self) -> list[MediaComparisonRead]:
        rows = self.session.scalars(
            select(MediaStatementComparison)
            .options(
                selectinload(MediaStatementComparison.statement_a),
                selectinload(MediaStatementComparison.statement_b),
                selectinload(MediaStatementComparison.court_citation_b).options(*CITATION_LOAD),
            )
            .where(
                MediaStatementComparison.case_id == self.case.id,
                MediaStatementComparison.verification_state != VerificationState.HUMAN_REJECTED,
            )
            .order_by(MediaStatementComparison.comparison_key)
        ).all()
        return [
            MediaComparisonRead(
                id=row.id,
                comparison_key=row.comparison_key,
                title=row.title,
                classification=row.classification,
                statement_a=self._statement(row.statement_a),
                statement_b=self._statement(row.statement_b) if row.statement_b else None,
                court_citation_b=(
                    mappers.to_citation(row.court_citation_b)
                    if row.court_citation_b is not None
                    and row.court_citation_b.resolution_state == ResolutionState.RESOLVED
                    else None
                ),
                explanation=row.explanation,
                verification_state=row.verification_state,
            )
            for row in rows
        ]
