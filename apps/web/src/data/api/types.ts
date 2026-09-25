/**
 * Wire shapes of the read API (`apps/api/src/ksc_api/schemas`). Field names
 * are the API's snake_case; mapping to screen types happens in `mappers.ts`.
 */

export type ApiVisibility =
  "public" | "public_redacted" | "not_public" | "unknown" | "private_authorized";

export type ApiVerificationState =
  | "unreviewed"
  | "ai_flagged"
  | "human_verified"
  | "human_rejected"
  | "needs_more_evidence"
  | "unresolved";

export type ApiResolutionState = "resolved" | "unresolved" | "ambiguous" | "invalid";
export type ApiParty = "spo" | "defence" | "victims_counsel" | "court" | "other";
export type ApiDateType = "event" | "document" | "filing" | "testimony" | "decision";
export type ApiStance = "supports" | "contradicts" | "qualifies" | "neutral" | "unclear";
export type ApiCourtMediaStatus =
  | "external_only"
  | "mentioned"
  | "tendered"
  | "admitted"
  | "rejected"
  | "discussed"
  | "relied_upon"
  | "unknown";

export interface ApiMediaWorkspace {
  items: {
    id: string;
    title: string;
    publisher: string;
    canonical_url: string;
    published_at: string | null;
    captured_at: string;
    source_type: string;
    language: string;
    court_statuses: ApiCourtMediaStatus[];
    verification_state: ApiVerificationState;
  }[];
  comparisons: {
    id: string;
    comparison_key: string;
    title: string;
    classification: string;
    statement_a: { text: string };
    statement_b: { text: string } | null;
    court_citation_b: ApiCitation | null;
    explanation: string;
    verification_state: ApiVerificationState;
  }[];
  coverage: {
    sources: number;
    items: number;
    statements: number;
    court_links: number;
    citation_backed_court_links: number;
    comparisons: number;
  };
  court_status_taxonomy: ApiCourtMediaStatus[];
  limitations: string[];
}

export interface ApiAiSource {
  id: string;
  rank: number;
  retrieval_method: string;
  retrieval_score: string | number;
  category:
    | "court_finding"
    | "witness_testimony"
    | "spo_argument"
    | "defence_argument"
    | "document_exhibit"
    | "court_response"
    | "human_note";
  visibility: string;
  ref: string;
  version_ref: string | null;
  display: string;
  target_path: string;
  source_url: string | null;
  excerpt: string;
  excerpt_sha256: string;
  page_from: number | null;
  page_to: number | null;
  pdf_page_index: number | null;
  para_from: number | null;
  para_to: number | null;
  line_from: number | null;
  line_to: number | null;
  verification_state: ApiVerificationState;
  verification_reviewed_by: string | null;
  verification_reviewed_at: string | null;
  metadata: Record<string, string | null> | null;
}

export interface ApiAiBlock {
  id: string;
  sequence: number;
  kind:
    "court" | "evidence" | "testimony" | "spo" | "defence" | "court_response" | "human_note" | "ai";
  content_type: "verbatim_quote" | "source_paraphrase" | "ai_analysis" | "abstention";
  text: string;
  verification_state: ApiVerificationState;
  sources: ApiAiSource[];
}

export interface ApiAiRun {
  id: string;
  question: string;
  provider: string;
  model: string;
  prompt_name: string;
  prompt_version: number;
  system_prompt_sha256: string;
  parameters: Record<string, unknown>;
  status: "pending" | "completed" | "failed";
  created_at: string;
  finished_at: string | null;
  answer_withheld: boolean;
  insufficient_evidence: boolean;
  sources: ApiAiSource[];
  blocks: ApiAiBlock[];
  citation_status: {
    produced: number;
    resolved: number;
    quotations_matched: number;
    unresolved: number;
    human_verified_sources: number;
    unreviewed_sources: number;
  };
  validation_errors: { code: string; detail: string; claim_index: number | null }[];
  gaps: string[];
}

export interface ApiAiRunSummary {
  id: string;
  question: string;
  status: "pending" | "completed" | "failed";
  answer_withheld: boolean;
  created_at: string;
}

export interface ApiPage<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiReferenceCounts {
  relationships: number;
  document_mentions: number;
  transcript_mentions: number;
  exhibit_refs: number;
  findings: number;
  witnesses_who_referred: number;
  incidents: number;
  citations_resolved: number;
}

export interface ApiOrganization {
  slug: string;
  name: string;
  kind: string | null;
  name_variants: string[];
  description: string | null;
  counts: ApiReferenceCounts;
}

export interface ApiCitation {
  id: string;
  source_type: "court" | "witness" | "spo" | "defence" | "exhibit";
  ref: string;
  doc_id: string | null;
  citation_type: string;
  raw_text: string;
  page: number | null;
  para_from: number | null;
  para_to: number | null;
  line_from: number | null;
  line_to: number | null;
  pdf_page_index?: number | null;
  target_path?: string | null;
  source_document_version_ref?: string | null;
  source_page?: number | null;
  source_pdf_page_index?: number | null;
  source_para?: number | null;
  source_char_start?: number | null;
  source_char_end?: number | null;
  source_url?: string | null;
  source_path?: string | null;
  resolution_state: ApiResolutionState;
  resolved: boolean;
  display: string;
  verification_state: ApiVerificationState;
}

export type ApiArtifactStatus = "not_fetched" | "fetched" | "failed";

export interface ApiDocumentVersion {
  official_version_ref: string;
  version_type: string;
  version_label: string | null;
  visibility: ApiVisibility;
  public_date: string | null;
  source_url: string | null;
  /** `not_fetched`: official URLs recorded, bytes not held (metadata-only). */
  artifact_status: ApiArtifactStatus;
  sha256: string | null;
  mime_type: string | null;
  page_count: number | null;
  fetched_at: string | null;
  text_extraction_method?: string;
  parsed_at?: string | null;
  parser_name?: string | null;
  parser_version?: string | null;
  parse_requires_review?: boolean;
  supersedes_version_ref: string | null;
}

export interface ApiSourceAnchor {
  id: string;
  official_version_ref: string;
  pdf_page_index: number | null;
  page_number: number | null;
  paragraph_number: number | null;
  line_from: number | null;
  line_to: number | null;
  exact_text: string | null;
  extraction_method: string;
  extractor_version: string;
  processing_run_id: string | null;
  precision:
    "exact_geometry" | "ocr_geometry" | "page_and_line" | "page_only" | "text_only" | "unavailable";
  state: string;
  failure_reason: string | null;
  page_width: number | null;
  page_height: number | null;
  page_rotation: number | null;
  transcript_segment_id?: string | null;
  regions: { x: number; y: number; width: number; height: number; coordinate_space: string }[];
}

export interface ApiDocumentSummary {
  official_ref: string;
  filing_number: string | null;
  title: string;
  document_type: string;
  language: string | null;
  filing_party: ApiParty | null;
  document_date: string | null;
  filing_date: string | null;
  public_date: string | null;
  visibility: ApiVisibility;
  counts: ApiReferenceCounts;
}

export interface ApiDocumentDetail extends ApiDocumentSummary {
  source_url: string | null;
  versions: ApiDocumentVersion[];
}

export interface ApiDocumentChunk {
  sequence: number;
  chunk_kind?: string;
  pdf_page_index_from?: number | null;
  pdf_page_index_to?: number | null;
  page_from: number | null;
  page_to: number | null;
  para_from: number | null;
  para_to: number | null;
  text: string;
}

export interface ApiPerson {
  slug: string;
  display_name: string;
  public_role: string | null;
  description: string | null;
  aliases: string[];
  counts: ApiReferenceCounts;
}

/** `public` is absent — never null-filled — when the witness is protected. */
export interface ApiWitness {
  code: string;
  protected: boolean;
  protective_measures: string[];
  counts: ApiReferenceCounts;
  public?: { display_name: string; called_by: ApiParty | null };
}

export interface ApiExhibit {
  official_exhibit_id: string;
  title: string;
  description: string | null;
  status: string;
  tendered_by: ApiParty | null;
  through_witness_code: string | null;
  admitted_date: string | null;
  document_date: string | null;
  document_version_ref: string | null;
  visibility: ApiVisibility;
  counts: ApiReferenceCounts;
}

export interface ApiIncident {
  slug: string;
  title: string;
  summary: string | null;
  location: string | null;
  date_from: string | null;
  date_to: string | null;
  date_precision: string;
  charges_pleaded: Record<string, unknown>[] | null;
  counts: ApiReferenceCounts;
}

export interface ApiFindingSummary {
  finding_key: string;
  judgment_ref: string;
  text: string;
  para_from: number;
  para_to: number | null;
  person_slug: string | null;
  incident_slug: string | null;
  charge_ref: string | null;
  verification_state: ApiVerificationState;
  citation: ApiCitation | null;
  counts: ApiReferenceCounts;
}

export type ApiFindingLinkType = "relies_on" | "supports" | "qualifies" | "contrary" | "context";

export interface ApiFindingEvidenceLink {
  link_type: ApiFindingLinkType;
  court_cited: boolean;
  court_cited_para: number | null;
  relationship_basis: "explicit_court_citation" | "related_public_record";
  source_category: string;
  note: string | null;
  verification_state: ApiVerificationState;
  citation: ApiCitation;
}

export interface ApiArgument {
  argument_key: string;
  party: ApiParty;
  title: string;
  text: string;
  document_ref: string | null;
  document_version_ref: string | null;
  para_from: number | null;
  para_to: number | null;
  source_scope: "direct_source" | "court_summary" | "source_missing";
  underlying_source_ref: string | null;
  verification_state: ApiVerificationState;
  citation: ApiCitation | null;
}

export interface ApiArgumentResponse {
  response_kind: string;
  argument: ApiArgument;
  verification_state: ApiVerificationState;
  citation: ApiCitation | null;
}

export interface ApiFindingDetail extends ApiFindingSummary {
  legal_element: string | null;
  mode_of_liability: string | null;
  evidence_links: ApiFindingEvidenceLink[];
  arguments: ApiArgument[];
  court_responses: ApiArgumentResponse[];
  judgment: {
    document_ref: string;
    document_title: string;
    document_type: string;
    version_ref: string | null;
    visibility: ApiVisibility;
    source_url: string | null;
    sections: {
      heading: string;
      level: number;
      para_from: number | null;
      para_to: number | null;
    }[];
    paragraphs: {
      paragraph_number: number;
      page_from: number | null;
      pdf_page_index_from: number;
      text: string;
    }[];
  };
  human_notes: {
    author: string;
    title: string;
    body: string;
    provenance: "human";
    citations: ApiCitation[];
  }[];
  source_audit: {
    citations_total: number;
    citations_resolved: number;
    citations_unresolved: number;
    citations_ambiguous: number;
    citations_invalid: number;
    sources_missing: number;
    ambiguous_versions: number;
    transcript_coordinates_missing: number;
    relationships_unverified: number;
    public_redacted_sources: number;
    explicitly_cited_by_court: number;
    related_not_explicit: number;
    issues: { code: string; detail: string }[];
  };
  corroboration_categories: Record<string, number>;
  corroboration_note: string;
}

export interface ApiEvent {
  id: string;
  title: string;
  description: string | null;
  date_type: ApiDateType;
  date_from: string | null;
  date_to: string | null;
  date_precision: string;
  incident_slug: string | null;
  document_ref: string | null;
  citation: ApiCitation | null;
  hearing_ref?: string | null;
  source_system?: string | null;
  source_url?: string | null;
  extraction_origin?: string;
}

export interface ApiClaimMention {
  stance: ApiStance;
  quote_text: string | null;
  note: string | null;
  verification_state: ApiVerificationState;
  citation: ApiCitation;
}

export interface ApiClaim {
  claim_key: string;
  text: string;
  origin: "source_extracted" | "human" | "ai_extracted";
  verification_state: ApiVerificationState;
  source_citation: ApiCitation | null;
  mentions: ApiClaimMention[];
}

export interface ApiGraphNode {
  id: string;
  entity_kind: string;
  label: string;
  ref: string;
  protected: boolean;
}

export interface ApiRelationship {
  id: string;
  from_node_id: string;
  to_node_id: string;
  relationship_type: string;
  verification_state: ApiVerificationState;
  citation: ApiCitation;
  note: string | null;
  source_category?: "court" | "witness" | "spo" | "defence" | "exhibit";
  extraction_origin?: "source_documented" | "deterministic_citation" | "analytical";
  relationship_date?: string | null;
  date_precision?: string;
  /** Present on Evidence Path hops (the shared `ProvenanceRead` contract). */
  provenance?: ApiProvenance | null;
}

export interface ApiNetwork {
  nodes: ApiGraphNode[];
  edges: ApiRelationship[];
}

export type ApiEvidenceKind =
  "citation" | "entity_occurrence" | "witness_appearance" | "exhibit_status_event";

/** `ProvenanceRead`: one exact-source answer to "why does this exist?". */
export interface ApiProvenance {
  kind: ApiEvidenceKind;
  rule: string | null;
  document_ref: string;
  document_title: string;
  version_ref: string;
  language: string | null;
  pdf_page_index: number | null;
  page: number | null;
  paragraph: number | null;
  line_from: number | null;
  line_to: number | null;
  char_anchor: string | null;
  char_start: number | null;
  char_end: number | null;
  text: string;
  source_url: string | null;
  target_path: string;
}

export interface ApiEdge {
  id: string;
  from_node_id: string;
  to_node_id: string;
  relationship_type: string;
  extraction_origin: string;
  verification_state: ApiVerificationState;
  source_category: "court" | "witness" | "spo" | "defence" | "exhibit";
  relationship_date: string | null;
  evidence_count: number;
  provenance: ApiProvenance;
}

export interface ApiEdgePage {
  items: ApiEdge[];
  nodes: ApiGraphNode[];
  total: number;
  by_type: Record<string, number>;
  next_cursor: string | null;
}

export interface ApiWitnessAppearance {
  hearing_date: string;
  session_label: string | null;
  transcript_ref: string | null;
  version_ref: string;
  language: string | null;
  page_from: number | null;
  page_to: number | null;
  header_pages: number;
  open_session_pages: number;
  private_session_pages: number;
  closed_session_pages: number;
  examinations: { page?: number | null; text?: string }[];
  rule_id: string;
  provenance: ApiProvenance;
}

export interface ApiExhibitStatusEvent {
  exhibit_identifier: string;
  event_type:
    "number_assigned" | "admitted" | "rejected" | "marked_for_identification" | "withdrawn";
  classification: string | null;
  statement_date: string | null;
  speaker: string | null;
  rule_id: string;
  provenance: ApiProvenance;
}

export interface ApiEvidencePath {
  found: boolean;
  nodes: ApiGraphNode[];
  hops: ApiRelationship[];
}

export interface ApiSearchHit {
  category:
    | "documents"
    | "transcripts"
    | "people"
    | "organizations"
    | "witnesses"
    | "exhibits"
    | "incidents"
    | "findings"
    | "locations";
  ref: string;
  title: string;
  context: string | null;
  protected: boolean;
  match_kind?: "exact_identifier" | "title" | "phrase" | "keyword";
  version_ref?: string | null;
  pdf_page_index?: number | null;
  page?: number | null;
  para_from?: number | null;
  para_to?: number | null;
  line_from?: number | null;
  line_to?: number | null;
  source_url?: string | null;
  target_path?: string | null;
  match_class?: "SEARCH_MATCH";
}

/** A persisted Phase 19A deterministic mention (`/{kind}/{key}/mentions`). */
export interface ApiEntityMention {
  id: string;
  entity_kind: "person" | "witness" | "organization" | "exhibit";
  match_class: "VERIFIED_MENTION" | "REVIEW_REQUIRED";
  rule_id: string;
  rule_version: number;
  occurrence_text: string;
  document_ref: string;
  document_title: string;
  version_ref: string;
  version_superseded: boolean;
  language: string | null;
  char_anchor: "transcript_segment_text" | "transcript_speaker_label" | "document_page_text";
  char_start: number;
  char_end: number;
  pdf_page_index: number | null;
  page: number | null;
  paragraph: number | null;
  line_from: number | null;
  line_to: number | null;
  source_url: string | null;
  target_path: string;
}

export interface ApiSearch {
  query: string;
  hits: ApiSearchHit[];
}

export interface ApiAppealIssueSummary {
  id: string;
  issue_key: string;
  category: string;
  context: string;
  title: string;
  description: string;
  finding_key: string;
  para_from: number;
  para_to: number | null;
  court_treatment: string;
  court_treatment_note: string;
  red_team_result: string;
  verification_state: ApiVerificationState;
}

export interface ApiStatementComparison {
  id: string;
  comparison_key: string;
  issue_key: string | null;
  title: string;
  comparison_type: string;
  classification: string;
  statement_a_excerpt: string;
  statement_b_excerpt: string;
  statement_a_speaker: string | null;
  statement_b_speaker: string | null;
  statement_a_citation: ApiCitation;
  statement_b_citation: ApiCitation;
  explanation: string;
  verification_state: ApiVerificationState;
}

export interface ApiRedTeamFinding {
  sequence: number;
  perspective: string;
  category: string;
  text: string;
  verification_state: ApiVerificationState;
  citation: ApiCitation | null;
}

export interface ApiAppealIssue extends ApiAppealIssueSummary {
  notes: string | null;
  sources: {
    id: string;
    sequence: number;
    role: string;
    source_category: string;
    excerpt: string;
    note: string | null;
    verification_state: ApiVerificationState;
    citation: ApiCitation;
  }[];
  missing_material: { reference: string; kind: string; reason: string; state: string }[];
  statement_comparisons: ApiStatementComparison[];
  red_team_reviews: {
    result: string;
    summary: string;
    origin: string;
    verification_state: ApiVerificationState;
    findings: ApiRedTeamFinding[];
  }[];
  citation_audit: {
    citations_total: number;
    citations_resolved: number;
    quotes_verified: number;
    sources_human_verified: number;
    unresolved: number;
    unsupported_relationships: number;
    ready_for_human_review: boolean;
    issues: string[];
  };
}

export interface ApiAppealWorkspace {
  issues: ApiAppealIssueSummary[];
  coverage: {
    issues: number;
    source_backed_links: number;
    statement_comparisons: number;
    red_team_reviews: number;
    citations_resolved: number;
    citations_unresolved: number;
    human_verified_relationships: number;
    needs_more_evidence: number;
  };
  corpus_limitations: string[];
}

export interface ApiArgumentLab {
  issue: ApiAppealIssueSummary;
  draft_title: string;
  draft_text: string;
  draft_citations: ApiCitation[];
  unsupported_sentences: string[];
  stages: ApiRedTeamFinding[];
  result: string;
  notice: string;
}
