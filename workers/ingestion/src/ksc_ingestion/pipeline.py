"""The controlled ingestion pipeline (roadmap Phase 7).

    Discovery → SourceRecord → normalization → public visibility check
      → bytes (captured) → SHA-256 → object storage
      → Document + DocumentVersion (+ Hearing / Transcript)
      → IngestionJob / IngestionJobItem + AuditLog

Guarantees:
- every record becomes an `IngestionJobItem` with a terminal status; failures
  are rows, not log lines;
- each item commits on its own, so a crash leaves a resumable job; a re-run of
  the same bundle resumes the unfinished job or, if it finished, produces a new
  job whose items are all duplicates / no-ops;
- identity is (case, source system, external id) for provenance, (case,
  official ref) for documents, (document, official version ref) for versions
  and the SHA-256 for bytes. Nothing is overwritten: a version already holding
  different bytes is an `ambiguous_mapping` failure;
- nothing non-public is fetched or stored; UNKNOWN visibility fails closed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    INGESTION_FAILURE_STATUSES,
    PUBLIC_VISIBILITIES,
    ArtifactAcquisition,
    ArtifactQuarantine,
    ArtifactStatus,
    AuditLog,
    Case,
    Document,
    DocumentIngestionState,
    DocumentVersion,
    DocumentVersionType,
    Hearing,
    IngestionItemStatus,
    IngestionJob,
    IngestionJobStatus,
    SourceRecord,
    SourceRecordSnapshot,
    SourceSystem,
    Transcript,
    Visibility,
)
from ksc_ingestion.artifacts import ArtifactInfo, UnsupportedArtifactError, inspect
from ksc_ingestion.capture import CaptureBundle, DetailPageParser, DiscoveryFailure, discover
from ksc_ingestion.discovery import DiscoveredRecord
from ksc_ingestion.normalize import (
    NormalizationError,
    NormalizedDocument,
    NormalizedVersion,
    normalize,
)
from ksc_ingestion.storage import ObjectStore, storage_key

log = logging.getLogger(__name__)

ACTOR = "worker:ingestion"
JOB_TYPE_CAPTURE_BUNDLE = "capture_bundle"
JOB_TYPE_INVENTORY_SYNC = "official_inventory_sync"

_OPEN_JOB_STATUSES = (
    IngestionJobStatus.PENDING,
    IngestionJobStatus.RUNNING,
    IngestionJobStatus.FAILED,
)
# Worst-first order used to summarise a record with several artifacts.
_SEVERITY = (
    IngestionItemStatus.BLOCKED_BY_ACCESS_CONTROL,
    IngestionItemStatus.FAILED_DOWNLOAD,
    IngestionItemStatus.AMBIGUOUS_MAPPING,
    IngestionItemStatus.INVALID_METADATA,
    IngestionItemStatus.UNSUPPORTED_ARTIFACT,
    IngestionItemStatus.DOWNLOADED,
    IngestionItemStatus.METADATA_ONLY,
    IngestionItemStatus.SKIPPED_DUPLICATE,
    IngestionItemStatus.NOT_PUBLIC,
)


class CaseNotSeededError(RuntimeError):
    pass


@dataclass(frozen=True)
class VersionOutcome:
    official_version_ref: str
    status: IngestionItemStatus
    reason: str | None = None
    version_id: str | None = None
    sha256: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ItemOutcome:
    item_key: str
    status: IngestionItemStatus
    reason: str | None
    versions: tuple[VersionOutcome, ...] = ()
    skipped_as_done: bool = False


@dataclass(frozen=True)
class RunOutcome:
    job_id: str
    status: IngestionJobStatus
    items: tuple[ItemOutcome, ...]
    resumed: bool
    dry_run: bool

    def count(self, status: IngestionItemStatus) -> int:
        return sum(1 for i in self.items if i.status is status)

    @property
    def downloaded_artifacts(self) -> int:
        return sum(
            1 for i in self.items for v in i.versions if v.status is IngestionItemStatus.DOWNLOADED
        )


def _now() -> datetime:
    return datetime.now(UTC)


class Ingestor:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        store: ObjectStore,
        *,
        case_number: str,
        actor: str = ACTOR,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self._sessions = session_factory
        self._store = store
        self.case_number = case_number
        self.actor = actor
        self._clock = clock

    # ------------------------------------------------------------- bundles --
    def run_bundle(
        self,
        bundle: CaptureBundle,
        *,
        parsers: Iterable[DetailPageParser] = (),
        resume: bool = True,
        dry_run: bool = False,
    ) -> RunOutcome:
        if bundle.manifest.case_number != self.case_number:
            raise CaseNotSeededError(
                f"bundle is for {bundle.manifest.case_number}; ingestor is scoped to "
                f"{self.case_number}"
            )
        records = discover(bundle, parsers=parsers)
        cursor = {
            "bundle_id": bundle.manifest.bundle_id,
            "bundle_root": str(bundle.root),
            "captured_by": bundle.manifest.captured_by,
            "captured_at": bundle.manifest.captured_at.isoformat(),
        }
        return self.run_records(
            records,
            job_type=JOB_TYPE_CAPTURE_BUNDLE,
            source_system=SourceSystem.KSC_PUBLIC_COURT_RECORDS,
            cursor=cursor,
            resume_key=("bundle_id", bundle.manifest.bundle_id),
            resume=resume,
            dry_run=dry_run,
        )

    def run_inventory(
        self,
        inventory: CaptureBundle,
        *,
        resume: bool = True,
        dry_run: bool = False,
    ) -> RunOutcome:
        """Persist a public metadata inventory without acquiring bytes."""

        if inventory.manifest.case_number != self.case_number:
            raise CaseNotSeededError(
                f"inventory is for {inventory.manifest.case_number}; ingestor is scoped to "
                f"{self.case_number}"
            )
        records = discover(inventory)
        cursor = {
            "inventory_id": inventory.manifest.bundle_id,
            "inventory_path": str(inventory.root),
            "observed_at": inventory.manifest.captured_at.isoformat(),
        }
        return self.run_records(
            records,
            job_type=JOB_TYPE_INVENTORY_SYNC,
            source_system=SourceSystem.KSC_PUBLIC_COURT_RECORDS,
            cursor=cursor,
            resume_key=("inventory_id", inventory.manifest.bundle_id),
            resume=resume,
            dry_run=dry_run,
        )

    # ------------------------------------------------------------- records --
    def run_records(
        self,
        records: Sequence[DiscoveredRecord | DiscoveryFailure],
        *,
        job_type: str,
        source_system: SourceSystem,
        cursor: dict[str, Any],
        resume_key: tuple[str, str] | None = None,
        resume: bool = True,
        dry_run: bool = False,
    ) -> RunOutcome:
        """Run every record as its own committed unit of work. With
        `dry_run` everything happens in one transaction that is rolled back,
        so outcomes are reported but nothing persists."""

        if dry_run:
            with self._sessions() as session:
                job, resumed = self._start(session, records, job_type, source_system, cursor, None)
                outcomes = [self._run_item(session, job, record) for record in records]
                self._finish(session, job)
                result = RunOutcome(
                    str(job.id), job.status, tuple(outcomes), resumed=resumed, dry_run=True
                )
                session.rollback()
            return result

        with self._sessions() as session:
            job, resumed = self._start(
                session, records, job_type, source_system, cursor, resume_key if resume else None
            )
            job_id = job.id
            session.commit()

        outcomes = []
        for record in records:
            with self._sessions() as session:
                current = session.get(IngestionJob, job_id)
                assert current is not None
                try:
                    outcomes.append(self._run_item(session, current, record))
                    session.commit()
                except Exception:
                    session.rollback()
                    self._mark_failed(job_id, record.item_key)
                    raise

        with self._sessions() as session:
            final = session.get(IngestionJob, job_id)
            assert final is not None
            self._finish(session, final)
            status = final.status
            session.commit()
        return RunOutcome(str(job_id), status, tuple(outcomes), resumed=resumed, dry_run=False)

    def _start(
        self,
        session: Session,
        records: Sequence[DiscoveredRecord | DiscoveryFailure],
        job_type: str,
        source_system: SourceSystem,
        cursor: dict[str, Any],
        resume_key: tuple[str, str] | None,
    ) -> tuple[IngestionJob, bool]:
        case = self._case(session)
        job, resumed = self._open_job(session, case, job_type, source_system, cursor, resume_key)
        self._register_items(session, job, records)
        job.status = IngestionJobStatus.RUNNING
        job.started_at = job.started_at or self._clock()
        session.add(
            AuditLog(
                actor=self.actor,
                action="ingestion.job.started",
                entity_type="ingestion_job",
                entity_id=str(job.id),
                detail={"job_type": job_type, "resumed": resumed, "items": len(records)},
            )
        )
        session.flush()
        return job, resumed

    def _finish(self, session: Session, job: IngestionJob) -> None:
        self._recount(job)
        job.status = IngestionJobStatus.COMPLETED
        job.finished_at = self._clock()
        session.add(
            AuditLog(
                actor=self.actor,
                action="ingestion.job.finished",
                entity_type="ingestion_job",
                entity_id=str(job.id),
                detail={
                    "discovered": job.discovered_count,
                    "downloaded": job.downloaded_count,
                    "processed": job.processed_count,
                    "failed": job.failed_count,
                },
            )
        )
        session.flush()

    def _mark_failed(self, job_id: Any, item_key: str) -> None:
        with self._sessions() as session:
            job = session.get(IngestionJob, job_id)
            if job is not None:
                job.status = IngestionJobStatus.FAILED
                job.error_summary = f"unexpected error while processing {item_key}"
                session.commit()

    # ------------------------------------------------------------- job ops --
    def _case(self, session: Session) -> Case:
        case = session.scalar(select(Case).where(Case.case_number == self.case_number))
        if case is None:
            raise CaseNotSeededError(f"case {self.case_number} is not seeded")
        return case

    def _open_job(
        self,
        session: Session,
        case: Case,
        job_type: str,
        source_system: SourceSystem,
        cursor: dict[str, Any],
        resume_key: tuple[str, str] | None,
    ) -> tuple[IngestionJob, bool]:
        if resume_key is not None:
            key, value = resume_key
            existing = session.scalars(
                select(IngestionJob)
                .where(
                    IngestionJob.case_id == case.id,
                    IngestionJob.job_type == job_type,
                    IngestionJob.cursor[key].astext == value,
                    IngestionJob.status.in_(_OPEN_JOB_STATUSES),
                )
                .order_by(IngestionJob.created_at.desc())
            ).first()
            if existing is not None:
                existing.cursor = {**(existing.cursor or {}), **cursor}
                return existing, True
        job = IngestionJob(
            case_id=case.id,
            source_system=source_system,
            job_type=job_type,
            status=IngestionJobStatus.PENDING,
            cursor=cursor,
            checkpoint={},
        )
        session.add(job)
        session.flush()
        return job, False

    def _register_items(
        self,
        session: Session,
        job: IngestionJob,
        records: Sequence[DiscoveredRecord | DiscoveryFailure],
    ) -> None:
        from ksc_api.models import IngestionJobItem

        existing = {item.item_key: item for item in job.items}
        next_sequence = max((item.sequence for item in job.items), default=-1) + 1
        for record in records:
            if record.item_key in existing:
                continue
            item = IngestionJobItem(
                job_id=job.id,
                item_key=record.item_key,
                sequence=next_sequence,
                status=IngestionItemStatus.PENDING,
            )
            next_sequence += 1
            session.add(item)
            existing[record.item_key] = item
        job.discovered_count = len(existing)
        session.flush()

    def _recount(self, job: IngestionJob) -> None:
        terminal = [i for i in job.items if i.status is not IngestionItemStatus.PENDING]
        job.discovered_count = len(job.items)
        job.processed_count = len(terminal)
        job.failed_count = sum(1 for i in terminal if i.status in INGESTION_FAILURE_STATUSES)
        job.downloaded_count = sum(
            1
            for i in terminal
            for v in (i.detail or {}).get("versions", [])
            if v.get("status") == IngestionItemStatus.DOWNLOADED.value
        )
        failures = [i for i in terminal if i.status in INGESTION_FAILURE_STATUSES]
        job.error_summary = (
            "; ".join(f"{i.item_key}: {i.status.value}" for i in failures[:20]) or None
        )

    # ---------------------------------------------------------------- item --
    def _run_item(
        self, session: Session, job: IngestionJob, record: DiscoveredRecord | DiscoveryFailure
    ) -> ItemOutcome:
        from ksc_api.models import IngestionJobItem

        item = session.scalar(
            select(IngestionJobItem).where(
                IngestionJobItem.job_id == job.id, IngestionJobItem.item_key == record.item_key
            )
        )
        assert item is not None
        if item.status is not IngestionItemStatus.PENDING:
            return ItemOutcome(item.item_key, item.status, item.reason, skipped_as_done=True)

        item.started_at = self._clock()
        outcome = self._process(session, job, item, record)
        item.status = outcome.status
        item.reason = outcome.reason
        item.detail = {
            **(item.detail or {}),
            "versions": [
                {
                    "official_version_ref": v.official_version_ref,
                    "status": v.status.value,
                    "reason": v.reason,
                    "sha256": v.sha256,
                    **v.detail,
                }
                for v in outcome.versions
            ],
        }
        item.finished_at = self._clock()
        self._quarantine_failures(session, job, item, outcome)
        job.checkpoint = {
            **(job.checkpoint or {}),
            "last_item_key": item.item_key,
            "last_sequence": item.sequence,
            "updated_at": self._clock().isoformat(),
        }
        job.processed_count += 1
        if outcome.status in INGESTION_FAILURE_STATUSES:
            job.failed_count += 1
        job.downloaded_count += sum(
            1 for v in outcome.versions if v.status is IngestionItemStatus.DOWNLOADED
        )
        session.add(
            AuditLog(
                actor=self.actor,
                action=f"ingestion.item.{outcome.status.value}",
                entity_type="ingestion_job_item",
                entity_id=str(item.id),
                detail={
                    "job_id": str(job.id),
                    "item_key": item.item_key,
                    "reason": outcome.reason,
                    "versions": [
                        {
                            "ref": v.official_version_ref,
                            "status": v.status.value,
                            "sha256": v.sha256,
                        }
                        for v in outcome.versions
                    ],
                },
            )
        )
        session.flush()
        return outcome

    def _quarantine_failures(
        self, session: Session, job: IngestionJob, item: Any, outcome: ItemOutcome
    ) -> None:
        """Keep provenance/artifact conflicts out of trusted processing.

        Access-control blocks and ordinary download failures are operational
        states, not evidence-quality conflicts, so they remain visible on the
        ingestion item without entering the human review queue.
        """

        serious = {
            IngestionItemStatus.AMBIGUOUS_MAPPING,
            IngestionItemStatus.INVALID_METADATA,
            IngestionItemStatus.UNSUPPORTED_ARTIFACT,
        }
        failures: list[VersionOutcome | None] = [
            version for version in outcome.versions if version.status in serious
        ]
        if not failures and outcome.status in serious:
            failures = [None]
        for version in failures:
            status = version.status if version is not None else outcome.status
            reason = (version.reason if version is not None else outcome.reason) or status.value
            version_id = (
                uuid.UUID(version.version_id)
                if version is not None and version.version_id is not None
                else None
            )
            sha256 = version.sha256 if version is not None else None
            # A re-run of the same capture must not open a second review row
            # for the same conflict; the existing open row already carries it.
            already_open = session.scalar(
                select(ArtifactQuarantine.id).where(
                    ArtifactQuarantine.case_id == job.case_id,
                    ArtifactQuarantine.state == "open",
                    ArtifactQuarantine.reason_code == status.value,
                    ArtifactQuarantine.reason == reason,
                    ArtifactQuarantine.document_version_id.is_(version_id)
                    if version_id is None
                    else ArtifactQuarantine.document_version_id == version_id,
                )
            )
            if already_open is not None:
                continue
            session.add(
                ArtifactQuarantine(
                    case_id=job.case_id,
                    document_version_id=version_id,
                    ingestion_job_item_id=item.id,
                    reason_code=status.value,
                    reason=reason,
                    artifact_sha256=sha256,
                    detail=version.detail if version is not None else item.detail,
                    state="open",
                )
            )

    def _process(
        self,
        session: Session,
        job: IngestionJob,
        item: Any,
        record: DiscoveredRecord | DiscoveryFailure,
    ) -> ItemOutcome:
        if isinstance(record, DiscoveryFailure):
            item.detail = dict(record.detail)
            return ItemOutcome(record.item_key, record.status, record.reason)

        case = session.get(Case, job.case_id)
        assert case is not None

        source = self._upsert_source_record(session, case, record)
        item.source_record_id = source.id
        item.detail = {
            "detail_page_url": record.detail_page_url,
            "discovery_url": record.discovery_url,
            "metadata_source": record.metadata_source.value,
            "official_ref": record.official_ref,
        }

        try:
            normalized = normalize(record, expected_case_number=case.case_number)
        except NormalizationError as exc:
            status = (
                IngestionItemStatus.AMBIGUOUS_MAPPING
                if exc.ambiguous
                else IngestionItemStatus.INVALID_METADATA
            )
            return ItemOutcome(record.item_key, status, str(exc))

        document = self._upsert_document(session, case, record, normalized)
        item.document_id = document.id
        source.document_id = document.id
        source.record_type = normalized.document_type
        source.visibility = normalized.visibility

        if normalized.visibility not in PUBLIC_VISIBILITIES:
            # Identifier known, material not public: stated, never fetched.
            return ItemOutcome(
                record.item_key,
                IngestionItemStatus.NOT_PUBLIC,
                f"record classification {record.classification!r} → {normalized.visibility.value}; "
                "nothing fetched or stored",
            )

        outcomes: list[VersionOutcome] = []
        primary_version: DocumentVersion | None = None
        for nv in normalized.versions:
            outcome, version = self._ingest_version(session, case, document, nv)
            outcomes.append(outcome)
            if version is not None and (
                primary_version is None or version.artifact_status is ArtifactStatus.FETCHED
            ):
                primary_version = version

        if primary_version is not None:
            source.document_version_id = primary_version.id
            item.document_version_id = primary_version.id
            if record.hearing is not None:
                self._upsert_transcript(session, case, document, primary_version, record, source)

        if any(v.artifact_status is ArtifactStatus.FETCHED for v in document.versions):
            if document.ingestion_state is DocumentIngestionState.DISCOVERED:
                document.ingestion_state = DocumentIngestionState.DOWNLOADED

        status, reason = self._summarise(outcomes)
        return ItemOutcome(record.item_key, status, reason, tuple(outcomes))

    # ------------------------------------------------------------ upserts --
    def _upsert_source_record(
        self, session: Session, case: Case, record: DiscoveredRecord
    ) -> SourceRecord:
        source = session.scalar(
            select(SourceRecord).where(
                SourceRecord.case_id == case.id,
                SourceRecord.source_system == record.source_system,
                SourceRecord.external_record_id == record.external_record_id,
            )
        )
        now = self._clock()
        seen_at = record.discovered_at or now
        if source is None:
            source = SourceRecord(
                case_id=case.id,
                source_system=record.source_system,
                external_record_id=record.external_record_id,
                record_type=record.record_type.lower(),
                language=record.language,
                discovery_url=record.discovery_url,
                canonical_source_url=record.detail_page_url,
                title=record.title,
                visibility=Visibility.UNKNOWN,
                raw_metadata=record.raw_metadata,
                discovered_at=seen_at,
                last_seen_at=seen_at,
            )
            session.add(source)
            session.flush()
            self._snapshot_source_record(session, source, record, seen_at)
            return source
        source.last_seen_at = max(source.last_seen_at, seen_at)
        source.title = record.title
        source.language = record.language or source.language
        source.canonical_source_url = record.detail_page_url
        source.raw_metadata = record.raw_metadata
        self._snapshot_source_record(session, source, record, seen_at)
        return source

    @staticmethod
    def _snapshot_source_record(
        session: Session,
        source: SourceRecord,
        record: DiscoveredRecord,
        observed_at: datetime,
    ) -> None:
        metadata = {
            "record_type": record.record_type,
            "language": record.language,
            "discovery_url": record.discovery_url,
            "canonical_source_url": record.detail_page_url,
            "title": record.title,
            "raw_metadata": record.raw_metadata,
        }
        encoded = json.dumps(metadata, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
        digest = hashlib.sha256(encoded).hexdigest()
        exists = session.scalar(
            select(SourceRecordSnapshot.id).where(
                SourceRecordSnapshot.source_record_id == source.id,
                SourceRecordSnapshot.metadata_sha256 == digest,
            )
        )
        if exists is None:
            session.add(
                SourceRecordSnapshot(
                    source_record_id=source.id,
                    observed_at=observed_at,
                    metadata_sha256=digest,
                    metadata_payload=metadata,
                )
            )

    def _upsert_document(
        self,
        session: Session,
        case: Case,
        record: DiscoveredRecord,
        normalized: NormalizedDocument,
    ) -> Document:
        document = session.scalar(
            select(Document).where(
                Document.case_id == case.id, Document.official_ref == normalized.official_ref
            )
        )
        values: dict[str, Any] = {
            "filing_number": normalized.filing_number,
            "title": normalized.title,
            "document_type": normalized.document_type,
            "language": normalized.language,
            "filing_party": normalized.filing_party,
            "document_date": normalized.document_date,
            "filing_date": normalized.filing_date,
            "public_date": normalized.public_date,
            "visibility": normalized.visibility,
            "source_url": record.detail_page_url,
        }
        if document is None:
            document = Document(
                case_id=case.id,
                official_ref=normalized.official_ref,
                ingestion_state=DocumentIngestionState.DISCOVERED,
                **values,
            )
            session.add(document)
            session.flush()
            return document
        incoming_is_translation = all(
            version.version_type is DocumentVersionType.TRANSLATION
            for version in normalized.versions
        )
        if normalized.language and document.language and normalized.language != document.language:
            # A translation adds a version; it does not rename or re-source the
            # document, whose identity stays with the original-language record.
            # When the translation happened to arrive first, the original-language
            # record takes the identity over on arrival (audited below).
            if incoming_is_translation:
                for key in ("title", "language", "source_url"):
                    values.pop(key)
        changed = [k for k, v in values.items() if v is not None and getattr(document, k) != v]
        for k in changed:
            setattr(document, k, values[k])
        if changed:
            session.add(
                AuditLog(
                    actor=self.actor,
                    action="document.metadata_updated",
                    entity_type="document",
                    entity_id=document.official_ref,
                    detail={"fields": changed, "metadata_source": record.metadata_source.value},
                )
            )
        return document

    def _ingest_version(
        self, session: Session, case: Case, document: Document, nv: NormalizedVersion
    ) -> tuple[VersionOutcome, DocumentVersion | None]:
        ref = nv.official_version_ref
        existing = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.document_id == document.id,
                DocumentVersion.official_version_ref == ref,
            )
        )

        if nv.visibility not in PUBLIC_VISIBILITIES:
            return (
                VersionOutcome(
                    ref,
                    IngestionItemStatus.NOT_PUBLIC,
                    f"version classification {nv.artifact.classification!r} → {nv.visibility.value}",
                ),
                existing,
            )

        if nv.artifact.local_file is None:
            if existing is not None:
                held = existing.artifact_status is ArtifactStatus.FETCHED
                return (
                    VersionOutcome(
                        ref,
                        IngestionItemStatus.METADATA_ONLY,
                        "already held" if held else "already recorded; bytes not fetched",
                        version_id=str(existing.id),
                        sha256=existing.sha256,
                    ),
                    existing,
                )
            version = self._new_version(document, nv, ArtifactStatus.NOT_FETCHED)
            session.add(version)
            session.flush()
            return (
                VersionOutcome(
                    ref,
                    IngestionItemStatus.METADATA_ONLY,
                    "official URLs recorded; bytes not fetched",
                    version_id=str(version.id),
                ),
                version,
            )

        data = nv.artifact.local_file.read_bytes()
        try:
            info = inspect(data)
        except UnsupportedArtifactError as exc:
            if existing is None:
                existing = self._new_version(document, nv, ArtifactStatus.FAILED)
                session.add(existing)
                session.flush()
            return (
                VersionOutcome(
                    ref,
                    IngestionItemStatus.UNSUPPORTED_ARTIFACT,
                    str(exc),
                    version_id=str(existing.id),
                ),
                existing,
            )

        detail: dict[str, Any] = {
            "byte_size": info.byte_size,
            "page_count": info.page_count,
            "has_text_layer": info.has_text_layer,
            "case_numbers_on_first_page": list(info.case_numbers_on_first_page),
            "declared_sha256": nv.artifact.declared_sha256,
            "declared_byte_size": nv.artifact.declared_byte_size,
        }
        declared = nv.artifact.declared_sha256
        if (declared is not None and declared != info.sha256) or (
            nv.artifact.declared_byte_size is not None
            and nv.artifact.declared_byte_size != info.byte_size
        ):
            return (
                VersionOutcome(
                    ref,
                    IngestionItemStatus.AMBIGUOUS_MAPPING,
                    "file does not match the hash / size recorded at capture time; not stored",
                    sha256=info.sha256,
                    detail=detail,
                ),
                existing,
            )
        if (
            info.case_numbers_on_first_page
            and case.case_number not in info.case_numbers_on_first_page
        ):
            return (
                VersionOutcome(
                    ref,
                    IngestionItemStatus.INVALID_METADATA,
                    f"first page names {', '.join(info.case_numbers_on_first_page)}, not "
                    f"{case.case_number}",
                    sha256=info.sha256,
                    detail=detail,
                ),
                existing,
            )

        if existing is not None and existing.artifact_status is ArtifactStatus.FETCHED:
            if existing.sha256 == info.sha256:
                self._store.put(existing.storage_key or "", data, info.mime_type)
                self._mark_acquired(session, existing)
                return (
                    VersionOutcome(
                        ref,
                        IngestionItemStatus.SKIPPED_DUPLICATE,
                        "identical bytes already held",
                        version_id=str(existing.id),
                        sha256=info.sha256,
                        detail=detail,
                    ),
                    existing,
                )
            return (
                VersionOutcome(
                    ref,
                    IngestionItemStatus.AMBIGUOUS_MAPPING,
                    "version already holds different bytes; not overwritten",
                    version_id=str(existing.id),
                    sha256=info.sha256,
                    detail={**detail, "held_sha256": existing.sha256},
                ),
                existing,
            )

        same_bytes = session.scalar(
            select(DocumentVersion).where(DocumentVersion.sha256 == info.sha256)
        )
        if same_bytes is not None:
            if existing is None:
                existing = self._new_version(document, nv, ArtifactStatus.NOT_FETCHED)
                session.add(existing)
                session.flush()
            other_doc = session.get(Document, same_bytes.document_id)
            return (
                VersionOutcome(
                    ref,
                    IngestionItemStatus.SKIPPED_DUPLICATE,
                    "identical bytes already held under another version",
                    version_id=str(existing.id),
                    sha256=info.sha256,
                    detail={
                        **detail,
                        "duplicate_of": {
                            "official_ref": other_doc.official_ref if other_doc else None,
                            "official_version_ref": same_bytes.official_version_ref,
                        },
                    },
                ),
                existing,
            )

        key = storage_key(case.case_number, nv.official_version_ref, info.sha256)
        self._store.put(key, data, info.mime_type)
        version = existing or self._new_version(document, nv, ArtifactStatus.NOT_FETCHED)
        self._fill_bytes(version, nv, info, key)
        session.add(version)
        session.flush()
        self._mark_acquired(session, version)
        return (
            VersionOutcome(
                ref,
                IngestionItemStatus.DOWNLOADED,
                None,
                version_id=str(version.id),
                sha256=info.sha256,
                detail={**detail, "storage_key": key},
            ),
            version,
        )

    @staticmethod
    def _mark_acquired(session: Session, version: DocumentVersion) -> None:
        queued = session.scalar(
            select(ArtifactAcquisition).where(ArtifactAcquisition.document_version_id == version.id)
        )
        if queued is not None:
            queued.status = "captured"
            queued.lease_owner = None
            queued.lease_expires_at = None
            queued.last_failure_class = None
            queued.last_error = None

    @staticmethod
    def _new_version(
        document: Document, nv: NormalizedVersion, status: ArtifactStatus
    ) -> DocumentVersion:
        return DocumentVersion(
            document_id=document.id,
            official_version_ref=nv.official_version_ref,
            version_type=nv.version_type,
            version_label=nv.version_label,
            visibility=nv.visibility,
            public_date=nv.public_date,
            source_url=nv.source_url,
            artifact_status=status,
        )

    def _fill_bytes(
        self, version: DocumentVersion, nv: NormalizedVersion, info: ArtifactInfo, key: str
    ) -> None:
        version.artifact_status = ArtifactStatus.FETCHED
        version.storage_key = key
        version.sha256 = info.sha256
        version.mime_type = info.mime_type
        version.byte_size = info.byte_size
        version.page_count = info.page_count
        version.fetched_at = nv.artifact.captured_at or self._clock()
        version.fetch_method = nv.artifact.fetch_method or "unknown"
        version.source_url = nv.source_url

    def _upsert_transcript(
        self,
        session: Session,
        case: Case,
        document: Document,
        version: DocumentVersion,
        record: DiscoveredRecord,
        source: SourceRecord,
    ) -> None:
        assert record.hearing is not None
        h = record.hearing
        hearing = session.scalar(
            select(Hearing).where(
                Hearing.case_id == case.id,
                Hearing.hearing_date == h.hearing_date,
                Hearing.session_sequence == h.session_sequence,
            )
        )
        if hearing is None:
            hearing = Hearing(
                case_id=case.id,
                hearing_date=h.hearing_date,
                session_sequence=h.session_sequence,
                session_label=h.session_label,
                hearing_type=h.hearing_type,
                source_url=record.detail_page_url,
                visibility=document.visibility,
            )
            session.add(hearing)
            session.flush()
        transcript = session.scalar(
            select(Transcript).where(Transcript.document_version_id == version.id)
        )
        if transcript is None:
            transcript = Transcript(
                hearing_id=hearing.id,
                document_version_id=version.id,
                official_ref=document.official_ref,
                language=document.language,
                visibility=version.visibility,
            )
            session.add(transcript)
            session.flush()
        source.hearing_id = hearing.id
        source.transcript_id = transcript.id

    @staticmethod
    def _summarise(outcomes: Sequence[VersionOutcome]) -> tuple[IngestionItemStatus, str | None]:
        if not outcomes:
            return IngestionItemStatus.METADATA_ONLY, "record recorded; no public artifact listed"
        statuses = {o.status for o in outcomes}
        for status in _SEVERITY:
            if status in statuses:
                reasons = [o.reason for o in outcomes if o.status is status and o.reason]
                return status, "; ".join(reasons) or None
        return outcomes[0].status, outcomes[0].reason
