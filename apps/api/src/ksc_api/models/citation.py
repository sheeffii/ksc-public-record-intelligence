"""Citation — the resolution index (ADR-005) — and RecordIdentifier, the
identifier/alias lookup foundation it will resolve against.

A citation row separates three things that are easy to conflate:

- the **source coordinate**: where the citing text appears
  (`source_document_version_id`, `source_page`, `source_para`,
  `source_transcript_segment_id`);
- the **raw / normalized text** of the reference itself;
- the **resolved target**: which record and which page / paragraph / line range
  it points at. Targets are true foreign keys; a citation that resolves to
  nothing keeps every target NULL and `resolution_state = unresolved`.

`display` is pre-formatted at resolution time so no client reconstructs a
citation string. For anything but RESOLVED it is the literal "UNRESOLVED".
Ambiguous references are never silently mapped: AMBIGUOUS keeps targets NULL.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.enums import (
    CitationType,
    EntityKind,
    IdentifierKind,
    ResolutionMethod,
    ResolutionState,
    db_enum,
)
from ksc_api.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VerificationMixin,
    human_verification_requires_reviewer,
)

if TYPE_CHECKING:
    from ksc_api.models.actor import Witness
    from ksc_api.models.document import Document, DocumentVersion
    from ksc_api.models.evidence import Exhibit, Finding
    from ksc_api.models.hearing import Transcript, TranscriptSegment

UNRESOLVED_DISPLAY = "UNRESOLVED"

_TARGET_COLUMNS = (
    "target_document_id",
    "target_document_version_id",
    "target_transcript_id",
    "target_transcript_segment_id",
    "target_exhibit_id",
    "target_witness_id",
    "target_finding_id",
)


class Citation(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "citations"
    __table_args__ = (
        # A resolved citation points at something; anything else points at nothing.
        CheckConstraint(
            "(resolution_state = 'resolved' AND num_nonnulls("
            + ", ".join(_TARGET_COLUMNS)
            + ") >= 1) OR (resolution_state <> 'resolved' AND num_nonnulls("
            + ", ".join(_TARGET_COLUMNS)
            + ") = 0)",
            name="targets_match_resolution_state",
        ),
        CheckConstraint(
            "resolution_state = 'resolved' OR display = 'UNRESOLVED'",
            name="unresolved_display_literal",
        ),
        CheckConstraint(
            "resolution_state <> 'resolved' OR resolved_at IS NOT NULL",
            name="resolved_has_timestamp",
        ),
        CheckConstraint(
            "resolution_confidence IS NULL OR "
            "(resolution_confidence >= 0 AND resolution_confidence <= 1)",
            name="confidence_unit_interval",
        ),
        CheckConstraint(
            "target_para_to IS NULL OR target_para_from IS NULL OR target_para_to >= target_para_from",
            name="para_range",
        ),
        CheckConstraint(
            "target_line_to IS NULL OR target_line_from IS NULL OR target_line_to >= target_line_from",
            name="line_range",
        ),
        CheckConstraint("target_page IS NULL OR target_page >= 1", name="target_page_positive"),
        CheckConstraint(
            "source_pdf_page_index IS NULL OR source_pdf_page_index >= 0",
            name="source_pdf_page_index_non_negative",
        ),
        CheckConstraint(
            "source_char_start IS NULL OR source_char_start >= 0",
            name="source_char_start_non_negative",
        ),
        CheckConstraint(
            "source_char_end IS NULL OR source_char_start IS NULL OR "
            "source_char_end >= source_char_start",
            name="source_char_range",
        ),
        CheckConstraint(
            "target_pdf_page_index IS NULL OR target_pdf_page_index >= 0",
            name="target_pdf_page_index_non_negative",
        ),
        human_verification_requires_reviewer(),
        Index("ix_citations_case_resolution", "case_id", "resolution_state"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(String(512), index=True)
    citation_type: Mapped[CitationType] = mapped_column(
        db_enum(CitationType, name="citation_type"),
        nullable=False,
        default=CitationType.UNKNOWN,
        server_default=CitationType.UNKNOWN.value,
    )

    # --- where the citing text appears -----------------------------------
    source_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), index=True
    )
    source_page: Mapped[int | None] = mapped_column(Integer)
    source_pdf_page_index: Mapped[int | None] = mapped_column(Integer)
    source_para: Mapped[int | None] = mapped_column(Integer)
    source_char_start: Mapped[int | None] = mapped_column(Integer)
    source_char_end: Mapped[int | None] = mapped_column(Integer)
    source_transcript_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcript_segments.id", ondelete="SET NULL")
    )
    source_url: Mapped[str | None] = mapped_column(String(1024))

    # --- what it resolves to ----------------------------------------------
    target_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )
    target_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), index=True
    )
    target_page: Mapped[int | None] = mapped_column(Integer)
    target_pdf_page_index: Mapped[int | None] = mapped_column(Integer)
    target_para_from: Mapped[int | None] = mapped_column(Integer)
    target_para_to: Mapped[int | None] = mapped_column(Integer)
    target_transcript_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="SET NULL"), index=True
    )
    target_transcript_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcript_segments.id", ondelete="SET NULL")
    )
    target_line_from: Mapped[int | None] = mapped_column(Integer)
    target_line_to: Mapped[int | None] = mapped_column(Integer)
    target_exhibit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exhibits.id", ondelete="SET NULL"), index=True
    )
    target_witness_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("witnesses.id", ondelete="SET NULL"), index=True
    )
    target_finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="SET NULL"), index=True
    )

    # --- resolution --------------------------------------------------------
    resolution_state: Mapped[ResolutionState] = mapped_column(
        db_enum(ResolutionState, name="resolution_state"),
        nullable=False,
        default=ResolutionState.UNRESOLVED,
        server_default=ResolutionState.UNRESOLVED.value,
    )
    resolution_method: Mapped[ResolutionMethod] = mapped_column(
        db_enum(ResolutionMethod, name="resolution_method"),
        nullable=False,
        default=ResolutionMethod.NONE,
        server_default=ResolutionMethod.NONE.value,
    )
    # Confidence of the *string resolution* (deterministic methods = 1.0).
    # This is never a statement about a person or about evidential weight.
    resolution_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    display: Mapped[str] = mapped_column(
        String(255), nullable=False, default=UNRESOLVED_DISPLAY, server_default=UNRESOLVED_DISPLAY
    )
    # Audit detail for every terminal state. Ambiguous candidates are stored
    # as identifiers only; no candidate is silently selected as the target.
    resolution_detail: Mapped[str | None] = mapped_column(Text)
    candidate_identifiers: Mapped[list[str] | None] = mapped_column(JSONB)

    target_document: Mapped[Document | None] = relationship(foreign_keys=[target_document_id])
    target_document_version: Mapped[DocumentVersion | None] = relationship(
        foreign_keys=[target_document_version_id]
    )
    target_transcript: Mapped[Transcript | None] = relationship(foreign_keys=[target_transcript_id])
    target_transcript_segment: Mapped[TranscriptSegment | None] = relationship(
        foreign_keys=[target_transcript_segment_id]
    )
    target_exhibit: Mapped[Exhibit | None] = relationship(foreign_keys=[target_exhibit_id])
    target_witness: Mapped[Witness | None] = relationship(foreign_keys=[target_witness_id])
    target_finding: Mapped[Finding | None] = relationship(foreign_keys=[target_finding_id])

    @property
    def is_resolved(self) -> bool:
        return self.resolution_state == ResolutionState.RESOLVED


class RecordIdentifier(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Identifier / alias → record. The persisted lookup the resolver will use.

    Each row maps exactly one identifier string (`F01234`, `F01234/RED`,
    `P00123`, `W01234`, …) to exactly one record through a real foreign key.
    Lookup by `(case_id, normalized_identifier)` yields 0 rows (UNRESOLVED),
    1 row (RESOLVED) or several (AMBIGUOUS — never auto-picked).
    """

    __tablename__ = "record_identifiers"
    __table_args__ = (
        UniqueConstraint(
            "case_id", "normalized_identifier", "entity_kind", name="uq_record_identifiers_lookup"
        ),
        CheckConstraint(
            "num_nonnulls(document_id, document_version_id, exhibit_id, witness_id, "
            "transcript_id, finding_id) = 1",
            name="exactly_one_target",
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    identifier: Mapped[str] = mapped_column(String(128), nullable=False)
    # Upper-cased, whitespace-collapsed form used for lookup.
    normalized_identifier: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    identifier_kind: Mapped[IdentifierKind] = mapped_column(
        db_enum(IdentifierKind, name="identifier_kind"), nullable=False
    )
    entity_kind: Mapped[EntityKind] = mapped_column(
        db_enum(EntityKind, name="entity_kind"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE")
    )
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE")
    )
    exhibit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exhibits.id", ondelete="CASCADE")
    )
    witness_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("witnesses.id", ondelete="CASCADE")
    )
    transcript_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="CASCADE")
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE")
    )


def normalize_identifier(raw: str) -> str:
    """Canonical lookup form: trimmed, single-spaced, upper-cased."""
    return " ".join(raw.split()).upper()
