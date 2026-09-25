"""Phase 20A native PDF geometry and reusable SourceAnchor projection.

Only already-held public artifacts are read. Native text is preferred; an empty
native layer is marked ``ocr_required`` and is never silently OCR-derived.
"""

from __future__ import annotations

import io
import re
import uuid
from collections.abc import Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from itertools import chain
from typing import Any

import pdfminer
import pypdf
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTAnno, LTChar, LTContainer, LTPage, LTTextLine
from pypdf import PdfReader
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    ArtifactStatus,
    Case,
    Citation,
    Document,
    DocumentPage,
    DocumentParagraph,
    DocumentVersion,
    EntityOccurrence,
    Finding,
    PageTextGeometry,
    ProcessingRun,
    Relationship,
    SourceAnchor,
    SourcePrecision,
    SourceRegion,
    SourceSpan,
    TextExtractionMethod,
    Visibility,
    WitnessAppearance,
)
from ksc_ingestion.storage import ObjectStore

PROCESSOR = "phase20a-source-geometry"
PROCESSOR_VERSION = "1"
GEOMETRY_EXTRACTOR = "ksc-native-pdf-geometry"
_NAMESPACE = uuid.UUID("cf13158f-60f1-49f2-9d08-283ba78cdfaa")
_PUBLIC = (Visibility.PUBLIC, Visibility.PUBLIC_REDACTED)


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NAMESPACE, "|".join(str(part) for part in parts))


@dataclass(frozen=True)
class GeometryWord:
    text: str
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class GeometryPage:
    width: float
    height: float
    rotation: int
    text: str
    words: tuple[GeometryWord, ...]


@dataclass(frozen=True)
class ProjectionResult:
    run_id: uuid.UUID
    versions: int
    native_pages: int
    ocr_required_pages: int
    geometry_words: int
    anchors: int
    precision: dict[str, int]
    by_object_type: dict[str, int]


def _lines(node: LTContainer[Any]) -> Iterable[LTTextLine]:
    for child in node:
        if isinstance(child, LTTextLine):
            yield child
        elif isinstance(child, LTContainer):
            yield from _lines(child)


def _line_words(line: LTTextLine, page_height: float) -> list[GeometryWord]:
    words: list[GeometryWord] = []
    chars: list[LTChar] = []

    def flush() -> None:
        if not chars:
            return
        value = "".join(char.get_text() for char in chars)
        if value.strip():
            x0 = min(char.x0 for char in chars)
            y0 = min(char.y0 for char in chars)
            x1 = max(char.x1 for char in chars)
            y1 = max(char.y1 for char in chars)
            words.append(GeometryWord(value, x0, page_height - y1, x1 - x0, y1 - y0))
        chars.clear()

    for child in line:
        if isinstance(child, LTChar):
            if child.get_text().isspace():
                flush()
            else:
                chars.append(child)
        elif isinstance(child, LTAnno):
            if child.get_text().isspace():
                flush()
    flush()
    return words


def extract_native_geometry(data: bytes) -> list[GeometryPage]:
    """Extract word boxes directly from the embedded PDF text layer."""

    pages: list[GeometryPage] = []
    # pdfminer normalizes rotated pages into their rendered orientation and
    # consequently exposes ``LTPage.rotate`` as zero. Preserve the source PDF's
    # rotation separately while retaining pdfminer's rendered dimensions and
    # coordinates, which are the coordinate space used by PDF.js.
    rotations = [
        int(page.get("/Rotate", 0) or 0) % 360 for page in PdfReader(io.BytesIO(data)).pages
    ]
    for page_index, layout in enumerate(extract_pages(io.BytesIO(data))):
        assert isinstance(layout, LTPage)
        extracted = chain.from_iterable(_line_words(line, layout.height) for line in _lines(layout))
        # Some public PDFs draw stamps outside their declared MediaBox. Those
        # coordinates cannot be rendered faithfully and are omitted, never
        # clamped into a guessed region.
        words = tuple(
            word
            for word in extracted
            if word.x >= 0
            and word.y >= 0
            and word.x + word.width <= layout.width
            and word.y + word.height <= layout.height
        )
        text = " ".join(word.text for word in words)
        pages.append(
            GeometryPage(
                width=float(layout.width),
                height=float(layout.height),
                rotation=rotations[page_index],
                text=text,
                words=words,
            )
        )
    return pages


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def _matches(words: list[PageTextGeometry], exact_text: str) -> list[list[PageTextGeometry]]:
    wanted = _tokenize(exact_text)
    if not wanted:
        return []
    values = [word.text for word in words]
    size = len(wanted)
    return [
        words[index : index + size]
        for index in range(len(values) - size + 1)
        if values[index : index + size] == wanted
    ]


class SourceGeometryProjector:
    def __init__(
        self, sessions: sessionmaker[Session], store: ObjectStore, *, case_number: str
    ) -> None:
        self.sessions = sessions
        self.store = store
        self.case_number = case_number

    def run(self) -> ProjectionResult:
        started = datetime.now(UTC)
        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise LookupError(f"case {self.case_number} is not seeded")
            versions = session.scalars(
                select(DocumentVersion)
                .join(Document)
                .where(
                    Document.case_id == case.id,
                    Document.visibility.in_(_PUBLIC),
                    DocumentVersion.visibility.in_(_PUBLIC),
                    DocumentVersion.artifact_status == ArtifactStatus.FETCHED,
                    DocumentVersion.parsed_at.is_not(None),
                )
                .order_by(DocumentVersion.official_version_ref)
            ).all()
            run = ProcessingRun(
                case_id=case.id,
                processor=PROCESSOR,
                processor_version=PROCESSOR_VERSION,
                status="running",
                selected_count=len(versions),
                processed_count=0,
                failed_count=0,
                started_at=started,
                detail={
                    "geometry_extractor": GEOMETRY_EXTRACTOR,
                    "geometry_extractor_version": PROCESSOR_VERSION,
                    "dependencies": {
                        "pdfminer.six": pdfminer.__version__,
                        "pypdf": pypdf.__version__,
                    },
                },
            )
            session.add(run)
            session.commit()
            run_id = run.id

        native_pages = ocr_required = word_count = 0
        try:
            pending: list[DocumentVersion] = []
            for version in versions:
                if version.storage_key is None:
                    continue
                with self.sessions() as session:
                    existing_pages = session.scalars(
                        select(DocumentPage).where(DocumentPage.document_version_id == version.id)
                    ).all()
                    if existing_pages and all(
                        page.geometry_extractor == GEOMETRY_EXTRACTOR
                        and page.geometry_extractor_version == PROCESSOR_VERSION
                        and page.geometry_state != "unavailable"
                        for page in existing_pages
                    ):
                        # The bytes/extractor output is idempotently reusable,
                        # while this successful reconciliation run becomes the
                        # current page-level processing lineage.
                        for page in existing_pages:
                            page.geometry_processing_run_id = run_id
                        native_pages += sum(
                            page.geometry_state == "native" for page in existing_pages
                        )
                        ocr_required += sum(
                            page.geometry_state == "ocr_required" for page in existing_pages
                        )
                        word_count += int(
                            session.scalar(
                                select(func.count(PageTextGeometry.id)).where(
                                    PageTextGeometry.document_version_id == version.id
                                )
                            )
                            or 0
                        )
                        current_run = session.get(ProcessingRun, run_id)
                        assert current_run is not None
                        current_run.processed_count += 1
                        session.commit()
                        continue
                pending.append(version)

            # Geometry extraction is CPU-bound. Keep at most four artifacts in
            # flight so long transcripts complete in parallel without holding
            # the corpus (or all extracted word objects) in memory at once.
            pending_iter = iter(pending)
            futures: dict[Future[list[GeometryPage]], DocumentVersion] = {}
            with ProcessPoolExecutor(max_workers=min(4, len(pending)) or 1) as executor:

                def submit_next() -> bool:
                    version = next(pending_iter, None)
                    if version is None:
                        return False
                    assert version.storage_key is not None
                    futures[
                        executor.submit(
                            extract_native_geometry, self.store.get(version.storage_key)
                        )
                    ] = version
                    return True

                for _ in range(4):
                    if not submit_next():
                        break
                while futures:
                    finished, _ = wait(futures, return_when=FIRST_COMPLETED)
                    for future in finished:
                        version = futures.pop(future)
                        added_native, added_ocr, added_words = self._persist_geometry(
                            version, future.result(), run_id
                        )
                        native_pages += added_native
                        ocr_required += added_ocr
                        word_count += added_words
                        submit_next()
            anchors, precision, by_type = self._project_anchors(run_id)
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
                "native_pages": native_pages,
                "ocr_required_pages": ocr_required,
                "geometry_words": word_count,
                "anchors": anchors,
                "precision": precision,
                "by_object_type": by_type,
            }
            session.commit()
        return ProjectionResult(
            run_id,
            len(versions),
            native_pages,
            ocr_required,
            word_count,
            anchors,
            precision,
            by_type,
        )

    def _persist_geometry(
        self,
        version: DocumentVersion,
        layouts: list[GeometryPage],
        run_id: uuid.UUID,
    ) -> tuple[int, int, int]:
        native_pages = ocr_required = word_count = 0
        with self.sessions() as session:
            current = session.get(DocumentVersion, version.id)
            assert current is not None
            pages = {page.pdf_page_index: page for page in current.pages}
            if len(layouts) != len(pages):
                raise RuntimeError(f"page count changed for {version.official_version_ref}")
            session.execute(
                delete(PageTextGeometry).where(PageTextGeometry.document_version_id == version.id)
            )
            for index, layout in enumerate(layouts):
                page = pages[index]
                page.width_points = layout.width
                page.height_points = layout.height
                page.rotation = layout.rotation
                page.geometry_text = layout.text or None
                page.geometry_extraction_method = "native_pdf_text" if layout.words else None
                page.geometry_state = "native" if layout.words else "ocr_required"
                page.geometry_extractor = GEOMETRY_EXTRACTOR
                page.geometry_extractor_version = PROCESSOR_VERSION
                page.geometry_processing_run_id = run_id
                if layout.words:
                    native_pages += 1
                else:
                    ocr_required += 1
                cursor = 0
                for sequence, word in enumerate(layout.words):
                    start = cursor
                    end = start + len(word.text)
                    session.add(
                        PageTextGeometry(
                            id=_id(version.id, "geometry", index, sequence),
                            document_version_id=version.id,
                            pdf_page_index=index,
                            sequence=sequence,
                            text=word.text,
                            char_start=start,
                            char_end=end,
                            x=Decimal(str(round(word.x, 4))),
                            y=Decimal(str(round(word.y, 4))),
                            width=Decimal(str(round(word.width, 4))),
                            height=Decimal(str(round(word.height, 4))),
                            extraction_method=TextExtractionMethod.NATIVE_TEXT,
                            extraction_state="usable",
                        )
                    )
                    cursor = end + 1
                    word_count += 1
            current_run = session.get(ProcessingRun, run_id)
            assert current_run is not None
            current_run.processed_count += 1
            session.commit()
        return native_pages, ocr_required, word_count

    def _project_anchors(self, run_id: uuid.UUID) -> tuple[int, dict[str, int], dict[str, int]]:
        precision: dict[str, int] = {}
        by_type: dict[str, int] = {}
        basis_spans: dict[tuple[str, uuid.UUID, str], tuple[uuid.UUID, SourcePrecision]] = {}
        self._cached_geometry: (
            tuple[tuple[uuid.UUID, int | None], DocumentPage | None, list[PageTextGeometry]] | None
        ) = None
        with self.sessions() as session:
            # Phase 20B transcript-segment anchors own their spans and are
            # re-projected by `transcript_sync`; leave them in place.
            owned = select(SourceAnchor.source_span_id).where(
                SourceAnchor.object_type != "transcript_segment"
            )
            session.execute(delete(SourceSpan).where(SourceSpan.id.in_(owned)))
            session.flush()

            occurrences = session.scalars(
                select(EntityOccurrence)
                .where(EntityOccurrence.rule_id.is_not(None))
                .order_by(EntityOccurrence.document_version_id, EntityOccurrence.pdf_page_index)
            ).all()
            for occurrence in occurrences:
                span_id, span_precision = self._add_anchor(
                    session,
                    run_id,
                    "entity_occurrence",
                    occurrence.id,
                    "mention",
                    occurrence.document_version_id,
                    occurrence.pdf_page_index,
                    occurrence.page_number,
                    occurrence.paragraph_number,
                    occurrence.transcript_segment_id,
                    occurrence.line_from,
                    occurrence.line_to,
                    occurrence.occurrence_text,
                    occurrence.char_anchor,
                    occurrence.char_start,
                    occurrence.char_end,
                    "verified" if occurrence.mention_state == "verified" else "review_required",
                    precision,
                    by_type,
                )
                basis_spans[("entity_occurrence", occurrence.id, "mention")] = (
                    span_id,
                    span_precision,
                )

            citations = session.scalars(
                select(Citation)
                .where(Citation.source_document_version_id.is_not(None))
                .order_by(Citation.source_document_version_id, Citation.source_pdf_page_index)
            ).all()
            for citation in citations:
                assert citation.source_document_version_id is not None
                span_id, span_precision = self._add_anchor(
                    session,
                    run_id,
                    "citation",
                    citation.id,
                    "citation_source",
                    citation.source_document_version_id,
                    citation.source_pdf_page_index,
                    citation.source_page,
                    citation.source_para,
                    citation.source_transcript_segment_id,
                    None,
                    None,
                    citation.raw_text,
                    "transcript_segment_text"
                    if citation.source_transcript_segment_id
                    else "document_page_text",
                    citation.source_char_start,
                    citation.source_char_end,
                    citation.verification_state.value,
                    precision,
                    by_type,
                )
                basis_spans[("citation", citation.id, "citation_source")] = (
                    span_id,
                    span_precision,
                )

            relationships = session.scalars(select(Relationship)).all()
            for relationship in relationships:
                basis_key: tuple[str, uuid.UUID, str] | None = None
                if relationship.entity_occurrence_id is not None:
                    basis_key = ("entity_occurrence", relationship.entity_occurrence_id, "mention")
                elif relationship.citation_id is not None:
                    basis_key = ("citation", relationship.citation_id, "citation_source")
                elif relationship.witness_appearance_id is not None:
                    appearance = session.get(WitnessAppearance, relationship.witness_appearance_id)
                    if appearance is None or appearance.document_version_id is None:
                        continue
                    span_id, span_precision = self._add_anchor(
                        session,
                        run_id,
                        "relationship",
                        relationship.id,
                        "relationship_evidence",
                        appearance.document_version_id,
                        appearance.signal_pdf_page_index,
                        appearance.signal_page_number,
                        None,
                        None,
                        None,
                        None,
                        appearance.signal_text,
                        "document_page_text",
                        appearance.signal_char_start,
                        appearance.signal_char_end,
                        relationship.verification_state.value,
                        precision,
                        by_type,
                    )
                    continue
                if basis_key is None or basis_key not in basis_spans:
                    continue
                span_id, span_precision = basis_spans[basis_key]
                session.add(
                    SourceAnchor(
                        id=_id("anchor", "relationship", relationship.id, "relationship_evidence"),
                        source_span_id=span_id,
                        object_type="relationship",
                        object_id=relationship.id,
                        anchor_role="relationship_evidence",
                        source_verification_state=relationship.verification_state.value,
                    )
                )
                precision[span_precision.value] = precision.get(span_precision.value, 0) + 1
                by_type["relationship"] = by_type.get("relationship", 0) + 1

            findings = session.scalars(
                select(Finding).where(Finding.judgment_version_id.is_not(None))
            ).all()
            for finding in findings:
                assert finding.judgment_version_id is not None
                paragraph = session.scalar(
                    select(DocumentParagraph).where(
                        DocumentParagraph.document_version_id == finding.judgment_version_id,
                        DocumentParagraph.paragraph_number == finding.para_from,
                    )
                )
                self._add_anchor(
                    session,
                    run_id,
                    "finding",
                    finding.id,
                    "finding_passage",
                    finding.judgment_version_id,
                    paragraph.pdf_page_index_from if paragraph else None,
                    paragraph.page_from if paragraph else None,
                    finding.para_from,
                    None,
                    None,
                    None,
                    finding.text,
                    "document_page_text",
                    None,
                    None,
                    finding.verification_state.value,
                    precision,
                    by_type,
                )
            session.commit()
        return sum(precision.values()), precision, by_type

    def _add_anchor(
        self,
        session: Session,
        run_id: uuid.UUID,
        object_type: str,
        object_id: uuid.UUID,
        role: str,
        version_id: uuid.UUID,
        pdf_page_index: int | None,
        page_number: int | None,
        paragraph: int | None,
        segment_id: uuid.UUID | None,
        line_from: int | None,
        line_to: int | None,
        exact_text: str | None,
        text_basis: str | None,
        char_start: int | None,
        char_end: int | None,
        verification: str,
        precision_counts: dict[str, int],
        type_counts: dict[str, int],
    ) -> tuple[uuid.UUID, SourcePrecision]:
        key = (version_id, pdf_page_index)
        if self._cached_geometry is not None and self._cached_geometry[0] == key:
            _, page, words = self._cached_geometry
        else:
            page = (
                session.scalar(
                    select(DocumentPage).where(
                        DocumentPage.document_version_id == version_id,
                        DocumentPage.pdf_page_index == pdf_page_index,
                    )
                )
                if pdf_page_index is not None
                else None
            )
            words = (
                list(
                    session.scalars(
                        select(PageTextGeometry)
                        .where(
                            PageTextGeometry.document_version_id == version_id,
                            PageTextGeometry.pdf_page_index == pdf_page_index,
                        )
                        .order_by(PageTextGeometry.sequence)
                    ).all()
                )
                if page is not None
                else []
            )
            self._cached_geometry = (key, page, words)
        matches = _matches(list(words), exact_text or "") if exact_text else []
        selected: list[PageTextGeometry] | None = matches[0] if len(matches) == 1 else None
        if (
            selected is None
            and len(matches) > 1
            and page is not None
            and page.text is not None
            and text_basis == "document_page_text"
            and exact_text
            and char_start is not None
            and char_end is not None
            and page.text[char_start:char_end] == exact_text
        ):
            starts = [match.start() for match in re.finditer(re.escape(exact_text), page.text)]
            if len(starts) == len(matches) and char_start in starts:
                selected = matches[starts.index(char_start)]
        if selected is not None:
            precision = (
                SourcePrecision.OCR_GEOMETRY
                if page and page.geometry_state == "ocr"
                else SourcePrecision.EXACT_GEOMETRY
            )
            method = (
                TextExtractionMethod.OCR
                if precision is SourcePrecision.OCR_GEOMETRY
                else TextExtractionMethod.NATIVE_TEXT
            )
            failure = None
        elif pdf_page_index is not None and line_from is not None:
            precision, method, failure = (
                SourcePrecision.PAGE_AND_LINE,
                TextExtractionMethod.NATIVE_TEXT,
                "geometry_text_not_unique",
            )
        elif pdf_page_index is not None:
            precision, method, failure = (
                SourcePrecision.PAGE_ONLY,
                TextExtractionMethod.NATIVE_TEXT,
                "geometry_text_not_unique" if len(matches) > 1 else "geometry_text_not_found",
            )
        elif exact_text:
            precision, method, failure = (
                SourcePrecision.TEXT_ONLY,
                TextExtractionMethod.NATIVE_TEXT,
                "pdf_page_unavailable",
            )
        else:
            precision, method, failure = (
                SourcePrecision.UNAVAILABLE,
                TextExtractionMethod.NONE,
                "source_coordinate_unavailable",
            )
        span_id = _id("span", object_type, object_id, role)
        span = SourceSpan(
            id=span_id,
            document_version_id=version_id,
            pdf_page_index=pdf_page_index,
            page_number=page_number,
            paragraph_number=paragraph,
            transcript_segment_id=segment_id,
            line_from=line_from,
            line_to=line_to,
            exact_text=exact_text,
            text_basis=text_basis,
            char_start=char_start,
            char_end=char_end,
            extraction_method=method,
            extractor_version=PROCESSOR_VERSION,
            precision=precision,
            state="verified"
            if selected is not None
            else (
                "review_required"
                if verification in {"review_required", "ai_flagged"}
                else "unavailable"
            ),
            failure_reason=failure,
            processing_run_id=run_id,
        )
        session.add(span)
        for sequence, word in enumerate(selected or []):
            span.regions.append(
                SourceRegion(
                    id=_id(span_id, "region", sequence),
                    sequence=sequence,
                    x=word.x,
                    y=word.y,
                    width=word.width,
                    height=word.height,
                )
            )
        session.add(
            SourceAnchor(
                id=_id("anchor", object_type, object_id, role),
                source_span_id=span_id,
                object_type=object_type,
                object_id=object_id,
                anchor_role=role,
                source_verification_state=verification,
            )
        )
        precision_counts[precision.value] = precision_counts.get(precision.value, 0) + 1
        type_counts[object_type] = type_counts.get(object_type, 0) + 1
        return span_id, precision
