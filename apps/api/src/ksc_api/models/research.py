"""Research notes stored apart from court evidence with explicit provenance.

A note stores its source set (citations), not rendered text from those sources.
AI-assisted notes retain the audited originating run and never become evidence.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.citation import Citation
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

HUMAN_PROVENANCE = "human"
AI_ASSISTED_PROVENANCE = "ai_assisted"


class ResearchNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_notes"
    __table_args__ = (
        CheckConstraint("provenance IN ('human', 'ai_assisted')", name="provenance_allowed"),
        CheckConstraint(
            "(provenance = 'ai_assisted') = (origin_ai_run_id IS NOT NULL)",
            name="ai_origin_matches_provenance",
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="SET NULL"), index=True
    )
    origin_ai_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_runs.id", ondelete="RESTRICT"), index=True
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
