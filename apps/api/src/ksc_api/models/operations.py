"""Phase 13 ingestion operations and immutable history.

These rows keep discovery, acquisition, quarantine and reprocessing state
separate from the authoritative evidence tables.  Operational failures can
therefore never become searchable source material by accident.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ksc_api.db.base import Base
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SourceRecordSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable representation of source metadata at one observation."""

    __tablename__ = "source_record_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "source_record_id", "metadata_sha256", name="uq_source_record_snapshots_hash"
        ),
    )

    source_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_payload: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False)


class ArtifactAcquisition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A retryable, lease-based request for one public artifact version."""

    __tablename__ = "artifact_acquisitions"
    __table_args__ = (
        UniqueConstraint("document_version_id", name="uq_artifact_acquisitions_version"),
        Index("ix_artifact_acquisitions_claim", "status", "available_at", "created_at"),
        CheckConstraint(
            "status IN ('pending','leased','captured','blocked','failed','quarantined')",
            name="status_allowed",
        ),
        CheckConstraint("attempt_count >= 0", name="attempt_count_non_negative"),
        CheckConstraint("max_attempts >= 1", name="max_attempts_positive"),
        CheckConstraint(
            "(status = 'leased') = (lease_owner IS NOT NULL AND lease_expires_at IS NOT NULL)",
            name="lease_matches_status",
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    official_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=4, server_default="4"
    )
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease_owner: Mapped[str | None] = mapped_column(String(128))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_class: Mapped[str | None] = mapped_column(String(64))
    last_error: Mapped[str | None] = mapped_column(Text)


class ArtifactQuarantine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Review queue for bytes or mappings refused by trusted processing."""

    __tablename__ = "artifact_quarantine"
    __table_args__ = (
        CheckConstraint("state IN ('open','released','rejected')", name="state_allowed"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), index=True
    )
    ingestion_job_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ingestion_job_items.id", ondelete="SET NULL")
    )
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_sha256: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    reviewed_by: Mapped[str | None] = mapped_column(String(128))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProcessingRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Auditable parser/resolver/projection invocation."""

    __tablename__ = "processing_runs"
    __table_args__ = (
        CheckConstraint("status IN ('running','completed','failed')", name="status_allowed"),
        CheckConstraint(
            "selected_count >= 0 AND processed_count >= 0 AND failed_count >= 0",
            name="counts_non_negative",
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    processor: Mapped[str] = mapped_column(String(64), nullable=False)
    processor_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="running")
    forced: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    selected_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    processed_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    failed_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
