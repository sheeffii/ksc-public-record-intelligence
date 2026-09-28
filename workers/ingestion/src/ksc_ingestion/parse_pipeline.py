"""Phase 8 parse → citation extraction → persisted resolution pipeline."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session, object_session, sessionmaker

from ksc_api.models import (
    AiRetrievalSource,
    ArtifactQuarantine,
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
    ProcessingRun,
    Relationship,
    RelationshipOrigin,
    TextExtractionMethod,
    Transcript,
    TranscriptSegment,
    VerificationState,
)
from ksc_ingestion.citation_resolution import (
    apply_resolution,
    extract_citations,
    rebuild_identifier_index,
    resolve_extracted,
)
from ksc_ingestion.pdf_parser import PARSER_NAME, PARSER_VERSION, ParsedPdf, parse_pdf
from ksc_ingestion.storage import ObjectStore

log = logging.getLogger(__name__)

_PHASE8_NAMESPACE = uuid.UUID("d14af643-3782-4fba-a1a2-546c3d1ee9d5")


def not_open_quarantined() -> Any:
    """Open quarantine material never enters parsing or citation resolution.

    Quarantine is explicit review state; a version stays excluded until a
    reviewer releases or rejects the row. The Phase 13 gate separately fails
    if any open-quarantine version already holds parsed output.
    """
    return ~exists().where(
        ArtifactQuarantine.document_version_id == DocumentVersion.id,
        ArtifactQuarantine.state == "open",
    )


def select_processable_versions(case_id: uuid.UUID, *, parsed_only: bool = False) -> Any:
    """Versions the parser (held bytes) or resolver (parsed output) may touch."""
    statement = (
        select(DocumentVersion)
        .join(Document)
        .where(Document.case_id == case_id, not_open_quarantined())
        .order_by(DocumentVersion.official_version_ref)
    )
    if parsed_only:
        return statement.where(DocumentVersion.parsed_at.is_not(None))
    return statement.where(DocumentVersion.artifact_status == ArtifactStatus.FETCHED)


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
    # Set when this version could not be parsed. Nothing of it was written;
    # the rest of the run continued (one bad PDF never aborts a batch).
    error: str | None = None


@dataclass(frozen=True)
class Phase8RunResult:
    versions: list[ParsedVersionResult]
    identifiers: int
    citations: int
    resolved: int
    ambiguous: int
    unresolved: int
    invalid: int


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _holds_excerpt(text: str, excerpt: str) -> bool:
    """Whether `text` holds the excerpt verbatim. The excerpt may open on text
    parser v4 keeps apart (a heading, the previous page), so a 60-character
    window slides forward word by word; the first window found decides."""
    haystack = _normalized(text)
    full = _normalized(excerpt)[:400]
    for start in [0] + [i + 1 for i, ch in enumerate(full) if ch == " "]:
        window = full[start : start + 60]
        if len(window) < 40:
            return False
        if window in haystack:
            return True
    return False


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
        # Stale citations retired by the most recent extract-and-resolve pass.
        self.retired_citations = 0
        self.repair_structure: frozenset[str] = frozenset()

    def run(
        self, *, force: bool = False, repair_structure: frozenset[str] = frozenset()
    ) -> Phase8RunResult:
        """`repair_structure` names versions whose paragraph/chunk structure may
        change (a segmentation repair). Every other version still fails closed
        on a structural change."""
        self.repair_structure = repair_structure
        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise LookupError(f"case {self.case_number} is not seeded")
            version_ids = [
                version.id
                for version in session.scalars(select_processable_versions(case.id)).all()
            ]
            run = ProcessingRun(
                case_id=case.id,
                processor="pdf_parse_and_citation_resolution",
                processor_version=PARSER_VERSION,
                status="running",
                forced=force,
                selected_count=len(version_ids),
                started_at=datetime.now(UTC),
            )
            session.add(run)
            session.commit()
            run_id = run.id

        try:
            results = self._parse_all(run_id, version_ids, force=force)
            failed = sum(1 for r in results if r.error)

            with self.sessions() as session:
                case = session.scalar(select(Case).where(Case.case_number == self.case_number))
                if case is None:  # pragma: no cover - protected by first lookup
                    raise LookupError(f"case {self.case_number} is not seeded")
                identifiers = rebuild_identifier_index(session, case)
                session.commit()

            citation_counts = self._extract_and_resolve()
            result = Phase8RunResult(
                versions=results,
                identifiers=identifiers,
                citations=sum(citation_counts.values()),
                resolved=citation_counts["resolved"],
                ambiguous=citation_counts["ambiguous"],
                unresolved=citation_counts["unresolved"],
                invalid=citation_counts["invalid"],
            )
        except Exception as exc:
            self._finish_processing_run(run_id, status="failed", error=type(exc).__name__)
            raise
        self._finish_processing_run(
            run_id,
            status="completed",
            processed=len(results) - failed,
            failed=failed,
            detail={
                "identifiers": identifiers,
                **citation_counts,
                "failed_versions": [r.official_version_ref for r in results if r.error],
            },
        )
        return result

    def reresolve(self) -> dict[str, int]:
        """Rebuild identifier mappings and deterministically resolve all citations."""

        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise LookupError(f"case {self.case_number} is not seeded")
            run = ProcessingRun(
                case_id=case.id,
                processor="citation_resolution",
                processor_version="exact-v1",
                status="running",
                forced=True,
                started_at=datetime.now(UTC),
            )
            session.add(run)
            session.commit()
            run_id = run.id
            identifiers = rebuild_identifier_index(session, case)
            session.commit()
        try:
            counts = self._extract_and_resolve()
        except Exception as exc:
            self._finish_processing_run(run_id, status="failed", error=type(exc).__name__)
            raise
        self._finish_processing_run(
            run_id,
            status="completed",
            processed=sum(counts.values()),
            detail={"identifiers": identifiers, **counts, "retired": self.retired_citations},
        )
        return {"identifiers": identifiers, **counts, "retired": self.retired_citations}

    def _finish_processing_run(
        self,
        run_id: uuid.UUID,
        *,
        status: str,
        processed: int = 0,
        failed: int | None = None,
        error: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        with self.sessions() as session:
            run = session.get(ProcessingRun, run_id)
            assert run is not None
            run.status = status
            run.processed_count = processed
            run.failed_count = failed if failed is not None else (1 if status == "failed" else 0)
            run.finished_at = datetime.now(UTC)
            run.detail = {**(detail or {}), **({"error": error} if error else {})}
            session.commit()

    def _parse_all(
        self, run_id: uuid.UUID, version_ids: list[uuid.UUID], *, force: bool
    ) -> list[ParsedVersionResult]:
        """Each version parses in its own transaction. A failure is recorded and
        the batch continues: one bad PDF never aborts the others."""

        results: list[ParsedVersionResult] = []
        for version_id in version_ids:
            try:
                results.append(self._parse_version(version_id, force=force))
            except Exception as exc:  # noqa: BLE001 - isolated per version and recorded
                results.append(self._record_parse_failure(run_id, version_id, exc))
        return results

    def _record_parse_failure(
        self, run_id: uuid.UUID, version_id: uuid.UUID, exc: Exception
    ) -> ParsedVersionResult:
        """The version's own transaction was rolled back with its session, so
        none of its output was written. Record why, visibly, and move on."""

        error = f"{type(exc).__name__}: {exc}"[:500]
        with self.sessions() as session:
            version = session.get(DocumentVersion, version_id)
            ref = version.official_version_ref if version is not None else str(version_id)
            session.add(
                AuditLog(
                    actor="ksc-ingest-phase8",
                    action="document_version.parse_failed",
                    entity_type="document_version",
                    entity_id=str(version_id),
                    detail={
                        "official_version_ref": ref,
                        "processing_run_id": str(run_id),
                        "error": error,
                    },
                )
            )
            session.commit()
        log.warning("parse failed for %s: %s", ref, error)
        return ParsedVersionResult(
            official_version_ref=ref,
            pages=0,
            paragraphs=0,
            chunks=0,
            transcript_segments=0,
            requires_review=True,
            error=error,
        )

    def _parse_version(self, version_id: uuid.UUID, *, force: bool) -> ParsedVersionResult:
        with self.sessions() as session:
            version = session.get(DocumentVersion, version_id)
            if version is None or version.storage_key is None:
                raise LookupError(f"document version {version_id} has no held artifact")
            transcript = session.scalar(
                select(Transcript).where(Transcript.document_version_id == version.id)
            )
            if not force and (
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
            repair = version.official_version_ref in self.repair_structure
            unlinked = self._replace_parse(session, version, parsed, repair=repair)
            if repair:
                session.add(
                    AuditLog(
                        actor="ksc-ingest-phase8",
                        action="document_version.structure_repaired",
                        entity_type="document_version",
                        entity_id=str(version.id),
                        detail={
                            "official_version_ref": version.official_version_ref,
                            "parser": f"{PARSER_NAME}/{PARSER_VERSION}",
                            "ai_retrieval_sources_repointed": unlinked,
                        },
                    )
                )
            session.add(
                AuditLog(
                    actor="ksc-ingest-phase8",
                    action=("document_version.reprocessed" if force else "document_version.parsed"),
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
    def _replace_parse(
        session: Session, version: DocumentVersion, parsed: ParsedPdf, *, repair: bool = False
    ) -> int:
        """Reconcile stable parser rows without breaking downstream lineage.

        Once citations/findings/graph rows reference parser output, delete and
        reinsert is unsafe even when UUIDs are deterministic. Text and coordinate
        improvements update rows in place. A structural ID-set change fails
        closed and requires an explicit projection migration/review.

        Citable paragraph identity (¶ numbers) may change only under an explicit
        `repair`. Chunks and sections are derived search/display units: a new
        parser version may restructure them. Either way, AI retrieval rows that
        pointed at changed text are detached first and the count returned.
        """

        upgrade = version.parser_version != PARSER_VERSION
        removed: list[Any] = []
        transcript = session.scalar(
            select(Transcript).where(Transcript.document_version_id == version.id)
        )
        new_pages = [
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
        ]
        new_paragraphs = [
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
        ]
        new_sections = [
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
        ]
        new_chunks = [
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
        ]
        Phase8Pipeline._reconcile_rows(
            version.pages,
            new_pages,
            fields=(
                "pdf_page_index",
                "page_number",
                "printed_page_label",
                "text",
                "running_head",
                "has_redactions",
                "redaction_extents",
            ),
            label="pages",
        )
        Phase8Pipeline._reconcile_rows(
            version.paragraphs,
            new_paragraphs,
            fields=(
                "sequence",
                "paragraph_number",
                "pdf_page_index_from",
                "pdf_page_index_to",
                "page_from",
                "page_to",
                "text",
            ),
            label="paragraphs",
            removed=removed,
            allow_structure_change=repair,
        )
        Phase8Pipeline._reconcile_rows(
            version.sections,
            new_sections,
            fields=(
                "sequence",
                "level",
                "heading",
                "page_from",
                "page_to",
                "para_from",
                "para_to",
            ),
            label="sections",
            removed=removed,
            allow_structure_change=repair or upgrade,
        )
        Phase8Pipeline._reconcile_rows(
            version.chunks,
            new_chunks,
            fields=(
                "sequence",
                "chunk_kind",
                "pdf_page_index_from",
                "pdf_page_index_to",
                "page_from",
                "page_to",
                "para_from",
                "para_to",
                "text",
                "char_count",
            ),
            label="chunks",
            removed=removed,
            allow_structure_change=repair or upgrade,
        )
        if transcript is not None:
            transcript.page_from = parsed.page_from
            transcript.page_to = parsed.page_to
            transcript.text_extraction_method = TextExtractionMethod.NATIVE_TEXT
            new_segments = [
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
            ]
            Phase8Pipeline._reconcile_rows(
                transcript.segments,
                new_segments,
                fields=(
                    "sequence",
                    "pdf_page_index",
                    "page_number",
                    "line_from",
                    "line_to",
                    "speaker",
                    "speaker_role",
                    "examination_type",
                    "text",
                    "closed_session",
                ),
                label="transcript segments",
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
        session.flush()
        # New rows exist now: re-point AI retrieval rows that cited changed or
        # removed rows, then delete the removed rows.
        repointed = (
            Phase8Pipeline._repoint_ai_sources(session, version, removed)
            if repair or upgrade
            else 0
        )
        for row in removed:
            session.delete(row)
        session.flush()
        return repointed

    @staticmethod
    def _reconcile_rows(
        existing: list[Any],
        incoming: list[Any],
        *,
        fields: tuple[str, ...],
        label: str,
        removed: list[Any] | None = None,
        allow_structure_change: bool = False,
    ) -> None:
        if not existing:
            existing.extend(incoming)
            return
        current = {row.id: row for row in existing}
        proposed = {row.id: row for row in incoming}
        if current.keys() != proposed.keys():
            if not allow_structure_change:
                raise RuntimeError(
                    f"reprocessing changes stable {label} identity; "
                    "review/projection migration required"
                )
            # Park existing sequence numbers so updates and inserts never
            # collide with (version, sequence) uniqueness mid-flush.
            for index, row in enumerate(existing):
                if hasattr(row, "sequence"):
                    row.sequence = 1_000_000 + index
            session = object_session(existing[0])
            if session is not None:
                session.flush()
            if removed is not None:
                removed.extend(row for row in existing if row.id not in proposed)
        for row_id, candidate in proposed.items():
            row = current.get(row_id)
            if row is None:
                existing.append(candidate)
                continue
            for field in fields:
                setattr(row, field, getattr(candidate, field))

    @staticmethod
    def _repoint_ai_sources(session: Session, version: DocumentVersion, removed: list[Any]) -> int:
        """State-based and idempotent: every AI retrieval row linked to this
        version's paragraphs or chunks must point at a row whose text contains
        its verbatim excerpt. One that does not (the text changed, or the row is
        being removed) is re-pointed to the page-local chunk holding that exact
        excerpt, preferring the recorded PDF page; the previous ids and the
        reason go to its metadata. No match → the version fails closed."""

        removed_ids = {row.id for row in removed}
        chunks = [row for row in version.chunks if row.id not in removed_ids]
        rows: dict[uuid.UUID, DocumentChunk | DocumentParagraph] = {
            **{row.id: row for row in version.chunks},
            **{row.id: row for row in version.paragraphs},
        }
        repointed = 0
        for source in session.scalars(
            select(AiRetrievalSource).where(
                or_(
                    AiRetrievalSource.document_paragraph_id.in_(rows),
                    AiRetrievalSource.document_chunk_id.in_(rows),
                )
            )
        ):
            linked_id = source.document_chunk_id or source.document_paragraph_id
            linked = rows.get(linked_id) if linked_id is not None else None
            if (
                linked is not None
                and linked.id not in removed_ids
                and _holds_excerpt(linked.text, source.excerpt)
            ):
                continue
            matches = [chunk for chunk in chunks if _holds_excerpt(chunk.text, source.excerpt)]
            if not matches:
                raise RuntimeError(
                    f"AI retrieval source {source.id} excerpt not found in "
                    f"{version.official_version_ref}; review required"
                )
            target = next(
                (c for c in matches if c.pdf_page_index_from == source.pdf_page_index), matches[0]
            )
            source.source_metadata = {
                **(source.source_metadata or {}),
                "structure_repair": {
                    "parser": f"{PARSER_NAME}/{PARSER_VERSION}",
                    "previous_document_paragraph_id": str(source.document_paragraph_id)
                    if source.document_paragraph_id
                    else None,
                    "previous_document_chunk_id": str(source.document_chunk_id)
                    if source.document_chunk_id
                    else None,
                    "reason": "segmentation repaired; re-pointed by exact excerpt",
                },
            }
            source.document_paragraph_id = None
            source.document_chunk_id = target.id
            source.pdf_page_index = target.pdf_page_index_from
            repointed += 1
        session.flush()
        return repointed

    def repoint_ai_sources(self, version_refs: frozenset[str] | None = None) -> dict[str, int]:
        """Re-check every AI retrieval link of the held versions (or the named
        ones) against its excerpt; re-point stale links. Audited."""

        counts: dict[str, int] = {}
        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise LookupError(f"case {self.case_number} is not seeded")
            for version in session.scalars(select_processable_versions(case.id, parsed_only=True)):
                if version_refs and version.official_version_ref not in version_refs:
                    continue
                n = self._repoint_ai_sources(session, version, [])
                if n:
                    counts[version.official_version_ref] = n
                    session.add(
                        AuditLog(
                            actor="ksc-ingest-phase8",
                            action="ai_retrieval_sources.repointed",
                            entity_type="document_version",
                            entity_id=str(version.id),
                            detail={
                                "official_version_ref": version.official_version_ref,
                                "count": n,
                            },
                        )
                    )
            session.commit()
        return counts

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
        retired: list[uuid.UUID] = []
        with self.sessions() as session:
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise LookupError(f"case {self.case_number} is not seeded")
            versions = session.scalars(select_processable_versions(case.id, parsed_only=True)).all()
            for version in versions:
                existing_citations = {
                    citation.id: citation
                    for citation in session.scalars(
                        select(Citation).where(Citation.source_document_version_id == version.id)
                    ).all()
                }
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
                extracted_ids: set[uuid.UUID] = set()
                for text, source_page, pdf_page_index, source_segment_id in sources:
                    for extracted in extract_citations(text):
                        resolution = resolve_extracted(
                            session,
                            case,
                            extracted,
                            source_version_ref=version.official_version_ref,
                        )
                        citation_id = _stable_id(
                            version.id,
                            "citation",
                            pdf_page_index,
                            source_segment_id,
                            extracted.source_start,
                            extracted.source_end,
                            extracted.raw_text,
                        )
                        extracted_ids.add(citation_id)
                        citation = existing_citations.get(citation_id)
                        if citation is None:
                            citation = Citation(id=citation_id, case_id=case.id)
                            session.add(citation)
                            existing_citations[citation_id] = citation
                        citation.raw_text = extracted.raw_text
                        citation.normalized_text = normalize_for_storage(
                            extracted.normalized_identifier
                        )
                        citation.citation_type = extracted.citation_type
                        citation.source_document_version_id = version.id
                        citation.source_page = source_page
                        citation.source_pdf_page_index = pdf_page_index
                        citation.source_transcript_segment_id = source_segment_id
                        citation.source_char_start = extracted.source_start
                        citation.source_char_end = extracted.source_end
                        citation.source_url = version.source_url
                        citation.target_page = extracted.target_page
                        citation.target_para_from = extracted.target_para_from
                        citation.target_para_to = extracted.target_para_to
                        citation.target_line_from = extracted.target_line_from
                        citation.target_line_to = extracted.target_line_to
                        apply_resolution(citation, resolution)
                        counts[resolution.state.value] += 1
                retired.extend(
                    self._retire_stale_citations(
                        session,
                        [c for cid, c in existing_citations.items() if cid not in extracted_ids],
                    )
                )
                version.document.ingestion_state = DocumentIngestionState.INDEXED
            session.add(
                AuditLog(
                    actor="ksc-ingest-phase8",
                    action="citations.resolved",
                    entity_type="case",
                    entity_id=str(case.id),
                    detail={**counts, "retired": len(retired)},
                )
            )
            session.commit()
        self.retired_citations = len(retired)
        return counts

    @staticmethod
    def _retire_stale_citations(session: Session, stale: list[Citation]) -> list[uuid.UUID]:
        """Retire machine-extracted citations the current parser no longer produces.

        Only unreviewed rows are removed, each with an audit record. The one
        reference that may go with them is their own derived projection: an
        unreviewed, deterministic-citation edge, which `build-evidence` rebuilds
        from citations anyway. Any other reference (curated, human-reviewed,
        finding, appeal, AI, note, media) keeps the row for review.
        """

        retired: list[uuid.UUID] = []
        referencing = [
            column
            for table in Citation.metadata.sorted_tables
            for column in table.columns
            if column.table.name != "relationships"
            and any(fk.target_fullname == "citations.id" for fk in column.foreign_keys)
        ]
        for citation in stale:
            if citation.verification_state is not VerificationState.UNREVIEWED:
                continue
            if any(
                session.scalar(select(exists().where(column == citation.id)))
                for column in referencing
            ):
                continue
            edges = session.scalars(
                select(Relationship).where(Relationship.citation_id == citation.id)
            ).all()
            if any(
                edge.extraction_origin is not RelationshipOrigin.DETERMINISTIC_CITATION
                or edge.verification_state is not VerificationState.UNREVIEWED
                for edge in edges
            ):
                continue
            session.add(
                AuditLog(
                    actor="ksc-ingest-phase8",
                    action="citation.retired",
                    entity_type="citation",
                    entity_id=str(citation.id),
                    detail={
                        "reason": "no longer extracted by the current parser/resolver; "
                        "unreviewed and referenced only by its own derived edges",
                        "raw_text": citation.raw_text,
                        "normalized_text": citation.normalized_text,
                        "source_document_version_id": str(citation.source_document_version_id),
                        "source_pdf_page_index": citation.source_pdf_page_index,
                        "source_char_start": citation.source_char_start,
                        "source_char_end": citation.source_char_end,
                        "resolution_state": citation.resolution_state.value,
                        "derived_edges_removed": [str(edge.id) for edge in edges],
                    },
                )
            )
            for edge in edges:
                session.delete(edge)
            session.flush()
            session.delete(citation)
            retired.append(citation.id)
        return retired


def re_page_header(line: str) -> bool:
    return " of " in line or "PAGE " in line.upper() or "FAQE " in line.upper()


def normalize_for_storage(identifier: str) -> str:
    return " ".join(identifier.split()).upper()
