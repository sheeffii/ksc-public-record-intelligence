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
from datetime import UTC, date, datetime
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
    Hearing,
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
# An exhibit number keeps its sub-number: "P01136.1" is its own exhibit, never
# P01136. A base number is taken only when no ".<digit>" follows it, so a
# sub-number reference is never truncated to its base ("P00761.7_ET" → P00761.7).
_EXHIBIT_RE = re.compile(r"\bP\d{4,5}(?:\.\d{1,3}(?!\d)|\b(?!\.\d))", re.IGNORECASE)
_EXHIBIT_PART_RE = re.compile(r"^P\d{4,5}\.\d{1,3}$", re.IGNORECASE)
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
_DASH = "[-\u2010\u2011\u2013]"
# The case number of another court immediately before a bare identifier:
# "IT-04-84bis P00119" is ICTY Haradinaj's exhibit, "KSC-BC-2020-05 P00123" the
# Mustafa case's. Between them only a binding separator is allowed: whitespace,
# one comma or colon ("IT-04-84bis, P00119"), and parentheses around either side
# ("(IT-04-84) P00340", "IT-04-84 (P00340)"). A semicolon separates distinct
# citations, so an identifier after it is not bound to the earlier case.
_FOREIGN_CASE_BEFORE_RE = re.compile(
    rf"(?<![0-9A-Za-z])(?P<case>(?:IT|ICTR|MICT|IRMCT|STL|ICC|SCSL){_DASH}\d{{2}}{_DASH}\d{{1,3}}"
    rf"(?:\.\d+)?(?:bis|ter)?(?:{_DASH}[A-Z]{{1,3}}\d*)?|KSC-[A-Z]{{2}}-\d{{4}}-\d{{2}})"
    r"\)?[^\S\n]*[,:]?\s*\(?\s*$"
)


def foreign_case_before(text: str, start: int, case_number: str) -> str | None:
    """The other case whose number immediately precedes `text[start:]`, if any."""

    match = _FOREIGN_CASE_BEFORE_RE.search(text, max(0, start - 48), start)
    if match is None:
        return None
    foreign = re.sub(_DASH, "-", match.group("case"))
    return None if foreign.upper() == case_number.upper() else foreign


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
    # Case number printed immediately before a bare identifier (another court).
    preceding_case: str | None = None


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
    exhibit_id: uuid.UUID | None = None
    witness_id: uuid.UUID | None = None
    target_pdf_page_index: int | None = None
    # Machine-readable HOW: the named rule that produced this terminal state.
    rule: str = ""


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
                        preceding_case=(
                            foreign_case_before(text, match.start(), "")
                            if pattern is not _CASE_REF_RE
                            else None
                        ),
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
    tail = document.official_ref.split("/", 1)[-1]
    aliases = {document.official_ref, tail}
    # A bare filing number names the base filing only. Annexes (F00002/A01)
    # and subcase filings (IA042/F00002) carry it too but are not that filing.
    if document.filing_number and canonical_identifier(tail) == canonical_identifier(
        document.filing_number
    ):
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


_SUBCASE_SOURCE_RE = re.compile(r"/((?:IA|PL)\d{3})/", re.IGNORECASE)
_BARE_FILING_RE = re.compile(r"^F\d{5}(?:/|$)", re.IGNORECASE)
# The sub-number travels with the padded number: P1136.1 → P01136.1, never P01136.
_UNPADDED_RE = re.compile(r"^([WP])(\d{4})((?:\.\d{1,3})?)$", re.IGNORECASE)
_BASE_FILING_RE = re.compile(r"^((?:(?:IA|PL)\d{3}/)?F\d{5})", re.IGNORECASE)


def _hearing_date(value: int) -> date | None:
    """`T.20240429` cites a transcript by hearing date, never by page."""
    text = str(value)
    if len(text) != 8:
        return None
    try:
        parsed = date(int(text[:4]), int(text[4:6]), int(text[6:]))
    except ValueError:
        return None
    # The case record begins in 2020; a future date cannot be a held hearing.
    return parsed if date(2020, 1, 1) <= parsed <= datetime.now(UTC).date() else None


def _unresolved_rule(session: Session, case: Case, identifier: str) -> str:
    """Distinguish a held filing cited in an unheld version from an unheld target."""
    bare = canonical_identifier(identifier).removeprefix(f"{case.case_number.upper()}/")
    if _EXHIBIT_PART_RE.match(bare):
        # No registry row for this exact sub-number; the base exhibit is not it.
        return "unresolved.exhibit_part_not_registered"
    base = _BASE_FILING_RE.match(bare)
    if base is not None and base.group(1) != bare:
        rows = _candidate_rows(session, case, base.group(1))
        if any(row.entity_kind == EntityKind.DOCUMENT for row in rows):
            return "unresolved.version_not_held"
    return "unresolved.target_not_held"


def _resolve_by_hearing_date(
    session: Session, case: Case, hearing_day: date, source_version_ref: str
) -> Resolution:
    rows = session.execute(
        select(Transcript, DocumentVersion)
        .join(Hearing, Hearing.id == Transcript.hearing_id)
        .join(DocumentVersion, DocumentVersion.id == Transcript.document_version_id)
        .where(Hearing.case_id == case.id, Hearing.hearing_date == hearing_day)
    ).all()
    if not rows:
        return Resolution(
            ResolutionState.UNRESOLVED,
            ResolutionMethod.PATTERN,
            UNRESOLVED_DISPLAY,
            "no held transcript for the cited hearing date",
            rule="unresolved.transcript_date_not_held",
        )
    source_is_sqi = source_version_ref.upper().endswith("/SQI")
    matched = [
        (transcript, version)
        for transcript, version in rows
        if version.official_version_ref.upper().endswith("/SQI") == source_is_sqi
    ]
    if len(matched) != 1:
        return Resolution(
            ResolutionState.AMBIGUOUS,
            ResolutionMethod.PATTERN,
            UNRESOLVED_DISPLAY,
            "hearing date maps to several held transcript versions",
            sorted(version.official_version_ref for _, version in rows),
            rule="ambiguous.transcript_date",
        )
    transcript, version = matched[0]
    return Resolution(
        ResolutionState.RESOLVED,
        ResolutionMethod.PATTERN,
        f"{transcript.official_ref or version.official_version_ref} · {hearing_day.isoformat()}",
        "unique held transcript for the cited hearing date in the citing language",
        document_version_id=version.id,
        transcript_id=transcript.id,
        rule="transcript.hearing_date",
    )


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
            rule="invalid.other_case",
        )
    preceding = extracted.preceding_case
    if preceding and preceding.upper() != case.case_number.upper():
        return Resolution(
            ResolutionState.INVALID,
            ResolutionMethod.PATTERN,
            UNRESOLVED_DISPLAY,
            f"identifier follows the case number of a different case {preceding}",
            rule="invalid.other_case",
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
                rule="invalid.transcript_line_grid",
            )

    if identifier.startswith("T.") and extracted.target_page is not None:
        if extracted.target_page >= 10_000_000:
            hearing_day = _hearing_date(extracted.target_page)
            if hearing_day is not None:
                return _resolve_by_hearing_date(session, case, hearing_day, source_version_ref)
            return Resolution(
                ResolutionState.UNRESOLVED,
                ResolutionMethod.PATTERN,
                UNRESOLVED_DISPLAY,
                "transcript reference is neither a printed page nor a valid hearing date",
                rule="unresolved.malformed_transcript_reference",
            )
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
                rule="unresolved.transcript_page_not_held",
            )
        if len(transcripts) > 1:
            refs = sorted(t.official_ref or str(t.id) for t in transcripts)
            return Resolution(
                ResolutionState.AMBIGUOUS,
                ResolutionMethod.PATTERN,
                UNRESOLVED_DISPLAY,
                "printed transcript page occurs in more than one held transcript",
                refs,
                rule="ambiguous.transcript_page",
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
                    rule="invalid.transcript_line_missing",
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
            rule="transcript.page_line" if segment is not None else "transcript.page_range",
        )

    subcase = _SUBCASE_SOURCE_RE.search(source_version_ref)
    if subcase is not None and _BARE_FILING_RE.match(identifier):
        # Inside an appeal/other subcase filing a bare F-number may name the
        # subcase's own record or the main case's; the text does not say which.
        base = canonical_identifier(identifier)
        return Resolution(
            ResolutionState.AMBIGUOUS,
            ResolutionMethod.EXACT_ID,
            UNRESOLVED_DISPLAY,
            "bare filing number cited inside a subcase filing; main case vs subcase not stated",
            [
                f"{case.case_number}/{base}",
                f"{case.case_number}/{subcase.group(1).upper()}/{base}",
            ],
            rule="ambiguous.subcase_bare_filing",
        )
    rule = "identifier.exact"
    rows = _preferred_rows(_candidate_rows(session, case, identifier), identifier)
    unpadded = _UNPADDED_RE.match(identifier)
    if not rows and unpadded is not None:
        # P1070 / W4018 are the same official numbers as P01070 / W04018.
        padded = f"{unpadded.group(1).upper()}0{unpadded.group(2)}{unpadded.group(3)}"
        rows = _preferred_rows(_candidate_rows(session, case, padded), padded)
        rule = "identifier.zero_padded"
    if not rows:
        return Resolution(
            ResolutionState.UNRESOLVED,
            ResolutionMethod.EXACT_ID,
            UNRESOLVED_DISPLAY,
            "identifier is syntactically valid but is not in the controlled held corpus",
            rule=_unresolved_rule(session, case, identifier),
        )
    if len(rows) > 1:
        refs = sorted(row.identifier for row in rows)
        return Resolution(
            ResolutionState.AMBIGUOUS,
            ResolutionMethod.EXACT_ID,
            UNRESOLVED_DISPLAY,
            "identifier maps to multiple held records",
            refs,
            rule="ambiguous.identifier",
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
                rule="invalid.coordinate_missing",
            )
        if len(versions) > 1:
            refs = sorted(version.official_version_ref for version in versions)
            return Resolution(
                ResolutionState.AMBIGUOUS,
                ResolutionMethod.EXACT_ID,
                UNRESOLVED_DISPLAY,
                "coordinate exists in multiple held versions",
                refs,
                rule="ambiguous.coordinate_versions",
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
                rule="invalid.page_missing",
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
        exhibit_id=row.exhibit_id,
        witness_id=row.witness_id,
        target_pdf_page_index=page_row.pdf_page_index if page_row is not None else None,
        rule=rule,
    )


def apply_resolution(citation: Citation, resolution: Resolution) -> None:
    citation.resolution_state = resolution.state
    citation.resolution_method = resolution.method
    citation.display = resolution.display
    citation.resolution_detail = resolution.detail
    citation.resolution_rule = resolution.rule or None
    citation.candidate_identifiers = resolution.candidate_identifiers
    citation.target_document_id = resolution.document_id
    citation.target_document_version_id = resolution.document_version_id
    citation.target_transcript_id = resolution.transcript_id
    citation.target_transcript_segment_id = resolution.transcript_segment_id
    citation.target_exhibit_id = resolution.exhibit_id
    citation.target_witness_id = resolution.witness_id
    citation.target_pdf_page_index = resolution.target_pdf_page_index
    if resolution.state == ResolutionState.RESOLVED:
        citation.resolution_confidence = Decimal("1.00")
        citation.resolved_at = datetime.now(UTC)
    else:
        citation.resolution_confidence = None
        citation.resolved_at = None
