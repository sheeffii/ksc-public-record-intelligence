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
    Boolean,
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
    question: Mapped[str | None] = mapped_column(Text)
    system_prompt_sha256: Mapped[str | None] = mapped_column(String(64))
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    structured_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    validation_errors: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    answer_withheld: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    insufficient_evidence: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
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

    prompt_version: Mapped[PromptVersion | None] = relationship()
    outputs: Mapped[list[AiOutput]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="AiOutput.sequence"
    )
    retrieval_sources: Mapped[list[AiRetrievalSource]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AiRetrievalSource.rank",
    )


class AiOutput(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """One answer block. Block order comes from the API; clients never reorder."""

    __tablename__ = "ai_outputs"
    __table_args__ = (
        UniqueConstraint("ai_run_id", "sequence", name="uq_ai_outputs_run_sequence"),
        CheckConstraint("unresolved_citation_count >= 0", name="unresolved_count_non_negative"),
        CheckConstraint(
            "content_type IN ('verbatim_quote', 'source_paraphrase', 'ai_analysis', 'abstention')",
            name="content_type_allowed",
        ),
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
    content_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="source_paraphrase", server_default="source_paraphrase"
    )
    claim_key: Mapped[str | None] = mapped_column(String(128))
    # Blocks depending on an unresolved citation are withheld by the API.
    unresolved_citation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    run: Mapped[AiRun] = relationship(back_populates="outputs")
    citations: Mapped[list[Citation]] = relationship(secondary="ai_output_citations")
    sources: Mapped[list[AiRetrievalSource]] = relationship(secondary="ai_output_sources")


class AiOutputCitation(Base):
    __tablename__ = "ai_output_citations"

    ai_output_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_outputs.id", ondelete="CASCADE"), primary_key=True
    )
    citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="RESTRICT"), primary_key=True
    )


class AiRetrievalSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One ranked, immutable source snapshot supplied to an AI run.

    Retrieval sources are not evidence relationships. They preserve the exact
    public source coordinate and text the provider was allowed to see.
    """

    __tablename__ = "ai_retrieval_sources"
    __table_args__ = (
        UniqueConstraint("ai_run_id", "rank", name="uq_ai_retrieval_sources_run_rank"),
        CheckConstraint("rank >= 1", name="rank_positive"),
        CheckConstraint("retrieval_score >= 0", name="retrieval_score_non_negative"),
        CheckConstraint(
            "source_category IN ('court_finding', 'witness_testimony', 'spo_argument', "
            "'defence_argument', 'document_exhibit', 'court_response', 'human_note')",
            name="source_category_allowed",
        ),
        CheckConstraint(
            "source_visibility IN ('public', 'public_redacted', 'private_authorized')",
            name="source_visibility_allowed",
        ),
        CheckConstraint(
            "num_nonnulls(document_paragraph_id, document_chunk_id, transcript_segment_id, "
            "finding_id, argument_id, research_note_id) = 1",
            name="exactly_one_source_anchor",
        ),
        CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from", name="page_range"
        ),
        CheckConstraint(
            "para_to IS NULL OR para_from IS NULL OR para_to >= para_from", name="para_range"
        ),
        CheckConstraint(
            "line_to IS NULL OR line_from IS NULL OR line_to >= line_from", name="line_range"
        ),
        CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') "
            "OR (verification_reviewed_by IS NOT NULL AND verification_reviewed_at IS NOT NULL)",
            name="human_verification_has_reviewer",
        ),
    )

    ai_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    retrieval_method: Mapped[str] = mapped_column(String(32), nullable=False)
    retrieval_score: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    source_category: Mapped[str] = mapped_column(String(32), nullable=False)
    source_visibility: Mapped[str] = mapped_column(String(32), nullable=False)
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    version_ref: Mapped[str | None] = mapped_column(String(128))
    display: Mapped[str] = mapped_column(String(255), nullable=False)
    target_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    page_from: Mapped[int | None] = mapped_column(Integer)
    page_to: Mapped[int | None] = mapped_column(Integer)
    pdf_page_index: Mapped[int | None] = mapped_column(Integer)
    para_from: Mapped[int | None] = mapped_column(Integer)
    para_to: Mapped[int | None] = mapped_column(Integer)
    line_from: Mapped[int | None] = mapped_column(Integer)
    line_to: Mapped[int | None] = mapped_column(Integer)
    verification_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unreviewed", server_default="unreviewed"
    )
    verification_reviewed_by: Mapped[str | None] = mapped_column(String(128))
    verification_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="RESTRICT"), index=True
    )
    document_paragraph_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_paragraphs.id", ondelete="RESTRICT")
    )
    document_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="RESTRICT")
    )
    transcript_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcript_segments.id", ondelete="RESTRICT")
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="RESTRICT")
    )
    argument_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("arguments.id", ondelete="RESTRICT")
    )
    research_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_notes.id", ondelete="RESTRICT")
    )
    citation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="RESTRICT")
    )

    run: Mapped[AiRun] = relationship(back_populates="retrieval_sources")


class AiOutputSource(Base):
    __tablename__ = "ai_output_sources"

    ai_output_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_outputs.id", ondelete="CASCADE"), primary_key=True
    )
    retrieval_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_retrieval_sources.id", ondelete="CASCADE"),
        primary_key=True,
    )
