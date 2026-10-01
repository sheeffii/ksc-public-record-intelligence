"""Version-scoped SourceAnchor projection: an object re-anchored in a scoped run
keeps exactly one anchor on its current evidence version, and anchors of
objects outside the scope are left exactly as they were."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ksc_api.models import (
    ArtifactStatus,
    Case,
    Document,
    DocumentPage,
    DocumentVersion,
    DocumentVersionType,
    EntityKind,
    EntityOccurrence,
    GraphNode,
    Person,
    Relationship,
    RelationshipType,
    SourceAnchor,
    SourceSpan,
)
from ksc_ingestion.source_geometry import SourceGeometryProjector
from ksc_ingestion.storage import InMemoryObjectStore
from support.synthetic import make_pdf

pytestmark = pytest.mark.integration

_TEXT = "Witness statement names Arben Krasniqi"
_NAME = "Arben Krasniqi"


class _Corpus:
    """Three versions: A and B of one document, U of an unrelated one. Each has
    one verified mention of the same person; `rel` is a mentioned_in edge whose
    evidence starts on A, `rel_u` an unrelated edge on U."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.ns = uuid.uuid4()
        self.case_number = f"KSC-TEST-ANC-{self.ns.hex[:8]}"
        self.sessions = sessions
        pdf = make_pdf([_TEXT])
        self.store = InMemoryObjectStore({f"anc/{name}.pdf": pdf for name in "ABU"})
        start = _TEXT.index(_NAME)
        with sessions() as session:
            session.add(
                Case(id=self.id("case"), case_number=self.case_number, title="t", court="t")
            )
            session.flush()
            session.add(
                Person(id=self.id("person"), case_id=self.id("case"), slug="p", display_name=_NAME)
            )
            session.add(
                GraphNode(
                    id=self.id("node-person"),
                    case_id=self.id("case"),
                    entity_kind=EntityKind.PERSON,
                    label=_NAME,
                    person_id=self.id("person"),
                )
            )
            for doc in ("doc", "other"):
                session.add(
                    Document(
                        id=self.id(doc),
                        case_id=self.id("case"),
                        official_ref=f"{self.case_number}/{doc}",
                        title=doc,
                        document_type="filing",
                        language="en",
                    )
                )
                session.add(
                    GraphNode(
                        id=self.id(f"node-{doc}"),
                        case_id=self.id("case"),
                        entity_kind=EntityKind.DOCUMENT,
                        label=doc,
                        document_id=self.id(doc),
                    )
                )
            session.flush()
            for name, doc in (("A", "doc"), ("B", "doc"), ("U", "other")):
                session.add(
                    DocumentVersion(
                        id=self.id(name),
                        document_id=self.id(doc),
                        official_version_ref=f"{self.case_number}/{doc}/{name}",
                        version_type=DocumentVersionType.ORIGINAL,
                        artifact_status=ArtifactStatus.FETCHED,
                        storage_key=f"anc/{name}.pdf",
                        sha256=hashlib.sha256(f"{self.ns}{name}".encode()).hexdigest(),
                        parsed_at=datetime.now(UTC),
                    )
                )
                session.flush()
                session.add(
                    DocumentPage(
                        id=self.id(f"page-{name}"),
                        document_version_id=self.id(name),
                        pdf_page_index=0,
                        page_number=1,
                        text=_TEXT,
                    )
                )
                session.add(
                    EntityOccurrence(
                        id=self.id(f"occ-{name}"),
                        case_id=self.id("case"),
                        document_version_id=self.id(name),
                        person_id=self.id("person"),
                        rule_id="test-rule",
                        rule_version=1,
                        char_anchor="document_page_text",
                        char_start=start,
                        char_end=start + len(_NAME),
                        occurrence_text=_NAME,
                        pdf_page_index=0,
                        page_number=1,
                    )
                )
            # An occurrence with no anchoring rule never gets a span.
            session.add(
                EntityOccurrence(
                    id=self.id("occ-B-unanchored"),
                    case_id=self.id("case"),
                    document_version_id=self.id("B"),
                    person_id=self.id("person"),
                    char_start=start,
                    char_end=start + len(_NAME),
                    occurrence_text=_NAME,
                )
            )
            session.flush()
            for rel, occurrence, doc in (("rel", "occ-A", "doc"), ("rel-u", "occ-U", "other")):
                session.add(
                    Relationship(
                        id=self.id(rel),
                        case_id=self.id("case"),
                        from_node_id=self.id("node-person"),
                        to_node_id=self.id(f"node-{doc}"),
                        relationship_type=RelationshipType.MENTIONED_IN,
                        entity_occurrence_id=self.id(occurrence),
                    )
                )
            session.commit()

    def id(self, name: str) -> uuid.UUID:
        return uuid.uuid5(self.ns, name)

    def project(self, *versions: str) -> None:
        SourceGeometryProjector(self.sessions, self.store, case_number=self.case_number).run(
            version_ids=frozenset(self.id(v) for v in versions)
        )

    def move_rel_to(self, occurrence: str) -> None:
        with self.sessions() as session:
            rel = session.get(Relationship, self.id("rel"))
            assert rel is not None
            rel.entity_occurrence_id = self.id(occurrence)
            session.commit()

    def rel_anchor_versions(self, rel: str = "rel") -> list[uuid.UUID]:
        with self.sessions() as session:
            return list(
                session.scalars(
                    select(SourceSpan.document_version_id)
                    .join(SourceAnchor, SourceAnchor.source_span_id == SourceSpan.id)
                    .where(
                        SourceAnchor.object_type == "relationship",
                        SourceAnchor.object_id == self.id(rel),
                    )
                ).all()
            )

    def snapshot(self, version: str) -> list[tuple[Any, ...]]:
        """Every anchor/span column, timestamps included, for one version."""
        with self.sessions() as session:
            rows = session.execute(
                select(SourceAnchor, SourceSpan)
                .join(SourceSpan, SourceSpan.id == SourceAnchor.source_span_id)
                .where(SourceSpan.document_version_id == self.id(version))
                .order_by(SourceAnchor.id)
            ).all()
            return [
                (
                    tuple(getattr(a, c.key) for c in SourceAnchor.__table__.columns),
                    tuple(getattr(s, c.key) for c in SourceSpan.__table__.columns),
                )
                for a, s in rows
            ]


@pytest.fixture
def corpus(integration_settings) -> _Corpus:
    from ksc_api.db.session import get_sessionmaker

    return _Corpus(get_sessionmaker())


def test_moved_relationship_is_reanchored_only_on_its_new_version(corpus: _Corpus) -> None:
    corpus.project("A", "B", "U")
    assert corpus.rel_anchor_versions() == [corpus.id("A")]
    before_a, before_u = corpus.snapshot("A"), corpus.snapshot("U")

    corpus.move_rel_to("occ-B")
    corpus.project("B")  # used to raise UniqueViolation on pk_source_anchors

    assert corpus.rel_anchor_versions() == [corpus.id("B")]
    after_a = corpus.snapshot("A")
    rel_anchor = corpus.id("rel")
    # A keeps its own mention anchor untouched; only the moved edge left it.
    object_id = [c.key for c in SourceAnchor.__table__.columns].index("object_id")
    assert after_a == [row for row in before_a if row[0][object_id] != rel_anchor]
    assert len(after_a) == len(before_a) - 1
    assert corpus.snapshot("U") == before_u
    assert corpus.rel_anchor_versions("rel-u") == [corpus.id("U")]


def test_scoped_reanchoring_is_idempotent(corpus: _Corpus) -> None:
    corpus.project("A", "B", "U")
    corpus.move_rel_to("occ-B")
    corpus.project("B")
    first = corpus.snapshot("B")
    corpus.project("B")
    second = corpus.snapshot("B")

    volatile = {"created_at", "updated_at", "processing_run_id"}
    anchor_keep = [i for i, c in enumerate(SourceAnchor.__table__.columns) if c.key not in volatile]
    span_keep = [i for i, c in enumerate(SourceSpan.__table__.columns) if c.key not in volatile]

    def ids(rows: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
        return [(tuple(a[i] for i in anchor_keep), tuple(s[i] for i in span_keep)) for a, s in rows]

    assert ids(first) == ids(second) and len(second) == 2
    assert corpus.rel_anchor_versions() == [corpus.id("B")]


def test_relationship_moved_out_of_scope_follows_its_evidence(corpus: _Corpus) -> None:
    """Scoped to the OLD version: the edge anchored there is affected and is
    re-anchored on the persisted span of its current evidence."""
    corpus.project("A", "B", "U")
    corpus.move_rel_to("occ-B")
    corpus.project("A")
    assert corpus.rel_anchor_versions() == [corpus.id("B")]


def test_relationship_without_valid_current_provenance_gets_no_anchor(corpus: _Corpus) -> None:
    corpus.project("A", "B", "U")
    corpus.move_rel_to("occ-B-unanchored")
    corpus.project("B")
    # Fails closed: no anchor on B (no span for that evidence) and none left on A.
    assert corpus.rel_anchor_versions() == []
    assert corpus.rel_anchor_versions("rel-u") == [corpus.id("U")]
