"""AuditLog — append-only record of system and reviewer actions.

Logged detail must never contain document text or anything that could identify
a protected witness (docs/SECURITY.md).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ksc_api.db.base import Base
from ksc_api.models.mixins import UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_log"

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    # "system", a worker name, or a reviewer identifier. Nullable for anonymous.
    actor: Mapped[str | None] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(128))
    detail: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
