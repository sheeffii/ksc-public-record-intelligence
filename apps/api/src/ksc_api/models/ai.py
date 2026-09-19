"""PromptVersion, AiRun, AiOutput — the audit schema for every future AI call.

No model is called in Phase 6. The tables exist so that when Phase 11 does
call one, provider, model, prompt hash, retrieval set, tokens, cost and every
output block are recorded, and so that no output can be promoted to a human
verification state without a named reviewer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.citation import Citation
from ksc_api.models.enums import AiRunStatus, AnswerBlockKind, db_enum
from ksc_api.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VerificationMixin,
    human_verification_requires_reviewer,
)


class PromptVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_prompt_versions_name_version"),)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    template_sha256: Mapped[str] = mapped_column(String(64), nullable=False)


class AiRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_runs"
    __table_args__ = (
        CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0", name="input_tokens_non_negative"
        ),
        CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0", name="output_tokens_non_negative"
        ),
    )

    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), index=True
    )
    prompt_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_versions.id", ondelete="RESTRICT")
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    status: Mapped[AiRunStatus] = mapped_column(
        db_enum(AiRunStatus, name="ai_run_status"),
        nullable=False,
        default=AiRunStatus.PENDING,
        server_default=AiRunStatus.PENDING.value,
    )
    requested_by: Mapped[str | None] = mapped_column(String(128))
    # Hash of the full rendered input; the input itself may contain source text
    # and is not stored here.
    input_sha256: Mapped[str | None] = mapped_column(String(64))
    # The retrieval set the answer was composed from: citation ids.
    retrieved_citation_ids: Mapped[list[str] | None] = mapped_column(JSONB)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    outputs: Mapped[list[AiOutput]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="AiOutput.sequence"
    )


class AiOutput(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """One answer block. Block order comes from the API; clients never reorder."""

    __tablename__ = "ai_outputs"
    __table_args__ = (
        UniqueConstraint("ai_run_id", "sequence", name="uq_ai_outputs_run_sequence"),
        CheckConstraint("unresolved_citation_count >= 0", name="unresolved_count_non_negative"),
        human_verification_requires_reviewer(),
    )

    ai_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[AnswerBlockKind] = mapped_column(
        db_enum(AnswerBlockKind, name="answer_block_kind"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Blocks depending on an unresolved citation are withheld by the API.
    unresolved_citation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    run: Mapped[AiRun] = relationship(back_populates="outputs")
    citations: Mapped[list[Citation]] = relationship(secondary="ai_output_citations")


class AiOutputCitation(Base):
    __tablename__ = "ai_output_citations"

    ai_output_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_outputs.id", ondelete="CASCADE"), primary_key=True
    )
    citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="RESTRICT"), primary_key=True
    )
