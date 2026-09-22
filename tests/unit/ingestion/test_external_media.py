from __future__ import annotations

import json
from pathlib import Path

import pytest

from ksc_ingestion.external_media import MediaManifestError, load_media_manifest

MANIFEST = Path("docs/ingestion/manifests/phase14-external-media.json")


def test_real_manifest_has_exact_public_sources_and_no_inferred_court_status():
    manifest = load_media_manifest(MANIFEST)
    assert len(manifest["items"]) == 3
    assert {item["court_status"] for item in manifest["items"]} == {"external_only"}
    assert all(item["canonical_url"].startswith("https://") for item in manifest["items"])
    assert manifest["coverage_limitations"]


def test_private_or_login_gated_manifest_is_rejected(tmp_path: Path):
    manifest = load_media_manifest(MANIFEST)
    manifest["items"][0]["access_status"] = "restricted"
    path = tmp_path / "restricted.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(MediaManifestError, match="explicitly public"):
        load_media_manifest(path)

    manifest = load_media_manifest(MANIFEST)
    manifest["items"][0]["canonical_url"] = "https://10.0.0.8/private"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(MediaManifestError, match="local/private"):
        load_media_manifest(path)


def test_duplicate_url_and_modified_excerpt_are_rejected(tmp_path: Path):
    manifest = load_media_manifest(MANIFEST)
    manifest["items"][1]["canonical_url"] = manifest["items"][0]["canonical_url"]
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(MediaManifestError, match="duplicate canonical URL"):
        load_media_manifest(path)

    manifest = load_media_manifest(MANIFEST)
    manifest["items"][0]["captured_text"] += " changed"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(MediaManifestError, match="content hash mismatch"):
        load_media_manifest(path)


def test_publication_and_capture_times_remain_distinct_and_ordered(tmp_path: Path):
    manifest = load_media_manifest(MANIFEST)
    item = manifest["items"][0]
    assert item["published_at"] != item["captured_at"]

    item["captured_at"] = "2020-01-01T00:00:00+00:00"
    path = tmp_path / "bad-time.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(MediaManifestError, match="publication/capture"):
        load_media_manifest(path)


def test_manual_import_cannot_assign_a_stronger_court_status_without_citation_workflow(
    tmp_path: Path,
):
    manifest = load_media_manifest(MANIFEST)
    manifest["items"][0]["court_status"] = "admitted"
    path = tmp_path / "promoted.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(MediaManifestError, match="exact-citation workflow"):
        load_media_manifest(path)
