"""Phase 20B transcript-segment anchors and printed page-header context.

A transcript segment receives PDF rectangles only when its own version's native
word geometry exposes one unambiguous printed line-number column (1..N, right
aligned, strictly descending the page) and the words on those numbered lines
reproduce the stored segment text exactly (whitespace-insensitive). Anything
else keeps the honest ``PAGE_AND_LINE`` / ``PAGE_ONLY`` coordinate with a
machine-readable reason. Private/closed-session segments never receive a
region, and nothing is copied between related versions.

The page-header context is the official running header ("Witness: W03877
(Open Session) … Examination by Mr. Capin"), read with the Phase 19B rule. It
says whose evidence a page belongs to; it never names a speaker label.
"""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from itertools import pairwise
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    Case,
    Document,
    DocumentPage,
    DocumentVersion,
    Hearing,
    PageTextGeometry,
    ProcessingRun,
    SourceAnchor,
    SourcePrecision,
    SourceRegion,
    SourceSpan,
    TextExtractionMethod,
    Transcript,
    TranscriptPageContext,
    TranscriptSegment,
    Visibility,
)
from ksc_ingestion.witness_appearances import RULE_ID as HEADER_RULE_ID
from ksc_ingestion.witness_appearances import RULE_VERSION as HEADER_RULE_VERSION
from ksc_ingestion.witness_appearances import parse_page_header

PROCESSOR = "phase20b-transcript-sync"
PROCESSOR_VERSION = "1"
OBJECT_TYPE = "transcript_segment"
TEXT_BASIS = "transcript_segment_text"
SEGMENT_STATE = "deterministic_parse"
_NAMESPACE = uuid.UUID("5d0c3a6e-20b0-4f7a-9a55-7b1c2e0f20b0")
_PUBLIC = (Visibility.PUBLIC, Visibility.PUBLIC_REDACTED)
_LINE_NUMBER = re.compile(r"\d{1,2}")
# Right edges of one printed line-number column agree to within this many points.
_COLUMN_TOLERANCE = 1.5


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NAMESPACE, "|".join(str(part) for part in parts))


class Word(Protocol):
    @property
    def text(self) -> str: ...
    @property
    def x(self) -> float | Decimal: ...
    @property
    def y(self) -> float | Decimal: ...
    @property
    def width(self) -> float | Decimal: ...
    @property
    def height(self) -> float | Decimal: ...


@dataclass(frozen=True)
class LineBox:
    number: int
    text: str
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class LineGrid:
    lines: dict[int, LineBox | None]
    """Printed line number → its body words' box (``None`` for an empty line)."""


def _nospace(value: str) -> str:
    return "".join(value.split())


def line_grid(words: Sequence[Word]) -> tuple[LineGrid | None, str | None]:
    """Map printed transcript line numbers to the words printed on that line.

    Returns ``(None, reason)`` unless exactly one right-aligned numeric column
    holds the values 1..N in strictly increasing vertical order.
    """
    numeric = [
        (index, word)
        for index, word in enumerate(words)
        if _LINE_NUMBER.fullmatch(word.text) and 1 <= int(word.text) <= 99
    ]
    columns: list[list[tuple[int, Word]]] = []
    for item in sorted(numeric, key=lambda pair: float(pair[1].x) + float(pair[1].width)):
        right = float(item[1].x) + float(item[1].width)
        if columns:
            last = columns[-1][-1][1]
            if right - (float(last.x) + float(last.width)) <= _COLUMN_TOLERANCE:
                columns[-1].append(item)
                continue
        columns.append([item])
    qualifying: list[list[tuple[int, Word]]] = []
    for column in columns:
        ordered = sorted(column, key=lambda pair: float(pair[1].y))
        values = [int(word.text) for _, word in ordered]
        tops = [float(word.y) for _, word in ordered]
        if (
            len(values) >= 2
            and values == list(range(1, len(values) + 1))
            and all(b > a for a, b in pairwise(tops))
        ):
            qualifying.append(ordered)
    if not qualifying:
        return None, "geometry_line_grid_not_found"
    if len(qualifying) > 1:
        return None, "geometry_line_grid_ambiguous"
    column = qualifying[0]
    column_ids = {index for index, _ in column}
    right_edge = max(float(word.x) + float(word.width) for _, word in column)
    centers = [float(word.y) + float(word.height) / 2 for _, word in column]
    pitch = min(b - a for a, b in pairwise(centers))
    tolerance = pitch * 0.4
    assigned: dict[int, list[Word]] = defaultdict(list)
    for index, word in enumerate(words):
        if index in column_ids or float(word.x) < right_edge:
            continue
        center = float(word.y) + float(word.height) / 2
        nearest = min(range(len(centers)), key=lambda k: abs(centers[k] - center))
        if abs(centers[nearest] - center) <= tolerance:
            assigned[nearest + 1].append(word)
    lines: dict[int, LineBox | None] = {}
    for number in range(1, len(column) + 1):
        body = assigned.get(number)
        if not body:
            lines[number] = None
            continue
        x0 = min(float(word.x) for word in body)
        y0 = min(float(word.y) for word in body)
        x1 = max(float(word.x) + float(word.width) for word in body)
        y1 = max(float(word.y) + float(word.height) for word in body)
        lines[number] = LineBox(
            number, " ".join(word.text for word in body), x0, y0, x1 - x0, y1 - y0
        )
    return LineGrid(lines), None


def segment_regions(
    grid: LineGrid | None,
    grid_reason: str | None,
    *,
    speaker: str | None,
    text: str,
    line_from: int,
    line_to: int,
    page_width: float,
    page_height: float,
) -> tuple[list[LineBox], str | None]:
    """The validated per-line boxes for one segment, or an empty list and why."""
    if grid is None:
        return [], grid_reason
    if any(number not in grid.lines for number in range(line_from, line_to + 1)):
        return [], "geometry_line_missing"
    boxes = [
        box for number in range(line_from, line_to + 1) if (box := grid.lines[number]) is not None
    ]
    expected = _nospace(f"{speaker}:{text}" if speaker else text)
    if not boxes or _nospace("".join(box.text for box in boxes)) != expected:
        return [], "geometry_line_text_mismatch"
    if any(
        box.x < 0 or box.y < 0 or box.x + box.width > page_width or box.y + box.height > page_height
        for box in boxes
    ):
        return [], "geometry_line_out_of_bounds"
    return boxes, None


@dataclass(frozen=True)
class TranscriptSyncResult:
    run_id: uuid.UUID
    versions: int
    segments: int
    precision: dict[str, int]
    reasons: dict[str, int]
    page_contexts: int


class TranscriptSyncProjector:
    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def run(self) -> TranscriptSyncResult:
        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise LookupError(f"case {self.case_number} is not seeded")
            transcripts = session.execute(
                select(Transcript.id, DocumentVersion.id)
                .join(DocumentVersion, DocumentVersion.id == Transcript.document_version_id)
                .join(Document, Document.id == DocumentVersion.document_id)
                .join(Hearing, Hearing.id == Transcript.hearing_id)
                .where(
                    Hearing.case_id == case.id,
                    Document.case_id == case.id,
                    Document.visibility.in_(_PUBLIC),
                    DocumentVersion.visibility.in_(_PUBLIC),
                    Transcript.visibility.in_(_PUBLIC),
                )
                .order_by(DocumentVersion.official_version_ref)
            ).all()
            run = ProcessingRun(
                case_id=case.id,
                processor=PROCESSOR,
                processor_version=PROCESSOR_VERSION,
                status="running",
                selected_count=len(transcripts),
                processed_count=0,
                failed_count=0,
                started_at=datetime.now(UTC),
                detail={"header_rule": f"{HEADER_RULE_ID}/{HEADER_RULE_VERSION}"},
            )
            session.add(run)
            session.commit()
            run_id = run.id

        precision: dict[str, int] = defaultdict(int)
        reasons: dict[str, int] = defaultdict(int)
        segments = contexts = 0
        try:
            with self.sessions() as session:
                owned = select(SourceAnchor.source_span_id).where(
                    SourceAnchor.object_type == OBJECT_TYPE
                )
                session.execute(delete(SourceSpan).where(SourceSpan.id.in_(owned)))
                session.commit()
            for transcript_id, version_id in transcripts:
                with self.sessions() as session:
                    added, added_contexts = self._project_version(
                        session, run_id, transcript_id, version_id, precision, reasons
                    )
                    segments += added
                    contexts += added_contexts
                    current = session.get(ProcessingRun, run_id)
                    assert current is not None
                    current.processed_count += 1
                    session.commit()
        except Exception:
            with self.sessions() as session:
                failed = session.get(ProcessingRun, run_id)
                assert failed is not None
                failed.status = "failed"
                failed.failed_count += 1
                failed.finished_at = datetime.now(UTC)
                session.commit()
            raise

        with self.sessions() as session:
            completed = session.get(ProcessingRun, run_id)
            assert completed is not None
            completed.status = "completed"
            completed.finished_at = datetime.now(UTC)
            completed.detail = {
                **(completed.detail or {}),
                "segments": segments,
                "precision": dict(precision),
                "reasons": dict(reasons),
                "page_contexts": contexts,
            }
            session.commit()
        return TranscriptSyncResult(
            run_id, len(transcripts), segments, dict(precision), dict(reasons), contexts
        )

    def _project_version(
        self,
        session: Session,
        run_id: uuid.UUID,
        transcript_id: uuid.UUID,
        version_id: uuid.UUID,
        precision: dict[str, int],
        reasons: dict[str, int],
    ) -> tuple[int, int]:
        pages = {
            page.pdf_page_index: page
            for page in session.scalars(
                select(DocumentPage).where(DocumentPage.document_version_id == version_id)
            )
        }
        words: dict[int, list[PageTextGeometry]] = defaultdict(list)
        for word in session.scalars(
            select(PageTextGeometry)
            .where(PageTextGeometry.document_version_id == version_id)
            .order_by(PageTextGeometry.pdf_page_index, PageTextGeometry.sequence)
        ):
            words[word.pdf_page_index].append(word)

        session.execute(
            delete(TranscriptPageContext).where(
                TranscriptPageContext.document_version_id == version_id
            )
        )
        contexts = 0
        for index, held in sorted(pages.items()):
            header = parse_page_header(held.text or "")
            if header is None:
                continue
            assert held.text is not None and held.text[header.start : header.end] == header.text
            session.add(
                TranscriptPageContext(
                    id=_id("context", version_id, index),
                    document_version_id=version_id,
                    pdf_page_index=index,
                    page_number=held.page_number,
                    header_text=header.text,
                    header_char_start=header.start,
                    header_char_end=header.end,
                    subject=header.subject,
                    subject_is_code=header.is_code,
                    session_state=header.session,
                    examination=header.examination,
                    rule_id=HEADER_RULE_ID,
                    rule_version=HEADER_RULE_VERSION,
                    processing_run_id=run_id,
                )
            )
            contexts += 1

        grids: dict[int, tuple[LineGrid | None, str | None]] = {}
        count = 0
        for segment in session.scalars(
            select(TranscriptSegment)
            .where(TranscriptSegment.transcript_id == transcript_id)
            .order_by(TranscriptSegment.sequence)
        ):
            page: DocumentPage | None = (
                pages.get(segment.pdf_page_index) if segment.pdf_page_index is not None else None
            )
            boxes: list[LineBox] = []
            if page is None:
                level = SourcePrecision.TEXT_ONLY if segment.text else SourcePrecision.UNAVAILABLE
                reason: str | None = "pdf_page_unavailable"
            elif segment.line_from is None:
                level, reason = SourcePrecision.PAGE_ONLY, "transcript_line_unavailable"
            elif segment.closed_session:
                level, reason = SourcePrecision.PAGE_AND_LINE, "closed_session_text_withheld"
            elif page.geometry_state != "native" or not page.width_points or not page.height_points:
                level, reason = SourcePrecision.PAGE_AND_LINE, "pdf_page_geometry_unavailable"
            else:
                if page.pdf_page_index not in grids:
                    grids[page.pdf_page_index] = line_grid(words.get(page.pdf_page_index, []))
                grid, grid_reason = grids[page.pdf_page_index]
                boxes, reason = segment_regions(
                    grid,
                    grid_reason,
                    speaker=segment.speaker,
                    text=segment.text,
                    line_from=segment.line_from,
                    line_to=segment.line_to or segment.line_from,
                    page_width=float(page.width_points),
                    page_height=float(page.height_points),
                )
                level = SourcePrecision.EXACT_GEOMETRY if boxes else SourcePrecision.PAGE_AND_LINE
            span_id = _id("span", segment.id)
            span = SourceSpan(
                id=span_id,
                document_version_id=version_id,
                pdf_page_index=segment.pdf_page_index if page is not None else None,
                page_number=segment.page_number,
                transcript_segment_id=segment.id,
                line_from=segment.line_from,
                line_to=segment.line_to,
                exact_text=segment.text or None,
                text_basis=TEXT_BASIS if segment.text else None,
                char_start=0 if segment.text else None,
                char_end=len(segment.text) if segment.text else None,
                extraction_method=TextExtractionMethod.NATIVE_TEXT
                if page is not None
                else TextExtractionMethod.NONE,
                extractor_version=PROCESSOR_VERSION,
                precision=level,
                state="verified" if boxes else "unavailable",
                failure_reason=reason,
                processing_run_id=run_id,
            )
            for sequence, box in enumerate(boxes):
                span.regions.append(
                    SourceRegion(
                        id=_id(span_id, "region", sequence),
                        sequence=sequence,
                        x=Decimal(str(round(box.x, 4))),
                        y=Decimal(str(round(box.y, 4))),
                        width=Decimal(str(round(box.width, 4))),
                        height=Decimal(str(round(box.height, 4))),
                    )
                )
            session.add(span)
            session.add(
                SourceAnchor(
                    id=_id("anchor", segment.id),
                    source_span_id=span_id,
                    object_type=OBJECT_TYPE,
                    object_id=segment.id,
                    anchor_role=OBJECT_TYPE,
                    source_verification_state=SEGMENT_STATE,
                )
            )
            precision[level.value] += 1
            if reason:
                reasons[reason] += 1
            count += 1
        return count, contexts
