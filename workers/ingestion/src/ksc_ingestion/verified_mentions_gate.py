"""Phase 19A verified-mention reconciliation and quality gate.

Read-only. Re-derives every persisted mention from its public anchor text and
reports provenance, deduplication and protected-witness violations, plus a
seeded sampling re-verification per entity kind and search-only match counts.
"""

from __future__ import annotations

import json
import random
import re
import uuid
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ksc_api.models import (
    Case,
    Document,
    DocumentVersion,
    EntityOccurrence,
    Exhibit,
    Person,
    Transcript,
)
from ksc_ingestion.verified_mentions import (
    EXHIBIT_ID,
    PAGE_TEXT,
    PROCESSOR,
    REVIEW_REQUIRED,
    RULES,
    SPEAKER_LABEL,
    VERIFIED,
    WITNESS_CODE,
    Anchor,
    anchor_mentions,
    load_registry,
    public_anchors,
    version_language,
)

KINDS = ("person", "witness", "organization", "exhibit")
SAMPLE_SIZE = 100
SAMPLE_SEED = 19
# Declared 19A threshold: automated re-derivation must reproduce every sample.
PRECISION_THRESHOLD = 1.0
_CODE_ONLY = re.compile(r"W\d{5}")
_ANY_CODE = re.compile(r"(?<![0-9A-Za-z])[Ww]\d{5}(?![0-9A-Za-z])")
_TITLE_PREFIX = re.compile(r"^(?:Judge|Accused)\s+")


class KindCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: int = Field(ge=0)
    review_required: int = Field(ge=0)
    rejected: int = Field(ge=0)
    search_only: int | None = Field(default=None, ge=0)
    unregistered_identifiers: int | None = Field(default=None, ge=0)
    sampled: int = Field(ge=0)
    sample_reproduced: int = Field(ge=0)
    sample_precision: float | None = None


class Phase19AMentionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: date
    case_number: str
    projection_run_id: str | None
    rule_versions: dict[str, int]
    kinds: dict[str, KindCounts]
    by_rule: dict[str, int]
    by_anchor: dict[str, int]
    by_language: dict[str, int]
    language_metadata_conflicts: int = Field(ge=0)
    total_rows: int = Field(ge=0)
    total_verified: int = Field(ge=0)
    total_review_required: int = Field(ge=0)
    legacy_rows: int = Field(ge=0)
    verified_with_paragraph: int = Field(ge=0)
    verified_with_line: int = Field(ge=0)
    provenance_violations: int = Field(ge=0)
    protected_identity_violations: int = Field(ge=0)
    dedup_conflicts: int = Field(ge=0)
    review_state_violations: int = Field(ge=0)
    smith_review_required: int = Field(ge=0)
    exhibit_status_counts: dict[str, int]
    sample_seed: int
    precision_threshold: float
    passed: bool


def _kind(row: EntityOccurrence) -> str:
    for kind in KINDS:
        if getattr(row, f"{kind}_id") is not None:
            return kind
    raise ValueError(f"occurrence {row.id} has no entity")


def _anchor_key(row: EntityOccurrence) -> str:
    if row.transcript_segment_id is not None:
        return f"{row.char_anchor}:{row.transcript_segment_id}"
    return f"{row.char_anchor}:{row.document_version_id}:{row.pdf_page_index}"


def run_phase19a_gate(
    session: Session, case: Case, generated_at: date, *, sample_size: int = SAMPLE_SIZE
) -> Phase19AMentionReport:
    registry = load_registry(session, case)
    anchors: dict[str, Anchor] = {anchor.key: anchor for anchor in public_anchors(session, case)}
    rows = session.scalars(
        select(EntityOccurrence).where(EntityOccurrence.case_id == case.id)
    ).all()
    legacy = [row for row in rows if row.rule_id is None]
    rows = [row for row in rows if row.rule_id is not None]

    provenance_violations = 0
    protected_violations = 0
    review_state_violations = 0
    by_kind_state: Counter[tuple[str, str]] = Counter()
    spans: dict[tuple[str, int, int, str], set[uuid.UUID]] = defaultdict(set)
    verified_by_kind: dict[str, list[EntityOccurrence]] = defaultdict(list)
    for row in rows:
        kind = _kind(row)
        by_kind_state[(kind, row.mention_state)] += 1
        anchor = anchors.get(_anchor_key(row))
        # Public-only, live version, exact coordinates, verbatim span.
        if (
            anchor is None
            or anchor.document_version_id != row.document_version_id
            or anchor.text[row.char_start : row.char_end] != row.occurrence_text
            or row.char_end <= row.char_start
            or row.rule_id not in RULES
            or RULES[row.rule_id][0] != row.rule_version
            or row.extraction_origin != "deterministic"
        ):
            provenance_violations += 1
        if kind == "witness" and not _CODE_ONLY.fullmatch(row.occurrence_text):
            protected_violations += 1
        expected_state = RULES.get(row.rule_id or "", (0, ""))[1]
        if row.mention_state != expected_state or row.review_required != (
            row.mention_state == REVIEW_REQUIRED
        ):
            review_state_violations += 1
        if row.mention_state == VERIFIED:
            verified_by_kind[kind].append(row)
            entity = getattr(row, f"{kind}_id")
            spans[(_anchor_key(row), row.char_start, row.char_end, kind)].add(entity)
    dedup_conflicts = sum(1 for entities in spans.values() if len(entities) > 1)

    # Seeded sampling re-verification: re-run the rules on the anchor text and
    # require the persisted (span, entity, rule) to be reproduced exactly.
    rng = random.Random(SAMPLE_SEED)  # noqa: S311 - reproducible audit sample
    samples: dict[str, tuple[int, int]] = {}
    for kind in KINDS:
        population = sorted(verified_by_kind[kind], key=lambda row: str(row.id))
        chosen = rng.sample(population, min(sample_size, len(population)))
        reproduced = 0
        for row in chosen:
            anchor = anchors.get(_anchor_key(row))
            if anchor is None:
                continue
            entity = getattr(row, f"{kind}_id")
            reproduced += any(
                mention.char_start == row.char_start
                and mention.char_end == row.char_end
                and mention.entity_id == entity
                and mention.rule_id == row.rule_id
                for mention in anchor_mentions(anchor, registry)
            )
        samples[kind] = (len(chosen), reproduced)

    # Search-only matches: lexical hits a dossier search would surface that no
    # persisted mention covers. Counted, never stored.
    body_anchors = [anchor for anchor in anchors.values() if anchor.kind != SPEAKER_LABEL]
    terms: dict[str, int] = {}
    for display_name, slug in session.execute(
        select(Person.display_name, Person.slug).where(Person.case_id == case.id)
    ).all():
        if slug.split("-", 1)[0] in {"judge", "accused", "counsel_or_participant"}:
            terms[_TITLE_PREFIX.sub("", display_name)] = 0
    person_search_only = 0
    if terms:
        pattern = re.compile(
            r"(?<!\w)(?:"
            + "|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True))
            + r")(?!\w)",
            re.IGNORECASE,
        )
        person_search_only = sum(len(pattern.findall(anchor.text)) for anchor in body_anchors)
    witness_search_only = 0
    witness_unregistered = 0
    exhibit_unregistered = 0
    for anchor in body_anchors:
        for match in _ANY_CODE.finditer(anchor.text):
            code = match.group(0)
            if code.upper() not in registry.witnesses:
                witness_unregistered += int(WITNESS_CODE.fullmatch(code) is not None)
            elif code not in registry.witnesses:
                witness_search_only += 1
        exhibit_unregistered += sum(
            m.group(0) not in registry.exhibits for m in EXHIBIT_ID.finditer(anchor.text)
        )

    kinds: dict[str, KindCounts] = {}
    for kind in KINDS:
        sampled, reproduced = samples[kind]
        kinds[kind] = KindCounts(
            verified=by_kind_state[(kind, VERIFIED)],
            review_required=by_kind_state[(kind, REVIEW_REQUIRED)],
            rejected=by_kind_state[(kind, "rejected")],
            search_only={"person": person_search_only, "witness": witness_search_only}.get(kind),
            unregistered_identifiers={
                "witness": witness_unregistered,
                "exhibit": exhibit_unregistered,
            }.get(kind),
            sampled=sampled,
            sample_reproduced=reproduced,
            sample_precision=round(reproduced / sampled, 4) if sampled else None,
        )

    smith_id = session.scalar(
        select(Person.id).where(
            Person.case_id == case.id, Person.slug == "counsel_or_participant-smith"
        )
    )
    smith_rows = [row for row in rows if smith_id is not None and row.person_id == smith_id]
    exhibit_statuses = {
        str(status): int(count)
        for status, count in session.execute(
            select(Exhibit.status, func.count())
            .where(Exhibit.case_id == case.id)
            .group_by(Exhibit.status)
        ).all()
    }
    # Versions whose official language marker disagrees with the recorded
    # transcript/document language. The marker is used; the metadata is reported.
    language_conflicts = 0
    for version_ref, document_language, transcript_language in session.execute(
        select(DocumentVersion.official_version_ref, Document.language, Transcript.language)
        .join(Document, Document.id == DocumentVersion.document_id)
        .outerjoin(Transcript, Transcript.document_version_id == DocumentVersion.id)
        .where(Document.case_id == case.id)
    ).all():
        recorded = transcript_language or document_language
        language_conflicts += int(version_language(version_ref, recorded) != recorded)
    run_id = next((str(row.projection_run_id) for row in rows if row.projection_run_id), None)
    verified_rows = [row for row in rows if row.mention_state == VERIFIED]
    precision_ok = all(
        count.sample_precision is None or count.sample_precision >= PRECISION_THRESHOLD
        for count in kinds.values()
    )
    passed = (
        provenance_violations == 0
        and protected_violations == 0
        and dedup_conflicts == 0
        and review_state_violations == 0
        and not legacy
        and all(row.mention_state == REVIEW_REQUIRED for row in smith_rows)
        and precision_ok
        and len({row.projection_run_id for row in rows}) <= 1
    )
    return Phase19AMentionReport(
        generated_at=generated_at,
        case_number=case.case_number,
        projection_run_id=run_id,
        rule_versions={rule: version for rule, (version, _) in RULES.items()},
        kinds=kinds,
        by_rule=dict(sorted(Counter(str(row.rule_id) for row in rows).items())),
        by_anchor=dict(sorted(Counter(str(row.char_anchor) for row in rows).items())),
        by_language=dict(sorted(Counter(str(row.language) for row in rows).items())),
        language_metadata_conflicts=language_conflicts,
        total_rows=len(rows),
        total_verified=len(verified_rows),
        total_review_required=sum(row.mention_state == REVIEW_REQUIRED for row in rows),
        legacy_rows=len(legacy),
        verified_with_paragraph=sum(
            row.paragraph_number is not None
            for row in verified_rows
            if row.char_anchor == PAGE_TEXT
        ),
        verified_with_line=sum(row.line_from is not None for row in verified_rows),
        provenance_violations=provenance_violations,
        protected_identity_violations=protected_violations,
        dedup_conflicts=dedup_conflicts,
        review_state_violations=review_state_violations,
        smith_review_required=sum(row.mention_state == REVIEW_REQUIRED for row in smith_rows),
        exhibit_status_counts=dict(sorted(exhibit_statuses.items())),
        sample_seed=SAMPLE_SEED,
        precision_threshold=PRECISION_THRESHOLD,
        passed=passed,
    )


def write_phase19a_report(report: Phase19AMentionReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"processor": PROCESSOR, **report.model_dump(mode="json")}, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
