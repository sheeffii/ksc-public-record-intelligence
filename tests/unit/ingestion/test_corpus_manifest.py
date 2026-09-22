"""The tracked Phase 7 corpus manifest is valid, metadata-only and internally
consistent. Runs without infrastructure."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ksc_ingestion.corpus_manifest import CorpusManifest, validate_manifest_file
from ksc_ingestion.sources import UrlKind, classify

REPO = Path(__file__).resolve().parents[3]
MANIFEST = REPO / "docs" / "ingestion" / "manifests" / "phase7-controlled-corpus.json"


@pytest.fixture(scope="module")
def manifest() -> CorpusManifest:
    return validate_manifest_file(MANIFEST)


def test_phase7_manifest_describes_the_controlled_corpus(manifest: CorpusManifest) -> None:
    assert manifest.schema_version == 1
    assert manifest.case_number == "KSC-BC-2020-06"
    assert manifest.bundle_id == "2026-09-20-corpus-01"
    assert manifest.record_count == 22
    assert manifest.document_count == 19
    assert manifest.version_count == 22
    assert manifest.total_bytes == 24_429_094
    assert [r.record_id for r in manifest.records] == [f"r{i:02d}" for i in range(1, 23)]


def test_every_record_is_verified_public_and_held(manifest: CorpusManifest) -> None:
    for r in manifest.records:
        assert r.quality_gate.status == "PASS", r.record_id
        assert r.quality_gate.checks_passed == r.quality_gate.checks_total
        assert r.visibility in {"public", "public_redacted"}
        assert r.artifact_status == "fetched"
        assert r.fetch_method == "operator_browser_capture"
        assert r.metadata_source == "capture_snapshot"
        assert classify(r.detail_page_url).kind is UrlKind.PCR_DETAIL
        assert classify(r.artifact_url).kind is UrlKind.PCR_ARTIFACT
        assert r.sha256 in r.object_key and r.object_key.startswith("documents/KSC-BC-2020-06/")


def test_language_and_version_relationships(manifest: CorpusManifest) -> None:
    by_ref = {r.official_version_ref: r for r in manifest.records}
    for eng, sq in (
        ("KSC-BC-2020-06/F00045/A03", "KSC-BC-2020-06/F00045/A03/sqi"),
        ("KSC-BC-2020-06/F00004/RED", "KSC-BC-2020-06/F00004/RED/sqi"),
        ("KSC-BC-2020-06/T/2026-02-18", "KSC-BC-2020-06/T/2026-02-18/sqi"),
    ):
        assert by_ref[eng].document_official_ref == by_ref[sq].document_official_ref
        assert by_ref[sq].version_type == "translation" and by_ref[sq].language == "sq"
        assert by_ref[eng].language == "en"
    # annex vs further-redacted brief are different documents (not a RED→RED2 pair)
    assert (
        by_ref["KSC-BC-2020-06/F03668/RED/A01/RED"].document_official_ref
        == "KSC-BC-2020-06/F03668/A01"
    )
    assert by_ref["KSC-BC-2020-06/F03668/RED2"].document_official_ref == "KSC-BC-2020-06/F03668"
    assert by_ref["KSC-BC-2020-06/F03667/COR/RED"].version_type == "public_redacted"
    assert {
        by_ref[k].version_type
        for k in ("KSC-BC-2020-06/F00001", "KSC-BC-2020-06/IA042/F00002", "KSC-BC-2020-06/F03774")
    } == {"reclassified"}


def test_transcripts_carry_hearing_identity_and_nothing_is_inferred(
    manifest: CorpusManifest,
) -> None:
    transcripts = [r for r in manifest.records if r.record_type == "Transcript"]
    assert len(transcripts) == 3
    assert {r.hearing.hearing_date.isoformat() for r in transcripts if r.hearing} == {
        "2026-02-16",
        "2026-02-18",
    }
    for r in transcripts:
        assert r.published_document_id is None and r.filing_party is None
    annexes = [r for r in manifest.records if r.record_type == "Filing Annex"]
    assert len(annexes) == 3 and all(
        r.filing_party is None and r.published_date is None for r in annexes
    )


def test_manifest_holds_metadata_only() -> None:
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    forbidden = {"text", "body", "content", "pages_text", "extract"}
    for record in raw["records"]:
        assert not forbidden & set(record), record["record_id"]
        for value in record.values():
            if isinstance(value, str):
                assert len(value) < 600, record["record_id"]
    assert MANIFEST.stat().st_size < 200_000


def test_phase13_manifests_describe_the_scaled_corpus() -> None:
    corpus_02 = validate_manifest_file(
        REPO / "docs" / "ingestion" / "manifests" / "phase13-corpus-02.json"
    )
    assert corpus_02.bundle_id == "2026-09-21-corpus-02"
    assert corpus_02.record_count == 39 and corpus_02.version_count == 39
    assert corpus_02.document_count == 38 and corpus_02.total_bytes == 12_014_877
    assert [r.reason_code for r in corpus_02.refused] == ["ambiguous_mapping"]
    assert corpus_02.refused[0].record_id == "r31"
    combined = validate_manifest_file(
        REPO / "docs" / "ingestion" / "manifests" / "phase13-controlled-corpus.json"
    )
    assert combined.record_count == 22 + 39 and combined.version_count == 61
    assert combined.document_count == 56 and combined.total_bytes == 24_429_094 + 12_014_877
    assert len({r.sha256 for r in combined.records}) == 61
    assert len(combined.refused) == 1
