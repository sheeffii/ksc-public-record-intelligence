"""Version-specific PDF geometry and reusable research-object source anchors."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.enums import SourcePrecision, TextExtractionMethod, db_enum
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PageTextGeometry(UUIDPrimaryKeyMixin, Base):
    """One native/OCR word box in canonical top-left PDF-point coordinates."""

    __tablename__ = "page_text_geometry"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_version_id", "pdf_page_index"],
            ["document_pages.document_version_id", "document_pages.pdf_page_index"],
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "document_version_id", "pdf_page_index", "sequence", name="uq_page_geometry_sequence"
        ),
        CheckConstraint("pdf_page_index >= 0", name="pdf_page_index_non_negative"),
        CheckConstraint("sequence >= 0", name="sequence_non_negative"),
        CheckConstraint("char_start >= 0 AND char_end > char_start", name="char_range"),
        CheckConstraint(
            "x >= 0 AND y >= 0 AND width > 0 AND height > 0", name="positive_rectangle"
        ),
        CheckConstraint(
            "extraction_state IN ('usable', 'review_required')", name="extraction_state_allowed"
        ),
        Index("ix_page_text_geometry_version_page", "document_version_id", "pdf_page_index"),
    )

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False
    )
    pdf_page_index: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_basis: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="page_geometry_text",
        server_default="page_geometry_text",
    )
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    x: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    y: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    width: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    height: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    extraction_method: Mapped[TextExtractionMethod] = mapped_column(
        db_enum(TextExtractionMethod, name="text_extraction_method"), nullable=False
    )
    extraction_state: Mapped[str] = mapped_column(String(24), nullable=False)


class SourceSpan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable coordinate into one exact public document version."""

    __tablename__ = "source_spans"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_version_id", "pdf_page_index"],
            ["document_pages.document_version_id", "document_pages.pdf_page_index"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "pdf_page_index IS NULL OR pdf_page_index >= 0", name="pdf_page_index_non_negative"
        ),
        CheckConstraint("page_number IS NULL OR page_number >= 1", name="page_number_positive"),
        CheckConstraint(
            "char_start IS NULL OR (char_end IS NOT NULL AND char_end >= char_start)",
            name="char_range",
        ),
        CheckConstraint(
            "line_to IS NULL OR (line_from IS NOT NULL AND line_to >= line_from)", name="line_range"
        ),
        CheckConstraint(
            "state IN ('verified', 'review_required', 'unavailable')", name="state_allowed"
        ),
        Index("ix_source_spans_version_page", "document_version_id", "pdf_page_index"),
    )

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False
    )
    pdf_page_index: Mapped[int | None] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer)
    paragraph_number: Mapped[int | None] = mapped_column(Integer)
    transcript_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcript_segments.id", ondelete="CASCADE")
    )
    line_from: Mapped[int | None] = mapped_column(Integer)
    line_to: Mapped[int | None] = mapped_column(Integer)
    exact_text: Mapped[str | None] = mapped_column(Text)
    text_basis: Mapped[str | None] = mapped_column(String(32))
    char_start: Mapped[int | None] = mapped_column(Integer)
    char_end: Mapped[int | None] = mapped_column(Integer)
    extraction_method: Mapped[TextExtractionMethod] = mapped_column(
        db_enum(TextExtractionMethod, name="text_extraction_method"), nullable=False
    )
    extractor_version: Mapped[str] = mapped_column(String(32), nullable=False)
    precision: Mapped[SourcePrecision] = mapped_column(
        db_enum(SourcePrecision, name="source_precision"), nullable=False, index=True
    )
    state: Mapped[str] = mapped_column(String(24), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(128))
    processing_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("processing_runs.id", ondelete="SET NULL")
    )
    regions: Mapped[list[SourceRegion]] = relationship(
        back_populates="span", cascade="all, delete-orphan", order_by="SourceRegion.sequence"
    )
    anchors: Mapped[list[SourceAnchor]] = relationship(
        back_populates="span", cascade="all, delete-orphan"
    )


class SourceRegion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "source_regions"
    __table_args__ = (
        UniqueConstraint("source_span_id", "sequence", name="uq_source_regions_span_sequence"),
        CheckConstraint("sequence >= 0", name="sequence_non_negative"),
        CheckConstraint(
            "x >= 0 AND y >= 0 AND width > 0 AND height > 0", name="positive_rectangle"
        ),
    )

    source_span_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_spans.id", ondelete="CASCADE"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    x: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    y: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    width: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    height: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    coordinate_space: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pdf_points_top_left",
        server_default="pdf_points_top_left",
    )
    span: Mapped[SourceSpan] = relationship(back_populates="regions")


class SourceAnchor(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A typed research object binding to one reusable SourceSpan."""

    __tablename__ = "source_anchors"
    __table_args__ = (
        UniqueConstraint(
            "object_type", "object_id", "anchor_role", name="uq_source_anchors_object_role"
        ),
        CheckConstraint(
            "object_type IN ('entity_occurrence','citation','relationship','finding')",
            name="object_type_allowed",
        ),
    )

    source_span_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_spans.id", ondelete="CASCADE"), nullable=False
    )
    object_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    object_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    anchor_role: Mapped[str] = mapped_column(String(32), nullable=False)
    # Snapshot of the source object's state. This is intentionally not the
    # reviewable VerificationMixin field: the authoritative object remains the
    # only place a human verification state/reviewer can be changed.
    source_verification_state: Mapped[str] = mapped_column(String(32), nullable=False)
    span: Mapped[SourceSpan] = relationship(back_populates="anchors")
