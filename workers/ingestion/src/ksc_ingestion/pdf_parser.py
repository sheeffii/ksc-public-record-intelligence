"""Deterministic native-text parsing for held public KSC PDFs.

The parser never manufactures source coordinates. ``pdf_page_index`` is the
zero-based position in the held artifact. ``page_number`` is populated only
when a printed filing/transcript header is present. Numbered paragraphs and
transcript lines likewise come only from explicit text in the PDF layer.
"""

from __future__ import annotations

import io
import re
from collections import Counter
from dataclasses import dataclass, field, replace

from pypdf import PdfReader

PARSER_NAME = "ksc-native-pdf"
PARSER_VERSION = "4"

_FILING_PAGE_RE = re.compile(
    r"(?m)^\s*KSC-(?:[A-Z]+-\d{4}-\d{2}|DEMO-\d{4})/.+?/(\d+)\s+of\s+(\d+)\b"
)
_TRANSCRIPT_PAGE_RE = re.compile(r"(?im)\b(Page|Faqe)\s+([0-9][0-9 ]*)\s*$")
_LINE_RE = re.compile(r"^\s*(\d{1,2})\s+(\S.*)$")
_BARE_LINE_RE = re.compile(r"^\s*(\d{1,2})\s*$")
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


def _blank_line_grid(text: str) -> bool:
    """True when the page's numbered lines are exactly 1..N, all empty."""

    numbers = [
        int(match.group(1))
        for match in (_BARE_LINE_RE.match(line) for line in text.splitlines())
        if match is not None
    ]
    return bool(numbers) and numbers == list(range(1, len(numbers) + 1))


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
            # A private-session page prints its full line grid (1..N) with no
            # text: structurally complete, nothing to segment, nothing to review.
            if not _blank_line_grid(page.text):
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


# A numbered legal paragraph continues onto the next page, but never across
# dozens: beyond this many PDF pages it is closed and the version is flagged.
MAX_PARAGRAPH_PAGES = 5
# Visible paragraph numbers advance by one; a small gap tolerates a number the
# text layer does not carry. A larger jump is a wrapped footnote reference
# ("…infra paras 169, 271, 359.") and never opens a paragraph.
_MAX_PARAGRAPH_STEP = 3
_MAX_FIRST_PARAGRAPH = 5
_FOOTNOTE_START_RE = re.compile(r"^\s*(\d{1,4})\s+(\S.*)$")
_HEADER_FURNITURE_RE = re.compile(
    r"^(?:KSC-\S+/\d+\s+of\s+\d+\b.*|PUBLIC|PUBLIKE?|"
    r"Date (?:original|public redacted version|public redacted|public)\b.*|"
    r"Data (?:origjinale|e versionit publik)\b.*)$",
    re.IGNORECASE,
)
_FOOTER_FURNITURE_RE = re.compile(r"^KSC-[A-Z]{2,6}-\d{4}(?:-\d{2})?\s+\d{1,4}\s+\S.*\d{4}$")


@dataclass(frozen=True)
class _Block:
    """A page-local run of text: part of a numbered paragraph, unnumbered body
    text, or the page's footnotes. Chunks are built from blocks, so no chunk
    ever holds text from another page."""

    pdf_page_index: int
    page_number: int | None
    paragraph_number: int | None
    kind: str  # "paragraph" | "body" | "footnotes"
    text: str


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_furniture(compact: str) -> bool:
    return bool(_HEADER_FURNITURE_RE.match(compact) or _FOOTER_FURNITURE_RE.match(compact))


# A superscript footnote reference as the text layer renders it: glued to the
# preceding word or punctuation ("Law1", "[REDACTED].46", "2025,10"). Hyphens,
# slashes and leading zeros belong to identifiers (KSC-BC-2020-06, F00026).
_GLUED_REFERENCE_RE = re.compile(r"(?<=[^\s\d\-/])([1-9]\d{0,3})(?!\d)")


def _footnote_start(lines: list[str]) -> int | None:
    """Index of the page's first footnote line, or None. It must carry the
    number of the first footnote reference in the body above it, and no
    numbered paragraph may follow it — a wrapped body line that happens to
    start with a number never ends the body."""

    for index, line in enumerate(lines):
        if index == 0:
            continue
        match = _FOOTNOTE_START_RE.match(" ".join(line.split()))
        if match is None:
            continue
        references = _GLUED_REFERENCE_RE.findall(" ".join(lines[:index]))
        if not references or int(match.group(1)) != int(references[0]):
            continue
        if any(_PARAGRAPH_RE.match(later) for later in lines[index:]):
            continue
        return index
    return None


_SUBHEADING_RE = re.compile(r"^\s*\([a-z]{1,4}\)\s+[A-Z]")
_SENTENCE_END_RE = re.compile(r"[.;:,)\]\"\u2019\u201d\d]$")


def _is_numbered_heading(
    raw_line: str,
    rest: str,
    following: str | None,
    after: str | None,
    base: int,
    full_width: int,
) -> bool:
    """A numbered heading is a title-case line that ends well before the right
    edge of the page's justified text (a paragraph's first line runs to that
    edge, even with a hanging indent), has no sentence-ending punctuation, and
    is followed by an indented paragraph start or a lettered sub-heading."""
    title = " ".join(rest.split())
    words = [word for word in re.findall(r"[^\W\d_][\w\-]*", title) if len(word) >= 4]
    title_case = bool(words) and sum(word[0].isupper() for word in words) / len(words) >= 0.6
    return (
        title_case
        and len(raw_line.rstrip()) < 0.85 * full_width
        and _SENTENCE_END_RE.search(title) is None
        and following is not None
        and (
            _SUBHEADING_RE.match(following) is not None
            # The next line opens a paragraph: indented, with the line after it
            # back at the body margin (a hanging indent keeps every line indented).
            or (_indent(following) >= base + 3 and after is not None and _indent(after) <= base + 1)
        )
    )


def _paragraphs_and_sections(
    pages: list[ParsedPage],
) -> tuple[list[ParsedParagraph], list[ParsedSection], list[_Block], list[str]]:
    paragraphs: list[ParsedParagraph] = []
    sections: list[ParsedSection] = []
    blocks: list[_Block] = []
    reasons: list[str] = []
    current: _OpenParagraph | None = None
    last_number: int | None = None

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

    def emit(page: ParsedPage, number: int | None, parts: list[str]) -> None:
        text = " ".join(" ".join(parts).split())
        if text:
            blocks.append(
                _Block(
                    page.pdf_page_index,
                    page.page_number,
                    number,
                    "paragraph" if number is not None else "body",
                    text,
                )
            )

    for page in pages:
        lines = [line for line in page.text.splitlines() if line.strip()]
        lines = [line for line in lines if not _is_furniture(" ".join(line.split()))]
        # The body margin is the most common indent of full lines (footnotes
        # and quotes sit elsewhere); ties resolve to the smaller indent.
        margins = Counter(_indent(line) for line in lines if len(line.strip()) >= 30)
        base = min(margins, key=lambda indent: (-margins[indent], indent)) if margins else 0
        # Right edge of justified body text, in layout columns: the most common
        # end column of full lines (wide headers and tables sit elsewhere).
        ends = Counter(len(line.rstrip()) for line in lines if len(line.strip()) >= 30)
        full_width = min(ends, key=lambda end: (-ends[end], -end)) if ends else 0
        footnotes_at = _footnote_start(lines)
        body_lines = lines if footnotes_at is None else lines[:footnotes_at]
        footnote_lines = [] if footnotes_at is None else lines[footnotes_at:]

        run: list[str] = []
        run_number: int | None = None

        if current is not None and page.pdf_page_index - current.pdf_from + 1 > MAX_PARAGRAPH_PAGES:
            reasons.append(
                f"paragraph {current.number} would exceed {MAX_PARAGRAPH_PAGES} pages; "
                f"closed at pdf page {current.pdf_to}"
            )
            flush()
        run_number = current.number if current is not None else None

        for position, raw_line in enumerate(body_lines):
            compact = " ".join(raw_line.split())
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
            following = body_lines[position + 1] if position + 1 < len(body_lines) else None
            if match is not None and _is_numbered_heading(
                raw_line,
                match.group(2),
                following,
                body_lines[position + 2] if position + 2 < len(body_lines) else None,
                base,
                full_width,
            ):
                # "4. Counts 8 and 9: Murder" — a numbered heading, not a legal
                # paragraph: it ends the open paragraph, is kept as a section
                # and as page text, and does not advance paragraph numbering.
                emit(page, run_number, run)
                run = []
                flush()
                run_number = None
                sections.append(
                    ParsedSection(
                        sequence=len(sections),
                        level=2,
                        heading=compact,
                        page_from=page.page_number,
                        page_to=page.page_number,
                        para_from=None,
                        para_to=None,
                    )
                )
                run.append(compact)
                continue
            if match is not None and "....." not in raw_line:
                number = int(match.group(1))
                # The first legal paragraph of a document is numbered 1 (a few
                # numbers of slack); a first "218." is a wrapped reference.
                in_sequence = (
                    number <= _MAX_FIRST_PARAGRAPH
                    if last_number is None
                    else last_number < number <= last_number + _MAX_PARAGRAPH_STEP
                )
                if in_sequence:
                    emit(page, run_number, run)
                    run = []
                    flush()
                    last_number = number
                    current = _OpenParagraph(
                        number=number,
                        pdf_from=page.pdf_page_index,
                        pdf_to=page.pdf_page_index,
                        page_from=page.page_number,
                        page_to=page.page_number,
                        parts=[match.group(2)],
                    )
                    run_number = number
                    run.append(match.group(2))
                    continue
            structural_start = (
                _indent(raw_line) >= base + 3
                and following is not None
                and _indent(following) <= base + 1
                and compact[:1].isalnum()
                and compact[:1].upper() == compact[:1]
            )
            if structural_start and match is None:
                # A paragraph start whose number the text layer does not carry
                # (e.g. rendered as an image). It ends the open paragraph; its
                # own text stays page body — a ¶ number is never invented.
                emit(page, run_number, run)
                run = []
                flush()
                run_number = None
            if current is not None:
                current.pdf_to = page.pdf_page_index
                current.page_to = page.page_number
                current.parts.append(compact)
            run.append(compact)
        emit(page, run_number, run)
        if footnote_lines:
            text = " ".join(" ".join(" ".join(line.split()) for line in footnote_lines).split())
            blocks.append(_Block(page.pdf_page_index, page.page_number, None, "footnotes", text))
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
    return paragraphs, sections, blocks, reasons


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

    # A printed page number that repeats within one version is not a coordinate
    # (e.g. a reclassification stamp "1 of 8" on every page). Fail closed: those
    # pages keep their exact PDF index, lose the printed number, and need review.
    repeated = {
        number
        for number, count in Counter(
            page.page_number for page in pages if page.page_number is not None
        ).items()
        if count > 1
    }
    if repeated:
        pages = [
            replace(page, page_number=None) if page.page_number in repeated else page
            for page in pages
        ]
        reasons.append(f"printed page numbers repeat within the version: {sorted(repeated)}")

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

    paragraphs, sections, blocks, segmentation_reasons = _paragraphs_and_sections(pages)
    reasons.extend(segmentation_reasons)
    # Every chunk is page-local: a paragraph that continues onto the next page
    # is one chunk per page, and body text or footnotes outside any numbered
    # paragraph stay on their own page.
    chunks: list[ParsedChunk] = []
    chunked_pages: set[int] = set()
    for block in blocks:
        chunked_pages.add(block.pdf_page_index)
        chunks.append(
            ParsedChunk(
                sequence=len(chunks),
                chunk_kind="paragraph" if block.kind == "paragraph" else "page",
                pdf_page_index_from=block.pdf_page_index,
                pdf_page_index_to=block.pdf_page_index,
                page_from=block.page_number,
                page_to=block.page_number,
                para_from=block.paragraph_number,
                para_to=block.paragraph_number,
                text=block.text,
            )
        )
    for page in pages:
        if page.pdf_page_index not in chunked_pages and page.text.strip():
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
    chunks.sort(key=lambda chunk: (chunk.pdf_page_index_from or 0, chunk.sequence))
    chunks = [replace(chunk, sequence=index) for index, chunk in enumerate(chunks)]
    return ParsedPdf(
        pages=pages,
        paragraphs=paragraphs,
        sections=sections,
        chunks=chunks,
        requires_review=bool(reasons),
        review_reasons=reasons,
    )
