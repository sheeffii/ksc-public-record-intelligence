"""The synthetic fixture proves every traversal the roadmap requires:

Document → Version → Page → Citation
Witness → Transcript → Segment → Citation
Claim → Mention → Citation → Source
Finding → Evidence Link → Citation → Source
Relationship → Citation → Source
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.fixtures.demo import DEMO_CASE_NUMBER, load_demo_fixture
from ksc_api.models import (
    Case,
    Citation,
    Claim,
    Document,
    Finding,
    Relationship,
    ResolutionState,
    SourceRecord,
    Witness,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def session(demo_settings) -> Iterator[Session]:
    from ksc_api.db.session import get_sessionmaker

    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


def test_fixture_is_idempotent_and_synthetic(session):
    case, created = load_demo_fixture(session)
    assert created is False
    assert case.case_number == DEMO_CASE_NUMBER
    refs = session.scalars(select(Document.official_ref).where(Document.case_id == case.id)).all()
    assert all("DEMO" in ref for ref in refs)
    urls = session.scalars(select(SourceRecord.discovery_url)).all()
    assert urls and all(url.startswith("https://example.invalid/") for url in urls)


def test_document_version_page_citation(session):
    document = session.scalar(select(Document).where(Document.filing_number == "F-DEMO-001"))
    version = next(v for v in document.versions if v.official_version_ref == "F-DEMO-001/RED")
    page = next(p for p in version.pages if p.page_number == 2)
    assert page.has_redactions and page.redaction_extents
    citations = [
        c
        for c in version.citations_targeting
        if c.target_page == page.page_number and c.resolution_state == ResolutionState.RESOLVED
    ]
    assert citations
    assert all(c.display != "UNRESOLVED" for c in citations)


def test_witness_transcript_segment_citation(session):
    witness = session.scalar(select(Witness).where(Witness.code == "W-DEMO-001"))
    assert witness.is_protected and witness.person_id is None and witness.public_name is None
    appearance = witness.appearances[0]
    transcript = next(t for t in appearance.hearing.transcripts if t.id == appearance.transcript_id)
    segment = next(s for s in transcript.segments if s.witness_id == witness.id)
    citation = session.scalar(
        select(Citation).where(Citation.target_transcript_segment_id == segment.id)
    )
    assert citation is not None and citation.is_resolved
    assert (citation.target_line_from, citation.target_line_to) == (
        segment.line_from,
        segment.line_to,
    )


def test_claim_mention_citation_source(session):
    claim = session.scalar(select(Claim).where(Claim.claim_key == "CL-DEMO-001"))
    resolved = [m for m in claim.mentions if m.citation.is_resolved]
    unresolved = [m for m in claim.mentions if not m.citation.is_resolved]
    assert len(resolved) == 4 and len(unresolved) == 1
    sources = {
        m.citation.target_document.official_ref for m in resolved if m.citation.target_document
    }
    assert {"KSC-DEMO-0000/F-DEMO-002", "KSC-DEMO-0000/F-DEMO-003"} <= sources
    assert unresolved[0].citation.display == "UNRESOLVED"


def test_finding_evidence_link_citation_source(session):
    finding = session.scalar(select(Finding).where(Finding.finding_key == "FD-DEMO-001"))
    assert finding.judgment_document.official_ref == "KSC-DEMO-0000/F-DEMO-001"
    assert finding.citation is not None and finding.citation.target_finding_id == finding.id
    court_cited = [link for link in finding.evidence_links if link.court_cited]
    assert court_cited and all(link.court_cited_para == 13 for link in court_cited)
    transcript_link = next(
        link for link in finding.evidence_links if link.citation.target_transcript_id is not None
    )
    assert transcript_link.citation.target_transcript.official_ref == "T-DEMO-001"


def test_relationship_citation_source(session):
    case = session.scalar(select(Case).where(Case.case_number == DEMO_CASE_NUMBER))
    edges = session.scalars(select(Relationship).where(Relationship.case_id == case.id)).all()
    assert len(edges) == 12
    assert all(edge.citation_id is not None for edge in edges)
    provenance = {edge.citation.resolution_state for edge in edges}
    assert provenance == {ResolutionState.RESOLVED, ResolutionState.UNRESOLVED}


def test_discovery_chain_case_page_to_transcript(session):
    record = session.scalar(
        select(SourceRecord).where(SourceRecord.external_record_id == "DEMO-HEARING-001")
    )
    assert record.source_system.value == "ksc_case_page"
    assert record.hearing_id is not None and record.transcript_id is not None
    transcript_record = session.scalar(
        select(SourceRecord).where(SourceRecord.external_record_id == "DEMO-REC-001")
    )
    assert transcript_record.document_version_id is not None
