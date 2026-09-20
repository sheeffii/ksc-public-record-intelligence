"""Hearing → Transcript → TranscriptSegment, plus WitnessAppearance.

Segments carry the official transcript page and line coordinates only when
known. Lines are never invented; closed-session segments hold no text.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.enums import ExaminationType, TextExtractionMethod, Visibility, db_enum
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ksc_api.models.actor import Witness
    from ksc_api.models.document import DocumentVersion


class Hearing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hearings"
    __table_args__ = (
        UniqueConstraint(
            "case_id", "hearing_date", "session_sequence", name="uq_hearings_case_date_session"
        ),
        CheckConstraint("session_sequence >= 1", name="session_sequence_positive"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    hearing_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Sessions on the same day (morning / afternoon) in order.
    session_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    session_label: Mapped[str | None] = mapped_column(String(64))
    hearing_type: Mapped[str | None] = mapped_column(String(64))
    official_ref: Mapped[str | None] = mapped_column(String(128))
    source_url: Mapped[str | None] = mapped_column(String(1024))
    visibility: Mapped[Visibility] = mapped_column(
        db_enum(Visibility, name="visibility"),
        nullable=False,
        default=Visibility.PUBLIC,
        server_default=Visibility.PUBLIC.value,
    )

    transcripts: Mapped[list[Transcript]] = relationship(
        back_populates="hearing", cascade="all, delete-orphan"
    )
    appearances: Mapped[list[WitnessAppearance]] = relationship(
        back_populates="hearing", cascade="all, delete-orphan"
    )


class Transcript(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transcripts"
    __table_args__ = (
        Index(
            "uq_transcripts_document_version",
            "document_version_id",
            unique=True,
            postgresql_where="document_version_id IS NOT NULL",
        ),
        CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from", name="page_range"
        ),
    )

    hearing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hearings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The official transcript artifact, when held.
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL")
    )
    official_ref: Mapped[str | None] = mapped_column(String(128), index=True)
    language: Mapped[str | None] = mapped_column(String(16))
    visibility: Mapped[Visibility] = mapped_column(
        db_enum(Visibility, name="visibility"),
        nullable=False,
        default=Visibility.PUBLIC,
        server_default=Visibility.PUBLIC.value,
    )
    # Running transcript page range ("T. 4,226").
    page_from: Mapped[int | None] = mapped_column(Integer)
    page_to: Mapped[int | None] = mapped_column(Integer)
    text_extraction_method: Mapped[TextExtractionMethod] = mapped_column(
        db_enum(TextExtractionMethod, name="text_extraction_method"),
        nullable=False,
        default=TextExtractionMethod.NONE,
        server_default=TextExtractionMethod.NONE.value,
    )

    hearing: Mapped[Hearing] = relationship(back_populates="transcripts")
    document_version: Mapped[DocumentVersion | None] = relationship()
    segments: Mapped[list[TranscriptSegment]] = relationship(
        back_populates="transcript",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.sequence",
    )


class TranscriptSegment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (
        UniqueConstraint("transcript_id", "sequence", name="uq_transcript_segments_sequence"),
        CheckConstraint("sequence >= 0", name="sequence_non_negative"),
        CheckConstraint("page_number IS NULL OR page_number >= 1", name="page_number_positive"),
        CheckConstraint(
            "pdf_page_index IS NULL OR pdf_page_index >= 0", name="pdf_page_index_non_negative"
        ),
        CheckConstraint("line_from IS NULL OR line_from >= 1", name="line_from_positive"),
        CheckConstraint(
            "line_to IS NULL OR line_from IS NULL OR line_to >= line_from", name="line_range"
        ),
        CheckConstraint("line_to IS NULL OR line_from IS NOT NULL", name="line_to_needs_line_from"),
        # A closed-session segment records that content exists but is not
        # public; it carries no text.
        CheckConstraint("NOT closed_session OR text = ''", name="closed_session_has_no_text"),
        Index("ix_transcript_segments_search_vector", "search_vector", postgresql_using="gin"),
    )

    transcript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False
    )
    # Deterministic order within the transcript.
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    # Zero-based page index in the held PDF, distinct from the running
    # transcript page number below.
    pdf_page_index: Mapped[int | None] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer)
    line_from: Mapped[int | None] = mapped_column(Integer)
    line_to: Mapped[int | None] = mapped_column(Integer)
    speaker: Mapped[str | None] = mapped_column(String(255))
    speaker_role: Mapped[str | None] = mapped_column(String(64))
    witness_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("witnesses.id", ondelete="SET NULL"), index=True
    )
    examination_type: Mapped[ExaminationType] = mapped_column(
        db_enum(ExaminationType, name="examination_type"),
        nullable=False,
        default=ExaminationType.UNKNOWN,
        server_default=ExaminationType.UNKNOWN.value,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    closed_session: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('simple', coalesce(text, ''))", persisted=True),
        deferred=True,
    )

    transcript: Mapped[Transcript] = relationship(back_populates="segments")
    witness: Mapped[Witness | None] = relationship()


class WitnessAppearance(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "witness_appearances"
    __table_args__ = (
        UniqueConstraint("witness_id", "hearing_id", name="uq_witness_appearances_witness_hearing"),
        CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from", name="page_range"
        ),
    )

    witness_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("witnesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hearing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hearings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transcript_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="SET NULL")
    )
    # Testimony date is a date type of its own (DESIGN_DECISIONS.md §7).
    testimony_date: Mapped[date | None] = mapped_column(Date)
    page_from: Mapped[int | None] = mapped_column(Integer)
    page_to: Mapped[int | None] = mapped_column(Integer)

    witness: Mapped[Witness] = relationship(back_populates="appearances")
    hearing: Mapped[Hearing] = relationship(back_populates="appearances")
