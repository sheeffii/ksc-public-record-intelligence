from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import delete, select

from ksc_api.db.session import session_scope
from ksc_api.models import (
    AppealIssue,
    AppealIssueSource,
    AppealMissingMaterial,
    Citation,
    Finding,
    FindingEvidenceLink,
    RedTeamFinding,
    RedTeamReview,
    ResearchNote,
    StatementComparison,
    VerificationState,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def phase12_demo(demo_settings: Any) -> Iterator[dict[str, str]]:
    issue_key = f"PIR-DEMO-{uuid.uuid4().hex[:8]}"
    comparison_key = f"SC-DEMO-{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC)
    with session_scope() as session:
        finding = session.scalar(select(Finding).where(Finding.finding_key == "FD-DEMO-001"))
        assert finding is not None and finding.citation_id is not None
        link = session.scalar(
            select(FindingEvidenceLink).where(FindingEvidenceLink.finding_id == finding.id)
        )
        assert link is not None
        citations = session.scalars(
            select(Citation).where(
                Citation.case_id == finding.case_id,
                Citation.id.in_([finding.citation_id, link.citation_id]),
            )
        ).all()
        assert len(citations) == 2
        by_id = {citation.id: citation for citation in citations}
        issue = AppealIssue(
            case_id=finding.case_id,
            issue_key=issue_key,
            category="reasoning",
            context="legal",
            title="Potential Issue for Review (synthetic fixture)",
            description="A synthetic structural issue for API testing.",
            finding_id=finding.id,
            court_treatment="not_located",
            court_treatment_note="Court treatment not yet located; this does not mean ignored.",
            red_team_result="insufficient_record",
            extraction_origin="synthetic_fixture",
            verification_state=VerificationState.NEEDS_MORE_EVIDENCE,
        )
        session.add(issue)
        session.flush()
        session.add(
            AppealIssueSource(
                issue_id=issue.id,
                sequence=1,
                role="court_reasoning",
                source_category="court_finding",
                citation_id=finding.citation_id,
                excerpt=finding.text,
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by="test-reviewer",
                verified_at=now,
            )
        )
        session.add(
            AppealMissingMaterial(
                issue_id=issue.id,
                reference="F-DEMO-MISSING",
                kind="underlying_filing",
                reason="Synthetic missing-source test.",
                state="source_unavailable",
            )
        )
        session.add(
            StatementComparison(
                case_id=finding.case_id,
                comparison_key=comparison_key,
                issue_id=issue.id,
                title="Synthetic exact-source comparison",
                comparison_type="source_source",
                classification="not_comparable",
                statement_a_citation_id=finding.citation_id,
                statement_b_citation_id=link.citation_id,
                statement_a_excerpt=finding.text,
                statement_b_excerpt=by_id[link.citation_id].raw_text,
                explanation="One source is missing context; silence is not treated as a difference.",
                extraction_origin="synthetic_fixture",
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by="test-reviewer",
                verified_at=now,
            )
        )
        review = RedTeamReview(
            issue_id=issue.id,
            result="insufficient_record",
            summary="The controlled fixture is insufficient.",
            origin="human",
            verification_state=VerificationState.HUMAN_VERIFIED,
            verified_by="test-reviewer",
            verified_at=now,
        )
        session.add(review)
        session.flush()
        session.add_all(
            [
                RedTeamFinding(
                    review_id=review.id,
                    sequence=1,
                    perspective="defence_analyst",
                    category="well_supported",
                    text="The exact passage is available.",
                    citation_id=finding.citation_id,
                    verification_state=VerificationState.HUMAN_VERIFIED,
                    verified_by="test-reviewer",
                    verified_at=now,
                ),
                RedTeamFinding(
                    review_id=review.id,
                    sequence=2,
                    perspective="neutral_reviewer",
                    category="source_limitation",
                    text="The missing source prevents a conclusion.",
                    verification_state=VerificationState.HUMAN_VERIFIED,
                    verified_by="test-reviewer",
                    verified_at=now,
                ),
            ]
        )
        issue_id = issue.id
        citation_id = str(finding.citation_id)
    yield {"issue_key": issue_key, "comparison_key": comparison_key, "citation_id": citation_id}
    with session_scope() as session:
        session.execute(delete(ResearchNote).where(ResearchNote.appeal_issue_id == issue_id))
        session.execute(delete(StatementComparison).where(StatementComparison.issue_id == issue_id))
        session.execute(delete(AppealIssue).where(AppealIssue.id == issue_id))


def test_appeal_api_is_source_backed_and_distinguishes_not_located(
    phase12_demo: dict[str, str], demo_client: Any
) -> None:
    key = phase12_demo["issue_key"]
    workspace = demo_client.get("/api/v1/appeal/issues").json()
    item = next(issue for issue in workspace["issues"] if issue["issue_key"] == key)
    assert item["court_treatment"] == "not_located"
    assert "ignored" in item["court_treatment_note"]
    assert not ({"probability", "likelihood", "strength", "rank"} & item.keys())

    detail = demo_client.get(f"/api/v1/appeal/issues/{key}").json()
    assert len(detail["sources"]) == 1
    assert detail["sources"][0]["citation"]["resolved"] is True
    assert detail["citation_audit"]["ready_for_human_review"] is False
    assert detail["missing_material"][0]["reference"] == "F-DEMO-MISSING"
    assert detail["red_team_reviews"][0]["result"] == "insufficient_record"
    assert {row["perspective"] for row in detail["red_team_reviews"][0]["findings"]} == {
        "defence_analyst",
        "neutral_reviewer",
    }


def test_argument_lab_and_comparison_keep_exact_citations(
    phase12_demo: dict[str, str], demo_client: Any
) -> None:
    key = phase12_demo["issue_key"]
    lab = demo_client.get(f"/api/v1/appeal/issues/{key}/argument-lab").json()
    assert lab["result"] == "insufficient_record"
    assert lab["draft_citations"][0]["resolved"] is True
    assert "does not declare a winner" in lab["notice"]
    comparisons = demo_client.get("/api/v1/statement-comparisons", params={"issue_key": key}).json()
    assert len(comparisons) == 1
    assert comparisons[0]["classification"] == "not_comparable"
    assert comparisons[0]["statement_a_citation"]["target_path"]
    assert comparisons[0]["statement_b_citation"]["target_path"]


def test_note_rejects_non_whitelisted_source_and_saves_only_as_research(
    phase12_demo: dict[str, str], demo_client: Any
) -> None:
    key = phase12_demo["issue_key"]
    payload = {"author": "reviewer", "title": "Review note", "body": "Requires human review."}
    rejected = demo_client.post(
        f"/api/v1/appeal/issues/{key}/notes",
        json={**payload, "citation_ids": [str(uuid.uuid4())]},
    )
    assert rejected.status_code == 422
    saved = demo_client.post(
        f"/api/v1/appeal/issues/{key}/notes",
        json={**payload, "citation_ids": [phase12_demo["citation_id"]]},
    )
    assert saved.status_code == 201
    assert saved.json()["provenance"] == "human"
