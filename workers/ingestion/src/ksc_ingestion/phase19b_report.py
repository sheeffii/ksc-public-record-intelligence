"""Phase 19B corpus-depth analysis and structured-intelligence reconciliation.

Read-only. Produces one JSON document with:

- ``corpus``: distributions and gaps (years, classes, languages, parties,
  version variants, language counterparts, hearings, extraction quality);
- ``entities`` / ``relationships`` / ``citations`` / ``provenance``: coverage
  by kind, state and rule;
- ``checks``: reconciliation invariants that must all be zero;
- ``capture_plan``: the next official batch, ranked by what it would resolve.

Nothing here writes to the database or estimates a value it cannot count.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ksc_api.models import (
    Case,
    Citation,
    Document,
    DocumentPage,
    DocumentVersion,
    EntityOccurrence,
    Exhibit,
    ExhibitStatusEvent,
    Hearing,
    Organization,
    Person,
    PersonAlias,
    Relationship,
    Transcript,
    TranscriptSegment,
    Witness,
    WitnessAppearance,
    WitnessIdentityStatus,
    version_language,
)
from ksc_ingestion.exhibit_status import speaker_role
from ksc_ingestion.identity import slug_role_and_key
from ksc_ingestion.verified_mentions_gate import run_phase19a_gate

_VARIANT = re.compile(r"/(RED2|RED|COR|CORRED|SQI|A\d{2})(?=/|$)", re.I)
_SUBCASE = re.compile(r"/(?:IA|PL)\d{3}/", re.I)
_TARGET = re.compile(r"^(?:KSC-BC-2020-06/)?((?:(?:IA|PL)\d{3}/)?F\d{5})", re.I)


def _document_class(document: Document) -> str:
    kind = document.document_type.lower()
    if _SUBCASE.search(document.official_ref):
        return "appeal_or_subcase"
    if kind == "transcript":
        return "transcript"
    if kind in {"decision", "order"}:
        return "decision_or_order"
    if kind == "filing_annex" or re.search(r"/A\d{2}$", document.official_ref):
        return "annex"
    return "party_or_registry_filing"


def _year(document: Document) -> str:
    day = document.document_date or document.public_date
    return str(day.year) if day else "undated"


def _corpus(session: Session, case: Case) -> dict[str, Any]:
    documents = session.scalars(select(Document).where(Document.case_id == case.id)).all()
    versions = session.execute(
        select(DocumentVersion, Document)
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(Document.case_id == case.id)
    ).all()
    by_year_class: dict[str, Counter[str]] = defaultdict(Counter)
    parties: Counter[str] = Counter()
    for document in documents:
        by_year_class[_year(document)][_document_class(document)] += 1
        parties[str(document.filing_party.value if document.filing_party else "unstated")] += 1
    variant_counts: Counter[str] = Counter()
    languages_by_document: dict[str, set[str]] = defaultdict(set)
    for version, document in versions:
        tail = version.official_version_ref.removeprefix(document.official_ref)
        markers = [m.group(1).upper() for m in _VARIANT.finditer(tail)] or ["BASE"]
        for marker in markers:
            variant_counts[marker] += 1
        language = version_language(version.official_version_ref, document.language) or "?"
        languages_by_document[document.official_ref].add(language)
    counterparts = Counter(
        "en+sq" if {"en", "sq"} <= langs else ("sq_only" if langs == {"sq"} else "en_only")
        for langs in languages_by_document.values()
    )
    class_counterparts: dict[str, Counter[str]] = defaultdict(Counter)
    for document in documents:
        langs = languages_by_document.get(document.official_ref, set())
        key = "en+sq" if {"en", "sq"} <= langs else ("sq_only" if langs == {"sq"} else "en_only")
        class_counterparts[_document_class(document)][key] += 1

    hearings = session.execute(
        select(Hearing.hearing_date, Hearing.session_label, func.count(Transcript.id))
        .outerjoin(Transcript, Transcript.hearing_id == Hearing.id)
        .where(Hearing.case_id == case.id)
        .group_by(Hearing.id)
        .order_by(Hearing.hearing_date)
    ).all()
    hearings_with_appearance = {
        hearing_id
        for (hearing_id,) in session.execute(
            select(WitnessAppearance.hearing_id)
            .join(Hearing, Hearing.id == WitnessAppearance.hearing_id)
            .where(Hearing.case_id == case.id, WitnessAppearance.rule_id.is_not(None))
        ).all()
    }
    kinds = Counter(
        "trial_hearing"
        if re.search(r"Trial Hearing|Seancë gjykimi", label or "", re.I)
        else "opening_or_closing"
        if re.search(r"Opening|Closing|hyrëse|përmbyllëse", label or "", re.I)
        else "status_or_procedural"
        for _, label, _ in hearings
    )
    review = session.execute(
        select(DocumentVersion.official_version_ref)
        .join(Document, Document.id == DocumentVersion.document_id)
        .where(Document.case_id == case.id, DocumentVersion.parse_requires_review.is_(True))
    ).all()
    empty_pages = int(
        session.scalar(
            select(func.count())
            .select_from(DocumentPage)
            .join(DocumentVersion, DocumentVersion.id == DocumentPage.document_version_id)
            .join(Document, Document.id == DocumentVersion.document_id)
            .where(
                Document.case_id == case.id,
                func.coalesce(func.length(func.trim(DocumentPage.text)), 0) == 0,
            )
        )
        or 0
    )
    segments_without_lines = int(
        session.scalar(
            select(func.count())
            .select_from(TranscriptSegment)
            .join(Transcript, Transcript.id == TranscriptSegment.transcript_id)
            .join(Hearing, Hearing.id == Transcript.hearing_id)
            .where(Hearing.case_id == case.id, TranscriptSegment.line_from.is_(None))
        )
        or 0
    )
    return {
        "documents": len(documents),
        "versions": len(versions),
        "by_year_and_class": {
            year: dict(sorted(counter.items())) for year, counter in sorted(by_year_class.items())
        },
        "parties": dict(parties.most_common()),
        "version_variants": dict(variant_counts.most_common()),
        "language_counterparts": dict(counterparts),
        "language_counterparts_by_class": {
            key: dict(value) for key, value in sorted(class_counterparts.items())
        },
        "hearings": len(hearings),
        "hearings_by_kind": dict(kinds),
        "hearings_by_year": dict(Counter(str(day.year) for day, _, _ in hearings)),
        "hearings_with_recorded_appearance": len(hearings_with_appearance),
        "versions_requiring_parse_review": [ref for (ref,) in review],
        "empty_text_pages": empty_pages,
        "transcript_segments_without_lines": segments_without_lines,
    }


def _entities(session: Session, case: Case) -> dict[str, Any]:
    people: Counter[str] = Counter()
    basis: Counter[str] = Counter()
    full_name_people = {
        person_id
        for (person_id,) in session.execute(
            select(PersonAlias.person_id).where(PersonAlias.alias_kind == "full_name")
        ).all()
    }
    for person_id, slug in session.execute(
        select(Person.id, Person.slug).where(Person.case_id == case.id)
    ).all():
        role, _ = slug_role_and_key(slug)
        people[role] += 1
        if person_id in full_name_people:
            basis["source_backed_full_name"] += 1
        elif role in {"judge", "accused"}:
            basis["role_qualified_label"] += 1
        elif role == "counsel_or_participant":
            basis["surname_level_label"] += 1
        else:
            basis["other"] += 1

    def mentioned(column: Any, state: str = "verified") -> int:
        return int(
            session.scalar(
                select(func.count(func.distinct(column))).where(
                    EntityOccurrence.case_id == case.id,
                    EntityOccurrence.mention_state == state,
                    column.is_not(None),
                )
            )
            or 0
        )

    witnesses = int(
        session.scalar(select(func.count()).select_from(Witness).where(Witness.case_id == case.id))
        or 0
    )
    exhibits = int(
        session.scalar(select(func.count()).select_from(Exhibit).where(Exhibit.case_id == case.id))
        or 0
    )
    organizations = int(
        session.scalar(
            select(func.count()).select_from(Organization).where(Organization.case_id == case.id)
        )
        or 0
    )
    witness_with_appearance = int(
        session.scalar(
            select(func.count(func.distinct(WitnessAppearance.witness_id))).where(
                WitnessAppearance.rule_id.is_not(None), WitnessAppearance.witness_id.is_not(None)
            )
        )
        or 0
    )
    events = Counter(
        f"{event_type}:{'bound' if bound else 'unbound'}"
        for event_type, bound in session.execute(
            select(ExhibitStatusEvent.event_type, ExhibitStatusEvent.exhibit_id.is_not(None)).where(
                ExhibitStatusEvent.case_id == case.id
            )
        ).all()
    )
    statuses = Counter(
        status
        for (status,) in session.execute(
            select(Exhibit.status).where(Exhibit.case_id == case.id)
        ).all()
    )
    exhibits_with_events = int(
        session.scalar(
            select(func.count(func.distinct(ExhibitStatusEvent.exhibit_id))).where(
                ExhibitStatusEvent.case_id == case.id, ExhibitStatusEvent.exhibit_id.is_not(None)
            )
        )
        or 0
    )
    return {
        "people_by_role": dict(people),
        "people_by_identity_basis": dict(basis),
        "people_with_verified_mention": mentioned(EntityOccurrence.person_id),
        "people_with_review_required_mentions": mentioned(
            EntityOccurrence.person_id, "review_required"
        ),
        "witnesses": witnesses,
        "witnesses_with_verified_mention": mentioned(EntityOccurrence.witness_id),
        "witnesses_with_recorded_appearance": witness_with_appearance,
        "organizations": organizations,
        "organizations_with_verified_mention": mentioned(EntityOccurrence.organization_id),
        "exhibits": exhibits,
        "exhibits_with_verified_mention": mentioned(EntityOccurrence.exhibit_id),
        "exhibits_with_status_events": exhibits_with_events,
        "exhibit_status": dict(statuses),
        "exhibit_status_events": dict(events),
    }


def _relationships(session: Session, case: Case) -> dict[str, Any]:
    rows = session.execute(
        select(
            Relationship.relationship_type,
            Relationship.citation_id.is_not(None),
            Relationship.entity_occurrence_id.is_not(None),
            Relationship.witness_appearance_id.is_not(None),
            func.count(),
            func.sum(Relationship.evidence_count),
        )
        .where(Relationship.case_id == case.id)
        .group_by(
            Relationship.relationship_type,
            Relationship.citation_id.is_not(None),
            Relationship.entity_occurrence_id.is_not(None),
            Relationship.witness_appearance_id.is_not(None),
        )
    ).all()
    result: dict[str, dict[str, int]] = {}
    for kind, is_citation, is_occurrence, is_appearance, count, evidence in rows:
        evidence_kind = (
            "citation"
            if is_citation
            else "entity_occurrence"
            if is_occurrence
            else "witness_appearance"
            if is_appearance
            else "none"
        )
        result[f"{kind.value}:{evidence_kind}"] = {"edges": int(count), "evidence": int(evidence)}
    return dict(sorted(result.items()))


def _citations(session: Session, case: Case) -> dict[str, Any]:
    by_rule = Counter(
        f"{state.value}:{rule or 'unrecorded'}"
        for state, rule in session.execute(
            select(Citation.resolution_state, Citation.resolution_rule).where(
                Citation.case_id == case.id
            )
        ).all()
    )
    states = Counter(key.split(":", 1)[0] for key in by_rule.elements())
    unheld_filings: Counter[str] = Counter()
    unheld_dates: Counter[str] = Counter()
    per_source: dict[str, Counter[str]] = defaultdict(Counter)
    for normalized, rule, state, source_ref in session.execute(
        select(
            Citation.normalized_text,
            Citation.resolution_rule,
            Citation.resolution_state,
            DocumentVersion.official_version_ref,
        )
        .join(DocumentVersion, DocumentVersion.id == Citation.source_document_version_id)
        .where(Citation.case_id == case.id)
    ).all():
        per_source[source_ref][state.value] += 1
        if rule == "unresolved.target_not_held":
            match = _TARGET.match((normalized or "").upper())
            if match:
                unheld_filings[match.group(1)] += 1
        elif rule == "unresolved.transcript_date_not_held":
            value = (normalized or "").upper().removeprefix("T.")
            unheld_dates[f"{value[:4]}-{value[4:6]}-{value[6:]}"] += 1
    ranked = sorted(
        (
            (counts["unresolved"], ref, sum(counts.values()))
            for ref, counts in per_source.items()
            if sum(counts.values()) >= 50
        ),
        key=lambda row: (-row[0], row[1]),
    )[:12]
    noisy = [
        {
            "source": ref,
            "total": total,
            "unresolved": unresolved,
            "unresolved_share": round(unresolved / total, 3),
        }
        for unresolved, ref, total in ranked
    ]
    return {
        "states": dict(states),
        "by_state_and_rule": dict(sorted(by_rule.items())),
        "distinct_unheld_filing_targets": len(unheld_filings),
        "top_unheld_filing_targets": unheld_filings.most_common(60),
        "distinct_unheld_hearing_dates": len(unheld_dates),
        "top_unheld_hearing_dates": unheld_dates.most_common(25),
        "sources_with_most_unresolved": noisy,
    }


CHECK_KEYS = (
    "appearance_signal_mismatch",
    "appearance_date_mismatch",
    "appearance_rows_without_signal_page",
    "named_witness_linked_to_code",
    "protected_witness_with_identity",
    "alias_source_mismatch",
    "ambiguous_full_names",
    "status_event_span_mismatch",
    "status_event_non_court_speaker",
    "status_event_identifier_not_in_text",
    "status_unknown_with_event",
    "status_without_supporting_event",
    "admitted_date_without_source",
    "mention_edge_unverified_evidence",
    "mention_edge_speaker_label_evidence",
    "appearance_edge_without_rule",
    "edges_without_evidence",
)


def _checks(session: Session, case: Case) -> dict[str, int]:
    checks: Counter[str] = Counter(dict.fromkeys(CHECK_KEYS, 0))
    # Appearances: exact signal span, one subject, never a protected identity.
    for appearance, page_text, hearing_date in session.execute(
        select(WitnessAppearance, DocumentPage.text, Hearing.hearing_date)
        .join(Hearing, Hearing.id == WitnessAppearance.hearing_id)
        .join(
            DocumentPage,
            (DocumentPage.document_version_id == WitnessAppearance.document_version_id)
            & (DocumentPage.pdf_page_index == WitnessAppearance.signal_pdf_page_index),
        )
        .where(Hearing.case_id == case.id, WitnessAppearance.rule_id.is_not(None))
    ).all():
        start, end = appearance.signal_char_start or 0, appearance.signal_char_end or 0
        if (page_text or "")[start:end] != appearance.signal_text:
            checks["appearance_signal_mismatch"] += 1
        if appearance.testimony_date != hearing_date:
            checks["appearance_date_mismatch"] += 1
    checks["appearance_rows_without_signal_page"] = int(
        session.scalar(
            select(func.count())
            .select_from(WitnessAppearance)
            .join(Hearing, Hearing.id == WitnessAppearance.hearing_id)
            .where(
                Hearing.case_id == case.id,
                WitnessAppearance.rule_id.is_not(None),
                ~select(DocumentPage.id)
                .where(
                    DocumentPage.document_version_id == WitnessAppearance.document_version_id,
                    DocumentPage.pdf_page_index == WitnessAppearance.signal_pdf_page_index,
                )
                .exists(),
            )
        )
        or 0
    )
    named_people = {
        person_id
        for (person_id,) in session.execute(
            select(WitnessAppearance.person_id).where(WitnessAppearance.person_id.is_not(None))
        ).all()
    }
    checks["named_witness_linked_to_code"] = int(
        session.scalar(
            select(func.count())
            .select_from(Witness)
            .where(Witness.case_id == case.id, Witness.person_id.in_(list(named_people) or [None]))
        )
        or 0
    )
    checks["protected_witness_with_identity"] = int(
        session.scalar(
            select(func.count())
            .select_from(Witness)
            .where(
                Witness.case_id == case.id,
                Witness.identity_status == WitnessIdentityStatus.PROTECTED_CODE,
                (Witness.person_id.is_not(None)) | (Witness.public_name.is_not(None)),
            )
        )
        or 0
    )
    # Full-name aliases reproduce their source span (whitespace-normalized).
    for alias, page_text in session.execute(
        select(PersonAlias, DocumentPage.text)
        .join(
            DocumentPage,
            (DocumentPage.document_version_id == PersonAlias.source_document_version_id)
            & (DocumentPage.pdf_page_index == PersonAlias.source_pdf_page_index),
        )
        .where(PersonAlias.alias_kind == "full_name")
    ).all():
        span = (page_text or "")[alias.source_char_start or 0 : alias.source_char_end or 0]
        if " ".join(span.split()) != alias.alias:
            checks["alias_source_mismatch"] += 1
    owners: dict[str, set[Any]] = defaultdict(set)
    for person_id, alias in session.execute(
        select(PersonAlias.person_id, PersonAlias.alias).where(
            PersonAlias.alias_kind == "full_name"
        )
    ).all():
        owners[alias.casefold()].add(person_id)
    checks["ambiguous_full_names"] = sum(1 for people in owners.values() if len(people) > 1)
    # Status events: exact span, court speaker only, derived status consistent.
    for event, segment_text in session.execute(
        select(ExhibitStatusEvent, TranscriptSegment.text)
        .join(TranscriptSegment, TranscriptSegment.id == ExhibitStatusEvent.transcript_segment_id)
        .where(ExhibitStatusEvent.case_id == case.id)
    ).all():
        if segment_text[event.char_start : event.char_end] != event.occurrence_text:
            checks["status_event_span_mismatch"] += 1
        if speaker_role(event.speaker) is None:
            checks["status_event_non_court_speaker"] += 1
        if event.exhibit_identifier not in event.occurrence_text:
            checks["status_event_identifier_not_in_text"] += 1
    for exhibit, event in session.execute(
        select(Exhibit, ExhibitStatusEvent)
        .outerjoin(ExhibitStatusEvent, ExhibitStatusEvent.id == Exhibit.status_event_id)
        .where(Exhibit.case_id == case.id)
    ).all():
        if exhibit.status == "unknown" and event is not None:
            checks["status_unknown_with_event"] += 1
        if exhibit.status != "unknown" and (
            event is None or event.event_type != exhibit.status or event.exhibit_id != exhibit.id
        ):
            checks["status_without_supporting_event"] += 1
        if exhibit.admitted_date is not None:
            checks["admitted_date_without_source"] += 1
    # Typed edges: evidence must exist, be verified/rule-backed, and counts reproduce.
    for _edge, occurrence in session.execute(
        select(Relationship, EntityOccurrence)
        .join(EntityOccurrence, EntityOccurrence.id == Relationship.entity_occurrence_id)
        .where(Relationship.case_id == case.id)
    ).all():
        if occurrence.mention_state != "verified" or occurrence.rule_id is None:
            checks["mention_edge_unverified_evidence"] += 1
        if occurrence.char_anchor not in {"transcript_segment_text", "document_page_text"}:
            checks["mention_edge_speaker_label_evidence"] += 1
    for _edge, appearance in session.execute(
        select(Relationship, WitnessAppearance)
        .join(WitnessAppearance, WitnessAppearance.id == Relationship.witness_appearance_id)
        .where(Relationship.case_id == case.id)
    ).all():
        if appearance.rule_id is None:
            checks["appearance_edge_without_rule"] += 1
    checks["edges_without_evidence"] = int(
        session.scalar(
            select(func.count())
            .select_from(Relationship)
            .where(
                Relationship.case_id == case.id,
                Relationship.citation_id.is_(None),
                Relationship.entity_occurrence_id.is_(None),
                Relationship.witness_appearance_id.is_(None),
            )
        )
        or 0
    )
    return {key: int(value) for key, value in sorted(checks.items())}


def _capture_plan(citations: dict[str, Any], corpus: dict[str, Any]) -> dict[str, Any]:
    filings = [
        {"filing": target, "citations": count}
        for target, count in citations["top_unheld_filing_targets"]
        if not target.startswith(("IA", "PL"))
    ][:50]
    subcase = [
        {"filing": target, "citations": count}
        for target, count in citations["top_unheld_filing_targets"]
        if target.startswith(("IA", "PL"))
    ]
    return {
        "principle": (
            "Official public KSC sources only, through the operator-attached browser "
            "(ADR-011). Ranked by how many held citations each record would resolve; "
            "no record is guessed or fetched outside the public repository UI."
        ),
        "main_case_filings_by_citation_count": filings,
        "appeal_subcase_filings_by_citation_count": subcase,
        "transcripts_by_cited_hearing_date": [
            {"hearing_date": day, "citations": count}
            for day, count in citations["top_unheld_hearing_dates"]
        ],
        "language_counterparts_missing": corpus["language_counterparts_by_class"],
    }


def run_phase19b_report(session: Session, case: Case, generated_at: date) -> dict[str, Any]:
    corpus = _corpus(session, case)
    citations = _citations(session, case)
    checks = _checks(session, case)
    mentions = run_phase19a_gate(session, case, generated_at)
    return {
        "schema_version": 1,
        "phase": "19B",
        "generated_at": generated_at.isoformat(),
        "case_number": case.case_number,
        "corpus": corpus,
        "entities": _entities(session, case),
        "relationships": _relationships(session, case),
        "citations": citations,
        "mentions": {
            "total_rows": mentions.total_rows,
            "verified": mentions.total_verified,
            "review_required": mentions.total_review_required,
            "by_rule": mentions.by_rule,
            "phase19a_gate_passed": mentions.passed,
            "provenance_violations": mentions.provenance_violations,
        },
        "checks": checks,
        "capture_plan": _capture_plan(citations, corpus),
        "passed": mentions.passed and all(value == 0 for value in checks.values()),
    }


def write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
