"""Exhibit status history from explicit court-record statements (Phase 19B).

Only the bench (a role-qualified judge label) or the court officer can produce
an event, and only through a named pattern:

- ``number_assigned``: the court officer states the exhibit number, e.g. "will
  be assigned Exhibit P01137" / "do të marrë numrin e provës materiale P01137".
- ``admitted``: the bench states that an item has been admitted as a numbered
  exhibit, e.g. "Proofing Note 1 was admitted as Exhibit P01137" / "është
  pranuar si prova materiale P01137".

Party argument ("admitted through the bar table") and words like "admits"
never produce an event. A range ("P01136.1 to P01136.4") records its two
stated endpoints only. The identifier is kept verbatim; it binds to an exhibit
only when that exact (or zero-padded) identifier is already registered.

An exhibit's ``status`` is derived from its events: ``admitted`` when an
admission event exists, otherwise ``unknown``. A number assignment alone does
not establish admission. ``event_date`` is the date of the court-record
statement (the hearing), not an inferred admission date.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    Case,
    Document,
    DocumentVersion,
    Exhibit,
    ExhibitStatusEvent,
    Hearing,
    Transcript,
    TranscriptSegment,
    version_language,
)
from ksc_ingestion.identity import speaker_label_identity

RULE_VERSION = 1
_NS = uuid.UUID("e1b1719b-5a7e-4d3c-9e0f-19b0e5a7a7e5")
_ID = r"[PD]\d{4,5}(?:\.\d{1,2})?"
_COURT_OFFICER = re.compile(
    r"^(?:THE COURT OFFICER|SEKRETAR(?:I|JA)\s+(?:I|E)\s+(?:GJYKATËS|SEANCËS))$", re.I
)

_RULES: tuple[tuple[str, str, str, re.Pattern[str]], ...] = (
    (
        "exhibit.status.number_assigned.en",
        "number_assigned",
        "officer",
        re.compile(
            rf"\b(?:will|shall)\s+(?:then\s+)?be\s+(?:assigned|given)\s+"
            rf"(?:Exhibit|exhibit\s+number)\s+(?P<first>{_ID})\b"
        ),
    ),
    (
        "exhibit.status.number_assigned.sq",
        "number_assigned",
        "officer",
        re.compile(
            rf"\b[Dd]o\s+të\s+marr(?:ë|in)\s+numrin\s+e\s+provës\s+materiale\s+(?P<first>{_ID})\b"
        ),
    ),
    (
        "exhibit.status.admitted_statement.en",
        "admitted",
        "bench",
        re.compile(
            rf"\b(?:has|have|had)\s+been\s+admitted\s+as\s+(?:Exhibit\s+)?(?P<first>{_ID})"
            rf"(?:\s+to\s+(?P<last>{_ID}))?\b"
            rf"|\b(?:was|were)\s+admitted\s+(?:into\s+evidence\s+)?as\s+(?:Exhibit\s+)?"
            rf"(?P<first2>{_ID})(?:\s+to\s+(?P<last2>{_ID}))?\b"
        ),
    ),
    (
        "exhibit.status.admitted_statement.sq",
        "admitted",
        "bench",
        re.compile(
            rf"\b(?:(?:është|janë)\s+pranuar|u\s+pranua)(?:\s+tashmë)?\s+si\s+prov[ëa]\s+"
            rf"materiale\s+(?:si\s+)?(?P<first>{_ID})(?:\s+deri\s+në\s+(?P<last>{_ID}))?\b"
        ),
    ),
)
_CLASSIFICATION = re.compile(
    r"classified\s+as\s+(?P<en>confidential|public)|klasifiko(?:het|hen)\s+si\s+"
    r"(?P<sq>konfidenciale|publike)",
    re.I,
)
_SENTENCE_END = re.compile(r"[.;]\s")


@dataclass(frozen=True)
class StatusStatement:
    rule_id: str
    event_type: str
    identifier: str
    start: int
    end: int
    text: str
    classification: str | None


def speaker_role(speaker: str | None) -> str | None:
    """`bench` for a role-qualified judge label, `officer` for the court officer."""
    if not speaker:
        return None
    label = " ".join(speaker.split())
    if _COURT_OFFICER.match(label):
        return "officer"
    identity = speaker_label_identity(label)
    if identity is not None and identity[2] == "judge":
        return "bench"
    return None


def status_statements(text: str, role: str | None) -> Iterator[StatusStatement]:
    if role is None:
        return
    for rule_id, event_type, required_role, pattern in _RULES:
        if role != required_role:
            continue
        for match in pattern.finditer(text):
            end_of_sentence = _SENTENCE_END.search(text, match.end())
            sentence_tail = text[match.end() : end_of_sentence.start() if end_of_sentence else None]
            classification = None
            if event_type == "number_assigned":
                found = _CLASSIFICATION.search(sentence_tail)
                if found is not None:
                    value = (found.group("en") or found.group("sq")).lower()
                    classification = "public" if value in {"public", "publike"} else "confidential"
            for group in ("first", "last", "first2", "last2"):
                identifier = match.groupdict().get(group)
                if identifier:
                    yield StatusStatement(
                        rule_id=rule_id,
                        event_type=event_type,
                        identifier=identifier,
                        start=match.start(),
                        end=match.end(),
                        text=match.group(0),
                        classification=classification,
                    )


def _registered(identifier: str, registry: dict[str, uuid.UUID]) -> uuid.UUID | None:
    if identifier in registry:
        return registry[identifier]
    unpadded = re.fullmatch(r"([PD])(\d{4})", identifier)
    if unpadded is not None:
        return registry.get(f"{unpadded.group(1)}0{unpadded.group(2)}")
    return None


@dataclass(frozen=True)
class StatusResult:
    events: int
    bound_events: int
    unbound_identifiers: list[str]
    admitted_exhibits: int
    status_changes: dict[str, int]


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NS, ":".join(str(part) for part in parts))


def project_status_events(session: Session, case: Case, run_id: uuid.UUID) -> StatusResult:
    registry = {
        official: exhibit_id
        for official, exhibit_id in session.execute(
            select(Exhibit.official_exhibit_id, Exhibit.id).where(Exhibit.case_id == case.id)
        ).all()
    }
    session.execute(update(Exhibit).where(Exhibit.case_id == case.id).values(status_event_id=None))
    session.execute(delete(ExhibitStatusEvent).where(ExhibitStatusEvent.case_id == case.id))
    public = tuple(PUBLIC_VISIBILITIES)
    rows = session.execute(
        select(TranscriptSegment, Transcript, Hearing, DocumentVersion)
        .join(Transcript, Transcript.id == TranscriptSegment.transcript_id)
        .join(Hearing, Hearing.id == Transcript.hearing_id)
        .join(DocumentVersion, DocumentVersion.id == Transcript.document_version_id)
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(
            Hearing.case_id == case.id,
            Document.visibility.in_(public),
            DocumentVersion.visibility.in_(public),
            Transcript.visibility.in_(public),
            TranscriptSegment.closed_session.is_(False),
        )
        .order_by(DocumentVersion.official_version_ref, TranscriptSegment.sequence)
    ).all()
    events: list[ExhibitStatusEvent] = []
    unbound: set[str] = set()
    for segment, transcript, hearing, version in rows:
        for statement in status_statements(segment.text, speaker_role(segment.speaker)):
            exhibit_id = _registered(statement.identifier, registry)
            if exhibit_id is None:
                unbound.add(statement.identifier)
            event = ExhibitStatusEvent(
                id=_id(segment.id, statement.start, statement.identifier, statement.event_type),
                case_id=case.id,
                exhibit_id=exhibit_id,
                exhibit_identifier=statement.identifier,
                event_type=statement.event_type,
                classification=statement.classification,
                event_date=hearing.hearing_date,
                hearing_id=hearing.id,
                document_version_id=version.id,
                transcript_segment_id=segment.id,
                page_number=segment.page_number,
                pdf_page_index=segment.pdf_page_index,
                line_from=segment.line_from,
                line_to=segment.line_to,
                char_anchor="transcript_segment_text",
                char_start=statement.start,
                char_end=statement.end,
                occurrence_text=statement.text,
                speaker=segment.speaker,
                language=version_language(version.official_version_ref, transcript.language),
                rule_id=statement.rule_id,
                rule_version=RULE_VERSION,
                projection_run_id=run_id,
            )
            session.add(event)
            events.append(event)
    session.flush()

    # Derive current status from the history; unknown stays unknown.
    changes: dict[str, int] = {}
    admitted: dict[uuid.UUID, ExhibitStatusEvent] = {}
    for event in sorted(events, key=lambda row: (row.event_date or date.min, str(row.id))):
        if event.event_type == "admitted" and event.exhibit_id is not None:
            admitted.setdefault(event.exhibit_id, event)
    for exhibit in session.scalars(select(Exhibit).where(Exhibit.case_id == case.id)):
        admission = admitted.get(exhibit.id)
        new_status = "admitted" if admission is not None else "unknown"
        if exhibit.status != new_status:
            key = f"{exhibit.status}->{new_status}"
            changes[key] = changes.get(key, 0) + 1
        exhibit.status = new_status
        exhibit.status_event_id = admission.id if admission is not None else None
        # The event date is when the court *stated* the admission, which may be
        # later than the admission itself; the admission date stays unknown.
        exhibit.admitted_date = None
    session.flush()
    return StatusResult(
        events=len(events),
        bound_events=sum(event.exhibit_id is not None for event in events),
        unbound_identifiers=sorted(unbound),
        admitted_exhibits=len(admitted),
        status_changes=changes,
    )
