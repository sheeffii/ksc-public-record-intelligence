"""Fail-closed public filtering shared by every repository query."""

from __future__ import annotations

from typing import Any

from sqlalchemy import ColumnElement, and_, or_

from ksc_api.models import (
    PUBLIC_VISIBILITIES,
    Citation,
    Document,
    Exhibit,
    GraphNode,
    Hearing,
    ResolutionState,
    VerificationState,
)


def public_visibility(column: Any) -> Any:
    """PUBLIC and PUBLIC_REDACTED only. UNKNOWN, NOT_PUBLIC and
    PRIVATE_AUTHORIZED are excluded; there is no override in public mode."""
    return column.in_(list(PUBLIC_VISIBILITIES))


def not_rejected(model: Any) -> Any:
    """Facts a human reviewer rejected never surface."""
    return model.verification_state != VerificationState.HUMAN_REJECTED


def citation_resolved() -> ColumnElement[bool]:
    """Anything that depends on an unresolved citation is withheld."""
    return Citation.resolution_state == ResolutionState.RESOLVED


def node_is_public(node: Any, document: Any, exhibit: Any, hearing: Any) -> ColumnElement[bool]:
    """A graph node is public when the entity it wraps is. Entities without a
    visibility column (persons, incidents, findings, …) are public records by
    construction; witnesses are public *codes* — identity is decided at
    serialisation, never here."""
    return and_(
        or_(node.document_id.is_(None), public_visibility(document.visibility)),
        or_(node.exhibit_id.is_(None), public_visibility(exhibit.visibility)),
        or_(node.hearing_id.is_(None), public_visibility(hearing.visibility)),
    )


__all__ = [
    "Document",
    "Exhibit",
    "GraphNode",
    "Hearing",
    "citation_resolved",
    "node_is_public",
    "not_rejected",
    "public_visibility",
]
