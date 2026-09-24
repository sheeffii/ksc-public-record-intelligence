"""Phase 19B structured-intelligence pipeline.

Order matters and is fixed:

1. source-backed full-name aliases (case caption),
2. witness ↔ hearing appearances from transcript page headers (and publicly
   named witnesses as people),
3. exhibit status events and derived status,
4. verified mentions (Phase 19A projector, now aware of full-name aliases),
5. typed evidence-backed edges (TESTIFIED_AT, MENTIONED_IN).

Step 4 replaces occurrence rows, which cascades to MENTIONED_IN edges, so step
5 always runs last. Citation re-resolution and citation edges (`reresolve`,
`build-evidence`) run before this pipeline.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import Case, ProcessingRun
from ksc_ingestion.exhibit_status import project_status_events
from ksc_ingestion.identity_projection import project_caption_aliases
from ksc_ingestion.typed_edges import project_typed_edges
from ksc_ingestion.verified_mentions import Phase19MentionProjector
from ksc_ingestion.witness_appearances import project_appearances

PROCESSOR = "phase19b-intelligence"
PROCESSOR_VERSION = "1"


@dataclass(frozen=True)
class IntelligenceResult:
    run_id: uuid.UUID
    detail: dict[str, Any]


class Phase19BPipeline:
    def __init__(self, sessions: sessionmaker[Session], *, case_number: str) -> None:
        self.sessions = sessions
        self.case_number = case_number

    def _case(self, session: Session) -> Case:
        case = session.scalar(select(Case).where(Case.case_number == self.case_number))
        if case is None:
            raise RuntimeError(f"case {self.case_number} is not seeded")
        return case

    def run(self) -> IntelligenceResult:
        detail: dict[str, Any] = {}
        with self.sessions() as session, session.begin():
            case = self._case(session)
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
            run_id = run.id
            detail["aliases"] = asdict(project_caption_aliases(session, case))
            detail["appearances"] = asdict(project_appearances(session, case, run_id))
            detail["exhibit_status"] = asdict(project_status_events(session, case, run_id))

        mentions = Phase19MentionProjector(self.sessions, case_number=self.case_number).run()
        detail["mentions"] = {
            "run_id": str(mentions.run_id),
            "by_kind_state": mentions.by_kind_state,
            "by_rule": mentions.by_rule,
        }

        with self.sessions() as session, session.begin():
            case = self._case(session)
            detail["typed_edges"] = asdict(project_typed_edges(session, case))
            finished = session.get(ProcessingRun, run_id)
            assert finished is not None
            finished.status = "completed"
            finished.finished_at = datetime.now(UTC)
            finished.detail = detail
        return IntelligenceResult(run_id=run_id, detail=detail)
