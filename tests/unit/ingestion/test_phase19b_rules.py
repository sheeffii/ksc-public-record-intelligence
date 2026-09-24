"""Phase 19B deterministic rules: identity, witness headers, exhibit status,
citation resolution helpers. Negative cases carry as much weight as positives."""

import uuid
from collections import Counter
from datetime import date

from ksc_api.models import Document
from ksc_ingestion.citation_resolution import _hearing_date, _identifier_aliases
from ksc_ingestion.exhibit_status import speaker_role, status_statements
from ksc_ingestion.identity import (
    IdentityState,
    bind_caption_accused,
    caption_lists,
    classify_label,
    speaker_label_identity,
)
from ksc_ingestion.witness_appearances import parse_page_header

ACCUSED = {name: uuid.uuid4() for name in ("thaci", "veseli", "selimi", "krasniqi")}
CAPTION = (
    "THE SPECIALIST PROSECUTOR\n"
    "Specialist Prosecutor v. Hashim Thaçi, Kadri Veseli, Rexhep\n\n   Selimi and Jakup Krasniqi\n"
    "Before: Trial Panel II"
)


# ------------------------------------------------------------- identity --
def test_caption_binds_each_accused_once_with_exact_spans() -> None:
    (names,) = caption_lists(CAPTION)
    bound = bind_caption_accused(names, ACCUSED)
    assert [" ".join(name.name.split()) for _, name in bound] == [
        "Hashim Thaçi",
        "Kadri Veseli",
        "Rexhep Selimi",
        "Jakup Krasniqi",
    ]
    assert all(CAPTION[name.start : name.end] == name.name for _, name in bound)
    assert [person for person, _ in bound] == [ACCUSED[k] for k in ACCUSED]


def test_caption_never_binds_other_cases_homoglyphs_or_repeated_surnames() -> None:
    other_case = caption_lists("Specialist Prosecutor v. Sabit Januzi and Ismet Bahtijari")
    assert other_case and bind_caption_accused(other_case[0], ACCUSED) == []
    # Cyrillic "ҫ" is not the Latin "ç": the caption does not parse at all.
    assert (
        caption_lists("Specialist Prosecutor v. Hashim Thaҫi, Kadri Veseli and Jakup Krasniqi")
        == []
    )
    (twice,) = caption_lists("Specialist Prosecutor v. Hashim Thaçi and Ilir Thaçi")
    assert bind_caption_accused(twice, ACCUSED) == []


def test_speaker_label_states_are_explicit() -> None:
    judge, counsel, smith = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    labels = {
        "JUDGE SMITH": (judge, "judge", "smith"),
        "MR. EMMERSON": (counsel, "counsel_or_participant", "emmerson"),
        "MR. SMITH": (smith, "counsel_or_participant", "smith"),
    }
    counts = Counter({"smith": 2, "emmerson": 1})
    verified = classify_label("JUDGE SMITH", labels, counts)
    assert verified is not None and verified.state == IdentityState.VERIFIED
    honorific = classify_label("MR. EMMERSON", labels, counts)
    assert honorific is not None and honorific.state == IdentityState.REVIEW_REQUIRED
    shared = classify_label("MR. SMITH", labels, counts)
    assert shared is not None and shared.rule == "person.speaker_label.shared_surname"
    ambiguous = classify_label("MR. X", labels, counts, ambiguous={"MR. X"})
    assert ambiguous is not None and ambiguous.state == IdentityState.AMBIGUOUS
    assert ambiguous.person_id is None
    assert classify_label("MS. NOBODY", labels, counts) is None
    assert speaker_label_identity("THE WITNESS") is None


# ------------------------------------------------------- witness headers --
def test_page_header_variants_parse_with_exact_spans() -> None:
    samples = {
        "F3105.Kosovo Specialist Chambers - Basic Court Witness: W03877 (Private Session) "
        "Page 15003 Examination by Mr. Capin 1 A.": (
            "W03877",
            "private",
            "Examination by Mr. Capin",
        ),
        " Kosovo SpecialistKSC-OFFICIAL Chambers - Basic Court PUBLIC Witness: W04371 "
        "(Closed Session) Page 15247 Examination by Ms. Insinga 1": ("W04371", "closed", None),
        "Gjykata Themelore Dëshmitari: Nuredin Abazi (Seancë e hapur) Faqe 111 "
        "Pyetje nga z. Pace 1 PY.": ("Nuredin Abazi", "open", "Pyetje nga z. Pace"),
        "Basic Court Witness: Nuredin Abazi (Resumed)(Private Session) Page 1": (
            "Nuredin Abazi",
            "private",
            None,
        ),
    }
    for text, (subject, session, _exam) in samples.items():
        header = parse_page_header(text)
        assert header is not None, text
        assert (header.subject, header.session) == (subject, session)
        assert text[header.start : header.end] == header.text
        assert text[header.subject_start : header.subject_end].split() == subject.split()
    exam = parse_page_header(next(iter(samples)))
    assert exam is not None and exam.examination == "Examination by Mr. Capin"


def test_page_header_rejects_body_text_and_non_witness_headers() -> None:
    assert parse_page_header("Basic Court Procedural Matters (Private Session) Page 14983") is None
    # A code in the body, even with parentheses, is a mention, not a header.
    body = "x" * 700 + " Witness: W01234 (Open Session)"
    assert parse_page_header(body) is None
    assert parse_page_header("Witness: W01234 (said so) and more") is None


# ------------------------------------------------------ exhibit status --
def test_only_court_speakers_produce_status_events() -> None:
    officer = speaker_role("THE COURT OFFICER")
    bench = speaker_role("PRESIDING JUDGE SMITH")
    assert (officer, bench) == ("officer", "bench")
    assert speaker_role("SEKRETARJA E GJYKATËS") == "officer"
    assert speaker_role("MR. PACE") is None
    assert speaker_role("THE WITNESS") is None

    assigned = list(
        status_statements(
            "And it will be assigned Exhibit P01137, classified as confidential.", officer
        )
    )
    assert [(s.event_type, s.identifier, s.classification) for s in assigned] == [
        ("number_assigned", "P01137", "confidential")
    ]
    sq = list(
        status_statements(
            "[Përkthim] Do të marrë numrin e provës materiale P01137, dhe do të "
            "klasifikohet si konfidenciale.",
            speaker_role("SEKRETARI I GJYKATËS"),
        )
    )
    assert [(s.identifier, s.classification) for s in sq] == [("P01137", "confidential")]
    admitted = list(
        status_statements(
            "statements, which have been admitted as P01136.1 to P01136.4, do not", bench
        )
    )
    # A stated range records its endpoints only; nothing between is inferred.
    assert [s.identifier for s in admitted] == ["P01136.1", "P01136.4"]
    assert all(s.event_type == "admitted" for s in admitted)
    text = "Proofing Note 1 was admitted as Exhibit P01137. The Panel"
    (statement,) = status_statements(text, bench)
    assert text[statement.start : statement.end] == statement.text


def test_status_language_outside_court_rules_never_produces_events() -> None:
    bench = speaker_role("JUDGE METTRAUX")
    assert list(status_statements("Mr. Zyrapi admits a number of facts in P01355", bench)) == []
    assert list(status_statements("P3910 was admitted through the bar table", None)) == []
    # A party saying the same words is not a court record of status.
    assert (
        list(status_statements("it was admitted as Exhibit P01137", speaker_role("MR. PACE"))) == []
    )
    # The officer rule does not fire on bench speech and vice versa.
    assert list(status_statements("will be assigned Exhibit P01135", bench)) == []


# --------------------------------------------------- citation resolution --
def test_hearing_date_form_is_distinct_from_page_numbers() -> None:
    assert _hearing_date(20240429) == date(2024, 4, 29)
    assert _hearing_date(20770207) is None  # future: a mis-joined page, not a hearing
    assert _hearing_date(20241399) is None
    assert _hearing_date(15083) is None


def test_bare_filing_alias_belongs_to_the_base_filing_only() -> None:
    def document(ref: str, filing_number: str | None) -> Document:
        return Document(official_ref=ref, filing_number=filing_number, title="t", document_type="x")

    assert "F00002" in _identifier_aliases(document("KSC-BC-2020-06/F00002", "F00002"))
    annex = _identifier_aliases(document("KSC-BC-2020-06/F00002/A01", "F00002"))
    assert "F00002" not in annex and "F00002/A01" in annex
    subcase = _identifier_aliases(document("KSC-BC-2020-06/IA042/F00005", "F00005"))
    assert "F00005" not in subcase and "IA042/F00005" in subcase
