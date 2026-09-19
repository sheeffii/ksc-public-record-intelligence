"""Citation contract — mirrors `Citation` in packages/shared (HANDOFF.md §9).

`resolved is False` means the client renders no chip and withholds or marks
whatever depended on it. `display` is the persisted, pre-formatted string; the
literal "UNRESOLVED" for anything not resolved.
"""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import Field

from ksc_api.models.enums import CitationType, ResolutionState, VerificationState
from ksc_api.schemas.common import ReadModel

# Subset of source types that can back a citation. AI never cites itself.
CitableSourceType = Literal["court", "witness", "spo", "defence", "exhibit"]


class CitationRead(ReadModel):
    id: uuid.UUID
    source_type: CitableSourceType
    # The target record's own reference ("F-DEMO-001", "P-DEMO-001", "W-DEMO-001").
    ref: str
    # `official_ref` of the target document, when the target lives in one.
    doc_id: str | None
    citation_type: CitationType
    raw_text: str
    page: int | None = Field(default=None, ge=1)
    para_from: int | None = None
    para_to: int | None = None
    line_from: int | None = None
    line_to: int | None = None
    resolution_state: ResolutionState
    resolved: bool
    display: str
    verification_state: VerificationState


class IdentifierMatch(ReadModel):
    identifier: str
    entity_kind: str
    entity_id: uuid.UUID
    ref: str


class ResolveResult(ReadModel):
    """Lookup against the identifier index. 0 matches → unresolved,
    1 → resolved, more → ambiguous (never auto-picked)."""

    query: str
    normalized: str
    state: ResolutionState
    matches: list[IdentifierMatch]
