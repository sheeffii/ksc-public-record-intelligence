"""Phase 12 controlled-corpus quality gate (read-only, no network access)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.models import (
    AppealIssue,
    AppealIssueSource,
    Case,
    Finding,
    FindingEvidenceLink,
    RedTeamFinding,
    RedTeamReview,
    ResolutionState,
    StatementComparison,
    VerificationState,
)
from ksc_api.services.appeal_research import AppealResearchService


@dataclass(frozen=True)
class Phase12GateReport:
    generated_at: str
    case_number: str
    issues: int
    source_backed_links: int
    comparisons: int
    red_team_reviews: int
    red_team_findings: int
    resolved_citations: int
    unresolved_citations: int
    source_navigation: int
    human_verified_relationships: int
    needs_more_evidence: int
    abstentions: int
    unsupported_relationships_rejected: int
    missing_sources: list[str]
    authoritative_fingerprint_before: str
    authoritative_fingerprint_after: str
    authoritative_records_unchanged: bool
    trial_judgment_present: bool
    passed: bool


def _fingerprint(session: Session, case_id: object) -> str:
    findings = session.scalars(select(Finding).where(Finding.case_id == case_id)).all()
    payload: dict[str, Any] = {
        "findings": sorted(
            (row.finding_key, row.text, row.verification_state.value) for row in findings
        ),
        "links": sorted(
            (
                str(row.id),
                str(row.finding_id),
                str(row.citation_id),
                row.link_type.value,
                row.verification_state.value,
            )
            for row in session.scalars(select(FindingEvidenceLink)).all()
        ),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def run_phase12_gate(session: Session, *, case_number: str, generated_at: str) -> Phase12GateReport:
    case = session.scalar(select(Case).where(Case.case_number == case_number))
    if case is None:
        raise RuntimeError(f"case {case_number} is not seeded")
    before = _fingerprint(session, case.id)
    service = AppealResearchService(session, case)
    workspace = service.workspace()
    issues = session.scalars(select(AppealIssue).where(AppealIssue.case_id == case.id)).all()
    issue_ids = [issue.id for issue in issues]
    sources = session.scalars(
        select(AppealIssueSource).where(AppealIssueSource.issue_id.in_(issue_ids))
    ).all()
    comparisons = session.scalars(
        select(StatementComparison).where(StatementComparison.case_id == case.id)
    ).all()
    reviews = session.scalars(
        select(RedTeamReview).where(RedTeamReview.issue_id.in_(issue_ids))
    ).all()
    review_ids = [review.id for review in reviews]
    findings = session.scalars(
        select(RedTeamFinding).where(RedTeamFinding.review_id.in_(review_ids))
    ).all()
    details = [service.get_issue(issue.issue_key) for issue in issues]
    if any(detail is None for detail in details):
        raise RuntimeError("canonical issue could not be read through the public service")
    material = [detail for detail in details if detail is not None]
    unique_citations = {source.citation.id: source.citation for source in sources}
    for comparison in comparisons:
        unique_citations[comparison.statement_a_citation.id] = comparison.statement_a_citation
        unique_citations[comparison.statement_b_citation.id] = comparison.statement_b_citation
    for finding in findings:
        if finding.citation is not None:
            unique_citations[finding.citation.id] = finding.citation
    resolved = sum(
        citation.resolution_state == ResolutionState.RESOLVED
        for citation in unique_citations.values()
    )
    navigation = sum(
        citation.resolution_state == ResolutionState.RESOLVED
        and (
            citation.target_document_id is not None
            or citation.target_document_version_id is not None
            or citation.target_transcript_id is not None
        )
        for citation in unique_citations.values()
    )
    missing = sorted(item.reference for detail in material for item in detail.missing_material)
    after = _fingerprint(session, case.id)
    trial_judgment_present = bool(
        session.scalar(
            select(Finding.id)
            .join(Finding.judgment_document)
            .where(
                Finding.case_id == case.id, Finding.judgment_document.has(document_type="judgment")
            )
            .limit(1)
        )
    )
    human_verified = (
        sum(source.verification_state == VerificationState.HUMAN_VERIFIED for source in sources)
        + sum(
            comparison.verification_state == VerificationState.HUMAN_VERIFIED
            for comparison in comparisons
        )
        + sum(
            finding.verification_state == VerificationState.HUMAN_VERIFIED for finding in findings
        )
    )
    needs_more = sum(
        issue.verification_state == VerificationState.NEEDS_MORE_EVIDENCE for issue in issues
    )
    abstentions = sum(review.result == "insufficient_record" for review in reviews)
    unsupported = sum(detail.citation_audit.unsupported_relationships for detail in material)
    passed = all(
        [
            len(issues) == 1,
            len(sources) == 5,
            len(comparisons) == 1,
            len(reviews) == 1,
            len(findings) == 4,
            resolved == len(unique_citations),
            navigation == len(unique_citations),
            needs_more == 1,
            abstentions == 1,
            unsupported == 0,
            all(not detail.citation_audit.ready_for_human_review for detail in material),
            set(missing)
            == {
                "F03743",
                "F03746",
                "pre-correction SPO Final Trial Brief",
                "public Trial Judgment",
            },
            before == after,
            not trial_judgment_present,
            workspace.coverage.issues == 1,
        ]
    )
    return Phase12GateReport(
        generated_at=generated_at,
        case_number=case_number,
        issues=len(issues),
        source_backed_links=len(sources),
        comparisons=len(comparisons),
        red_team_reviews=len(reviews),
        red_team_findings=len(findings),
        resolved_citations=resolved,
        unresolved_citations=len(unique_citations) - resolved,
        source_navigation=navigation,
        human_verified_relationships=human_verified,
        needs_more_evidence=needs_more,
        abstentions=abstentions,
        unsupported_relationships_rejected=unsupported,
        missing_sources=missing,
        authoritative_fingerprint_before=before,
        authoritative_fingerprint_after=after,
        authoritative_records_unchanged=before == after,
        trial_judgment_present=trial_judgment_present,
        passed=passed,
    )


def write_phase12_report(report: Phase12GateReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n")
