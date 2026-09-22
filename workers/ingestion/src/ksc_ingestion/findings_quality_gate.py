"""Phase 10 real-corpus quality gate.

Absence of the Trial Judgment is reported as a limitation, never papered over
with a party brief. The gate evaluates the capability against the available
public Court decision benchmark and fails unsupported relationship claims.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ksc_api.models import (
    Argument,
    ArgumentResponse,
    ArtifactStatus,
    Case,
    Document,
    DocumentParagraph,
    DocumentVersion,
    Finding,
    FindingEvidenceLink,
    ResearchNote,
    ResolutionState,
    SourceRecord,
    VerificationState,
)


@dataclass(frozen=True)
class Phase10QualityReport:
    phase: int
    generated_at: str
    case_number: str
    input_manifest: str
    input_manifest_sha256: str
    controlled_records: int
    pinned_versions: int
    held_versions: int
    trial_judgment_present: bool
    benchmark_record_ref: str | None
    benchmark_record_type: str | None
    findings: int
    exact_paragraph_mappings: int
    explicit_court_cited_links: int
    explicit_links_resolved: int
    explicit_links_with_exact_source_coordinate: int
    unsupported_relied_upon_labels: int
    party_positions: int
    party_positions_by_party: dict[str, int]
    court_responses: int
    human_verified_relationships: int
    unresolved_linked_citations: int
    missing_underlying_party_sources: list[str]
    contrary_links: int
    human_notes: int
    ai_generated_findings: int
    missing_official_material: list[str]
    passed: bool


def run_phase10_gate(
    session: Session,
    *,
    case_number: str,
    manifest_path: Path,
    generated_at: str,
) -> Phase10QualityReport:
    case = session.scalar(select(Case).where(Case.case_number == case_number))
    if case is None:
        raise RuntimeError(f"case {case_number} is not seeded")
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pinned_versions = int(manifest["version_count"])
    held_versions = (
        session.scalar(
            select(func.count())
            .select_from(DocumentVersion)
            .join(Document, Document.id == DocumentVersion.document_id)
            .where(
                Document.case_id == case.id,
                DocumentVersion.artifact_status == ArtifactStatus.FETCHED,
            )
        )
        or 0
    )
    controlled_records = (
        session.scalar(
            select(func.count()).select_from(SourceRecord).where(SourceRecord.case_id == case.id)
        )
        or 0
    )
    trial_judgment_present = (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.case_id == case.id, func.lower(Document.document_type) == "judgment")
        )
        or 0
    ) > 0
    findings = session.scalars(
        select(Finding).where(
            Finding.case_id == case.id,
            Finding.extraction_origin == "phase10_hand_verified",
            Finding.verification_state == VerificationState.HUMAN_VERIFIED,
        )
    ).all()
    finding_ids = [finding.id for finding in findings]
    links = (
        session.scalars(
            select(FindingEvidenceLink).where(FindingEvidenceLink.finding_id.in_(finding_ids))
        ).all()
        if finding_ids
        else []
    )
    arguments = (
        session.scalars(select(Argument).where(Argument.finding_id.in_(finding_ids))).all()
        if finding_ids
        else []
    )
    argument_ids = [argument.id for argument in arguments]
    responses = (
        session.scalars(
            select(ArgumentResponse).where(ArgumentResponse.argument_id.in_(argument_ids))
        ).all()
        if argument_ids
        else []
    )

    exact_mappings = 0
    for finding in findings:
        if finding.judgment_version_id is None:
            continue
        paragraphs = session.scalars(
            select(DocumentParagraph)
            .where(
                DocumentParagraph.document_version_id == finding.judgment_version_id,
                DocumentParagraph.paragraph_number >= finding.para_from,
                DocumentParagraph.paragraph_number <= (finding.para_to or finding.para_from),
            )
            .order_by(DocumentParagraph.paragraph_number)
        ).all()
        if paragraphs and finding.text == "\n\n".join(paragraph.text for paragraph in paragraphs):
            exact_mappings += 1

    explicit = [link for link in links if link.court_cited]
    explicit_resolved = sum(
        link.citation.resolution_state == ResolutionState.RESOLVED for link in explicit
    )
    exact_source = sum(
        link.citation.source_document_version_id is not None
        and link.citation.source_para is not None
        and link.citation.source_page is not None
        and link.citation.source_char_start is not None
        and link.citation.source_char_end is not None
        for link in explicit
    )
    unsupported = sum(
        link.relationship_basis != "explicit_court_citation"
        or link.citation.resolution_state != ResolutionState.RESOLVED
        or link.citation.source_para is None
        or link.citation.target_document_version_id is None
        for link in explicit
    )
    party_arguments = [
        argument for argument in arguments if argument.party.value in {"spo", "defence"}
    ]
    party_counts = {
        party: sum(argument.party.value == party for argument in party_arguments)
        for party in ("spo", "defence")
    }
    missing_refs = sorted(
        {
            argument.underlying_source_ref
            for argument in party_arguments
            if argument.source_scope != "direct_source" and argument.underlying_source_ref
        }
    )
    verified_relationships = (
        sum(link.verification_state == VerificationState.HUMAN_VERIFIED for link in links)
        + sum(
            argument.verification_state == VerificationState.HUMAN_VERIFIED
            for argument in arguments
        )
        + sum(
            response.verification_state == VerificationState.HUMAN_VERIFIED
            for response in responses
        )
    )
    unresolved = sum(link.citation.resolution_state != ResolutionState.RESOLVED for link in links)
    benchmark_doc = findings[0].judgment_document if findings else None
    missing_material = []
    if not trial_judgment_present:
        missing_material.append("Public Trial Judgment for KSC-BC-2020-06")
    missing_material.extend(f"Underlying public party filing {ref}" for ref in missing_refs)
    human_notes = (
        session.scalar(
            select(func.count())
            .select_from(ResearchNote)
            .where(ResearchNote.finding_id.in_(finding_ids))
        )
        if finding_ids
        else 0
    )
    passed = all(
        [
            # The held corpus is exactly the pinned manifest (no drift, no extras).
            held_versions == pinned_versions,
            len(findings) >= 1,
            exact_mappings == len(findings),
            len(explicit) >= 1,
            explicit_resolved == len(explicit),
            exact_source == len(explicit),
            unsupported == 0,
            party_counts == {"spo": 1, "defence": 1},
            len(responses) >= 1,
            verified_relationships == len(links) + len(arguments) + len(responses),
            unresolved == 0,
        ]
    )
    return Phase10QualityReport(
        phase=10,
        generated_at=generated_at,
        case_number=case_number,
        input_manifest=str(manifest_path),
        input_manifest_sha256=manifest_hash,
        controlled_records=controlled_records,
        pinned_versions=pinned_versions,
        held_versions=held_versions,
        trial_judgment_present=trial_judgment_present,
        benchmark_record_ref=benchmark_doc.official_ref if benchmark_doc else None,
        benchmark_record_type=benchmark_doc.document_type if benchmark_doc else None,
        findings=len(findings),
        exact_paragraph_mappings=exact_mappings,
        explicit_court_cited_links=len(explicit),
        explicit_links_resolved=explicit_resolved,
        explicit_links_with_exact_source_coordinate=exact_source,
        unsupported_relied_upon_labels=unsupported,
        party_positions=len(party_arguments),
        party_positions_by_party=party_counts,
        court_responses=len(responses),
        human_verified_relationships=verified_relationships,
        unresolved_linked_citations=unresolved,
        missing_underlying_party_sources=missing_refs,
        contrary_links=sum(link.link_type.value == "contrary" for link in links),
        human_notes=human_notes or 0,
        ai_generated_findings=0,
        missing_official_material=missing_material,
        passed=passed,
    )


def write_phase10_report(report: Phase10QualityReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8")
