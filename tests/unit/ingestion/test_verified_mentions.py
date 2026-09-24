"""Phase 19A deterministic mention rules, including negative cases."""

import uuid
from collections import Counter

from ksc_ingestion.verified_mentions import (
    RULES,
    Anchor,
    Registry,
    _paragraph_spans,
    classify_speaker_label,
    exhibit_mentions,
    organization_mentions,
    version_language,
    witness_code_mentions,
)

W1, P1, O1, O2 = (uuid.uuid4() for _ in range(4))
JUDGE, COUNSEL, COUNSEL_SMITH, ACCUSED = (uuid.uuid4() for _ in range(4))


def _registry() -> Registry:
    return Registry(
        witnesses={"W01234": W1},
        exhibits={"P00003": P1},
        organization_variants={
            "NATO": {O1},
            "Kosovo Specialist Chambers": {O2},
            "Specialist Prosecutor's Office": {O2},
        },
        person_labels={
            "JUDGE SMITH": (JUDGE, "judge", "smith"),
            "MR. SMITH": (COUNSEL_SMITH, "counsel_or_participant", "smith"),
            "MR. EMMERSON": (COUNSEL, "counsel_or_participant", "emmerson"),
            "THE ACCUSED THAÇI": (ACCUSED, "accused", "thaci"),
        },
        name_keys=Counter({"smith": 2, "emmerson": 1, "thaci": 1}),
    )


def test_witness_code_is_exact_registered_and_code_only() -> None:
    text = "W01234 testified; W99999 is unknown; xW01234, W012345, w01234 and W01234.1 are not."
    mentions = list(witness_code_mentions(text, _registry().witnesses))
    assert [(m.char_start, m.char_end, m.text) for m in mentions] == [(0, 6, "W01234")]
    assert mentions[0].entity_id == W1
    assert mentions[0].state == "verified"


def test_exhibit_identifier_is_exact_and_unknown_identifiers_are_not_bound() -> None:
    text = "Exhibit P00003 was admitted; P00004 and P000031 were referred to."
    mentions = list(exhibit_mentions(text, _registry().exhibits))
    assert [(m.text, m.char_start) for m in mentions] == [("P00003", 8)]


def test_organization_acronyms_are_case_sensitive_and_names_whole_token() -> None:
    text = "NATO and nato; the Kosovo Specialist Chambers; Specialist Prosecutor\u2019s Office."
    mentions = list(organization_mentions(text, _registry().organization_variants))
    found = {(m.text, m.rule_id) for m in mentions}
    assert ("NATO", "organization.acronym.exact") in found
    assert ("nato", "organization.acronym.exact") not in found
    assert ("Kosovo Specialist Chambers", "organization.name.exact") in found
    assert ("Specialist Prosecutor\u2019s Office", "organization.name.exact") in found
    assert all(text[m.char_start : m.char_end] == m.text for m in mentions)


def test_shared_organization_variant_is_review_required() -> None:
    variants = {"KLA": {O1, O2}}
    mentions = list(organization_mentions("The KLA", variants))
    assert {m.entity_id for m in mentions} == {O1, O2}
    assert {m.state for m in mentions} == {"review_required"}


def test_person_labels_verify_only_role_qualified_identities() -> None:
    registry = _registry()
    judge = classify_speaker_label("JUDGE SMITH", registry)
    accused = classify_speaker_label("THE ACCUSED THAÇI", registry)
    counsel = classify_speaker_label("MR. EMMERSON", registry)
    smith = classify_speaker_label("MR. SMITH", registry)
    assert judge is not None and judge.state == "verified"
    assert accused is not None and accused.state == "verified"
    # Surname-level labels are never auto-verified.
    assert counsel is not None and counsel.rule_id == "person.speaker_label.honorific"
    assert counsel.state == "review_required"
    assert smith is not None and smith.rule_id == "person.speaker_label.shared_surname"
    assert smith.state == "review_required" and smith.entity_id == COUNSEL_SMITH
    # Unregistered, initial-only or near-miss labels bind nothing.
    assert classify_speaker_label("MR. SMYTH", registry) is None
    assert classify_speaker_label("JUDGE S.", registry) is None


def test_every_rule_declares_a_version_and_state() -> None:
    assert all(version >= 1 for version, _ in RULES.values())
    assert {state for _, state in RULES.values()} == {"verified", "review_required"}


def test_paragraph_spans_require_a_unique_exact_token_sequence() -> None:
    page = "12. The Panel notes P00003.\n13. The Panel notes P00003.\n14. Unique  text\nhere."
    spans = _paragraph_spans(
        page, [(12, "12. The Panel notes P00003."), (14, "14. Unique text here.")]
    )
    assert [number for *_, number in spans] == [12, 14]
    repeated = _paragraph_spans("A. A.", [(1, "A.")])
    assert repeated == ()
    anchor = Anchor(
        kind="document_page_text",
        text=page,
        document_version_id=uuid.uuid4(),
        language="en",
        paragraphs=spans,
    )
    assert anchor.paragraph_at(20, 26) == 12
    assert anchor.paragraph_at(48, 54) is None


def test_official_version_marker_wins_over_recorded_language() -> None:
    assert version_language("KSC-BC-2020-06/T/2022-03-24/sqi", "en") == "sq"
    assert version_language("KSC-BC-2020-06/F00002/RED", "en") == "en"
    assert version_language("KSC-BC-2020-06/F00002/RED", None) is None
