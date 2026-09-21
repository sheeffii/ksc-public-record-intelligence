"""Neutral appellate/review research objects with exact-source provenance.

These rows organise research questions; they never establish legal error or
predict an outcome. Every affirmative source relationship points to a
persisted citation. Missing material is represented separately and never
silently converted into a claim that the Court ignored it.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VerificationMixin,
    human_verification_requires_reviewer,
)

if TYPE_CHECKING:
    from ksc_api.models.ai import AiRun
    from ksc_api.models.citation import Citation
    from ksc_api.models.evidence import Argument, Finding, FindingEvidenceLink


ISSUE_CATEGORIES = (
    "error_of_law",
    "error_of_fact",
    "sentencing",
    "procedural_fairness",
    "evidence_assessment",
    "reasoning",
    "disclosure",
    "legal_standard",
    "causation",
    "mode_of_liability",
    "other",
)


class AppealIssue(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """A source-backed question for human review, never a concluded ground."""

    __tablename__ = "appeal_issues"
    __table_args__ = (
        UniqueConstraint("case_id", "issue_key", name="uq_appeal_issues_case_key"),
        CheckConstraint(f"category IN {ISSUE_CATEGORIES!r}", name="category_allowed"),
        CheckConstraint(
            "context IN ('legal', 'factual', 'sentencing', 'procedural', 'other')",
            name="context_allowed",
        ),
        CheckConstraint(
            "court_treatment IN ('addressed', 'accepted', 'rejected', 'distinguished', "
            "'qualified', 'not_located', 'unresolved')",
            name="court_treatment_allowed",
        ),
        CheckConstraint(
            "red_team_result IN ('supported_for_review', 'qualified', 'countered', "
            "'insufficient_record')",
            name="red_team_result_allowed",
        ),
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    issue_key: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    context: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    court_treatment: Mapped[str] = mapped_column(String(24), nullable=False)
    court_treatment_note: Mapped[str] = mapped_column(Text, nullable=False)
    red_team_result: Mapped[str] = mapped_column(String(32), nullable=False)
    extraction_origin: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    finding: Mapped[Finding] = relationship()
    sources: Mapped[list[AppealIssueSource]] = relationship(
        back_populates="issue", cascade="all, delete-orphan", order_by="AppealIssueSource.sequence"
    )
    missing_material: Mapped[list[AppealMissingMaterial]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )
    red_team_reviews: Mapped[list[RedTeamReview]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )


class AppealIssueSource(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """One exact source relationship supporting an issue research structure."""

    __tablename__ = "appeal_issue_sources"
    __table_args__ = (
        UniqueConstraint("issue_id", "sequence", name="uq_appeal_issue_sources_sequence"),
        CheckConstraint("sequence >= 1", name="sequence_positive"),
        CheckConstraint(
            "role IN ('court_reasoning', 'applicable_standard', 'evidence_relied', "
            "'defence_position', 'spo_position', 'court_response', 'supporting', "
            "'contrary', 'qualifying')",
            name="role_allowed",
        ),
        CheckConstraint(
            "source_category IN ('court_finding', 'spo_argument', 'defence_argument', "
            "'witness_testimony', 'document_exhibit', 'court_response', 'public_authority')",
            name="source_category_allowed",
        ),
        human_verification_requires_reviewer(),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appeal_issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    source_category: Mapped[str] = mapped_column(String(32), nullable=False)
    citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    argument_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("arguments.id", ondelete="RESTRICT")
    )
    finding_evidence_link_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("finding_evidence_links.id", ondelete="RESTRICT")
    )
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    issue: Mapped[AppealIssue] = relationship(back_populates="sources")
    citation: Mapped[Citation] = relationship()
    argument: Mapped[Argument | None] = relationship()
    finding_evidence_link: Mapped[FindingEvidenceLink | None] = relationship()


class AppealMissingMaterial(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "appeal_missing_material"
    __table_args__ = (
        UniqueConstraint("issue_id", "reference", name="uq_appeal_missing_material_reference"),
        CheckConstraint(
            "state IN ('source_unavailable', 'court_treatment_not_located', 'unresolved')",
            name="state_allowed",
        ),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appeal_issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reference: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)

    issue: Mapped[AppealIssue] = relationship(back_populates="missing_material")


class StatementComparison(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """A comparison of two exact public passages; never a credibility finding."""

    __tablename__ = "statement_comparisons"
    __table_args__ = (
        UniqueConstraint("case_id", "comparison_key", name="uq_statement_comparisons_case_key"),
        CheckConstraint(
            "classification IN ('possible_contradiction', 'qualification', "
            "'timeline_difference', 'consistent', 'not_comparable')",
            name="classification_allowed",
        ),
        CheckConstraint(
            "comparison_type IN ('witness_statement_testimony', 'testimony_testimony', "
            "'party_filing_court_summary', 'court_characterization_source', 'source_source')",
            name="comparison_type_allowed",
        ),
        CheckConstraint(
            "statement_a_citation_id <> statement_b_citation_id", name="distinct_sources"
        ),
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    comparison_key: Mapped[str] = mapped_column(String(64), nullable=False)
    issue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appeal_issues.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    comparison_type: Mapped[str] = mapped_column(String(40), nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)
    statement_a_citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="RESTRICT"), nullable=False
    )
    statement_b_citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="RESTRICT"), nullable=False
    )
    statement_a_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    statement_b_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    statement_a_speaker: Mapped[str | None] = mapped_column(String(128))
    statement_b_speaker: Mapped[str | None] = mapped_column(String(128))
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_origin: Mapped[str] = mapped_column(String(64), nullable=False)

    issue: Mapped[AppealIssue | None] = relationship()
    statement_a_citation: Mapped[Citation] = relationship(foreign_keys=[statement_a_citation_id])
    statement_b_citation: Mapped[Citation] = relationship(foreign_keys=[statement_b_citation_id])


class RedTeamReview(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "red_team_reviews"
    __table_args__ = (
        CheckConstraint(
            "result IN ('supported_for_review', 'qualified', 'countered', 'insufficient_record')",
            name="result_allowed",
        ),
        CheckConstraint("origin IN ('human', 'ai_assisted')", name="origin_allowed"),
        CheckConstraint(
            "(origin = 'ai_assisted') = (ai_run_id IS NOT NULL)", name="ai_origin_matches_run"
        ),
        human_verification_requires_reviewer(),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appeal_issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    ai_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_runs.id", ondelete="RESTRICT")
    )

    issue: Mapped[AppealIssue] = relationship(back_populates="red_team_reviews")
    ai_run: Mapped[AiRun | None] = relationship()
    findings: Mapped[list[RedTeamFinding]] = relationship(
        back_populates="review", cascade="all, delete-orphan", order_by="RedTeamFinding.sequence"
    )


class RedTeamFinding(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "red_team_findings"
    __table_args__ = (
        UniqueConstraint("review_id", "sequence", name="uq_red_team_findings_sequence"),
        CheckConstraint("sequence >= 1", name="sequence_positive"),
        CheckConstraint(
            "perspective IN ('defence_analyst', 'spo_red_team', 'neutral_reviewer')",
            name="perspective_allowed",
        ),
        CheckConstraint(
            "category IN ('unsupported', 'missing_citation', 'ignored_evidence', 'unanswered', "
            "'factual_dispute', 'legal_question', 'well_supported', 'human_required', "
            "'counter_material', 'source_limitation')",
            name="category_allowed",
        ),
        CheckConstraint(
            "citation_id IS NOT NULL OR category IN "
            "('missing_citation', 'legal_question', 'human_required', 'source_limitation')",
            name="uncited_only_for_explicit_gap",
        ),
        human_verification_requires_reviewer(),
    )

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("red_team_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(nullable=False)
    perspective: Mapped[str] = mapped_column(String(24), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    citation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="RESTRICT")
    )

    review: Mapped[RedTeamReview] = relationship(back_populates="findings")
    citation: Mapped[Citation | None] = relationship()
