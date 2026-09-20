"""Hand-reviewed Phase 10 finding projection for the controlled real corpus.

The controlled corpus does not contain the Trial Judgment. This module never
substitutes a party brief for it. It creates one narrowly scoped benchmark from
an available public Court decision, copying exact persisted paragraph text and
linking only a source the Panel explicitly cites in that reasoning.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, object_session, sessionmaker

from ksc_api.models import (
    Argument,
    ArgumentResponse,
    ArgumentResponseKind,
    Case,
    Citation,
    CitationType,
    Document,
    DocumentParagraph,
    DocumentVersion,
    EntityKind,
    Finding,
    FindingEvidenceLink,
    FindingLinkType,
    IdentifierKind,
    Party,
    RecordIdentifier,
    ResolutionMethod,
    ResolutionState,
    VerificationState,
    normalize_identifier,
)

_NS = uuid.UUID("26a66ed4-a4a6-4460-826c-f6ff882c1660")
_ORIGIN = "phase10_hand_verified"
_REVIEWER = "phase10-benchmark-review"
_REVIEWED_AT = datetime(2026, 9, 21, tzinfo=UTC)
_DECISION_REF = "KSC-BC-2020-06/F03752"
_SOURCE_VERSION_REF = "KSC-BC-2020-06/F03667/COR/RED"
_FINDING_KEY = "FD-F03752-P12-16"


def _id(kind: str) -> uuid.UUID:
    return uuid.uuid5(_NS, kind)


@dataclass(frozen=True)
class FindingBuildResult:
    findings: int
    evidence_links: int
    party_arguments: int
    court_responses: int
    missing_underlying_party_sources: int


class Phase10Pipeline:
    """Build the manually reviewed benchmark without inference or network I/O."""

    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def run(self) -> FindingBuildResult:
        with self.sessions() as session, session.begin():
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise RuntimeError(f"case {self.case_number} is not seeded")
            decision = session.scalar(
                select(Document).where(
                    Document.case_id == case.id, Document.official_ref == _DECISION_REF
                )
            )
            if decision is None or decision.document_type.lower() != "decision":
                raise RuntimeError(f"required public Court decision {_DECISION_REF} is not held")
            version = session.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.document_id == decision.id,
                    DocumentVersion.official_version_ref == _DECISION_REF,
                )
            )
            source_version = session.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.official_version_ref == _SOURCE_VERSION_REF
                )
            )
            if version is None or source_version is None:
                raise RuntimeError("required benchmark document versions are not held")

            paragraphs = {
                paragraph.paragraph_number: paragraph
                for paragraph in session.scalars(
                    select(DocumentParagraph).where(
                        DocumentParagraph.document_version_id == version.id,
                        DocumentParagraph.paragraph_number.in_([6, 7, 12, 13, 14, 15, 16]),
                    )
                ).all()
            }
            missing = sorted({6, 7, 12, 13, 14, 15, 16} - paragraphs.keys())
            if missing:
                raise RuntimeError(f"benchmark decision lacks parsed paragraph(s): {missing}")

            self._clear_previous(session, case.id)

            finding = Finding(
                id=_id("finding"),
                case_id=case.id,
                finding_key=_FINDING_KEY,
                judgment_document_id=decision.id,
                judgment_version_id=version.id,
                extraction_origin=_ORIGIN,
                text="\n\n".join(paragraphs[number].text for number in range(12, 17)),
                para_from=12,
                para_to=16,
                legal_element="Scope of permissible correction under Registry Practice Direction Article 27(1)",
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by=_REVIEWER,
                verified_at=_REVIEWED_AT,
            )
            session.add(finding)
            session.flush()

            finding_citation = self._coordinate_citation(
                case_id=case.id,
                key="finding-coordinate",
                raw_text="KSC-BC-2020-06/F03752, paras 12-16",
                display="F03752 · ¶¶12-16",
                document=decision,
                version=version,
                para_from=12,
                para_to=16,
                paragraph=paragraphs[12],
                target_finding_id=finding.id,
            )
            session.add(finding_citation)
            session.flush()
            finding.citation_id = finding_citation.id

            cited_phrase = "Corrected Version of the SPO Final Trial Brief"
            cited_text = paragraphs[12].text
            start = cited_text.find(cited_phrase)
            if start < 0:
                raise RuntimeError("hand-reviewed citation phrase is absent from paragraph 12")
            evidence_citation = Citation(
                id=_id("citation:explicit-source"),
                case_id=case.id,
                raw_text=cited_phrase,
                normalized_text=normalize_identifier(cited_phrase),
                citation_type=CitationType.DOCUMENT_VERSION,
                source_document_version_id=version.id,
                source_page=paragraphs[12].page_from,
                source_pdf_page_index=paragraphs[12].pdf_page_index_from,
                source_para=12,
                source_char_start=start,
                source_char_end=start + len(cited_phrase),
                source_url=version.source_url,
                target_document_id=source_version.document_id,
                target_document_version_id=source_version.id,
                resolution_state=ResolutionState.RESOLVED,
                resolution_method=ResolutionMethod.MANUAL,
                resolution_confidence=Decimal("1.00"),
                resolved_at=_REVIEWED_AT,
                display="F03667/COR/RED",
                resolution_detail=(
                    "Hand-verified defined term in F03752 paragraph 12; the decision identifies "
                    "the public redacted corrected version as F03667/COR/RED."
                ),
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by=_REVIEWER,
                verified_at=_REVIEWED_AT,
            )
            session.add(evidence_citation)
            session.flush()
            session.add(
                FindingEvidenceLink(
                    id=_id("evidence-link"),
                    finding_id=finding.id,
                    citation_id=evidence_citation.id,
                    link_type=FindingLinkType.RELIES_ON,
                    court_cited=True,
                    court_cited_para=12,
                    relationship_basis="explicit_court_citation",
                    source_category="spo_argument",
                    extraction_origin=_ORIGIN,
                    note=(
                        "The Panel's reasoning expressly identifies the corrected SPO brief. "
                        "This link records citation, not endorsement or evidential weight."
                    ),
                    verification_state=VerificationState.HUMAN_VERIFIED,
                    verified_by=_REVIEWER,
                    verified_at=_REVIEWED_AT,
                )
            )

            defence = self._argument(
                case_id=case.id,
                key="AR-F03752-DEF-P6",
                party=Party.DEFENCE,
                title="Defence position as recorded by the Panel",
                paragraph=paragraphs[6],
                decision=decision,
                version=version,
                finding=finding,
                underlying_source_ref="F03743",
            )
            spo = self._argument(
                case_id=case.id,
                key="AR-F03752-SPO-P7",
                party=Party.SPO,
                title="SPO position as recorded by the Panel",
                paragraph=paragraphs[7],
                decision=decision,
                version=version,
                finding=finding,
                underlying_source_ref="F03746",
            )
            court = self._argument(
                case_id=case.id,
                key="AR-F03752-COURT-P14-16",
                party=Party.COURT,
                title="Panel reasoning and response",
                paragraph=paragraphs[14],
                decision=decision,
                version=version,
                finding=finding,
                para_to=16,
                text="\n\n".join(paragraphs[number].text for number in range(14, 17)),
                source_scope="direct_source",
            )
            session.add_all([defence, spo, court])
            session.flush()
            for argument in (defence, spo):
                session.add(
                    ArgumentResponse(
                        id=_id(f"response:{argument.argument_key}"),
                        argument_id=argument.id,
                        response_argument_id=court.id,
                        response_kind=ArgumentResponseKind.RULES_ON,
                        citation_id=court.citation_id,
                        note="The Court response is stored separately from the party position.",
                        extraction_origin=_ORIGIN,
                        verification_state=VerificationState.HUMAN_VERIFIED,
                        verified_by=_REVIEWER,
                        verified_at=_REVIEWED_AT,
                    )
                )
            session.add(
                RecordIdentifier(
                    id=_id("finding-identifier"),
                    case_id=case.id,
                    identifier=_FINDING_KEY,
                    normalized_identifier=normalize_identifier(_FINDING_KEY),
                    identifier_kind=IdentifierKind.FINDING,
                    entity_kind=EntityKind.FINDING,
                    finding_id=finding.id,
                )
            )
            session.flush()
            return FindingBuildResult(
                findings=1,
                evidence_links=1,
                party_arguments=2,
                court_responses=2,
                missing_underlying_party_sources=2,
            )

    @staticmethod
    def _clear_previous(session: Session, case_id: uuid.UUID) -> None:
        finding_id = _id("finding")
        argument_ids = [
            _id(f"argument:{key}")
            for key in ("AR-F03752-DEF-P6", "AR-F03752-SPO-P7", "AR-F03752-COURT-P14-16")
        ]
        citation_ids = [_id("citation:finding-coordinate"), _id("citation:explicit-source")]
        citation_ids.extend(
            _id(f"citation:{key}")
            for key in ("AR-F03752-DEF-P6", "AR-F03752-SPO-P7", "AR-F03752-COURT-P14-16")
        )
        session.execute(
            update(Finding)
            .where(Finding.case_id == case_id, Finding.id == finding_id)
            .values(citation_id=None)
        )
        session.execute(
            delete(ArgumentResponse).where(
                (ArgumentResponse.argument_id.in_(argument_ids))
                | (ArgumentResponse.response_argument_id.in_(argument_ids))
            )
        )
        session.execute(delete(Argument).where(Argument.id.in_(argument_ids)))
        session.execute(
            delete(FindingEvidenceLink).where(FindingEvidenceLink.finding_id == finding_id)
        )
        session.execute(
            delete(RecordIdentifier).where(RecordIdentifier.id == _id("finding-identifier"))
        )
        session.execute(delete(Finding).where(Finding.case_id == case_id, Finding.id == finding_id))
        session.flush()
        session.execute(delete(Citation).where(Citation.id.in_(citation_ids)))

    @staticmethod
    def _coordinate_citation(
        *,
        case_id: uuid.UUID,
        key: str,
        raw_text: str,
        display: str,
        document: Document,
        version: DocumentVersion,
        para_from: int,
        para_to: int,
        paragraph: DocumentParagraph,
        target_finding_id: uuid.UUID | None = None,
    ) -> Citation:
        return Citation(
            id=_id(f"citation:{key}"),
            case_id=case_id,
            raw_text=raw_text,
            normalized_text=normalize_identifier(raw_text),
            citation_type=CitationType.FINDING if target_finding_id else CitationType.PARAGRAPH,
            source_url=version.source_url,
            target_document_id=document.id,
            target_document_version_id=version.id,
            target_finding_id=target_finding_id,
            target_page=paragraph.page_from,
            target_pdf_page_index=paragraph.pdf_page_index_from,
            target_para_from=para_from,
            target_para_to=para_to,
            resolution_state=ResolutionState.RESOLVED,
            resolution_method=ResolutionMethod.MANUAL,
            resolution_confidence=Decimal("1.00"),
            resolved_at=_REVIEWED_AT,
            display=display,
            resolution_detail="Hand-verified exact paragraph coordinate in the controlled corpus.",
            verification_state=VerificationState.HUMAN_VERIFIED,
            verified_by=_REVIEWER,
            verified_at=_REVIEWED_AT,
        )

    def _argument(
        self,
        *,
        case_id: uuid.UUID,
        key: str,
        party: Party,
        title: str,
        paragraph: DocumentParagraph,
        decision: Document,
        version: DocumentVersion,
        finding: Finding,
        underlying_source_ref: str | None = None,
        para_to: int | None = None,
        text: str | None = None,
        source_scope: str = "court_summary",
    ) -> Argument:
        end = para_to or paragraph.paragraph_number
        citation = self._coordinate_citation(
            case_id=case_id,
            key=key,
            raw_text=f"{_DECISION_REF}, para{'s' if end != paragraph.paragraph_number else ''} "
            f"{paragraph.paragraph_number}{f'-{end}' if end != paragraph.paragraph_number else ''}",
            display=(
                f"F03752 · ¶{paragraph.paragraph_number}"
                if end == paragraph.paragraph_number
                else f"F03752 · ¶¶{paragraph.paragraph_number}-{end}"
            ),
            document=decision,
            version=version,
            para_from=paragraph.paragraph_number,
            para_to=end,
            paragraph=paragraph,
        )
        # SQLAlchemy cascades no relationship here, so add through the finding's session.
        active = object_session(finding)
        if active is None:
            raise RuntimeError("finding is detached")
        active.add(citation)
        active.flush()
        return Argument(
            id=_id(f"argument:{key}"),
            case_id=case_id,
            argument_key=key,
            party=party,
            title=title,
            text=text or paragraph.text,
            document_id=decision.id,
            document_version_id=version.id,
            para_from=paragraph.paragraph_number,
            para_to=end,
            citation_id=citation.id,
            finding_id=finding.id,
            source_scope=source_scope,
            underlying_source_ref=underlying_source_ref,
            extraction_origin=_ORIGIN,
            verification_state=VerificationState.HUMAN_VERIFIED,
            verified_by=_REVIEWER,
            verified_at=_REVIEWED_AT,
        )
