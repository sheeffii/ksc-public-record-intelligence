"""Phase 17A's tracked inventory is metadata-only and internally honest."""

from __future__ import annotations

import json
from pathlib import Path

from ksc_ingestion.phase17_report import Phase17PassAReport
from ksc_ingestion.sources import UrlKind, classify

REPO = Path(__file__).resolve().parents[3]
REPORT = REPO / "docs" / "ingestion" / "manifests" / "phase17-pass-a-coverage.json"
PASS_B_REPORT = REPO / "docs" / "ingestion" / "manifests" / "phase17-pass-b-coverage.json"


def test_tracked_phase17_report_matches_the_real_baseline() -> None:
    report = Phase17PassAReport.model_validate_json(REPORT.read_text(encoding="utf-8"))

    assert report.case_number == "KSC-BC-2020-06"
    assert report.official_inventory_count == len(report.inventory) == 62
    assert report.held_corpus_count == 61
    assert report.counts.model_dump() == {
        "source_records": 62,
        "documents": 56,
        "versions": 61,
        "pdfs": 61,
        "pages": 2832,
        "paragraphs": 2019,
        "transcript_segments": 1363,
        "parsed_versions": 61,
        "indexed_versions": 61,
        "citations": 15730,
        "citations_resolved": 188,
        "citations_ambiguous": 3,
        "citations_unresolved": 15420,
        "citations_invalid": 119,
    }
    assert report.languages == {"en": 53, "sq": 9}
    assert report.years.get("2021", 0) == report.years.get("2022", 0) == 0
    assert report.years.get("2023", 0) == report.years.get("2024", 0) == 0
    assert "not a complete-corpus claim" in report.completeness_claim


def test_inventory_tracks_official_urls_and_processing_state() -> None:
    report = Phase17PassAReport.model_validate_json(REPORT.read_text(encoding="utf-8"))

    assert sum(row.acquisition_state == "fetched" for row in report.inventory) == 61
    assert sum(row.parse_state == "parsed" for row in report.inventory) == 60
    assert sum(row.parse_state == "review_required" for row in report.inventory) == 1
    assert sum(row.acquisition_state == "not_fetched" for row in report.inventory) == 1
    for row in report.inventory:
        assert classify(row.official_detail_url).kind is UrlKind.PCR_DETAIL
        if row.official_pdf_url:
            assert classify(row.official_pdf_url).kind is UrlKind.PCR_ARTIFACT


def test_structured_audit_never_turns_zero_rows_into_absence() -> None:
    report = Phase17PassAReport.model_validate_json(REPORT.read_text(encoding="utf-8"))
    by_category = {row.category: row for row in report.structured_data}

    for category in ("people", "witness_codes", "organizations", "exhibits"):
        assert by_category[category].real_rows == 0
        assert by_category[category].missing is not None
    assert by_category["hearings"].source_backed_rows == 3
    assert by_category["statements"].source_backed_rows == 1363
    assert by_category["events"].source_backed_rows == 54
    assert by_category["relationships"].source_backed_rows == 178


def test_next_batch_stays_fail_closed_until_official_discovery() -> None:
    report = Phase17PassAReport.model_validate_json(REPORT.read_text(encoding="utf-8"))

    assert report.next_batch.target_size == 75
    assert report.next_batch.genuinely_new_inventory_records == 0
    assert report.next_batch.status == "requires_new_official_inventory"
    assert not report.next_batch.inventory_supports_acquisition


def test_report_contains_metadata_only() -> None:
    raw = json.loads(REPORT.read_text(encoding="utf-8"))
    forbidden = {"text", "body", "content", "pages_text", "extract"}
    for record in raw["inventory"]:
        assert not forbidden & set(record)
    assert REPORT.stat().st_size < 100_000


def test_pass_b_report_reconciles_the_official_corpus_and_quarantine() -> None:
    report = json.loads(PASS_B_REPORT.read_text(encoding="utf-8"))

    assert report["discovery"] | {"years": {}, "languages": {}, "record_types": {}} == {
        "genuinely_new_candidates": 75,
        "selected": 75,
        "accepted": 73,
        "duplicates": 0,
        "failed": 0,
        "quarantined": 2,
        "missing_pdfs": 0,
        "bytes": 42_867_559,
        "years": {},
        "languages": {},
        "record_types": {},
    }
    assert report["official_corpus"]["after"]["source_records"] == 135
    assert report["official_corpus"]["after"]["documents"] == 116
    assert report["official_corpus"]["after"]["versions"] == 134
    assert report["quality_gate"]["passed"] == 73
    assert report["structured_data"]["events"] == {"before": 54, "after": 127}
    assert report["structured_data"]["relationships"] == {"before": 178, "after": 291}
    assert report["citations"]["after"] == {
        "resolved": 306,
        "ambiguous": 3,
        "unresolved": 16_831,
        "invalid": 141,
        "total": 17_281,
    }
    assert {row["record_id"] for row in report["quarantine"]} == {"r17", "r22"}
    assert all(
        row["reason"] == "transcript page 1 has no open-session heading"
        for row in report["quarantine"]
    )
