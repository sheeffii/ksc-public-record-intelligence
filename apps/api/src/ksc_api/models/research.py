"""ResearchNote — human notes, stored apart from court evidence and labelled
as human provenance. A note stores its source set (citations), not rendered
text from those sources."""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.citation import Citation
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

HUMAN_PROVENANCE = "human"


class ResearchNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_notes"
    __table_args__ = (
        CheckConstraint(f"provenance = '{HUMAN_PROVENANCE}'", name="provenance_is_human"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="SET NULL"), index=True
    )
    author: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[str] = mapped_column(
        String(16), nullable=False, default=HUMAN_PROVENANCE, server_default=HUMAN_PROVENANCE
    )

    citations: Mapped[list[Citation]] = relationship(secondary="research_note_citations")


class ResearchNoteCitation(Base):
    __tablename__ = "research_note_citations"

    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_notes.id", ondelete="CASCADE"), primary_key=True
    )
    citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="RESTRICT"), primary_key=True
    )
