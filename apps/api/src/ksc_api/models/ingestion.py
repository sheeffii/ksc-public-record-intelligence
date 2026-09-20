"""IngestionJob and IngestionJobItem.

A job is one run over one source (a captured bundle, a live probe, …). Every
record the run touches becomes an item with a terminal status, so failures are
visible rows rather than log lines, and a re-run can resume by skipping items
that already reached a terminal state.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.enums import IngestionItemStatus, IngestionJobStatus, SourceSystem, db_enum
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class IngestionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        CheckConstraint(
            "discovered_count >= 0 AND downloaded_count >= 0 AND processed_count >= 0 "
            "AND failed_count >= 0",
            name="counts_non_negative",
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_system: Mapped[SourceSystem] = mapped_column(
        db_enum(SourceSystem, name="source_system"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[IngestionJobStatus] = mapped_column(
        db_enum(IngestionJobStatus, name="ingestion_job_status"),
        nullable=False,
        default=IngestionJobStatus.PENDING,
        server_default=IngestionJobStatus.PENDING.value,
    )
    # Resumable position in the source listing and last durable checkpoint.
    cursor: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    checkpoint: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    discovered_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    downloaded_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    processed_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    failed_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_summary: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list[IngestionJobItem]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="IngestionJobItem.sequence"
    )


class IngestionJobItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ingestion_job_items"
    __table_args__ = (
        UniqueConstraint("job_id", "item_key", name="uq_ingestion_job_items_job_key"),
        CheckConstraint("sequence >= 0", name="sequence_non_negative"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingestion_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Stable key of the record within the source (external record id / URL).
    item_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[IngestionItemStatus] = mapped_column(
        db_enum(IngestionItemStatus, name="ingestion_item_status"),
        nullable=False,
        default=IngestionItemStatus.PENDING,
        server_default=IngestionItemStatus.PENDING.value,
    )
    reason: Mapped[str | None] = mapped_column(Text)
    # Identifiers, URLs, hashes and per-artifact outcomes — never document text
    # (docs/SECURITY.md logging rule).
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_records.id", ondelete="SET NULL")
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL")
    )
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL")
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    job: Mapped[IngestionJob] = relationship(back_populates="items")
