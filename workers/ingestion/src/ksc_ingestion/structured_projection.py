"""Deterministic, public-only Phase 17C structured entity projection."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    Case,
    Citation,
    EntityKind,
    EntityOccurrence,
    Exhibit,
    IdentifierKind,
    Organization,
    Person,
    PersonAlias,
    RecordIdentifier,
    ResolutionState,
    Transcript,
    TranscriptSegment,
    Visibility,
    Witness,
    WitnessIdentityStatus,
    normalize_identifier,
)
from ksc_ingestion.identity import speaker_label_identity

_NS = uuid.UUID("8b407a92-23a8-4daf-9d36-5c577f88ac35")
_WITNESS = re.compile(r"^W\d{5}$", re.I)
_EXHIBIT = re.compile(r"^[PD]\d{5}$", re.I)

_ORGANIZATIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "kosovo-specialist-chambers",
        "Kosovo Specialist Chambers",
        ("Kosovo Specialist Chambers", "Dhomat e Specializuara të Kosovës"),
    ),
    (
        "specialist-prosecutors-office",
        "Specialist Prosecutor's Office",
        (
            "Specialist Prosecutor's Office",
            "Specialist Prosecutor\u2019s Office",
            "Zyra e Prokurorit të Specializuar",
        ),
    ),
    (
        "kosovo-liberation-army",
        "Kosovo Liberation Army",
        ("Kosovo Liberation Army", "Ushtria Çlirimtare e Kosovës"),
    ),
    ("united-nations", "United Nations", ("United Nations",)),
    ("nato", "NATO", ("NATO",)),
    ("osce", "OSCE", ("OSCE",)),
)


def _id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(_NS, ":".join(str(part) for part in parts))


# Speaker-label identity lives in `identity.py` (Phase 19B); kept importable here.
_person_identity = speaker_label_identity


@dataclass(frozen=True)
class StructuredProjectionResult:
    people: int
    witnesses: int
    organizations: int
    exhibits: int
    occurrences: int
    review_required: int


class Phase17StructuredPipeline:
    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def run(self) -> StructuredProjectionResult:
        with self.sessions() as session, session.begin():
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise RuntimeError(f"case {self.case_number} is not seeded")

            session.execute(
                delete(EntityOccurrence).where(
                    EntityOccurrence.case_id == case.id,
                    EntityOccurrence.extraction_origin == "phase17c",
                )
            )
            segments = session.execute(
                select(TranscriptSegment, Transcript)
                .join(Transcript, Transcript.id == TranscriptSegment.transcript_id)
                .where(
                    Transcript.visibility.in_(tuple(PUBLIC_VISIBILITIES)),
                    Transcript.document_version_id.is_not(None),
                    TranscriptSegment.closed_session.is_(False),
                )
                .order_by(TranscriptSegment.id)
            ).all()
            occurrences = 0
            review_count = 0

            people: dict[str, Person] = {}
            for segment, transcript in segments:
                if not segment.speaker:
                    continue
                identity = _person_identity(segment.speaker)
                if identity is None:
                    continue
                slug, display, role = identity
                person = people.get(slug)
                if person is None:
                    person = session.get(Person, _id("person", case.id, slug)) or Person(
                        id=_id("person", case.id, slug),
                        case_id=case.id,
                        slug=slug,
                        display_name=display,
                        public_role=role,
                    )
                    person.display_name, person.public_role = display, role
                    session.add(person)
                    people[slug] = person
                alias_id = _id("person-alias", person.id, segment.speaker)
                if session.get(PersonAlias, alias_id) is None:
                    session.add(
                        PersonAlias(
                            id=alias_id,
                            person_id=person.id,
                            alias=segment.speaker,
                            language=transcript.language,
                        )
                    )
                ambiguous = slug == "counsel_or_participant-smith"
                review_count += int(ambiguous)
                session.add(
                    EntityOccurrence(
                        id=_id("person-occurrence", person.id, segment.id),
                        case_id=case.id,
                        person_id=person.id,
                        document_version_id=transcript.document_version_id,
                        transcript_segment_id=segment.id,
                        page_number=segment.page_number,
                        pdf_page_index=segment.pdf_page_index,
                        line_from=segment.line_from,
                        line_to=segment.line_to,
                        char_start=0,
                        char_end=len(segment.speaker),
                        occurrence_text=segment.speaker,
                        extraction_origin="phase17c",
                        review_required=ambiguous,
                    )
                )
                occurrences += 1

            organizations: dict[str, Organization] = {}
            for segment, transcript in segments:
                for slug, name, aliases in _ORGANIZATIONS:
                    for alias in aliases:
                        for match in re.finditer(
                            rf"(?<!\w){re.escape(alias)}(?!\w)", segment.text, re.I
                        ):
                            organization = organizations.get(slug)
                            if organization is None:
                                organization = session.scalar(
                                    select(Organization).where(
                                        Organization.case_id == case.id,
                                        Organization.slug == slug,
                                    )
                                )
                                if organization is None:
                                    organization = Organization(
                                        id=_id("organization", case.id, slug),
                                        case_id=case.id,
                                        slug=slug,
                                        name=name,
                                        kind="public institution or organization",
                                        name_variants=list(aliases),
                                    )
                                organization.name = name
                                organization.name_variants = list(aliases)
                                session.add(organization)
                                session.flush()
                                organizations[slug] = organization
                            session.add(
                                EntityOccurrence(
                                    id=_id(
                                        "organization-occurrence",
                                        organization.id,
                                        segment.id,
                                        match.start(),
                                        match.end(),
                                    ),
                                    case_id=case.id,
                                    organization_id=organization.id,
                                    document_version_id=transcript.document_version_id,
                                    transcript_segment_id=segment.id,
                                    page_number=segment.page_number,
                                    pdf_page_index=segment.pdf_page_index,
                                    line_from=segment.line_from,
                                    line_to=segment.line_to,
                                    char_start=match.start(),
                                    char_end=match.end(),
                                    occurrence_text=match.group(0),
                                    extraction_origin="phase17c",
                                )
                            )
                            occurrences += 1

            citations = session.scalars(
                select(Citation)
                .where(
                    Citation.case_id == case.id,
                    Citation.resolution_state.in_(
                        [ResolutionState.UNRESOLVED, ResolutionState.RESOLVED]
                    ),
                    Citation.source_document_version_id.is_not(None),
                )
                .order_by(Citation.id)
            ).all()
            witnesses: dict[str, Witness] = {}
            exhibits: dict[str, Exhibit] = {}
            for citation in citations:
                identifier = (citation.normalized_text or "").upper()
                entity: Witness | Exhibit | None = None
                entity_field: str
                if _WITNESS.fullmatch(identifier):
                    entity = witnesses.get(identifier) or session.scalar(
                        select(Witness).where(
                            Witness.case_id == case.id, Witness.code == identifier
                        )
                    )
                    if entity is None:
                        entity = Witness(
                            id=_id("witness", case.id, identifier),
                            case_id=case.id,
                            code=identifier,
                            identity_status=WitnessIdentityStatus.PROTECTED_CODE,
                            protective_measures=[],
                        )
                        session.add(entity)
                    witnesses[identifier] = entity
                    entity_field = "witness_id"
                    kind, identifier_kind = EntityKind.WITNESS, IdentifierKind.WITNESS
                elif _EXHIBIT.fullmatch(identifier):
                    entity = exhibits.get(identifier) or session.scalar(
                        select(Exhibit).where(
                            Exhibit.case_id == case.id, Exhibit.official_exhibit_id == identifier
                        )
                    )
                    if entity is None:
                        # Status is never inferred from nearby words; explicit
                        # court-record events set it (exhibit_status.py).
                        entity = Exhibit(
                            id=_id("exhibit", case.id, identifier),
                            case_id=case.id,
                            official_exhibit_id=identifier,
                            title=f"Exhibit {identifier}",
                            status="unknown",
                            visibility=Visibility.PUBLIC,
                        )
                        session.add(entity)
                    exhibits[identifier] = entity
                    entity_field = "exhibit_id"
                    kind, identifier_kind = EntityKind.EXHIBIT, IdentifierKind.EXHIBIT
                else:
                    continue
                session.flush()
                normalized = normalize_identifier(identifier)
                existing_identifier = session.scalar(
                    select(RecordIdentifier).where(
                        RecordIdentifier.case_id == case.id,
                        RecordIdentifier.normalized_identifier == normalized,
                        RecordIdentifier.entity_kind == kind,
                    )
                )
                if existing_identifier is None:
                    session.add(
                        RecordIdentifier(
                            id=_id("identifier", case.id, kind.value, normalized),
                            case_id=case.id,
                            identifier=identifier,
                            normalized_identifier=normalized,
                            identifier_kind=identifier_kind,
                            entity_kind=kind,
                            is_primary=True,
                            **{entity_field: entity.id},
                        )
                    )
                kwargs = {entity_field: entity.id}
                session.add(
                    EntityOccurrence(
                        id=_id("citation-occurrence", entity.id, citation.id),
                        case_id=case.id,
                        document_version_id=citation.source_document_version_id,
                        transcript_segment_id=citation.source_transcript_segment_id,
                        page_number=citation.source_page,
                        pdf_page_index=citation.source_pdf_page_index,
                        char_start=citation.source_char_start or 0,
                        char_end=citation.source_char_end or len(citation.raw_text),
                        occurrence_text=citation.raw_text,
                        extraction_origin="phase17c",
                        **kwargs,
                    )
                )
                occurrences += 1

            session.flush()
            return StructuredProjectionResult(
                len(people),
                len(witnesses),
                len(organizations),
                len(exhibits),
                occurrences,
                review_count,
            )
