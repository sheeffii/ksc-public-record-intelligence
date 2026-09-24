"""Person, PersonAlias, Witness, Organization, Location.

A witness is not automatically a public person. `Witness` links to `Person`
only when an official public source identifies them; for a protected code the
link and public name are structurally absent (CHECK constraint), so nothing
downstream can render an identity. No table here — or anywhere — stores a
score, rank, weight or probability about a person.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.enums import Party, WitnessIdentityStatus, db_enum
from ksc_api.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from ksc_api.models.hearing import WitnessAppearance


class Person(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A named person in the public record."""

    __tablename__ = "persons"
    __table_args__ = (UniqueConstraint("case_id", "slug", name="uq_persons_case_slug"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Public role as stated in the record ("accused", "counsel", "expert", …).
    public_role: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)

    aliases: Mapped[list[PersonAlias]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    witnesses: Mapped[list[Witness]] = relationship(back_populates="person")


class PersonAlias(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "person_aliases"
    __table_args__ = (
        UniqueConstraint("person_id", "alias", name="uq_person_aliases_person_alias"),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str | None] = mapped_column(String(16))

    person: Mapped[Person] = relationship(back_populates="aliases")


class Witness(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "witnesses"
    __table_args__ = (
        UniqueConstraint("case_id", "code", name="uq_witnesses_case_code"),
        # Protection is structural: a protected code can carry no identity.
        CheckConstraint(
            "identity_status <> 'protected_code' OR (person_id IS NULL AND public_name IS NULL)",
            name="protected_code_has_no_identity",
        ),
        # A public name is only stored when the status says so.
        CheckConstraint(
            "identity_status = 'public' OR public_name IS NULL", name="public_name_requires_public"
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # The public witness code, e.g. "W01234". Never translated.
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    identity_status: Mapped[WitnessIdentityStatus] = mapped_column(
        db_enum(WitnessIdentityStatus, name="witness_identity_status"),
        nullable=False,
        default=WitnessIdentityStatus.PROTECTED_CODE,
        server_default=WitnessIdentityStatus.PROTECTED_CODE.value,
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), index=True
    )
    public_name: Mapped[str | None] = mapped_column(String(255))
    called_by: Mapped[Party | None] = mapped_column(db_enum(Party, name="party"))
    # Public descriptions of measures in force, e.g. ["pseudonym", "face distortion"].
    protective_measures: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )

    person: Mapped[Person | None] = relationship(back_populates="witnesses")
    appearances: Mapped[list[WitnessAppearance]] = relationship(
        back_populates="witness", cascade="all, delete-orphan"
    )

    @property
    def is_protected(self) -> bool:
        """Fails closed: anything that is not explicitly public is protected."""
        return self.identity_status != WitnessIdentityStatus.PUBLIC


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (UniqueConstraint("case_id", "slug", name="uq_organizations_case_slug"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str | None] = mapped_column(String(64))
    name_variants: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    description: Mapped[str | None] = mapped_column(Text)


class EntityOccurrence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An exact public-source occurrence behind an actor/exhibit projection."""

    __tablename__ = "entity_occurrences"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(person_id, witness_id, organization_id, exhibit_id) = 1",
            name="exactly_one_entity",
        ),
        CheckConstraint("char_start >= 0", name="char_start_non_negative"),
        CheckConstraint("char_end >= char_start", name="char_range"),
        UniqueConstraint(
            "document_version_id",
            "transcript_segment_id",
            "char_start",
            "char_end",
            "person_id",
            "witness_id",
            "organization_id",
            "exhibit_id",
            name="uq_entity_occurrences_source_entity",
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), index=True
    )
    witness_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("witnesses.id", ondelete="CASCADE"), index=True
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    exhibit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exhibits.id", ondelete="CASCADE"), index=True
    )
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False
    )
    transcript_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transcript_segments.id", ondelete="CASCADE")
    )
    page_number: Mapped[int | None] = mapped_column(Integer)
    pdf_page_index: Mapped[int | None] = mapped_column(Integer)
    line_from: Mapped[int | None] = mapped_column(Integer)
    line_to: Mapped[int | None] = mapped_column(Integer)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    occurrence_text: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_origin: Mapped[str] = mapped_column(
        String(32), nullable=False, default="deterministic", server_default="deterministic"
    )
    review_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )


class Location(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("case_id", "slug", name="uq_locations_case_slug"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Recorded spellings, e.g. Qirez / Çirez / Cirez / Ćirez. Never merged away.
    name_variants: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    kind: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
