"""Capture bundles: validation, discovery, parser precedence."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from ksc_api.models.enums import DocumentVersionType, IngestionItemStatus, SourceSystem
from ksc_ingestion.capture import (
    CAPTURE_FETCH_METHOD,
    BundleError,
    DiscoveryFailure,
    ManifestMetadata,
    discover,
    load_bundle,
    load_inventory,
)
from ksc_ingestion.discovery import DiscoveredRecord, MetadataSource
from ksc_ingestion.sources import ClassifiedUrl, UrlKind
from support.synthetic import DEMO_CASE, BundleBuilder, make_pdf, metadata, standard_bundle


def test_standard_bundle_discovers_every_record(tmp_path: Path) -> None:
    bundle = load_bundle(standard_bundle(tmp_path))
    records = discover(bundle)
    assert len(records) == 7
    assert all(isinstance(r, DiscoveredRecord) for r in records)
    a1 = records[0]
    assert isinstance(a1, DiscoveredRecord)
    assert a1.source_system is SourceSystem.KSC_PUBLIC_COURT_RECORDS
    assert a1.external_record_id == "00000000000000a1"
    assert a1.item_key == "ksc_public_court_records:00000000000000a1"
    assert a1.metadata_source is MetadataSource.SYNTHETIC_FIXTURE
    assert a1.filing_date == date(2020, 5, 28)
    assert a1.discovery_url.startswith("https://repository.scp-ks.org/?icc_filters")
    assert a1.detail_page_url == (
        "https://repository.scp-ks.org/details.php?doc_id=00000000000000a1&doc_type=stl_filing&lang=eng"
    )
    assert len(a1.artifacts) == 2
    assert a1.artifacts[0].local_file is not None and a1.artifacts[0].local_file.is_file()
    assert a1.artifacts[0].fetch_method == CAPTURE_FETCH_METHOD
    assert a1.artifacts[1].official_version_ref == f"{DEMO_CASE}/F00001/RED"
    assert a1.raw_metadata["capture"]["bundle_id"] == "synthetic-demo-01"
    assert a1.raw_metadata["metadata_source"] == "synthetic_fixture"

    a2 = records[1]
    assert isinstance(a2, DiscoveredRecord)
    assert a2.filing_date == date(2020, 6, 28)  # "28 June 2020"

    a3 = records[2]
    assert isinstance(a3, DiscoveredRecord)
    assert a3.artifacts[0].local_file is None
    assert a3.artifacts[0].fetch_method is None

    a4 = records[3]
    assert isinstance(a4, DiscoveredRecord)
    assert a4.hearing is not None and a4.hearing.hearing_date == date(2024, 11, 25)

    a7 = records[6]
    assert isinstance(a7, DiscoveredRecord)
    assert a7.language == "sq"
    assert a7.artifacts[0].version_type is DocumentVersionType.TRANSLATION


def test_missing_manifest_and_bad_json(tmp_path: Path) -> None:
    with pytest.raises(BundleError, match="no manifest"):
        load_bundle(tmp_path)
    (tmp_path / "manifest.json").write_text("{not json")
    with pytest.raises(BundleError, match="unreadable"):
        load_bundle(tmp_path)


def test_manifest_schema_is_strict(tmp_path: Path) -> None:
    b = BundleBuilder(tmp_path)
    b.write(captured_at="2026-09-20T12:00:00")  # naive timestamp
    with pytest.raises(BundleError, match="timezone"):
        load_bundle(tmp_path)
    b.write(unexpected_field=1)
    with pytest.raises(BundleError, match="invalid"):
        load_bundle(tmp_path)
    b.write(bundle_id="../escape")
    with pytest.raises(BundleError, match="invalid"):
        load_bundle(tmp_path)


def test_non_official_urls_reject_the_bundle(tmp_path: Path) -> None:
    b = BundleBuilder(tmp_path)
    b.records.append(
        {
            "detail_page_url": "https://example.com/details.php?doc_id=00000000000000a1",
            "artifacts": [],
        }
    )
    b.write()
    with pytest.raises(BundleError, match="not an official"):
        load_bundle(tmp_path)


def test_missing_files_and_path_escapes_reject_the_bundle(tmp_path: Path) -> None:
    b = BundleBuilder(tmp_path)
    b.add_record(
        "00000000000000a1",
        metadata(record_type="filing", official_ref=f"{DEMO_CASE}/F1", title="t"),
        [
            {
                "url": "https://repository.scp-ks.org/LW/Published/Filing/x/a.pdf",
                "file": "files/missing.pdf",
            }
        ],
    )
    b.write()
    with pytest.raises(BundleError, match="artifact file missing"):
        load_bundle(tmp_path)
    b.records[0]["artifacts"][0]["file"] = "../../etc/passwd"
    b.write()
    with pytest.raises(BundleError, match="escapes"):
        load_bundle(tmp_path)


def test_duplicate_detail_page_rejects_the_bundle(tmp_path: Path) -> None:
    b = BundleBuilder(tmp_path)
    md = metadata(record_type="filing", official_ref=f"{DEMO_CASE}/F1", title="t")
    b.add_record("00000000000000a1", md, [])
    b.add_record("00000000000000a1", md, [])
    b.write()
    with pytest.raises(BundleError, match="listed twice"):
        load_bundle(tmp_path)


def test_record_without_metadata_or_parser_is_a_visible_failure(tmp_path: Path) -> None:
    b = BundleBuilder(tmp_path)
    b.add_record("00000000000000a1", None, [], detail_page=True)
    b.add_record("00000000000000a2", None, [])
    b.write()
    records = discover(load_bundle(tmp_path))
    assert [type(r) for r in records] == [DiscoveryFailure, DiscoveryFailure]
    first, second = records
    assert isinstance(first, DiscoveryFailure) and isinstance(second, DiscoveryFailure)
    assert first.status is IngestionItemStatus.INVALID_METADATA
    assert "no parser" in first.reason
    assert second.status is IngestionItemStatus.INVALID_METADATA
    assert "no saved detail page" in second.reason
    assert first.item_key == "ksc_public_court_records:00000000000000a1"


def test_non_pcr_detail_url_needs_an_explicit_external_id(tmp_path: Path) -> None:
    b = BundleBuilder(tmp_path)
    md = metadata(record_type="transcript", official_ref=f"{DEMO_CASE}/T/2024-11-25", title="t")
    b.records.append(
        {"detail_page_url": "https://www.scp-ks.org/en/cases/demo", "artifacts": [], "metadata": md}
    )
    b.write()
    (failure,) = discover(load_bundle(tmp_path))
    assert isinstance(failure, DiscoveryFailure)
    assert "no stable external record id" in failure.reason

    md["external_record_id"] = "hearing-2024-11-25-1"
    b.write()
    (record,) = discover(load_bundle(tmp_path))
    assert isinstance(record, DiscoveredRecord)
    assert record.source_system is SourceSystem.KSC_CASE_PAGE
    assert record.external_record_id == "hearing-2024-11-25-1"


class FakeParser:
    """Stands in for the real PCR detail-page parser (pending real pages)."""

    def can_parse(self, url: ClassifiedUrl) -> bool:
        return url.kind is UrlKind.PCR_DETAIL

    def parse(self, html: bytes, url: ClassifiedUrl, *, case_number: str) -> ManifestMetadata:
        assert b"synthetic detail page" in html
        return ManifestMetadata(
            record_type="filing",
            official_ref=f"{case_number}/F00099",
            title="Parsed from page",
            case_number=case_number,
            classification="Public",
        )


def test_official_page_parser_wins_over_manifest_metadata(tmp_path: Path) -> None:
    b = BundleBuilder(tmp_path)
    b.add_record(
        "00000000000000a1",
        metadata(
            record_type="filing", official_ref=f"{DEMO_CASE}/F00001", title="Typed by operator"
        ),
        [],
        detail_page=True,
    )
    b.add_record(
        "00000000000000a2",
        metadata(
            record_type="filing", official_ref=f"{DEMO_CASE}/F00002", title="Typed by operator"
        ),
        [],
    )
    b.write()
    parsed, typed = discover(load_bundle(tmp_path), parsers=[FakeParser()])
    assert isinstance(parsed, DiscoveredRecord) and isinstance(typed, DiscoveredRecord)
    assert parsed.metadata_source is MetadataSource.OFFICIAL_PAGE
    assert parsed.title == "Parsed from page"
    assert typed.metadata_source is MetadataSource.SYNTHETIC_FIXTURE
    assert typed.title == "Typed by operator"


def test_operator_manifest_metadata_is_flagged_as_such(tmp_path: Path) -> None:
    b = BundleBuilder(tmp_path)
    md = metadata(record_type="filing", official_ref=f"{DEMO_CASE}/F00001", title="t")
    md["metadata_source"] = "operator_manifest"
    b.add_record("00000000000000a1", md, [])
    b.write()
    (record,) = discover(load_bundle(tmp_path))
    assert isinstance(record, DiscoveredRecord)
    assert record.metadata_source is MetadataSource.OPERATOR_MANIFEST
    raw = json.loads(json.dumps(record.raw_metadata))
    assert raw["metadata_source"] == "operator_manifest"
    assert raw["metadata"]["official_ref"] == f"{DEMO_CASE}/F00001"


def test_pdf_fixture_is_deterministic(tmp_path: Path) -> None:
    assert make_pdf(["x"]) == make_pdf(["x"])


def test_metadata_inventory_is_official_only_and_contains_no_local_files(tmp_path: Path) -> None:
    builder = BundleBuilder(tmp_path)
    md = metadata(record_type="filing", official_ref=f"{DEMO_CASE}/F1", title="Inventory")
    md["metadata_source"] = "operator_manifest"
    builder.add_record(
        "00000000000000a1",
        md,
        [{"url": "https://repository.scp-ks.org/LW/Published/Filing/x/a.pdf"}],
    )
    manifest = builder.write(capture_method="official_metadata_inventory") / "manifest.json"

    inventory = load_inventory(manifest)
    (record,) = discover(inventory)
    assert isinstance(record, DiscoveredRecord)
    assert record.artifacts[0].local_file is None

    data = json.loads(manifest.read_text())
    data["records"][0]["artifacts"][0]["file"] = "files/a.pdf"
    manifest.write_text(json.dumps(data))
    with pytest.raises(BundleError, match="metadata-only"):
        load_inventory(manifest)
