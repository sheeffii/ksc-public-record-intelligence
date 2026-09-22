from __future__ import annotations

import json
from pathlib import Path

from scripts.phase16_gate import ITEMS, evaluate


def test_gate_stays_pending_without_real_evidence(tmp_path: Path) -> None:
    passed, results = evaluate(tmp_path)
    assert not passed
    assert all(result["status"] == "missing" for result in results)


def test_gate_accepts_external_beta_dependency_only(tmp_path: Path) -> None:
    for item in ITEMS:
        status = "external_dependency" if item.name == "beta_feedback" else "pass"
        (tmp_path / item.file).write_text(json.dumps({"status": status}), encoding="utf-8")
    passed, _ = evaluate(tmp_path)
    assert passed
