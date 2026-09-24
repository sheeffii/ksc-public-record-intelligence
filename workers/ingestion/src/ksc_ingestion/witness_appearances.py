"""Witness ↔ hearing linkage from transcript page headers (Phase 19B).

Official KSC transcripts print a running header on every page that states whose
evidence the page belongs to and the session state, e.g.
``Witness: W03877 (Open Session) Page 15003 Examination by Mr. Capin`` or
``Dëshmitari: W03877 (Seancë private) Faqe 61 Pyetje nga z. Capin``.

That header is the only signal accepted for an appearance. A code merely
mentioned in the transcript body is a mention, never an appearance. Pages
without the header are not bridged, and private or closed session content is
never read. A named header ("Witness: Nuredin Abazi") is an official public
identification; it creates or reuses a public person, never a witness code.
"""

from __future__ import annotations

import re
import uuid
from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    Case,
    Document,
    DocumentPage,
    DocumentVersion,
    Hearing,
    Person,
    PersonAlias,
    Transcript,
    Witness,
    WitnessAppearance,
)
from ksc_ingestion.identity import name_key

RULE_ID = "witness.transcript_page_header"
RULE_VERSION = 1
NAMED_ALIAS_RULE = "person.alias.transcript_witness_header"
_NS = uuid.UUID("1a9b0f19-bb19-4c6e-9d0a-19b0a9e0c0de")
HEADER_ZONE = 600

_SUBJECT = r"(?P<subject>W\d{5}|[A-ZÇË][a-zçë'\u2019-]+(?:\s+[A-ZÇË][a-zçë'\u2019-]+){1,3})"
HEADER = re.compile(
    r"(?P<label>Witness|D[ëe]shmitar(?:i|ja)?)\s*:\s*"
    + _SUBJECT
    + r"\s*(?P<quals>(?:\(\s*[^()\n]{2,40}?\s*\)\s*){1,3})"
)
_OPEN = re.compile(r"Open\s+Session|Seanc[ëe]\s+e\s+hapur", re.I)
_PRIVATE = re.compile(r"Private\s+Session|Seanc[ëe]\s+private", re.I)
_CLOSED = re.compile(r"Closed\s+Session|Seanc[ëe]\s+e\s+mbyllur", re.I)
_EXAMINATION = re.compile(
    r"^\s*(?:Page|Faqe)\s+\d+\s+(?P<exam>"
    r"(?:(?:Cross|Re|Further)-?\s*)?[Ee]xamination\s+by\s+(?:Mr|Ms|Mrs)\.\s*[A-Z][\w'\u2019-]+"
    r"|Questioned\s+by\s+the\s+(?:Trial\s+)?Panel"
    r"|Pyetje(?:\s+të\s+mëtejshme|\s+shtesë)?\s+nga\s+(?:z|znj)\.\s*[A-ZÇË][\w'\u2019-]+"
    r"|Pyetje\s+nga\s+Trupi\s+Gjykues)"
)


@dataclass(frozen=True)
class PageHeader:
    subject: str
    is_code: bool
    session: str  # open | private | closed
    start: int
    end: int
    subject_start: int
    subject_end: int
    text: str
    examination: str | None


def parse_page_header(page_text: str) -> PageHeader | None:
    """The page's witness header, only if it sits in the header zone and states a session."""
    zone = page_text[:HEADER_ZONE]
    match = HEADER.search(zone)
    if match is None:
        return None
    quals = match.group("quals")
    if _CLOSED.search(quals):
        session = "closed"
    elif _PRIVATE.search(quals):
        session = "private"
    elif _OPEN.search(quals):
        session = "open"
    else:
        return None
    subject = " ".join(match.group("subject").split())
    exam = _EXAMINATION.match(page_text[match.end() : match.end() + 200])
    return PageHeader(
        subject=subject,
        is_code=re.fullmatch(r"W\d{5}", subject) is not None,
        session=session,
        start=match.start(),
        # The span reproduces `text` exactly (no trailing whitespace).
        end=match.start() + len(match.group(0).rstrip()),
        subject_start=match.start("subject"),
        subject_end=match.end("subject"),
        text=match.group(0).rstrip(),
        examination=" ".join(exam.group("exam").split()) if exam else None,
    )


@dataclass
class _Aggregate:
    subject: str
    is_code: bool
    first: tuple[int, int | None, PageHeader]  # (pdf index, printed page, header)
    pages: list[int] = field(default_factory=list)
    sessions: Counter[str] = field(default_factory=Counter)
    examinations: dict[str, int | None] = field(default_factory=dict)


@dataclass(frozen=True)
class AppearanceResult:
    appearances: int
    code_witness_appearances: int
    named_person_appearances: int
    hearings_with_appearance: int
    unregistered_codes: list[str]
    named_people_created: int


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NS, ":".join(str(part) for part in parts))


def project_appearances(session: Session, case: Case, run_id: uuid.UUID) -> AppearanceResult:
    """Replace header-backed appearances for the case (idempotent ids)."""
    witness_ids = {
        code: witness_id
        for code, witness_id in session.execute(
            select(Witness.code, Witness.id).where(Witness.case_id == case.id)
        ).all()
    }
    session.execute(
        delete(WitnessAppearance).where(
            WitnessAppearance.rule_id == RULE_ID,
            WitnessAppearance.hearing_id.in_(select(Hearing.id).where(Hearing.case_id == case.id)),
        )
    )
    public = tuple(PUBLIC_VISIBILITIES)
    rows = session.execute(
        select(DocumentPage, Transcript, Hearing, DocumentVersion)
        .join(Transcript, Transcript.document_version_id == DocumentPage.document_version_id)
        .join(Hearing, Hearing.id == Transcript.hearing_id)
        .join(DocumentVersion, DocumentVersion.id == DocumentPage.document_version_id)
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(
            Hearing.case_id == case.id,
            Document.visibility.in_(public),
            DocumentVersion.visibility.in_(public),
            Transcript.visibility.in_(public),
            DocumentPage.text.is_not(None),
        )
        .order_by(DocumentVersion.official_version_ref, DocumentPage.pdf_page_index)
    ).all()

    groups: dict[tuple[uuid.UUID, str], _Aggregate] = {}
    context: dict[uuid.UUID, tuple[Transcript, Hearing, DocumentVersion]] = {}
    for page, transcript, hearing, version in rows:
        header = parse_page_header(page.text or "")
        if header is None:
            continue
        context[transcript.id] = (transcript, hearing, version)
        key = (transcript.id, header.subject)
        aggregate = groups.get(key)
        if aggregate is None:
            aggregate = groups[key] = _Aggregate(
                header.subject, header.is_code, (page.pdf_page_index, page.page_number, header)
            )
        if page.page_number is not None:
            aggregate.pages.append(page.page_number)
        aggregate.sessions[header.session] += 1
        if header.examination and header.examination not in aggregate.examinations:
            aggregate.examinations[header.examination] = page.page_number

    unregistered: set[str] = set()
    named_created = 0
    people: dict[str, uuid.UUID] = {}
    appearances = 0
    code_rows = 0
    named_rows = 0
    hearings: set[uuid.UUID] = set()
    for (transcript_id, subject), aggregate in sorted(
        groups.items(), key=lambda item: (str(item[0][0]), item[0][1])
    ):
        transcript, hearing, version = context[transcript_id]
        witness_id: uuid.UUID | None = None
        person_id: uuid.UUID | None = None
        pdf_index, printed, header = aggregate.first
        if aggregate.is_code:
            witness_id = witness_ids.get(subject)
            if witness_id is None:
                # Never auto-create a witness from a header; report it instead.
                unregistered.add(subject)
                continue
        else:
            subject_key = name_key(subject)
            person_id = people.get(subject_key)
            if person_id is None:
                slug = f"witness-{subject_key}"
                person = session.scalar(
                    select(Person).where(Person.case_id == case.id, Person.slug == slug)
                )
                if person is None:
                    person = Person(
                        id=_id("person", case.id, slug),
                        case_id=case.id,
                        slug=slug,
                        display_name=subject,
                        public_role="witness",
                    )
                    session.add(person)
                    session.flush()
                    named_created += 1
                person_id = people[subject_key] = person.id
            alias_text = subject
            if (
                session.scalar(
                    select(PersonAlias.id).where(
                        PersonAlias.person_id == person_id, PersonAlias.alias == alias_text
                    )
                )
                is None
            ):
                session.add(
                    PersonAlias(
                        id=_id("alias", person_id, alias_text),
                        person_id=person_id,
                        alias=alias_text,
                        language=transcript.language,
                        alias_kind="full_name",
                        source_document_version_id=version.id,
                        source_pdf_page_index=pdf_index,
                        source_char_start=header.subject_start,
                        source_char_end=header.subject_end,
                        rule_id=NAMED_ALIAS_RULE,
                    )
                )
                session.flush()
        session.add(
            WitnessAppearance(
                id=_id("appearance", transcript_id, subject),
                witness_id=witness_id,
                person_id=person_id,
                hearing_id=hearing.id,
                transcript_id=transcript_id,
                testimony_date=hearing.hearing_date,
                page_from=min(aggregate.pages) if aggregate.pages else None,
                page_to=max(aggregate.pages) if aggregate.pages else None,
                document_version_id=version.id,
                signal_pdf_page_index=pdf_index,
                signal_page_number=printed,
                signal_char_start=header.start,
                signal_char_end=header.end,
                signal_text=header.text,
                header_pages=sum(aggregate.sessions.values()),
                open_session_pages=aggregate.sessions["open"],
                private_session_pages=aggregate.sessions["private"],
                closed_session_pages=aggregate.sessions["closed"],
                examinations=[
                    {"text": text, "page": page} for text, page in aggregate.examinations.items()
                ],
                rule_id=RULE_ID,
                rule_version=RULE_VERSION,
                projection_run_id=run_id,
            )
        )
        appearances += 1
        code_rows += int(witness_id is not None)
        named_rows += int(person_id is not None)
        hearings.add(hearing.id)
    session.flush()
    return AppearanceResult(
        appearances=appearances,
        code_witness_appearances=code_rows,
        named_person_appearances=named_rows,
        hearings_with_appearance=len(hearings),
        unregistered_codes=sorted(unregistered),
        named_people_created=named_created,
    )
