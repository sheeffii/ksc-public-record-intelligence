"""Citation extraction and deterministic persisted resolution (ADR-005).

Extraction preserves the exact matched source text. Resolution uses only held
record identifiers and parsed source coordinates; no fuzzy matching and no
model calls are involved. Plausible identifiers that are not held remain
UNRESOLVED. Contradictory case or impossible held coordinates are INVALID.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.models import (
    UNRESOLVED_DISPLAY,
    Case,
    Citation,
    CitationType,
    Document,
    DocumentPage,
    DocumentParagraph,
    DocumentVersion,
    EntityKind,
    IdentifierKind,
    RecordIdentifier,
    ResolutionMethod,
    ResolutionState,
    Transcript,
    TranscriptSegment,
    normalize_identifier,
)

_CASE_REF_RE = re.compile(
    r"\bKSC-[A-Z]+-\d{4}-\d{2}(?:/(?:(?:IA|PL)\d{3}|F\d{5}|RED2?|COR|sqi|A\d{2}))+\b",
    re.IGNORECASE,
)
_IA_REF_RE = re.compile(r"\b(?:IA|PL)\d{3}[-/]F\d{5}(?:CORRED|RED2?|/COR/RED|/RED2?)?\b", re.I)
_FILING_REF_RE = re.compile(
    r"\bF\d{5}(?:CORRED|RED2?|(?:/(?:COR|RED2?|sqi|A\d{2}))+)?\b", re.IGNORECASE
)
_WITNESS_RE = re.compile(r"\bW\d{4,5}\b", re.IGNORECASE)
_EXHIBIT_RE = re.compile(r"\bP\d{4,5}\b", re.IGNORECASE)
_TRANSCRIPT_RE = re.compile(
    r"\b(?:Transcript(?:\s+page)?|T\.)\s*([0-9]+(?:[ ,][0-9]{3})*)"
    r"(?:\s*[:,]\s*(?:lines?|ll?\.)?\s*(\d{1,2})(?:\s*[-\u2013]\s*(\d{1,2}))?)?",
    re.IGNORECASE,
)
_PARA_AFTER_RE = re.compile(
    r"^[\s,;()]*\b(?:paras?\.?|paragraphs?|¶)\s*(\d+)"
    r"(?:\s*[-\u2013]\s*(\d+))?",
    re.IGNORECASE,
)
_PAGE_AFTER_RE = re.compile(r"^[\s,;()]*\b(?:p\.|page)\s*(\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ExtractedCitation:
    raw_text: str
    normalized_identifier: str
    citation_type: CitationType
    target_page: int | None = None
    target_para_from: int | None = None
    target_para_to: int | None = None
    target_line_from: int | None = None
    target_line_to: int | None = None
    source_start: int = 0
    source_end: int = 0


@dataclass(frozen=True)
class Resolution:
    state: ResolutionState
    method: ResolutionMethod
    display: str
    detail: str
    candidate_identifiers: list[str] | None = None
    document_id: uuid.UUID | None = None
    document_version_id: uuid.UUID | None = None
    transcript_id: uuid.UUID | None = None
    transcript_segment_id: uuid.UUID | None = None
    target_pdf_page_index: int | None = None


def canonical_identifier(raw: str) -> str:
    compact = raw.strip().strip(".,;:()[]{}'").replace("\N{EN DASH}", "-")
    compact = re.sub(r"\s+", "", compact).upper()
    compact = compact.replace("-F", "/F") if compact.startswith(("IA", "PL")) else compact
    compact = compact.replace("CORRED", "/COR/RED")
    compact = re.sub(r"(?<!/)RED2$", "/RED2", compact)
    compact = re.sub(r"(?<!/)RED$", "/RED", compact)
    compact = re.sub(r"/+", "/", compact)
    return compact


def _coordinates_after(text: str, end: int) -> tuple[int | None, int | None, int | None, int]:
    tail = text[end : end + 96]
    paragraph = _PARA_AFTER_RE.match(tail)
    if paragraph is not None:
        start = int(paragraph.group(1))
        return None, start, int(paragraph.group(2) or start), end + paragraph.end()
    page = _PAGE_AFTER_RE.match(tail)
    if page is not None:
        return int(page.group(1)), None, None, end + page.end()
    return None, None, None, end


def extract_citations(text: str) -> list[ExtractedCitation]:
    """Extract non-overlapping identifier and transcript-coordinate references."""
    candidates: list[tuple[int, int, ExtractedCitation]] = []
    identifier_patterns = (
        (_CASE_REF_RE, CitationType.DOCUMENT_VERSION),
        (_IA_REF_RE, CitationType.DOCUMENT_VERSION),
        (_FILING_REF_RE, CitationType.DOCUMENT),
        (_WITNESS_RE, CitationType.WITNESS),
        (_EXHIBIT_RE, CitationType.EXHIBIT),
    )
    for pattern, base_type in identifier_patterns:
        for match in pattern.finditer(text):
            target_page, para_from, para_to, raw_end = _coordinates_after(text, match.end())
            identifier = canonical_identifier(match.group(0))
            citation_type = base_type
            if para_from is not None:
                citation_type = CitationType.PARAGRAPH
            elif target_page is not None:
                citation_type = CitationType.PAGE
            elif "/" in identifier.removeprefix("KSC-BC-2020-06/"):
                citation_type = CitationType.DOCUMENT_VERSION
            candidates.append(
                (
                    match.start(),
                    raw_end,
                    ExtractedCitation(
                        raw_text=text[match.start() : raw_end].strip(),
                        normalized_identifier=identifier,
                        citation_type=citation_type,
                        target_page=target_page,
                        target_para_from=para_from,
                        target_para_to=para_to,
                        source_start=match.start(),
                        source_end=raw_end,
                    ),
                )
            )
    for match in _TRANSCRIPT_RE.finditer(text):
        page = int(re.sub(r"[ ,]", "", match.group(1)))
        line_from = int(match.group(2)) if match.group(2) else None
        line_to = int(match.group(3) or match.group(2)) if match.group(2) else None
        candidates.append(
            (
                match.start(),
                match.end(),
                ExtractedCitation(
                    raw_text=match.group(0).strip(),
                    normalized_identifier=f"T.{page}",
                    citation_type=(
                        CitationType.TRANSCRIPT_LINE
                        if line_from is not None
                        else CitationType.TRANSCRIPT
                    ),
                    target_page=page,
                    target_line_from=line_from,
                    target_line_to=line_to,
                    source_start=match.start(),
                    source_end=match.end(),
                ),
            )
        )

    # Prefer the longest candidate at a start position, then suppress nested
    # forms (the bare F-number inside a full KSC reference, for example).
    selected: list[ExtractedCitation] = []
    occupied_until = -1
    for start, end, citation in sorted(candidates, key=lambda row: (row[0], -(row[1] - row[0]))):
        if start < occupied_until:
            continue
        selected.append(citation)
        occupied_until = end
    return selected


def _identifier_aliases(document: Document) -> set[str]:
    aliases = {document.official_ref, document.official_ref.split("/", 1)[-1]}
    if document.filing_number:
        aliases.add(document.filing_number)
    return {canonical_identifier(alias) for alias in aliases}


def _version_aliases(version: DocumentVersion) -> set[str]:
    full = canonical_identifier(version.official_version_ref)
    aliases = {full, full.split("/", 1)[-1]}
    tail = full.split("/", 1)[-1]
    if not tail.endswith("/SQI"):
        compact = tail.replace("/COR/RED", "CORRED")
        compact = compact.replace("/RED2", "RED2").replace("/RED", "RED")
        if compact.startswith(("IA", "PL")):
            compact = compact.replace("/F", "-F", 1)
        aliases.add(compact)
    return aliases


def rebuild_identifier_index(session: Session, case: Case) -> int:
    """Rebuild deterministic aliases for held documents, versions and transcripts."""
    rows = session.scalars(
        select(RecordIdentifier).where(
            RecordIdentifier.case_id == case.id,
            RecordIdentifier.entity_kind.in_(
                [EntityKind.DOCUMENT, EntityKind.DOCUMENT_VERSION, EntityKind.TRANSCRIPT]
            ),
        )
    ).all()
    for row in rows:
        session.delete(row)
    session.flush()
    count = 0
    seen: set[tuple[str, EntityKind]] = set()

    def add(
        identifier: str,
        kind: IdentifierKind,
        entity_kind: EntityKind,
        *,
        document: Document | None = None,
        version: DocumentVersion | None = None,
        transcript: Transcript | None = None,
        primary: bool,
    ) -> None:
        nonlocal count
        normalized = normalize_identifier(canonical_identifier(identifier))
        key = (normalized, entity_kind)
        if key in seen:
            return
        seen.add(key)
        session.add(
            RecordIdentifier(
                case_id=case.id,
                identifier=identifier,
                normalized_identifier=normalized,
                identifier_kind=kind,
                entity_kind=entity_kind,
                is_primary=primary,
                document_id=document.id if document is not None else None,
                document_version_id=version.id if version is not None else None,
                transcript_id=transcript.id if transcript is not None else None,
            )
        )
        count += 1

    documents = session.scalars(
        select(Document).where(Document.case_id == case.id).order_by(Document.official_ref)
    ).all()
    for document in documents:
        for alias in sorted(_identifier_aliases(document)):
            add(
                alias,
                IdentifierKind.FILING,
                EntityKind.DOCUMENT,
                document=document,
                primary=alias == canonical_identifier(document.official_ref),
            )
        for version in document.versions:
            for alias in sorted(_version_aliases(version)):
                add(
                    alias,
                    IdentifierKind.FILING_VERSION,
                    EntityKind.DOCUMENT_VERSION,
                    version=version,
                    primary=alias == canonical_identifier(version.official_version_ref),
                )
    transcripts = session.scalars(
        select(Transcript)
        .join(Transcript.hearing)
        .where(Transcript.hearing.has(case_id=case.id))
        .order_by(Transcript.official_ref)
    ).all()
    for transcript in transcripts:
        if transcript.official_ref:
            full = canonical_identifier(transcript.official_ref)
            for alias in {full, full.split("/", 1)[-1]}:
                add(
                    alias,
                    IdentifierKind.TRANSCRIPT,
                    EntityKind.TRANSCRIPT,
                    transcript=transcript,
                    primary=alias == full,
                )
    session.flush()
    return count


def _candidate_rows(session: Session, case: Case, identifier: str) -> list[RecordIdentifier]:
    normalized = normalize_identifier(canonical_identifier(identifier))
    exact = session.scalars(
        select(RecordIdentifier).where(
            RecordIdentifier.case_id == case.id,
            RecordIdentifier.normalized_identifier == normalized,
        )
    ).all()
    if exact:
        return list(exact)
    if not normalized.startswith(f"{case.case_number}/"):
        with_case = normalize_identifier(f"{case.case_number}/{normalized}")
        return list(
            session.scalars(
                select(RecordIdentifier).where(
                    RecordIdentifier.case_id == case.id,
                    RecordIdentifier.normalized_identifier == with_case,
                )
            ).all()
        )
    return []


def _preferred_rows(rows: list[RecordIdentifier], identifier: str) -> list[RecordIdentifier]:
    normalized = canonical_identifier(identifier)
    version_specific = "/RED" in normalized or "/COR" in normalized or "/SQI" in normalized
    if version_specific:
        versions = [row for row in rows if row.entity_kind == EntityKind.DOCUMENT_VERSION]
        return versions or rows
    documents = [row for row in rows if row.entity_kind == EntityKind.DOCUMENT]
    return documents or rows


def _version_for_document_coordinate(
    session: Session,
    document_id: uuid.UUID,
    source_version_ref: str,
    *,
    page: int | None,
    paragraph: int | None,
) -> list[DocumentVersion]:
    stmt = select(DocumentVersion).where(DocumentVersion.document_id == document_id)
    versions = list(session.scalars(stmt).all())
    source_is_sqi = source_version_ref.upper().endswith("/SQI")
    language_matched = [
        version
        for version in versions
        if version.official_version_ref.upper().endswith("/SQI") == source_is_sqi
    ]
    pool = language_matched or versions
    if paragraph is not None:
        ids = set(
            session.scalars(
                select(DocumentParagraph.document_version_id).where(
                    DocumentParagraph.document_version_id.in_([version.id for version in pool]),
                    DocumentParagraph.paragraph_number == paragraph,
                )
            ).all()
        )
        pool = [version for version in pool if version.id in ids]
    if page is not None:
        ids = set(
            session.scalars(
                select(DocumentPage.document_version_id).where(
                    DocumentPage.document_version_id.in_([version.id for version in pool]),
                    DocumentPage.page_number == page,
                )
            ).all()
        )
        pool = [version for version in pool if version.id in ids]
    return pool


def resolve_extracted(
    session: Session,
    case: Case,
    extracted: ExtractedCitation,
    *,
    source_version_ref: str,
) -> Resolution:
    identifier = extracted.normalized_identifier
    case_match = re.match(r"^(KSC-[A-Z]+-\d{4}-\d{2})/", identifier, re.I)
    if case_match and case_match.group(1).upper() != case.case_number.upper():
        return Resolution(
            ResolutionState.INVALID,
            ResolutionMethod.PATTERN,
            UNRESOLVED_DISPLAY,
            f"reference names different case {case_match.group(1)}",
        )
    if extracted.target_line_from is not None:
        if (
            extracted.target_line_from < 1
            or extracted.target_line_to is None
            or extracted.target_line_to > 25
            or extracted.target_line_to < extracted.target_line_from
        ):
            return Resolution(
                ResolutionState.INVALID,
                ResolutionMethod.PATTERN,
                UNRESOLVED_DISPLAY,
                "transcript line range is outside the printed 1-25 line grid",
            )

    if identifier.startswith("T.") and extracted.target_page is not None:
        transcripts = list(
            session.scalars(
                select(Transcript).where(
                    Transcript.page_from <= extracted.target_page,
                    Transcript.page_to >= extracted.target_page,
                )
            ).all()
        )
        transcripts = [t for t in transcripts if t.hearing.case_id == case.id]
        if not transcripts:
            return Resolution(
                ResolutionState.UNRESOLVED,
                ResolutionMethod.PATTERN,
                UNRESOLVED_DISPLAY,
                "no held transcript contains the printed page",
            )
        if len(transcripts) > 1:
            refs = sorted(t.official_ref or str(t.id) for t in transcripts)
            return Resolution(
                ResolutionState.AMBIGUOUS,
                ResolutionMethod.PATTERN,
                UNRESOLVED_DISPLAY,
                "printed transcript page occurs in more than one held transcript",
                refs,
            )
        transcript = transcripts[0]
        segment = None
        if extracted.target_line_from is not None:
            segment = session.scalar(
                select(TranscriptSegment).where(
                    TranscriptSegment.transcript_id == transcript.id,
                    TranscriptSegment.page_number == extracted.target_page,
                    TranscriptSegment.line_from <= extracted.target_line_from,
                    TranscriptSegment.line_to >= extracted.target_line_from,
                )
            )
            if (
                segment is None
                or segment.line_to is None
                or (
                    extracted.target_line_to is not None
                    and segment.line_to < extracted.target_line_to
                )
            ):
                return Resolution(
                    ResolutionState.INVALID,
                    ResolutionMethod.PATTERN,
                    UNRESOLVED_DISPLAY,
                    "held transcript does not contain the requested line range",
                )
        display = f"{transcript.official_ref} · p. {extracted.target_page}"
        if extracted.target_line_from is not None:
            display += f", lines {extracted.target_line_from}\N{EN DASH}{extracted.target_line_to}"
        return Resolution(
            ResolutionState.RESOLVED,
            ResolutionMethod.PATTERN,
            display,
            "unique held transcript page/line match",
            document_version_id=transcript.document_version_id,
            transcript_id=transcript.id,
            transcript_segment_id=segment.id if segment is not None else None,
            target_pdf_page_index=(segment.pdf_page_index if segment is not None else None),
        )

    rows = _preferred_rows(_candidate_rows(session, case, identifier), identifier)
    if not rows:
        return Resolution(
            ResolutionState.UNRESOLVED,
            ResolutionMethod.EXACT_ID,
            UNRESOLVED_DISPLAY,
            "identifier is syntactically valid but is not in the controlled held corpus",
        )
    if len(rows) > 1:
        refs = sorted(row.identifier for row in rows)
        return Resolution(
            ResolutionState.AMBIGUOUS,
            ResolutionMethod.EXACT_ID,
            UNRESOLVED_DISPLAY,
            "identifier maps to multiple held records",
            refs,
        )
    row = rows[0]
    document_id = row.document_id
    version_id = row.document_version_id
    if document_id is not None and (
        extracted.target_page is not None or extracted.target_para_from is not None
    ):
        versions = _version_for_document_coordinate(
            session,
            document_id,
            source_version_ref,
            page=extracted.target_page,
            paragraph=extracted.target_para_from,
        )
        if not versions:
            return Resolution(
                ResolutionState.INVALID,
                ResolutionMethod.EXACT_ID,
                UNRESOLVED_DISPLAY,
                "held document has no parsed target at the requested coordinate",
            )
        if len(versions) > 1:
            refs = sorted(version.official_version_ref for version in versions)
            return Resolution(
                ResolutionState.AMBIGUOUS,
                ResolutionMethod.EXACT_ID,
                UNRESOLVED_DISPLAY,
                "coordinate exists in multiple held versions",
                refs,
            )
        version_id = versions[0].id
    page_row = None
    if version_id is not None and extracted.target_page is not None:
        page_row = session.scalar(
            select(DocumentPage).where(
                DocumentPage.document_version_id == version_id,
                DocumentPage.page_number == extracted.target_page,
            )
        )
        if page_row is None:
            return Resolution(
                ResolutionState.INVALID,
                ResolutionMethod.EXACT_ID,
                UNRESOLVED_DISPLAY,
                "held version has no requested printed page",
            )
    ref = row.identifier
    display = ref
    if extracted.target_para_from is not None:
        display += f" · ¶{extracted.target_para_from}"
        if extracted.target_para_to != extracted.target_para_from:
            display += f"\N{EN DASH}{extracted.target_para_to}"
    elif extracted.target_page is not None:
        display += f" · p. {extracted.target_page}"
    return Resolution(
        ResolutionState.RESOLVED,
        ResolutionMethod.EXACT_ID,
        display,
        "unique exact identifier match with validated held coordinate",
        document_id=document_id,
        document_version_id=version_id,
        transcript_id=row.transcript_id,
        target_pdf_page_index=page_row.pdf_page_index if page_row is not None else None,
    )


def apply_resolution(citation: Citation, resolution: Resolution) -> None:
    citation.resolution_state = resolution.state
    citation.resolution_method = resolution.method
    citation.display = resolution.display
    citation.resolution_detail = resolution.detail
    citation.candidate_identifiers = resolution.candidate_identifiers
    citation.target_document_id = resolution.document_id
    citation.target_document_version_id = resolution.document_version_id
    citation.target_transcript_id = resolution.transcript_id
    citation.target_transcript_segment_id = resolution.transcript_segment_id
    citation.target_pdf_page_index = resolution.target_pdf_page_index
    if resolution.state == ResolutionState.RESOLVED:
        citation.resolution_confidence = Decimal("1.00")
        citation.resolved_at = datetime.now(UTC)
    else:
        citation.resolution_confidence = None
        citation.resolved_at = None
