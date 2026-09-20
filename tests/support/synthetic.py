"""Synthetic PDFs and capture bundles for the ingestion tests.

Everything produced here is invented for the synthetic demo case
`KSC-DEMO-0000` (docs/DATA_MODEL.md). Filing numbers, titles and PCR-style
identifiers are placeholders; the URLs use the official host only so the
allowlist is exercised, and the record ids are visibly non-real
(`00000000000000a1`, …). No real KSC record is described or implied.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEMO_CASE = "KSC-DEMO-0000"
PCR = "https://repository.scp-ks.org"
CAPTURED_AT = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def make_pdf(lines: list[str]) -> bytes:
    """A small, valid single-page PDF with a Helvetica text layer that pypdf
    can read back. Deterministic for identical input."""

    def esc(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_lines = ["BT", "/F1 12 Tf", "72 720 Td", "14 TL"]
    for line in lines:
        content_lines.append(f"({esc(line)}) Tj T*")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    ).encode()
    return bytes(out)


def detail_url(doc_id: str, lang: str = "eng") -> str:
    return f"{PCR}/details.php?doc_id={doc_id}&doc_type=stl_filing&lang={lang}"


def artifact_url(kind: str, name: str) -> str:
    return f"{PCR}/LW/Published/{kind}/{DEMO_CASE}/{name}"


def listing_url(page: int = 1) -> str:
    return (
        f"{PCR}/?icc_filters[case_number]={DEMO_CASE}&icc_filters[language_short]=_all"
        f"&icc_filters[record_type_short]=_all&icc_filters[sort_order]=_sort_date_newest/1000"
        f"&page={page}"
    )


def metadata(
    *,
    record_type: str,
    official_ref: str,
    title: str,
    classification: str | None = "Public",
    language: str = "en",
    filing_party_label: str | None = None,
    filing_date: str | None = None,
    document_date: str | None = None,
    hearing: dict[str, Any] | None = None,
    case_number: str = DEMO_CASE,
    external_record_id: str | None = None,
) -> dict[str, Any]:
    md: dict[str, Any] = {
        "metadata_source": "synthetic_fixture",
        "record_type": record_type,
        "official_ref": official_ref,
        "title": title,
        "case_number": case_number,
        "language": language,
        "classification": classification,
    }
    if filing_party_label:
        md["filing_party_label"] = filing_party_label
    if filing_date:
        md["filing_date"] = filing_date
    if document_date:
        md["document_date"] = document_date
    if hearing:
        md["hearing"] = hearing
    if external_record_id:
        md["external_record_id"] = external_record_id
    return md


class BundleBuilder:
    """Writes a synthetic capture bundle to disk."""

    def __init__(self, root: Path, bundle_id: str = "synthetic-demo-01") -> None:
        self.root = root
        self.bundle_id = bundle_id
        self.records: list[dict[str, Any]] = []
        self.listing_pages: list[dict[str, Any]] = []
        (root / "pages").mkdir(parents=True, exist_ok=True)
        (root / "files").mkdir(parents=True, exist_ok=True)

    def add_listing(self, name: str = "listing-all-p1.html", page: int = 1) -> BundleBuilder:
        (self.root / "pages" / name).write_text("<html><body>synthetic listing</body></html>")
        self.listing_pages.append({"url": listing_url(page), "file": f"pages/{name}"})
        return self

    def add_record(
        self,
        doc_id: str,
        md: dict[str, Any] | None,
        artifacts: list[dict[str, Any]],
        *,
        detail_page: bool = False,
        reason: str = "synthetic coverage",
        lang: str = "eng",
    ) -> BundleBuilder:
        record: dict[str, Any] = {
            "detail_page_url": detail_url(doc_id, lang),
            "artifacts": artifacts,
            "selection_reason": reason,
        }
        if detail_page:
            (self.root / "pages" / f"{doc_id}.html").write_text(
                "<html><body>synthetic detail page</body></html>"
            )
            record["detail_page_file"] = f"pages/{doc_id}.html"
        if md is not None:
            record["metadata"] = md
        self.records.append(record)
        return self

    def file(self, name: str, data: bytes) -> str:
        (self.root / "files" / name).write_bytes(data)
        return f"files/{name}"

    def write(self, **overrides: Any) -> Path:
        manifest: dict[str, Any] = {
            "bundle_id": self.bundle_id,
            "case_number": DEMO_CASE,
            "captured_by": "test operator",
            "captured_at": CAPTURED_AT.isoformat(),
            "capture_method": "synthetic fixture (no browser session, no real record)",
            "browser": None,
            "listing_pages": self.listing_pages,
            "records": self.records,
        }
        manifest.update(overrides)
        (self.root / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return self.root


def standard_bundle(root: Path, bundle_id: str = "synthetic-demo-01") -> Path:
    """The representative synthetic corpus used by the integration tests:

    a1  SPO filing, original + public redacted version (two files)
    a2  Defence filing, single public file
    a3  Trial Panel decision, metadata only (URL recorded, no file)
    a4  transcript with hearing date, public redacted
    a5  confidential record (no public file) — must stay not_public
    a6  record with a non-PDF file — unsupported artifact
    a7  Albanian-language version of a2's filing (translation)
    """

    b = BundleBuilder(root, bundle_id).add_listing()
    a1 = b.file("F00001.pdf", make_pdf([f"{DEMO_CASE}/F00001", "Synthetic SPO request"]))
    a1r = b.file(
        "F00001-RED.pdf",
        make_pdf([f"{DEMO_CASE}/F00001/RED", "Public redacted version", "[REDACTED]"]),
    )
    b.add_record(
        "00000000000000a1",
        metadata(
            record_type="filing",
            official_ref=f"{DEMO_CASE}/F00001",
            title="Synthetic Prosecution request",
            filing_party_label="Specialist Prosecutor",
            filing_date="2020-05-28",
        ),
        [
            {"url": artifact_url("Filing", "F00001.pdf"), "file": a1},
            {
                "url": artifact_url("Filing", "F00001-RED.pdf"),
                "file": a1r,
                "official_version_ref": f"{DEMO_CASE}/F00001/RED",
                "classification": "Public Redacted",
            },
        ],
        detail_page=True,
    )
    a2 = b.file("F00002.pdf", make_pdf([f"{DEMO_CASE}/F00002", "Synthetic Defence response"]))
    b.add_record(
        "00000000000000a2",
        metadata(
            record_type="filing",
            official_ref=f"{DEMO_CASE}/F00002",
            title="Synthetic Defence response",
            filing_party_label="Defence",
            filing_date="28 June 2020",
        ),
        [{"url": artifact_url("Filing", "F00002.pdf"), "file": a2}],
    )
    b.add_record(
        "00000000000000a3",
        metadata(
            record_type="decision",
            official_ref=f"{DEMO_CASE}/F00003",
            title="Synthetic decision on a request",
            filing_party_label="Trial Panel",
            document_date="2021-01-15",
        ),
        [{"url": artifact_url("Filing", "F00003.pdf")}],
        reason="metadata-only: URL recorded, bytes deliberately not captured",
    )
    a4 = b.file(
        "T-2024-11-25.pdf",
        make_pdf([DEMO_CASE, "Trial Hearing - 25 November 2024", "Public Redacted"]),
    )
    b.add_record(
        "00000000000000a4",
        metadata(
            record_type="transcript",
            official_ref=f"{DEMO_CASE}/T/2024-11-25",
            title="Trial Hearing - 25 November 2024 - Public Redacted",
            classification="Public Redacted",
            hearing={"date": "2024-11-25", "session_sequence": 1, "hearing_type": "trial"},
        ),
        [
            {
                "url": artifact_url("Transcript", "Trial Hearing - 25 November 2024.pdf"),
                "file": a4,
            }
        ],
    )
    b.add_record(
        "00000000000000a5",
        metadata(
            record_type="filing",
            official_ref=f"{DEMO_CASE}/F00005",
            title="Synthetic confidential submission",
            classification="Confidential",
        ),
        [],
        reason="negative: confidential entry seen in listing; nothing public to capture",
    )
    a6 = b.file("F00006.pdf", b"<html>not a pdf</html>")
    b.add_record(
        "00000000000000a6",
        metadata(
            record_type="filing",
            official_ref=f"{DEMO_CASE}/F00006",
            title="Synthetic filing whose download was an error page",
        ),
        [{"url": artifact_url("Filing", "F00006.pdf"), "file": a6}],
        reason="negative: unsupported artifact",
    )
    a7 = b.file("F00002-ALB.pdf", make_pdf([f"{DEMO_CASE}/F00002", "Përgjigje sintetike"]))
    b.add_record(
        "00000000000000a7",
        metadata(
            record_type="filing",
            official_ref=f"{DEMO_CASE}/F00002",
            title="Synthetic Defence response (Albanian)",
            filing_party_label="Defence",
            language="sq",
        ),
        [
            {
                "url": artifact_url("Filing", "F00002-ALB.pdf"),
                "file": a7,
                "official_version_ref": f"{DEMO_CASE}/F00002/ALB",
                "version_type": "translation",
            }
        ],
        lang="alb",
    )
    return b.write()
