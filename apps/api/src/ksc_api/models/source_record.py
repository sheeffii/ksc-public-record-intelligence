"""SourceRecord — where a record was discovered, kept separate from what
normalized entity it became and from any stored file.

    Official KSC case page ──discovered hearing──▶ SourceRecord
    Public Court Records record ──official PDF──▶ SourceRecord ─▶ Document / Version
                                                                     └─▶ pages / citations

Nothing is fetched in Phase 6. The table exists so Phase 7 discovery can
persist provenance without a schema change.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ksc_api.db.base import Base
from ksc_api.models.enums import SourceSystem, Visibility, db_enum
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SourceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_records"
    __table_args__ = (
        UniqueConstraint(
            "case_id", "source_system", "external_record_id", name="uq_source_records_external"
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_system: Mapped[SourceSystem] = mapped_column(
        db_enum(SourceSystem, name="source_system"), nullable=False
    )
    # The source's own record key (a records-repository id, a hearing slug, …).
    external_record_id: Mapped[str] = mapped_column(String(256), nullable=False)
    record_type: Mapped[str] = mapped_column(String(64), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16))
    # Where it was seen versus the official canonical location, when different.
    discovery_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    canonical_source_url: Mapped[str | None] = mapped_column(String(1024))
    title: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[Visibility] = mapped_column(
        db_enum(Visibility, name="visibility"),
        nullable=False,
        default=Visibility.UNKNOWN,
        server_default=Visibility.UNKNOWN.value,
    )
    raw_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Optional resolution to normalized entities. All true foreign keys.
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL")
    )
    hearing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hearings.id", ondelete="SET NULL")
    )
    transcript_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="SET NULL")
    )
