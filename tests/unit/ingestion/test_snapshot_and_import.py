"""Normalised-snapshot parser and the v0 capture importer (SHA-256 matching,
reference derivation confirmed by the PDF header, strict validation)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from ksc_ingestion.capture import load_bundle
from ksc_ingestion.capture_import import (
    HeaderInfo,
    SourceImportError,
    SourceLanguage,
    SourceRecordEntry,
    derive_references,
    import_capture,
    load_source,
    match_pdfs,
    page1_classification,
    pdf_header_references,
)
from ksc_ingestion.snapshot import SnapshotFormatError, parse_snapshot
from support.synthetic import DEMO_CASE, make_pdf, snapshot_html, source_capture

DETAIL = (
    "https://repository.scp-ks.org/details.php?doc_id=0000000000000001&doc_type=stl_filing&lang=eng"
)
PDF = "https://repository.scp-ks.org/LW/Published/Filing/x/a.pdf"


def _fields(**overrides: str) -> dict[str, str]:
    base = {
        "Record ID": "r01",
        "Case Number": DEMO_CASE,
        "Title": "A title",
        "Document / Filing ID": "F00004RED",
        "Record Type": "Filing",
        "Filing Type": "Decision",
        "Filing Party": "— (not published)",
        "Court Level": "Basic Court Chamber",
        "Date": "—",
        "Language": "English (eng)",
        "Public / Redacted Status": "public_redacted",
        "SHA-256": "ab" * 32,
        "Bytes": "1234",
        "Selection Reason": "why",
    }
    base.update(overrides)
    return base


def test_snapshot_parser_reads_fields_and_blanks_as_none() -> None:
    snap = parse_snapshot(snapshot_html(_fields(), DETAIL, PDF))
    assert snap.record_id == "r01" and snap.case_number == DEMO_CASE
    assert snap.document_id == "F00004RED" and snap.filing_party is None and snap.date is None
    assert (snap.language_code, snap.language_name) == ("eng", "English")
    assert snap.sha256 == "ab" * 32 and snap.byte_size == 1234
    assert snap.detail_page_url == DETAIL and snap.pdf_url == PDF
    assert snap.footer_note and "Normalised snapshot" in snap.footer_note


def test_snapshot_parser_rejects_unknown_fields_and_missing_links() -> None:
    with pytest.raises(SnapshotFormatError, match="unknown snapshot field"):
        parse_snapshot(snapshot_html({**_fields(), "Secret": "x"}, DETAIL, PDF))
    with pytest.raises(SnapshotFormatError, match="no field table"):
        parse_snapshot("<html><body>nothing</body></html>")


def test_page1_classification_tolerates_split_words() -> None:
    assert (
        page1_classification("Classification: Strictly Confidentia l Request")
        == "Strictly Confidential"
    )
    assert page1_classification("Classification: Public Decision") == "Public"
    assert page1_classification("Klasifikimi: Publik Vendim") == "Publik"
    assert page1_classification("no classification here") is None


def _entry(**overrides: object) -> SourceRecordEntry:
    base: dict[str, object] = {
        "record_id": "r01",
        "case_number": DEMO_CASE,
        "title": "Public Redacted Version of a Decision",
        "document_id": "F00004RED",
        "record_type": "Filing",
        "filing_type": "Decision",
        "filing_party": None,
        "court_level": None,
        "date": "27/05/2020",
        "language": SourceLanguage(code="eng", name="English"),
        "public_status": "public_redacted",
        "confidential_content_included": False,
        "detail_page_url": DETAIL,
        "pdf_url": PDF,
        "artifact_path": "/LW/Published/Filing/x/a.pdf",
        "local_file": "files/r01.pdf",
        "local_page_snapshot": "pages/r01.html",
        "sha256": "ab" * 32,
        "bytes": 10,
        "http_status_verified": 200,
    }
    base.update(overrides)
    return SourceRecordEntry.model_validate(base)


def _header(refs: dict[str, int] | None = None, reclass: str | None = None) -> HeaderInfo:
    return HeaderInfo(refs or {}, None, reclass, 1)


def test_reference_confirmed_by_header() -> None:
    refs = derive_references(_entry(), _header({f"{DEMO_CASE}/F00004/RED": 4}))
    assert refs.document_ref == f"{DEMO_CASE}/F00004"
    assert refs.version_ref == f"{DEMO_CASE}/F00004/RED"
    assert refs.version_type == "public_redacted" and refs.version_label == "RED"
    assert refs.ref_source == "published_id_confirmed_by_pdf_header" and refs.status == "ok"


def test_language_suffix_and_translation() -> None:
    refs = derive_references(
        _entry(language=SourceLanguage(code="sqi", name="Albanian")),
        _header({f"{DEMO_CASE}/F00004/RED/sqi": 4}),
    )
    assert refs.version_ref == f"{DEMO_CASE}/F00004/RED/sqi"
    assert refs.version_type == "translation" and refs.version_label == "RED/sqi"


def test_header_may_extend_but_not_contradict_the_published_id() -> None:
    annex = _entry(
        document_id="F03668RED",
        record_type="Filing Annex",
        title="ANNEX 1 to Public Redacted Version",
    )
    refs = derive_references(annex, _header({f"{DEMO_CASE}/F03668/RED/A01/RED": 14}))
    assert refs.document_ref == f"{DEMO_CASE}/F03668/A01"
    assert refs.version_ref == f"{DEMO_CASE}/F03668/RED/A01/RED" and refs.ref_source == "pdf_header"
    conflict = derive_references(_entry(), _header({f"{DEMO_CASE}/F00004/COR": 4}))
    assert conflict.status == "ambiguous" and conflict.version_ref is None
    assert "contradicts" in (conflict.note or "")


def test_suffix_families_and_sub_proceedings() -> None:
    cor = derive_references(_entry(document_id="F03667CORRED"), _header())
    assert (
        cor.version_ref == f"{DEMO_CASE}/F03667/COR/RED" and cor.version_type == "public_redacted"
    )
    red2 = derive_references(
        _entry(document_id="F03664RED2", public_status="public_redacted_v2"), _header()
    )
    assert red2.version_ref == f"{DEMO_CASE}/F03664/RED2"
    ia = derive_references(_entry(document_id="IA042-F00005RED"), _header())
    assert (
        ia.document_ref == f"{DEMO_CASE}/IA042/F00005"
        and ia.version_ref == f"{DEMO_CASE}/IA042/F00005/RED"
    )
    plain = derive_references(_entry(document_id="F03752", public_status="public"), _header())
    assert plain.version_type == "original" and plain.version_label is None
    weird = derive_references(_entry(document_id="F03752XYZ"), _header())
    assert weird.status == "ambiguous"


def test_reclassified_only_when_the_court_stamp_is_present() -> None:
    stamped = derive_references(
        _entry(document_id="F00001", public_status="public"),
        _header({f"{DEMO_CASE}/F00001": 3}, "PUBLIC Reclassified as Public pursuant to CRSPD1"),
    )
    assert stamped.version_type == "reclassified"
    plain = derive_references(
        _entry(document_id="F00001", public_status="public"), _header({f"{DEMO_CASE}/F00001": 3})
    )
    assert plain.version_type == "original"


def test_transcripts_use_a_derived_key_and_need_a_hearing_date() -> None:
    t = derive_references(
        _entry(
            document_id=None,
            record_type="Transcript",
            filing_type="Transcript",
            date="18/02/2026",
            hearing_date="18/02/2026",
        ),
        _header(),
    )
    assert t.document_ref == f"{DEMO_CASE}/T/2026-02-18" and t.version_ref == t.document_ref
    assert t.ref_source == "derived_transcript_key"
    sq = derive_references(
        _entry(
            document_id=None,
            record_type="Transcript",
            filing_type="Transcript",
            date="18/02/2026",
            language=SourceLanguage(code="sqi", name="Albanian"),
        ),
        _header(),
    )
    assert sq.version_ref == f"{DEMO_CASE}/T/2026-02-18/sqi" and sq.version_type == "translation"
    none = derive_references(
        _entry(document_id=None, record_type="Transcript", filing_type="Transcript", date=None),
        _header(),
    )
    assert none.status == "ambiguous"


def test_pdf_header_references_reads_refs_classification_and_stamp() -> None:
    data = make_pdf(
        [
            f"{DEMO_CASE}/F00001/1 of 3",
            "Classification: Confidential",
            "PUBLIC Reclassified as Public pursuant to CRSPD1 of 24 April 2020.",
        ]
    )
    header = pdf_header_references(data, DEMO_CASE)
    assert header.refs == {f"{DEMO_CASE}/F00001": 1}
    assert header.classification == "Confidential"
    assert header.reclassification_note and header.reclassification_note.startswith(
        "PUBLIC Reclassified as Public"
    )
    assert header.pages == 1


def test_source_capture_loads_and_matches_by_hash_only(tmp_path: Path) -> None:
    src = source_capture(tmp_path / "src", tmp_path / "downloads")
    manifest, snapshots = load_source(src)
    assert len(manifest.records) == 10 and len(snapshots) == 10
    rows = match_pdfs(manifest, [tmp_path / "downloads"])
    assert [r.match_status for r in rows] == ["MATCHED"] * 10
    assert all(
        Path(r.matched_local_pdf or "").name != f"{r.record_id}.pdf" for r in rows
    )  # names were not used
    # a decoy with the right name but wrong bytes is ignored; a missing file is MISSING
    (tmp_path / "downloads" / "Decision Assigning a Judge.pdf").write_bytes(make_pdf(["tampered"]))
    rows = match_pdfs(manifest, [tmp_path / "downloads"])
    assert {r.record_id: r.match_status for r in rows}["r03"] == "MISSING"


def test_source_validation_refuses_confidential_flags_and_snapshot_mismatches(
    tmp_path: Path,
) -> None:
    src = source_capture(tmp_path / "src", tmp_path / "downloads")
    manifest_path = src / "manifest.json"
    data = json.loads(manifest_path.read_text())
    data["records"][0]["confidential_content_included"] = True
    manifest_path.write_text(json.dumps(data))
    with pytest.raises(SourceImportError, match="confidential content flagged"):
        load_source(src)
    data["records"][0]["confidential_content_included"] = False
    data["records"][0]["title"] = "Edited after capture"
    manifest_path.write_text(json.dumps(data))
    with pytest.raises(SourceImportError, match="snapshot title"):
        load_source(src)


def test_import_writes_a_valid_project_bundle(tmp_path: Path) -> None:
    src = source_capture(tmp_path / "src", tmp_path / "downloads")
    dest = tmp_path / "dest"
    report = import_capture(
        src,
        dest,
        pdf_dirs=[tmp_path / "downloads"],
        bundle_id="synthetic-import",
        captured_by="test",
        browser=None,
    )
    assert report["matched"] == report["total"] == 10
    bundle = load_bundle(dest)
    assert len(bundle.manifest.records) == 10
    assert (dest / "files" / "r01.pdf").is_file() and (dest / "source_manifest.json").is_file()
    assert (dest / "CAPTURE_NOTES.md").is_file() and (dest / "import_report.json").is_file()
    by_id = {r.metadata.extra["source_record_id"]: r for r in bundle.manifest.records if r.metadata}
    r01 = by_id["r01"]
    assert r01.metadata is not None and r01.metadata.metadata_source == "capture_snapshot"
    assert r01.metadata.official_ref == f"{DEMO_CASE}/F00004"
    assert r01.artifacts[0].official_version_ref == f"{DEMO_CASE}/F00004/RED"
    assert r01.artifacts[0].sha256 and r01.artifacts[0].byte_size
    assert r01.metadata.extra["original_download_filename"].endswith(".pdf")
    assert (
        by_id["r03"].artifacts[0].version_type is not None
        and by_id["r03"].artifacts[0].version_type.value == "reclassified"
    )
    assert by_id["r03"].metadata.extra["page1_classification_text"] == "Confidential"
    assert by_id["r05"].artifacts[0].official_version_ref == f"{DEMO_CASE}/F03668/RED/A01/RED"
    assert (
        by_id["r08"].metadata.hearing is not None
        and by_id["r08"].metadata.hearing.session_sequence == 1
    )
    assert by_id["r10"].metadata.extra["page1_classification_text"] == "Strictly Confidential"
    # sha256sums of the copies equals the declared hashes
    sums = dict(
        reversed(line.split("  "))
        for line in (dest / "files" / "sha256sums.txt").read_text().splitlines()
    )
    assert sums["files/r01.pdf"] == r01.artifacts[0].sha256
    # originals untouched
    assert sorted(p.name for p in (tmp_path / "downloads").iterdir()) == sorted(
        json.loads((src / "manifest.json").read_text())["records"][i]["title"] + ".pdf"
        for i in range(10)
    )


def test_import_refuses_when_a_pdf_is_missing(tmp_path: Path) -> None:
    src = source_capture(tmp_path / "src", tmp_path / "downloads")
    (tmp_path / "downloads" / "Decision Assigning a Judge.pdf").unlink()
    with pytest.raises(SourceImportError, match="r03: MISSING"):
        import_capture(
            src,
            tmp_path / "dest",
            pdf_dirs=[tmp_path / "downloads"],
            bundle_id="x",
            captured_by="t",
            browser=None,
        )
    assert not (tmp_path / "dest" / "manifest.json").exists()


def test_import_is_repeatable(tmp_path: Path) -> None:
    src = source_capture(tmp_path / "src", tmp_path / "downloads")
    dest = tmp_path / "dest"
    kwargs = dict(pdf_dirs=[tmp_path / "downloads"], bundle_id="x", captured_by="t", browser=None)
    import_capture(src, dest, **kwargs)  # type: ignore[arg-type]
    first = (dest / "manifest.json").read_text()
    shutil.copy(dest / "manifest.json", tmp_path / "first.json")
    import_capture(src, dest, **kwargs)  # type: ignore[arg-type]
    assert (dest / "manifest.json").read_text() == first
