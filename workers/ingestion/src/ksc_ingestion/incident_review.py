"""First reviewed incident batch: SPO allegations from the Amended Indictment.

Writes only what the owner-directed review cleared, and nothing else:

- six incidents, each an SPO allegation as pleaded in the operative Amended
  Indictment KSC-BC-2020-06/F00999/A03 — never a Court finding and never a
  determination of anything;
- their villages and municipalities, named exactly as the source names them,
  with no coordinates and no derived geography;
- exact sources per incident: the operative F00999/A03 paragraphs (quoted
  verbatim, redactions as published), the superseded F00045/A03 paragraphs as
  version history, and the SPO's F03155/RED notice as withdrawal review.

Bare and Bajgorë/Bajgora are pleaded together in the same two paragraphs; each
incident quotes those same paragraphs and the review decision names the other,
so nothing is duplicated or split beyond what the source says.

INC-CAND-03 Drenoc/Drenovac (POSSIBLY_AFFECTED by F03155 item (b)) and
INC-CAND-08 Kleçkë/Klečka (CANNOT_DETERMINE under F03155 item (e)) stay held
and are not written. Every row has a deterministic id: a re-run replaces
exactly what it wrote. Anchors are built by `project-legal-matrix`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    AuditLog,
    Case,
    DatePrecision,
    DocumentParagraph,
    DocumentVersion,
    Incident,
    IncidentSource,
    Location,
    VerificationState,
)

_NS = uuid.UUID("5b0c7f0e-3d6a-4e1f-8a52-1f0d7c9e4b31")
_ORIGIN = "reviewed_incident_batch_1"
_REVIEWER = "owner-directed-incident-review"
_REVIEWED_AT = datetime(2026, 10, 4, tzinfo=UTC)
_ACTOR = "ksc-ingest-incident-review"

_CASE_PREFIX = "KSC-BC-2020-06"
OPERATIVE_REF = f"{_CASE_PREFIX}/F00999/A03"
HISTORY_REF = f"{_CASE_PREFIX}/F00045/A03"
WITHDRAWAL_REF = f"{_CASE_PREFIX}/F03155/RED"
_WITHDRAWAL_PARAGRAPH = 1
HELD_CANDIDATES = {
    "INC-CAND-03": "POSSIBLY_AFFECTED",
    "INC-CAND-08": "CANNOT_DETERMINE",
}


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(_NS, key)


@dataclass(frozen=True)
class _Place:
    slug: str
    name: str
    kind: str
    parent: str | None = None


# Names exactly as F00999/A03 writes them; variants are the halves of "A/B".
_PLACES = (
    _Place("gjakove-dakovica", "Gjakovë/Đakovica", "municipality"),
    _Place("drenas-gllogoc-glogovac", "Drenas (Gllogoc)/Glogovac", "municipality"),
    _Place("podujeve-podujevo", "Podujevë/Podujevo", "municipality"),
    _Place("prishtine-pristina", "Prishtinë/Priština", "municipality"),
    _Place("jabllanice-jablanica", "Jabllanicë/Jablanica", "village", "gjakove-dakovica"),
    _Place("llapushnik-lapusnik", "Llapushnik/Lapušnik", "village", "drenas-gllogoc-glogovac"),
    _Place("bare", "Bare", "village", "podujeve-podujevo"),
    _Place("bajgore-bajgora", "Bajgorë/Bajgora", "village", "podujeve-podujevo"),
    _Place("llapashtice-lapastica", "Llapashticë/Lapaštica", "village", "podujeve-podujevo"),
    _Place("zllash-zlas", "Zllash/Zlaš", "village", "prishtine-pristina"),
)


@dataclass(frozen=True)
class _Paragraph:
    number: int
    # A sub-heading the parser attaches to the paragraph's end (it opens the
    # next site's section); it is not part of the allegation and is not quoted.
    trailing_heading: str | None = None


@dataclass(frozen=True)
class _Candidate:
    key: str
    slug: str
    place: str
    operative: tuple[_Paragraph, ...]
    history: tuple[int, ...]
    date_as_pleaded: str
    date_from: date | None
    date_to: date | None
    date_precision: DatePrecision
    named_in_source: tuple[str, ...]
    units: tuple[str, ...]
    shares_source_with: str | None = None


_CANDIDATES = (
    _Candidate(
        "INC-CAND-01",
        "spo-allegation-f00999-a03-jabllanice-jablanica",
        "jabllanice-jablanica",
        (_Paragraph(63, "Llapushnik/Lapušnik"), _Paragraph(100, "Llapushnik/Lapušnik")),
        (61, 98),
        "Between at least April 1998 and late July 1998",
        date(1998, 4, 1),
        date(1998, 7, 31),
        DatePrecision.APPROXIMATE,
        ("Lahi BRAHIMAJ",),
        (),
    ),
    _Candidate(
        "INC-CAND-02",
        "spo-allegation-f00999-a03-llapushnik-lapusnik",
        "llapushnik-lapusnik",
        (_Paragraph(64, "Drenoc/Drenovac"), _Paragraph(101, "Drenoc/Drenovac")),
        (62, 99),
        "Between about late April 1998 and 25 or 26 July 1998",
        date(1998, 4, 1),
        date(1998, 7, 26),
        DatePrecision.APPROXIMATE,
        ("Fatmir LIMAJ", "Shukri BUJA"),
        (),
    ),
    _Candidate(
        "INC-CAND-04",
        "spo-allegation-f00999-a03-bare",
        "bare",
        (
            _Paragraph(70, "Llapashticë/Lapaštica and Related Sites"),
            _Paragraph(106, "Llapashticë/Lapaštica and Related Locations"),
        ),
        (67, 103),
        "In August 1998",
        date(1998, 8, 1),
        date(1998, 8, 31),
        DatePrecision.MONTH_ONLY,
        ("Rrustem MUSTAFA",),
        ("Llap Operational Zone",),
        "INC-CAND-05",
    ),
    _Candidate(
        "INC-CAND-05",
        "spo-allegation-f00999-a03-bajgore-bajgora",
        "bajgore-bajgora",
        (
            _Paragraph(70, "Llapashticë/Lapaštica and Related Sites"),
            _Paragraph(106, "Llapashticë/Lapaštica and Related Locations"),
        ),
        (67, 103),
        "Between August 1998 and mid-September 1998",
        date(1998, 8, 1),
        date(1998, 9, 30),
        DatePrecision.APPROXIMATE,
        ("Rrustem MUSTAFA",),
        ("Llap Operational Zone",),
        "INC-CAND-04",
    ),
    _Candidate(
        "INC-CAND-06",
        "spo-allegation-f00999-a03-llapashtice-lapastica",
        "llapashtice-lapastica",
        (_Paragraph(71), _Paragraph(107)),
        (68, 104),
        "Between at least November 1998 and March 1999",
        date(1998, 11, 1),
        date(1999, 3, 31),
        DatePrecision.APPROXIMATE,
        ("Rrustem MUSTAFA", "Latif GASHI"),
        ("Llap Operational Zone",),
    ),
    # Two separate periods are pleaded; one range would imply continuity, so
    # only the verbatim wording is kept.
    _Candidate(
        "INC-CAND-07",
        "spo-allegation-f00999-a03-zllash-zlas",
        "zllash-zlas",
        (_Paragraph(75), _Paragraph(109)),
        (72, 106),
        "In September 1998 and between approximately 1 and 19 April 1999",
        None,
        None,
        DatePrecision.UNKNOWN,
        (),
        ("BIA Guerilla unit", "Llap Operational Zone"),
    ),
)


def operative_excerpt(text: str, trailing_heading: str | None) -> str:
    """The paragraph as pleaded, without a parser-attached trailing sub-heading.
    Fails closed if a declared heading is not exactly where the review saw it."""

    if trailing_heading is None:
        return text
    suffix = f" {trailing_heading}"
    if not text.endswith(suffix):
        raise RuntimeError(f"expected trailing heading {trailing_heading!r} is not present")
    return text[: -len(suffix)]


@dataclass(frozen=True)
class IncidentReviewResult:
    incidents: int
    locations: int
    sources: int
    held: dict[str, str]


class ReviewedIncidentBatch:
    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def run(self) -> IncidentReviewResult:
        with self.sessions() as session, session.begin():
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise RuntimeError(f"case {self.case_number} is not seeded")
            operative = self._public_version(session, OPERATIVE_REF)
            history = self._public_version(session, HISTORY_REF)
            withdrawal = self._public_version(session, WITHDRAWAL_REF)

            self._clear(session)
            locations = self._locations(session, case.id)
            source_count = 0
            for candidate in _CANDIDATES:
                incident = self._incident(session, case.id, candidate, locations)
                source_count += self._sources(
                    session, incident, candidate, operative, history, withdrawal
                )
            session.add(
                AuditLog(
                    actor=_ACTOR,
                    action="incidents.reviewed_batch_written",
                    entity_type="case",
                    entity_id=self.case_number,
                    detail={
                        "source_category": "spo_allegation",
                        "operative_source": OPERATIVE_REF,
                        "version_history": HISTORY_REF,
                        "withdrawal_review": WITHDRAWAL_REF,
                        "written": [c.key for c in _CANDIDATES],
                        "held_not_written": HELD_CANDIDATES,
                        "locations": [p.slug for p in _PLACES],
                    },
                )
            )
            return IncidentReviewResult(
                incidents=len(_CANDIDATES),
                locations=len(locations),
                sources=source_count,
                held=dict(HELD_CANDIDATES),
            )

    # ----------------------------------------------------------- helpers --
    @staticmethod
    def _public_version(session: Session, ref: str) -> DocumentVersion:
        version = session.scalar(
            select(DocumentVersion).where(DocumentVersion.official_version_ref == ref)
        )
        if version is None or version.visibility.value not in {"public", "public_redacted"}:
            raise RuntimeError(f"required public source {ref} is not held")
        if version.parsed_at is None:
            raise RuntimeError(f"required public source {ref} is not parsed")
        return version

    @staticmethod
    def _clear(session: Session) -> None:
        incident_ids = [_id(f"incident:{c.key}") for c in _CANDIDATES]
        session.execute(delete(IncidentSource).where(IncidentSource.incident_id.in_(incident_ids)))
        session.execute(delete(Incident).where(Incident.id.in_(incident_ids)))
        villages = [_id(f"location:{p.slug}") for p in _PLACES if p.parent is not None]
        municipalities = [_id(f"location:{p.slug}") for p in _PLACES if p.parent is None]
        session.execute(delete(Location).where(Location.id.in_(villages)))
        session.execute(delete(Location).where(Location.id.in_(municipalities)))
        session.flush()

    @staticmethod
    def _locations(session: Session, case_id: uuid.UUID) -> dict[str, Location]:
        locations: dict[str, Location] = {}
        for place in _PLACES:  # municipalities first, so parents exist
            location = Location(
                id=_id(f"location:{place.slug}"),
                case_id=case_id,
                slug=place.slug,
                name=place.name,
                name_variants=[place.name, *place.name.split("/")]
                if "/" in place.name
                else [place.name],
                kind=place.kind,
                parent_location_id=locations[place.parent].id if place.parent else None,
                description=f"Named as written in {OPERATIVE_REF}. No coordinates recorded.",
            )
            session.add(location)
            session.flush()
            locations[place.slug] = location
        return locations

    @staticmethod
    def _incident(
        session: Session,
        case_id: uuid.UUID,
        candidate: _Candidate,
        locations: dict[str, Location],
    ) -> Incident:
        place = locations[candidate.place]
        paragraphs = ", ".join(f"¶{p.number}" for p in candidate.operative)
        decision: dict[str, Any] = {
            "candidate": candidate.key,
            "decision": "write",
            "source_category": "spo_allegation",
            "not_a_court_finding": True,
            "operative_source": OPERATIVE_REF,
            "operative_paragraphs": [p.number for p in candidate.operative],
            "version_history": {"source": HISTORY_REF, "paragraphs": list(candidate.history)},
            "withdrawal_review": {
                "source": WITHDRAWAL_REF,
                "paragraph": _WITHDRAWAL_PARAGRAPH,
                "status": "UNAFFECTED",
                "basis": (
                    "Items (a)-(e) of the SPO notice were checked against F00999/A03; none "
                    "concerns the paragraphs pleading this site."
                ),
            },
            "named_in_source": list(candidate.named_in_source),
            "units_in_source": list(candidate.units),
            "redactions": "preserved exactly as published",
        }
        if candidate.shares_source_with is not None:
            decision["shares_source_paragraphs_with"] = candidate.shares_source_with
        incident = Incident(
            id=_id(f"incident:{candidate.key}"),
            case_id=case_id,
            slug=candidate.slug,
            title=f"Alleged detention at {place.name} (SPO allegation)",
            summary=(
                f"SPO allegation as pleaded in the Amended Indictment, F00999/A03 {paragraphs}. "
                "Not a Court finding and not a determination."
            ),
            location_id=place.id,
            date_from=candidate.date_from,
            date_to=candidate.date_to,
            date_precision=candidate.date_precision,
            date_as_pleaded=candidate.date_as_pleaded,
            source_category="spo_allegation",
            review_decision=decision,
            extraction_origin=_ORIGIN,
            verification_state=VerificationState.HUMAN_VERIFIED,
            verified_by=_REVIEWER,
            verified_at=_REVIEWED_AT,
        )
        session.add(incident)
        session.flush()
        return incident

    @staticmethod
    def _paragraph(session: Session, version: DocumentVersion, number: int) -> DocumentParagraph:
        paragraph = session.scalar(
            select(DocumentParagraph).where(
                DocumentParagraph.document_version_id == version.id,
                DocumentParagraph.paragraph_number == number,
            )
        )
        if paragraph is None:
            raise RuntimeError(f"{version.official_version_ref} lacks ¶{number}")
        return paragraph

    def _sources(
        self,
        session: Session,
        incident: Incident,
        candidate: _Candidate,
        operative: DocumentVersion,
        history: DocumentVersion,
        withdrawal: DocumentVersion,
    ) -> int:
        place_name = incident.location.name if incident.location else ""
        rows: list[IncidentSource] = []
        for spec in candidate.operative:
            paragraph = self._paragraph(session, operative, spec.number)
            excerpt = operative_excerpt(paragraph.text, spec.trailing_heading)
            if place_name not in excerpt:
                raise RuntimeError(f"{OPERATIVE_REF} ¶{spec.number} does not name {place_name}")
            rows.append(
                self._row(incident, len(rows) + 1, "operative", operative, spec.number, excerpt)
            )
        for number in candidate.history:
            self._paragraph(session, history, number)
            rows.append(self._row(incident, len(rows) + 1, "version_history", history, number))
        self._paragraph(session, withdrawal, _WITHDRAWAL_PARAGRAPH)
        rows.append(
            self._row(
                incident,
                len(rows) + 1,
                "withdrawal_review",
                withdrawal,
                _WITHDRAWAL_PARAGRAPH,
                note="SPO notice of allegations no longer relied upon; none affects this site.",
            )
        )
        session.add_all(rows)
        session.flush()
        return len(rows)

    @staticmethod
    def _row(
        incident: Incident,
        sequence: int,
        role: str,
        version: DocumentVersion,
        paragraph_number: int,
        excerpt: str | None = None,
        note: str | None = None,
    ) -> IncidentSource:
        return IncidentSource(
            id=_id(f"incident-source:{incident.id}:{sequence}"),
            incident_id=incident.id,
            sequence=sequence,
            role=role,
            source_ref=version.official_version_ref,
            document_version_id=version.id,
            paragraph_number=paragraph_number,
            excerpt=excerpt,
            note=note
            or (
                "Superseded Indictment paragraph; version history only."
                if role == "version_history"
                else None
            ),
            verification_state=VerificationState.HUMAN_VERIFIED,
            verified_by=_REVIEWER,
            verified_at=_REVIEWED_AT,
        )
