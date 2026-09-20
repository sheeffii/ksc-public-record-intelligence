"""Synthetic evidence fixture for KSC-DEMO-0000.

Every identifier is visibly synthetic (`F-DEMO-001`, `W-DEMO-001`,
`P-DEMO-001`, …), every URL points at `example.invalid`, every text is
generic. No real person, witness, exhibit, filing or allegation appears. The
fixture exists to prove the Phase 6 schema end to end:

    Document → Version → Page → Citation
    Witness → Transcript → Segment → Citation
    Claim → Mention → Citation → Source
    Finding → Evidence Link → Citation → Source
    Relationship → Citation → Source

Loading is idempotent: ids are UUID5 of stable keys and the loader returns
early when the demo case already exists.
"""

# ruff: noqa: RUF001  (canonical citation strings use an EN DASH between paragraph numbers)

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ksc_api.config import get_settings
from ksc_api.db.session import session_scope
from ksc_api.logging_config import configure_logging
from ksc_api.models import (
    Argument,
    ArgumentResponse,
    ArgumentResponseKind,
    ArtifactStatus,
    AuditLog,
    Case,
    Citation,
    CitationType,
    Claim,
    ClaimMention,
    ClaimOrigin,
    ClaimStance,
    DatePrecision,
    DateType,
    Document,
    DocumentChunk,
    DocumentIngestionState,
    DocumentPage,
    DocumentSection,
    DocumentVersion,
    DocumentVersionType,
    EntityKind,
    Event,
    ExaminationType,
    Exhibit,
    Finding,
    FindingEvidenceLink,
    FindingLinkType,
    GraphNode,
    Hearing,
    IdentifierKind,
    Incident,
    Location,
    Organization,
    Party,
    Person,
    PersonAlias,
    RecordIdentifier,
    Relationship,
    RelationshipType,
    ResearchNote,
    ResolutionMethod,
    ResolutionState,
    SourceRecord,
    SourceSystem,
    TextExtractionMethod,
    Transcript,
    TranscriptSegment,
    VerificationState,
    Visibility,
    Witness,
    WitnessAppearance,
    WitnessIdentityStatus,
    normalize_identifier,
)

log = logging.getLogger(__name__)

DEMO_CASE_NUMBER = "KSC-DEMO-0000"
_NAMESPACE = uuid.UUID("6f1b6d0c-5c1e-4b7e-9a8e-000000000d3a")
_REVIEWED_AT = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
_DEMO_URL = "https://example.invalid/demo/"


def demo_id(key: str) -> uuid.UUID:
    """Deterministic id for a fixture object, so reloads never duplicate."""
    return uuid.uuid5(_NAMESPACE, key)


def _sha(label: str) -> str:
    return hashlib.sha256(f"synthetic:{label}".encode()).hexdigest()


def _resolved(
    *,
    key: str,
    case: Case,
    raw: str,
    citation_type: CitationType,
    display: str,
    **targets: object,
) -> Citation:
    return Citation(
        id=demo_id(f"citation:{key}"),
        case_id=case.id,
        raw_text=raw,
        normalized_text=normalize_identifier(raw),
        citation_type=citation_type,
        resolution_state=ResolutionState.RESOLVED,
        resolution_method=ResolutionMethod.EXACT_ID,
        resolution_confidence=Decimal("1.00"),
        resolved_at=_REVIEWED_AT,
        display=display,
        verification_state=VerificationState.HUMAN_VERIFIED,
        verified_by="demo-reviewer",
        verified_at=_REVIEWED_AT,
        **targets,
    )


def load_demo_fixture(session: Session) -> tuple[Case, bool]:
    """Create the synthetic case and its evidence graph. Returns (case, created)."""
    existing = session.scalar(select(Case).where(Case.case_number == DEMO_CASE_NUMBER))
    if existing is not None:
        return existing, False

    case = Case(
        id=demo_id("case"),
        case_number=DEMO_CASE_NUMBER,
        title="Synthetic demonstration case — no real court material",
        court="Demo Chambers (synthetic)",
        seat="Nowhere",
        official_source_url=_DEMO_URL,
        description="Generic demo data used to exercise the Phase 6 evidence model.",
    )
    session.add(case)
    session.flush()

    # --- documents and versions -------------------------------------------
    def document(
        key: str,
        title: str,
        doc_type: str,
        party: Party | None,
        visibility: Visibility,
        **dates: date,
    ) -> Document:
        doc = Document(
            id=demo_id(f"document:{key}"),
            case_id=case.id,
            official_ref=f"{DEMO_CASE_NUMBER}/{key}",
            filing_number=key,
            title=title,
            document_type=doc_type,
            language="en",
            filing_party=party,
            visibility=visibility,
            ingestion_state=DocumentIngestionState.PARSED
            if visibility in (Visibility.PUBLIC, Visibility.PUBLIC_REDACTED)
            else DocumentIngestionState.DISCOVERED,
            source_url=f"{_DEMO_URL}{key}",
            **dates,
        )
        session.add(doc)
        return doc

    judgment = document(
        "F-DEMO-001",
        "Demo judgment (synthetic)",
        "judgment",
        Party.COURT,
        Visibility.PUBLIC_REDACTED,
        document_date=date(2024, 1, 15),
        filing_date=date(2024, 1, 15),
        public_date=date(2024, 1, 16),
    )
    spo_filing = document(
        "F-DEMO-002",
        "Demo prosecution submission (synthetic)",
        "filing",
        Party.SPO,
        Visibility.PUBLIC,
        document_date=date(2023, 3, 1),
        filing_date=date(2023, 3, 1),
    )
    defence_filing = document(
        "F-DEMO-003",
        "Demo defence response (synthetic)",
        "filing",
        Party.DEFENCE,
        Visibility.PUBLIC,
        document_date=date(2023, 3, 20),
        filing_date=date(2023, 3, 21),
    )
    # Exists in the public docket but is not public: no version, no text.
    document(
        "F-DEMO-004",
        "Demo confidential filing (synthetic; not public)",
        "filing",
        Party.SPO,
        Visibility.NOT_PUBLIC,
        filing_date=date(2023, 4, 2),
    )
    transcript_doc = document(
        "T-DEMO-001",
        "Demo hearing transcript (synthetic)",
        "transcript",
        Party.COURT,
        Visibility.PUBLIC,
        document_date=date(2023, 6, 1),
    )
    session.flush()

    def version(
        doc: Document, ref: str, vtype: DocumentVersionType, visibility: Visibility, pages: int
    ) -> DocumentVersion:
        ver = DocumentVersion(
            id=demo_id(f"version:{ref}"),
            document_id=doc.id,
            official_version_ref=ref,
            version_type=vtype,
            visibility=visibility,
            source_url=f"{_DEMO_URL}{ref}.pdf",
            artifact_status=ArtifactStatus.FETCHED,
            storage_key=f"demo/{ref}.pdf",
            sha256=_sha(ref),
            mime_type="application/pdf",
            page_count=pages,
            text_extraction_method=TextExtractionMethod.NATIVE_TEXT,
        )
        session.add(ver)
        return ver

    judgment_original = version(
        judgment, "F-DEMO-001", DocumentVersionType.ORIGINAL, Visibility.NOT_PUBLIC, 3
    )
    judgment_red = version(
        judgment,
        "F-DEMO-001/RED",
        DocumentVersionType.PUBLIC_REDACTED,
        Visibility.PUBLIC_REDACTED,
        3,
    )
    judgment_red.supersedes_version_id = judgment_original.id
    spo_version = version(
        spo_filing, "F-DEMO-002", DocumentVersionType.ORIGINAL, Visibility.PUBLIC, 6
    )
    defence_version = version(
        defence_filing, "F-DEMO-003", DocumentVersionType.ORIGINAL, Visibility.PUBLIC, 9
    )
    transcript_version = version(
        transcript_doc, "T-DEMO-001", DocumentVersionType.ORIGINAL, Visibility.PUBLIC, 40
    )
    session.flush()

    page_texts = {
        1: "Demo judgment, page 1. Introductory text (synthetic).",
        2: "Demo judgment, page 2. Paragraphs 10–20 (synthetic). [REDACTED]",
        3: "Demo judgment, page 3. Paragraphs 21–40 (synthetic).",
    }
    for number, text in page_texts.items():
        session.add(
            DocumentPage(
                id=demo_id(f"page:F-DEMO-001/RED:{number}"),
                document_version_id=judgment_red.id,
                page_number=number,
                text=text,
                running_head="KSC-DEMO-0000/F-DEMO-001/RED",
                has_redactions=number == 2,
                redaction_extents=[{"kind": "name", "extent": "2 lines"}] if number == 2 else None,
            )
        )
    intro = DocumentSection(
        id=demo_id("section:F-DEMO-001/RED:1"),
        document_version_id=judgment_red.id,
        sequence=1,
        level=0,
        heading="I. Introduction",
        page_from=1,
        page_to=1,
        para_from=1,
        para_to=9,
    )
    findings_section = DocumentSection(
        id=demo_id("section:F-DEMO-001/RED:2"),
        document_version_id=judgment_red.id,
        sequence=2,
        level=0,
        heading="II. Findings",
        page_from=2,
        page_to=3,
        para_from=10,
        para_to=40,
    )
    session.add_all([intro, findings_section])
    session.flush()
    for seq, (section, para_from, para_to, text) in enumerate(
        [
            (intro, 1, 9, "Demo chunk: introduction (synthetic)."),
            (findings_section, 10, 20, "Demo chunk: findings 10–20 (synthetic)."),
            (findings_section, 21, 40, "Demo chunk: findings 21–40 (synthetic)."),
        ]
    ):
        session.add(
            DocumentChunk(
                id=demo_id(f"chunk:F-DEMO-001/RED:{seq}"),
                document_version_id=judgment_red.id,
                section_id=section.id,
                sequence=seq,
                page_from=section.page_from,
                page_to=section.page_to,
                para_from=para_from,
                para_to=para_to,
                text=text,
                char_count=len(text),
            )
        )

    # --- actors --------------------------------------------------------------
    person_a = Person(
        id=demo_id("person:demo-person-a"),
        case_id=case.id,
        slug="demo-person-a",
        display_name="Demo Person A",
        public_role="accused (synthetic)",
        description="A synthetic person used only to exercise the data model.",
    )
    public_witness_person = Person(
        id=demo_id("person:demo-public-witness"),
        case_id=case.id,
        slug="demo-public-witness",
        display_name="Demo Public Witness",
        public_role="witness (synthetic)",
    )
    session.add_all([person_a, public_witness_person])
    session.flush()
    session.add(PersonAlias(id=demo_id("alias:a1"), person_id=person_a.id, alias="D. Person A"))

    protected_witness = Witness(
        id=demo_id("witness:W-DEMO-001"),
        case_id=case.id,
        code="W-DEMO-001",
        identity_status=WitnessIdentityStatus.PROTECTED_CODE,
        called_by=Party.SPO,
        protective_measures=["pseudonym", "face and voice distortion"],
    )
    public_witness = Witness(
        id=demo_id("witness:W-DEMO-002"),
        case_id=case.id,
        code="W-DEMO-002",
        identity_status=WitnessIdentityStatus.PUBLIC,
        person_id=public_witness_person.id,
        public_name="Demo Public Witness",
        called_by=Party.DEFENCE,
        protective_measures=[],
    )
    organization = Organization(
        id=demo_id("organization:demo-unit"),
        case_id=case.id,
        slug="demo-unit",
        name="Demo Unit",
        kind="unit (synthetic)",
        name_variants=["Demo Unit", "Njësia Demo"],
    )
    location = Location(
        id=demo_id("location:demo-village"),
        case_id=case.id,
        slug="demo-village",
        name="Demo Village",
        name_variants=["Demo Village", "Fshati Demo"],
        kind="village (synthetic)",
    )
    session.add_all([protected_witness, public_witness, organization, location])
    session.flush()

    # --- hearing / transcript / segments -----------------------------------
    hearing = Hearing(
        id=demo_id("hearing:DEMO-HEARING-001"),
        case_id=case.id,
        hearing_date=date(2023, 6, 1),
        session_sequence=1,
        session_label="morning",
        hearing_type="evidentiary (synthetic)",
        official_ref="DEMO-HEARING-001",
        source_url=f"{_DEMO_URL}hearings/DEMO-HEARING-001",
        visibility=Visibility.PUBLIC,
    )
    session.add(hearing)
    session.flush()
    transcript = Transcript(
        id=demo_id("transcript:T-DEMO-001"),
        hearing_id=hearing.id,
        document_version_id=transcript_version.id,
        official_ref="T-DEMO-001",
        language="en",
        visibility=Visibility.PUBLIC,
        page_from=100,
        page_to=140,
        text_extraction_method=TextExtractionMethod.NATIVE_TEXT,
    )
    session.add(transcript)
    session.flush()
    segments = [
        TranscriptSegment(
            id=demo_id("segment:0"),
            transcript_id=transcript.id,
            sequence=0,
            page_number=101,
            line_from=1,
            line_to=5,
            speaker="Presiding Judge",
            speaker_role="judge",
            examination_type=ExaminationType.UNKNOWN,
            text="Demo: the witness is reminded of the solemn declaration (synthetic).",
        ),
        TranscriptSegment(
            id=demo_id("segment:1"),
            transcript_id=transcript.id,
            sequence=1,
            page_number=101,
            line_from=6,
            line_to=12,
            speaker="W-DEMO-001",
            speaker_role="witness",
            witness_id=protected_witness.id,
            examination_type=ExaminationType.DIRECT,
            text="Demo testimony: I was in Demo Village on the stated date (synthetic).",
        ),
        TranscriptSegment(
            id=demo_id("segment:2"),
            transcript_id=transcript.id,
            sequence=2,
            page_number=102,
            line_from=1,
            line_to=8,
            speaker="W-DEMO-001",
            speaker_role="witness",
            witness_id=protected_witness.id,
            examination_type=ExaminationType.CROSS,
            text="Demo testimony under cross-examination (synthetic).",
        ),
        TranscriptSegment(
            id=demo_id("segment:3"),
            transcript_id=transcript.id,
            sequence=3,
            page_number=103,
            speaker_role="closed session",
            examination_type=ExaminationType.UNKNOWN,
            text="",
            closed_session=True,
        ),
    ]
    session.add_all(segments)
    session.add_all(
        [
            WitnessAppearance(
                id=demo_id("appearance:W-DEMO-001"),
                witness_id=protected_witness.id,
                hearing_id=hearing.id,
                transcript_id=transcript.id,
                testimony_date=date(2023, 6, 1),
                page_from=101,
                page_to=103,
            ),
            WitnessAppearance(
                id=demo_id("appearance:W-DEMO-002"),
                witness_id=public_witness.id,
                hearing_id=hearing.id,
                transcript_id=transcript.id,
                testimony_date=date(2023, 6, 1),
                page_from=120,
                page_to=130,
            ),
        ]
    )
    session.flush()

    # --- exhibit / incident ---------------------------------------------------
    exhibit = Exhibit(
        id=demo_id("exhibit:P-DEMO-001"),
        case_id=case.id,
        official_exhibit_id="P-DEMO-001",
        title="Demo exhibit (synthetic document)",
        description="A synthetic exhibit tendered through a public demo witness.",
        tendered_by=Party.SPO,
        through_witness_id=public_witness.id,
        admitted_date=date(2023, 6, 1),
        document_date=date(2022, 11, 5),
        document_version_id=spo_version.id,
        visibility=Visibility.PUBLIC,
    )
    incident = Incident(
        id=demo_id("incident:demo-incident-001"),
        case_id=case.id,
        slug="demo-incident-001",
        title="Demo incident (synthetic)",
        summary="A synthetic incident described in the demo material. As charged — not a determination.",
        location_id=location.id,
        date_from=date(1999, 5, 1),
        date_to=date(1999, 5, 3),
        date_precision=DatePrecision.RANGE,
        charges_pleaded=[{"count": 1, "label": "Demo count (as charged — not a determination)"}],
    )
    session.add_all([exhibit, incident])
    session.flush()

    # --- findings (created before citations that target them) ---------------
    finding = Finding(
        id=demo_id("finding:FD-DEMO-001"),
        case_id=case.id,
        finding_key="FD-DEMO-001",
        judgment_document_id=judgment.id,
        text="The Panel finds that the synthetic demo event occurred as described (demo text).",
        para_from=12,
        para_to=14,
        person_id=person_a.id,
        incident_id=incident.id,
        charge_ref="Count 1 (demo)",
        legal_element="demo element",
        mode_of_liability="demo mode",
        verification_state=VerificationState.HUMAN_VERIFIED,
        verified_by="demo-reviewer",
        verified_at=_REVIEWED_AT,
    )
    session.add(finding)
    session.flush()

    # --- citations ------------------------------------------------------------
    c_judgment_para = _resolved(
        key="judgment-para-12",
        case=case,
        raw="F-DEMO-001, para. 12",
        citation_type=CitationType.PARAGRAPH,
        display="F-DEMO-001 · ¶12",
        source_document_version_id=spo_version.id,
        source_page=4,
        source_para=7,
        target_document_id=judgment.id,
        target_document_version_id=judgment_red.id,
        target_page=2,
        target_para_from=12,
        target_para_to=12,
    )
    c_transcript = _resolved(
        key="transcript-101-6-12",
        case=case,
        raw="T. 101, lines 6–12",
        citation_type=CitationType.TRANSCRIPT_LINE,
        display="T. 101 · lines 6–12",
        source_document_version_id=judgment_red.id,
        source_page=2,
        source_para=13,
        target_transcript_id=transcript.id,
        target_transcript_segment_id=segments[1].id,
        target_page=101,
        target_line_from=6,
        target_line_to=12,
    )
    c_exhibit = _resolved(
        key="exhibit-P-DEMO-001",
        case=case,
        raw="P-DEMO-001",
        citation_type=CitationType.EXHIBIT,
        display="P-DEMO-001",
        source_document_version_id=judgment_red.id,
        source_page=2,
        source_para=13,
        target_exhibit_id=exhibit.id,
    )
    c_judgment_page = _resolved(
        key="judgment-red-page-2",
        case=case,
        raw="F-DEMO-001/RED, p. 2",
        citation_type=CitationType.PAGE,
        display="F-DEMO-001/RED · p. 2",
        target_document_id=judgment.id,
        target_document_version_id=judgment_red.id,
        target_page=2,
    )
    c_witness = _resolved(
        key="witness-W-DEMO-001",
        case=case,
        raw="W-DEMO-001",
        citation_type=CitationType.WITNESS,
        display="W-DEMO-001",
        source_document_version_id=judgment_red.id,
        source_page=2,
        source_para=13,
        target_witness_id=protected_witness.id,
    )
    c_spo = _resolved(
        key="spo-para-5",
        case=case,
        raw="F-DEMO-002, para. 5",
        citation_type=CitationType.PARAGRAPH,
        display="F-DEMO-002 · ¶5",
        target_document_id=spo_filing.id,
        target_document_version_id=spo_version.id,
        target_page=3,
        target_para_from=5,
        target_para_to=5,
    )
    c_defence = _resolved(
        key="defence-para-8",
        case=case,
        raw="F-DEMO-003, para. 8",
        citation_type=CitationType.PARAGRAPH,
        display="F-DEMO-003 · ¶8",
        target_document_id=defence_filing.id,
        target_document_version_id=defence_version.id,
        target_page=4,
        target_para_from=8,
        target_para_to=8,
    )
    c_finding = _resolved(
        key="finding-FD-DEMO-001",
        case=case,
        raw="Judgment, paras 12–14",
        citation_type=CitationType.FINDING,
        display="F-DEMO-001 · ¶12–14",
        target_document_id=judgment.id,
        target_document_version_id=judgment_red.id,
        target_finding_id=finding.id,
        target_page=2,
        target_para_from=12,
        target_para_to=14,
    )
    c_unresolved = Citation(
        id=demo_id("citation:unresolved"),
        case_id=case.id,
        raw_text="F-DEMO-999, para. 3",
        normalized_text=normalize_identifier("F-DEMO-999, para. 3"),
        citation_type=CitationType.PARAGRAPH,
        source_document_version_id=defence_version.id,
        source_page=5,
        source_para=11,
        resolution_state=ResolutionState.UNRESOLVED,
        resolution_method=ResolutionMethod.NONE,
        verification_state=VerificationState.UNRESOLVED,
    )
    c_ambiguous = Citation(
        id=demo_id("citation:ambiguous"),
        case_id=case.id,
        raw_text="DEMO-AMBIG",
        normalized_text="DEMO-AMBIG",
        citation_type=CitationType.UNKNOWN,
        source_document_version_id=defence_version.id,
        source_page=6,
        source_para=2,
        resolution_state=ResolutionState.AMBIGUOUS,
        resolution_method=ResolutionMethod.PATTERN,
        resolution_confidence=Decimal("0.50"),
        verification_state=VerificationState.NEEDS_MORE_EVIDENCE,
    )
    session.add_all(
        [
            c_judgment_para,
            c_transcript,
            c_exhibit,
            c_judgment_page,
            c_witness,
            c_spo,
            c_defence,
            c_finding,
            c_unresolved,
            c_ambiguous,
        ]
    )
    session.flush()
    finding.citation_id = c_finding.id

    # --- identifier index ------------------------------------------------------
    def identifier(
        text: str, kind: IdentifierKind, entity_kind: EntityKind, **target: uuid.UUID
    ) -> None:
        session.add(
            RecordIdentifier(
                id=demo_id(f"identifier:{text}:{entity_kind.value}"),
                case_id=case.id,
                identifier=text,
                normalized_identifier=normalize_identifier(text),
                identifier_kind=kind,
                entity_kind=entity_kind,
                **target,
            )
        )

    identifier("F-DEMO-001", IdentifierKind.FILING, EntityKind.DOCUMENT, document_id=judgment.id)
    identifier(
        "F-DEMO-001/RED",
        IdentifierKind.FILING_VERSION,
        EntityKind.DOCUMENT_VERSION,
        document_version_id=judgment_red.id,
    )
    identifier("F-DEMO-002", IdentifierKind.FILING, EntityKind.DOCUMENT, document_id=spo_filing.id)
    identifier(
        "F-DEMO-003", IdentifierKind.FILING, EntityKind.DOCUMENT, document_id=defence_filing.id
    )
    identifier("P-DEMO-001", IdentifierKind.EXHIBIT, EntityKind.EXHIBIT, exhibit_id=exhibit.id)
    identifier(
        "W-DEMO-001", IdentifierKind.WITNESS, EntityKind.WITNESS, witness_id=protected_witness.id
    )
    identifier(
        "W-DEMO-002", IdentifierKind.WITNESS, EntityKind.WITNESS, witness_id=public_witness.id
    )
    identifier(
        "T-DEMO-001", IdentifierKind.TRANSCRIPT, EntityKind.TRANSCRIPT, transcript_id=transcript.id
    )
    identifier("FD-DEMO-001", IdentifierKind.FINDING, EntityKind.FINDING, finding_id=finding.id)
    # Deliberately ambiguous: the same string names two different records.
    identifier("DEMO-AMBIG", IdentifierKind.OTHER, EntityKind.DOCUMENT, document_id=spo_filing.id)
    identifier("DEMO-AMBIG", IdentifierKind.OTHER, EntityKind.EXHIBIT, exhibit_id=exhibit.id)

    # --- claims ----------------------------------------------------------------
    claim = Claim(
        id=demo_id("claim:CL-DEMO-001"),
        case_id=case.id,
        claim_key="CL-DEMO-001",
        text="Demo claim: a synthetic event occurred at Demo Village on the stated date.",
        origin=ClaimOrigin.HUMAN,
        created_by="demo-researcher",
        source_citation_id=c_spo.id,
        verification_state=VerificationState.UNREVIEWED,
    )
    session.add(claim)
    session.flush()
    for key, citation, stance, quote in [
        ("m1", c_transcript, ClaimStance.SUPPORTS, "I was in Demo Village on the stated date"),
        ("m2", c_spo, ClaimStance.SUPPORTS, None),
        ("m3", c_defence, ClaimStance.CONTRADICTS, None),
        ("m4", c_exhibit, ClaimStance.NEUTRAL, None),
        # Depends on an unresolved citation: must be withheld by the API.
        ("m5", c_unresolved, ClaimStance.UNCLEAR, None),
    ]:
        session.add(
            ClaimMention(
                id=demo_id(f"mention:{key}"),
                claim_id=claim.id,
                citation_id=citation.id,
                stance=stance,
                quote_text=quote,
                verification_state=VerificationState.UNREVIEWED,
            )
        )

    # --- finding evidence links ------------------------------------------------
    for key, citation, link_type, court_cited, para in [
        ("l1", c_transcript, FindingLinkType.RELIES_ON, True, 13),
        ("l2", c_exhibit, FindingLinkType.SUPPORTS, True, 13),
        ("l3", c_spo, FindingLinkType.CONTEXT, False, None),
    ]:
        session.add(
            FindingEvidenceLink(
                id=demo_id(f"finding-link:{key}"),
                finding_id=finding.id,
                citation_id=citation.id,
                link_type=link_type,
                court_cited=court_cited,
                court_cited_para=para,
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by="demo-reviewer",
                verified_at=_REVIEWED_AT,
            )
        )

    # --- arguments ---------------------------------------------------------------
    spo_argument = Argument(
        id=demo_id("argument:AR-DEMO-001"),
        case_id=case.id,
        argument_key="AR-DEMO-001",
        party=Party.SPO,
        title="Demo prosecution position (synthetic)",
        text="The prosecution submits (demo) that the synthetic event occurred.",
        document_id=spo_filing.id,
        para_from=5,
        para_to=5,
        citation_id=c_spo.id,
        finding_id=finding.id,
    )
    defence_argument = Argument(
        id=demo_id("argument:AR-DEMO-002"),
        case_id=case.id,
        argument_key="AR-DEMO-002",
        party=Party.DEFENCE,
        title="Demo defence position (synthetic)",
        text="The defence submits (demo) that the synthetic event is not established.",
        document_id=defence_filing.id,
        para_from=8,
        para_to=8,
        citation_id=c_defence.id,
        finding_id=finding.id,
    )
    court_argument = Argument(
        id=demo_id("argument:AR-DEMO-003"),
        case_id=case.id,
        argument_key="AR-DEMO-003",
        party=Party.COURT,
        title="Demo Panel response (synthetic)",
        text="The Panel addressed both positions at paragraphs 12–14 (demo).",
        document_id=judgment.id,
        para_from=12,
        para_to=14,
        citation_id=c_judgment_para.id,
        finding_id=finding.id,
    )
    session.add_all([spo_argument, defence_argument, court_argument])
    session.flush()
    session.add_all(
        [
            ArgumentResponse(
                id=demo_id("response:1"),
                argument_id=spo_argument.id,
                response_argument_id=defence_argument.id,
                response_kind=ArgumentResponseKind.DISPUTES,
                citation_id=c_defence.id,
            ),
            ArgumentResponse(
                id=demo_id("response:2"),
                argument_id=spo_argument.id,
                response_argument_id=court_argument.id,
                response_kind=ArgumentResponseKind.RULES_ON,
                citation_id=c_judgment_para.id,
            ),
            ArgumentResponse(
                id=demo_id("response:3"),
                argument_id=defence_argument.id,
                response_argument_id=court_argument.id,
                response_kind=ArgumentResponseKind.RULES_ON,
                citation_id=c_judgment_para.id,
            ),
        ]
    )

    # --- events (five date types, never merged) ------------------------------
    session.add_all(
        [
            Event(
                id=demo_id("event:incident"),
                case_id=case.id,
                title="Demo incident date (as alleged)",
                date_type=DateType.EVENT,
                date_from=date(1999, 5, 1),
                date_to=date(1999, 5, 3),
                date_precision=DatePrecision.RANGE,
                incident_id=incident.id,
                citation_id=c_spo.id,
            ),
            Event(
                id=demo_id("event:document"),
                case_id=case.id,
                title="Demo judgment document date",
                date_type=DateType.DOCUMENT,
                date_from=date(2024, 1, 15),
                date_precision=DatePrecision.EXACT,
                document_id=judgment.id,
                citation_id=c_judgment_page.id,
            ),
            Event(
                id=demo_id("event:filing"),
                case_id=case.id,
                title="Demo prosecution submission filed",
                date_type=DateType.FILING,
                date_from=date(2023, 3, 1),
                date_precision=DatePrecision.EXACT,
                document_id=spo_filing.id,
                citation_id=c_spo.id,
            ),
            Event(
                id=demo_id("event:testimony"),
                case_id=case.id,
                title="W-DEMO-001 testifies (demo)",
                date_type=DateType.TESTIMONY,
                date_from=date(2023, 6, 1),
                date_precision=DatePrecision.EXACT,
                hearing_id=hearing.id,
                citation_id=c_transcript.id,
            ),
            Event(
                id=demo_id("event:decision"),
                case_id=case.id,
                title="Demo judgment delivered",
                date_type=DateType.DECISION,
                date_from=date(2024, 1, 15),
                date_precision=DatePrecision.EXACT,
                document_id=judgment.id,
                citation_id=c_finding.id,
            ),
        ]
    )

    # --- graph -------------------------------------------------------------------
    def node(kind: EntityKind, label: str, **fk: uuid.UUID) -> GraphNode:
        gn = GraphNode(
            id=demo_id(f"node:{kind.value}:{label}"),
            case_id=case.id,
            entity_kind=kind,
            label=label,
            **fk,
        )
        session.add(gn)
        return gn

    n_person_a = node(EntityKind.PERSON, "Demo Person A", person_id=person_a.id)
    n_witness_1 = node(EntityKind.WITNESS, "W-DEMO-001", witness_id=protected_witness.id)
    n_witness_2 = node(EntityKind.WITNESS, "W-DEMO-002", witness_id=public_witness.id)
    n_org = node(EntityKind.ORGANIZATION, "Demo Unit", organization_id=organization.id)
    n_location = node(EntityKind.LOCATION, "Demo Village", location_id=location.id)
    n_judgment = node(EntityKind.DOCUMENT, "F-DEMO-001", document_id=judgment.id)
    n_exhibit = node(EntityKind.EXHIBIT, "P-DEMO-001", exhibit_id=exhibit.id)
    n_incident = node(EntityKind.INCIDENT, "Demo incident", incident_id=incident.id)
    n_finding = node(EntityKind.FINDING, "FD-DEMO-001", finding_id=finding.id)
    n_hearing = node(EntityKind.HEARING, "Hearing 2023-06-01", hearing_id=hearing.id)
    n_spo_arg = node(EntityKind.ARGUMENT, "AR-DEMO-001", argument_id=spo_argument.id)
    n_def_arg = node(EntityKind.ARGUMENT, "AR-DEMO-002", argument_id=defence_argument.id)
    session.flush()

    def edge(
        key: str, src: GraphNode, dst: GraphNode, rtype: RelationshipType, citation: Citation
    ) -> None:
        session.add(
            Relationship(
                id=demo_id(f"edge:{key}"),
                case_id=case.id,
                from_node_id=src.id,
                to_node_id=dst.id,
                relationship_type=rtype,
                citation_id=citation.id,
                verification_state=VerificationState.HUMAN_VERIFIED,
                verified_by="demo-reviewer",
                verified_at=_REVIEWED_AT,
            )
        )

    edge("1", n_person_a, n_org, RelationshipType.MEMBER_OF, c_judgment_para)
    edge("2", n_witness_1, n_hearing, RelationshipType.TESTIFIED_AT, c_transcript)
    edge("3", n_witness_1, n_incident, RelationshipType.TESTIFIED_ABOUT, c_transcript)
    edge("4", n_incident, n_location, RelationshipType.OCCURRED_AT, c_spo)
    edge("5", n_exhibit, n_judgment, RelationshipType.CITED_IN, c_exhibit)
    edge("6", n_finding, n_exhibit, RelationshipType.RELIES_ON, c_exhibit)
    edge("7", n_finding, n_incident, RelationshipType.PART_OF_INCIDENT, c_finding)
    edge("8", n_def_arg, n_spo_arg, RelationshipType.DISPUTES, c_defence)
    edge("9", n_witness_2, n_hearing, RelationshipType.TESTIFIED_AT, c_exhibit)
    edge("10", n_person_a, n_finding, RelationshipType.MENTIONED_IN, c_finding)
    # Two edges that must never surface: one a reviewer rejected, one whose
    # only provenance is an unresolved citation.
    session.add(
        Relationship(
            id=demo_id("edge:rejected"),
            case_id=case.id,
            from_node_id=n_person_a.id,
            to_node_id=n_location.id,
            relationship_type=RelationshipType.LOCATED_AT,
            citation_id=c_spo.id,
            verification_state=VerificationState.HUMAN_REJECTED,
            verified_by="demo-reviewer",
            verified_at=_REVIEWED_AT,
            note="Rejected on review (demo).",
        )
    )
    session.add(
        Relationship(
            id=demo_id("edge:unresolved"),
            case_id=case.id,
            from_node_id=n_person_a.id,
            to_node_id=n_incident.id,
            relationship_type=RelationshipType.ASSOCIATED_WITH,
            citation_id=c_unresolved.id,
            verification_state=VerificationState.UNRESOLVED,
        )
    )

    # --- discovery provenance ----------------------------------------------------
    session.add_all(
        [
            SourceRecord(
                id=demo_id("source:DEMO-REC-001"),
                case_id=case.id,
                source_system=SourceSystem.KSC_PUBLIC_COURT_RECORDS,
                external_record_id="DEMO-REC-001",
                record_type="filing",
                language="en",
                discovery_url=f"{_DEMO_URL}records/DEMO-REC-001",
                canonical_source_url=f"{_DEMO_URL}F-DEMO-001/RED.pdf",
                title="Demo judgment (synthetic)",
                visibility=Visibility.PUBLIC_REDACTED,
                raw_metadata={"synthetic": True},
                discovered_at=_REVIEWED_AT,
                last_seen_at=_REVIEWED_AT,
                document_id=judgment.id,
                document_version_id=judgment_red.id,
            ),
            SourceRecord(
                id=demo_id("source:DEMO-HEARING-001"),
                case_id=case.id,
                source_system=SourceSystem.KSC_CASE_PAGE,
                external_record_id="DEMO-HEARING-001",
                record_type="hearing",
                discovery_url=f"{_DEMO_URL}hearings/DEMO-HEARING-001",
                title="Demo hearing (synthetic)",
                visibility=Visibility.PUBLIC,
                raw_metadata={"synthetic": True},
                discovered_at=_REVIEWED_AT,
                last_seen_at=_REVIEWED_AT,
                hearing_id=hearing.id,
                transcript_id=transcript.id,
            ),
        ]
    )

    # --- human note ---------------------------------------------------------------
    note = ResearchNote(
        id=demo_id("note:1"),
        case_id=case.id,
        author="demo-researcher",
        title="Demo note (human)",
        body="A human note pointing at two sources. Not evidence.",
    )
    note.citations = [c_judgment_para, c_transcript]
    session.add(note)

    session.add(
        AuditLog(
            actor="system:demo-fixture",
            action="fixture.loaded",
            entity_type="case",
            entity_id=DEMO_CASE_NUMBER,
            detail={"synthetic": True},
        )
    )
    session.flush()
    return case, True


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    with session_scope() as session:
        case, created = load_demo_fixture(session)
    log.info("demo case %s %s", case.case_number, "created" if created else "already present")


if __name__ == "__main__":
    main()
