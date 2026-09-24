"""ORM → read-contract mapping. The only place that knows both shapes."""

from __future__ import annotations

from urllib.parse import quote

from ksc_api.models import (
    Argument,
    ArgumentResponse,
    Case,
    Citation,
    CitationType,
    Claim,
    ClaimMention,
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentParagraph,
    DocumentVersion,
    Event,
    Exhibit,
    Finding,
    FindingEvidenceLink,
    GraphNode,
    Hearing,
    Incident,
    Organization,
    Party,
    Person,
    Relationship,
    SourceRecord,
    Transcript,
    TranscriptSegment,
    Witness,
)
from ksc_api.schemas.citation import CitableSourceType, CitationRead
from ksc_api.schemas.records import (
    ArgumentRead,
    ArgumentResponseRead,
    CaseRead,
    ClaimMentionRead,
    ClaimRead,
    DocumentChunkRead,
    DocumentDetail,
    DocumentPageRead,
    DocumentParagraphRead,
    DocumentSummary,
    DocumentVersionRead,
    EventRead,
    ExhibitRead,
    FindingDetail,
    FindingEvidenceLinkRead,
    FindingSourceAuditRead,
    FindingSummary,
    GraphNodeRead,
    HumanNoteRead,
    IncidentRead,
    JudgmentStructureRead,
    OrganizationRead,
    PersonRead,
    ReferenceCounts,
    RelationshipRead,
    TranscriptRead,
    TranscriptSegmentRead,
    WitnessPublic,
    WitnessRead,
)

ZERO_COUNTS = ReferenceCounts(
    relationships=0,
    document_mentions=0,
    transcript_mentions=0,
    exhibit_refs=0,
    findings=0,
    witnesses_who_referred=0,
    incidents=0,
    citations_resolved=0,
)


def _document_source_type(document: Document | None) -> CitableSourceType:
    if document is not None and document.filing_party == Party.SPO:
        return "spo"
    if document is not None and document.filing_party == Party.DEFENCE:
        return "defence"
    return "court"


def citation_source_type(citation: Citation) -> CitableSourceType:
    """Colour encodes source, never severity. Derived server-side so the client
    never guesses."""
    if citation.target_finding_id is not None:
        return "court"
    if citation.target_exhibit_id is not None:
        return "exhibit"
    if citation.target_witness_id is not None or citation.target_transcript_id is not None:
        return "witness"
    if citation.target_document_id is not None:
        return _document_source_type(citation.target_document)
    if citation.citation_type == CitationType.EXHIBIT:
        return "exhibit"
    if citation.citation_type in (
        CitationType.WITNESS,
        CitationType.TRANSCRIPT,
        CitationType.TRANSCRIPT_LINE,
    ):
        return "witness"
    return "court"


def _citation_ref_and_doc(citation: Citation) -> tuple[str, str | None]:
    if citation.target_finding is not None:
        doc = citation.target_finding.judgment_document
        return citation.target_finding.finding_key, doc.official_ref
    if citation.target_exhibit is not None:
        exhibit = citation.target_exhibit
        version = exhibit.document_version
        return exhibit.official_exhibit_id, version.document.official_ref if version else None
    if citation.target_witness is not None:
        return citation.target_witness.code, None
    if citation.target_transcript is not None:
        transcript = citation.target_transcript
        version = transcript.document_version
        ref = transcript.official_ref or f"T. {citation.target_page}"
        return ref, version.document.official_ref if version else None
    if citation.target_document_version is not None:
        version = citation.target_document_version
        return version.official_version_ref, version.document.official_ref
    if citation.target_document is not None:
        doc = citation.target_document
        return doc.filing_number or doc.official_ref, doc.official_ref
    return citation.raw_text, None


def to_citation(citation: Citation) -> CitationRead:
    ref, doc_id = _citation_ref_and_doc(citation)
    return CitationRead(
        id=citation.id,
        source_type=citation_source_type(citation),
        ref=ref,
        doc_id=doc_id,
        citation_type=citation.citation_type,
        raw_text=citation.raw_text,
        page=citation.target_page,
        para_from=citation.target_para_from,
        para_to=citation.target_para_to,
        line_from=citation.target_line_from,
        line_to=citation.target_line_to,
        pdf_page_index=citation.target_pdf_page_index,
        target_path=_citation_target_path(citation),
        source_document_version_ref=(
            citation.source_document_version.official_version_ref
            if citation.source_document_version is not None
            else None
        ),
        source_page=citation.source_page,
        source_pdf_page_index=citation.source_pdf_page_index,
        source_para=citation.source_para,
        source_char_start=citation.source_char_start,
        source_char_end=citation.source_char_end,
        source_url=citation.source_url,
        source_path=_citation_source_path(citation),
        resolution_state=citation.resolution_state,
        resolved=citation.is_resolved,
        display=citation.display,
        verification_state=citation.verification_state,
    )


def _citation_source_path(citation: Citation) -> str | None:
    version = citation.source_document_version
    if version is None:
        return None
    route_id = version.document.official_ref.split("/", 1)[-1]
    if "/" in route_id:
        path = (
            f"/documents/transcript?document={quote(route_id, safe='')}"
            f"&version={quote(version.official_version_ref, safe='')}"
        )
    else:
        path = f"/documents/{quote(route_id, safe='')}?version={quote(version.official_version_ref, safe='')}"
    if citation.source_page is not None:
        path += f"&page={citation.source_page}"
    elif citation.source_pdf_page_index is not None:
        path += f"&pdfPage={citation.source_pdf_page_index}"
    if citation.source_para is not None:
        path += f"&para={citation.source_para}"
    return path


def _citation_target_path(citation: Citation) -> str | None:
    if not citation.is_resolved:
        return None
    if citation.target_witness is not None:
        return f"/witnesses/{quote(citation.target_witness.code, safe='')}"
    if citation.target_exhibit is not None:
        return f"/exhibits/{quote(citation.target_exhibit.official_exhibit_id, safe='')}"
    if citation.target_transcript is not None:
        transcript = citation.target_transcript
        version = transcript.document_version
        if version is None:
            return None
        document = version.document
        route_id = document.official_ref.split("/", 1)[-1]
        if "/" in route_id:
            path = (
                f"/documents/transcript?document={quote(route_id, safe='')}"
                f"&version={quote(version.official_version_ref, safe='')}"
            )
        else:
            path = f"/documents/{quote(route_id, safe='')}?version={quote(version.official_version_ref, safe='')}"
        if citation.target_page is not None:
            path += f"&page={citation.target_page}"
            if citation.target_line_from is not None:
                path += f"&line={citation.target_line_from}"
        return path
    version = citation.target_document_version
    target_document = version.document if version is not None else citation.target_document
    if target_document is None:
        return None
    route_id = target_document.official_ref.split("/", 1)[-1]
    if "/" in route_id:
        path = "/documents/transcript"
        params = [f"document={quote(route_id, safe='')}"]
    else:
        path = f"/documents/{quote(route_id, safe='')}"
        params = []
    if version is not None:
        params.append(f"version={quote(version.official_version_ref, safe='')}")
    if citation.target_pdf_page_index is not None:
        params.append(f"pdfPage={citation.target_pdf_page_index}")
    if citation.target_para_from is not None:
        params.append(f"para={citation.target_para_from}")
    return path + (f"?{'&'.join(params)}" if params else "")


def to_case(case: Case) -> CaseRead:
    return CaseRead.model_validate(case)


def to_document_version(version: DocumentVersion) -> DocumentVersionRead:
    return DocumentVersionRead(
        official_version_ref=version.official_version_ref,
        version_type=version.version_type,
        version_label=version.version_label,
        visibility=version.visibility,
        public_date=version.public_date,
        source_url=version.source_url,
        artifact_status=version.artifact_status,
        sha256=version.sha256,
        mime_type=version.mime_type,
        page_count=version.page_count,
        fetched_at=version.fetched_at,
        text_extraction_method=version.text_extraction_method.value,
        parsed_at=version.parsed_at,
        parser_name=version.parser_name,
        parser_version=version.parser_version,
        parse_requires_review=version.parse_requires_review,
        supersedes_version_ref=(
            version.supersedes.official_version_ref if version.supersedes is not None else None
        ),
    )


def to_document_summary(document: Document, counts: ReferenceCounts) -> DocumentSummary:
    return DocumentSummary(
        official_ref=document.official_ref,
        filing_number=document.filing_number,
        title=document.title,
        document_type=document.document_type,
        language=document.language,
        filing_party=document.filing_party,
        document_date=document.document_date,
        filing_date=document.filing_date,
        public_date=document.public_date,
        visibility=document.visibility,
        counts=counts,
    )


def to_document_detail(
    document: Document, counts: ReferenceCounts, public_versions: list[DocumentVersion]
) -> DocumentDetail:
    summary = to_document_summary(document, counts)
    return DocumentDetail(
        **summary.model_dump(),
        source_url=document.source_url,
        versions=[to_document_version(v) for v in public_versions],
    )


def to_document_page(page: DocumentPage) -> DocumentPageRead:
    return DocumentPageRead.model_validate(page)


def to_document_chunk(chunk: DocumentChunk) -> DocumentChunkRead:
    return DocumentChunkRead.model_validate(chunk)


def to_document_paragraph(paragraph: DocumentParagraph) -> DocumentParagraphRead:
    return DocumentParagraphRead.model_validate(paragraph)


def to_person(person: Person, counts: ReferenceCounts) -> PersonRead:
    return PersonRead(
        slug=person.slug,
        display_name=person.display_name,
        public_role=person.public_role,
        description=person.description,
        aliases=[alias.alias for alias in person.aliases],
        counts=counts,
    )


def to_organization(organization: Organization, counts: ReferenceCounts) -> OrganizationRead:
    return OrganizationRead(
        slug=organization.slug,
        name=organization.name,
        kind=organization.kind,
        name_variants=list(organization.name_variants),
        description=organization.description,
        counts=counts,
    )


def to_witness(witness: Witness, counts: ReferenceCounts) -> WitnessRead:
    """Fails closed: only an explicitly PUBLIC witness with a stored public
    name gets a `public` block."""
    protected = witness.is_protected or witness.public_name is None
    return WitnessRead(
        code=witness.code,
        protected=protected,
        protective_measures=list(witness.protective_measures),
        counts=counts,
        public=(
            None
            if protected
            else WitnessPublic(display_name=str(witness.public_name), called_by=witness.called_by)
        ),
    )


def to_exhibit(exhibit: Exhibit, counts: ReferenceCounts) -> ExhibitRead:
    return ExhibitRead(
        official_exhibit_id=exhibit.official_exhibit_id,
        title=exhibit.title,
        description=exhibit.description,
        status=exhibit.status,
        tendered_by=exhibit.tendered_by,
        through_witness_code=(
            exhibit.through_witness.code if exhibit.through_witness is not None else None
        ),
        admitted_date=exhibit.admitted_date,
        document_date=exhibit.document_date,
        document_version_ref=(
            exhibit.document_version.official_version_ref
            if exhibit.document_version is not None
            else None
        ),
        visibility=exhibit.visibility,
        counts=counts,
    )


def to_incident(incident: Incident, counts: ReferenceCounts) -> IncidentRead:
    return IncidentRead(
        slug=incident.slug,
        title=incident.title,
        summary=incident.summary,
        location=incident.location.name if incident.location is not None else None,
        date_from=incident.date_from,
        date_to=incident.date_to,
        date_precision=incident.date_precision,
        charges_pleaded=incident.charges_pleaded,
        counts=counts,
    )


def to_event(
    event: Event,
    incident: Incident | None,
    document: Document | None,
    hearing: Hearing | None,
    source_record: SourceRecord | None,
) -> EventRead:
    citation = event.citation
    return EventRead(
        id=event.id,
        title=event.title,
        description=event.description,
        date_type=event.date_type,
        date_from=event.date_from,
        date_to=event.date_to,
        date_precision=event.date_precision,
        incident_slug=incident.slug if incident is not None else None,
        document_ref=document.official_ref if document is not None else None,
        citation=to_citation(citation) if citation is not None and citation.is_resolved else None,
        hearing_ref=hearing.official_ref if hearing is not None else None,
        source_system=source_record.source_system.value if source_record is not None else None,
        source_url=(
            source_record.canonical_source_url or source_record.discovery_url
            if source_record is not None
            else None
        ),
        extraction_origin=event.extraction_origin,
    )


def to_claim_mention(mention: ClaimMention) -> ClaimMentionRead:
    return ClaimMentionRead(
        stance=mention.stance,
        quote_text=mention.quote_text,
        note=mention.note,
        verification_state=mention.verification_state,
        citation=to_citation(mention.citation),
    )


def to_claim(claim: Claim, mentions: list[ClaimMention]) -> ClaimRead:
    source = claim.source_citation
    return ClaimRead(
        claim_key=claim.claim_key,
        text=claim.text,
        origin=claim.origin,
        verification_state=claim.verification_state,
        source_citation=to_citation(source) if source is not None and source.is_resolved else None,
        mentions=[to_claim_mention(m) for m in mentions],
    )


def to_evidence_link(link: FindingEvidenceLink) -> FindingEvidenceLinkRead:
    return FindingEvidenceLinkRead(
        link_type=link.link_type,
        court_cited=link.court_cited,
        court_cited_para=link.court_cited_para,
        relationship_basis=link.relationship_basis,
        source_category=link.source_category,
        note=link.note,
        verification_state=link.verification_state,
        citation=to_citation(link.citation),
    )


def to_argument(argument: Argument) -> ArgumentRead:
    citation = argument.citation
    return ArgumentRead(
        argument_key=argument.argument_key,
        party=argument.party,
        title=argument.title,
        text=argument.text,
        document_ref=argument.document.official_ref if argument.document is not None else None,
        document_version_ref=(
            argument.document_version.official_version_ref
            if argument.document_version is not None
            else None
        ),
        para_from=argument.para_from,
        para_to=argument.para_to,
        source_scope=argument.source_scope,
        underlying_source_ref=argument.underlying_source_ref,
        verification_state=argument.verification_state,
        citation=to_citation(citation) if citation is not None else None,
    )


def to_argument_response(response: ArgumentResponse) -> ArgumentResponseRead:
    citation = response.citation
    return ArgumentResponseRead(
        response_kind=response.response_kind.value,
        argument=to_argument(response.response_argument),
        verification_state=response.verification_state,
        citation=to_citation(citation) if citation is not None else None,
    )


def to_finding_summary(finding: Finding, counts: ReferenceCounts) -> FindingSummary:
    citation = finding.citation
    return FindingSummary(
        finding_key=finding.finding_key,
        judgment_ref=finding.judgment_document.official_ref,
        text=finding.text,
        para_from=finding.para_from,
        para_to=finding.para_to,
        person_slug=finding.person.slug if finding.person is not None else None,
        incident_slug=finding.incident.slug if finding.incident is not None else None,
        charge_ref=finding.charge_ref,
        verification_state=finding.verification_state,
        citation=to_citation(citation) if citation is not None and citation.is_resolved else None,
        counts=counts,
    )


def to_finding_detail(
    finding: Finding,
    counts: ReferenceCounts,
    links: list[FindingEvidenceLink],
    arguments: list[Argument],
    *,
    court_responses: list[ArgumentResponseRead],
    judgment: JudgmentStructureRead,
    human_notes: list[HumanNoteRead],
    source_audit: FindingSourceAuditRead,
    corroboration_categories: dict[str, int],
) -> FindingDetail:
    summary = to_finding_summary(finding, counts)
    return FindingDetail(
        **summary.model_dump(),
        legal_element=finding.legal_element,
        mode_of_liability=finding.mode_of_liability,
        evidence_links=[to_evidence_link(link) for link in links],
        arguments=[to_argument(a) for a in arguments],
        court_responses=court_responses,
        judgment=judgment,
        human_notes=human_notes,
        source_audit=source_audit,
        corroboration_categories=corroboration_categories,
        corroboration_note=(
            "No additional corroborating source has been identified in the indexed public record."
        ),
    )


def to_segment(segment: TranscriptSegment) -> TranscriptSegmentRead:
    return TranscriptSegmentRead(
        sequence=segment.sequence,
        pdf_page_index=segment.pdf_page_index,
        page_number=segment.page_number,
        line_from=segment.line_from,
        line_to=segment.line_to,
        speaker=segment.speaker,
        speaker_role=segment.speaker_role,
        witness_code=segment.witness.code if segment.witness is not None else None,
        examination_type=segment.examination_type,
        closed_session=segment.closed_session,
        text=None if segment.closed_session else segment.text,
    )


def to_transcript(transcript: Transcript, segments: list[TranscriptSegment]) -> TranscriptRead:
    version = transcript.document_version
    return TranscriptRead(
        official_ref=transcript.official_ref,
        hearing_date=transcript.hearing.hearing_date,
        session_label=transcript.hearing.session_label,
        language=transcript.language,
        visibility=transcript.visibility,
        page_from=transcript.page_from,
        page_to=transcript.page_to,
        document_version_ref=version.official_version_ref if version is not None else None,
        segments=[to_segment(s) for s in segments],
    )


def to_graph_node(node: GraphNode, ref: str, protected: bool) -> GraphNodeRead:
    return GraphNodeRead(
        id=node.id, entity_kind=node.entity_kind, label=node.label, ref=ref, protected=protected
    )


def to_relationship(edge: Relationship) -> RelationshipRead:
    return RelationshipRead(
        id=edge.id,
        from_node_id=edge.from_node_id,
        to_node_id=edge.to_node_id,
        relationship_type=edge.relationship_type,
        verification_state=edge.verification_state,
        citation=to_citation(edge.citation),
        note=edge.note,
        source_category=edge.source_category,
        extraction_origin=edge.extraction_origin,
        relationship_date=edge.relationship_date,
        date_precision=edge.date_precision,
    )
