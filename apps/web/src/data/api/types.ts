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
}

export interface ApiNetwork {
  nodes: ApiGraphNode[];
  edges: ApiRelationship[];
}

export interface ApiSearchHit {
  category:
    | "documents"
    | "transcripts"
    | "people"
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
}

export interface ApiSearch {
  query: string;
  hits: ApiSearchHit[];
}
