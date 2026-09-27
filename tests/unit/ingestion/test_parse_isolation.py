"""One bad PDF never aborts a parse batch: it is recorded, the rest continue."""

from __future__ import annotations

import uuid
from typing import Any

from ksc_ingestion.parse_pipeline import ParsedVersionResult, Phase8Pipeline


class _Pipeline(Phase8Pipeline):
    def __init__(self, bad: set[uuid.UUID]) -> None:
        self.bad = bad
        self.parsed: list[uuid.UUID] = []
        self.failures: list[tuple[uuid.UUID, str]] = []

    def _parse_version(self, version_id: uuid.UUID, *, force: bool) -> ParsedVersionResult:
        if version_id in self.bad:
            raise ValueError("malformed PDF")
        self.parsed.append(version_id)
        return ParsedVersionResult(str(version_id), 1, 0, 0, 0, False)

    def _record_parse_failure(
        self, run_id: uuid.UUID, version_id: uuid.UUID, exc: Exception
    ) -> ParsedVersionResult:
        self.failures.append((version_id, str(exc)))
        return ParsedVersionResult(str(version_id), 0, 0, 0, 0, True, error=str(exc))


def test_a_failing_version_is_recorded_and_the_batch_continues() -> None:
    ids = [uuid.uuid4() for _ in range(5)]
    pipeline = _Pipeline(bad={ids[1], ids[3]})
    results: list[Any] = pipeline._parse_all(uuid.uuid4(), ids, force=False)

    assert [r.official_version_ref for r in results] == [str(i) for i in ids]
    assert pipeline.parsed == [ids[0], ids[2], ids[4]]
    assert [v for v, _ in pipeline.failures] == [ids[1], ids[3]]
    assert [bool(r.error) for r in results] == [False, True, False, True, False]
