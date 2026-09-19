from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ksc_api.models.enums import VerificationState, db_enum


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class VerificationMixin:
    """Reviewer state on a fact row. Verification is a first-class column with
    reviewer identity, never a boolean (docs/DATA_MODEL.md)."""

    verification_state: Mapped[VerificationState] = mapped_column(
        db_enum(VerificationState, name="verification_state"),
        nullable=False,
        default=VerificationState.UNREVIEWED,
        server_default=VerificationState.UNREVIEWED.value,
    )
    verified_by: Mapped[str | None] = mapped_column(String(128))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


def human_verification_requires_reviewer() -> CheckConstraint:
    """HUMAN_VERIFIED / HUMAN_REJECTED need a named reviewer. Nothing — and in
    particular no AI path — can promote a row to a human state anonymously."""

    return CheckConstraint(
        "verification_state NOT IN ('human_verified', 'human_rejected') "
        "OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
        # The metadata naming convention prefixes "ck_<table>_".
        name="human_verification_has_reviewer",
    )
