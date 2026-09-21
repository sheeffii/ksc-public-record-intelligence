from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from ksc_api.models.enums import VerificationState
from ksc_api.schemas.citation import CitationRead
from ksc_api.schemas.common import ReadModel

IssueCategory = Literal[
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
]
CourtTreatment = Literal[
    "addressed",
    "accepted",
    "rejected",
    "distinguished",
    "qualified",
    "not_located",
    "unresolved",
]
RedTeamResult = Literal["supported_for_review", "qualified", "countered", "insufficient_record"]


class AppealSourceRead(ReadModel):
    id: uuid.UUID
    sequence: int = Field(ge=1)
    role: str
    source_category: str
    excerpt: str
    note: str | None
    verification_state: VerificationState
    citation: CitationRead


class MissingMaterialRead(ReadModel):
    reference: str
    kind: str
    reason: str
    state: str


class RedTeamFindingRead(ReadModel):
    sequence: int = Field(ge=1)
    perspective: str
    category: str
    text: str
    verification_state: VerificationState
    citation: CitationRead | None


class RedTeamReviewRead(ReadModel):
    id: uuid.UUID
    result: RedTeamResult
    summary: str
    origin: Literal["human", "ai_assisted"]
    verification_state: VerificationState
    findings: list[RedTeamFindingRead]


class CitationAuditRead(ReadModel):
    citations_total: int = Field(ge=0)
    citations_resolved: int = Field(ge=0)
    quotes_verified: int = Field(ge=0)
    sources_human_verified: int = Field(ge=0)
    unresolved: int = Field(ge=0)
    unsupported_relationships: int = Field(ge=0)
    ready_for_human_review: bool
    issues: list[str]


class AppealIssueSummary(ReadModel):
    id: uuid.UUID
    issue_key: str
    category: IssueCategory
    context: Literal["legal", "factual", "sentencing", "procedural", "other"]
    title: str
    description: str
    finding_key: str
    para_from: int
    para_to: int | None
    court_treatment: CourtTreatment
    court_treatment_note: str
    red_team_result: RedTeamResult
    verification_state: VerificationState
    verified_by: str | None
    verified_at: datetime | None


class AppealIssueDetail(AppealIssueSummary):
    notes: str | None
    sources: list[AppealSourceRead]
    missing_material: list[MissingMaterialRead]
    statement_comparisons: list[StatementComparisonRead]
    red_team_reviews: list[RedTeamReviewRead]
    citation_audit: CitationAuditRead


class AppealCoverageRead(ReadModel):
    issues: int = Field(ge=0)
    source_backed_links: int = Field(ge=0)
    statement_comparisons: int = Field(ge=0)
    red_team_reviews: int = Field(ge=0)
    citations_resolved: int = Field(ge=0)
    citations_unresolved: int = Field(ge=0)
    human_verified_relationships: int = Field(ge=0)
    needs_more_evidence: int = Field(ge=0)


class AppealWorkspaceRead(ReadModel):
    issues: list[AppealIssueSummary]
    coverage: AppealCoverageRead
    corpus_limitations: list[str]


class StatementComparisonRead(ReadModel):
    id: uuid.UUID
    comparison_key: str
    issue_key: str | None
    title: str
    comparison_type: str
    classification: Literal[
        "possible_contradiction",
        "qualification",
        "timeline_difference",
        "consistent",
        "not_comparable",
    ]
    statement_a_excerpt: str
    statement_b_excerpt: str
    statement_a_speaker: str | None
    statement_b_speaker: str | None
    statement_a_citation: CitationRead
    statement_b_citation: CitationRead
    explanation: str
    verification_state: VerificationState
    verified_by: str | None
    verified_at: datetime | None


class ArgumentLabRead(ReadModel):
    issue: AppealIssueSummary
    draft_title: str
    draft_text: str
    draft_citations: list[CitationRead]
    unsupported_sentences: list[str]
    citation_audit: CitationAuditRead
    stages: list[RedTeamFindingRead]
    result: RedTeamResult
    notice: str


class ReviewStateUpdate(ReadModel):
    verification_state: Literal["human_verified", "human_rejected", "needs_more_evidence"]
    reviewer: str = Field(min_length=1, max_length=128)


class ResearchNoteCreate(ReadModel):
    author: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1)
    citation_ids: list[uuid.UUID] = Field(min_length=1)


class ResearchNoteCreated(ReadModel):
    id: uuid.UUID
    provenance: Literal["human"]
