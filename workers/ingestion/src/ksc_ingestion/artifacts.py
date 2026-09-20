"""Artifact bytes: hashing, type sniffing and PDF validation.

Validation only. `inspect_pdf` reads the page count and looks for the case
number on the first page so the quality gate can confirm "correct case" —
it does not extract, segment or store text (that is Phase 8). Nothing here
touches redacted content in any special way; a redaction is just page
content that stays as published.
"""

from __future__ import annotations

import hashlib
import io
import logging
import re
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from ksc_ingestion.sources import CASE_NUMBER_PATTERN

log = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"
_CASE_NUMBER_RE = re.compile(CASE_NUMBER_PATTERN)


class UnsupportedArtifactError(ValueError):
    """The bytes are not a PDF we can hold as a court record artifact."""


@dataclass(frozen=True)
class ArtifactInfo:
    sha256: str
    byte_size: int
    mime_type: str
    page_count: int | None
    # Case numbers found on the first page, if the PDF has a text layer.
    case_numbers_on_first_page: tuple[str, ...]
    has_text_layer: bool | None


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sniff_mime(data: bytes) -> str | None:
    if data.startswith(PDF_MAGIC):
        return "application/pdf"
    return None


def inspect_pdf(data: bytes) -> tuple[int | None, tuple[str, ...], bool | None]:
    """(page_count, case numbers on first page, has_text_layer). A damaged
    PDF yields (None, (), None) and a warning — the caller decides."""

    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        page_count = len(reader.pages)
    except (PyPdfError, ValueError, KeyError, IndexError, TypeError) as exc:
        log.warning("pdf unreadable: %s", type(exc).__name__)
        return None, (), None
    if page_count == 0:
        return 0, (), None
    try:
        text = reader.pages[0].extract_text() or ""
    except (PyPdfError, ValueError, KeyError, IndexError, TypeError) as exc:
        log.warning("pdf first-page text unavailable: %s", type(exc).__name__)
        return page_count, (), None
    found = tuple(dict.fromkeys(_CASE_NUMBER_RE.findall(text)))
    return page_count, found, bool(text.strip())


def inspect(data: bytes) -> ArtifactInfo:
    """Hash and validate. Raises UnsupportedArtifactError for non-PDF bytes."""

    if not data:
        raise UnsupportedArtifactError("empty file")
    mime = sniff_mime(data)
    if mime != "application/pdf":
        raise UnsupportedArtifactError("not a PDF (magic bytes)")
    page_count, case_numbers, has_text = inspect_pdf(data)
    if page_count is None:
        raise UnsupportedArtifactError("PDF structure unreadable")
    return ArtifactInfo(
        sha256=sha256_hex(data),
        byte_size=len(data),
        mime_type=mime,
        page_count=page_count,
        case_numbers_on_first_page=case_numbers,
        has_text_layer=has_text,
    )
