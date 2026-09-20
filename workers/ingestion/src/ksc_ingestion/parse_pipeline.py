"""Phase 8 parse → citation extraction → persisted resolution pipeline."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    ArtifactStatus,
    AuditLog,
    Case,
    Citation,
    Document,
    DocumentChunk,
    DocumentIngestionState,
    DocumentPage,
    DocumentParagraph,
    DocumentSection,
    DocumentVersion,
    TextExtractionMethod,
    Transcript,
    TranscriptSegment,
)
from ksc_ingestion.citation_resolution import (
    apply_resolution,
    extract_citations,
    rebuild_identifier_index,
    resolve_extracted,
)
from ksc_ingestion.pdf_parser import PARSER_NAME, PARSER_VERSION, ParsedPdf, parse_pdf
from ksc_ingestion.storage import ObjectStore

_PHASE8_NAMESPACE = uuid.UUID("d14af643-3782-4fba-a1a2-546c3d1ee9d5")


def _stable_id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_PHASE8_NAMESPACE, ":".join(str(part) for part in parts))


@dataclass(frozen=True)
class ParsedVersionResult:
    official_version_ref: str
    pages: int
    paragraphs: int
    chunks: int
    transcript_segments: int
    requires_review: bool


@dataclass(frozen=True)
class Phase8RunResult:
    versions: list[ParsedVersionResult]
    identifiers: int
    citations: int
    resolved: int
    ambiguous: int
    unresolved: int
    invalid: int


class Phase8Pipeline:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        store: ObjectStore,
        *,
        case_number: str,
    ) -> None:
        self.sessions = sessions
        self.store = store
        self.case_number = case_number

    def run(self) -> Phase8RunResult:
        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise LookupError(f"case {self.case_number} is not seeded")
            version_ids = list(
                session.scalars(
                    select(DocumentVersion.id)
                    .join(Document)
                    .where(
                        Document.case_id == case.id,
                        DocumentVersion.artifact_status == ArtifactStatus.FETCHED,
                    )
                    .order_by(DocumentVersion.official_version_ref)
                ).all()
            )

        results: list[ParsedVersionResult] = []
        for version_id in version_ids:
            results.append(self._parse_version(version_id))

        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:  # pragma: no cover - protected by first lookup
                raise LookupError(f"case {self.case_number} is not seeded")
            identifiers = rebuild_identifier_index(session, case)
            session.commit()

        citation_counts = self._extract_and_resolve()
        return Phase8RunResult(
            versions=results,
            identifiers=identifiers,
            citations=sum(citation_counts.values()),
            resolved=citation_counts["resolved"],
            ambiguous=citation_counts["ambiguous"],
            unresolved=citation_counts["unresolved"],
            invalid=citation_counts["invalid"],
        )

    def _parse_version(self, version_id: uuid.UUID) -> ParsedVersionResult:
        with self.sessions() as session:
            version = session.get(DocumentVersion, version_id)
            if version is None or version.storage_key is None:
                raise LookupError(f"document version {version_id} has no held artifact")
            transcript = session.scalar(
                select(Transcript).where(Transcript.document_version_id == version.id)
            )
            if (
                version.parser_name == PARSER_NAME
                and version.parser_version == PARSER_VERSION
                and version.parsed_at is not None
                and version.page_count == len(version.pages)
            ):
                return ParsedVersionResult(
                    official_version_ref=version.official_version_ref,
                    pages=len(version.pages),
                    paragraphs=len(version.paragraphs),
                    chunks=len(version.chunks),
                    transcript_segments=len(transcript.segments) if transcript is not None else 0,
                    requires_review=version.parse_requires_review,
                )
            document = version.document
            data = self.store.get(version.storage_key)
            parsed = parse_pdf(data, transcript=document.document_type == "transcript")
            self._replace_parse(session, version, parsed)
            session.add(
                AuditLog(
                    actor="ksc-ingest-phase8",
                    action="document_version.parsed",
                    entity_type="document_version",
                    entity_id=str(version.id),
                    detail={
                        "official_version_ref": version.official_version_ref,
                        "parser": f"{PARSER_NAME}/{PARSER_VERSION}",
                        "pages": len(parsed.pages),
                        "paragraphs": len(parsed.paragraphs),
                        "chunks": len(parsed.chunks),
                        "transcript_segments": len(parsed.transcript_segments),
                        "requires_review": parsed.requires_review,
                    },
                )
            )
            session.commit()
            return ParsedVersionResult(
                official_version_ref=version.official_version_ref,
                pages=len(parsed.pages),
                paragraphs=len(parsed.paragraphs),
                chunks=len(parsed.chunks),
                transcript_segments=len(parsed.transcript_segments),
                requires_review=parsed.requires_review,
            )

    @staticmethod
    def _replace_parse(session: Session, version: DocumentVersion, parsed: ParsedPdf) -> None:
        # Extracted citations are regenerated after every parse. Citations in
        # other sources that target this version remain untouched.
        session.execute(delete(Citation).where(Citation.source_document_version_id == version.id))
        version.chunks.clear()
        version.sections.clear()
        version.paragraphs.clear()
        version.pages.clear()
        transcript = session.scalar(
            select(Transcript).where(Transcript.document_version_id == version.id)
        )
        if transcript is not None:
            transcript.segments.clear()
        session.flush()

        version.pages.extend(
            DocumentPage(
                id=_stable_id(version.id, "page", page.pdf_page_index),
                pdf_page_index=page.pdf_page_index,
                page_number=page.page_number,
                printed_page_label=page.printed_page_label,
                text=page.text,
                running_head=page.running_head,
                has_redactions=page.has_redactions,
                redaction_extents=page.redaction_extents,
            )
            for page in parsed.pages
        )
        version.paragraphs.extend(
            DocumentParagraph(
                id=_stable_id(version.id, "paragraph", paragraph.paragraph_number),
                sequence=paragraph.sequence,
                paragraph_number=paragraph.paragraph_number,
                pdf_page_index_from=paragraph.pdf_page_index_from,
                pdf_page_index_to=paragraph.pdf_page_index_to,
                page_from=paragraph.page_from,
                page_to=paragraph.page_to,
                text=paragraph.text,
            )
            for paragraph in parsed.paragraphs
        )
        version.sections.extend(
            DocumentSection(
                id=_stable_id(version.id, "section", section.sequence),
                sequence=section.sequence,
                level=section.level,
                heading=section.heading,
                page_from=section.page_from,
                page_to=section.page_to,
                para_from=section.para_from,
                para_to=section.para_to,
            )
            for section in parsed.sections
        )
        version.chunks.extend(
            DocumentChunk(
                id=_stable_id(version.id, "chunk", chunk.sequence),
                sequence=chunk.sequence,
                chunk_kind=chunk.chunk_kind,
                pdf_page_index_from=chunk.pdf_page_index_from,
                pdf_page_index_to=chunk.pdf_page_index_to,
                page_from=chunk.page_from,
                page_to=chunk.page_to,
                para_from=chunk.para_from,
                para_to=chunk.para_to,
                text=chunk.text,
                char_count=len(chunk.text),
            )
            for chunk in parsed.chunks
        )
        if transcript is not None:
            transcript.page_from = parsed.page_from
            transcript.page_to = parsed.page_to
            transcript.text_extraction_method = TextExtractionMethod.NATIVE_TEXT
            transcript.segments.extend(
                TranscriptSegment(
                    id=_stable_id(version.id, "segment", segment.sequence),
                    sequence=segment.sequence,
                    pdf_page_index=segment.pdf_page_index,
                    page_number=segment.page_number,
                    line_from=segment.line_from,
                    line_to=segment.line_to,
                    speaker=segment.speaker,
                    speaker_role=segment.speaker_role,
                    examination_type=segment.examination_type,
                    text=segment.text,
                    closed_session=segment.closed_session,
                )
                for segment in parsed.transcript_segments
            )
        version.text_extraction_method = TextExtractionMethod.NATIVE_TEXT
        version.parsed_at = datetime.now(UTC)
        version.parser_name = PARSER_NAME
        version.parser_version = PARSER_VERSION
        version.parse_requires_review = parsed.requires_review
        version.parse_notes = (
            {"review_reasons": parsed.review_reasons} if parsed.review_reasons else None
        )
        version.document.ingestion_state = DocumentIngestionState.PARSED

    @staticmethod
    def _citation_text(text: str, version_ref: str) -> str:
        lines = []
        upper_ref = version_ref.upper()
        for line in text.splitlines():
            compact = " ".join(line.split())
            if upper_ref in compact.upper() and re_page_header(compact):
                lines.append(" " * len(line))
            else:
                lines.append(line)
        return "\n".join(lines)

    def _extract_and_resolve(self) -> dict[str, int]:
        counts = {"resolved": 0, "ambiguous": 0, "unresolved": 0, "invalid": 0}
        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise LookupError(f"case {self.case_number} is not seeded")
            versions = session.scalars(
                select(DocumentVersion)
                .join(Document)
                .where(Document.case_id == case.id, DocumentVersion.parsed_at.is_not(None))
                .order_by(DocumentVersion.official_version_ref)
            ).all()
            for version in versions:
                session.execute(
                    delete(Citation).where(Citation.source_document_version_id == version.id)
                )
                transcript = session.scalar(
                    select(Transcript).where(Transcript.document_version_id == version.id)
                )
                if transcript is not None:
                    sources: list[tuple[str, int | None, int | None, uuid.UUID | None]] = [
                        (
                            segment.text,
                            segment.page_number,
                            segment.pdf_page_index,
                            segment.id,
                        )
                        for segment in transcript.segments
                        if not segment.closed_session
                    ]
                else:
                    sources = [
                        (
                            self._citation_text(page.text or "", version.official_version_ref),
                            page.page_number,
                            page.pdf_page_index,
                            None,
                        )
                        for page in version.pages
                    ]
                for text, source_page, pdf_page_index, source_segment_id in sources:
                    for extracted in extract_citations(text):
                        resolution = resolve_extracted(
                            session,
                            case,
                            extracted,
                            source_version_ref=version.official_version_ref,
                        )
                        citation = Citation(
                            id=_stable_id(
                                version.id,
                                "citation",
                                pdf_page_index,
                                source_segment_id,
                                extracted.source_start,
                                extracted.source_end,
                                extracted.raw_text,
                            ),
                            case_id=case.id,
                            raw_text=extracted.raw_text,
                            normalized_text=normalize_for_storage(extracted.normalized_identifier),
                            citation_type=extracted.citation_type,
                            source_document_version_id=version.id,
                            source_page=source_page,
                            source_pdf_page_index=pdf_page_index,
                            source_transcript_segment_id=source_segment_id,
                            source_char_start=extracted.source_start,
                            source_char_end=extracted.source_end,
                            source_url=version.source_url,
                            target_page=extracted.target_page,
                            target_para_from=extracted.target_para_from,
                            target_para_to=extracted.target_para_to,
                            target_line_from=extracted.target_line_from,
                            target_line_to=extracted.target_line_to,
                        )
                        apply_resolution(citation, resolution)
                        session.add(citation)
                        counts[resolution.state.value] += 1
                version.document.ingestion_state = DocumentIngestionState.INDEXED
            session.add(
                AuditLog(
                    actor="ksc-ingest-phase8",
                    action="citations.resolved",
                    entity_type="case",
                    entity_id=str(case.id),
                    detail=counts,
                )
            )
            session.commit()
        return counts


def re_page_header(line: str) -> bool:
    return " of " in line or "PAGE " in line.upper() or "FAQE " in line.upper()


def normalize_for_storage(identifier: str) -> str:
    return " ".join(identifier.split()).upper()
