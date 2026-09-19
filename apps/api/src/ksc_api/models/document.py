"""Document — a public court filing, decision, transcript or exhibit record.

Phase 4 creates the table only. No rows are ingested; no downloads occur.

Design rules carried by this model:
- `document_date` and `filing_date` are separate columns and are never merged
  (DESIGN_DECISIONS.md §7). Neither is inferred from the other.
- `official_ref` is the record's own identifier (e.g. KSC-BC-2020-06/F01234/RED)
  and is what routes and citations use; the UUID is internal only.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.case import Case
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DocumentPublicState(enum.StrEnum):
    """Availability of the text in the public record.

    `not_held` records that an identifier exists in the public record but the
    document itself is not public — the system states this rather than
    rendering a generic 404 (ROUTE_MAP.md §8).
    """

    PUBLIC = "public"
    PUBLIC_REDACTED = "public_redacted"
    NOT_HELD = "not_held"


class DocumentIngestionState(enum.StrEnum):
    DISCOVERED = "discovered"
    DOWNLOADED = "downloaded"
    PARSED = "parsed"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("case_id", "official_ref", name="uq_documents_case_official_ref"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Full official reference, e.g. "KSC-BC-2020-06/F01234/RED".
    official_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    # Bare filing number, e.g. "F01234", for citation resolution lookups.
    filing_number: Mapped[str | None] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    # Free-form record classification (filing, decision, judgment, transcript,
    # exhibit, …). Becomes a constrained vocabulary in the full schema.
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16))

    document_date: Mapped[date | None] = mapped_column(Date)
    filing_date: Mapped[date | None] = mapped_column(Date)

    public_state: Mapped[DocumentPublicState] = mapped_column(
        Enum(DocumentPublicState, name="document_public_state"),
        nullable=False,
        default=DocumentPublicState.PUBLIC,
    )
    ingestion_state: Mapped[DocumentIngestionState] = mapped_column(
        Enum(DocumentIngestionState, name="document_ingestion_state"),
        nullable=False,
        default=DocumentIngestionState.DISCOVERED,
    )

    # Provenance of the bytes we hold. Populated only by a later, controlled
    # ingestion phase — and only from official public URLs.
    source_url: Mapped[str | None] = mapped_column(String(1024))
    storage_key: Mapped[str | None] = mapped_column(String(512))
    sha256: Mapped[str | None] = mapped_column(String(64))
    page_count: Mapped[int | None] = mapped_column(Integer)

    case: Mapped[Case] = relationship(back_populates="documents")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Document {self.official_ref}>"
