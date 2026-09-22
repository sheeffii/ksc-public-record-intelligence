"""Lawfully public external media, kept structurally outside the court record."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VerificationMixin,
    human_verification_requires_reviewer,
)

if TYPE_CHECKING:
    from ksc_api.models.actor import Person
    from ksc_api.models.citation import Citation
    from ksc_api.models.document import Document
    from ksc_api.models.evidence import Exhibit, Finding


COURT_MEDIA_STATUSES = (
    "external_only",
    "mentioned",
    "tendered",
    "admitted",
    "rejected",
    "discussed",
    "relied_upon",
    "unknown",
)
COMPARISON_CLASSES = (
    "possible_contradiction",
    "qualification",
    "timeline_difference",
    "consistent",
    "not_comparable",
)


class ExternalSource(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "external_sources"
    __table_args__ = (
        UniqueConstraint("case_id", "canonical_url", name="uq_external_sources_case_url"),
        CheckConstraint("visibility = 'public'", name="public_only"),
        CheckConstraint(
            "access_method IN ('manual_url', 'public_webpage', 'official_api', 'operator_capture')",
            name="access_method_allowed",
        ),
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    account: Mapped[str | None] = mapped_column(String(255))
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, default="public")
    access_method: Mapped[str] = mapped_column(String(32), nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    terms_note: Mapped[str] = mapped_column(Text, nullable=False)
    coverage_note: Mapped[str] = mapped_column(Text, nullable=False)

    items: Mapped[list[MediaItem]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class MediaItem(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "media_items"
    __table_args__ = (
        UniqueConstraint("case_id", "canonical_url", name="uq_media_items_case_url"),
        CheckConstraint(
            "access_status IN ('public', 'restricted', 'rejected')", name="access_status_allowed"
        ),
        CheckConstraint(
            "item_kind IN ('original', 'repost', 'clip', 'embedded')", name="item_kind_allowed"
        ),
        CheckConstraint(
            "captured_at >= published_at OR published_at IS NULL",
            name="capture_not_before_publication",
        ),
        CheckConstraint("access_status = 'public'", name="held_items_public_only"),
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    external_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("external_sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    transcript_origin: Mapped[str | None] = mapped_column(String(64))
    item_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    archive_url: Mapped[str | None] = mapped_column(String(2048))
    access_status: Mapped[str] = mapped_column(String(16), nullable=False)
    captured_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_metadata: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)

    source: Mapped[ExternalSource] = relationship(back_populates="items")
    statements: Mapped[list[MediaStatement]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="MediaStatement.sequence"
    )
    court_links: Mapped[list[CourtMediaLink]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class MediaStatement(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "media_statements"
    __table_args__ = (
        UniqueConstraint("media_item_id", "sequence", name="uq_media_statements_item_sequence"),
        CheckConstraint("sequence >= 1", name="sequence_positive"),
        CheckConstraint("char_from IS NULL OR char_from >= 0", name="char_from_non_negative"),
        CheckConstraint("char_to IS NULL OR char_to > char_from", name="char_range_valid"),
        CheckConstraint(
            "timecode_start_ms IS NULL OR timecode_start_ms >= 0", name="timecode_non_negative"
        ),
        human_verification_requires_reviewer(),
    )

    media_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(nullable=False)
    speaker: Mapped[str | None] = mapped_column(String(255))
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    exact_quote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    char_from: Mapped[int | None]
    char_to: Mapped[int | None]
    timecode_start_ms: Mapped[int | None] = mapped_column(BigInteger)
    timecode_end_ms: Mapped[int | None] = mapped_column(BigInteger)
    transcript_origin: Mapped[str | None] = mapped_column(String(64))

    item: Mapped[MediaItem] = relationship(back_populates="statements")
    person: Mapped[Person | None] = relationship()


class CourtMediaLink(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "court_media_links"
    __table_args__ = (
        UniqueConstraint(
            "media_item_id",
            "court_status",
            "citation_id",
            name="uq_court_media_links_status_citation",
        ),
        CheckConstraint(f"court_status IN {COURT_MEDIA_STATUSES!r}", name="court_status_allowed"),
        CheckConstraint(
            "court_status IN ('external_only', 'unknown') OR citation_id IS NOT NULL",
            name="court_status_requires_citation",
        ),
        CheckConstraint(
            "court_status IN ('external_only', 'unknown') OR verification_state = 'human_verified'",
            name="court_status_requires_human_verification",
        ),
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    media_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    court_status: Mapped[str] = mapped_column(String(24), nullable=False)
    citation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="RESTRICT"), index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="RESTRICT")
    )
    exhibit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exhibits.id", ondelete="RESTRICT")
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="RESTRICT")
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)

    item: Mapped[MediaItem] = relationship(back_populates="court_links")
    citation: Mapped[Citation | None] = relationship()
    document: Mapped[Document | None] = relationship()
    exhibit: Mapped[Exhibit | None] = relationship()
    finding: Mapped[Finding | None] = relationship()


class MediaStatementComparison(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "media_statement_comparisons"
    __table_args__ = (
        UniqueConstraint(
            "case_id", "comparison_key", name="uq_media_statement_comparisons_case_key"
        ),
        CheckConstraint(f"classification IN {COMPARISON_CLASSES!r}", name="classification_allowed"),
        CheckConstraint(
            "statement_b_id IS NOT NULL OR court_citation_b_id IS NOT NULL",
            name="second_source_required",
        ),
        CheckConstraint(
            "NOT (statement_b_id IS NOT NULL AND court_citation_b_id IS NOT NULL)",
            name="second_source_exactly_one_kind",
        ),
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    comparison_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    statement_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_statements.id", ondelete="RESTRICT"), nullable=False
    )
    statement_b_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_statements.id", ondelete="RESTRICT")
    )
    court_citation_b_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="RESTRICT")
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_origin: Mapped[str] = mapped_column(String(64), nullable=False)

    statement_a: Mapped[MediaStatement] = relationship(foreign_keys=[statement_a_id])
    statement_b: Mapped[MediaStatement | None] = relationship(foreign_keys=[statement_b_id])
    court_citation_b: Mapped[Citation | None] = relationship()
