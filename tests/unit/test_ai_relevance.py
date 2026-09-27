from __future__ import annotations

import uuid
from decimal import Decimal

from ksc_api.services.ai_research import (
    Candidate,
    RelevancePlan,
    _candidate_relevant,
    _relevance_plan,
)


def _candidate(*, text: str, category: str = "document_exhibit", method: str = "lexical_fts"):
    return Candidate(
        anchor_kind="document_chunk",
        anchor_id=uuid.uuid4(),
        document_version_id=uuid.uuid4(),
        citation_id=None,
        category=category,
        visibility="public",
        ref="KSC-BC-2020-06/F00001",
        version_ref="KSC-BC-2020-06/F00001/RED",
        display="F00001",
        target_path="/documents/F00001",
        source_url="https://example.test/F00001.pdf",
        text=text,
        method=method,
        score=Decimal("1"),
    )


def test_low_overlap_lexical_passage_is_not_relevant() -> None:
    plan = _relevance_plan(
        "What did the Panel say about amendments to the Corrected Version of the SPO Final Trial Brief?"
    )
    candidate = _candidate(text="A different trial concerned unrelated detention evidence.")
    assert _candidate_relevant(candidate, plan) is False


def test_direct_structured_passage_is_relevant() -> None:
    plan = _relevance_plan(
        "What did the Panel say about amendments to the Corrected Version of the SPO Final Trial Brief?"
    )
    candidate = _candidate(
        category="court_finding",
        method="structured_verified",
        text="The Panel addressed amendments in the Corrected Version of the SPO Final Trial Brief.",
    )
    assert _candidate_relevant(candidate, plan) is True


def test_question_intent_requires_matching_semantic_category() -> None:
    defence = _relevance_plan("What did the Defence argue about disclosure?")
    testimony = _relevance_plan("What testimony did witness W01234 give about disclosure?")
    reliance = _relevance_plan("What evidence did the Court rely on for this finding?")
    assert defence.required_categories == frozenset({"defence_argument"})
    assert testimony.required_categories == frozenset({"witness_testimony"})
    assert testimony.identifiers == ("W01234",)
    assert reliance.intent == "FIND_COURT_RELIANCE"


def test_party_name_inside_document_title_does_not_change_question_intent() -> None:
    plan = _relevance_plan(
        "What did the Panel say about amendments to the Corrected Version of the SPO Final Trial Brief?"
    )
    assert plan.intent == "EXPLAIN_OR_SUMMARIZE"
    assert plan.required_categories == frozenset()


def test_entity_specific_question_requires_exact_identifier() -> None:
    plan = RelevancePlan(
        intent="FIND_WITNESS_TESTIMONY",
        topic_tokens=("disclosure",),
        identifiers=("W01234",),
        required_categories=frozenset({"witness_testimony"}),
    )
    candidate = _candidate(
        category="witness_testimony",
        text="W05678 gave evidence about disclosure.",
    )
    assert _candidate_relevant(candidate, plan) is False
