"""Phase 19B: aliases, witness ↔ hearing appearances, exhibit status history,
typed evidence edges, resolver rules, reconciliation and the read API."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import select

from ksc_api.models import (
    Case,
    CitationType,
    Document,
    DocumentPage,
    DocumentVersion,
    DocumentVersionType,
    EntityKind,
    Exhibit,
    ExhibitStatusEvent,
    Hearing,
    IdentifierKind,
    Person,
    PersonAlias,
    RecordIdentifier,
    Relationship,
    RelationshipOrigin,
    ResolutionState,
    Transcript,
    TranscriptSegment,
    Visibility,
    Witness,
    WitnessAppearance,
    WitnessIdentityStatus,
)
from ksc_ingestion.citation_resolution import (
    ExtractedCitation,
    rebuild_identifier_index,
    resolve_extracted,
)
from ksc_ingestion.phase19b import Phase19BPipeline
from ksc_ingestion.phase19b_report import run_phase19b_report

pytestmark = pytest.mark.integration

CASE_NUMBER = "KSC-TEST-19B"
_NS = uuid.UUID("19b19b19-0000-4000-8000-000000019b19")
COVER = (
    "KSC-TEST-19B/F00010 1 12 March 2024\n"
    "Specialist Prosecutor v. Hashim Thaçi, Kadri Veseli, Rexhep\n  Selimi and Jakup Krasniqi\n"
    "Before: Trial Panel II\n1. The Accused Hashim Thaçi and Kadri VESELI are named here."
)
HEADERS = [
    "Kosovo Specialist Chambers - Basic Court Procedural Matters (Open Session) Page 100",
    "Kosovo Specialist Chambers - Basic Court Witness: W01234 (Open Session) Page 101 "
    "Examination by Mr. Doe 1 Q. Good morning.",
    "Kosovo Specialist Chambers - Basic Court Witness: W01234 (Private Session) Page 102",
    "Kosovo Specialist Chambers - Basic Court Witness: Ada Lovelace (Open Session) Page 103 "
    "Cross-examination by Ms. Roe 1 Q. Thank you.",
]
ACCUSED = ("thaci", "veseli", "selimi", "krasniqi")


def _id(name: str) -> uuid.UUID:
    return uuid.uuid5(_NS, name)


def _seed(session) -> None:  # type: ignore[no-untyped-def]
    case_id = _id("case")
    objects: list[object] = [
        Case(id=case_id, case_number=CASE_NUMBER, title="Phase 19B test", court="Test"),
        Document(
            id=_id("filing"),
            case_id=case_id,
            official_ref=f"{CASE_NUMBER}/F00010",
            filing_number="F00010",
            title="Public filing",
            document_type="submission",
            language="en",
        ),
        DocumentVersion(
            id=_id("filing-v"),
            document_id=_id("filing"),
            official_version_ref=f"{CASE_NUMBER}/F00010/RED",
            version_type=DocumentVersionType.PUBLIC_REDACTED,
        ),
        DocumentPage(
            id=_id("cover"),
            document_version_id=_id("filing-v"),
            pdf_page_index=0,
            page_number=1,
            text=COVER,
        ),
        Document(
            id=_id("annex"),
            case_id=case_id,
            official_ref=f"{CASE_NUMBER}/F00020/A01",
            filing_number="F00020",
            title="Annex only",
            document_type="filing_annex",
            language="en",
        ),
        Document(
            id=_id("t-doc"),
            case_id=case_id,
            official_ref=f"{CASE_NUMBER}/T/2024-04-29",
            title="Trial Hearing",
            document_type="transcript",
            language="en",
        ),
        DocumentVersion(
            id=_id("t-ver"),
            document_id=_id("t-doc"),
            official_version_ref=f"{CASE_NUMBER}/T/2024-04-29",
            version_type=DocumentVersionType.ORIGINAL,
        ),
        Hearing(
            id=_id("hearing"),
            case_id=case_id,
            hearing_date=date(2024, 4, 29),
            session_label="Trial Hearing - 29 April 2024",
        ),
        Transcript(
            id=_id("transcript"),
            hearing_id=_id("hearing"),
            document_version_id=_id("t-ver"),
            official_ref=f"{CASE_NUMBER}/T/2024-04-29",
            language="en",
            page_from=100,
            page_to=103,
        ),
        Witness(
            id=_id("witness"),
            case_id=case_id,
            code="W01234",
            identity_status=WitnessIdentityStatus.PROTECTED_CODE,
            protective_measures=[],
        ),
        Exhibit(
            id=_id("exhibit"),
            case_id=case_id,
            official_exhibit_id="P00003",
            title="Exhibit P00003",
            status="admitted",  # a stale guessed value: must be re-derived to unknown
            visibility=Visibility.PUBLIC,
        ),
        Exhibit(
            id=_id("exhibit-2"),
            case_id=case_id,
            official_exhibit_id="P01137",
            title="Exhibit P01137",
            visibility=Visibility.PUBLIC,
        ),
        RecordIdentifier(
            id=_id("rid-exhibit"),
            case_id=case_id,
            identifier="P00003",
            normalized_identifier="P00003",
            identifier_kind=IdentifierKind.EXHIBIT,
            entity_kind=EntityKind.EXHIBIT,
            exhibit_id=_id("exhibit"),
        ),
    ]
    for surname in ACCUSED:
        objects.append(
            Person(
                id=_id(f"accused-{surname}"),
                case_id=case_id,
                slug=f"accused-{surname}",
                display_name=f"Accused {surname.title()}",
                public_role="accused",
            )
        )
    objects.append(
        Person(
            id=_id("judge"),
            case_id=case_id,
            slug="judge-smith",
            display_name="Judge Smith",
            public_role="judge",
        )
    )
    objects.append(PersonAlias(id=_id("judge-alias"), person_id=_id("judge"), alias="JUDGE SMITH"))
    for index, header in enumerate(HEADERS):
        objects.append(
            DocumentPage(
                id=_id(f"t-page-{index}"),
                document_version_id=_id("t-ver"),
                pdf_page_index=index,
                page_number=100 + index,
                text=header,
            )
        )
    segments = [
        (
            "THE COURT OFFICER",
            "And it will be assigned Exhibit P01137, classified as confidential.",
        ),
        ("JUDGE SMITH", "Proofing Note 1 was admitted as Exhibit P01137. The Panel rules."),
        (
            "MR. DOE",
            "P00003 was admitted through the bar table, it was admitted as Exhibit P00003.",
        ),
        ("JUDGE SMITH", "The witness admits a number of facts in P00003."),
    ]
    for obj in objects:
        session.merge(obj)
        session.flush()
    for sequence, (speaker, text) in enumerate(segments):
        session.merge(
            TranscriptSegment(
                id=_id(f"seg-{sequence}"),
                transcript_id=_id("transcript"),
                sequence=sequence,
                page_number=101,
                pdf_page_index=1,
                line_from=sequence + 1,
                line_to=sequence + 1,
                speaker=speaker,
                text=text,
            )
        )
    session.flush()


@pytest.fixture
def phase19b(migrated_database_url: str, monkeypatch: pytest.MonkeyPatch):
    from ksc_api import config
    from ksc_api.db.session import get_engine, get_sessionmaker, session_scope

    monkeypatch.setenv("DATABASE_URL", migrated_database_url)
    monkeypatch.setenv("CASE_ID", CASE_NUMBER)
    for cached in (config.get_settings, get_engine, get_sessionmaker):
        cached.cache_clear()
    with session_scope() as session:
        _seed(session)
    yield get_sessionmaker()
    for cached in (config.get_settings, get_engine, get_sessionmaker):
        cached.cache_clear()


def _snapshot(sessions) -> dict[str, list[tuple[object, ...]]]:  # type: ignore[no-untyped-def]
    with sessions() as session:
        case_id = _id("case")
        return {
            "appearances": sorted(
                (str(a.id), a.page_from, a.page_to, a.signal_text)
                for a in session.scalars(
                    select(WitnessAppearance).where(WitnessAppearance.hearing_id == _id("hearing"))
                )
            ),
            "events": sorted(
                (str(e.id), e.event_type, e.exhibit_identifier)
                for e in session.scalars(
                    select(ExhibitStatusEvent).where(ExhibitStatusEvent.case_id == case_id)
                )
            ),
            "edges": sorted(
                (str(r.id), r.relationship_type.value, r.evidence_count)
                for r in session.scalars(
                    select(Relationship).where(
                        Relationship.case_id == case_id,
                        Relationship.extraction_origin
                        == RelationshipOrigin.DETERMINISTIC_OCCURRENCE,
                    )
                )
            ),
        }


def test_pipeline_is_idempotent_source_backed_and_fail_closed(phase19b) -> None:
    sessions = phase19b
    first = Phase19BPipeline(sessions, case_number=CASE_NUMBER).run()
    before = _snapshot(sessions)
    Phase19BPipeline(sessions, case_number=CASE_NUMBER).run()
    assert _snapshot(sessions) == before
    assert first.detail["aliases"]["captions_bound"] == 1

    with sessions() as session:
        # Full names come only from the caption, with exact spans.
        aliases = session.scalars(
            select(PersonAlias).where(PersonAlias.alias_kind == "full_name")
        ).all()
        caption = {a.alias for a in aliases if a.rule_id == "person.alias.case_caption"}
        assert caption == {"Hashim Thaçi", "Kadri Veseli", "Rexhep Selimi", "Jakup Krasniqi"}
        for alias in aliases:
            if alias.rule_id != "person.alias.case_caption":
                continue
            span = COVER[alias.source_char_start : alias.source_char_end]  # type: ignore[index]
            assert " ".join(span.split()) == alias.alias

        # Appearances: header-backed only, per transcript version, exact signal.
        appearances = session.scalars(
            select(WitnessAppearance).where(WitnessAppearance.hearing_id == _id("hearing"))
        ).all()
        code = next(a for a in appearances if a.witness_id == _id("witness"))
        assert (code.page_from, code.page_to, code.header_pages) == (101, 102, 2)
        assert (code.open_session_pages, code.private_session_pages) == (1, 1)
        assert code.examinations == [{"text": "Examination by Mr. Doe", "page": 101}]
        assert HEADERS[1][code.signal_char_start : code.signal_char_end] == code.signal_text  # type: ignore[index]
        named = next(a for a in appearances if a.person_id is not None)
        person = session.get(Person, named.person_id)
        assert person is not None and person.display_name == "Ada Lovelace"
        assert person.public_role == "witness"
        # The protected code never gains an identity.
        witness = session.get(Witness, _id("witness"))
        assert witness is not None and witness.person_id is None and witness.public_name is None

        # Exhibit status: court speakers only; stale guesses reset to unknown.
        events = session.scalars(
            select(ExhibitStatusEvent).where(ExhibitStatusEvent.case_id == _id("case"))
        ).all()
        assert sorted((e.exhibit_identifier, e.event_type) for e in events) == [
            ("P01137", "admitted"),
            ("P01137", "number_assigned"),
        ]
        assert next(e for e in events if e.event_type == "number_assigned").classification == (
            "confidential"
        )
        guessed = session.get(Exhibit, _id("exhibit"))
        admitted = session.get(Exhibit, _id("exhibit-2"))
        assert guessed is not None and guessed.status == "unknown"
        assert admitted is not None and admitted.status == "admitted"
        assert admitted.status_event_id is not None and admitted.admitted_date is None

        # Typed edges: exactly one evidence anchor; counts reproduce.
        edges = session.scalars(
            select(Relationship).where(
                Relationship.case_id == _id("case"),
                Relationship.extraction_origin == RelationshipOrigin.DETERMINISTIC_OCCURRENCE,
            )
        ).all()
        testified = [e for e in edges if e.relationship_type.value == "testified_at"]
        mentioned = [e for e in edges if e.relationship_type.value == "mentioned_in"]
        assert len(testified) == 2 and all(e.witness_appearance_id for e in testified)
        assert mentioned and all(e.entity_occurrence_id for e in mentioned)
        assert all(e.citation_id is None for e in edges)

        case = session.scalar(select(Case).where(Case.case_number == CASE_NUMBER))
        assert case is not None
        report = run_phase19b_report(session, case, date(2026, 9, 24))
    assert report["passed"], report["checks"]
    assert all(value == 0 for value in report["checks"].values())


def test_resolver_rules_are_deterministic_and_record_how(phase19b) -> None:
    with phase19b() as session, session.begin():
        case = session.scalar(select(Case).where(Case.case_number == CASE_NUMBER))
        assert case is not None
        rebuild_identifier_index(session, case)

        def resolve(identifier: str, kind: CitationType, source: str, **coords: int):  # type: ignore[no-untyped-def]
            return resolve_extracted(
                session,
                case,
                ExtractedCitation(identifier, identifier, kind, **coords),
                source_version_ref=source,
            )

        main = f"{CASE_NUMBER}/F00010/RED"
        # P0003 is the same official number as P00003; an unregistered one stays unresolved.
        padded = resolve("P0003", CitationType.EXHIBIT, main)
        assert (padded.state, padded.rule) == (ResolutionState.RESOLVED, "identifier.zero_padded")
        assert padded.exhibit_id == _id("exhibit")
        assert resolve("P1234", CitationType.EXHIBIT, main).state == ResolutionState.UNRESOLVED
        exhibit = resolve("P00003", CitationType.EXHIBIT, main)
        assert (exhibit.state, exhibit.rule) == (ResolutionState.RESOLVED, "identifier.exact")
        # The annex does not answer for its base filing.
        base = resolve("F00020", CitationType.DOCUMENT, main)
        assert (base.state, base.rule) == (ResolutionState.UNRESOLVED, "unresolved.target_not_held")
        # Bare filing numbers inside a subcase filing are ambiguous, never forced.
        subcase = resolve("F00010", CitationType.DOCUMENT, f"{CASE_NUMBER}/IA042/F00005/RED")
        assert (subcase.state, subcase.rule) == (
            ResolutionState.AMBIGUOUS,
            "ambiguous.subcase_bare_filing",
        )
        assert subcase.candidate_identifiers and len(subcase.candidate_identifiers) == 2
        # Hearing-date transcript citations resolve to the held transcript.
        dated = resolve("T.20240429", CitationType.TRANSCRIPT, main, target_page=20240429)
        assert (dated.state, dated.rule) == (ResolutionState.RESOLVED, "transcript.hearing_date")
        assert dated.transcript_id == _id("transcript")
        missing = resolve("T.20240430", CitationType.TRANSCRIPT, main, target_page=20240430)
        assert missing.rule == "unresolved.transcript_date_not_held"
        paged = resolve("T.101", CitationType.TRANSCRIPT, main, target_page=101)
        assert (paged.state, paged.rule) == (ResolutionState.RESOLVED, "transcript.page_range")
        session.rollback()


def test_intelligence_api_serves_bounded_provenance(phase19b) -> None:
    from fastapi.testclient import TestClient

    from ksc_api.main import create_app

    Phase19BPipeline(phase19b, case_number=CASE_NUMBER).run()
    with TestClient(create_app()) as client:
        first = client.get("/api/v1/network/edges", params={"limit": 1}).json()
        assert first["total"] >= 3 and len(first["items"]) == 1 and first["next_cursor"]
        second = client.get(
            "/api/v1/network/edges", params={"limit": 1, "cursor": first["next_cursor"]}
        ).json()
        assert second["items"][0]["id"] > first["items"][0]["id"]

        testified = client.get(
            "/api/v1/network/edges", params={"relationship_type": "testified_at"}
        ).json()
        assert testified["total"] == 2
        provenance = testified["items"][0]["provenance"]
        assert provenance["kind"] == "witness_appearance"
        assert provenance["rule"] == "witness.transcript_page_header"
        assert "pdfPage=" in provenance["target_path"]
        protected = [n for n in testified["nodes"] if n["entity_kind"] == "witness"]
        assert protected and all(n["protected"] and n["label"] == "W01234" for n in protected)

        focused = client.get(
            "/api/v1/network/edges",
            params={"focus_ref": "accused-thaci", "evidence_kind": "entity_occurrence"},
        ).json()
        assert focused["total"] == 1
        item = focused["items"][0]
        assert item["relationship_type"] == "mentioned_in"
        assert item["evidence_count"] == 2  # caption + paragraph 1
        assert item["provenance"]["text"] == "Hashim Thaçi"

        appearances = client.get("/api/v1/witnesses/W01234/appearances").json()
        assert [
            (a["page_from"], a["page_to"], a["private_session_pages"]) for a in appearances
        ] == [(101, 102, 1)]
        named = client.get("/api/v1/people/witness-ada-lovelace/appearances").json()
        assert named[0]["examinations"][0]["text"] == "Cross-examination by Ms. Roe"
        events = client.get("/api/v1/exhibits/P01137/status-events").json()
        assert [e["event_type"] for e in events] == ["number_assigned", "admitted"]
        assert all(e["provenance"]["kind"] == "exhibit_status_event" for e in events)
        assert client.get("/api/v1/exhibits/P00003/status-events").json() == []
        assert client.get("/api/v1/witnesses/W99999/appearances").status_code == 404
        assert (
            client.get("/api/v1/network/edges", params={"focus_ref": "nope"}).json()["total"] == 0
        )
