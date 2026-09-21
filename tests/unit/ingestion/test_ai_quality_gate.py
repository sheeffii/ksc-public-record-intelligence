from pathlib import Path

import pytest

from ksc_ingestion.ai_quality_gate import load_evaluation_set


def test_phase11_evaluation_set_keeps_grounded_and_abstention_cases():
    case_number, records, cases = load_evaluation_set(
        Path("tests/evaluation/phase11_questions.json")
    )
    assert case_number == "KSC-BC-2020-06"
    assert records == 22
    assert sum(item.should_answer for item in cases) == 1
    assert sum(not item.should_answer for item in cases) == 3
    assert all(
        item.expected_error == "DOCUMENT_NOT_FOUND" for item in cases if not item.should_answer
    )


def test_phase11_evaluation_loader_rejects_wrong_phase(tmp_path: Path):
    path = tmp_path / "evaluation.json"
    path.write_text('{"phase": 12}', encoding="utf-8")
    with pytest.raises(ValueError, match="Phase 11"):
        load_evaluation_set(path)
