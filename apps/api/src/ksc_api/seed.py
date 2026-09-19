"""Seed basic, public case metadata for KSC-BC-2020-06.

Idempotent: re-running updates nothing destructive and never duplicates the
case. No documents are created — Phase 4 ingests nothing.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.config import get_settings
from ksc_api.db.session import session_scope
from ksc_api.logging_config import configure_logging
from ksc_api.models import AuditLog, Case

log = logging.getLogger(__name__)

# Public, official case metadata only. Everything here appears on the Kosovo
# Specialist Chambers' public website. Nothing below is an assessment.
CASE_SEED = {
    "case_number": "KSC-BC-2020-06",
    "title": (
        "The Specialist Prosecutor v. Hashim Thaçi, Kadri Veseli, Rexhep Selimi and Jakup Krasniqi"
    ),
    "court": "Kosovo Specialist Chambers",
    "seat": "The Hague, the Netherlands",
    "official_source_url": "https://www.scp-ks.org",
    "description": (
        "Public-record research case. Only lawfully public court materials will "
        "ever be ingested. No documents have been ingested yet."
    ),
}


def seed_case(session: Session) -> tuple[Case, bool]:
    """Insert the case if missing. Returns (case, created)."""
    existing = session.scalar(select(Case).where(Case.case_number == CASE_SEED["case_number"]))
    if existing is not None:
        return existing, False

    case = Case(**CASE_SEED)
    session.add(case)
    session.add(
        AuditLog(
            actor="system:seed",
            action="case.seeded",
            entity_type="case",
            entity_id=case.case_number,
            detail={"source": "ksc_api.seed"},
        )
    )
    session.flush()
    return case, True


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    with session_scope() as session:
        case, created = seed_case(session)
    log.info("case %s %s", case.case_number, "created" if created else "already present")


if __name__ == "__main__":
    main()
