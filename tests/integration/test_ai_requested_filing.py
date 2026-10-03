"""A question naming a held party filing is answered from that filing's own
text, attributed to its party; a Court summary of it is secondary context only
and never answers on its own."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import delete, select

from ksc_api.models import (
    AiRun,
    Argument,
    ArtifactStatus,
    Case,
    Document,
    DocumentChunk,
    DocumentVersion,
    DocumentVersionType,
    Party,
    VerificationState,
    Visibility,
)
from ksc_api.services.ai_providers import DeterministicExtractiveProvider
from ksc_api.services.ai_research import AiResearchService

pytestmark = pytest.mark.integration

_REQUESTER = "test-requested-filing"
_FILINGS = {
    "F09743": (
        Party.DEFENCE,
        "Joint Defence submissions: the filing asks the Panel to strike the synthetic "
        "amendments to the brief because they exceed a permissible correction.",
    ),
    "F09746": (
        Party.SPO,
        "Prosecution response: the filing argues the synthetic amendments to the brief "
        "are a permissible correction and should not be struck.",
    ),
}


@pytest.fixture
def filings(demo_settings) -> Iterator[dict[str, uuid.UUID]]:
    from ksc_api.db.session import get_sessionmaker
    from ksc_api.fixtures.demo import DEMO_CASE_NUMBER

    sessions = get_sessionmaker()
    created: dict[str, uuid.UUID] = {}
    with sessions() as session:
        case = session.scalar(select(Case).where(Case.case_number == DEMO_CASE_NUMBER))
        assert case is not None
        court = session.scalar(select(Argument).where(Argument.argument_key == "AR-DEMO-003"))
        assert court is not None
        for number, (party, text) in _FILINGS.items():
            doc = Document(
                case_id=case.id,
                official_ref=f"{DEMO_CASE_NUMBER}/{number}",
                filing_number=number,
                title=f"Synthetic party filing {number}",
                document_type="filing",
                language="en",
                visibility=Visibility.PUBLIC,
            )
            session.add(doc)
            session.flush()
            version = DocumentVersion(
                document_id=doc.id,
                official_version_ref=f"{DEMO_CASE_NUMBER}/{number}",
                version_type=DocumentVersionType.ORIGINAL,
                visibility=Visibility.PUBLIC,
                artifact_status=ArtifactStatus.FETCHED,
                sha256=(digest := hashlib.sha256(f"{uuid.uuid4()}".encode()).hexdigest()),
                storage_key=f"test/{digest}.pdf",
                byte_size=len(text),
                fetched_at=datetime.now(UTC),
                parsed_at=datetime.now(UTC),
                source_url=f"https://repository.scp-ks.org/LW/Published/Filing/x/{number}.pdf",
            )
            session.add(version)
            session.flush()
            session.add(
                DocumentChunk(
                    document_version_id=version.id,
                    sequence=0,
                    page_from=1,
                    page_to=1,
                    para_from=1,
                    para_to=1,
                    pdf_page_index_from=0,
                    pdf_page_index_to=0,
                    text=text,
                    char_count=len(text),
                )
            )
            # The Court's summary of this party's position, naming the filing.
            session.add(
                Argument(
                    case_id=case.id,
                    argument_key=f"AR-TEST-SUMMARY-{number}",
                    party=party,
                    title="Court summary (synthetic)",
                    text=f"The Panel summarises filing {number}: the synthetic amendments "
                    "to the brief are disputed.",
                    document_id=court.document_id,
                    document_version_id=court.document_version_id,
                    para_from=court.para_from,
                    para_to=court.para_to,
                    citation_id=court.citation_id,
                    finding_id=court.finding_id,
                    party_attribution=party.value,
                    source_scope="court_summary",
                    underlying_source_ref=number,
                    verification_state=VerificationState.HUMAN_VERIFIED,
                    verified_by="test-reviewer",
                    verified_at=datetime.now(UTC),
                )
            )
            created[number] = version.id
        session.commit()
    yield created
    with sessions() as session:
        session.execute(delete(AiRun).where(AiRun.requested_by == _REQUESTER))
        session.execute(delete(Argument).where(Argument.argument_key.like("AR-TEST-SUMMARY-%")))
        session.execute(delete(Document).where(Document.filing_number.in_(list(_FILINGS))))
        session.commit()


def _ask(question: str) -> AiRun:
    from ksc_api.config import get_settings
    from ksc_api.db.session import get_sessionmaker
    from ksc_api.fixtures.demo import DEMO_CASE_NUMBER

    with get_sessionmaker()() as session:
        case = session.scalar(select(Case).where(Case.case_number == DEMO_CASE_NUMBER))
        assert case is not None
        run = AiResearchService(
            session, case, get_settings(), provider=DeterministicExtractiveProvider()
        ).create_run(question, requested_by=_REQUESTER)
        session.commit()
        session.refresh(run)
        sources = sorted(run.retrieval_sources, key=lambda source: source.rank)
        session.expunge_all()
        run.__dict__["_sorted"] = sources
        return run


@pytest.mark.parametrize(
    ("number", "category"), [("F09743", "defence_argument"), ("F09746", "spo_argument")]
)
def test_held_filing_text_outranks_the_court_summary_of_it(
    filings: dict[str, uuid.UUID], number: str, category: str
) -> None:
    run = _ask(f"What does filing {number} establish?")
    sources = run.__dict__["_sorted"]
    assert not run.answer_withheld and sources
    own = [s for s in sources if s.document_version_id == filings[number]]
    summaries = [s for s in sources if s.argument_id is not None]
    assert own and own[0].rank == 1
    assert {s.source_category for s in own} == {category}
    # The summary stays a separate source on the Court's document, ranked after.
    assert all(s.document_version_id != filings[number] for s in summaries)
    assert all(s.rank > max(o.rank for o in own) for s in summaries)
    assert all(s.excerpt in _FILINGS[number][1] or number in s.excerpt for s in own)


def test_unsupported_question_about_a_held_filing_fails_closed(
    filings: dict[str, uuid.UUID],
) -> None:
    run = _ask("What does filing F09743 say about lunar treaty remedies?")
    assert run.answer_withheld
    assert run.__dict__["_sorted"] == []
