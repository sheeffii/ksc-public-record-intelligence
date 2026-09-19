"""GraphNode and Relationship — the provenance-backed evidence graph.

Polymorphism without fake foreign keys: `graph_nodes` is a registry row per
entity that can take part in the graph. Each row carries exactly one non-NULL
foreign key (CHECK `num_nonnulls(...) = 1`) to the real entity table, with
ON DELETE CASCADE, so a node cannot outlive its entity and a relationship
cannot outlive its nodes. `relationships` therefore never holds a bare UUID.

Every relationship requires a citation (`citation_id NOT NULL`). A connection
never implies wrongdoing, responsibility, agreement, endorsement or guilt.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ksc_api.db.base import Base
from ksc_api.models.enums import EntityKind, RelationshipType, db_enum
from ksc_api.models.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VerificationMixin,
    human_verification_requires_reviewer,
)

if TYPE_CHECKING:
    from ksc_api.models.citation import Citation

NODE_FK_COLUMNS: dict[EntityKind, str] = {
    EntityKind.PERSON: "person_id",
    EntityKind.WITNESS: "witness_id",
    EntityKind.ORGANIZATION: "organization_id",
    EntityKind.LOCATION: "location_id",
    EntityKind.DOCUMENT: "document_id",
    EntityKind.EXHIBIT: "exhibit_id",
    EntityKind.INCIDENT: "incident_id",
    EntityKind.EVENT: "event_id",
    EntityKind.CLAIM: "claim_id",
    EntityKind.FINDING: "finding_id",
    EntityKind.ARGUMENT: "argument_id",
    EntityKind.HEARING: "hearing_id",
}


def _fk(table: str) -> Mapped[uuid.UUID | None]:
    return mapped_column(UUID(as_uuid=True), ForeignKey(f"{table}.id", ondelete="CASCADE"))


class GraphNode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "graph_nodes"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(" + ", ".join(NODE_FK_COLUMNS.values()) + ") = 1",
            name="exactly_one_entity",
        ),
        # The kind column must agree with the populated foreign key.
        CheckConstraint(
            " OR ".join(
                f"(entity_kind = '{kind.value}' AND {col} IS NOT NULL)"
                for kind, col in NODE_FK_COLUMNS.items()
            ),
            name="kind_matches_entity",
        ),
        *[
            Index(f"uq_graph_nodes_{col}", col, unique=True, postgresql_where=f"{col} IS NOT NULL")
            for col in NODE_FK_COLUMNS.values()
        ],
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    entity_kind: Mapped[EntityKind] = mapped_column(
        db_enum(EntityKind, name="entity_kind"), nullable=False
    )
    # Denormalised public label for graph rendering (a W-code for a witness).
    label: Mapped[str] = mapped_column(String(255), nullable=False)

    person_id: Mapped[uuid.UUID | None] = _fk("persons")
    witness_id: Mapped[uuid.UUID | None] = _fk("witnesses")
    organization_id: Mapped[uuid.UUID | None] = _fk("organizations")
    location_id: Mapped[uuid.UUID | None] = _fk("locations")
    document_id: Mapped[uuid.UUID | None] = _fk("documents")
    exhibit_id: Mapped[uuid.UUID | None] = _fk("exhibits")
    incident_id: Mapped[uuid.UUID | None] = _fk("incidents")
    event_id: Mapped[uuid.UUID | None] = _fk("events")
    claim_id: Mapped[uuid.UUID | None] = _fk("claims")
    finding_id: Mapped[uuid.UUID | None] = _fk("findings")
    argument_id: Mapped[uuid.UUID | None] = _fk("arguments")
    hearing_id: Mapped[uuid.UUID | None] = _fk("hearings")

    outgoing: Mapped[list[Relationship]] = relationship(
        back_populates="from_node", foreign_keys="Relationship.from_node_id"
    )
    incoming: Mapped[list[Relationship]] = relationship(
        back_populates="to_node", foreign_keys="Relationship.to_node_id"
    )

    @property
    def entity_id(self) -> uuid.UUID:
        value: uuid.UUID | None = getattr(self, NODE_FK_COLUMNS[self.entity_kind])
        assert value is not None  # guaranteed by CHECK constraints
        return value


class Relationship(UUIDPrimaryKeyMixin, TimestampMixin, VerificationMixin, Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint(
            "from_node_id",
            "to_node_id",
            "relationship_type",
            "citation_id",
            name="uq_relationships_edge_citation",
        ),
        CheckConstraint("from_node_id <> to_node_id", name="no_self_loop"),
        human_verification_requires_reviewer(),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    from_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        db_enum(RelationshipType, name="relationship_type"), nullable=False
    )
    # Provenance is mandatory. RESTRICT: a citation in use cannot be deleted.
    citation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text)

    from_node: Mapped[GraphNode] = relationship(
        back_populates="outgoing", foreign_keys=[from_node_id]
    )
    to_node: Mapped[GraphNode] = relationship(back_populates="incoming", foreign_keys=[to_node_id])
    citation: Mapped[Citation] = relationship()
