"""Legal Tools Database mirror of the public KSC record (ADR-030).

The Legal Tools Database (legal-tools.org, administered by CILRAP) holds public
KSC filings and transcripts it downloaded from the official repository, each
with the official `repository.scp-ks.org` PDF URL it came from. CILRAP gave the
project written permission to download them (ADR-030). This module turns its
public search API into capture-v0 records the existing `import-capture` path
already understands; `scripts/ksc_legal_tools_harvest.py` does the network I/O.

What is taken from the mirror, and what is not:

- the **bytes** (hashed; re-verified against any official hash we hold);
- the **official artifact URL** (must classify as an official PCR artifact, or
  the record is skipped — never guessed);
- title, published filing id, language and date, which agreed with every
  officially captured record we could compare (2026-09-27: 168/168 dates);
- nothing else. Filing party and court level stay blank rather than being
  translated from the mirror's own categories.

Public status is still decided by the PDF's own page-1 markings
(`scripts/check_capture_pdfs.py`), exactly as for browser captures.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote, unquote, urlsplit

from ksc_ingestion.sources import NotOfficialSourceError, UrlKind, classify

FETCH_METHOD = "legal_tools_mirror"
MIRROR_NAME = "Legal Tools Database"
SEARCH_URL = "https://legal-tools.org/api/ltddocs/search"
# The API host, the document pages (PURLs) and the object store the PDFs live in.
MIRROR_HOSTS: frozenset[str] = frozenset(
    {"legal-tools.org", "www.legal-tools.org", "ltd-docs.s3.nl-ams.scw.cloud"}
)
PAGE_SIZE = 100

# Legal Tools language ids → the capture-v0 language the official repository
# publishes. Serbian is out of scope for this project (English and Shqip only).
LANGUAGES: dict[str, tuple[str, str]] = {
    "5d8f15835240a52088f2a853": ("eng", "English"),
    "5d8f15835240a52088f2a839": ("sqi", "Albanian"),
}
OUT_OF_SCOPE_LANGUAGES: dict[str, str] = {"635bae266ed280740af8bc60": "Serbian"}

# The mirror's judicial document types that name the same thing the official
# repository's "Filing Type" does. Anything else stays blank.
_FILING_TYPES = {"decision": "Decision", "order": "Order", "judgment": "Judgment"}
_SERIES_RE = re.compile(r"^(?:IA|PL|RAC)\d{3}$")
_FILING_RE = re.compile(r"^F\d{5}[A-Z0-9]*$")
_ANNEX_TOKEN_RE = re.compile(r"^A\d{2,3}$")
_ANNEX_TITLE_RE = re.compile(
    r"^(?:public\s+redacted\s+version\s+of\s+)?(?:ANNEX|SHTOJC[ËE])\s+\d+\b", re.IGNORECASE
)
_FILING_ID_IN_PATH_RE = re.compile(r"^/LW/Published/Filing/([0-9a-f]{16})/")
_SERBIAN_TRANSCRIPT_RE = re.compile(
    r"\b(?:zasedanje|statusna\s+konferencija|inicijalno\s+pojavljivanje|"
    r"ponovno\s+pristupanje|su[đd]enje|javna\s+sednica|svedok)\b",
    re.IGNORECASE,
)
_TRANSCRIPT_VERSION_REVIEW_RE = re.compile(r"\b(?:superseded|zamenjen[ao]?)\b", re.IGNORECASE)

PILOT_CATEGORY_QUOTAS: tuple[tuple[str, int], ...] = (
    ("Defence", 20),
    ("SPO", 20),
    ("Trial Chamber", 15),
    ("Appeals", 10),
    ("Registry", 10),
    ("Victims' Counsel", 10),
    ("Other", 15),
)


class MirrorError(ValueError):
    """A mirror record or URL that cannot be used without guessing."""


def require_mirror(url: str) -> str:
    """The URL if it is https on a Legal Tools host; otherwise raise."""

    parts = urlsplit(url.strip())
    if parts.scheme != "https" or (parts.hostname or "").lower() not in MIRROR_HOSTS:
        raise MirrorError(f"not a Legal Tools URL: {url!r}")
    return url.strip()


def official_key(url: str) -> str:
    """Comparable form of an official artifact URL: the mirror and our
    manifests percent-encode names differently, so compare decoded."""

    return unquote(url.strip())


@dataclass(frozen=True)
class MirrorRecord:
    slug: str
    purl: str
    external_id: str
    title: str
    case_number: str
    language_code: str
    language_name: str
    official_url: str
    pdf_url: str
    date: str | None
    judicial_document_type: str | None
    mirror_source: str | None
    raw: dict[str, Any] = field(repr=False, compare=False)

    @property
    def is_transcript(self) -> bool:
        return classify(self.official_url).artifact_kind == "Transcript"


@dataclass(frozen=True)
class Skip:
    slug: str | None
    title: str | None
    reason: str


def looks_serbian(text: str) -> bool:
    """Strong Serbian transcript markers used only to reject mislabeled input."""

    folded = unicodedata.normalize("NFKC", " ".join(text.split()))
    return bool(_SERBIAN_TRANSCRIPT_RE.search(folded))


def _official_url(hit: Mapping[str, Any]) -> str | None:
    origin = hit.get("documentOrigin") or {}
    for key in ("kscPdfUrlEncoded", "kscPdfUrl"):
        value = origin.get(key)
        if value:
            # A few mirror URLs keep spaces; encode them exactly once.
            return quote(value.strip(), safe=":/?&=%#")
    return None


def parse_hit(hit: Mapping[str, Any], *, case_number: str) -> MirrorRecord | Skip:
    """One search hit → a usable record, or a Skip with the reason."""

    slug = hit.get("slug")
    title = " ".join(str(hit.get("title") or "").split()) or None
    if hit.get("deleted") or not hit.get("isPublished", True):
        return Skip(slug, title, "not published on the mirror")
    if hit.get("caseNumber") != case_number:
        return Skip(slug, title, f"case {hit.get('caseNumber')!r}")
    if hit.get("confidentiality") != "public":
        return Skip(slug, title, f"mirror confidentiality {hit.get('confidentiality')!r}")
    if hit.get("requireDownloadPermission"):
        return Skip(slug, title, "mirror requires download permission")
    if not slug or not title:
        return Skip(slug, title, "no slug or title")
    languages = hit.get("languageIds") or []
    if len(languages) != 1:
        return Skip(slug, title, f"{len(languages)} languages declared")
    if languages[0] in OUT_OF_SCOPE_LANGUAGES:
        return Skip(slug, title, f"language out of scope ({OUT_OF_SCOPE_LANGUAGES[languages[0]]})")
    if languages[0] not in LANGUAGES:
        return Skip(slug, title, f"unknown language id {languages[0]!r}")
    official = _official_url(hit)
    if official is None:
        return Skip(slug, title, "no official artifact URL")
    try:
        if classify(official).kind is not UrlKind.PCR_ARTIFACT:
            return Skip(slug, title, "official URL is not a repository artifact")
    except NotOfficialSourceError:
        return Skip(slug, title, "official URL is not on an official host")
    pdf_url = hit.get("orignalPdfURL")  # sic: the mirror's field name
    if not pdf_url:
        return Skip(slug, title, "no PDF on the mirror")
    try:
        require_mirror(pdf_url)
    except MirrorError as exc:
        return Skip(slug, title, str(exc))
    code, name = LANGUAGES[languages[0]]
    created = str(hit.get("dateCreated") or "")[:10] or None
    record = MirrorRecord(
        slug=slug,
        purl=f"https://www.legal-tools.org/doc/{slug}/",
        external_id=str(hit.get("externalId") or ""),
        title=title,
        case_number=case_number,
        language_code=code,
        language_name=name,
        official_url=official,
        pdf_url=pdf_url,
        date=created,
        judicial_document_type=hit.get("judicialDocumentType"),
        mirror_source=hit.get("source"),
        raw=dict(hit),
    )
    if record.is_transcript and looks_serbian(record.title):
        return Skip(slug, title, "Serbian transcript mislabeled as supported language")
    if record.is_transcript and _TRANSCRIPT_VERSION_REVIEW_RE.search(record.title):
        return Skip(slug, title, "transcript version semantics require review")
    return record


def published_document_id(external_id: str, case_number: str) -> str | None:
    """The repository's published filing number for a mirror external id:
    `KSC-BC-2020-06/IA042/F00002/RED/A01` → `IA042-F00002RED`. The annex
    number is not part of it (the importer reads it from the title). None when
    the id has any token this function does not know."""

    if not external_id.startswith(case_number + "/"):
        return None
    tokens = external_id[len(case_number) + 1 :].split("/")
    series = tokens.pop(0) if tokens and _SERIES_RE.match(tokens[0]) else None
    if not tokens or not _FILING_RE.match(tokens[0]):
        return None
    filing = tokens.pop(0)
    suffix = ""
    for token in tokens:
        if _ANNEX_TOKEN_RE.match(token):
            continue
        if not re.fullmatch(r"[A-Z0-9]+", token):
            return None
        suffix += token
    return (f"{series}-" if series else "") + filing + suffix


def public_status_for(document_id: str | None, title: str) -> str:
    """Same rule as the browser collector's `publicStatusFor`."""

    ident = (document_id or "").upper()
    if ident.endswith("CORRED"):
        return "public_redacted_corrected"
    if ident.endswith("RED2"):
        return "public_redacted_v2"
    if ident.endswith("RED"):
        return "public_redacted"
    if re.search(r"public\s+redacted|redaktuar\s+publik", title, re.IGNORECASE):
        return "public_redacted"
    return "public"


def external_record_id(official_url: str) -> str:
    """Stable id for the source record. The mirror does not know the
    repository's detail-page `doc_id`, so the official artifact is the key:
    its folder id for filings, its decoded path for transcripts."""

    path = unquote(urlsplit(official_url).path)
    m = _FILING_ID_IN_PATH_RE.match(path)
    if m:
        return f"artifact:{m.group(1)}"
    key = f"artifact-path:{path}"
    if len(key) > 256:
        raise MirrorError(f"official artifact path too long for a record id: {path!r}")
    return key


def _dmy(iso: str | None) -> str | None:
    if not iso or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", iso):
        return None
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


@dataclass(frozen=True)
class Plan:
    selected: list[MirrorRecord]
    skipped: list[Skip]


def plan(
    hits: Iterable[Mapping[str, Any]],
    *,
    case_number: str,
    held_official_urls: Iterable[str] = (),
) -> Plan:
    """Usable, not-yet-held records, one per official artifact URL, in mirror
    order. Byte-level duplicates are removed later, after hashing."""

    held = {official_key(u) for u in held_official_urls}
    seen: set[str] = set()
    selected: list[MirrorRecord] = []
    skipped: list[Skip] = []
    for hit in hits:
        parsed = parse_hit(hit, case_number=case_number)
        if isinstance(parsed, Skip):
            skipped.append(parsed)
            continue
        key = official_key(parsed.official_url)
        if key in held:
            skipped.append(Skip(parsed.slug, parsed.title, "already held (official URL)"))
            continue
        if key in seen:
            skipped.append(Skip(parsed.slug, parsed.title, "mirror duplicate (official URL)"))
            continue
        seen.add(key)
        selected.append(parsed)
    collision_counts: Counter[tuple[str | None, str]] = Counter(
        (record.date, record.language_code)
        for record in selected
        if record.is_transcript and record.date
    )
    safe: list[MirrorRecord] = []
    for record in selected:
        collision_key = (record.date, record.language_code)
        if record.is_transcript and collision_counts[collision_key] > 1:
            skipped.append(
                Skip(
                    record.slug,
                    record.title,
                    "same-date transcript identity collision (date-only key refused)",
                )
            )
        else:
            safe.append(record)
    return Plan(safe, skipped)


def pilot_category(record: MirrorRecord) -> str:
    """Research mix used only for pilot selection, never canonical attribution."""

    source = (record.mirror_source or "").strip().lower()
    if source == "defence":
        return "Defence"
    if source == "prosecution":
        return "SPO"
    if source == "trial chamber":
        return "Trial Chamber"
    if source == "appeals chamber":
        return "Appeals"
    if source == "registry":
        return "Registry"
    if source == "victim":
        return "Victims' Counsel"
    return "Other"


def select_pilot(records: Iterable[MirrorRecord], *, size: int = 100) -> list[MirrorRecord]:
    """Deterministic, stratified filing pilot with EN/SQ pairs preferred.

    The mirror category is used only to make a useful research sample. Canonical
    filing-party and court attribution remain blank until source-backed later.
    """

    if size < 1:
        raise ValueError("pilot size must be positive")
    eligible = [
        record
        for record in records
        if not record.is_transcript
        and published_document_id(record.external_id, record.case_number) is not None
    ]
    by_category: dict[str, list[MirrorRecord]] = {}
    for record in eligible:
        by_category.setdefault(pilot_category(record), []).append(record)

    quota_total = sum(quota for _, quota in PILOT_CATEGORY_QUOTAS)
    quotas = {
        category: (size * quota // quota_total) for category, quota in PILOT_CATEGORY_QUOTAS
    }
    for category, _ in PILOT_CATEGORY_QUOTAS:
        if sum(quotas.values()) >= size:
            break
        quotas[category] += 1

    selected: list[MirrorRecord] = []
    chosen: set[str] = set()
    for category, _ in PILOT_CATEGORY_QUOTAS:
        candidates = by_category.get(category, [])
        grouped: dict[str, list[MirrorRecord]] = {}
        for record in candidates:
            grouped.setdefault(record.external_id, []).append(record)
        groups = sorted(
            grouped.values(),
            key=lambda group: (
                -len({r.language_code for r in group}),
                min(r.date or "9999-99-99" for r in group),
                min(r.external_id for r in group),
            ),
        )
        target = quotas[category]
        for group in groups:
            ordered = sorted(group, key=lambda r: (r.language_code != "sqi", r.official_url))
            for record in ordered:
                if len([r for r in selected if pilot_category(r) == category]) >= target:
                    break
                if record.official_url not in chosen:
                    selected.append(record)
                    chosen.add(record.official_url)
            if len([r for r in selected if pilot_category(r) == category]) >= target:
                break

    if len(selected) < size:
        remainder = sorted(
            (r for r in eligible if r.official_url not in chosen),
            key=lambda r: (r.language_code != "sqi", r.date or "9999-99-99", r.official_url),
        )
        selected.extend(remainder[: size - len(selected)])
    return selected[:size]


def record_type_for(record: MirrorRecord) -> str:
    if record.is_transcript:
        return "Transcript"
    if _ANNEX_TITLE_RE.match(record.title) or any(
        _ANNEX_TOKEN_RE.match(t) for t in record.external_id.split("/")
    ):
        return "Filing Annex"
    return "Filing"


def source_entry(
    record: MirrorRecord, *, record_id: str, sha256: str, byte_size: int, permission: str
) -> dict[str, Any]:
    """The capture-v0 manifest record for a downloaded mirror PDF. The
    official PDF URL stands in for the detail page the mirror never saw."""

    transcript = record.is_transcript
    document_id = (
        None if transcript else published_document_id(record.external_id, record.case_number)
    )
    date = _dmy(record.date)
    return {
        "record_id": record_id,
        "case_number": record.case_number,
        "title": record.title,
        "document_id": document_id,
        "record_type": record_type_for(record),
        "filing_type": _FILING_TYPES.get((record.judicial_document_type or "").lower()),
        "filing_party": None,
        "court_level": None,
        "date": date,
        "language": {"code": record.language_code, "name": record.language_name},
        "public_status": public_status_for(document_id, record.title),
        "confidential_content_included": False,
        "detail_page_url": record.official_url,
        "pdf_url": record.official_url,
        "artifact_path": unquote(urlsplit(record.official_url).path),
        "local_file": f"files/{record_id}.pdf",
        "local_page_snapshot": f"pages/{record_id}.html",
        "sha256": sha256,
        "bytes": byte_size,
        "http_status_verified": 200,
        "selection_reason": f"Held by the {MIRROR_NAME} ({record.purl}); not yet held by the project",
        "hearing_date": date if transcript else None,
        "external_record_id": external_record_id(record.official_url),
        "mirror": {
            "name": MIRROR_NAME,
            "purl": record.purl,
            "slug": record.slug,
            "pdf_url": record.pdf_url,
            "external_id": record.external_id,
            "source": record.mirror_source,
            "judicial_document_type": record.judicial_document_type,
            "date_created": record.date,
            "permission": permission,
        },
    }


def snapshot_html(entry: Mapping[str, Any]) -> str:
    """A normalised snapshot (`snapshot.parse_snapshot` format) of the
    mirror's fields, so the importer can cross-check it like any capture."""

    from html import escape

    def cell(value: object) -> str:
        return escape(str(value)) if value not in (None, "") else "— (not published)"

    lang = entry["language"]
    rows = [
        ("Record ID", entry["record_id"]),
        ("Case Number", entry["case_number"]),
        ("Title", entry["title"]),
        ("Document / Filing ID", entry["document_id"]),
        ("Record Type", entry["record_type"]),
        ("Filing Type", entry["filing_type"]),
        ("Filing Party", entry["filing_party"]),
        ("Court Level", entry["court_level"]),
        ("Date", entry["date"]),
        ("Language", f"{lang['name']} ({lang['code']})"),
        ("Public / Redacted Status", entry["public_status"]),
        ("SHA-256", entry["sha256"]),
        ("Bytes", entry["bytes"]),
        ("Selection Reason", entry["selection_reason"]),
    ]
    table = "".join(f"<tr><th>{k}</th><td>{cell(v)}</td></tr>" for k, v in rows)
    url = escape(entry["pdf_url"])
    purl = escape(entry["mirror"]["purl"])
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f"<title>{escape(entry['record_id'])} — {cell(entry['document_id'])}</title></head>\n<body>\n"
        f"<h1>{escape(entry['title'])}</h1>\n<table>{table}</table>\n"
        f'<p class="src"><strong>Official detail page (not known to the mirror; official PDF)</strong> '
        f'<a href="{url}">{url}</a></p>\n'
        f'<p class="src"><strong>Official PDF</strong> <a href="{url}">{url}</a></p>\n'
        f'<p class="src">Normalised snapshot of the {MIRROR_NAME} record {purl}, written by '
        "scripts/ksc_legal_tools_harvest.py. Bytes from the mirror; official URL as the mirror "
        "recorded it (ADR-030).</p>\n</body></html>\n"
    )
