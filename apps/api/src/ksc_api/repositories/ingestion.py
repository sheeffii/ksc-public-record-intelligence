"""IngestionStatusRepository — internal data-status reads.

Unlike `RecordRepository` this view is *not* filtered to public visibility:
its purpose is to show what ingestion did, including records it refused
(`not_public`, `unknown`). It still exposes only identifiers, URLs, hashes and
job state — never document text.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from ksc_api.config import Settings, get_settings
from ksc_api.db.session import get_session
from ksc_api.models import (
    INGESTION_FAILURE_STATUSES,
    PUBLIC_VISIBILITIES,
    ArtifactAcquisition,
    ArtifactQuarantine,
    ArtifactStatus,
    Case,
    Citation,
    Document,
    DocumentIngestionState,
    DocumentPage,
    DocumentParagraph,
    DocumentVersion,
    Hearing,
    IngestionItemStatus,
    IngestionJob,
    IngestionJobItem,
    ProcessingRun,
    ResolutionState,
    SourceRecord,
    SourceRecordSnapshot,
    Transcript,
    TranscriptSegment,
)
from ksc_api.repositories.records import CaseNotConfiguredError
from ksc_api.schemas.ingestion import (
    HeldVersionRead,
    IngestionCounts,
    IngestionItemRead,
    IngestionJobRead,
    IngestionStatusRead,
)


class IngestionStatusRepository:
    def __init__(self, session: Session, case: Case) -> None:
        self.session = session
        self.case = case

    def _count(self, stmt: Select[tuple[int]]) -> int:
        return int(self.session.scalar(stmt) or 0)

    def counts(self) -> IngestionCounts:
        case_id = self.case.id
        docs = select(func.count()).select_from(Document).where(Document.case_id == case_id)
        versions = (
            select(func.count())
            .select_from(DocumentVersion)
            .join(Document, Document.id == DocumentVersion.document_id)
            .where(Document.case_id == case_id)
        )
        return IngestionCounts(
            source_records=self._count(
                select(func.count())
                .select_from(SourceRecord)
                .where(SourceRecord.case_id == case_id)
            ),
            documents=self._count(docs),
            documents_public=self._count(docs.where(Document.visibility.in_(PUBLIC_VISIBILITIES))),
            documents_not_public=self._count(
                docs.where(Document.visibility.notin_(PUBLIC_VISIBILITIES))
            ),
            versions=self._count(versions),
            versions_fetched=self._count(
                versions.where(DocumentVersion.artifact_status == ArtifactStatus.FETCHED)
            ),
            versions_not_fetched=self._count(
                versions.where(DocumentVersion.artifact_status == ArtifactStatus.NOT_FETCHED)
            ),
            versions_failed=self._count(
                versions.where(DocumentVersion.artifact_status == ArtifactStatus.FAILED)
            ),
            versions_parsed=self._count(versions.where(DocumentVersion.parsed_at.is_not(None))),
            documents_indexed=self._count(
                docs.where(Document.ingestion_state == DocumentIngestionState.INDEXED)
            ),
            pages_parsed=self._count(
                select(func.count())
                .select_from(DocumentPage)
                .join(DocumentVersion)
                .join(Document)
                .where(Document.case_id == case_id)
            ),
            paragraphs_parsed=self._count(
                select(func.count())
                .select_from(DocumentParagraph)
                .join(DocumentVersion)
                .join(Document)
                .where(Document.case_id == case_id)
            ),
            transcript_segments_parsed=self._count(
                select(func.count())
                .select_from(TranscriptSegment)
                .join(Transcript)
                .join(Hearing)
                .where(Hearing.case_id == case_id)
            ),
            citations=self._count(
                select(func.count()).select_from(Citation).where(Citation.case_id == case_id)
            ),
            citations_resolved=self._count(
                select(func.count())
                .select_from(Citation)
                .where(
                    Citation.case_id == case_id,
                    Citation.resolution_state == ResolutionState.RESOLVED,
                )
            ),
            citations_ambiguous=self._count(
                select(func.count())
                .select_from(Citation)
                .where(
                    Citation.case_id == case_id,
                    Citation.resolution_state == ResolutionState.AMBIGUOUS,
                )
            ),
            citations_unresolved=self._count(
                select(func.count())
                .select_from(Citation)
                .where(
                    Citation.case_id == case_id,
                    Citation.resolution_state == ResolutionState.UNRESOLVED,
                )
            ),
            citations_invalid=self._count(
                select(func.count())
                .select_from(Citation)
                .where(
                    Citation.case_id == case_id,
                    Citation.resolution_state == ResolutionState.INVALID,
                )
            ),
            hearings=self._count(
                select(func.count()).select_from(Hearing).where(Hearing.case_id == case_id)
            ),
            transcripts=self._count(
                select(func.count())
                .select_from(Transcript)
                .join(Hearing, Hearing.id == Transcript.hearing_id)
                .where(Hearing.case_id == case_id)
            ),
            jobs=self._count(
                select(func.count())
                .select_from(IngestionJob)
                .where(IngestionJob.case_id == case_id)
            ),
            items_failed=self._count(
                select(func.count())
                .select_from(IngestionJobItem)
                .join(IngestionJob, IngestionJob.id == IngestionJobItem.job_id)
                .where(
                    IngestionJob.case_id == case_id,
                    IngestionJobItem.status.in_(INGESTION_FAILURE_STATUSES),
                )
            ),
            items_duplicate=self._count(
                select(func.count())
                .select_from(IngestionJobItem)
                .join(IngestionJob, IngestionJob.id == IngestionJobItem.job_id)
                .where(
                    IngestionJob.case_id == case_id,
                    IngestionJobItem.status == IngestionItemStatus.SKIPPED_DUPLICATE,
                )
            ),
            verified_artifact_bytes=int(
                self.session.scalar(
                    select(func.coalesce(func.sum(DocumentVersion.byte_size), 0))
                    .select_from(DocumentVersion)
                    .join(Document)
                    .where(
                        Document.case_id == case_id,
                        DocumentVersion.artifact_status == ArtifactStatus.FETCHED,
                    )
                )
                or 0
            ),
            parse_review_required=self._count(
                versions.where(DocumentVersion.parse_requires_review.is_(True))
            ),
            source_metadata_snapshots=self._count(
                select(func.count())
                .select_from(SourceRecordSnapshot)
                .join(SourceRecord)
                .where(SourceRecord.case_id == case_id)
            ),
            acquisition_pending=self._count(
                select(func.count())
                .select_from(ArtifactAcquisition)
                .where(
                    ArtifactAcquisition.case_id == case_id,
                    ArtifactAcquisition.status == "pending",
                )
            ),
            acquisition_leased=self._count(
                select(func.count())
                .select_from(ArtifactAcquisition)
                .where(
                    ArtifactAcquisition.case_id == case_id,
                    ArtifactAcquisition.status == "leased",
                )
            ),
            acquisition_blocked=self._count(
                select(func.count())
                .select_from(ArtifactAcquisition)
                .where(
                    ArtifactAcquisition.case_id == case_id,
                    ArtifactAcquisition.status == "blocked",
                )
            ),
            acquisition_failed=self._count(
                select(func.count())
                .select_from(ArtifactAcquisition)
                .where(
                    ArtifactAcquisition.case_id == case_id,
                    ArtifactAcquisition.status == "failed",
                )
            ),
            quarantine_open=self._count(
                select(func.count())
                .select_from(ArtifactQuarantine)
                .where(
                    ArtifactQuarantine.case_id == case_id,
                    ArtifactQuarantine.state == "open",
                )
            ),
            processing_runs=self._count(
                select(func.count())
                .select_from(ProcessingRun)
                .where(ProcessingRun.case_id == case_id)
            ),
        )

    def jobs(self, limit: int) -> list[IngestionJobRead]:
        rows = self.session.scalars(
            select(IngestionJob)
            .options(selectinload(IngestionJob.items))
            .where(IngestionJob.case_id == self.case.id)
            .order_by(IngestionJob.created_at.desc())
            .limit(limit)
        ).all()
        return [
            IngestionJobRead(
                id=job.id,
                job_type=job.job_type,
                source_system=job.source_system,
                status=job.status,
                cursor=job.cursor,
                checkpoint=job.checkpoint,
                discovered_count=job.discovered_count,
                downloaded_count=job.downloaded_count,
                processed_count=job.processed_count,
                failed_count=job.failed_count,
                started_at=job.started_at,
                finished_at=job.finished_at,
                error_summary=job.error_summary,
                items=[
                    IngestionItemRead(
                        item_key=item.item_key,
                        sequence=item.sequence,
                        status=item.status,
                        reason=item.reason,
                        detail=item.detail,
                        official_ref=(item.detail or {}).get("official_ref"),
                        started_at=item.started_at,
                        finished_at=item.finished_at,
                    )
                    for item in job.items
                ],
            )
            for job in rows
        ]

    def held(self) -> list[HeldVersionRead]:
        rows = self.session.execute(
            select(DocumentVersion, Document, SourceRecord)
            .join(Document, Document.id == DocumentVersion.document_id)
            .outerjoin(SourceRecord, SourceRecord.document_id == Document.id)
            .where(Document.case_id == self.case.id)
            .order_by(Document.official_ref, DocumentVersion.official_version_ref)
        ).all()
        out: list[HeldVersionRead] = []
        seen: set[object] = set()
        for version, document, source in rows:
            if version.id in seen:
                continue
            seen.add(version.id)
            raw = (source.raw_metadata if source is not None else None) or {}
            out.append(
                HeldVersionRead(
                    official_ref=document.official_ref,
                    official_version_ref=version.official_version_ref,
                    title=document.title,
                    document_type=document.document_type,
                    visibility=version.visibility,
                    artifact_status=version.artifact_status,
                    source_url=version.source_url,
                    detail_page_url=source.canonical_source_url if source is not None else None,
                    discovery_url=source.discovery_url if source is not None else None,
                    source_system=source.source_system if source is not None else None,
                    external_record_id=source.external_record_id if source is not None else None,
                    metadata_source=raw.get("metadata_source"),
                    sha256=version.sha256,
                    byte_size=version.byte_size,
                    page_count=version.page_count,
                    fetched_at=version.fetched_at,
                    fetch_method=version.fetch_method,
                )
            )
        return out

    def status(self, *, job_limit: int = 20) -> IngestionStatusRead:
        return IngestionStatusRead(
            case_number=self.case.case_number,
            counts=self.counts(),
            jobs=self.jobs(job_limit),
            held=self.held(),
        )


def get_ingestion_repository(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> IngestionStatusRepository:
    case = session.scalar(select(Case).where(Case.case_number == settings.case_id))
    if case is None:
        raise CaseNotConfiguredError(settings.case_id)
    return IngestionStatusRepository(session, case)
