"""Reviewed incident reads expose only validated public source navigation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.models import (
    Case,
    DocumentParagraph,
    DocumentVersion,
    Incident,
    IncidentSource,
    SourceAnchor,
    SourcePrecision,
    SourceSpan,
    TextExtractionMethod,
    VerificationState,
    Visibility,
)
from ksc_api.repositories.records import RecordRepository

pytestmark = pytest.mark.integration


def test_incident_sources_link_to_their_own_public_version(demo_settings, engine) -> None:
    connection = engine.connect()
    transaction = connection.begin()
    try:
        with Session(bind=connection, expire_on_commit=False) as session:
            case = session.scalar(select(Case).where(Case.case_number == "KSC-DEMO-0000"))
            incident = session.scalar(select(Incident).where(Incident.slug == "demo-incident-001"))
            version = session.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.official_version_ref == "F-DEMO-001/RED"
                )
            )
            assert case is not None and incident is not None and version is not None
            paragraph = session.scalar(
                select(DocumentParagraph).where(
                    DocumentParagraph.document_version_id == version.id,
                    DocumentParagraph.paragraph_number == 12,
                )
            )
            assert paragraph is not None
            incident.source_category = "spo_allegation"
            incident.verification_state = VerificationState.HUMAN_VERIFIED
            incident.verified_by = "test reviewer"
            incident.verified_at = datetime.now(UTC)
            incident.review_decision = {"withdrawal_review": {"status": "UNAFFECTED"}}
            source_id, span_id, anchor_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
            source = IncidentSource(
                id=source_id,
                incident_id=incident.id,
                sequence=1,
                role="operative",
                source_ref=version.official_version_ref,
                document_version_id=version.id,
                paragraph_number=12,
                excerpt=paragraph.text,
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by="test reviewer",
                verified_at=datetime.now(UTC),
            )
            span = SourceSpan(
                id=span_id,
                document_version_id=version.id,
                pdf_page_index=paragraph.pdf_page_index_from,
                page_number=paragraph.page_from,
                paragraph_number=12,
                exact_text=paragraph.text,
                extraction_method=TextExtractionMethod.NATIVE_TEXT,
                extractor_version="test",
                precision=SourcePrecision.PAGE_ONLY,
                state="verified",
            )
            anchor = SourceAnchor(
                id=anchor_id,
                source_span_id=span_id,
                object_type="incident_source",
                object_id=source_id,
                anchor_role="incident_source",
                source_verification_state="human_verified",
            )
            session.add_all([source, span, anchor])
            session.flush()
            source.source_anchor_id = anchor_id
            session.flush()

            repo = RecordRepository(session, case)
            detail = repo.get_incident(incident.slug)
            assert detail is not None
            assert detail.source_category == "spo_allegation"
            assert detail.verification_state == VerificationState.HUMAN_VERIFIED
            assert len(detail.sources) == 1
            assert detail.sources[0].excerpt == paragraph.text
            assert detail.sources[0].target_path is not None
            assert f"anchor={anchor_id}" in detail.sources[0].target_path
            assert "version=F-DEMO-001%2FRED" in detail.sources[0].target_path

            anchor.source_verification_state = "human_rejected"
            session.flush()
            session.expire_all()
            rejected_anchor = repo.get_incident(incident.slug)
            assert rejected_anchor is not None
            assert rejected_anchor.sources[0].excerpt is None
            assert rejected_anchor.sources[0].target_path is None
            anchor.source_verification_state = "human_verified"
            session.flush()

            span.exact_text = "different text"
            session.flush()
            session.expire_all()
            withheld = repo.get_incident(incident.slug)
            assert withheld is not None
            assert withheld.sources[0].excerpt is None
            assert withheld.sources[0].target_path is None

            source.verification_state = VerificationState.HUMAN_REJECTED
            session.flush()
            assert repo.get_incident(incident.slug) is None
            source.verification_state = VerificationState.HUMAN_VERIFIED
            session.flush()

            version.visibility = Visibility.UNKNOWN
            session.flush()
            assert repo.get_incident(incident.slug) is None
            assert all(
                row.slug != incident.slug for row in repo.list_incidents(limit=100, offset=0).items
            )
    finally:
        transaction.rollback()
        connection.close()
