"""Document, DocumentVersion, DocumentPage, DocumentSection, DocumentChunk.

A `Document` is the logical filing / decision / transcript / exhibit record.
A `DocumentVersion` is one specific publicly available artifact of it
(original, public redacted, corrected, …). Bytes, hashes and page counts live
on the version; a public-redacted or corrected version is never overwritten by
another version.

Design rules carried by these models:
- `document_date`, `filing_date` and `public_date` are separate columns and are
  never merged (DESIGN_DECISIONS.md §7). None is inferred from another.
- `official_ref` is the record's own identifier (e.g. KSC-BC-2020-06/F01234)
  and is what routes and citations use; the UUID is internal only.
- Page numbers are stored only when known and are unique per version.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.case import Case
from ksc_api.models.enums import (
    ArtifactStatus,
    DocumentVersionType,
    Party,
    TextExtractionMethod,
    Visibility,
    db_enum,
)
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ksc_api.models.citation import Citation


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
    # Full official reference, e.g. "KSC-BC-2020-06/F01234".
    official_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    # Bare filing number, e.g. "F01234", for citation resolution lookups.
    filing_number: Mapped[str | None] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    # Free-form record classification (filing, decision, judgment, transcript,
    # exhibit, …). Constrained at the service layer, not the schema, so real
    # KSC vocabulary discovered in Phase 7 does not need a migration.
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16))
    filing_party: Mapped[Party | None] = mapped_column(db_enum(Party, name="party"))

    document_date: Mapped[date | None] = mapped_column(Date)
    filing_date: Mapped[date | None] = mapped_column(Date)
    public_date: Mapped[date | None] = mapped_column(Date)

    visibility: Mapped[Visibility] = mapped_column(
        db_enum(Visibility, name="visibility"),
        nullable=False,
        default=Visibility.PUBLIC,
        server_default=Visibility.PUBLIC.value,
    )
    ingestion_state: Mapped[DocumentIngestionState] = mapped_column(
        db_enum(DocumentIngestionState, name="document_ingestion_state"),
        nullable=False,
        default=DocumentIngestionState.DISCOVERED,
    )
    # Official public URL the logical record was discovered at. Never guessed.
    source_url: Mapped[str | None] = mapped_column(String(1024))

    case: Mapped[Case] = relationship(back_populates="documents")
    versions: Mapped[list[DocumentVersion]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.created_at",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Document {self.official_ref}>"


class DocumentVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "official_version_ref", name="uq_document_versions_document_ref"
        ),
        # One stored artifact per hash. A second version with identical bytes is
        # a duplicate, not a new version.
        Index(
            "uq_document_versions_sha256",
            "sha256",
            unique=True,
            postgresql_where="sha256 IS NOT NULL",
        ),
        CheckConstraint("page_count IS NULL OR page_count >= 0", name="page_count_non_negative"),
        CheckConstraint(
            "supersedes_version_id IS NULL OR supersedes_version_id <> id", name="no_self_supersede"
        ),
        # Bytes are held exactly when the version is FETCHED; a metadata-only
        # version (NOT_FETCHED) carries the official URLs and nothing else.
        CheckConstraint(
            "(artifact_status = 'fetched') = (sha256 IS NOT NULL AND storage_key IS NOT NULL)",
            name="fetched_has_hash_and_object",
        ),
        CheckConstraint("byte_size IS NULL OR byte_size >= 0", name="byte_size_non_negative"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The version's own public identifier, e.g. "F01234/RED" or "F01234/COR".
    official_version_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    version_type: Mapped[DocumentVersionType] = mapped_column(
        db_enum(DocumentVersionType, name="document_version_type"), nullable=False
    )
    version_label: Mapped[str | None] = mapped_column(String(64))
    visibility: Mapped[Visibility] = mapped_column(
        db_enum(Visibility, name="visibility"),
        nullable=False,
        default=Visibility.PUBLIC,
        server_default=Visibility.PUBLIC.value,
    )
    public_date: Mapped[date | None] = mapped_column(Date)

    # Provenance of the bytes held for this version — only ever from official
    # public URLs (docs/SECURITY.md). `source_url` is the official artifact URL
    # and is recorded even when the bytes have not been fetched.
    source_url: Mapped[str | None] = mapped_column(String(1024))
    artifact_status: Mapped[ArtifactStatus] = mapped_column(
        db_enum(ArtifactStatus, name="artifact_status"),
        nullable=False,
        default=ArtifactStatus.NOT_FETCHED,
        server_default=ArtifactStatus.NOT_FETCHED.value,
    )
    storage_key: Mapped[str | None] = mapped_column(String(512))
    sha256: Mapped[str | None] = mapped_column(String(64))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    byte_size: Mapped[int | None] = mapped_column(BigInteger)
    page_count: Mapped[int | None] = mapped_column(Integer)
    # When and how the bytes were obtained (e.g. "operator_browser_capture",
    # "http"). Discovery provenance lives on `source_records`.
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetch_method: Mapped[str | None] = mapped_column(String(64))
    text_extraction_method: Mapped[TextExtractionMethod] = mapped_column(
        db_enum(TextExtractionMethod, name="text_extraction_method"),
        nullable=False,
        default=TextExtractionMethod.NONE,
        server_default=TextExtractionMethod.NONE.value,
    )
    supersedes_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL")
    )

    document: Mapped[Document] = relationship(back_populates="versions")
    supersedes: Mapped[DocumentVersion | None] = relationship(remote_side="DocumentVersion.id")
    pages: Mapped[list[DocumentPage]] = relationship(
        back_populates="version", cascade="all, delete-orphan", order_by="DocumentPage.page_number"
    )
    sections: Mapped[list[DocumentSection]] = relationship(
        back_populates="version", cascade="all, delete-orphan", order_by="DocumentSection.sequence"
    )
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="version", cascade="all, delete-orphan", order_by="DocumentChunk.sequence"
    )
    citations_targeting: Mapped[list[Citation]] = relationship(
        foreign_keys="Citation.target_document_version_id", viewonly=True
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<DocumentVersion {self.official_version_ref}>"


class DocumentPage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_pages"
    __table_args__ = (
        UniqueConstraint(
            "document_version_id", "page_number", name="uq_document_pages_version_page"
        ),
        CheckConstraint("page_number >= 1", name="page_number_positive"),
    )

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False
    )
    # The real printed page number. Stored only when known.
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    running_head: Mapped[str | None] = mapped_column(String(512))
    has_redactions: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Extents of redaction on the page as published, e.g. [{"kind": "name", "extent": "2 lines"}].
    # Describes the public artifact; never a reconstruction.
    redaction_extents: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)

    version: Mapped[DocumentVersion] = relationship(back_populates="pages")


class DocumentSection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_sections"
    __table_args__ = (
        UniqueConstraint(
            "document_version_id", "sequence", name="uq_document_sections_version_sequence"
        ),
        CheckConstraint("level >= 0", name="level_non_negative"),
        CheckConstraint(
            "para_to IS NULL OR para_from IS NULL OR para_to >= para_from", name="para_range"
        ),
        CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from", name="page_range"
        ),
    )

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False
    )
    parent_section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_sections.id", ondelete="CASCADE")
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    heading: Mapped[str] = mapped_column(Text, nullable=False)
    page_from: Mapped[int | None] = mapped_column(Integer)
    page_to: Mapped[int | None] = mapped_column(Integer)
    para_from: Mapped[int | None] = mapped_column(Integer)
    para_to: Mapped[int | None] = mapped_column(Integer)

    version: Mapped[DocumentVersion] = relationship(back_populates="sections")
    parent: Mapped[DocumentSection | None] = relationship(remote_side="DocumentSection.id")


class DocumentChunk(UUIDPrimaryKeyMixin, Base):
    """Structural retrieval unit (paragraph / section span), prepared for later
    search. No embedding is generated in Phase 6; an embedding column is added
    by the phase that generates them."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_version_id", "sequence", name="uq_document_chunks_version_sequence"
        ),
        CheckConstraint(
            "para_to IS NULL OR para_from IS NULL OR para_to >= para_from", name="para_range"
        ),
        CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from", name="page_range"
        ),
    )

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_sections.id", ondelete="SET NULL")
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    page_from: Mapped[int | None] = mapped_column(Integer)
    page_to: Mapped[int | None] = mapped_column(Integer)
    para_from: Mapped[int | None] = mapped_column(Integer)
    para_to: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    version: Mapped[DocumentVersion] = relationship(back_populates="chunks")
