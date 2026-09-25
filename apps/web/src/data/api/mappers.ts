/**
 * API wire shapes → screen-facing types.
 *
 * Fail-closed rules live here, not in screens:
 * - a citation that is not RESOLVED maps to `resolved: false` (no chip);
 * - a human-rejected fact maps to no verification state and is dropped;
 * - a witness is public only when the API sent a `public` block with a
 *   display name and a calling party; anything else is code-only.
 */

import type {
  AnswerBlock,
  Citation,
  DateType,
  Direction,
  ReferenceCounts,
  SourceType,
  VerificationState,
  Witness,
} from "@ksc/shared";
import type {
  DirectoryKind,
  DirectoryRow,
  DocumentView,
  EntityMention,
  EvidenceRow,
  ExhibitStatusEventView,
  NetworkQuery,
  NetworkView,
  ProvenanceView,
  WitnessAppearanceView,
  FindingArgumentView,
  FindingCitationView,
  FindingView,
  IncidentView,
  OrganizationDossier,
  ExhibitDossier,
  AiResearchRun,
  AiResearchSource,
  AiRunSummaryView,
  AppealIssueSummaryView,
  AppealIssueView,
  AppealWorkspaceView,
  ArgumentLabView,
  NetworkEdge,
  NetworkNode,
  PersonDossier,
  WitnessDossier,
  SearchResult,
  TimelineItem,
  StatementComparisonView,
} from "../contract";
import type {
  ApiAiRun,
  ApiAiRunSummary,
  ApiAiSource,
  ApiAppealIssue,
  ApiAppealIssueSummary,
  ApiAppealWorkspace,
  ApiArgumentLab,
  ApiCitation,
  ApiClaim,
  ApiDocumentChunk,
  ApiDocumentDetail,
  ApiDocumentSummary,
  ApiDocumentVersion,
  ApiEvent,
  ApiExhibit,
  ApiFindingSummary,
  ApiFindingDetail,
  ApiGraphNode,
  ApiIncident,
  ApiOrganization,
  ApiParty,
  ApiPerson,
  ApiReferenceCounts,
  ApiRelationship,
  ApiSearchHit,
  ApiStance,
  ApiStatementComparison,
  ApiVerificationState,
  ApiWitness,
  ApiEntityMention,
  ApiEdge,
  ApiEdgePage,
  ApiExhibitStatusEvent,
  ApiProvenance,
  ApiWitnessAppearance,
} from "./types";
import { withExactSource } from "@/lib/exact-source";

const VERIFICATION: Record<ApiVerificationState, VerificationState | null> = {
  human_verified: "verified",
  ai_flagged: "ai-flagged",
  unresolved: "unresolved",
  needs_more_evidence: "needs-evidence",
  unreviewed: "unreviewed",
  // Rejected facts never surface. The API already withholds them.
  human_rejected: null,
};

const DIRECTION: Record<ApiStance, Direction | null> = {
  supports: "supports",
  contradicts: "contradicts",
  qualifies: "qualifies",
  neutral: "neutral",
  // "Unclear" has no design vocabulary entry; withheld rather than guessed.
  unclear: null,
};

const NODE_TYPE: Record<string, SourceType | "person"> = {
  person: "person",
  witness: "witness",
  organization: "organisation",
  location: "location",
  document: "court",
  exhibit: "exhibit",
  incident: "incident",
  event: "court",
  claim: "court",
  finding: "court",
  argument: "court",
  hearing: "court",
};

export function toVerification(state: ApiVerificationState): VerificationState | null {
  return VERIFICATION[state] ?? null;
}

export function toAppealIssueSummary(issue: ApiAppealIssueSummary): AppealIssueSummaryView {
  return {
    id: issue.id,
    key: issue.issue_key,
    category: issue.category,
    context: issue.context,
    title: issue.title,
    description: issue.description,
    findingKey: issue.finding_key,
    paraFrom: issue.para_from,
    paraTo: issue.para_to ?? undefined,
    courtTreatment: issue.court_treatment,
    courtTreatmentNote: issue.court_treatment_note,
    redTeamResult: issue.red_team_result,
    verification: toVerification(issue.verification_state) ?? "unreviewed",
  };
}

export function toStatementComparison(comparison: ApiStatementComparison): StatementComparisonView {
  return {
    id: comparison.id,
    key: comparison.comparison_key,
    issueKey: comparison.issue_key ?? undefined,
    title: comparison.title,
    type: comparison.comparison_type,
    classification: comparison.classification,
    statementA: {
      excerpt: comparison.statement_a_excerpt,
      speaker: comparison.statement_a_speaker ?? undefined,
      source: findingCitation(comparison.statement_a_citation),
    },
    statementB: {
      excerpt: comparison.statement_b_excerpt,
      speaker: comparison.statement_b_speaker ?? undefined,
      source: findingCitation(comparison.statement_b_citation),
    },
    explanation: comparison.explanation,
    verification: toVerification(comparison.verification_state) ?? "unreviewed",
  };
}

function redTeamFinding(row: ApiArgumentLab["stages"][number]) {
  return {
    sequence: row.sequence,
    perspective: row.perspective,
    category: row.category,
    text: row.text,
    verification: toVerification(row.verification_state) ?? "unreviewed",
    source: row.citation ? findingCitation(row.citation) : undefined,
  };
}

export function toAppealIssue(issue: ApiAppealIssue): AppealIssueView {
  return {
    ...toAppealIssueSummary(issue),
    notes: issue.notes ?? undefined,
    sources: issue.sources.map((source) => ({
      id: source.id,
      sequence: source.sequence,
      role: source.role,
      category: source.source_category,
      excerpt: source.excerpt,
      note: source.note ?? undefined,
      verification: toVerification(source.verification_state) ?? "unreviewed",
      source: findingCitation(source.citation),
    })),
    missingMaterial: issue.missing_material,
    comparisons: issue.statement_comparisons.map(toStatementComparison),
    redTeam: issue.red_team_reviews.map((review) => ({
      result: review.result,
      summary: review.summary,
      origin: review.origin,
      verification: toVerification(review.verification_state) ?? "unreviewed",
      findings: review.findings.map(redTeamFinding),
    })),
    audit: {
      citationsTotal: issue.citation_audit.citations_total,
      citationsResolved: issue.citation_audit.citations_resolved,
      quotesVerified: issue.citation_audit.quotes_verified,
      sourcesHumanVerified: issue.citation_audit.sources_human_verified,
      unresolved: issue.citation_audit.unresolved,
      unsupportedRelationships: issue.citation_audit.unsupported_relationships,
      readyForHumanReview: issue.citation_audit.ready_for_human_review,
      issues: issue.citation_audit.issues,
    },
  };
}

export function toAppealWorkspace(workspace: ApiAppealWorkspace): AppealWorkspaceView {
  return {
    issues: workspace.issues.map(toAppealIssueSummary),
    coverage: {
      issues: workspace.coverage.issues,
      sourceBackedLinks: workspace.coverage.source_backed_links,
      comparisons: workspace.coverage.statement_comparisons,
      redTeamReviews: workspace.coverage.red_team_reviews,
      citationsResolved: workspace.coverage.citations_resolved,
      citationsUnresolved: workspace.coverage.citations_unresolved,
      humanVerifiedRelationships: workspace.coverage.human_verified_relationships,
      needsMoreEvidence: workspace.coverage.needs_more_evidence,
    },
    limitations: workspace.corpus_limitations,
  };
}

export function toArgumentLab(lab: ApiArgumentLab): ArgumentLabView {
  return {
    issue: toAppealIssueSummary(lab.issue),
    title: lab.draft_title,
    draft: lab.draft_text,
    citations: lab.draft_citations.map(findingCitation),
    unsupportedSentences: lab.unsupported_sentences,
    stages: lab.stages.map(redTeamFinding),
    result: lab.result,
    notice: lab.notice,
  };
}

/** Route id of a document: the official reference without the case prefix. */
export function documentRouteId(officialRef: string): string {
  const [, ...rest] = officialRef.split("/");
  return rest.length ? rest.join("/") : officialRef;
}

function documentHref(officialRef: string | null): string {
  return officialRef ? `/documents/${documentRouteId(officialRef)}` : "/documents";
}

export function toCitation(citation: ApiCitation): Citation {
  const resolved = citation.resolved && citation.resolution_state === "resolved";
  return {
    sourceType: citation.source_type,
    ref: citation.ref,
    docId: citation.doc_id ? documentRouteId(citation.doc_id) : citation.ref,
    page: citation.page ?? undefined,
    paraFrom: citation.para_from ?? undefined,
    paraTo: citation.para_to ?? undefined,
    lineFrom: citation.line_from ?? undefined,
    lineTo: citation.line_to ?? undefined,
    resolved,
    // The API persists "UNRESOLVED" for anything not resolved; never rebuilt here.
    display: resolved ? citation.display : "UNRESOLVED",
  };
}

export function toCounts(counts: ApiReferenceCounts): ReferenceCounts {
  return {
    documentMentions: counts.document_mentions,
    transcriptMentions: counts.transcript_mentions,
    exhibitRefs: counts.exhibit_refs,
    findings: counts.findings,
    witnessesWhoReferred: counts.witnesses_who_referred,
    incidents: counts.incidents,
    citationsResolved: counts.citations_resolved,
  };
}

function references(counts: ApiReferenceCounts): number {
  return counts.relationships + counts.citations_resolved;
}

function partySource(party: ApiParty | null): Citation["sourceType"] {
  if (party === "spo") return "spo";
  if (party === "defence") return "defence";
  return "court";
}

const NO_DATE = "—";

export function documentRow(document: ApiDocumentSummary): DirectoryRow {
  const id = document.filing_number ?? documentRouteId(document.official_ref);
  return {
    id,
    title: document.title,
    kind: "documents",
    description: [
      document.document_type,
      document.language,
      document.filing_party,
      document.visibility,
    ]
      .filter(Boolean)
      .join(" · "),
    date: document.filing_date ?? document.document_date ?? NO_DATE,
    references: references(document.counts),
    verification: "unreviewed",
    href: documentHref(document.official_ref),
  };
}

export function personRow(person: ApiPerson): DirectoryRow {
  return {
    id: person.slug,
    title: person.display_name,
    kind: "people",
    description: person.public_role ?? "",
    date: NO_DATE,
    references: references(person.counts),
    verification: "unreviewed",
    href: `/people/${person.slug}`,
    counts: toCounts(person.counts),
    relationshipCount: person.counts.relationships,
  };
}

export function witnessRow(witness: ApiWitness): DirectoryRow {
  const mapped = toWitness(witness);
  return {
    id: witness.code,
    title: mapped.protected ? witness.code : mapped.public.displayName,
    kind: "witnesses",
    description: mapped.protected ? "" : (mapped.public.calledBy ?? ""),
    date: NO_DATE,
    references: references(witness.counts),
    verification: "unreviewed",
    href: `/witnesses/${witness.code}`,
    ...(mapped.protected ? { protected: true } : {}),
    counts: toCounts(witness.counts),
    relationshipCount: witness.counts.relationships,
  };
}

export function exhibitRow(exhibit: ApiExhibit): DirectoryRow {
  return {
    id: exhibit.official_exhibit_id,
    title: exhibit.title,
    kind: "exhibits",
    description: exhibit.description ?? exhibit.title,
    date: exhibit.admitted_date ?? exhibit.document_date ?? NO_DATE,
    references: references(exhibit.counts),
    verification: "unreviewed",
    href: `/exhibits/${encodeURIComponent(exhibit.official_exhibit_id)}`,
    status: exhibit.status,
    party: exhibit.tendered_by ?? undefined,
    relatedWitness: exhibit.through_witness_code ?? undefined,
    counts: toCounts(exhibit.counts),
    relationshipCount: exhibit.counts.relationships,
  };
}

export function toExhibit(exhibit: ApiExhibit): ExhibitDossier {
  return {
    id: exhibit.official_exhibit_id,
    title: exhibit.title,
    description: exhibit.description ?? undefined,
    status: exhibit.status,
    tenderedBy: exhibit.tendered_by ?? undefined,
    throughWitnessCode: exhibit.through_witness_code ?? undefined,
    admittedDate: exhibit.admitted_date ?? undefined,
    documentDate: exhibit.document_date ?? undefined,
    documentVersionRef: exhibit.document_version_ref ?? undefined,
    visibility: exhibit.visibility,
    counts: toCounts(exhibit.counts),
    relationshipCount: exhibit.counts.relationships,
  };
}

export function toOrganization(organization: ApiOrganization): OrganizationDossier {
  return {
    slug: organization.slug,
    name: organization.name,
    kind: organization.kind ?? undefined,
    nameVariants: organization.name_variants,
    description: organization.description ?? undefined,
    counts: toCounts(organization.counts),
    relationshipCount: organization.counts.relationships,
  };
}

export function incidentRow(incident: ApiIncident): DirectoryRow {
  return {
    id: incident.slug,
    title: incident.title,
    kind: "incidents",
    description: incident.location ?? "",
    date: incident.date_from ?? NO_DATE,
    references: references(incident.counts),
    verification: "unreviewed",
    href: `/incidents/${incident.slug}`,
  };
}

export function toIncident(incident: ApiIncident): IncidentView {
  return {
    slug: incident.slug,
    title: incident.title,
    summary: incident.summary ?? undefined,
    location: incident.location ?? undefined,
    dateFrom: incident.date_from ?? undefined,
    dateTo: incident.date_to ?? undefined,
    datePrecision: incident.date_precision,
    charges: incident.charges_pleaded ?? [],
    counts: toCounts(incident.counts),
  };
}

export function findingRow(finding: ApiFindingSummary): DirectoryRow | null {
  const verification = toVerification(finding.verification_state);
  if (verification === null) return null;
  return {
    id: finding.finding_key,
    title: `${documentRouteId(finding.judgment_ref)} · ¶${finding.para_from}${finding.para_to && finding.para_to !== finding.para_from ? `–${finding.para_to}` : ""}`,
    kind: "findings",
    description:
      finding.text.length > 180 ? `${finding.text.slice(0, 177).trimEnd()}…` : finding.text,
    date: NO_DATE,
    references: references(finding.counts),
    verification,
    href: `/findings/${finding.finding_key}`,
  };
}

function findingCitation(citation: ApiCitation): FindingCitationView {
  return {
    citation: toCitation(citation),
    targetPath: citation.target_path ?? undefined,
    sourcePath: citation.source_path ?? undefined,
    rawText: citation.raw_text,
    resolutionState: citation.resolution_state,
  };
}

function findingArgument(argument: ApiFindingDetail["arguments"][number]): FindingArgumentView {
  return {
    key: argument.argument_key,
    party: argument.party,
    title: argument.title,
    text: argument.text,
    documentRef: argument.document_ref ?? undefined,
    versionRef: argument.document_version_ref ?? undefined,
    paraFrom: argument.para_from ?? undefined,
    paraTo: argument.para_to ?? undefined,
    sourceScope: argument.source_scope,
    underlyingSourceRef: argument.underlying_source_ref ?? undefined,
    verification: toVerification(argument.verification_state) ?? "unreviewed",
    source: argument.citation ? findingCitation(argument.citation) : undefined,
  };
}

export function toFinding(finding: ApiFindingDetail): FindingView {
  return {
    key: finding.finding_key,
    text: finding.text,
    paraFrom: finding.para_from,
    paraTo: finding.para_to ?? undefined,
    chargeRef: finding.charge_ref ?? undefined,
    legalElement: finding.legal_element ?? undefined,
    modeOfLiability: finding.mode_of_liability ?? undefined,
    verification: toVerification(finding.verification_state) ?? "unreviewed",
    source: finding.citation ? findingCitation(finding.citation) : undefined,
    adjudicativeRecord: {
      ref: finding.judgment.document_ref,
      title: finding.judgment.document_title,
      documentType: finding.judgment.document_type,
      versionRef: finding.judgment.version_ref ?? undefined,
      visibility: finding.judgment.visibility,
      sourceUrl: finding.judgment.source_url ?? undefined,
      sections: finding.judgment.sections.map((section) => ({
        heading: section.heading,
        level: section.level,
        paraFrom: section.para_from ?? undefined,
        paraTo: section.para_to ?? undefined,
      })),
      paragraphs: finding.judgment.paragraphs.map((paragraph) => ({
        number: paragraph.paragraph_number,
        page: paragraph.page_from ?? undefined,
        pdfPageIndex: paragraph.pdf_page_index_from,
        text: paragraph.text,
      })),
    },
    evidence: finding.evidence_links.map((link) => ({
      linkType: link.link_type,
      courtCited: link.court_cited,
      courtCitedPara: link.court_cited_para ?? undefined,
      relationshipBasis: link.relationship_basis,
      sourceCategory: link.source_category,
      note: link.note ?? undefined,
      verification: toVerification(link.verification_state) ?? "unreviewed",
      source: findingCitation(link.citation),
    })),
    arguments: finding.arguments.map(findingArgument),
    courtResponses: finding.court_responses.map((response) => ({
      kind: response.response_kind,
      response: findingArgument(response.argument),
      verification: toVerification(response.verification_state) ?? "unreviewed",
      source: response.citation ? findingCitation(response.citation) : undefined,
    })),
    humanNotes: finding.human_notes.map((note) => ({
      author: note.author,
      title: note.title,
      body: note.body,
      sources: note.citations.map(findingCitation),
    })),
    audit: {
      citationsTotal: finding.source_audit.citations_total,
      citationsResolved: finding.source_audit.citations_resolved,
      citationsUnresolved: finding.source_audit.citations_unresolved,
      citationsAmbiguous: finding.source_audit.citations_ambiguous,
      sourcesMissing: finding.source_audit.sources_missing,
      relationshipsUnverified: finding.source_audit.relationships_unverified,
      publicRedactedSources: finding.source_audit.public_redacted_sources,
      explicitlyCitedByCourt: finding.source_audit.explicitly_cited_by_court,
      relatedNotExplicit: finding.source_audit.related_not_explicit,
      issues: finding.source_audit.issues,
    },
    corroborationCategories: finding.corroboration_categories,
    corroborationNote: finding.corroboration_note,
  };
}

export const DIRECTORY_PATH: Record<DirectoryKind, string> = {
  people: "/people",
  witnesses: "/witnesses",
  documents: "/documents",
  findings: "/findings",
  exhibits: "/exhibits",
  incidents: "/incidents",
};

export function toPerson(person: ApiPerson): PersonDossier {
  return {
    slug: person.slug,
    displayName: person.display_name,
    role: person.public_role ?? "",
    aliases: person.aliases,
    counts: toCounts(person.counts),
    relationshipCount: person.counts.relationships,
  };
}

export function toWitnessDossier(witness: ApiWitness): WitnessDossier {
  return {
    witness: toWitness(witness),
    counts: toCounts(witness.counts),
    relationshipCount: witness.counts.relationships,
  };
}

export function toWitness(witness: ApiWitness): Witness {
  const calledBy = witness.public?.called_by;
  const isPublic =
    !witness.protected &&
    witness.public !== undefined &&
    witness.public.display_name.length > 0 &&
    (calledBy === "spo" || calledBy === "defence");
  if (!isPublic || witness.public === undefined || (calledBy !== "spo" && calledBy !== "defence")) {
    return {
      code: witness.code,
      protected: true,
      protectiveMeasures: witness.protective_measures,
    };
  }
  return {
    code: witness.code,
    protected: false,
    protectiveMeasures: witness.protective_measures,
    public: { displayName: witness.public.display_name, calledBy },
  };
}

export function toDocument(
  document: ApiDocumentDetail,
  chunks: ApiDocumentChunk[],
  version: ApiDocumentVersion | undefined = document.versions.at(-1),
): DocumentView {
  const routeId = documentRouteId(document.official_ref);
  const visibility: DocumentView["visibility"] =
    document.visibility === "public" || document.visibility === "public_redacted"
      ? document.visibility
      : "not_public";
  const isPublic = visibility !== "not_public";
  const ref = document.filing_number ?? routeId;
  return {
    id: ref,
    title: document.title,
    type: document.document_type,
    language: document.language ?? "",
    page: chunks[0]?.page_from ?? chunks[0]?.pdf_page_index_from ?? 0,
    coordinateKind:
      chunks[0]?.page_from !== null && chunks[0]?.page_from !== undefined ? "source" : "pdf",
    paragraphs: isPublic
      ? chunks.map((chunk) => ({
          number: chunk.para_from ?? undefined,
          text: chunk.text,
          page: chunk.page_from ?? undefined,
          pageTo: chunk.page_to ?? undefined,
          pdfPageIndex: chunk.pdf_page_index_from ?? undefined,
          pdfPageIndexTo: chunk.pdf_page_index_to ?? undefined,
        }))
      : [],
    citation: {
      sourceType: partySource(document.filing_party),
      ref,
      docId: routeId,
      resolved: true,
      display: ref,
    },
    visibility,
    pageCount: version?.page_count ?? undefined,
    documentDate: document.document_date ?? undefined,
    filingDate: document.filing_date ?? undefined,
    versionRef: version?.official_version_ref,
    versionType: version?.version_type,
    versionLabel: version?.version_label ?? undefined,
    sourceUrl: version?.source_url ?? document.source_url ?? undefined,
    artifactStatus: version?.artifact_status,
    parsedAt: version?.parsed_at ?? undefined,
    parserName: version?.parser_name ?? undefined,
    parserVersion: version?.parser_version ?? undefined,
    parseRequiresReview: version?.parse_requires_review,
    extractionMethod: version?.text_extraction_method,
  };
}

const SEARCH_HREF: Record<ApiSearchHit["category"], (ref: string) => string> = {
  documents: (ref) => documentHref(ref),
  transcripts: (ref) => documentHref(ref),
  people: (ref) => `/people/${ref}`,
  organizations: (ref) => `/organizations/${ref}`,
  witnesses: (ref) => `/witnesses/${ref}`,
  exhibits: (ref) => `/exhibits/${encodeURIComponent(ref)}`,
  incidents: (ref) => `/incidents/${ref}`,
  findings: (ref) => `/findings/${ref}`,
  locations: (ref) => `/search?q=${encodeURIComponent(ref)}`,
};

export function toSearchResult(hit: ApiSearchHit): SearchResult {
  const sourceType: Citation["sourceType"] = hit.category === "transcripts" ? "witness" : "court";
  const coordinate = [
    hit.page !== null && hit.page !== undefined ? `p. ${hit.page}` : undefined,
    hit.para_from !== null && hit.para_from !== undefined
      ? `¶${hit.para_from}${hit.para_to && hit.para_to !== hit.para_from ? `–${hit.para_to}` : ""}`
      : undefined,
    hit.line_from !== null && hit.line_from !== undefined
      ? `lines ${hit.line_from}${hit.line_to && hit.line_to !== hit.line_from ? `–${hit.line_to}` : ""}`
      : undefined,
    hit.pdf_page_index !== null && hit.pdf_page_index !== undefined && hit.page == null
      ? `PDF ${hit.pdf_page_index}`
      : undefined,
  ].filter(Boolean);
  const citation =
    (hit.category === "documents" || hit.category === "transcripts") && hit.target_path
      ? {
          sourceType,
          ref: hit.version_ref ?? hit.ref,
          docId: documentRouteId(hit.ref),
          page: hit.page ?? undefined,
          paraFrom: hit.para_from ?? undefined,
          paraTo: hit.para_to ?? undefined,
          lineFrom: hit.line_from ?? undefined,
          lineTo: hit.line_to ?? undefined,
          resolved: true,
          display: [hit.version_ref ?? hit.ref, ...coordinate].join(" · "),
        }
      : undefined;
  return {
    id: hit.category === "documents" ? documentRouteId(hit.ref) : hit.ref,
    category: hit.category,
    title: hit.protected ? hit.ref : hit.title,
    context: hit.protected ? "" : (hit.context ?? ""),
    href: hit.target_path ?? SEARCH_HREF[hit.category](hit.ref),
    citation,
    matchKind: hit.match_kind,
  };
}

/** Deterministic percentage-based ring layout; a real layout engine is a later phase. */
export function toNetworkNode(node: ApiGraphNode, index: number, total: number): NetworkNode {
  const angle = (2 * Math.PI * index) / Math.max(total, 1);
  const type =
    node.entity_kind === "witness" && node.protected ? "protected" : NODE_TYPE[node.entity_kind];
  return {
    id: node.id,
    label: node.protected ? node.ref : node.label,
    type: type ?? "court",
    x: Math.round(50 + 34 * Math.cos(angle)),
    y: Math.round(50 + 34 * Math.sin(angle)),
    ref: node.ref,
    entityKind: node.entity_kind,
  };
}

export function toNetworkEdge(edge: ApiRelationship): NetworkEdge | null {
  const verification = toVerification(edge.verification_state);
  const citation = toCitation(edge.citation);
  if (verification === null || !citation.resolved) return null;
  return {
    id: edge.id,
    from: edge.from_node_id,
    to: edge.to_node_id,
    relation: edge.relationship_type,
    sourceType: edge.source_category ?? citation.sourceType,
    citation,
    verification,
    extractionOrigin: edge.extraction_origin,
    relationshipDate: edge.relationship_date ?? undefined,
    datePrecision: edge.date_precision,
    note: edge.note ?? undefined,
    sourcePath: edge.citation.source_path ?? undefined,
    sourceCoordinate:
      [
        edge.citation.source_document_version_ref,
        edge.citation.source_page ? `p. ${edge.citation.source_page}` : undefined,
        edge.citation.source_para ? `¶${edge.citation.source_para}` : undefined,
      ]
        .filter(Boolean)
        .join(" · ") || undefined,
    ...(edge.provenance
      ? {
          evidenceKind: edge.provenance.kind,
          provenance: toProvenance(edge.provenance, edge.source_category ?? citation.sourceType),
        }
      : {}),
  };
}

export function toTimelineItem(event: ApiEvent): TimelineItem {
  const dateType: DateType = event.date_type;
  const href = event.document_ref
    ? documentHref(event.document_ref)
    : event.incident_slug
      ? `/incidents/${event.incident_slug}`
      : "/timeline";
  return {
    id: event.id,
    label: event.title,
    date: event.date_from ?? NO_DATE,
    dateType,
    href,
    dateTo: event.date_to ?? undefined,
    datePrecision: event.date_precision,
    sourceUrl: event.source_url ?? undefined,
    sourceSystem: event.source_system ?? undefined,
    extractionOrigin: event.extraction_origin,
  };
}

export function toEvidenceRows(claim: ApiClaim): EvidenceRow[] {
  const rows: EvidenceRow[] = [];
  for (const mention of claim.mentions) {
    const direction = DIRECTION[mention.stance];
    const verification = toVerification(mention.verification_state);
    const citation = toCitation(mention.citation);
    if (direction === null || verification === null || !citation.resolved) continue;
    rows.push({
      id: `${claim.claim_key}:${mention.citation.id}`,
      claim: claim.text,
      direction,
      sourceType: citation.sourceType,
      citation,
      verification,
    });
  }
  return rows;
}

/** Legacy placeholder; real Phase 11 answers are mapped from persisted AI runs. */
export const NO_ANSWER: readonly AnswerBlock[] = [];

export function toAiSource(source: ApiAiSource): AiResearchSource {
  return {
    id: source.id,
    rank: source.rank,
    category: source.category,
    ref: source.ref,
    versionRef: source.version_ref ?? undefined,
    display: source.display,
    targetPath: source.target_path,
    excerpt: source.excerpt,
    verification: toVerification(source.verification_state) ?? "unresolved",
    sourceScope: source.metadata?.source_scope ?? undefined,
    underlyingSourceRef: source.metadata?.underlying_source_ref ?? undefined,
  };
}

export function toAiRun(run: ApiAiRun): AiResearchRun {
  const sources = run.sources.map(toAiSource);
  const byId = new Map(sources.map((source) => [source.id, source]));
  return {
    id: run.id,
    question: run.question,
    provider: run.provider,
    model: run.model,
    promptVersion: run.prompt_version,
    status: run.status,
    createdAt: run.created_at,
    answerWithheld: run.answer_withheld,
    insufficientEvidence: run.insufficient_evidence,
    sources,
    blocks: run.blocks.map((block) => ({
      id: block.id,
      sequence: block.sequence,
      kind: block.kind,
      contentType: block.content_type,
      text: block.text,
      verification: toVerification(block.verification_state) ?? "ai-flagged",
      sources: block.sources.flatMap((source) => {
        const mapped = byId.get(source.id);
        return mapped ? [mapped] : [];
      }),
    })),
    citationStatus: {
      produced: run.citation_status.produced,
      resolved: run.citation_status.resolved,
      quotationsMatched: run.citation_status.quotations_matched,
      unresolved: run.citation_status.unresolved,
      humanVerifiedSources: run.citation_status.human_verified_sources,
      unreviewedSources: run.citation_status.unreviewed_sources,
    },
    errors: run.validation_errors.map(({ code, detail }) => ({ code, detail })),
    gaps: run.gaps,
  };
}

export function toAiRunSummary(run: ApiAiRunSummary): AiRunSummaryView {
  return {
    id: run.id,
    question: run.question,
    status: run.status,
    answerWithheld: run.answer_withheld,
    createdAt: run.created_at,
  };
}

/**
 * A persisted deterministic mention. The citation is exact (version + page /
 * paragraph / line where recorded); a mention is court-record presence only,
 * so it is never labelled as testimony.
 */
export function toEntityMention(mention: ApiEntityMention): EntityMention {
  const coordinate = coordinateParts(mention);
  return {
    id: mention.id,
    matchClass: mention.match_class,
    ruleId: mention.rule_id,
    occurrenceText: mention.occurrence_text,
    documentTitle: mention.document_title,
    versionSuperseded: mention.version_superseded,
    href: withExactSource(mention.target_path, mention.occurrence_text),
    citation: {
      sourceType: "court",
      ref: mention.version_ref,
      docId: documentRouteId(mention.document_ref),
      page: mention.page ?? undefined,
      paraFrom: mention.paragraph ?? undefined,
      lineFrom: mention.line_from ?? undefined,
      lineTo: mention.line_to ?? undefined,
      resolved: true,
      display: [mention.version_ref, ...coordinate].join(" · "),
    },
  };
}

function coordinateParts(p: {
  page: number | null;
  paragraph: number | null;
  line_from: number | null;
  line_to: number | null;
  pdf_page_index: number | null;
}): string[] {
  return [
    p.page !== null ? `p. ${p.page}` : undefined,
    p.paragraph !== null ? `¶${p.paragraph}` : undefined,
    p.line_from !== null
      ? `lines ${p.line_from}${p.line_to && p.line_to !== p.line_from ? `–${p.line_to}` : ""}`
      : undefined,
    p.page === null && p.pdf_page_index !== null ? `PDF ${p.pdf_page_index}` : undefined,
  ].filter((part): part is string => part !== undefined);
}

/** `ProvenanceRead` → the screen-facing exact-source view (one shape for every kind). */
export function toProvenance(
  provenance: ApiProvenance,
  sourceType: Citation["sourceType"] = "court",
): ProvenanceView {
  return {
    kind: provenance.kind,
    rule: provenance.rule ?? undefined,
    documentRef: provenance.document_ref,
    documentTitle: provenance.document_title,
    versionRef: provenance.version_ref,
    language: provenance.language ?? undefined,
    pdfPageIndex: provenance.pdf_page_index ?? undefined,
    page: provenance.page ?? undefined,
    paragraph: provenance.paragraph ?? undefined,
    lineFrom: provenance.line_from ?? undefined,
    lineTo: provenance.line_to ?? undefined,
    charStart: provenance.char_start ?? undefined,
    charEnd: provenance.char_end ?? undefined,
    text: provenance.text,
    href: withExactSource(provenance.target_path, provenance.text),
    citation: {
      sourceType,
      ref: provenance.version_ref,
      docId: documentRouteId(provenance.document_ref),
      page: provenance.page ?? undefined,
      paraFrom: provenance.paragraph ?? undefined,
      lineFrom: provenance.line_from ?? undefined,
      lineTo: provenance.line_to ?? undefined,
      resolved: true,
      display: [provenance.version_ref, ...coordinateParts(provenance)].join(" · "),
    },
  };
}

/** A `/network/edges` row. Every edge carries exactly one exact provenance. */
export function toEvidenceEdge(edge: ApiEdge): NetworkEdge | null {
  const verification = toVerification(edge.verification_state);
  if (verification === null) return null;
  const provenance = toProvenance(edge.provenance, edge.source_category);
  return {
    id: edge.id,
    from: edge.from_node_id,
    to: edge.to_node_id,
    relation: edge.relationship_type,
    sourceType: edge.source_category,
    citation: provenance.citation,
    verification,
    extractionOrigin: edge.extraction_origin as NetworkEdge["extractionOrigin"],
    relationshipDate: edge.relationship_date ?? undefined,
    sourcePath: provenance.href,
    sourceCoordinate: provenance.citation.display,
    evidenceKind: edge.provenance.kind,
    evidenceCount: edge.evidence_count,
    provenance,
  };
}

export function toEdgePage(page: ApiEdgePage, query: NetworkQuery): NetworkView {
  const edges = page.items
    .map(toEvidenceEdge)
    .filter((edge): edge is NonNullable<typeof edge> => edge !== null);
  const used = new Set(edges.flatMap((edge) => [edge.from, edge.to]));
  const nodes = page.nodes.filter((node) => used.has(node.id));
  return {
    nodes: nodes.map((node, index) => toNetworkNode(node, index, nodes.length)),
    edges,
    page: {
      total: page.total,
      byType: page.by_type,
      nextCursor: page.next_cursor ?? undefined,
      query,
    },
  };
}

export function toWitnessAppearance(row: ApiWitnessAppearance): WitnessAppearanceView {
  return {
    hearingDate: row.hearing_date,
    sessionLabel: row.session_label ?? undefined,
    transcriptRef: row.transcript_ref ?? undefined,
    versionRef: row.version_ref,
    language: row.language ?? undefined,
    pageFrom: row.page_from ?? undefined,
    pageTo: row.page_to ?? undefined,
    headerPages: row.header_pages,
    openSessionPages: row.open_session_pages,
    privateSessionPages: row.private_session_pages,
    closedSessionPages: row.closed_session_pages,
    examinations: row.examinations.flatMap((exam) =>
      exam.text ? [{ page: exam.page ?? undefined, text: exam.text }] : [],
    ),
    ruleId: row.rule_id,
    provenance: toProvenance(row.provenance, "witness"),
  };
}

export function toExhibitStatusEvent(row: ApiExhibitStatusEvent): ExhibitStatusEventView {
  return {
    identifier: row.exhibit_identifier,
    eventType: row.event_type,
    classification: row.classification ?? undefined,
    statementDate: row.statement_date ?? undefined,
    speaker: row.speaker ?? undefined,
    ruleId: row.rule_id,
    provenance: toProvenance(row.provenance),
  };
}
