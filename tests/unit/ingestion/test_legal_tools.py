"""Legal Tools mirror records (ADR-030): only public, in-scope records with an
official artifact URL are taken; nothing the mirror does not say is invented;
and a mirror bundle goes through the existing importer with its provenance."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Any

from pypdf import PdfWriter

from ksc_ingestion import legal_tools as lt
from ksc_ingestion.capture import discover, load_bundle
from ksc_ingestion.capture_import import import_capture
from ksc_ingestion.discovery import DiscoveredRecord

CASE = "KSC-BC-2020-06"
ENG = "5d8f15835240a52088f2a853"
SQI = "5d8f15835240a52088f2a839"
SRP = "635bae266ed280740af8bc60"
FILING_URL = (
    "https://repository.scp-ks.org/LW/Published/Filing/0b10c8e18026f7b2/"
    "Veseli%20Defence%20Request%20for%20Reclassification.pdf"
)
TRANSCRIPT_URL = (
    "https://repository.scp-ks.org/LW/Published/Transcript/KSC-BC-2020-06/"
    "Closing%20Statements%20-%2011%20February%202026%20-%20Public%20Redacted.pdf"
)


def hit(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "slug": "yw5woic0",
        "title": "Veseli Defence Request for Reclassification",
        "externalId": f"{CASE}/F02246",
        "caseNumber": CASE,
        "confidentiality": "public",
        "requireDownloadPermission": False,
        "isPublished": True,
        "deleted": False,
        "languageIds": [ENG],
        "documentOrigin": {"kscPdfUrlEncoded": FILING_URL, "kscPdfUrl": FILING_URL},
        "orignalPdfURL": "https://ltd-docs.s3.nl-ams.scw.cloud/alldocs/veseli_277404.pdf",
        "dateCreated": "2024-04-15T00:00:00.000Z",
        "judicialDocumentType": "submission",
        "source": "Defence",
    }
    base.update(overrides)
    return base


def test_public_english_filing_is_taken() -> None:
    record = lt.parse_hit(hit(), case_number=CASE)
    assert isinstance(record, lt.MirrorRecord)
    assert record.language_code == "eng"
    assert record.official_url == FILING_URL
    assert record.purl == "https://www.legal-tools.org/doc/yw5woic0/"
    assert not record.is_transcript


def test_out_of_scope_or_unusable_hits_are_skipped_with_a_reason() -> None:
    cases = {
        "language out of scope (Serbian)": hit(languageIds=[SRP]),
        "mirror confidentiality 'confidential'": hit(confidentiality="confidential"),
        "mirror requires download permission": hit(requireDownloadPermission=True),
        "no official artifact URL": hit(documentOrigin={"url": "https://www.scp-ks.org/"}),
        "official URL is not on an official host": hit(
            documentOrigin={"kscPdfUrlEncoded": "https://example.org/x.pdf"}
        ),
        "case 'KSC-BC-2020-05'": hit(caseNumber="KSC-BC-2020-05"),
        "no PDF on the mirror": hit(orignalPdfURL=None),
    }
    for reason, h in cases.items():
        parsed = lt.parse_hit(h, case_number=CASE)
        assert isinstance(parsed, lt.Skip), reason
        assert parsed.reason == reason
    off_host = lt.parse_hit(hit(orignalPdfURL="https://evil.example/x.pdf"), case_number=CASE)
    assert isinstance(off_host, lt.Skip) and "not a Legal Tools URL" in off_host.reason


def test_serbian_transcript_mislabeled_english_is_rejected() -> None:
    parsed = lt.parse_hit(
        hit(
            title="Zasedanje u prvostepenom postupku - 18. maj 2023.",
            externalId=CASE,
            documentOrigin={"kscPdfUrlEncoded": TRANSCRIPT_URL},
        ),
        case_number=CASE,
    )
    assert isinstance(parsed, lt.Skip)
    assert parsed.reason == "Serbian transcript mislabeled as supported language"


def test_published_document_id_from_mirror_external_id() -> None:
    assert lt.published_document_id(f"{CASE}/F02246", CASE) == "F02246"
    assert lt.published_document_id(f"{CASE}/F01603/RED", CASE) == "F01603RED"
    assert lt.published_document_id(f"{CASE}/IA042/F00002/RED/A01", CASE) == "IA042-F00002RED"
    assert lt.published_document_id(f"{CASE}/F00877RED/A03", CASE) == "F00877RED"
    assert lt.published_document_id(f"{CASE}/IA999/F00001/REDCOR", CASE) == "IA999-F00001REDCOR"
    assert lt.published_document_id(CASE, CASE) is None
    assert lt.published_document_id(f"{CASE}/T/2024", CASE) is None
    assert lt.published_document_id("KSC-BC-2020-05/F00001", CASE) is None


def test_plan_skips_held_and_duplicate_official_urls() -> None:
    held = FILING_URL.replace("%20", " ")  # held manifests may spell it decoded
    other = hit(
        slug="aaaa1111",
        documentOrigin={"kscPdfUrlEncoded": TRANSCRIPT_URL},
        externalId=CASE,
        title="Closing Statements - 11 February 2026 - Public Redacted",
    )
    dup = {**other, "slug": "bbbb2222"}
    planned = lt.plan([hit(), other, dup], case_number=CASE, held_official_urls=[held])
    assert [r.slug for r in planned.selected] == ["aaaa1111"]
    assert sorted(s.reason for s in planned.skipped) == [
        "already held (official URL)",
        "mirror duplicate (official URL)",
    ]


def test_plan_refuses_same_date_transcript_collision() -> None:
    first = hit(
        slug="first",
        externalId=CASE,
        title="Initial Appearance of A",
        dateCreated="2020-11-09T00:00:00.000Z",
        documentOrigin={"kscPdfUrlEncoded": TRANSCRIPT_URL.replace("Closing", "First")},
    )
    second = hit(
        slug="second",
        externalId=CASE,
        title="Initial Appearance of B",
        dateCreated="2020-11-09T00:00:00.000Z",
        documentOrigin={"kscPdfUrlEncoded": TRANSCRIPT_URL.replace("Closing", "Second")},
    )
    planned = lt.plan([first, second], case_number=CASE)
    assert planned.selected == []
    assert {row.reason for row in planned.skipped} == {
        "same-date transcript identity collision (date-only key refused)"
    }


def test_pilot_is_deterministic_stratified_and_prefers_language_pairs() -> None:
    hits = []
    sources = ["Defence", "Prosecution", "Trial Chamber", "Appeals Chamber", "Registry", "Victim"]
    for index in range(24):
        source = sources[index % len(sources)]
        external = f"{CASE}/F{index + 100:05d}"
        for language in ([ENG, SQI] if index < 12 else [ENG]):
            hits.append(
                hit(
                    slug=f"s{index}{language[-2:]}",
                    externalId=external,
                    languageIds=[language],
                    source=source,
                    documentOrigin={
                        "kscPdfUrlEncoded": FILING_URL.replace(
                            "0b10c8e18026f7b2", f"{index:016x}"
                        ).replace("Veseli", f"{language}-{index}-Veseli")
                    },
                )
            )
    records = lt.plan(hits, case_number=CASE).selected
    first = lt.select_pilot(records, size=18)
    second = lt.select_pilot(reversed(records), size=18)
    assert [r.official_url for r in first] == [r.official_url for r in second]
    assert len(first) == 18
    assert {lt.pilot_category(r) for r in first} >= {
        "Defence",
        "SPO",
        "Trial Chamber",
        "Appeals",
        "Registry",
        "Victims' Counsel",
    }
    assert sum(r.language_code == "sqi" for r in first) >= 6


def test_external_record_id_is_the_official_artifact() -> None:
    assert lt.external_record_id(FILING_URL) == "artifact:0b10c8e18026f7b2"
    assert lt.external_record_id(TRANSCRIPT_URL).startswith(
        "artifact-path:/LW/Published/Transcript/KSC-BC-2020-06/Closing Statements"
    )


def test_entry_takes_only_what_the_mirror_says() -> None:
    record = lt.parse_hit(
        hit(externalId=f"{CASE}/F01603/RED", judicialDocumentType="decision"), case_number=CASE
    )
    assert isinstance(record, lt.MirrorRecord)
    entry = lt.source_entry(
        record, record_id="r01", sha256="a" * 64, byte_size=10, permission="test permission"
    )
    assert entry["document_id"] == "F01603RED"
    assert entry["public_status"] == "public_redacted"
    assert entry["filing_type"] == "Decision"
    assert entry["filing_party"] is None and entry["court_level"] is None
    assert entry["date"] == "15/04/2024"
    assert entry["detail_page_url"] == entry["pdf_url"] == FILING_URL
    assert entry["mirror"]["purl"] == record.purl
    assert entry["mirror"]["permission"] == "test permission"


def _pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_mirror_bundle_imports_with_provenance(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "files").mkdir(parents=True)
    (source / "pages").mkdir()
    data = _pdf()
    digest = hashlib.sha256(data).hexdigest()
    record = lt.parse_hit(hit(), case_number=CASE)
    assert isinstance(record, lt.MirrorRecord)
    entry = lt.source_entry(
        record, record_id="r01", sha256=digest, byte_size=len(data), permission="CILRAP, test"
    )
    (source / "files" / "r01.pdf").write_bytes(data)
    (source / "pages" / "r01.html").write_text(lt.snapshot_html(entry), encoding="utf-8")
    (source / "manifest.json").write_text(
        json.dumps(
            {
                "bundle": {
                    "bundle_id": "t-ltd-01",
                    "case_number": CASE,
                    "capture_date": "2026-09-27",
                    "capture_method": "mirror test",
                    "fetch_method": lt.FETCH_METHOD,
                    "record_count": 1,
                },
                "records": [entry],
            }
        ),
        encoding="utf-8",
    )

    dest = tmp_path / "bundle"
    import_capture(
        source,
        dest,
        pdf_dirs=[source / "files"],
        bundle_id="t-ltd-01",
        captured_by="tester",
        browser=None,
    )
    written = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))
    artifact = written["records"][0]["artifacts"][0]
    metadata = written["records"][0]["metadata"]
    assert artifact["fetch_method"] == lt.FETCH_METHOD
    assert artifact["url"] == FILING_URL
    assert metadata["external_record_id"] == "artifact:0b10c8e18026f7b2"
    assert metadata["extra"]["mirror"]["purl"] == record.purl

    (discovered,) = discover(load_bundle(dest))
    assert isinstance(discovered, DiscoveredRecord)
    assert discovered.external_record_id == "artifact:0b10c8e18026f7b2"
    assert discovered.artifacts[0].fetch_method == lt.FETCH_METHOD
    assert discovered.artifacts[0].declared_sha256 == digest
