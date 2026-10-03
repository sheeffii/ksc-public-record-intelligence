from __future__ import annotations

from ksc_ingestion.findings_quality_gate import benchmark_versions_match

PINNED = {"KSC-BC-2020-06/F03752": "a" * 64, "KSC-BC-2020-06/F03667": "b" * 64}


def test_benchmark_passes_when_the_corpus_grows_beyond_the_manifest() -> None:
    assert benchmark_versions_match(PINNED, [("KSC-BC-2020-06/F03752", "a" * 64)])


def test_benchmark_fails_when_its_source_bytes_changed() -> None:
    assert not benchmark_versions_match(PINNED, [("KSC-BC-2020-06/F03752", "c" * 64)])


def test_benchmark_fails_when_its_version_is_missing_or_unpinned() -> None:
    assert not benchmark_versions_match(PINNED, [None])
    assert not benchmark_versions_match(PINNED, [("KSC-BC-2020-06/F09999", "a" * 64)])
    assert not benchmark_versions_match(PINNED, [])
