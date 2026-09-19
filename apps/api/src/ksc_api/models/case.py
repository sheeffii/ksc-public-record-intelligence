"""Case — the top-level container. Phase 4 seeds exactly one: KSC-BC-2020-06."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ksc_api.models.document import Document


class Case(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cases"

    # Official case number, e.g. "KSC-BC-2020-06". Never re-keyed; it is the
    # identifier researchers cite.
    case_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    court: Mapped[str] = mapped_column(String(255), nullable=False)
    seat: Mapped[str | None] = mapped_column(String(255))
    # Root of the court's official public site — the only lawful ingestion
    # source. Specific document URLs are never guessed (docs/SECURITY.md).
    official_source_url: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)

    documents: Mapped[list[Document]] = relationship(back_populates="case")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Case {self.case_number}>"
