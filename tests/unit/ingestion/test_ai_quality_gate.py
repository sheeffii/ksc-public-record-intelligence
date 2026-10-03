from pathlib import Path

import pytest

from ksc_ingestion.ai_quality_gate import load_evaluation_set


def test_phase11_evaluation_set_keeps_grounded_and_abstention_cases():
    case_number, records, cases = load_evaluation_set(
        Path("tests/evaluation/phase11_questions.json")
    )
    assert case_number == "KSC-BC-2020-06"
    # Minimum corpus: the Phase 13 corpus (22 controlled + 40 corpus-02 source records).
    assert records == 62
    # F03743/F03746 are held since Phase 23: answered from the party filings.
    assert sum(item.should_answer for item in cases) == 3
    assert sum(not item.should_answer for item in cases) == 1
    by_id = {item.id: item for item in cases}
    assert by_id["held-defence-filing"].expected_categories == ("defence_argument",)
    assert by_id["held-spo-filing"].expected_categories == ("spo_argument",)
    assert all(
        item.expected_error == "DOCUMENT_NOT_FOUND" for item in cases if not item.should_answer
    )


def test_phase11_evaluation_loader_rejects_wrong_phase(tmp_path: Path):
    path = tmp_path / "evaluation.json"
    path.write_text('{"phase": 12}', encoding="utf-8")
    with pytest.raises(ValueError, match="Phase 11"):
        load_evaluation_set(path)
