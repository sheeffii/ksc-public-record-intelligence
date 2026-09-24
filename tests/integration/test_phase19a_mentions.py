"""Phase 19A verified mentions: idempotent projection, provenance, privacy,
review-required handling, no status inference, and the mentions API."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import select

from ksc_api.models import (
    Case,
    Document,
    DocumentPage,
    DocumentParagraph,
    DocumentVersion,
    DocumentVersionType,
    EntityOccurrence,
    Exhibit,
    Hearing,
    Organization,
    Person,
    PersonAlias,
    Transcript,
    TranscriptSegment,
    Visibility,
    Witness,
    WitnessIdentityStatus,
)
from ksc_ingestion.verified_mentions import Phase19MentionProjector
from ksc_ingestion.verified_mentions_gate import run_phase19a_gate

pytestmark = pytest.mark.integration

CASE_NUMBER = "KSC-TEST-19A"
_NS = uuid.UUID("0d9c8f1e-19a0-4a5b-8c7d-6e5f4a3b2c1d")
PAGE_TEXT = (
    "1. Witness W01234 described exhibit P00003, which was admitted, and NATO.\n"
    "Footnote: W99999 and P00999 are not registered."
)
PARAGRAPH = "1. Witness W01234 described exhibit P00003, which was admitted, and NATO."


def _id(name: str) -> uuid.UUID:
    return uuid.uuid5(_NS, name)


def _seed(session) -> None:  # type: ignore[no-untyped-def]
    case_id = _id("case")
    objects = [
        Case(id=case_id, case_number=CASE_NUMBER, title="Phase 19A test", court="Test"),
        Document(
            id=_id("doc"),
            case_id=case_id,
            official_ref=f"{CASE_NUMBER}/F00001",
            title="Public filing",
            document_type="filing",
            language="en",
        ),
        DocumentVersion(
            id=_id("ver"),
            document_id=_id("doc"),
            official_version_ref=f"{CASE_NUMBER}/F00001/RED",
            version_type=DocumentVersionType.PUBLIC_REDACTED,
        ),
        DocumentPage(
            id=_id("page"),
            document_version_id=_id("ver"),
            pdf_page_index=0,
            page_number=1,
            text=PAGE_TEXT,
        ),
        DocumentParagraph(
            id=_id("para"),
            document_version_id=_id("ver"),
            sequence=0,
            paragraph_number=1,
            pdf_page_index_from=0,
            pdf_page_index_to=0,
            text=PARAGRAPH,
        ),
        Document(
            id=_id("secret-doc"),
            case_id=case_id,
            official_ref=f"{CASE_NUMBER}/F00002",
            title="Not public",
            document_type="filing",
            visibility=Visibility.NOT_PUBLIC,
        ),
        DocumentVersion(
            id=_id("secret-ver"),
            document_id=_id("secret-doc"),
            official_version_ref=f"{CASE_NUMBER}/F00002",
            version_type=DocumentVersionType.ORIGINAL,
            visibility=Visibility.NOT_PUBLIC,
        ),
        DocumentPage(
            id=_id("secret-page"),
            document_version_id=_id("secret-ver"),
            pdf_page_index=0,
            page_number=1,
            text="W01234 NATO P00003",
        ),
        Document(
            id=_id("t-doc"),
            case_id=case_id,
            official_ref=f"{CASE_NUMBER}/T/2024-01-01",
            title="Transcript",
            document_type="transcript",
            language="en",
        ),
        DocumentVersion(
            id=_id("t-ver"),
            document_id=_id("t-doc"),
            official_version_ref=f"{CASE_NUMBER}/T/2024-01-01/sqi",
            version_type=DocumentVersionType.TRANSLATION,
        ),
        Hearing(id=_id("hearing"), case_id=case_id, hearing_date=date(2024, 1, 1)),
        Transcript(
            id=_id("transcript"),
            hearing_id=_id("hearing"),
            document_version_id=_id("t-ver"),
            language="en",
        ),
        Person(
            id=_id("judge"),
            case_id=case_id,
            slug="judge-smith",
            display_name="Judge Smith",
            public_role="judge",
        ),
        Person(
            id=_id("counsel"),
            case_id=case_id,
            slug="counsel_or_participant-smith",
            display_name="Smith",
            public_role="counsel_or_participant",
        ),
        PersonAlias(id=_id("a1"), person_id=_id("judge"), alias="JUDGE SMITH"),
        PersonAlias(id=_id("a2"), person_id=_id("counsel"), alias="MR. SMITH"),
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
            status="unknown",
            visibility=Visibility.PUBLIC,
        ),
        Organization(
            id=_id("nato"), case_id=case_id, slug="nato", name="NATO", name_variants=["NATO"]
        ),
    ]
    for obj in objects:
        session.merge(obj)
        session.flush()
    segments = [
        ("JUDGE SMITH", "Witness W01234 may continue.", False),
        ("MR. SMITH", "Thank you.", False),
        (None, "", True),
    ]
    for sequence, (speaker, text, closed) in enumerate(segments):
        session.merge(
            TranscriptSegment(
                id=_id(f"seg-{sequence}"),
                transcript_id=_id("transcript"),
                sequence=sequence,
                page_number=3,
                pdf_page_index=2,
                line_from=sequence + 1,
                line_to=sequence + 1,
                speaker=speaker,
                text=text,
                closed_session=closed,
            )
        )
    session.flush()


@pytest.fixture
def phase19a_settings(migrated_database_url: str, monkeypatch: pytest.MonkeyPatch):
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


def _rows(sessions) -> list[EntityOccurrence]:  # type: ignore[no-untyped-def]
    with sessions() as session:
        case_id = session.scalar(select(Case.id).where(Case.case_number == CASE_NUMBER))
        return list(
            session.scalars(
                select(EntityOccurrence)
                .where(EntityOccurrence.case_id == case_id)
                .order_by(EntityOccurrence.id)
            )
        )


def test_projection_is_idempotent_public_only_and_fail_closed(phase19a_settings) -> None:
    sessions = phase19a_settings
    projector = Phase19MentionProjector(sessions, case_number=CASE_NUMBER)
    first = projector.run()
    first_rows = [(r.id, r.char_start, r.char_end, r.mention_state) for r in _rows(sessions)]
    second = projector.run()
    rows = _rows(sessions)
    assert [(r.id, r.char_start, r.char_end, r.mention_state) for r in rows] == first_rows
    assert first.by_kind_state == second.by_kind_state
    assert second.legacy_rows_removed == 0
    assert first.unregistered_witness_codes == 1
    assert first.unregistered_exhibit_ids == 1

    # Not-public text and closed-session segments produce nothing.
    assert all(r.document_version_id != _id("secret-ver") for r in rows)
    with sessions() as session:
        pages = {_id("ver"): PAGE_TEXT}
        segments = {
            s.id: s
            for s in session.scalars(select(TranscriptSegment)).all()
            if s.id in {_id("seg-0"), _id("seg-1")}
        }
        for row in rows:
            assert row.rule_id and row.rule_version and row.projection_run_id == second.run_id
            if row.char_anchor == "document_page_text":
                source = pages[row.document_version_id]
            elif row.char_anchor == "transcript_speaker_label":
                source = segments[row.transcript_segment_id].speaker or ""
            else:
                source = segments[row.transcript_segment_id].text
            assert source[row.char_start : row.char_end] == row.occurrence_text

        # Unknown codes are never auto-created; status is never inferred.
        assert session.scalar(select(Witness).where(Witness.code == "W99999")) is None
        assert session.get(Exhibit, _id("exhibit")).status == "unknown"  # type: ignore[union-attr]

    witness_rows = [r for r in rows if r.witness_id is not None]
    assert {r.occurrence_text for r in witness_rows} == {"W01234"}
    assert {r.char_anchor for r in witness_rows} == {
        "document_page_text",
        "transcript_segment_text",
    }
    page_witness = next(r for r in witness_rows if r.char_anchor == "document_page_text")
    assert page_witness.paragraph_number == 1 and page_witness.language == "en"
    segment_witness = next(r for r in witness_rows if r.char_anchor == "transcript_segment_text")
    assert segment_witness.line_from == 1 and segment_witness.language == "sq"

    people = {r.person_id: r for r in rows if r.person_id is not None}
    assert people[_id("judge")].mention_state == "verified"
    assert people[_id("counsel")].mention_state == "review_required"
    assert people[_id("counsel")].review_required is True

    with sessions() as session:
        case = session.scalar(select(Case).where(Case.case_number == CASE_NUMBER))
        report = run_phase19a_gate(session, case, date(2026, 9, 24))  # type: ignore[arg-type]
    assert report.passed
    assert report.provenance_violations == 0
    assert report.protected_identity_violations == 0
    assert report.smith_review_required == 1
    assert report.kinds["person"].verified == 1
    assert report.kinds["witness"].unregistered_identifiers == 1


def test_mentions_api_separates_verified_review_required_and_search(phase19a_settings) -> None:
    from fastapi.testclient import TestClient

    from ksc_api.main import create_app

    Phase19MentionProjector(phase19a_settings, case_number=CASE_NUMBER).run()
    with TestClient(create_app()) as client:
        judge = client.get("/api/v1/people/judge-smith/mentions").json()
        assert judge["total"] == 1
        item = judge["items"][0]
        assert item["match_class"] == "VERIFIED_MENTION"
        assert item["rule_id"] == "person.speaker_label.role_qualified"
        assert item["line_from"] == 1 and "line=1" in item["target_path"]

        counsel = client.get("/api/v1/people/counsel_or_participant-smith/mentions").json()
        assert [i["match_class"] for i in counsel["items"]] == ["REVIEW_REQUIRED"]
        verified_only = client.get(
            "/api/v1/people/counsel_or_participant-smith/mentions?state=verified"
        ).json()
        assert verified_only["total"] == 0
        assert client.get("/api/v1/people/judge-smith/mentions?state=rejected").status_code == 422

        witness = client.get("/api/v1/witnesses/W01234/mentions").json()
        assert witness["total"] == 2
        assert all(set(i["occurrence_text"]) <= set("W0123456789") for i in witness["items"])
        page_item = next(i for i in witness["items"] if i["char_anchor"] == "document_page_text")
        assert page_item["paragraph"] == 1 and "para=1" in page_item["target_path"]

        exhibit = client.get("/api/v1/exhibits/P00003/mentions").json()
        assert exhibit["total"] == 1
        organization = client.get("/api/v1/organizations/nato/mentions").json()
        assert organization["total"] == 1

        assert client.get("/api/v1/witnesses/W99999/mentions").status_code == 404
        hits = client.get("/api/v1/search", params={"q": "NATO"}).json()["hits"]
        assert hits and {hit["match_class"] for hit in hits} == {"SEARCH_MATCH"}
