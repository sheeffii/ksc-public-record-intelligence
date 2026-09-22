#!/usr/bin/env python3
"""Evidence-only Phase 16 gate. It performs no deployment or external beta."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GateItem:
    name: str
    file: str
    accepted: frozenset[str] = frozenset({"pass"})


ITEMS = (
    GateItem("deploy_reproducibility_https_smoke", "deployment-smoke.json"),
    GateItem("secrets_authorization", "authorization-review.json"),
    GateItem("backup_restore_drill", "restore-drill.json"),
    GateItem("observability_alerts", "alerts-check.json"),
    GateItem("security_review", "security-review.json"),
    GateItem("dependency_container_scan", "supply-chain-scan.json"),
    GateItem("representative_load_test", "load-test.json"),
    GateItem("accessibility_mobile", "accessibility.json"),
    GateItem("production_smoke", "production-smoke.json"),
    GateItem("beta_feedback", "beta-feedback.json", frozenset({"pass", "external_dependency"})),
)


def evaluate(evidence_dir: Path) -> tuple[bool, list[dict[str, str]]]:
    results: list[dict[str, str]] = []
    for item in ITEMS:
        path = evidence_dir / item.file
        if not path.is_file():
            results.append({"name": item.name, "status": "missing", "evidence": item.file})
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            status = str(payload["status"])
        except (json.JSONDecodeError, KeyError, TypeError):
            status = "invalid"
        results.append({"name": item.name, "status": status, "evidence": item.file})
    passed = all(
        result["status"] in item.accepted for result, item in zip(results, ITEMS, strict=True)
    )
    return passed, results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()
    passed, results = evaluate(args.evidence_dir)
    report = {"status": "pass" if passed else "pending", "checks": results}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_path:
        args.json_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
