"""Import the operator's 2026-09-20 capture (`ksc_capture/`) into a project
capture bundle the pipeline understands.

Source layout (produced in the browser session; no bytes inside):

    manifest.json        22 records: published fields, official URLs, SHA-256, size
    pages/rNN.html       normalised snapshot per record (`snapshot.parse_snapshot`)
    files/sha256sums.txt capture-time hashes (no PDFs — the workspace could not write them)
    CAPTURE_NOTES.md     operator notes (documentation, not authority)

The PDFs were downloaded separately by the operator, in a normal browser, with
their original repository file names. This module

1. validates the source manifest and every snapshot against it;
2. finds each PDF by **exact SHA-256** among candidate files (never by name);
3. derives the official document / version references from the published
   filing id and confirms them against the reference the PDF prints in its own
   header — adopting the header's spelling where it is more specific (annexes),
   and flagging any contradiction as ambiguous instead of guessing;
4. writes `data/captures/<bundle-id>/` with `files/rNN.pdf` copies (hash
   re-verified after copy), the snapshots, the notes, the source manifest and a
   project `manifest.json` (`capture.CaptureManifest`) whose records carry
   `metadata_source = capture_snapshot`.

Nothing here touches the network and nothing alters the originals.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import re
import shutil
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from ksc_ingestion.normalize import parse_date
from ksc_ingestion.snapshot import SnapshotRecord, parse_snapshot
from ksc_ingestion.sources import CASE_NUMBER_PATTERN, CASE_NUMBER_RE, canonicalize, classify

log = logging.getLogger(__name__)

PUBLIC_STATUSES: dict[str, str] = {
    # published status → classification wording the pipeline derives visibility from
    "public": "Public",
    "public_redacted": "Public Redacted",
    "public_redacted_v2": "Public Redacted",
    "public_redacted_corrected": "Public Redacted",
}
_DOC_ID_RE = re.compile(r"^(?:(?P<ia>IA\d{3})-)?(?P<filing>F\d{5})(?P<suffix>[A-Z0-9]*)$")
_SUFFIX_TOKENS = ("COR", "RED2", "RED")
_ANNEX_RE = re.compile(r"^(?:ANNEX|SHTOJC[ËE])\s+(\d+)\b", re.IGNORECASE)
_HEADER_REF_RE = re.compile(rf"{CASE_NUMBER_PATTERN}(?:/[A-Za-z0-9]+)*")
# The classification line KSC filings print on page 1 (English / Albanian
# wording). Matched on a space-stripped copy because text layers split words
# ("Confidentia l"); the canonical phrase is what gets recorded.
_CLASSIFICATIONS: tuple[tuple[str, str], ...] = (
    ("strictlyconfidentialandexparte", "Strictly Confidential and Ex Parte"),
    ("strictlyconfidential", "Strictly Confidential"),
    ("confidentialandexparte", "Confidential and Ex Parte"),
    ("confidential", "Confidential"),
    ("public", "Public"),
    ("rreptësishtkonfidencialedheexparte", "Rreptësisht konfidenciale dhe ex parte"),
    ("rreptesishtkonfidencialedheexparte", "Rreptësisht konfidenciale dhe ex parte"),
    ("rreptësishtkonfidenciale", "Rreptësisht konfidenciale"),
    ("rreptesishtkonfidenciale", "Rreptësisht konfidenciale"),
    ("konfidencialedheexparte", "Konfidenciale dhe ex parte"),
    ("konfidenciale", "Konfidenciale"),
    ("konfidencial", "Konfidencial"),
    ("publike", "Publike"),
    ("publik", "Publik"),
)
_CLASSIFICATION_RE = re.compile(r"(?:classification|klasifikimi):([a-zë]+)")


def page1_classification(text: str) -> str | None:
    """Canonical classification phrase printed on page 1, or None."""

    compact = "".join(text.split()).lower()
    m = _CLASSIFICATION_RE.search(compact)
    if not m:
        return None
    tail = m.group(1)
    for key, label in _CLASSIFICATIONS:
        if tail.startswith(key):
            return label
    return None


_ORIGINAL_LANGUAGE = "eng"


class SourceImportError(ValueError):
    pass


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SourceLanguage(_Model):
    code: str
    name: str


class SourceRecordEntry(_Model):
    record_id: str = Field(pattern=r"^r\d{2}$")
    case_number: str
    title: str
    document_id: str | None
    record_type: str
    filing_type: str | None
    filing_party: str | None
    court_level: str | None
    date: str | None
    language: SourceLanguage
    public_status: str
    confidential_content_included: bool
    detail_page_url: str
    pdf_url: str
    artifact_path: str
    local_file: str
    local_page_snapshot: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bytes: int = Field(ge=1)
    http_status_verified: int
    selection_reason: str | None = None
    hearing_date: str | None = None


class SourceBundleInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    case_number: str
    capture_date: str
    capture_method: str
    record_count: int


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra="allow")
    bundle: SourceBundleInfo
    records: list[SourceRecordEntry]


MatchStatus = Literal["MATCHED", "MISSING", "HASH_MISMATCH", "DUPLICATE_HASH", "AMBIGUOUS"]


@dataclass
class MatchRow:
    record_id: str
    document_id: str | None
    title: str
    expected_sha256: str
    matched_local_pdf: str | None
    actual_sha256: str | None
    expected_bytes: int
    actual_bytes: int | None
    match_status: MatchStatus
    all_copies: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class References:
    document_ref: str | None
    version_ref: str | None
    version_type: str | None
    version_label: str | None
    candidate_ref: str | None
    ref_source: str
    header_refs: dict[str, int]
    status: Literal["ok", "ambiguous"]
    note: str | None = None


# ------------------------------------------------------------------ load --
def load_source(root: Path) -> tuple[SourceManifest, dict[str, SnapshotRecord]]:
    root = Path(root)
    try:
        manifest = SourceManifest.model_validate(
            json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        )
    except (OSError, ValueError) as exc:
        raise SourceImportError(f"source manifest unreadable or invalid: {exc}") from exc
    if len(manifest.records) != manifest.bundle.record_count:
        raise SourceImportError("record_count does not match the records list")
    problems: list[str] = []
    seen_ids: set[str] = set()
    seen_sha: dict[str, str] = {}
    snapshots: dict[str, SnapshotRecord] = {}
    for r in manifest.records:
        if r.record_id in seen_ids:
            problems.append(f"{r.record_id}: duplicate record id")
        seen_ids.add(r.record_id)
        if r.confidential_content_included:
            problems.append(f"{r.record_id}: confidential content flagged — refused")
        if r.public_status not in PUBLIC_STATUSES:
            problems.append(f"{r.record_id}: unknown public status {r.public_status!r}")
        if not CASE_NUMBER_RE.match(r.case_number) or r.case_number != manifest.bundle.case_number:
            problems.append(f"{r.record_id}: case number {r.case_number!r}")
        for url in (r.detail_page_url, r.pdf_url):
            try:
                classify(url)
            except ValueError as exc:
                problems.append(f"{r.record_id}: {exc}")
        if r.sha256 in seen_sha:
            problems.append(f"{r.record_id}: sha256 also declared by {seen_sha[r.sha256]}")
        seen_sha[r.sha256] = r.record_id
        snap_path = root / r.local_page_snapshot
        if not snap_path.is_file():
            problems.append(f"{r.record_id}: snapshot missing {r.local_page_snapshot}")
            continue
        snap = parse_snapshot(snap_path.read_bytes())
        snapshots[r.record_id] = snap
        problems.extend(f"{r.record_id}: {p}" for p in _cross_check(r, snap))
    sums_path = root / "files" / "sha256sums.txt"
    if sums_path.is_file():
        declared: dict[str, str] = {}
        for line in sums_path.read_text().splitlines():
            if line.strip():
                digest, name = line.split(maxsplit=1)
                declared[name.strip()] = digest
        for r in manifest.records:
            if declared.get(r.local_file, "").strip() != r.sha256:
                problems.append(f"{r.record_id}: sha256sums.txt disagrees with manifest")
    if problems:
        raise SourceImportError("; ".join(problems))
    return manifest, snapshots


def _cross_check(r: SourceRecordEntry, snap: SnapshotRecord) -> list[str]:
    pairs = [
        ("record_id", r.record_id, snap.record_id),
        ("case_number", r.case_number, snap.case_number),
        ("title", " ".join(r.title.split()), snap.title),
        ("document_id", r.document_id, snap.document_id),
        ("record_type", r.record_type, snap.record_type),
        ("filing_type", r.filing_type, snap.filing_type),
        ("filing_party", r.filing_party, snap.filing_party),
        ("court_level", r.court_level, snap.court_level),
        ("date", r.date, snap.date),
        ("language", r.language.code, snap.language_code),
        ("public_status", r.public_status, snap.public_status),
        ("sha256", r.sha256, snap.sha256),
        ("bytes", r.bytes, snap.byte_size),
        ("detail_page_url", canonicalize(r.detail_page_url), canonicalize(snap.detail_page_url)),
        ("pdf_url", r.pdf_url, snap.pdf_url),
    ]
    return [f"snapshot {name} {b!r} != manifest {a!r}" for name, a, b in pairs if a != b]


# ----------------------------------------------------------------- match --
def sha256_of(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def match_pdfs(
    manifest: SourceManifest, search_dirs: Iterable[Path], *, exclude: Iterable[Path] = ()
) -> list[MatchRow]:
    """Exact SHA-256 matching only. Names and sizes are diagnostics."""

    excluded = [Path(e).resolve() for e in exclude]
    by_hash: dict[str, list[tuple[Path, int]]] = {}
    for directory in search_dirs:
        for path in sorted(Path(directory).rglob("*.pdf")):
            resolved = path.resolve()
            if any(resolved == e or e in resolved.parents for e in excluded):
                continue
            try:
                digest, size = sha256_of(path)
            except OSError:
                continue
            by_hash.setdefault(digest, []).append((path, size))

    rows: list[MatchRow] = []
    claimed: dict[str, list[str]] = {}
    for r in manifest.records:
        hits = by_hash.get(r.sha256, [])
        if not hits:
            rows.append(
                MatchRow(
                    r.record_id,
                    r.document_id,
                    r.title,
                    r.sha256,
                    None,
                    None,
                    r.bytes,
                    None,
                    "MISSING",
                )
            )
            continue
        path, size = hits[0]
        status: MatchStatus = "MATCHED" if size == r.bytes else "HASH_MISMATCH"
        claimed.setdefault(r.sha256, []).append(r.record_id)
        rows.append(
            MatchRow(
                r.record_id,
                r.document_id,
                r.title,
                r.sha256,
                str(path),
                r.sha256,
                r.bytes,
                size,
                status,
                [str(p) for p, _ in hits],
            )
        )
    for digest, ids in claimed.items():
        if len(ids) > 1:
            for row in rows:
                if row.expected_sha256 == digest:
                    row.match_status = "DUPLICATE_HASH"
    return rows


# ------------------------------------------------------------ references --
def _split_suffix(suffix: str) -> list[str] | None:
    tokens: list[str] = []
    rest = suffix
    while rest:
        for token in _SUFFIX_TOKENS:
            if rest.startswith(token):
                tokens.append(token)
                rest = rest[len(token) :]
                break
        else:
            return None
    return tokens


@dataclass(frozen=True)
class HeaderInfo:
    """What the PDF says about itself: references printed in its running
    header / footer (with occurrence counts), the classification line on page
    1, the court's reclassification stamp on page 1 if any, and the page count.
    Validation metadata only — no body text is kept."""

    refs: dict[str, int]
    classification: str | None
    reclassification_note: str | None
    pages: int


_RECLASS_RE = re.compile(
    r"((?:PUBLIC\s+)?(?:Reclassified as Public|reclassified as Public|this filing is reclassified as)"
    r"[^.]{0,160}\.?)",
    re.IGNORECASE,
)


def pdf_header_references(data: bytes, case_number: str) -> HeaderInfo:
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        pages = len(reader.pages)
    except (PyPdfError, ValueError, KeyError, IndexError, TypeError):
        return HeaderInfo({}, None, None, 0)
    refs: Counter[str] = Counter()
    classification = None
    reclassification = None
    for index in range(pages):
        try:
            text = reader.pages[index].extract_text() or ""
        except (PyPdfError, ValueError, KeyError, IndexError, TypeError):
            continue
        for found in _HEADER_REF_RE.findall(text):
            parts = found.split("/")
            if len(parts) > 1 and parts[-1].isdigit():
                parts = parts[:-1]
            ref = "/".join(parts)
            if ref.startswith(case_number) and ref != case_number:
                refs[ref] += 1
        if index == 0:
            classification = page1_classification(text)
            flat = " ".join(text.split())
            m = _RECLASS_RE.search(flat)
            if m:
                reclassification = m.group(1).strip()
    return HeaderInfo(dict(refs), classification, reclassification, pages)


def derive_references(r: SourceRecordEntry, header: HeaderInfo) -> References:
    case = r.case_number
    lang = r.language.code.lower()
    header_refs = header.refs

    if r.record_type.lower() == "transcript":
        hearing = parse_date(r.hearing_date or r.date)
        if hearing is None:
            return References(
                None,
                None,
                None,
                None,
                None,
                "none",
                header_refs,
                "ambiguous",
                "transcript without a hearing date",
            )
        document_ref = f"{case}/T/{hearing.isoformat()}"
        version_ref = document_ref if lang == _ORIGINAL_LANGUAGE else f"{document_ref}/{lang}"
        return References(
            document_ref,
            version_ref,
            "original" if lang == _ORIGINAL_LANGUAGE else "translation",
            None if lang == _ORIGINAL_LANGUAGE else lang,
            version_ref,
            "derived_transcript_key",
            header_refs,
            "ok",
            "transcripts carry no filing number; key = case/T/<hearing date>[/<lang>]",
        )

    if not r.document_id:
        return References(
            None,
            None,
            None,
            None,
            None,
            "none",
            header_refs,
            "ambiguous",
            "no published document id",
        )
    m = _DOC_ID_RE.match(r.document_id)
    if not m:
        return References(
            None,
            None,
            None,
            None,
            None,
            "none",
            header_refs,
            "ambiguous",
            f"unrecognised document id {r.document_id!r}",
        )
    suffix_tokens = _split_suffix(m.group("suffix"))
    if suffix_tokens is None:
        return References(
            None,
            None,
            None,
            None,
            None,
            "none",
            header_refs,
            "ambiguous",
            f"unrecognised suffix in {r.document_id!r}",
        )

    base = [case] + ([m.group("ia")] if m.group("ia") else []) + [m.group("filing")]
    annex: str | None = None
    if r.record_type.lower() == "filing annex":
        am = _ANNEX_RE.match(r.title)
        if not am:
            return References(
                None,
                None,
                None,
                None,
                None,
                "none",
                header_refs,
                "ambiguous",
                "annex without an annex number in its title",
            )
        annex = f"A{int(am.group(1)):02d}"
    document_ref = "/".join(base + ([annex] if annex else []))
    candidate = "/".join(base + suffix_tokens + ([annex] if annex else []))
    candidate_lang = candidate if lang == _ORIGINAL_LANGUAGE else f"{candidate}/{lang}"

    filing_refs = {ref: n for ref, n in header_refs.items() if m.group("filing") in ref.split("/")}
    version_ref = candidate_lang
    source = "derived_from_published_id"
    note = None
    if filing_refs:
        best = max(filing_refs, key=lambda k: (filing_refs[k], len(k)))
        if best == candidate_lang:
            source = "published_id_confirmed_by_pdf_header"
        elif best.startswith(candidate) and (
            lang == _ORIGINAL_LANGUAGE or best.endswith(f"/{lang}")
        ):
            version_ref, source = best, "pdf_header"
            note = f"header reference {best!r} extends published id {r.document_id!r}"
        else:
            return References(
                document_ref,
                None,
                None,
                None,
                candidate_lang,
                "conflict",
                header_refs,
                "ambiguous",
                f"pdf header {best!r} contradicts published id {r.document_id!r}",
            )

    if lang != _ORIGINAL_LANGUAGE:
        vtype = "translation"
    elif r.public_status.startswith("public_redacted") or any(
        t.startswith("RED") for t in suffix_tokens
    ):
        vtype = "public_redacted"
    elif "COR" in suffix_tokens:
        vtype = "corrected"
    elif header.reclassification_note:
        # The court's own page-1 stamp says the filing was reclassified as public.
        vtype = "reclassified"
    else:
        vtype = "original"
    label = (
        version_ref[len(document_ref) + 1 :]
        if version_ref.startswith(document_ref + "/")
        else ("/".join(suffix_tokens) or None)
    )
    return References(
        document_ref, version_ref, vtype, label, candidate_lang, source, header_refs, "ok", note
    )


# ----------------------------------------------------------------- write --
def _document_type(r: SourceRecordEntry) -> str:
    text = (r.filing_type or r.record_type).lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def import_capture(
    source_root: Path,
    dest_root: Path,
    *,
    pdf_dirs: Iterable[Path],
    bundle_id: str,
    captured_by: str,
    browser: str | None,
) -> dict[str, Any]:
    """Validate, match, derive, copy, write. Returns the import report (also
    written to `<dest>/import_report.json`). Raises SourceImportError when any
    record is MISSING / HASH_MISMATCH / DUPLICATE_HASH — nothing is written then."""

    source_root, dest_root = Path(source_root), Path(dest_root)
    manifest, snapshots = load_source(source_root)
    # A capture may carry its PDFs inside its own files/ directory (the
    # browser collector does); only the destination's copies are excluded.
    rows = match_pdfs(manifest, pdf_dirs, exclude=[dest_root])
    bad = [row for row in rows if row.match_status != "MATCHED"]
    if bad:
        raise SourceImportError(
            "pdf matching incomplete: "
            + "; ".join(f"{row.record_id}: {row.match_status}" for row in bad)
        )

    dest_root.mkdir(parents=True, exist_ok=True)
    (dest_root / "pages").mkdir(exist_ok=True)
    (dest_root / "files").mkdir(exist_ok=True)
    shutil.copy2(source_root / "manifest.json", dest_root / "source_manifest.json")
    if (source_root / "CAPTURE_NOTES.md").is_file():
        shutil.copy2(source_root / "CAPTURE_NOTES.md", dest_root / "CAPTURE_NOTES.md")

    captured_at = datetime.fromisoformat(manifest.bundle.capture_date).replace(tzinfo=UTC)
    by_id = {row.record_id: row for row in rows}
    records: list[dict[str, Any]] = []
    report_records: list[dict[str, Any]] = []
    sums_lines: list[str] = []

    for r in manifest.records:
        row = by_id[r.record_id]
        assert row.matched_local_pdf is not None
        src_pdf = Path(row.matched_local_pdf)
        data = src_pdf.read_bytes()
        dest_pdf = dest_root / "files" / f"{r.record_id}.pdf"
        dest_pdf.write_bytes(data)
        digest, size = sha256_of(dest_pdf)
        if digest != r.sha256 or size != r.bytes:
            raise SourceImportError(f"{r.record_id}: copy verification failed")
        sums_lines.append(f"{digest}  files/{r.record_id}.pdf")
        shutil.copy2(
            source_root / r.local_page_snapshot, dest_root / "pages" / f"{r.record_id}.html"
        )

        header = pdf_header_references(data, r.case_number)
        refs = derive_references(r, header)
        snap = snapshots[r.record_id]
        hearing = None
        if r.record_type.lower() == "transcript" and refs.status == "ok":
            hd = parse_date(r.hearing_date or r.date)
            assert hd is not None
            hearing = {
                "date": hd.isoformat(),
                "session_sequence": 1,
                "session_label": r.title,
            }
        extra: dict[str, Any] = {
            "source_record_id": r.record_id,
            "published_document_id": r.document_id,
            "published_record_type": r.record_type,
            "published_filing_type": r.filing_type,
            "published_court_level": r.court_level,
            "published_public_status": r.public_status,
            "published_date": r.date,
            "published_language": r.language.model_dump(),
            "original_download_filename": src_pdf.name,
            "capture_time_http_status": r.http_status_verified,
            "reference": {
                "status": refs.status,
                "source": refs.ref_source,
                "candidate": refs.candidate_ref,
                "adopted": refs.version_ref,
                "pdf_header_refs": header.refs,
                "note": refs.note,
            },
            "pdf_page_count": header.pages,
            "page1_classification_text": header.classification,
            "page1_reclassification_stamp": header.reclassification_note,
            "snapshot_footer": snap.footer_note,
        }
        if hearing:
            extra["hearing_session_sequence_assumed"] = True
        metadata: dict[str, Any] = {
            "metadata_source": "capture_snapshot",
            "record_type": _document_type(r),
            "official_ref": refs.document_ref or "",
            "title": " ".join(r.title.split()),
            "case_number": r.case_number,
            "language": r.language.code,
            "filing_party_label": r.filing_party,
            "document_date": r.date,
            "classification": PUBLIC_STATUSES[r.public_status],
            "extra": extra,
        }
        if hearing:
            metadata["hearing"] = hearing
        artifact: dict[str, Any] = {
            "url": r.pdf_url,
            "file": f"files/{r.record_id}.pdf",
            "language": r.language.code,
            "classification": PUBLIC_STATUSES[r.public_status],
            "sha256": r.sha256,
            "byte_size": r.bytes,
        }
        if refs.status == "ok":
            artifact["official_version_ref"] = refs.version_ref
            artifact["version_type"] = refs.version_type
            if refs.version_label:
                artifact["version_label"] = refs.version_label
        records.append(
            {
                "detail_page_url": r.detail_page_url,
                "detail_page_file": f"pages/{r.record_id}.html",
                "artifacts": [artifact],
                "selection_reason": r.selection_reason,
                "metadata": metadata,
            }
        )
        report_records.append(
            {
                **asdict(row),
                "document_ref": refs.document_ref,
                "version_ref": refs.version_ref,
                "version_type": refs.version_type,
                "ref_source": refs.ref_source,
                "ref_status": refs.status,
                "ref_note": refs.note,
                "pdf_page_count": header.pages,
                "page1_classification_text": header.classification,
                "page1_reclassification_stamp": header.reclassification_note,
            }
        )

    project_manifest = {
        "bundle_id": bundle_id,
        "case_number": manifest.bundle.case_number,
        "captured_by": captured_by,
        "captured_at": captured_at.isoformat(),
        "capture_method": manifest.bundle.capture_method,
        "browser": browser,
        "listing_pages": [],
        "records": records,
    }
    (dest_root / "manifest.json").write_text(
        json.dumps(project_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (dest_root / "files" / "sha256sums.txt").write_text("\n".join(sums_lines) + "\n")
    report = {
        "imported_at": datetime.now(UTC).isoformat(),
        "source": str(source_root),
        "dest": str(dest_root),
        "records": report_records,
        "matched": sum(1 for row in rows if row.match_status == "MATCHED"),
        "total": len(rows),
    }
    (dest_root / "import_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report
