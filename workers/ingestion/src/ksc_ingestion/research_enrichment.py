"""Phase 23 reviewed research enrichment of the F03752 benchmark.

Adds what the newly held primary filings support, and nothing else:

- the Defence's and the SPO's own filings (F03743, F03746) as direct-source
  party positions on finding FD-F03752-P12-16, beside, never replacing, the
  Court's summaries of them in F03752 ¶¶6-7;
- those filings, and Annex 3 to the corrected SPO brief as partial context, as
  sources of issue PIR-F03752-AMENDMENTS-RECORD;
- the issue's F03743/F03746 gaps resolved by the exact held versions, with the
  Registry memorandum F03759 recorded only as procedural provenance of F03746's
  public reclassification.

Every row has a deterministic id, so a re-run replaces exactly what it wrote.
The Court finding, its review status and every Court summary are untouched.
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
    AuditLog,
    Case,
    Citation,
    CitationType,
    DocumentPage,
    DocumentParagraph,
    DocumentVersion,
    Finding,
    Party,
    ResolutionMethod,
    ResolutionState,
    VerificationState,
    normalize_identifier,
)

_NS = uuid.UUID("2f6f1d87-5a0c-4f3e-9b0e-6c3d9b6f2a23")
_ORIGIN = "phase23_reviewed_enrichment"
_REVIEWER = "phase23-owner-directed-review"
_REVIEWED_AT = datetime(2026, 10, 4, tzinfo=UTC)
_ACTOR = "ksc-ingest-phase23-enrichment"

_CASE_PREFIX = "KSC-BC-2020-06"
_FINDING_KEY = "FD-F03752-P12-16"
_ISSUE_KEY = "PIR-F03752-AMENDMENTS-RECORD"
_DEFENCE_REF = f"{_CASE_PREFIX}/F03743"
_SPO_REF = f"{_CASE_PREFIX}/F03746"
_ANNEX_3_REF = f"{_CASE_PREFIX}/F03667/COR/RED/A03/RED"
_REGISTRY_MEMO_REF = f"{_CASE_PREFIX}/F03759"


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(_NS, key)


@dataclass(frozen=True)
class _Position:
    key: str
    party: Party
    attribution: str
    title: str
    version_ref: str
    para_from: int
    para_to: int


_POSITIONS = (
    _Position(
        "AR-F03743-DEF-P3",
        Party.DEFENCE,
        "Joint Defence",
        "Defence submission in its own filing: the three contested amendments",
        _DEFENCE_REF,
        3,
        3,
    ),
    _Position(
        "AR-F03743-DEF-P4",
        Party.DEFENCE,
        "Joint Defence",
        "Defence submission in its own filing: relief requested",
        _DEFENCE_REF,
        4,
        4,
    ),
    _Position(
        "AR-F03746-SPO-P1-3",
        Party.SPO,
        "SPO",
        "SPO response in its own filing: the amendments are permissible corrections",
        _SPO_REF,
        1,
        3,
    ),
)


@dataclass(frozen=True)
class EnrichmentResult:
    party_positions: int
    issue_sources: int
    resolved_gaps: int
    open_gaps: int


class Phase23ResearchEnrichment:
    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def run(self) -> EnrichmentResult:
        with self.sessions() as session, session.begin():
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise RuntimeError(f"case {self.case_number} is not seeded")
            finding = session.scalar(
                select(Finding).where(
                    Finding.case_id == case.id, Finding.finding_key == _FINDING_KEY
                )
            )
            issue = session.scalar(
                select(AppealIssue).where(
                    AppealIssue.case_id == case.id, AppealIssue.issue_key == _ISSUE_KEY
                )
            )
            if finding is None or issue is None:
                raise RuntimeError("benchmark finding or appeal issue is not held")
            for ref in (_DEFENCE_REF, _SPO_REF, _ANNEX_3_REF, _REGISTRY_MEMO_REF):
                self._public_version(session, ref)  # fails closed if not held and public

            self._clear(session)
            arguments = [self._position(session, case.id, finding, p) for p in _POSITIONS]
            sources = self._issue_sources(session, case.id, issue, arguments)
            self._summary_notes(session, issue)
            resolved, still_open = self._gaps(session, issue)
            session.add(
                AuditLog(
                    actor=_ACTOR,
                    action="research.enriched",
                    entity_type="appeal_issue",
                    entity_id=_ISSUE_KEY,
                    detail={
                        "finding": _FINDING_KEY,
                        "direct_party_positions": [p.key for p in _POSITIONS],
                        "issue_sources": len(sources),
                        "resolved_gaps": resolved,
                        "open_gaps": still_open,
                        "procedural_provenance": {
                            _SPO_REF: f"public reclassification recorded in {_REGISTRY_MEMO_REF}"
                        },
                        "review_state": {
                            "verification_state": issue.verification_state.value,
                            "red_team_result": issue.red_team_result,
                            "reason": (
                                "The party filings are now held, but the pre-correction brief "
                                "and the exhibit files P03720_ET / P00303_ET are not, so the "
                                "substitutions cannot be independently verified."
                            ),
                        },
                    },
                )
            )
            return EnrichmentResult(
                party_positions=len(arguments),
                issue_sources=len(sources),
                resolved_gaps=len(resolved),
                open_gaps=len(still_open),
            )

    # ----------------------------------------------------------- helpers --
    def _public_version(self, session: Session, ref: str) -> DocumentVersion:
        version = session.scalar(
            select(DocumentVersion).where(DocumentVersion.official_version_ref == ref)
        )
        if version is None or version.visibility.value not in {"public", "public_redacted"}:
            raise RuntimeError(f"required public source {ref} is not held")
        return version

    @staticmethod
    def _clear(session: Session) -> None:
        keys = [p.key for p in _POSITIONS]
        session.execute(
            delete(AppealIssueSource).where(
                AppealIssueSource.id.in_([_id(f"issue-source:{k}") for k in [*keys, "annex-3"]])
            )
        )
        session.execute(
            delete(Argument).where(Argument.id.in_([_id(f"argument:{k}") for k in keys]))
        )
        session.execute(
            delete(Citation).where(
                Citation.id.in_([_id(f"citation:{k}") for k in [*keys, "annex-3"]])
            )
        )
        session.flush()

    def _citation(
        self,
        case_id: uuid.UUID,
        key: str,
        version: DocumentVersion,
        *,
        raw_text: str,
        display: str,
        citation_type: CitationType,
        page: int | None,
        pdf_page_index: int | None,
        para_from: int | None = None,
        para_to: int | None = None,
    ) -> Citation:
        return Citation(
            id=_id(f"citation:{key}"),
            case_id=case_id,
            raw_text=raw_text,
            normalized_text=normalize_identifier(raw_text),
            citation_type=citation_type,
            source_url=version.source_url,
            target_document_id=version.document_id,
            target_document_version_id=version.id,
            target_page=page,
            target_pdf_page_index=pdf_page_index,
            target_para_from=para_from,
            target_para_to=para_to,
            resolution_state=ResolutionState.RESOLVED,
            resolution_method=ResolutionMethod.MANUAL,
            resolution_confidence=Decimal("1.00"),
            resolved_at=_REVIEWED_AT,
            display=display,
            resolution_detail="Owner-reviewed exact coordinate in a held public source.",
            verification_state=VerificationState.HUMAN_VERIFIED,
            verified_by=_REVIEWER,
            verified_at=_REVIEWED_AT,
        )

    def _position(
        self, session: Session, case_id: uuid.UUID, finding: Finding, position: _Position
    ) -> Argument:
        version = self._public_version(session, position.version_ref)
        paragraphs = session.scalars(
            select(DocumentParagraph)
            .where(
                DocumentParagraph.document_version_id == version.id,
                DocumentParagraph.paragraph_number.between(position.para_from, position.para_to),
            )
            .order_by(DocumentParagraph.paragraph_number)
        ).all()
        if [p.paragraph_number for p in paragraphs] != list(
            range(position.para_from, position.para_to + 1)
        ):
            raise RuntimeError(f"{position.version_ref} lacks the cited paragraph(s)")
        filing = position.version_ref.rsplit("/", 1)[-1]
        single = position.para_from == position.para_to
        span = f"{position.para_from}" if single else f"{position.para_from}-{position.para_to}"
        citation = self._citation(
            case_id,
            position.key,
            version,
            raw_text=f"{position.version_ref}, para{'' if single else 's'}. {span}",
            display=f"{filing} · ¶{'' if single else '¶'}{span}",
            citation_type=CitationType.PARAGRAPH,
            page=paragraphs[0].page_from,
            pdf_page_index=paragraphs[0].pdf_page_index_from,
            para_from=position.para_from,
            para_to=position.para_to,
        )
        session.add(citation)
        session.flush()
        argument = Argument(
            id=_id(f"argument:{position.key}"),
            case_id=case_id,
            argument_key=position.key,
            party=position.party,
            title=position.title,
            # The party's own words, verbatim; the Court's summary stays separate.
            text="\n\n".join(p.text for p in paragraphs),
            document_id=version.document_id,
            document_version_id=version.id,
            para_from=position.para_from,
            para_to=position.para_to,
            citation_id=citation.id,
            finding_id=finding.id,
            source_scope="direct_source",
            underlying_source_ref=None,
            party_attribution=position.attribution,
            extraction_origin=_ORIGIN,
            verification_state=VerificationState.HUMAN_VERIFIED,
            verified_by=_REVIEWER,
            verified_at=_REVIEWED_AT,
        )
        session.add(argument)
        session.flush()
        return argument

    def _issue_sources(
        self,
        session: Session,
        case_id: uuid.UUID,
        issue: AppealIssue,
        arguments: list[Argument],
    ) -> list[AppealIssueSource]:
        start = (
            max(
                (
                    s.sequence
                    for s in session.scalars(
                        select(AppealIssueSource).where(AppealIssueSource.issue_id == issue.id)
                    )
                ),
                default=0,
            )
            + 1
        )
        rows: list[AppealIssueSource] = []
        for offset, argument in enumerate(arguments):
            defence = argument.party is Party.DEFENCE
            rows.append(
                AppealIssueSource(
                    id=_id(f"issue-source:{argument.argument_key}"),
                    issue_id=issue.id,
                    sequence=start + offset,
                    role="defence_position" if defence else "spo_position",
                    source_category="defence_argument" if defence else "spo_argument",
                    citation_id=argument.citation_id,
                    argument_id=argument.id,
                    excerpt=argument.text,
                    note="Party's own filing (direct source); distinct from the Court summary.",
                    classification_origin="source_derived",
                    verification_state=VerificationState.HUMAN_VERIFIED,
                    verified_by=_REVIEWER,
                    verified_at=_REVIEWED_AT,
                )
            )
        annex = self._public_version(session, _ANNEX_3_REF)
        note_page = session.scalar(
            select(DocumentPage).where(
                DocumentPage.document_version_id == annex.id, DocumentPage.pdf_page_index == 1
            )
        )
        if note_page is None or "Corrections Explanatory Note" not in (note_page.text or ""):
            raise RuntimeError(f"{_ANNEX_3_REF} lacks its corrections explanatory note")
        citation = self._citation(
            case_id,
            "annex-3",
            annex,
            raw_text=f"{_ANNEX_3_REF}, p. 2",
            display="F03667/COR/RED/A03/RED · p. 2",
            citation_type=CitationType.PAGE,
            page=note_page.page_number,
            pdf_page_index=note_page.pdf_page_index,
        )
        session.add(citation)
        session.flush()
        rows.append(
            AppealIssueSource(
                id=_id("issue-source:annex-3"),
                issue_id=issue.id,
                sequence=start + len(arguments),
                role="qualifying",
                source_category="spo_argument",
                citation_id=citation.id,
                excerpt=_explanatory_note(note_page.text or ""),
                note=(
                    "Partial context only: the SPO's note lists its corrections by category and "
                    "offers comparison versions on request; it does not show the substitutions."
                ),
                classification_origin="human_defined",
                review_process="Phase 23 owner-directed review of newly held sources",
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by=_REVIEWER,
                verified_at=_REVIEWED_AT,
            )
        )
        session.add_all(rows)
        session.flush()
        return rows

    @staticmethod
    def _summary_notes(session: Session, issue: AppealIssue) -> None:
        """The Phase 12 notes on the Court summaries said the underlying filings
        were unavailable; they are now held. The summaries themselves are untouched."""
        for role, filing in (("defence_position", "F03743"), ("spo_position", "F03746")):
            summary = session.scalar(
                select(AppealIssueSource)
                .join(Argument, Argument.id == AppealIssueSource.argument_id)
                .where(
                    AppealIssueSource.issue_id == issue.id,
                    AppealIssueSource.role == role,
                    Argument.source_scope == "court_summary",
                )
            )
            if summary is not None:
                summary.note = (
                    f"Court summary; the underlying {filing} is held and cited separately "
                    "as a direct source."
                )

    def _gaps(self, session: Session, issue: AppealIssue) -> tuple[list[str], list[str]]:
        entries = {
            entry.reference: entry
            for entry in session.scalars(
                select(AppealMissingMaterial).where(AppealMissingMaterial.issue_id == issue.id)
            )
        }
        for reference, version_ref in (("F03743", _DEFENCE_REF), ("F03746", _SPO_REF)):
            entry = entries.get(reference)
            if entry is None:
                raise RuntimeError(f"missing-material entry {reference} is not held")
            entry.state = "resolved"
            entry.resolved_source_ref = version_ref
        brief = entries.get("pre-correction SPO Final Trial Brief")
        if brief is not None:
            brief.reason = (
                "The earlier brief is not held, so the claimed substitutions cannot be "
                "independently compared. Annex 3 to the corrected brief "
                f"({_ANNEX_3_REF}) lists the corrections only by category."
            )
        session.flush()
        resolved = sorted(r for r, e in entries.items() if e.state == "resolved")
        still_open = sorted(r for r, e in entries.items() if e.state != "resolved")
        return resolved, still_open


def _explanatory_note(text: str) -> str:
    compact = " ".join(text.split())
    start = compact.find("Corrections Explanatory Note")
    return compact[start : start + 600] if start >= 0 else compact[:600]
