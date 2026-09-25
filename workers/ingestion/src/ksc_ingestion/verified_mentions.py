"""Phase 19A deterministic verified-mention projection.

A verified mention is a persisted `entity_occurrences` row that says: this exact
character range, in this exact public source version, refers to this exact
registered entity, by this named deterministic rule. Anything weaker is either
written as `review_required` or not written at all and left to lexical search.

Rules never create entities: a code, identifier, name or label that is not
already in the case registry produces no row. No fuzzy, phonetic or model-based
matching. Exhibit status is never read or written here.
"""

from __future__ import annotations

import re
import uuid
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    Case,
    Document,
    DocumentPage,
    DocumentParagraph,
    DocumentVersion,
    EntityOccurrence,
    Exhibit,
    Organization,
    Person,
    PersonAlias,
    ProcessingRun,
    Transcript,
    TranscriptSegment,
    Witness,
    version_language,
)
from ksc_ingestion.citation_resolution import foreign_case_before
from ksc_ingestion.identity import (
    NAMED_ROLES,
    classify_label,
    slug_role_and_key,
    speaker_label_identity,
)

PROCESSOR = "phase19a-mentions"
PROCESSOR_VERSION = "1"
_NS = uuid.UUID("5f0c5d0e-7c62-4d1c-9a55-19a0a0e0b19a")

VERIFIED = "verified"
REVIEW_REQUIRED = "review_required"

SEGMENT_TEXT = "transcript_segment_text"
SPEAKER_LABEL = "transcript_speaker_label"
PAGE_TEXT = "document_page_text"

# rule_id -> (rule_version, mention_state it produces)
RULES: dict[str, tuple[int, str]] = {
    "witness.code.exact": (1, VERIFIED),
    # v2: an identifier printed right after another court's case number
    # ("IT-04-84 P00340") belongs to that case and is not a mention (Phase 19C).
    # v3: the same with a binding comma, colon or parentheses ("IT-04-84bis, P00119").
    "exhibit.identifier.exact": (3, VERIFIED),
    "organization.name.exact": (1, VERIFIED),
    "organization.acronym.exact": (1, VERIFIED),
    "organization.variant.shared": (1, REVIEW_REQUIRED),
    "person.speaker_label.role_qualified": (1, VERIFIED),
    "person.speaker_label.honorific": (1, REVIEW_REQUIRED),
    "person.speaker_label.shared_surname": (1, REVIEW_REQUIRED),
    "person.full_name.exact": (1, VERIFIED),
}

WITNESS_CODE = re.compile(r"(?<![0-9A-Za-z])W\d{5}(?![0-9A-Za-z]|\.\d)")
EXHIBIT_ID = re.compile(r"(?<![0-9A-Za-z])[PD]\d{5}(?![0-9A-Za-z]|\.\d)")
_ACRONYM = re.compile(r"^[A-ZÇË]{2,6}$")


@dataclass(frozen=True)
class Anchor:
    """One public text a mention's character range indexes into."""

    kind: str
    text: str
    document_version_id: uuid.UUID
    language: str | None
    transcript_segment_id: uuid.UUID | None = None
    page_number: int | None = None
    pdf_page_index: int | None = None
    line_from: int | None = None
    line_to: int | None = None
    # (char_start, char_end, paragraph_number) spans located exactly in `text`.
    paragraphs: tuple[tuple[int, int, int], ...] = ()

    @property
    def key(self) -> str:
        if self.transcript_segment_id is not None:
            return f"{self.kind}:{self.transcript_segment_id}"
        return f"{self.kind}:{self.document_version_id}:{self.pdf_page_index}"

    def paragraph_at(self, start: int, end: int) -> int | None:
        for para_start, para_end, number in self.paragraphs:
            if para_start <= start and end <= para_end:
                return number
        return None


@dataclass(frozen=True)
class Mention:
    entity_field: str
    entity_id: uuid.UUID
    rule_id: str
    char_start: int
    char_end: int
    text: str

    @property
    def state(self) -> str:
        return RULES[self.rule_id][1]


@dataclass
class Registry:
    witnesses: dict[str, uuid.UUID]
    exhibits: dict[str, uuid.UUID]
    # variant -> org ids that record it
    organization_variants: dict[str, set[uuid.UUID]]
    # exact speaker label -> (person id, role, name key)
    person_labels: dict[str, tuple[uuid.UUID, str, str]]
    # name key -> number of registered people sharing it (any role)
    name_keys: Counter[str] = field(default_factory=Counter)
    # recorded full-name alias -> people it is recorded for (source-backed only)
    full_names: dict[str, set[uuid.UUID]] = field(default_factory=dict)
    # The case being projected; another court's case number never names its records.
    case_number: str = ""


@dataclass(frozen=True)
class MentionProjectionResult:
    run_id: uuid.UUID
    rows: int
    by_kind_state: dict[str, int]
    by_rule: dict[str, int]
    unregistered_witness_codes: int
    unregistered_exhibit_ids: int
    unregistered_speaker_labels: int
    legacy_rows_removed: int


# ----------------------------------------------------------------- rules --
def witness_code_mentions(text: str, witnesses: Mapping[str, uuid.UUID]) -> Iterator[Mention]:
    for match in WITNESS_CODE.finditer(text):
        witness_id = witnesses.get(match.group(0))
        if witness_id is not None:
            yield Mention(
                "witness_id",
                witness_id,
                "witness.code.exact",
                match.start(),
                match.end(),
                match.group(0),
            )


def exhibit_mentions(
    text: str, exhibits: Mapping[str, uuid.UUID], case_number: str = ""
) -> Iterator[Mention]:
    for match in EXHIBIT_ID.finditer(text):
        exhibit_id = exhibits.get(match.group(0))
        if exhibit_id is not None and not foreign_case_before(text, match.start(), case_number):
            yield Mention(
                "exhibit_id",
                exhibit_id,
                "exhibit.identifier.exact",
                match.start(),
                match.end(),
                match.group(0),
            )


def _variant_pattern(variant: str) -> re.Pattern[str]:
    # Straight and typographic apostrophes are the same recorded variant.
    body = "".join("['\u2019]" if ch in "'\u2019" else re.escape(ch) for ch in variant)
    flags = 0 if _ACRONYM.fullmatch(variant) else re.IGNORECASE
    return re.compile(rf"(?<!\w){body}(?!\w)", flags)


def organization_mentions(text: str, variants: Mapping[str, set[uuid.UUID]]) -> Iterator[Mention]:
    seen: set[tuple[int, int, uuid.UUID]] = set()
    for variant, org_ids in variants.items():
        if not variant.strip():
            continue
        if len(org_ids) > 1:
            rule = "organization.variant.shared"
        elif _ACRONYM.fullmatch(variant):
            rule = "organization.acronym.exact"
        else:
            rule = "organization.name.exact"
        for match in _variant_pattern(variant).finditer(text):
            for org_id in sorted(org_ids):
                key = (match.start(), match.end(), org_id)
                if key in seen:
                    continue
                seen.add(key)
                yield Mention(
                    "organization_id",
                    org_id,
                    rule,
                    match.start(),
                    match.end(),
                    match.group(0),
                )


def classify_speaker_label(label: str, registry: Registry) -> Mention | None:
    """Bind a speaker label through the shared identity rules (`identity.py`).

    Role-qualified labels verify; honorific-only and shared-surname labels are
    review-required; unrecorded or ambiguous labels produce no row."""
    resolution = classify_label(label, registry.person_labels, registry.name_keys)
    if resolution is None or resolution.person_id is None:
        return None
    return Mention("person_id", resolution.person_id, resolution.rule, 0, len(label), label)


def full_name_mentions(text: str, full_names: Mapping[str, set[uuid.UUID]]) -> Iterator[Mention]:
    """Exact, whole-token, case-insensitive matches of recorded full names.

    A spelling recorded for more than one person is ambiguous and never bound."""
    seen: set[tuple[int, int]] = set()
    for name in sorted(full_names, key=len, reverse=True):
        owners = full_names[name]
        if len(owners) != 1:
            continue
        (person_id,) = owners
        pattern = r"\s+".join(re.escape(token) for token in name.split())
        for match in re.finditer(rf"(?<!\w){pattern}(?!\w)", text, re.IGNORECASE):
            span = (match.start(), match.end())
            if span in seen:
                continue
            seen.add(span)
            yield Mention(
                "person_id",
                person_id,
                "person.full_name.exact",
                match.start(),
                match.end(),
                match.group(0),
            )


# ------------------------------------------------------------- registry --
def load_registry(session: Session, case: Case) -> Registry:
    witnesses = {
        code: witness_id
        for code, witness_id in session.execute(
            select(Witness.code, Witness.id).where(Witness.case_id == case.id)
        ).all()
    }
    exhibits = {
        official: exhibit_id
        for official, exhibit_id in session.execute(
            select(Exhibit.official_exhibit_id, Exhibit.id).where(
                Exhibit.case_id == case.id,
                Exhibit.visibility.in_(tuple(PUBLIC_VISIBILITIES)),
            )
        ).all()
    }
    variants: dict[str, set[uuid.UUID]] = {}
    for organization in session.scalars(
        select(Organization).where(Organization.case_id == case.id)
    ):
        for variant in {organization.name, *(organization.name_variants or [])}:
            variants.setdefault(variant, set()).add(organization.id)

    person_labels: dict[str, tuple[uuid.UUID, str, str]] = {}
    name_keys: Counter[str] = Counter()
    ambiguous_labels: set[str] = set()
    people = session.execute(select(Person.id, Person.slug).where(Person.case_id == case.id)).all()
    slugs = {person_id: slug for person_id, slug in people}
    for slug in slugs.values():
        role, name_key = slug_role_and_key(slug)
        if role in NAMED_ROLES and name_key:
            name_keys[name_key] += 1
    full_names: dict[str, set[uuid.UUID]] = {}
    for person_id, alias, alias_kind in session.execute(
        select(PersonAlias.person_id, PersonAlias.alias, PersonAlias.alias_kind).where(
            PersonAlias.person_id.in_(list(slugs))
        )
    ).all():
        if alias_kind == "full_name":
            full_names.setdefault(" ".join(alias.split()), set()).add(person_id)
            continue
        identity = speaker_label_identity(alias)
        if identity is None or identity[0] != slugs[person_id]:
            # The alias does not deterministically reproduce this person's
            # canonical identity; it is never used as a binding.
            continue
        role, _, name_key = identity[0].partition("-")
        if alias in person_labels and person_labels[alias][0] != person_id:
            ambiguous_labels.add(alias)
        person_labels[alias] = (person_id, identity[2], name_key)
    for alias in ambiguous_labels:
        person_labels.pop(alias, None)
    # A full name that differs only by case is the same recorded spelling.
    folded: dict[str, set[uuid.UUID]] = {}
    for name, owners in full_names.items():
        folded.setdefault(name.casefold(), set()).update(owners)
    full_names = {name: folded[name.casefold()] for name in full_names}
    return Registry(
        witnesses, exhibits, variants, person_labels, name_keys, full_names, case.case_number
    )


# -------------------------------------------------------------- anchors --
def _paragraph_spans(
    page_text: str, paragraphs: Iterable[tuple[int, str]]
) -> tuple[tuple[int, int, int], ...]:
    spans: list[tuple[int, int, int]] = []
    for number, text in paragraphs:
        tokens = text.split()
        if not tokens:
            continue
        # The same token sequence, whitespace-insensitive; it must occur exactly
        # once on the page or the paragraph number stays NULL.
        matches = list(re.finditer(r"\s+".join(map(re.escape, tokens)), page_text))
        if len(matches) != 1:
            continue
        spans.append((matches[0].start(), matches[0].end(), number))
    return tuple(spans)


def public_anchors(session: Session, case: Case) -> Iterator[Anchor]:
    public = tuple(PUBLIC_VISIBILITIES)
    segment_rows = session.execute(
        select(TranscriptSegment, Transcript, DocumentVersion.official_version_ref)
        .join(Transcript, Transcript.id == TranscriptSegment.transcript_id)
        .join(DocumentVersion, DocumentVersion.id == Transcript.document_version_id)
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(
            Document.case_id == case.id,
            Document.visibility.in_(public),
            DocumentVersion.visibility.in_(public),
            Transcript.visibility.in_(public),
            TranscriptSegment.closed_session.is_(False),
        )
        .order_by(Transcript.id, TranscriptSegment.sequence)
    ).all()
    transcript_versions: set[uuid.UUID] = set()
    for segment, transcript, version_ref in segment_rows:
        assert transcript.document_version_id is not None
        transcript_versions.add(transcript.document_version_id)
        common = {
            "document_version_id": transcript.document_version_id,
            "language": version_language(version_ref, transcript.language),
            "transcript_segment_id": segment.id,
            "page_number": segment.page_number,
            "pdf_page_index": segment.pdf_page_index,
            "line_from": segment.line_from,
            "line_to": segment.line_to,
        }
        if segment.text:
            yield Anchor(kind=SEGMENT_TEXT, text=segment.text, **common)
        if segment.speaker:
            yield Anchor(kind=SPEAKER_LABEL, text=segment.speaker, **common)

    paragraphs: dict[tuple[uuid.UUID, int], list[tuple[int, str]]] = {}
    for version_id, page_index, number, text in session.execute(
        select(
            DocumentParagraph.document_version_id,
            DocumentParagraph.pdf_page_index_from,
            DocumentParagraph.paragraph_number,
            DocumentParagraph.text,
        ).where(DocumentParagraph.pdf_page_index_from == DocumentParagraph.pdf_page_index_to)
    ).all():
        paragraphs.setdefault((version_id, page_index), []).append((number, text))

    page_rows = session.execute(
        select(DocumentPage, Document.language, DocumentVersion.official_version_ref)
        .join(DocumentVersion, DocumentVersion.id == DocumentPage.document_version_id)
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(
            Document.case_id == case.id,
            Document.visibility.in_(public),
            DocumentVersion.visibility.in_(public),
            DocumentPage.text.is_not(None),
        )
        .order_by(DocumentPage.document_version_id, DocumentPage.pdf_page_index)
    ).all()
    for page, language, version_ref in page_rows:
        # Transcript versions are projected from segments, which carry lines.
        if page.document_version_id in transcript_versions or not page.text:
            continue
        yield Anchor(
            kind=PAGE_TEXT,
            text=page.text,
            document_version_id=page.document_version_id,
            language=version_language(version_ref, language),
            page_number=page.page_number,
            pdf_page_index=page.pdf_page_index,
            paragraphs=_paragraph_spans(
                page.text,
                paragraphs.get((page.document_version_id, page.pdf_page_index), ()),
            ),
        )


def anchor_mentions(anchor: Anchor, registry: Registry) -> Iterator[Mention]:
    if anchor.kind == SPEAKER_LABEL:
        mention = classify_speaker_label(anchor.text, registry)
        if mention is not None:
            yield mention
        return
    yield from witness_code_mentions(anchor.text, registry.witnesses)
    yield from exhibit_mentions(anchor.text, registry.exhibits, registry.case_number)
    yield from organization_mentions(anchor.text, registry.organization_variants)
    yield from full_name_mentions(anchor.text, registry.full_names)


def mention_id(anchor: Anchor, mention: Mention) -> uuid.UUID:
    return uuid.uuid5(
        _NS,
        ":".join(
            (
                anchor.key,
                str(mention.char_start),
                str(mention.char_end),
                mention.entity_field,
                str(mention.entity_id),
                mention.rule_id,
                str(RULES[mention.rule_id][0]),
            )
        ),
    )


# ------------------------------------------------------------- pipeline --
class Phase19MentionProjector:
    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def run(self) -> MentionProjectionResult:
        with self.sessions() as session, session.begin():
            case = session.scalar(select(Case).where(Case.case_number == self.case_number))
            if case is None:
                raise RuntimeError(f"case {self.case_number} is not seeded")
            registry = load_registry(session, case)
            previous = session.scalar(
                select(ProcessingRun)
                .where(
                    ProcessingRun.case_id == case.id,
                    ProcessingRun.processor == PROCESSOR,
                    ProcessingRun.status == "completed",
                )
                .order_by(ProcessingRun.started_at.desc())
                .limit(1)
            )
            run = ProcessingRun(
                id=uuid.uuid4(),
                case_id=case.id,
                processor=PROCESSOR,
                processor_version=PROCESSOR_VERSION,
                status="running",
                started_at=datetime.now(UTC),
            )
            session.add(run)
            session.flush()

            # Pre-19 Phase 17C rows carry no rule lineage; they are superseded.
            legacy = session.execute(
                delete(EntityOccurrence).where(
                    EntityOccurrence.case_id == case.id,
                    EntityOccurrence.extraction_origin == "phase17c",
                )
            )
            removed_legacy = int(getattr(legacy, "rowcount", 0) or 0)
            session.execute(
                delete(EntityOccurrence).where(
                    EntityOccurrence.case_id == case.id,
                    EntityOccurrence.rule_id.in_(list(RULES)),
                )
            )

            rows: dict[uuid.UUID, dict[str, object]] = {}
            unregistered_codes = 0
            unregistered_exhibits = 0
            unregistered_labels = 0
            for anchor in public_anchors(session, case):
                if anchor.kind == SPEAKER_LABEL:
                    unregistered_labels += int(
                        speaker_label_identity(anchor.text) is not None
                        and anchor.text not in registry.person_labels
                    )
                else:
                    unregistered_codes += sum(
                        m.group(0) not in registry.witnesses
                        for m in WITNESS_CODE.finditer(anchor.text)
                    )
                    unregistered_exhibits += sum(
                        m.group(0) not in registry.exhibits
                        for m in EXHIBIT_ID.finditer(anchor.text)
                    )
                for mention in anchor_mentions(anchor, registry):
                    # No provenance, no row: the span must reproduce the text.
                    if anchor.text[mention.char_start : mention.char_end] != mention.text:
                        continue
                    rule_version, state = RULES[mention.rule_id]
                    row_id = mention_id(anchor, mention)
                    rows[row_id] = {
                        "id": row_id,
                        "case_id": case.id,
                        "person_id": None,
                        "witness_id": None,
                        "organization_id": None,
                        "exhibit_id": None,
                        mention.entity_field: mention.entity_id,
                        "document_version_id": anchor.document_version_id,
                        "transcript_segment_id": anchor.transcript_segment_id,
                        "page_number": anchor.page_number,
                        "pdf_page_index": anchor.pdf_page_index,
                        "paragraph_number": (
                            anchor.paragraph_at(mention.char_start, mention.char_end)
                            if anchor.kind == PAGE_TEXT
                            else None
                        ),
                        "line_from": anchor.line_from,
                        "line_to": anchor.line_to,
                        "char_anchor": anchor.kind,
                        "char_start": mention.char_start,
                        "char_end": mention.char_end,
                        "occurrence_text": mention.text,
                        "language": anchor.language,
                        "extraction_origin": "deterministic",
                        "mention_state": state,
                        "review_required": state == REVIEW_REQUIRED,
                        "rule_id": mention.rule_id,
                        "rule_version": rule_version,
                        "projection_run_id": run.id,
                    }
            values = list(rows.values())
            for offset in range(0, len(values), 2000):
                session.execute(insert(EntityOccurrence), values[offset : offset + 2000])

            by_kind_state: Counter[str] = Counter()
            by_rule: Counter[str] = Counter()
            for row in values:
                kind = next(
                    name.removesuffix("_id")
                    for name in ("person_id", "witness_id", "organization_id", "exhibit_id")
                    if row[name] is not None
                )
                by_kind_state[f"{kind}:{row['mention_state']}"] += 1
                by_rule[str(row["rule_id"])] += 1
            previous_counts: dict[str, int] = dict(
                (previous.detail or {}).get("by_kind_state", {}) if previous else {}
            )
            run.status = "completed"
            run.finished_at = datetime.now(UTC)
            run.selected_count = len(values)
            run.processed_count = len(values)
            run.detail = {
                "rules": {rule: version for rule, (version, _) in RULES.items()},
                "by_kind_state": dict(sorted(by_kind_state.items())),
                "by_rule": dict(sorted(by_rule.items())),
                "previous_run_id": str(previous.id) if previous else None,
                "diff_vs_previous": {
                    key: by_kind_state.get(key, 0) - previous_counts.get(key, 0)
                    for key in sorted(set(by_kind_state) | set(previous_counts))
                },
                "unregistered_witness_codes": unregistered_codes,
                "unregistered_exhibit_ids": unregistered_exhibits,
                "unregistered_speaker_labels": unregistered_labels,
                "legacy_rows_removed": removed_legacy,
            }
            return MentionProjectionResult(
                run_id=run.id,
                rows=len(values),
                by_kind_state=dict(sorted(by_kind_state.items())),
                by_rule=dict(sorted(by_rule.items())),
                unregistered_witness_codes=unregistered_codes,
                unregistered_exhibit_ids=unregistered_exhibits,
                unregistered_speaker_labels=unregistered_labels,
                legacy_rows_removed=removed_legacy,
            )
