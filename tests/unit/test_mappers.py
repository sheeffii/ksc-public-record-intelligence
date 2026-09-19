"""Serialisation rules that must hold before any row reaches a client."""

from __future__ import annotations

import uuid

from ksc_api.models import (
    Citation,
    CitationType,
    Document,
    ExaminationType,
    Party,
    ResolutionState,
    TranscriptSegment,
    VerificationState,
    Witness,
    WitnessIdentityStatus,
)
from ksc_api.repositories import mappers
from ksc_api.schemas.records import WitnessRead

COUNTS = mappers.ZERO_COUNTS


def _witness(**kwargs: object) -> Witness:
    base: dict[str, object] = {
        "case_id": uuid.uuid4(),
        "code": "W-DEMO-001",
        "identity_status": WitnessIdentityStatus.PROTECTED_CODE,
        "protective_measures": ["pseudonym"],
    }
    base.update(kwargs)
    return Witness(**base)


def test_protected_witness_serialises_as_code_only():
    read = mappers.to_witness(_witness(), COUNTS)
    payload = read.model_dump(mode="json")
    assert payload["code"] == "W-DEMO-001"
    assert payload["protected"] is True
    assert "public" not in payload


def test_unknown_identity_status_fails_closed_to_protected():
    read = mappers.to_witness(_witness(identity_status=WitnessIdentityStatus.UNKNOWN), COUNTS)
    assert read.protected is True
    assert "public" not in read.model_dump(mode="json")


def test_public_status_without_a_stored_name_still_fails_closed():
    read = mappers.to_witness(
        _witness(identity_status=WitnessIdentityStatus.PUBLIC, public_name=None), COUNTS
    )
    assert read.protected is True


def test_public_witness_carries_public_block():
    read = mappers.to_witness(
        _witness(
            identity_status=WitnessIdentityStatus.PUBLIC,
            public_name="Demo Public Witness",
            called_by=Party.DEFENCE,
        ),
        COUNTS,
    )
    payload = read.model_dump(mode="json")
    assert payload["protected"] is False
    assert payload["public"] == {"display_name": "Demo Public Witness", "called_by": "defence"}


def test_witness_read_json_schema_never_requires_public():
    assert "public" not in WitnessRead.model_json_schema().get("required", [])


def _citation(**kwargs: object) -> Citation:
    base: dict[str, object] = {
        "id": uuid.uuid4(),
        "case_id": uuid.uuid4(),
        "raw_text": "raw",
        "citation_type": CitationType.UNKNOWN,
        "resolution_state": ResolutionState.UNRESOLVED,
        "display": "UNRESOLVED",
        "verification_state": VerificationState.UNRESOLVED,
    }
    base.update(kwargs)
    return Citation(**base)


def test_unresolved_citation_maps_to_resolved_false_and_literal_display():
    read = mappers.to_citation(_citation())
    assert read.resolved is False
    assert read.display == "UNRESOLVED"
    assert read.ref == "raw"
    assert read.doc_id is None


def test_source_type_follows_the_resolved_target_not_the_client():
    spo_doc = Document(
        case_id=uuid.uuid4(),
        official_ref="X/F-DEMO-002",
        filing_number="F-DEMO-002",
        title="t",
        document_type="filing",
        filing_party=Party.SPO,
    )
    resolved = _citation(
        resolution_state=ResolutionState.RESOLVED,
        display="F-DEMO-002 · ¶5",
        target_document_id=uuid.uuid4(),
    )
    resolved.target_document = spo_doc
    read = mappers.to_citation(resolved)
    assert read.source_type == "spo"
    assert read.ref == "F-DEMO-002"
    assert read.doc_id == "X/F-DEMO-002"
    assert read.resolved is True

    assert mappers.citation_source_type(_citation(target_exhibit_id=uuid.uuid4())) == "exhibit"
    assert mappers.citation_source_type(_citation(target_witness_id=uuid.uuid4())) == "witness"
    assert mappers.citation_source_type(_citation(target_finding_id=uuid.uuid4())) == "court"
    assert (
        mappers.citation_source_type(_citation(citation_type=CitationType.TRANSCRIPT)) == "witness"
    )


def test_closed_session_segment_exposes_no_text():
    segment = TranscriptSegment(
        transcript_id=uuid.uuid4(),
        sequence=3,
        page_number=103,
        examination_type=ExaminationType.UNKNOWN,
        text="",
        closed_session=True,
    )
    read = mappers.to_segment(segment)
    assert read.closed_session is True
    assert read.text is None
