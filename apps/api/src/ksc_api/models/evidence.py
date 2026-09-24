"""Exhibit, Incident, Event, Claim, ClaimMention, Finding, FindingEvidenceLink,
Argument, ArgumentResponse.

Distinctions these tables keep apart:

- `Incident` (a structured alleged event in case material; "as charged" is not
  a determination) vs `Event` (any typed timeline item — historical, document,
  filing, testimony or decision date — with its own precision).
- `Claim` (a proposition that exists in the research system; not a truth
  claim) vs `Finding` (an exact court finding with paragraph coordinates).
- `Argument` (a party position) vs `Finding` (what the Court found).

Every link to evidence goes through a `citations` row.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.enums import (
    ArgumentResponseKind,
    ClaimOrigin,
    ClaimStance,
    DatePrecision,
    DateType,
    FindingLinkType,
    Party,
    Visibility,
    db_enum,
)
from ksc_api.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VerificationMixin,
    human_verification_requires_reviewer,
)

if TYPE_CHECKING:
    from ksc_api.models.actor import Location, Person, Witness
    from ksc_api.models.citation import Citation
    from ksc_api.models.document import Document, DocumentVersion
    from ksc_api.models.source_record import SourceRecord


class Exhibit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exhibits"
    __table_args__ = (
        UniqueConstraint("case_id", "official_exhibit_id", name="uq_exhibits_case_official_id"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # The court's own exhibit number, e.g. "P00123" / "D00045". Internal UUID is separate.
    official_exhibit_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unknown", server_default="unknown"
    )
    tendered_by: Mapped[Party | None] = mapped_column(db_enum(Party, name="party"))
    through_witness_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("witnesses.id", ondelete="SET NULL")
    )
    admitted_date: Mapped[date | None] = mapped_column(Date)
    document_date: Mapped[date | None] = mapped_column(Date)
    # Public artifact of the exhibit, when one exists in the public record.
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL")
    )
    visibility: Mapped[Visibility] = mapped_column(
        db_enum(Visibility, name="visibility"),
        nullable=False,
        default=Visibility.PUBLIC,
        server_default=Visibility.PUBLIC.value,
    )

    through_witness: Mapped[Witness | None] = relationship()
    document_version: Mapped[DocumentVersion | None] = relationship()


class Incident(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "incidents"
    __table_args__ = (
        UniqueConstraint("case_id", "slug", name="uq_incidents_case_slug"),
        CheckConstraint(
            "date_to IS NULL OR date_from IS NULL OR date_to >= date_from", name="date_range"
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    # As pleaded / as described in case material — not a determination.
    summary: Mapped[str | None] = mapped_column(Text)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL")
    )
    date_from: Mapped[date | None] = mapped_column(Date)
    date_to: Mapped[date | None] = mapped_column(Date)
    date_precision: Mapped[DatePrecision] = mapped_column(
        db_enum(DatePrecision, name="date_precision"),
        nullable=False,
        default=DatePrecision.UNKNOWN,
        server_default=DatePrecision.UNKNOWN.value,
    )
    # Counts / charges as pleaded, e.g. [{"count": 1, "label": "…"}]. "As charged — not a determination".
    charges_pleaded: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)

    location: Mapped[Location | None] = relationship()


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A typed timeline item. Five date types are never merged."""

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "date_to IS NULL OR date_from IS NULL OR date_to >= date_from", name="date_range"
        ),
        CheckConstraint(
            "date_precision = 'unknown' OR date_from IS NOT NULL", name="known_precision_has_date"
        ),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    date_type: Mapped[DateType] = mapped_column(db_enum(DateType, name="date_type"), nullable=False)
    date_from: Mapped[date | None] = mapped_column(Date)
    date_to: Mapped[date | None] = mapped_column(Date)
    date_precision: Mapped[DatePrecision] = mapped_column(
        db_enum(DatePrecision, name="date_precision"),
        nullable=False,
        default=DatePrecision.UNKNOWN,
        server_default=DatePrecision.UNKNOWN.value,
    )
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL")
    )
    hearing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hearings.id", ondelete="SET NULL")
    )
    # Provenance for the date itself.
    citation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL")
    )
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_records.id", ondelete="SET NULL"), index=True
    )
    extraction_origin: Mapped[str] = mapped_column(
        String(32), nullable=False, default="manual", server_default="manual"
    )

    citation: Mapped[Citation | None] = relationship()
    source_record: Mapped[SourceRecord | None] = relationship()


class Claim(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """A proposition that exists in the structured research system. Storing a
    claim says nothing about whether it is true. AI-extracted never means
    verified."""

    __tablename__ = "claims"
    __table_args__ = (
        UniqueConstraint("case_id", "claim_key", name="uq_claims_case_key"),
        # "AI-extracted never means verified": a human state needs a named
        # reviewer (see mixin); AI code paths have none to give.
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    claim_key: Mapped[str] = mapped_column(String(64), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    origin: Mapped[ClaimOrigin] = mapped_column(
        db_enum(ClaimOrigin, name="claim_origin"), nullable=False
    )
    created_by: Mapped[str | None] = mapped_column(String(128))
    # Where the claim was first taken from, when source-extracted.
    source_citation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL")
    )

    source_citation: Mapped[Citation | None] = relationship()
    mentions: Mapped[list[ClaimMention]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimMention(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """Claim → exact citation, with a stance scoped to that claim."""

    __tablename__ = "claim_mentions"
    __table_args__ = (
        UniqueConstraint("claim_id", "citation_id", name="uq_claim_mentions_claim_citation"),
        human_verification_requires_reviewer(),
    )

    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    stance: Mapped[ClaimStance] = mapped_column(
        db_enum(ClaimStance, name="claim_stance"), nullable=False
    )
    # Verbatim excerpt from the public source, when held. Never paraphrased.
    quote_text: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)

    claim: Mapped[Claim] = relationship(back_populates="mentions")
    citation: Mapped[Citation] = relationship()


class Finding(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """A court finding, in the Court's words, at its paragraph coordinates.
    Never an AI conclusion."""

    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("case_id", "finding_key", name="uq_findings_case_key"),
        CheckConstraint("para_from >= 1", name="para_from_positive"),
        CheckConstraint("para_to IS NULL OR para_to >= para_from", name="para_range"),
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    finding_key: Mapped[str] = mapped_column(String(64), nullable=False)
    judgment_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    judgment_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="RESTRICT"),
        index=True,
    )
    extraction_origin: Mapped[str] = mapped_column(
        String(32), nullable=False, default="manual", server_default="manual"
    )
    # Exact court text.
    text: Mapped[str] = mapped_column(Text, nullable=False)
    para_from: Mapped[int] = mapped_column(Integer, nullable=False)
    para_to: Mapped[int | None] = mapped_column(Integer)
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), index=True
    )
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), index=True
    )
    charge_ref: Mapped[str | None] = mapped_column(String(128))
    legal_element: Mapped[str | None] = mapped_column(String(255))
    mode_of_liability: Mapped[str | None] = mapped_column(String(128))
    # The finding's own coordinates as a resolved citation, when indexed.
    citation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL", use_alter=True)
    )

    judgment_document: Mapped[Document] = relationship()
    judgment_version: Mapped[DocumentVersion | None] = relationship()
    person: Mapped[Person | None] = relationship()
    incident: Mapped[Incident | None] = relationship()
    citation: Mapped[Citation | None] = relationship(foreign_keys=[citation_id])
    evidence_links: Mapped[list[FindingEvidenceLink]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )


class FindingEvidenceLink(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "finding_evidence_links"
    __table_args__ = (
        UniqueConstraint(
            "finding_id", "citation_id", "link_type", name="uq_finding_evidence_links_triplet"
        ),
        CheckConstraint(
            "court_cited OR court_cited_para IS NULL", name="cited_para_needs_court_cited"
        ),
        CheckConstraint(
            "relationship_basis IN ('explicit_court_citation', 'related_public_record')",
            name="relationship_basis_allowed",
        ),
        CheckConstraint(
            "court_cited = (relationship_basis = 'explicit_court_citation')",
            name="court_cited_matches_basis",
        ),
        CheckConstraint(
            "source_category IN ('court_finding', 'spo_argument', 'defence_argument', "
            "'witness_testimony', 'document_exhibit', 'court_response', 'human_note', "
            "'ai_analysis', 'other')",
            name="source_category_allowed",
        ),
        human_verification_requires_reviewer(),
    )

    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    link_type: Mapped[FindingLinkType] = mapped_column(
        db_enum(FindingLinkType, name="finding_link_type"), nullable=False
    )
    # Whether the Court itself cited this source for the finding, and where.
    court_cited: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    court_cited_para: Mapped[int | None] = mapped_column(Integer)
    relationship_basis: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="related_public_record",
        server_default="related_public_record",
    )
    source_category: Mapped[str] = mapped_column(String(32), nullable=False)
    extraction_origin: Mapped[str] = mapped_column(
        String(32), nullable=False, default="manual", server_default="manual"
    )
    note: Mapped[str | None] = mapped_column(Text)

    finding: Mapped[Finding] = relationship(back_populates="evidence_links")
    citation: Mapped[Citation] = relationship()


class Argument(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """A party (or Court) position. Kept distinct from findings."""

    __tablename__ = "arguments"
    __table_args__ = (
        UniqueConstraint("case_id", "argument_key", name="uq_arguments_case_key"),
        CheckConstraint(
            "para_to IS NULL OR para_from IS NULL OR para_to >= para_from", name="para_range"
        ),
        CheckConstraint(
            "source_scope IN ('direct_source', 'court_summary', 'source_missing')",
            name="source_scope_allowed",
        ),
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    argument_key: Mapped[str] = mapped_column(String(64), nullable=False)
    party: Mapped[Party] = mapped_column(db_enum(Party, name="party"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), index=True
    )
    para_from: Mapped[int | None] = mapped_column(Integer)
    para_to: Mapped[int | None] = mapped_column(Integer)
    citation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL")
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="SET NULL"), index=True
    )
    source_scope: Mapped[str] = mapped_column(
        String(32), nullable=False, default="direct_source", server_default="direct_source"
    )
    underlying_source_ref: Mapped[str | None] = mapped_column(String(255))
    extraction_origin: Mapped[str] = mapped_column(
        String(32), nullable=False, default="manual", server_default="manual"
    )

    document: Mapped[Document | None] = relationship()
    document_version: Mapped[DocumentVersion | None] = relationship()
    citation: Mapped[Citation | None] = relationship()
    finding: Mapped[Finding | None] = relationship()
    responses: Mapped[list[ArgumentResponse]] = relationship(
        back_populates="argument",
        foreign_keys="ArgumentResponse.argument_id",
        cascade="all, delete-orphan",
    )


class ArgumentResponse(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    """`response_argument` responds to / disputes / concurs with / rules on `argument`."""

    __tablename__ = "argument_responses"
    __table_args__ = (
        UniqueConstraint(
            "argument_id", "response_argument_id", "response_kind", name="uq_argument_responses"
        ),
        CheckConstraint("argument_id <> response_argument_id", name="no_self_response"),
        human_verification_requires_reviewer(),
    )

    argument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("arguments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    response_argument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("arguments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    response_kind: Mapped[ArgumentResponseKind] = mapped_column(
        db_enum(ArgumentResponseKind, name="argument_response_kind"), nullable=False
    )
    citation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citations.id", ondelete="SET NULL")
    )
    note: Mapped[str | None] = mapped_column(Text)
    extraction_origin: Mapped[str] = mapped_column(
        String(32), nullable=False, default="manual", server_default="manual"
    )

    argument: Mapped[Argument] = relationship(
        back_populates="responses", foreign_keys=[argument_id]
    )
    response_argument: Mapped[Argument] = relationship(foreign_keys=[response_argument_id])
    citation: Mapped[Citation | None] = relationship()
