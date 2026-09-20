"""Deterministic native-text parsing for held public KSC PDFs.

The parser never manufactures source coordinates. ``pdf_page_index`` is the
zero-based position in the held artifact. ``page_number`` is populated only
when a printed filing/transcript header is present. Numbered paragraphs and
transcript lines likewise come only from explicit text in the PDF layer.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

from pypdf import PdfReader

PARSER_NAME = "ksc-native-pdf"
PARSER_VERSION = "2"

_FILING_PAGE_RE = re.compile(
    r"(?m)^\s*KSC-(?:[A-Z]+-\d{4}-\d{2}|DEMO-\d{4})/.+?/(\d+)\s+of\s+(\d+)\b"
)
_TRANSCRIPT_PAGE_RE = re.compile(r"(?im)\b(Page|Faqe)\s+([0-9][0-9 ]*)\s*$")
_LINE_RE = re.compile(r"^\s*(\d{1,2})\s+(\S.*)$")
_PARAGRAPH_RE = re.compile(r"^\s*(\d{1,4})\.\s+(\S.*)$")
_REDACTION_RE = re.compile(r"\[(?:PUBLIC\s+)?REDACTED(?:\s+CONTENT)?\]", re.IGNORECASE)
_SECTION_RE = re.compile(r"^\s*((?:[IVXLCDM]+|[A-Z])\.)\s+([A-Z][A-Z0-9 ,&()'\u2019:/\-]{2,})\s*$")


@dataclass(frozen=True)
class ParsedPage:
    pdf_page_index: int
    page_number: int | None
    printed_page_label: str | None
    text: str
    running_head: str | None
    has_redactions: bool
    redaction_extents: list[dict[str, str]] | None


@dataclass(frozen=True)
class ParsedParagraph:
    sequence: int
    paragraph_number: int
    pdf_page_index_from: int
    pdf_page_index_to: int
    page_from: int | None
    page_to: int | None
    text: str


@dataclass(frozen=True)
class ParsedSection:
    sequence: int
    level: int
    heading: str
    page_from: int | None
    page_to: int | None
    para_from: int | None
    para_to: int | None


@dataclass(frozen=True)
class ParsedChunk:
    sequence: int
    chunk_kind: str
    pdf_page_index_from: int | None
    pdf_page_index_to: int | None
    page_from: int | None
    page_to: int | None
    para_from: int | None
    para_to: int | None
    text: str


@dataclass(frozen=True)
class ParsedTranscriptSegment:
    sequence: int
    pdf_page_index: int
    page_number: int
    line_from: int
    line_to: int
    speaker: str | None
    speaker_role: str | None
    examination_type: str
    text: str
    closed_session: bool


@dataclass(frozen=True)
class ParsedPdf:
    pages: list[ParsedPage]
    paragraphs: list[ParsedParagraph]
    sections: list[ParsedSection]
    chunks: list[ParsedChunk]
    transcript_segments: list[ParsedTranscriptSegment] = field(default_factory=list)
    page_from: int | None = None
    page_to: int | None = None
    requires_review: bool = False
    review_reasons: list[str] = field(default_factory=list)


@dataclass
class _OpenParagraph:
    number: int
    pdf_from: int
    pdf_to: int
    page_from: int | None
    page_to: int | None
    parts: list[str]


def _page_coordinate(text: str, *, transcript: bool) -> tuple[int | None, str | None]:
    if transcript:
        match = _TRANSCRIPT_PAGE_RE.search(text)
        if match is None:
            return None, None
        label = f"{match.group(1)} {match.group(2).strip()}"
        return int(match.group(2).replace(" ", "")), label
    match = _FILING_PAGE_RE.search(text)
    if match is None:
        return None, None
    return int(match.group(1)), f"{match.group(1)} of {match.group(2)}"


def _running_head(text: str) -> str | None:
    for line in text.splitlines()[:8]:
        compact = " ".join(line.split())
        if compact.startswith("KSC-") or compact == "KSC-OFFICIAL":
            return compact[:512]
    return None


def _speaker_parts(body: str) -> tuple[str | None, str]:
    label, separator, rest = body.partition(":")
    candidate = " ".join(label.split())
    if not separator or not candidate or len(candidate) > 96:
        return None, body.strip()
    letters = "".join(char for char in candidate if char.isalpha())
    if not letters or letters.upper() != letters:
        return None, body.strip()
    return candidate, rest.strip()


def _speaker_role(speaker: str | None) -> str | None:
    if speaker is None:
        return None
    upper = speaker.upper()
    if "JUDGE" in upper or "TRUPIT GJYKUES" in upper:
        return "court"
    if "COURT OFFICER" in upper or "SEKRETARI I GJYKAT" in upper:
        return "court_officer"
    if "WITNESS" in upper or "DËSHMITAR" in upper:
        return "witness"
    if upper in {"SPO", "PROSECUTION"}:
        return "spo"
    if "DEFENCE" in upper or "MBROJT" in upper:
        return "defence"
    if "VICTIMS' COUNSEL" in upper or "VICTIMS\N{RIGHT SINGLE QUOTATION MARK} COUNSEL" in upper:
        return "victims_counsel"
    return None


def _examination_type(text: str) -> str:
    lower = text.casefold()
    if "cross-examination" in lower or "cross examination" in lower:
        return "cross"
    if "re-examination" in lower or "redirect examination" in lower:
        return "redirect"
    if "examination by" in lower:
        return "direct"
    return "unknown"


def _transcript_segments(
    pages: list[ParsedPage],
) -> tuple[list[ParsedTranscriptSegment], list[str]]:
    segments: list[ParsedTranscriptSegment] = []
    reasons: list[str] = []
    sequence = 0
    closed_session = False
    examination = "unknown"

    for page in pages:
        if page.page_number is None:
            reasons.append(f"pdf page {page.pdf_page_index}: no printed transcript page")
            continue
        printed_page_number = page.page_number
        numbered: list[tuple[int, str]] = []
        for raw_line in page.text.splitlines():
            match = _LINE_RE.match(raw_line)
            if match is not None:
                numbered.append((int(match.group(1)), match.group(2).rstrip()))
        if not numbered:
            reasons.append(f"pdf page {page.pdf_page_index}: no transcript lines")
            continue
        if len({line for line, _ in numbered}) != len(numbered):
            reasons.append(f"pdf page {page.pdf_page_index}: duplicate transcript line number")

        current_speaker: str | None = None
        current_role: str | None = None
        group_from: int | None = None
        group_to: int | None = None
        group_parts: list[str] = []
        group_closed = closed_session
        group_exam = examination

        def flush(
            pdf_page_index_value: int,
            page_number_value: int,
            speaker_value: str | None,
            role_value: str | None,
            exam_value: str,
            closed_value: bool,
        ) -> None:
            nonlocal sequence, group_from, group_to, group_parts
            if group_from is None or group_to is None:
                return
            text = " ".join(part for part in group_parts if part).strip()
            segments.append(
                ParsedTranscriptSegment(
                    sequence=sequence,
                    pdf_page_index=pdf_page_index_value,
                    page_number=page_number_value,
                    line_from=group_from,
                    line_to=group_to,
                    speaker=speaker_value,
                    speaker_role=role_value,
                    examination_type=exam_value,
                    text="" if closed_value else text,
                    closed_session=closed_value,
                )
            )
            sequence += 1
            group_from = None
            group_to = None
            group_parts = []

        for line_number, body in numbered:
            lower = body.casefold()
            next_closed = closed_session
            if "[closed session" in lower or "[private session" in lower:
                next_closed = True
            elif "[open session" in lower:
                next_closed = False
            next_exam = _examination_type(body)
            if next_exam == "unknown":
                next_exam = examination
            speaker, spoken = _speaker_parts(body)
            starts_group = (
                group_from is None
                or speaker is not None
                or next_closed != group_closed
                or next_exam != group_exam
                or (group_to is not None and line_number != group_to + 1)
            )
            if starts_group:
                flush(
                    page.pdf_page_index,
                    printed_page_number,
                    current_speaker,
                    current_role,
                    group_exam,
                    group_closed,
                )
                if speaker is not None:
                    current_speaker = speaker
                    current_role = _speaker_role(speaker)
                elif group_from is None:
                    # A continuation at the top of a PDF page has no explicit
                    # speaker on this page. Do not carry one across the page.
                    current_speaker = None
                    current_role = None
                group_from = line_number
                group_closed = next_closed
                group_exam = next_exam
            group_to = line_number
            group_parts.append(spoken if speaker is not None else body.strip())
            closed_session = next_closed
            examination = next_exam
        flush(
            page.pdf_page_index,
            printed_page_number,
            current_speaker,
            current_role,
            group_exam,
            group_closed,
        )
    return segments, reasons


def _paragraphs_and_sections(
    pages: list[ParsedPage],
) -> tuple[list[ParsedParagraph], list[ParsedSection]]:
    paragraphs: list[ParsedParagraph] = []
    sections: list[ParsedSection] = []
    current: _OpenParagraph | None = None
    seen: set[int] = set()

    def flush() -> None:
        nonlocal current
        if current is None:
            return
        text = " ".join(" ".join(current.parts).split())
        if text:
            paragraphs.append(
                ParsedParagraph(
                    sequence=len(paragraphs),
                    paragraph_number=current.number,
                    pdf_page_index_from=current.pdf_from,
                    pdf_page_index_to=current.pdf_to,
                    page_from=current.page_from,
                    page_to=current.page_to,
                    text=text,
                )
            )
        current = None

    for page in pages:
        for raw_line in page.text.splitlines():
            compact = " ".join(raw_line.split())
            if not compact:
                continue
            if " of " in compact and compact.startswith("KSC-"):
                continue
            section_match = _SECTION_RE.match(compact)
            if section_match is not None:
                sections.append(
                    ParsedSection(
                        sequence=len(sections),
                        level=0 if section_match.group(1)[0] in "IVXLCDM" else 1,
                        heading=f"{section_match.group(1)} {section_match.group(2)}",
                        page_from=page.page_number,
                        page_to=page.page_number,
                        para_from=None,
                        para_to=None,
                    )
                )
            match = _PARAGRAPH_RE.match(raw_line)
            if match is not None:
                number = int(match.group(1))
                # Numbered legal paragraphs are unique and advance through the
                # artifact. Dot-leader entries are table-of-contents rows, not
                # legal paragraphs; a repeated list/footnote number is not
                # relabelled as a paragraph.
                is_contents_row = "....." in raw_line
                if not is_contents_row and number not in seen and (not seen or number > max(seen)):
                    flush()
                    seen.add(number)
                    current = _OpenParagraph(
                        number=number,
                        pdf_from=page.pdf_page_index,
                        pdf_to=page.pdf_page_index,
                        page_from=page.page_number,
                        page_to=page.page_number,
                        parts=[match.group(2)],
                    )
                    continue
            if current is not None:
                current.pdf_to = page.pdf_page_index
                current.page_to = page.page_number
                current.parts.append(compact)
    flush()

    for index, section in enumerate(sections):
        next_page = sections[index + 1].page_from if index + 1 < len(sections) else None
        in_section = [
            paragraph
            for paragraph in paragraphs
            if section.page_from is not None
            and paragraph.page_from is not None
            and paragraph.page_from >= section.page_from
            and (next_page is None or paragraph.page_from < next_page)
        ]
        if in_section:
            sections[index] = ParsedSection(
                sequence=section.sequence,
                level=section.level,
                heading=section.heading,
                page_from=section.page_from,
                page_to=in_section[-1].page_to,
                para_from=in_section[0].paragraph_number,
                para_to=in_section[-1].paragraph_number,
            )
    return paragraphs, sections


def parse_pdf(data: bytes, *, transcript: bool) -> ParsedPdf:
    reader = PdfReader(io.BytesIO(data))
    pages: list[ParsedPage] = []
    reasons: list[str] = []
    for pdf_page_index, source_page in enumerate(reader.pages):
        text = source_page.extract_text(extraction_mode="layout") or ""
        page_number, label = _page_coordinate(text, transcript=transcript)
        if page_number is None:
            reasons.append(f"pdf page {pdf_page_index}: printed page not found")
        redactions = [
            {"kind": "explicit_marker", "marker": match.group(0)}
            for match in _REDACTION_RE.finditer(text)
        ]
        pages.append(
            ParsedPage(
                pdf_page_index=pdf_page_index,
                page_number=page_number,
                printed_page_label=label,
                text=text,
                running_head=_running_head(text),
                has_redactions=bool(redactions),
                redaction_extents=redactions or None,
            )
        )

    if transcript:
        segments, transcript_reasons = _transcript_segments(pages)
        reasons.extend(transcript_reasons)
        transcript_chunks = [
            ParsedChunk(
                sequence=index,
                chunk_kind="transcript_page",
                pdf_page_index_from=page.pdf_page_index,
                pdf_page_index_to=page.pdf_page_index,
                page_from=page.page_number,
                page_to=page.page_number,
                para_from=None,
                para_to=None,
                text=" ".join(
                    segment.text
                    for segment in segments
                    if segment.pdf_page_index == page.pdf_page_index and not segment.closed_session
                ),
            )
            for index, page in enumerate(pages)
        ]
        known_pages = [page.page_number for page in pages if page.page_number is not None]
        return ParsedPdf(
            pages=pages,
            paragraphs=[],
            sections=[],
            chunks=transcript_chunks,
            transcript_segments=segments,
            page_from=min(known_pages) if known_pages else None,
            page_to=max(known_pages) if known_pages else None,
            requires_review=bool(reasons),
            review_reasons=reasons,
        )

    paragraphs, sections = _paragraphs_and_sections(pages)
    covered_pages = {
        page_index
        for paragraph in paragraphs
        for page_index in range(paragraph.pdf_page_index_from, paragraph.pdf_page_index_to + 1)
    }
    chunks: list[ParsedChunk] = []
    for paragraph in paragraphs:
        chunks.append(
            ParsedChunk(
                sequence=len(chunks),
                chunk_kind="paragraph",
                pdf_page_index_from=paragraph.pdf_page_index_from,
                pdf_page_index_to=paragraph.pdf_page_index_to,
                page_from=paragraph.page_from,
                page_to=paragraph.page_to,
                para_from=paragraph.paragraph_number,
                para_to=paragraph.paragraph_number,
                text=paragraph.text,
            )
        )
    for page in pages:
        if page.pdf_page_index not in covered_pages and page.text.strip():
            chunks.append(
                ParsedChunk(
                    sequence=len(chunks),
                    chunk_kind="page",
                    pdf_page_index_from=page.pdf_page_index,
                    pdf_page_index_to=page.pdf_page_index,
                    page_from=page.page_number,
                    page_to=page.page_number,
                    para_from=None,
                    para_to=None,
                    text=page.text,
                )
            )
    return ParsedPdf(
        pages=pages,
        paragraphs=paragraphs,
        sections=sections,
        chunks=chunks,
        requires_review=bool(reasons),
        review_reasons=reasons,
    )
