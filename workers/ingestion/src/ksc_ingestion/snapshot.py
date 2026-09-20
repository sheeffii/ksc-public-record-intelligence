"""Parser for the *normalised snapshot* format of the 2026-09-20 capture.

The operator's browser session did not save the raw PCR detail-page DOM. It
wrote one small HTML page per record holding a two-column table of the fields
the official detail page publishes, plus the official detail-page and PDF
links. That is browser-captured source metadata, one step removed from the
live page; it is parsed here, on its own, and never confused with a raw PCR
page parser (which does not exist yet — `capture.DetailPageParser`).

Blank fields are published as "—" / "— (not published)" and become None. Nothing
is inferred to fill them.
"""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup

_BLANK_PREFIXES = ("—", "-", "n/a")

FIELD_KEYS = {
    "Record ID": "record_id",
    "Case Number": "case_number",
    "Title": "title",
    "Document / Filing ID": "document_id",
    "Record Type": "record_type",
    "Filing Type": "filing_type",
    "Filing Party": "filing_party",
    "Court Level": "court_level",
    "Date": "date",
    "Language": "language",
    "Public / Redacted Status": "public_status",
    "SHA-256": "sha256",
    "Bytes": "bytes",
    "Selection Reason": "selection_reason",
}


class SnapshotFormatError(ValueError):
    pass


@dataclass(frozen=True)
class SnapshotRecord:
    record_id: str
    case_number: str
    title: str
    document_id: str | None
    record_type: str
    filing_type: str | None
    filing_party: str | None
    court_level: str | None
    date: str | None
    language_code: str | None
    language_name: str | None
    public_status: str
    sha256: str | None
    byte_size: int | None
    selection_reason: str | None
    detail_page_url: str
    pdf_url: str | None
    footer_note: str | None


def _blank(value: str | None) -> str | None:
    if value is None:
        return None
    text = " ".join(value.split())
    if not text or text.lower().startswith(_BLANK_PREFIXES):
        return None
    return text


def parse_snapshot(html: bytes | str) -> SnapshotRecord:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise SnapshotFormatError("snapshot has no field table")
    fields: dict[str, str] = {}
    for row in table.find_all("tr"):
        th, td = row.find("th"), row.find("td")
        if th is None or td is None:
            continue
        label = " ".join(th.get_text().split())
        if label not in FIELD_KEYS:
            raise SnapshotFormatError(f"unknown snapshot field {label!r}")
        fields[FIELD_KEYS[label]] = td.get_text()
    missing = {"record_id", "case_number", "title", "record_type", "public_status"} - set(fields)
    if missing:
        raise SnapshotFormatError(f"snapshot lacks fields {sorted(missing)}")

    detail_url: str | None = None
    pdf_url: str | None = None
    for p in soup.find_all("p", class_="src"):
        strongs = [" ".join(s.get_text().split()) for s in p.find_all("strong")]
        links = [a.get("href") for a in p.find_all("a")]
        for label, href in zip(strongs, links, strict=False):
            if label.startswith("Official detail page"):
                detail_url = str(href)
            elif label.startswith("Official PDF"):
                pdf_url = str(href)
    if detail_url is None:
        raise SnapshotFormatError("snapshot has no official detail page link")

    language_code = language_name = None
    lang = _blank(fields.get("language"))
    if lang:
        if "(" in lang and lang.endswith(")"):
            language_name, code = lang[:-1].rsplit("(", 1)
            language_code, language_name = code.strip().lower(), language_name.strip()
        else:
            language_name = lang

    footer = None
    notes = [
        " ".join(p.get_text().split()) for p in soup.find_all("p", class_="src") if not p.find("a")
    ]
    if notes:
        footer = notes[-1]

    size = _blank(fields.get("bytes"))
    return SnapshotRecord(
        record_id=" ".join(fields["record_id"].split()),
        case_number=" ".join(fields["case_number"].split()),
        title=" ".join(fields["title"].split()),
        document_id=_blank(fields.get("document_id")),
        record_type=" ".join(fields["record_type"].split()),
        filing_type=_blank(fields.get("filing_type")),
        filing_party=_blank(fields.get("filing_party")),
        court_level=_blank(fields.get("court_level")),
        date=_blank(fields.get("date")),
        language_code=language_code,
        language_name=language_name,
        public_status=" ".join(fields["public_status"].split()),
        sha256=(_blank(fields.get("sha256")) or "").lower() or None,
        byte_size=int(size) if size and size.isdigit() else None,
        selection_reason=_blank(fields.get("selection_reason")),
        detail_page_url=detail_url,
        pdf_url=pdf_url,
        footer_note=footer,
    )
