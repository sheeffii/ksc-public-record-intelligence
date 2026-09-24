"""Phase 17C structured-data integrity and provenance gate."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import FromClause

from ksc_api.models import (
    Case,
    Citation,
    EntityOccurrence,
    Event,
    Exhibit,
    Hearing,
    Organization,
    Person,
    Relationship,
    ResolutionState,
    Transcript,
    TranscriptSegment,
    Witness,
    WitnessIdentityStatus,
)


class StructuredQualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: date
    case_number: str
    people: int = Field(ge=0)
    witnesses: int = Field(ge=0)
    organizations: int = Field(ge=0)
    exhibits: int = Field(ge=0)
    hearings: int = Field(ge=0)
    statements: int = Field(ge=0)
    events: int = Field(ge=0)
    relationships: int = Field(ge=0)
    occurrences: int = Field(ge=0)
    provenance_verified: int = Field(ge=0)
    review_required: int = Field(ge=0)
    provenance_violations: int = Field(ge=0)
    protected_identity_violations: int = Field(ge=0)
    invalid_exhibit_statuses: int = Field(ge=0)
    citations_resolved: int = Field(ge=0)
    citations_ambiguous: int = Field(ge=0)
    citations_unresolved: int = Field(ge=0)
    citations_invalid: int = Field(ge=0)
    passed: bool


def run_phase17c_gate(session: Session, case: Case, generated_at: date) -> StructuredQualityReport:
    def count(table: FromClause) -> int:
        return int(
            session.scalar(
                select(func.count()).select_from(table).where(table.c.case_id == case.id)
            )
            or 0
        )

    occurrences = count(EntityOccurrence.__table__)
    review_required = int(
        session.scalar(
            select(func.count())
            .select_from(EntityOccurrence)
            .where(EntityOccurrence.case_id == case.id, EntityOccurrence.review_required.is_(True))
        )
        or 0
    )
    provenance_violations = int(
        session.scalar(
            select(func.count())
            .select_from(EntityOccurrence)
            .where(
                EntityOccurrence.case_id == case.id,
                or_(
                    EntityOccurrence.document_version_id.is_(None),
                    EntityOccurrence.occurrence_text == "",
                    EntityOccurrence.char_end < EntityOccurrence.char_start,
                ),
            )
        )
        or 0
    )
    protected_identity_violations = int(
        session.scalar(
            select(func.count())
            .select_from(Witness)
            .where(
                Witness.case_id == case.id,
                Witness.identity_status == WitnessIdentityStatus.PROTECTED_CODE,
                or_(Witness.person_id.is_not(None), Witness.public_name.is_not(None)),
            )
        )
        or 0
    )
    invalid_exhibit_statuses = int(
        session.scalar(
            select(func.count())
            .select_from(Exhibit)
            .where(
                Exhibit.case_id == case.id,
                Exhibit.status.not_in(("unknown", "tendered", "admitted", "rejected", "other")),
            )
        )
        or 0
    )
    citation_states: dict[ResolutionState, int] = {
        state: int(total)
        for state, total in session.execute(
            select(Citation.resolution_state, func.count(Citation.id))
            .where(Citation.case_id == case.id)
            .group_by(Citation.resolution_state)
        ).all()
    }
    passed = (
        occurrences > 0
        and provenance_violations == 0
        and protected_identity_violations == 0
        and invalid_exhibit_statuses == 0
    )
    statements = int(
        session.scalar(
            select(func.count(TranscriptSegment.id))
            .join(Transcript, Transcript.id == TranscriptSegment.transcript_id)
            .join(Hearing, Hearing.id == Transcript.hearing_id)
            .where(Hearing.case_id == case.id)
        )
        or 0
    )
    return StructuredQualityReport(
        generated_at=generated_at,
        case_number=case.case_number,
        people=count(Person.__table__),
        witnesses=count(Witness.__table__),
        organizations=count(Organization.__table__),
        exhibits=count(Exhibit.__table__),
        hearings=count(Hearing.__table__),
        statements=statements,
        events=count(Event.__table__),
        relationships=count(Relationship.__table__),
        occurrences=occurrences,
        provenance_verified=occurrences - review_required,
        review_required=review_required,
        provenance_violations=provenance_violations,
        protected_identity_violations=protected_identity_violations,
        invalid_exhibit_statuses=invalid_exhibit_statuses,
        citations_resolved=int(citation_states.get(ResolutionState.RESOLVED, 0)),
        citations_ambiguous=int(citation_states.get(ResolutionState.AMBIGUOUS, 0)),
        citations_unresolved=int(citation_states.get(ResolutionState.UNRESOLVED, 0)),
        citations_invalid=int(citation_states.get(ResolutionState.INVALID, 0)),
        passed=passed,
    )


def write_phase17c_report(report: StructuredQualityReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
