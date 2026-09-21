"""Bounded artifact acquisition queue and browser-capture work plans.

This module schedules only versions already proven public by normalization.
It does not automate a browser, carry cookies, solve challenges or contact the
network.  A future admitted official HTTP adapter can consume leased rows; the
current Cloudflare state is recorded as terminal ``blocked`` and routed to the
documented operator-capture workflow.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    ArtifactAcquisition,
    ArtifactQuarantine,
    ArtifactStatus,
    AuditLog,
    Case,
    Document,
    DocumentVersion,
)
from ksc_ingestion.artifacts import UnsupportedArtifactError, inspect
from ksc_ingestion.fetch import AccessControlBlockedError, FetchError, HttpFetcher
from ksc_ingestion.sources import require_official
from ksc_ingestion.storage import ObjectStore, storage_key


@dataclass(frozen=True)
class AcquisitionPlanItem:
    queue_id: str
    official_ref: str
    official_version_ref: str
    official_url: str
    attempt_count: int


@dataclass(frozen=True)
class AcquiredArtifact:
    body: bytes
    fetched_at: datetime
    method: str


class AcquisitionAdapter(Protocol):
    """Official-source byte adapter; future bulk/API exports implement this contract."""

    def fetch(self, url: str) -> AcquiredArtifact: ...


class OfficialHttpAdapter:
    """Ordinary identified HTTP. Robots/access-control behavior lives in HttpFetcher."""

    def __init__(self, fetcher: HttpFetcher) -> None:
        self.fetcher = fetcher

    def fetch(self, url: str) -> AcquiredArtifact:
        result = self.fetcher.get(url)
        return AcquiredArtifact(result.body, result.fetched_at, "identified_http")


@dataclass(frozen=True)
class AcquisitionBatchResult:
    claimed: int
    fetched: int
    blocked: int
    failed: int
    quarantined: int


class AcquisitionQueue:
    """PostgreSQL-safe queue with expiring leases and deterministic backoff."""

    def __init__(self, session: Session, case: Case) -> None:
        self.session = session
        self.case = case

    def enqueue_missing(self, *, now: datetime | None = None) -> int:
        now = now or datetime.now(UTC)
        rows = self.session.execute(
            select(DocumentVersion, Document)
            .join(Document)
            .outerjoin(
                ArtifactAcquisition,
                ArtifactAcquisition.document_version_id == DocumentVersion.id,
            )
            .where(
                Document.case_id == self.case.id,
                Document.visibility.in_(PUBLIC_VISIBILITIES),
                DocumentVersion.visibility.in_(PUBLIC_VISIBILITIES),
                DocumentVersion.artifact_status == ArtifactStatus.NOT_FETCHED,
                DocumentVersion.source_url.is_not(None),
                ArtifactAcquisition.id.is_(None),
            )
        ).all()
        for version, _document in rows:
            assert version.source_url is not None
            self.session.add(
                ArtifactAcquisition(
                    case_id=self.case.id,
                    document_version_id=version.id,
                    official_url=require_official(version.source_url),
                    status="pending",
                    available_at=now,
                )
            )
        self.session.flush()
        return len(rows)

    def claim(
        self,
        owner: str,
        *,
        limit: int = 10,
        lease_seconds: int = 300,
        now: datetime | None = None,
    ) -> list[ArtifactAcquisition]:
        if not owner.strip():
            raise ValueError("lease owner is required")
        if limit < 1 or lease_seconds < 1:
            raise ValueError("limit and lease_seconds must be positive")
        now = now or datetime.now(UTC)
        rows = list(
            self.session.scalars(
                select(ArtifactAcquisition)
                .where(
                    ArtifactAcquisition.case_id == self.case.id,
                    ArtifactAcquisition.attempt_count < ArtifactAcquisition.max_attempts,
                    or_(
                        (
                            (ArtifactAcquisition.status == "pending")
                            & (ArtifactAcquisition.available_at <= now)
                        ),
                        (
                            (ArtifactAcquisition.status == "leased")
                            & (ArtifactAcquisition.lease_expires_at < now)
                        ),
                    ),
                )
                .order_by(ArtifactAcquisition.available_at, ArtifactAcquisition.created_at)
                .with_for_update(skip_locked=True)
                .limit(limit)
            ).all()
        )
        for row in rows:
            row.status = "leased"
            row.lease_owner = owner
            row.lease_expires_at = now + timedelta(seconds=lease_seconds)
            row.attempt_count += 1
        self.session.flush()
        return rows

    def complete(self, row: ArtifactAcquisition, owner: str) -> None:
        self._require_lease(row, owner)
        row.status = "captured"
        row.lease_owner = None
        row.lease_expires_at = None
        row.last_failure_class = None
        row.last_error = None
        self.session.flush()

    def fail(
        self,
        row: ArtifactAcquisition,
        owner: str,
        *,
        failure_class: str,
        error: str,
        retryable: bool,
        now: datetime | None = None,
    ) -> None:
        self._require_lease(row, owner)
        now = now or datetime.now(UTC)
        row.last_failure_class = failure_class[:64]
        row.last_error = error
        row.lease_owner = None
        row.lease_expires_at = None
        if failure_class == "access_control":
            # ADR-011: never retry a challenge in an attempt to evade it.
            row.status = "blocked"
        elif retryable and row.attempt_count < row.max_attempts:
            row.status = "pending"
            row.available_at = now + timedelta(seconds=min(3600, 30 * 2 ** (row.attempt_count - 1)))
        else:
            row.status = "failed"
        self.session.flush()

    @staticmethod
    def _require_lease(row: ArtifactAcquisition, owner: str) -> None:
        if row.status != "leased" or row.lease_owner != owner:
            raise ValueError("acquisition is not leased by this owner")

    def browser_plan(self, *, limit: int = 100) -> list[AcquisitionPlanItem]:
        rows = self.session.execute(
            select(ArtifactAcquisition, DocumentVersion, Document)
            .join(DocumentVersion, DocumentVersion.id == ArtifactAcquisition.document_version_id)
            .join(Document, Document.id == DocumentVersion.document_id)
            .where(
                ArtifactAcquisition.case_id == self.case.id,
                ArtifactAcquisition.status.in_(("pending", "blocked", "failed")),
                Document.visibility.in_(PUBLIC_VISIBILITIES),
                DocumentVersion.visibility.in_(PUBLIC_VISIBILITIES),
            )
            .order_by(Document.official_ref, DocumentVersion.official_version_ref)
            .limit(limit)
        ).all()
        return [
            AcquisitionPlanItem(
                queue_id=str(queue.id),
                official_ref=document.official_ref,
                official_version_ref=version.official_version_ref,
                official_url=queue.official_url,
                attempt_count=queue.attempt_count,
            )
            for queue, version, document in rows
        ]


class AutomatedAcquirer:
    """Consume one bounded queue lease batch with a pluggable official adapter."""

    def __init__(
        self,
        sessions: sessionmaker[Session],
        store: ObjectStore,
        *,
        case_number: str,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.sessions = sessions
        self.store = store
        self.case_number = case_number
        self.clock = clock or (lambda: datetime.now(UTC))

    def run_batch(
        self,
        adapter: AcquisitionAdapter,
        *,
        owner: str,
        batch_size: int = 10,
        lease_seconds: int = 300,
    ) -> AcquisitionBatchResult:
        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise LookupError(f"case {self.case_number} is not seeded")
            queue = AcquisitionQueue(session, case)
            queue.enqueue_missing(now=self.clock())
            claimed = queue.claim(
                owner, limit=batch_size, lease_seconds=lease_seconds, now=self.clock()
            )
            claimed_ids = [row.id for row in claimed]
            session.commit()

        fetched = blocked = failed = quarantined = 0
        for acquisition_id in claimed_ids:
            try:
                artifact = self._fetch_one(adapter, acquisition_id, owner)
            except AccessControlBlockedError as exc:
                self._fail(
                    acquisition_id,
                    owner,
                    failure_class="access_control",
                    error=exc.evidence,
                    retryable=False,
                )
                blocked += 1
            except FetchError as exc:
                self._fail(
                    acquisition_id,
                    owner,
                    failure_class="network",
                    error=str(exc),
                    retryable=True,
                )
                failed += 1
            except (UnsupportedArtifactError, ValueError) as exc:
                self._quarantine(acquisition_id, owner, type(exc).__name__, str(exc))
                quarantined += 1
            else:
                fetched += int(artifact)
        return AcquisitionBatchResult(
            claimed=len(claimed_ids),
            fetched=fetched,
            blocked=blocked,
            failed=failed,
            quarantined=quarantined,
        )

    def _fetch_one(
        self, adapter: AcquisitionAdapter, acquisition_id: uuid.UUID, owner: str
    ) -> bool:
        with self.sessions() as session:
            acquisition = session.get(ArtifactAcquisition, acquisition_id)
            if acquisition is None:
                raise ValueError("acquisition row disappeared")
            AcquisitionQueue._require_lease(acquisition, owner)
            official_url = acquisition.official_url

        artifact = adapter.fetch(official_url)
        info = inspect(artifact.body)

        with self.sessions() as session:
            acquisition = session.get(ArtifactAcquisition, acquisition_id)
            if acquisition is None:
                raise ValueError("acquisition row disappeared")
            AcquisitionQueue._require_lease(acquisition, owner)
            version = session.get(DocumentVersion, acquisition.document_version_id)
            if version is None:
                raise ValueError("document version disappeared")
            document = session.get(Document, version.document_id)
            case = session.get(Case, acquisition.case_id)
            if document is None or case is None:
                raise ValueError("acquisition provenance disappeared")
            if document.visibility not in PUBLIC_VISIBILITIES or version.visibility not in (
                PUBLIC_VISIBILITIES
            ):
                raise ValueError("version is no longer explicitly public")
            if require_official(version.source_url or "") != official_url:
                raise ValueError("official artifact URL changed while leased")
            if info.case_numbers_on_first_page and case.case_number not in (
                info.case_numbers_on_first_page
            ):
                raise ValueError(
                    f"artifact first page names {', '.join(info.case_numbers_on_first_page)}, "
                    f"not {case.case_number}"
                )
            if version.artifact_status == ArtifactStatus.FETCHED:
                if version.sha256 != info.sha256:
                    raise ValueError("immutable version already holds different bytes")
                AcquisitionQueue(session, case).complete(acquisition, owner)
                session.commit()
                return False
            duplicate = session.scalar(
                select(DocumentVersion.id).where(
                    DocumentVersion.sha256 == info.sha256,
                    DocumentVersion.id != version.id,
                )
            )
            if duplicate is not None:
                raise ValueError(f"artifact bytes already belong to version {duplicate}")
            key = storage_key(case.case_number, version.official_version_ref, info.sha256)
            self.store.put(key, artifact.body, info.mime_type)
            version.artifact_status = ArtifactStatus.FETCHED
            version.storage_key = key
            version.sha256 = info.sha256
            version.mime_type = info.mime_type
            version.byte_size = info.byte_size
            version.page_count = info.page_count
            version.fetched_at = artifact.fetched_at
            version.fetch_method = artifact.method
            AcquisitionQueue(session, case).complete(acquisition, owner)
            session.add(
                AuditLog(
                    actor=f"worker:acquisition:{owner}",
                    action="artifact.acquired",
                    entity_type="document_version",
                    entity_id=str(version.id),
                    detail={
                        "official_version_ref": version.official_version_ref,
                        "sha256": info.sha256,
                        "byte_size": info.byte_size,
                        "fetch_method": artifact.method,
                    },
                )
            )
            session.commit()
            return True

    def _fail(
        self,
        acquisition_id: uuid.UUID,
        owner: str,
        *,
        failure_class: str,
        error: str,
        retryable: bool,
    ) -> None:
        with self.sessions() as session:
            acquisition = session.get(ArtifactAcquisition, acquisition_id)
            if acquisition is None:
                return
            case = session.get(Case, acquisition.case_id)
            assert case is not None
            AcquisitionQueue(session, case).fail(
                acquisition,
                owner,
                failure_class=failure_class,
                error=error,
                retryable=retryable,
                now=self.clock(),
            )
            session.commit()

    def _quarantine(
        self, acquisition_id: uuid.UUID, owner: str, reason_code: str, reason: str
    ) -> None:
        with self.sessions() as session:
            acquisition = session.get(ArtifactAcquisition, acquisition_id)
            if acquisition is None:
                return
            AcquisitionQueue._require_lease(acquisition, owner)
            acquisition.status = "quarantined"
            acquisition.lease_owner = None
            acquisition.lease_expires_at = None
            acquisition.last_failure_class = reason_code[:64]
            acquisition.last_error = reason
            session.add(
                ArtifactQuarantine(
                    case_id=acquisition.case_id,
                    document_version_id=acquisition.document_version_id,
                    reason_code=reason_code[:64],
                    reason=reason,
                    state="open",
                )
            )
            session.commit()


def write_browser_plan(items: list[AcquisitionPlanItem], path: Path, *, case_number: str) -> None:
    payload = {
        "schema_version": 1,
        "case_number": case_number,
        "purpose": "operator_browser_capture",
        "instructions": "Use a normal authorized browser session; do not automate or bypass access controls.",
        "items": [item.__dict__ for item in items],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
