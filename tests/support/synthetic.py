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


# ------------------------------------------------------ source capture v0 --
def snapshot_html(fields: dict[str, str], detail_url: str, pdf_url: str) -> str:
    """A page in the normalised-snapshot format the 2026-09-20 capture used."""

    rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in fields.items())
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>snap</title></head><body>"
        f"<h1>{fields.get('Title', '')}</h1><table>{rows}</table>"
        f'<p class="src"><strong>Official detail page:</strong><br><a href="{detail_url}">{detail_url}</a><br>'
        f'<strong>Official PDF:</strong><br><a href="{pdf_url}">{pdf_url}</a></p>'
        '<p class="src">Normalised snapshot of the official KSC public detail page, captured 2026-09-20. '
        "Public record only.</p></body></html>"
    )


def source_capture(root: Path, downloads: Path) -> Path:
    """A synthetic capture in the operator's v0 layout (manifest.json + pages/ +
    files/sha256sums.txt, no PDF bytes) plus the "downloaded" PDFs under
    `downloads/` with human-readable names. Case KSC-DEMO-0000 throughout."""

    import hashlib

    (root / "pages").mkdir(parents=True, exist_ok=True)
    (root / "files").mkdir(exist_ok=True)
    downloads.mkdir(parents=True, exist_ok=True)

    def pdf(lines: list[str]) -> bytes:
        return make_pdf(lines)

    specs = [
        # record_id, document_id, record_type, filing_type, party, court, date, lang, status, title, header lines
        (
            "r01",
            "F00004RED",
            "Filing",
            "Decision",
            "Specialist Chambers",
            "Basic Court Chamber",
            "27/05/2020",
            ("eng", "English"),
            "public_redacted",
            "Public Redacted Version of Decision on a Request",
            [f"{DEMO_CASE}/F00004/RED/1 of 4", "Classification: Public"],
        ),
        (
            "r02",
            "F00004RED",
            "Filing",
            "Decision",
            "Specialist Chambers",
            "Basic Court Chamber",
            "27/05/2020",
            ("sqi", "Albanian"),
            "public_redacted",
            "Version i redaktuar publik i Vendimit",
            [f"{DEMO_CASE}/F00004/RED/sqi/1 of 4", "Klasifikimi: Publik"],
        ),
        (
            "r03",
            "F00001",
            "Filing",
            "Decision",
            "President",
            "Basic Court Chamber",
            "23/04/2020",
            ("eng", "English"),
            "public",
            "Decision Assigning a Judge",
            [
                f"{DEMO_CASE}/F00001/1 of 3",
                "Classification: Confidential",
                "PUBLIC Reclassified as Public pursuant to instructions contained in CRSPD1 of 24 April 2020",
            ],
        ),
        (
            "r04",
            "F00045",
            "Filing Annex",
            "Indictment",
            None,
            "Basic Court Chamber",
            None,
            ("eng", "English"),
            "public_redacted",
            "ANNEX 3 to Submission of corrected and public redacted versions",
            [f"{DEMO_CASE}/F00045/A03/1 of 68"],
        ),
        (
            "r05",
            "F03668RED",
            "Filing Annex",
            "Filing Annex",
            None,
            "Basic Court Chamber",
            None,
            ("eng", "English"),
            "public_redacted",
            "ANNEX 1 to Public Redacted Version of a Brief",
            [f"{DEMO_CASE}/F03668/RED/A01/RED/1 of 14"],
        ),
        (
            "r06",
            "F03667CORRED",
            "Filing",
            "Brief",
            "Specialist Prosecutor",
            "Basic Court Chamber",
            "19/01/2026",
            ("eng", "English"),
            "public_redacted_corrected",
            "Public Redacted Version of Corrected Version of a Brief",
            [f"{DEMO_CASE}/F03667/COR/RED/1 of 700"],
        ),
        (
            "r07",
            "IA042-F00005RED",
            "Filing",
            "Decision",
            "Specialist Chambers",
            "Court of Appeal Chamber",
            "28/05/2026",
            ("eng", "English"),
            "public_redacted",
            "Public Redacted Version of Decision on an Appeal",
            [f"{DEMO_CASE}/IA042/F00005/RED/1 of 41"],
        ),
        (
            "r08",
            None,
            "Transcript",
            "Transcript",
            None,
            None,
            "18/02/2026",
            ("eng", "English"),
            "public",
            "Closing Statements - 18 February 2026",
            [DEMO_CASE, "18 February 2026", "Page 29148"],
        ),
        (
            "r09",
            None,
            "Transcript",
            "Transcript",
            None,
            None,
            "18/02/2026",
            ("sqi", "Albanian"),
            "public",
            "Deklaratat përmbyllëse - 18 shkurt 2026",
            [DEMO_CASE, "18 shkurt 2026"],
        ),
        (
            "r10",
            "F03774",
            "Filing",
            "Request",
            "Specialist Counsel",
            "Basic Court Chamber",
            "21/08/2026",
            ("eng", "English"),
            "public",
            "Selimi Defence Request for Reclassification",
            [
                f"{DEMO_CASE}/F03769",
                "Classification: Strictly Confidentia l",
                "Reclassified as Public pursuant to instructions contained in CRSPD989 of 8 September 2026 PUBLIC",
            ],
        ),
    ]
    records = []
    sums = []
    for rid, doc_id, rtype, ftype, party, court, date, (
        lcode,
        lname,
    ), status, title, header in specs:
        data = pdf([*header, title])
        digest = hashlib.sha256(data).hexdigest()
        (downloads / f"{title}.pdf").write_bytes(data)
        detail = f"{PCR}/details.php?doc_id=00000000000000{rid[1:]}&doc_type=stl_{'transcript' if rtype == 'Transcript' else 'filing_annex' if rtype == 'Filing Annex' else 'filing'}&lang={lcode}"
        kind = "Transcript" if rtype == "Transcript" else "Filing"
        pdf_url = f"{PCR}/LW/Published/{kind}/{DEMO_CASE}/{rid}.pdf"
        local_file = f"files/{rid}__{doc_id or '-'}__{lcode}.pdf"
        fields = {
            "Record ID": rid,
            "Case Number": DEMO_CASE,
            "Title": title,
            "Document / Filing ID": doc_id or "— (not published for this record type)",
            "Record Type": rtype,
            "Filing Type": ftype,
            "Filing Party": party or "— (not published)",
            "Court Level": court or "— (not published)",
            "Date": date or "—",
            "Language": f"{lname} ({lcode})",
            "Public / Redacted Status": status,
            "SHA-256": digest,
            "Bytes": str(len(data)),
            "Selection Reason": "synthetic",
        }
        (root / "pages" / f"{rid}.html").write_text(
            snapshot_html(fields, detail, pdf_url), encoding="utf-8"
        )
        rec = {
            "record_id": rid,
            "case_number": DEMO_CASE,
            "title": title,
            "document_id": doc_id,
            "record_type": rtype,
            "filing_type": ftype,
            "filing_party": party,
            "court_level": court,
            "date": date,
            "language": {"code": lcode, "name": lname},
            "public_status": status,
            "confidential_content_included": False,
            "detail_page_url": detail,
            "pdf_url": pdf_url,
            "artifact_path": f"/LW/Published/{kind}/{DEMO_CASE}/{rid}.pdf",
            "local_file": local_file,
            "local_page_snapshot": f"pages/{rid}.html",
            "sha256": digest,
            "bytes": len(data),
            "http_status_verified": 200,
            "selection_reason": "synthetic",
        }
        if rtype == "Transcript":
            rec["hearing_date"] = date
        records.append(rec)
        sums.append(f"{digest}  {local_file}")
    manifest = {
        "bundle": {
            "name": "synthetic-source-capture",
            "case_number": DEMO_CASE,
            "capture_date": "2026-09-20",
            "capture_method": "synthetic fixture (no browser session, no real record)",
            "record_count": len(records),
        },
        "records": records,
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    (root / "files" / "sha256sums.txt").write_text("\n".join(sums) + "\n")
    (root / "CAPTURE_NOTES.md").write_text("# synthetic capture notes\n")
    return root
