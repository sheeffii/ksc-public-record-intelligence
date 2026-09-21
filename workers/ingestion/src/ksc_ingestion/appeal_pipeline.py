"""Hand-reviewed Phase 12 benchmark over the existing controlled corpus.

No source is fetched. The benchmark records a narrow potential procedural
review question around F03752, then red-teams it to an insufficient-record
result because the underlying party filings and pre-correction brief are not
held. It does not assert error or create an appeal ground.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    AppealIssue,
    AppealIssueSource,
    AppealMissingMaterial,
    Argument,
    Case,
    Citation,
    CitationType,
    Document,
    DocumentPage,
    DocumentParagraph,
    DocumentVersion,
    Finding,
    FindingEvidenceLink,
    RedTeamFinding,
    RedTeamReview,
    ResolutionMethod,
    ResolutionState,
    StatementComparison,
    VerificationState,
    normalize_identifier,
)

_NS = uuid.UUID("78f4fa94-8e6a-4d52-8230-7384b9ee55c7")
_ORIGIN = "phase12_hand_verified"
_REVIEWER = "phase12-benchmark-review"
_REVIEWED_AT = datetime(2026, 9, 21, tzinfo=UTC)
_ISSUE_KEY = "PIR-F03752-AMENDMENTS-RECORD"
_COMPARISON_KEY = "SC-F03752-P12-F03667-P160"
_DECISION_REF = "KSC-BC-2020-06/F03752"
_SOURCE_VERSION_REF = "KSC-BC-2020-06/F03667/COR/RED"


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(_NS, key)


@dataclass(frozen=True)
class AppealBuildResult:
    issues: int
    source_backed_links: int
    comparisons: int
    red_team_reviews: int
    red_team_findings: int
    missing_sources: int


class Phase12Pipeline:
    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def run(self) -> AppealBuildResult:
        with self.sessions() as session, session.begin():
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise RuntimeError(f"case {self.case_number} is not seeded")
            finding = session.scalar(
                select(Finding).where(
                    Finding.case_id == case.id, Finding.finding_key == "FD-F03752-P12-16"
                )
            )
            if finding is None or finding.citation_id is None:
                raise RuntimeError("Phase 10 finding benchmark must exist before Phase 12")
            arguments = {
                row.party.value: row
                for row in session.scalars(
                    select(Argument).where(Argument.finding_id == finding.id)
                ).all()
            }
            defence = arguments.get("defence")
            spo = arguments.get("spo")
            court = arguments.get("court")
            if any(row is None or row.citation_id is None for row in (defence, spo, court)):
                raise RuntimeError("Phase 10 party/Court argument benchmark is incomplete")
            assert defence is not None and spo is not None and court is not None
            evidence = session.scalar(
                select(FindingEvidenceLink).where(FindingEvidenceLink.finding_id == finding.id)
            )
            if evidence is None:
                raise RuntimeError("Phase 10 evidence link benchmark is incomplete")
            decision_version = session.scalar(
                select(DocumentVersion).where(DocumentVersion.official_version_ref == _DECISION_REF)
            )
            source_version = session.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.official_version_ref == _SOURCE_VERSION_REF
                )
            )
            if decision_version is None or source_version is None:
                raise RuntimeError("required held versions are missing")
            p12 = session.scalar(
                select(DocumentParagraph).where(
                    DocumentParagraph.document_version_id == decision_version.id,
                    DocumentParagraph.paragraph_number == 12,
                )
            )
            source_page = session.scalar(
                select(DocumentPage).where(
                    DocumentPage.document_version_id == source_version.id,
                    DocumentPage.page_number == 160,
                )
            )
            if p12 is None or source_page is None or source_page.text is None:
                raise RuntimeError("exact comparison coordinates are missing")
            court_excerpt = (
                "The Panel notes that: (i) the First Amendment substituted “P03720_ET, p. 2” "
                "with “P00303_ET, p. 2”; and (ii) the Second Amendment substituted "
                "“P03720_ET” with “P00303_ET, p. 2”, in the Corrected Version of the SPO Final Trial Brief."
            )
            source_excerpt = (
                "1216 See e.g. P00303_ET:p.2(Public). See also P01068:pp.116696-116698(Public)."
            )
            if court_excerpt not in p12.text or source_excerpt not in " ".join(
                source_page.text.split()
            ):
                raise RuntimeError("hand-reviewed comparison excerpts no longer match parsed text")

            self._clear_previous(session, case.id)
            citation_a = self._citation(
                case_id=case.id,
                key="comparison-a",
                raw=f"{_DECISION_REF}, para 12",
                display="F03752 · ¶12",
                document=decision_version.document,
                version=decision_version,
                page=p12.page_from,
                pdf_page=p12.pdf_page_index_from,
                para_from=12,
                para_to=12,
            )
            citation_b = self._citation(
                case_id=case.id,
                key="comparison-b",
                raw=f"{_SOURCE_VERSION_REF}, p. 160",
                display="F03667/COR/RED · p. 160",
                document=source_version.document,
                version=source_version,
                page=160,
                pdf_page=source_page.pdf_page_index,
            )
            session.add_all([citation_a, citation_b])
            session.flush()

            issue = AppealIssue(
                id=_id("issue"),
                case_id=case.id,
                issue_key=_ISSUE_KEY,
                category="procedural_fairness",
                context="procedural",
                title="Completeness of the public record for reviewing the First and Second Amendments",
                description=(
                    "Potential Issue for Review: the Panel addressed the First and Second Amendments "
                    "in F03752, while the controlled corpus lacks the underlying party filings and the "
                    "earlier brief needed to independently compare the amendments. The record is "
                    "incomplete and requires human legal review."
                ),
                finding_id=finding.id,
                court_treatment="addressed",
                court_treatment_note=(
                    "Court treatment is located at F03752 paragraphs 12-16. 'Addressed' records the "
                    "presence of reasoning; it does not assess whether that reasoning was correct."
                ),
                red_team_result="insufficient_record",
                extraction_origin=_ORIGIN,
                notes="No error, valid ground, or predicted outcome is asserted.",
                verification_state=VerificationState.NEEDS_MORE_EVIDENCE,
            )
            session.add(issue)
            session.flush()
            source_specs = [
                (
                    1,
                    "court_reasoning",
                    "court_finding",
                    finding.citation_id,
                    None,
                    None,
                    finding.text,
                    "Exact challenged Court passage.",
                ),
                (
                    2,
                    "defence_position",
                    "defence_argument",
                    defence.citation_id,
                    defence.id,
                    None,
                    defence.text,
                    "Court summary; underlying F03743 is unavailable.",
                ),
                (
                    3,
                    "spo_position",
                    "spo_argument",
                    spo.citation_id,
                    spo.id,
                    None,
                    spo.text,
                    "Court summary; underlying F03746 is unavailable.",
                ),
                (
                    4,
                    "evidence_relied",
                    "spo_argument",
                    evidence.citation_id,
                    None,
                    evidence.id,
                    evidence.citation.raw_text,
                    "Exact source expressly identified by the Court.",
                ),
                (
                    5,
                    "court_response",
                    "court_response",
                    court.citation_id,
                    court.id,
                    None,
                    court.text,
                    "Court response kept separate from both party positions.",
                ),
            ]
            for (
                sequence,
                role,
                category,
                citation_id,
                argument_id,
                link_id,
                excerpt,
                note,
            ) in source_specs:
                session.add(
                    AppealIssueSource(
                        id=_id(f"source:{sequence}"),
                        issue_id=issue.id,
                        sequence=sequence,
                        role=role,
                        source_category=category,
                        citation_id=citation_id,
                        argument_id=argument_id,
                        finding_evidence_link_id=link_id,
                        excerpt=excerpt,
                        note=note,
                        verification_state=VerificationState.HUMAN_VERIFIED,
                        verified_by=_REVIEWER,
                        verified_at=_REVIEWED_AT,
                    )
                )
            missing = [
                (
                    "F03743",
                    "underlying_defence_filing",
                    "The Defence position is available only through the Court's summary.",
                ),
                (
                    "F03746",
                    "underlying_spo_filing",
                    "The SPO position is available only through the Court's summary.",
                ),
                (
                    "pre-correction SPO Final Trial Brief",
                    "comparison_source",
                    "The earlier brief is not held, so the claimed substitutions cannot be independently compared.",
                ),
                (
                    "public Trial Judgment",
                    "adjudicative_record",
                    "The controlled corpus contains no Trial Judgment; no merits appeal analysis is attempted.",
                ),
            ]
            for reference, kind, reason in missing:
                session.add(
                    AppealMissingMaterial(
                        id=_id(f"missing:{reference}"),
                        issue_id=issue.id,
                        reference=reference,
                        kind=kind,
                        reason=reason,
                        state="source_unavailable",
                    )
                )
            comparison = StatementComparison(
                id=_id("comparison"),
                case_id=case.id,
                comparison_key=_COMPARISON_KEY,
                issue_id=issue.id,
                title="Panel characterization and held corrected brief",
                comparison_type="court_characterization_source",
                classification="not_comparable",
                statement_a_citation_id=citation_a.id,
                statement_b_citation_id=citation_b.id,
                statement_a_excerpt=court_excerpt,
                statement_b_excerpt=source_excerpt,
                statement_a_speaker="Trial Panel II",
                statement_b_speaker="SPO filing",
                explanation=(
                    "The held corrected brief shows the P00303_ET reference described by the Panel. "
                    "The earlier version is not held, so the substitution itself is Not Comparable. "
                    "This classification concerns the two passages, not any person's credibility."
                ),
                extraction_origin=_ORIGIN,
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by=_REVIEWER,
                verified_at=_REVIEWED_AT,
            )
            session.add(comparison)
            review = RedTeamReview(
                id=_id("red-team"),
                issue_id=issue.id,
                result="insufficient_record",
                summary=(
                    "The Court expressly addressed the amendments and stated why it treated the first "
                    "two as clerical corrections. The missing filings and earlier brief prevent a "
                    "complete source comparison, so the issue remains research-only."
                ),
                origin="human",
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by=_REVIEWER,
                verified_at=_REVIEWED_AT,
            )
            session.add(review)
            session.flush()
            red_findings = [
                (
                    1,
                    "defence_analyst",
                    "well_supported",
                    "The Panel recorded the Defence position and acknowledged that the amendments were not identified in Annex 3.",
                    citation_a.id,
                ),
                (
                    2,
                    "spo_red_team",
                    "counter_material",
                    "Paragraphs 14-16 contain Court reasoning that the two references concerned versions of the same document, were clerical, and caused no prejudice.",
                    court.citation_id,
                ),
                (
                    3,
                    "neutral_reviewer",
                    "source_limitation",
                    "F03743, F03746, and the pre-correction brief are unavailable in the controlled corpus.",
                    None,
                ),
                (
                    4,
                    "neutral_reviewer",
                    "human_required",
                    "Whether the complete record could support an appellate ground is a legal question for qualified counsel; this system does not answer it.",
                    None,
                ),
            ]
            for sequence, perspective, category, text, citation_id in red_findings:
                session.add(
                    RedTeamFinding(
                        id=_id(f"red:{sequence}"),
                        review_id=review.id,
                        sequence=sequence,
                        perspective=perspective,
                        category=category,
                        text=text,
                        citation_id=citation_id,
                        verification_state=VerificationState.HUMAN_VERIFIED,
                        verified_by=_REVIEWER,
                        verified_at=_REVIEWED_AT,
                    )
                )
            session.flush()
            return AppealBuildResult(1, len(source_specs), 1, 1, len(red_findings), len(missing))

    @staticmethod
    def _citation(
        *,
        case_id: uuid.UUID,
        key: str,
        raw: str,
        display: str,
        document: Document,
        version: DocumentVersion,
        page: int | None,
        pdf_page: int,
        para_from: int | None = None,
        para_to: int | None = None,
    ) -> Citation:
        return Citation(
            id=_id(f"citation:{key}"),
            case_id=case_id,
            raw_text=raw,
            normalized_text=normalize_identifier(raw),
            citation_type=CitationType.PARAGRAPH if para_from else CitationType.PAGE,
            target_document_id=document.id,
            target_document_version_id=version.id,
            target_page=page,
            target_pdf_page_index=pdf_page,
            target_para_from=para_from,
            target_para_to=para_to,
            source_url=version.source_url,
            resolution_state=ResolutionState.RESOLVED,
            resolution_method=ResolutionMethod.MANUAL,
            resolution_confidence=Decimal("1.00"),
            resolved_at=_REVIEWED_AT,
            display=display,
            resolution_detail="Phase 12 hand-verified exact coordinate in the controlled corpus.",
            verification_state=VerificationState.HUMAN_VERIFIED,
            verified_by=_REVIEWER,
            verified_at=_REVIEWED_AT,
        )

    @staticmethod
    def _clear_previous(session: Session, case_id: uuid.UUID) -> None:
        issue_id = _id("issue")
        session.execute(
            delete(StatementComparison).where(
                StatementComparison.case_id == case_id, StatementComparison.id == _id("comparison")
            )
        )
        session.execute(
            delete(AppealIssue).where(AppealIssue.case_id == case_id, AppealIssue.id == issue_id)
        )
        session.execute(
            delete(Citation).where(
                Citation.id.in_([_id("citation:comparison-a"), _id("citation:comparison-b")])
            )
        )
