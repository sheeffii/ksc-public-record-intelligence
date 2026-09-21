"""Case-scoped Phase 12 appeal research over canonical, reviewed records."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ksc_api.models import (
    AppealIssue,
    AppealIssueSource,
    Citation,
    RedTeamFinding,
    RedTeamReview,
    ResearchNote,
    ResolutionState,
    StatementComparison,
    VerificationState,
)
from ksc_api.models.case import Case
from ksc_api.repositories import mappers
from ksc_api.repositories.records import CITATION_LOAD
from ksc_api.schemas.appeal import (
    AppealCoverageRead,
    AppealIssueDetail,
    AppealIssueSummary,
    AppealSourceRead,
    AppealWorkspaceRead,
    ArgumentLabRead,
    CitationAuditRead,
    MissingMaterialRead,
    RedTeamFindingRead,
    RedTeamReviewRead,
    ResearchNoteCreate,
    StatementComparisonRead,
)

_LIMITATIONS = [
    "The controlled corpus does not contain the public Trial Judgment.",
    "The underlying Defence filing F03743 is not held in the controlled corpus.",
    "The underlying SPO filing F03746 is not held in the controlled corpus.",
    "The benchmark is a narrow Court decision review workflow, not a merits appeal analysis.",
]


class AppealResearchService:
    def __init__(self, session: Session, case: Case) -> None:
        self.session = session
        self.case = case

    @staticmethod
    def _summary(issue: AppealIssue) -> AppealIssueSummary:
        return AppealIssueSummary(
            id=issue.id,
            issue_key=issue.issue_key,
            category=issue.category,
            context=issue.context,
            title=issue.title,
            description=issue.description,
            finding_key=issue.finding.finding_key,
            para_from=issue.finding.para_from,
            para_to=issue.finding.para_to,
            court_treatment=issue.court_treatment,
            court_treatment_note=issue.court_treatment_note,
            red_team_result=issue.red_team_result,
            verification_state=issue.verification_state,
            verified_by=issue.verified_by,
            verified_at=issue.verified_at,
        )

    def _issues(self) -> list[AppealIssue]:
        return list(
            self.session.scalars(
                select(AppealIssue)
                .options(selectinload(AppealIssue.finding))
                .where(
                    AppealIssue.case_id == self.case.id,
                    AppealIssue.verification_state != VerificationState.HUMAN_REJECTED,
                )
                .order_by(AppealIssue.finding_id, AppealIssue.issue_key)
            ).all()
        )

    def workspace(
        self, *, category: str | None = None, verification_state: VerificationState | None = None
    ) -> AppealWorkspaceRead:
        issues = self._issues()
        filtered = [
            issue
            for issue in issues
            if (category is None or issue.category == category)
            and (verification_state is None or issue.verification_state == verification_state)
        ]
        issue_ids = [issue.id for issue in issues]
        source_rows = (
            list(
                self.session.scalars(
                    select(AppealIssueSource).where(AppealIssueSource.issue_id.in_(issue_ids))
                ).all()
            )
            if issue_ids
            else []
        )
        comparisons = int(
            self.session.scalar(
                select(func.count())
                .select_from(StatementComparison)
                .where(StatementComparison.case_id == self.case.id)
            )
            or 0
        )
        reviews = (
            int(
                self.session.scalar(
                    select(func.count())
                    .select_from(RedTeamReview)
                    .where(RedTeamReview.issue_id.in_(issue_ids))
                )
                or 0
            )
            if issue_ids
            else 0
        )
        citations = [row.citation_id for row in source_rows]
        resolved = (
            int(
                self.session.scalar(
                    select(func.count())
                    .select_from(Citation)
                    .where(
                        Citation.id.in_(citations),
                        Citation.resolution_state == ResolutionState.RESOLVED,
                    )
                )
                or 0
            )
            if citations
            else 0
        )
        verified_relationships = sum(
            row.verification_state == VerificationState.HUMAN_VERIFIED for row in source_rows
        )
        return AppealWorkspaceRead(
            issues=[self._summary(issue) for issue in filtered],
            coverage=AppealCoverageRead(
                issues=len(issues),
                source_backed_links=len(source_rows),
                statement_comparisons=comparisons,
                red_team_reviews=reviews,
                citations_resolved=resolved,
                citations_unresolved=len(citations) - resolved,
                human_verified_relationships=verified_relationships,
                needs_more_evidence=sum(
                    issue.verification_state == VerificationState.NEEDS_MORE_EVIDENCE
                    for issue in issues
                ),
            ),
            corpus_limitations=_LIMITATIONS,
        )

    def _load_issue(self, issue_key: str) -> AppealIssue | None:
        return self.session.scalar(
            select(AppealIssue)
            .options(
                selectinload(AppealIssue.finding),
                selectinload(AppealIssue.sources)
                .selectinload(AppealIssueSource.citation)
                .options(*CITATION_LOAD),
                selectinload(AppealIssue.missing_material),
                selectinload(AppealIssue.red_team_reviews)
                .selectinload(RedTeamReview.findings)
                .selectinload(RedTeamFinding.citation)
                .options(*CITATION_LOAD),
            )
            .where(
                AppealIssue.case_id == self.case.id,
                AppealIssue.issue_key == issue_key,
                AppealIssue.verification_state != VerificationState.HUMAN_REJECTED,
            )
        )

    @staticmethod
    def _comparison_read(row: StatementComparison) -> StatementComparisonRead:
        return StatementComparisonRead(
            id=row.id,
            comparison_key=row.comparison_key,
            issue_key=row.issue.issue_key if row.issue is not None else None,
            title=row.title,
            comparison_type=row.comparison_type,
            classification=row.classification,
            statement_a_excerpt=row.statement_a_excerpt,
            statement_b_excerpt=row.statement_b_excerpt,
            statement_a_speaker=row.statement_a_speaker,
            statement_b_speaker=row.statement_b_speaker,
            statement_a_citation=mappers.to_citation(row.statement_a_citation),
            statement_b_citation=mappers.to_citation(row.statement_b_citation),
            explanation=row.explanation,
            verification_state=row.verification_state,
            verified_by=row.verified_by,
            verified_at=row.verified_at,
        )

    @staticmethod
    def _red_finding(row: RedTeamFinding) -> RedTeamFindingRead:
        return RedTeamFindingRead(
            sequence=row.sequence,
            perspective=row.perspective,
            category=row.category,
            text=row.text,
            verification_state=row.verification_state,
            citation=mappers.to_citation(row.citation) if row.citation is not None else None,
        )

    @staticmethod
    def _audit(issue: AppealIssue, comparisons: list[StatementComparison]) -> CitationAuditRead:
        citations = [source.citation for source in issue.sources]
        citations.extend(
            c
            for review in issue.red_team_reviews
            for finding in review.findings
            if (c := finding.citation) is not None
        )
        citations.extend(
            c
            for comparison in comparisons
            for c in (comparison.statement_a_citation, comparison.statement_b_citation)
        )
        unique = {citation.id: citation for citation in citations}
        unresolved = sum(c.resolution_state != ResolutionState.RESOLVED for c in unique.values())
        unverified_sources = sum(
            source.verification_state != VerificationState.HUMAN_VERIFIED
            for source in issue.sources
        )
        issues = [f"{unresolved} citation(s) do not resolve."] if unresolved else []
        if unverified_sources:
            issues.append(f"{unverified_sources} source relationship(s) are not human verified.")
        issues.extend(
            f"Missing source: {item.reference}. {item.reason}" for item in issue.missing_material
        )
        ready = not unresolved and not unverified_sources and not issue.missing_material
        return CitationAuditRead(
            citations_total=len(unique),
            citations_resolved=len(unique) - unresolved,
            quotes_verified=sum(
                c.verification_state == VerificationState.HUMAN_VERIFIED for c in unique.values()
            ),
            sources_human_verified=sum(
                source.verification_state == VerificationState.HUMAN_VERIFIED
                for source in issue.sources
            ),
            unresolved=unresolved,
            unsupported_relationships=unverified_sources,
            ready_for_human_review=ready,
            issues=issues,
        )

    def comparisons(self, *, issue_id: uuid.UUID | None = None) -> list[StatementComparisonRead]:
        stmt = (
            select(StatementComparison)
            .options(
                selectinload(StatementComparison.issue),
                selectinload(StatementComparison.statement_a_citation).options(*CITATION_LOAD),
                selectinload(StatementComparison.statement_b_citation).options(*CITATION_LOAD),
            )
            .where(
                StatementComparison.case_id == self.case.id,
                StatementComparison.verification_state != VerificationState.HUMAN_REJECTED,
            )
            .order_by(StatementComparison.comparison_key)
        )
        if issue_id is not None:
            stmt = stmt.where(StatementComparison.issue_id == issue_id)
        return [self._comparison_read(row) for row in self.session.scalars(stmt).all()]

    def get_issue(self, issue_key: str) -> AppealIssueDetail | None:
        issue = self._load_issue(issue_key)
        if issue is None:
            return None
        comparison_rows = list(
            self.session.scalars(
                select(StatementComparison)
                .options(
                    selectinload(StatementComparison.issue),
                    selectinload(StatementComparison.statement_a_citation).options(*CITATION_LOAD),
                    selectinload(StatementComparison.statement_b_citation).options(*CITATION_LOAD),
                )
                .where(StatementComparison.issue_id == issue.id)
            ).all()
        )
        return AppealIssueDetail(
            **self._summary(issue).model_dump(),
            notes=issue.notes,
            sources=[
                AppealSourceRead(
                    id=source.id,
                    sequence=source.sequence,
                    role=source.role,
                    source_category=source.source_category,
                    excerpt=source.excerpt,
                    note=source.note,
                    verification_state=source.verification_state,
                    citation=mappers.to_citation(source.citation),
                )
                for source in issue.sources
            ],
            missing_material=[
                MissingMaterialRead.model_validate(item) for item in issue.missing_material
            ],
            statement_comparisons=[self._comparison_read(row) for row in comparison_rows],
            red_team_reviews=[
                RedTeamReviewRead(
                    id=review.id,
                    result=review.result,
                    summary=review.summary,
                    origin=review.origin,
                    verification_state=review.verification_state,
                    findings=[self._red_finding(finding) for finding in review.findings],
                )
                for review in issue.red_team_reviews
            ],
            citation_audit=self._audit(issue, comparison_rows),
        )

    def argument_lab(self, issue_key: str) -> ArgumentLabRead | None:
        issue = self._load_issue(issue_key)
        if issue is None:
            return None
        comparisons_rows = list(
            self.session.scalars(
                select(StatementComparison)
                .options(
                    selectinload(StatementComparison.statement_a_citation).options(*CITATION_LOAD),
                    selectinload(StatementComparison.statement_b_citation).options(*CITATION_LOAD),
                )
                .where(StatementComparison.issue_id == issue.id)
            ).all()
        )
        defence = next(
            (source for source in issue.sources if source.role == "defence_position"), None
        )
        draft_citations = [
            source.citation for source in issue.sources if source.citation.is_resolved
        ]
        draft = defence.excerpt if defence is not None else issue.description
        return ArgumentLabRead(
            issue=self._summary(issue),
            draft_title=issue.title,
            draft_text=draft,
            draft_citations=[mappers.to_citation(c) for c in draft_citations],
            unsupported_sentences=[],
            citation_audit=self._audit(issue, comparisons_rows),
            stages=[
                self._red_finding(finding)
                for review in issue.red_team_reviews
                for finding in review.findings
            ],
            result=issue.red_team_result,
            notice=(
                "The neutral reviewer reports record gaps and counter-material. It does not "
                "declare a winner or predict how any court would receive the issue."
            ),
        )

    def update_review_state(
        self, issue_key: str, state: VerificationState, reviewer: str
    ) -> AppealIssueSummary | None:
        issue = self.session.scalar(
            select(AppealIssue)
            .options(selectinload(AppealIssue.finding))
            .where(AppealIssue.case_id == self.case.id, AppealIssue.issue_key == issue_key)
        )
        if issue is None:
            return None
        issue.verification_state = state
        issue.verified_by = (
            reviewer
            if state in {VerificationState.HUMAN_VERIFIED, VerificationState.HUMAN_REJECTED}
            else None
        )
        issue.verified_at = datetime.now(UTC) if issue.verified_by else None
        self.session.commit()
        return self._summary(issue)

    def save_note(self, issue_key: str, payload: ResearchNoteCreate) -> ResearchNote:
        issue = self._load_issue(issue_key)
        if issue is None:
            raise LookupError("appeal issue not found")
        allowed = {
            source.citation_id: source.citation
            for source in issue.sources
            if source.citation.is_resolved
        }
        if not payload.citation_ids or any(
            citation_id not in allowed for citation_id in payload.citation_ids
        ):
            raise ValueError("every note citation must be a resolved source linked to this issue")
        note = ResearchNote(
            case_id=self.case.id,
            finding_id=issue.finding_id,
            appeal_issue_id=issue.id,
            author=payload.author,
            title=payload.title,
            body=payload.body,
            provenance="human",
        )
        note.citations = [allowed[citation_id] for citation_id in payload.citation_ids]
        self.session.add(note)
        self.session.commit()
        return note
