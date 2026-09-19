"""IngestionJob — schema foundation only. No job runs in Phase 6."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ksc_api.db.base import Base
from ksc_api.models.enums import IngestionJobStatus, SourceSystem, db_enum
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
