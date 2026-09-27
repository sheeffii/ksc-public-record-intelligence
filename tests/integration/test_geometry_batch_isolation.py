"""One unreadable PDF never aborts a source-geometry batch: its geometry is not
written, the failure is recorded, and the remaining versions are projected."""

from __future__ import annotations

import hashlib
import io
import uuid
from datetime import UTC, datetime

import pytest
from pypdf import PdfWriter
from sqlalchemy import select

from ksc_api.models import (
    ArtifactStatus,
    AuditLog,
    Case,
    Document,
    DocumentPage,
    DocumentVersion,
    DocumentVersionType,
    ProcessingRun,
)
from ksc_ingestion.source_geometry import PROCESSOR, SourceGeometryProjector
from ksc_ingestion.storage import InMemoryObjectStore

pytestmark = pytest.mark.integration

CASE_NUMBER = "KSC-TEST-GEO"
_NS = uuid.UUID("5a0e2c61-7b1f-4e0c-9d3a-2f6b8c4e1a90")


def _id(name: str) -> uuid.UUID:
    return uuid.uuid5(_NS, name)


def _pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_bad_pdf_is_recorded_and_the_batch_continues(integration_settings) -> None:
    from ksc_api.db.session import get_sessionmaker

    good, bad = _pdf(), b"%PDF-1.4 truncated and unreadable"
    store = InMemoryObjectStore({"geo/good.pdf": good, "geo/bad.pdf": bad})
    sessions = get_sessionmaker()
    with sessions() as session:
        session.merge(Case(id=_id("case"), case_number=CASE_NUMBER, title="Geo", court="Test"))
        for name, key, data in (("bad", "geo/bad.pdf", bad), ("good", "geo/good.pdf", good)):
            # "bad" sorts first, so a failure that aborted the batch would
            # leave "good" unprojected.
            session.merge(
                Document(
                    id=_id(f"doc-{name}"),
                    case_id=_id("case"),
                    official_ref=f"{CASE_NUMBER}/F-{name}",
                    title=name,
                    document_type="filing",
                    language="en",
                )
            )
            session.merge(
                DocumentVersion(
                    id=_id(f"ver-{name}"),
                    document_id=_id(f"doc-{name}"),
                    official_version_ref=f"{CASE_NUMBER}/F-{name}",
                    version_type=DocumentVersionType.ORIGINAL,
                    artifact_status=ArtifactStatus.FETCHED,
                    storage_key=key,
                    sha256=hashlib.sha256(data).hexdigest(),
                    parsed_at=datetime.now(UTC),
                )
            )
            session.merge(
                DocumentPage(
                    id=_id(f"page-{name}"),
                    document_version_id=_id(f"ver-{name}"),
                    pdf_page_index=0,
                    page_number=1,
                    text="",
                )
            )
        session.commit()

    result = SourceGeometryProjector(sessions, store, case_number=CASE_NUMBER).run()

    with sessions() as session:
        run = session.get(ProcessingRun, result.run_id)
        assert run is not None and run.processor == PROCESSOR
        assert run.status == "completed"
        assert run.failed_count == 1
        assert [f["official_version_ref"] for f in run.detail["failed_versions"]] == [
            f"{CASE_NUMBER}/F-bad"
        ]
        good_page = session.get(DocumentPage, _id("page-good"))
        bad_page = session.get(DocumentPage, _id("page-bad"))
        assert good_page is not None and good_page.geometry_processing_run_id == result.run_id
        assert bad_page is not None and bad_page.geometry_processing_run_id is None
        audit = session.scalar(
            select(AuditLog).where(
                AuditLog.action == "document_version.geometry_failed",
                AuditLog.entity_id == str(_id("ver-bad")),
            )
        )
        assert audit is not None
