/**
 * API responses shaped like the backend's synthetic `KSC-DEMO-0000` fixture.
 * Test-only; mirrors `apps/api/src/ksc_api/fixtures/demo.py`.
 */

import type {
  ApiCitation,
  ApiClaim,
  ApiDocumentChunk,
  ApiDocumentDetail,
  ApiDocumentSummary,
  ApiEvent,
  ApiEvidencePath,
  ApiExhibit,
  ApiFindingSummary,
  ApiIncident,
  ApiNetwork,
  ApiPage,
  ApiPerson,
  ApiReferenceCounts,
  ApiSearch,
  ApiWitness,
} from "./types";

export const counts: ApiReferenceCounts = {
  relationships: 2,
  document_mentions: 1,
  transcript_mentions: 0,
  exhibit_refs: 0,
  findings: 1,
  witnesses_who_referred: 0,
  incidents: 0,
  citations_resolved: 3,
};

export const resolvedCitation: ApiCitation = {
  id: "c-1",
  source_type: "court",
  ref: "F-DEMO-001",
  doc_id: "KSC-DEMO-0000/F-DEMO-001",
  citation_type: "paragraph",
  raw_text: "F-DEMO-001, para. 12",
  page: 2,
  para_from: 12,
  para_to: 12,
  line_from: null,
  line_to: null,
  resolution_state: "resolved",
  resolved: true,
  display: "F-DEMO-001 · ¶12",
  verification_state: "human_verified",
};

export const transcriptCitation: ApiCitation = {
  ...resolvedCitation,
  id: "c-2",
  source_type: "witness",
  ref: "T-DEMO-001",
  doc_id: "KSC-DEMO-0000/T-DEMO-001",
  citation_type: "transcript_line",
  raw_text: "T. 101, lines 6–12",
  page: 101,
  para_from: null,
  para_to: null,
  line_from: 6,
  line_to: 12,
  display: "T. 101 · lines 6–12",
};

export const unresolvedCitation: ApiCitation = {
  id: "c-9",
  source_type: "court",
  ref: "F-DEMO-999, para. 3",
  doc_id: null,
  citation_type: "paragraph",
  raw_text: "F-DEMO-999, para. 3",
  page: null,
  para_from: null,
  para_to: null,
  line_from: null,
  line_to: null,
  resolution_state: "unresolved",
  resolved: false,
  display: "UNRESOLVED",
  verification_state: "unresolved",
};

export const judgment: ApiDocumentDetail = {
  official_ref: "KSC-DEMO-0000/F-DEMO-001",
  filing_number: "F-DEMO-001",
  title: "Demo judgment (synthetic)",
  document_type: "judgment",
  language: "en",
  filing_party: "court",
  document_date: "2024-01-15",
  filing_date: "2024-01-15",
  public_date: "2024-01-16",
  visibility: "public_redacted",
  counts,
  source_url: "https://example.invalid/demo/F-DEMO-001",
  versions: [
    {
      official_version_ref: "F-DEMO-001/RED",
      version_type: "public_redacted",
      version_label: null,
      visibility: "public_redacted",
      public_date: null,
      source_url: null,
      artifact_status: "fetched",
      sha256: "abc",
      mime_type: "application/pdf",
      page_count: 3,
      fetched_at: null,
      supersedes_version_ref: "F-DEMO-001",
    },
  ],
};

export const notPublicDocument: ApiDocumentDetail = {
  ...judgment,
  official_ref: "KSC-DEMO-0000/F-DEMO-004",
  filing_number: "F-DEMO-004",
  title: "Demo confidential filing (synthetic; not public)",
  document_type: "filing",
  filing_party: "spo",
  visibility: "not_public",
  versions: [],
};

export const chunks: ApiDocumentChunk[] = [
  { sequence: 0, page_from: 1, page_to: 1, para_from: 1, para_to: 9, text: "Intro (synthetic)." },
  {
    sequence: 1,
    page_from: 2,
    page_to: 3,
    para_from: 10,
    para_to: 20,
    text: "Findings (synthetic).",
  },
];

export const person: ApiPerson = {
  slug: "demo-person-a",
  display_name: "Demo Person A",
  public_role: "accused (synthetic)",
  description: null,
  aliases: ["D. Person A"],
  counts,
};

export const protectedWitness: ApiWitness = {
  code: "W-DEMO-001",
  protected: true,
  protective_measures: ["pseudonym"],
  counts,
};

export const publicWitness: ApiWitness = {
  code: "W-DEMO-002",
  protected: false,
  protective_measures: [],
  counts,
  public: { display_name: "Demo Public Witness", called_by: "defence" },
};

export const exhibit: ApiExhibit = {
  official_exhibit_id: "P-DEMO-001",
  title: "Demo exhibit (synthetic document)",
  description: null,
  tendered_by: "spo",
  through_witness_code: "W-DEMO-002",
  admitted_date: "2023-06-01",
  document_date: "2022-11-05",
  document_version_ref: "F-DEMO-002",
  visibility: "public",
  counts,
};

export const incident: ApiIncident = {
  slug: "demo-incident-001",
  title: "Demo incident (synthetic)",
  summary: "As charged — not a determination.",
  location: "Demo Village",
  date_from: "1999-05-01",
  date_to: "1999-05-03",
  date_precision: "range",
  charges_pleaded: null,
  counts,
};

export const finding: ApiFindingSummary = {
  finding_key: "FD-DEMO-001",
  judgment_ref: "KSC-DEMO-0000/F-DEMO-001",
  text: "The Panel finds (demo text).",
  para_from: 12,
  para_to: 14,
  person_slug: "demo-person-a",
  incident_slug: "demo-incident-001",
  charge_ref: "Count 1 (demo)",
  verification_state: "human_verified",
  citation: resolvedCitation,
  counts,
};

export const events: ApiEvent[] = [
  {
    id: "e-1",
    title: "Demo incident date (as alleged)",
    description: null,
    date_type: "event",
    date_from: "1999-05-01",
    date_to: "1999-05-03",
    date_precision: "range",
    incident_slug: "demo-incident-001",
    document_ref: null,
    citation: resolvedCitation,
  },
  {
    id: "e-2",
    title: "Demo judgment delivered",
    description: null,
    date_type: "decision",
    date_from: "2024-01-15",
    date_to: null,
    date_precision: "exact",
    incident_slug: null,
    document_ref: "KSC-DEMO-0000/F-DEMO-001",
    citation: null,
  },
];

export const claim: ApiClaim = {
  claim_key: "CL-DEMO-001",
  text: "Demo claim (synthetic).",
  origin: "human",
  verification_state: "unreviewed",
  source_citation: null,
  mentions: [
    {
      stance: "supports",
      quote_text: null,
      note: null,
      verification_state: "unreviewed",
      citation: transcriptCitation,
    },
    {
      stance: "contradicts",
      quote_text: null,
      note: null,
      verification_state: "unreviewed",
      citation: resolvedCitation,
    },
    {
      stance: "unclear",
      quote_text: null,
      note: null,
      verification_state: "unreviewed",
      citation: resolvedCitation,
    },
    {
      stance: "supports",
      quote_text: null,
      note: null,
      verification_state: "unreviewed",
      citation: unresolvedCitation,
    },
  ],
};

export const network: ApiNetwork = {
  nodes: [
    {
      id: "n-person",
      entity_kind: "person",
      label: "Demo Person A",
      ref: "demo-person-a",
      protected: false,
    },
    {
      id: "n-witness",
      entity_kind: "witness",
      label: "W-DEMO-001",
      ref: "W-DEMO-001",
      protected: true,
    },
    {
      id: "n-hearing",
      entity_kind: "hearing",
      label: "Hearing 2023-06-01",
      ref: "2023-06-01",
      protected: false,
    },
    {
      id: "n-org",
      entity_kind: "organization",
      label: "Demo Unit",
      ref: "demo-unit",
      protected: false,
    },
    {
      id: "n-orphan",
      entity_kind: "location",
      label: "Unlinked",
      ref: "unlinked",
      protected: false,
    },
  ],
  edges: [
    {
      id: "r-1",
      from_node_id: "n-person",
      to_node_id: "n-org",
      relationship_type: "member_of",
      verification_state: "human_verified",
      citation: resolvedCitation,
      note: null,
    },
    {
      id: "r-2",
      from_node_id: "n-witness",
      to_node_id: "n-hearing",
      relationship_type: "testified_at",
      verification_state: "human_verified",
      citation: transcriptCitation,
      note: null,
    },
    {
      id: "r-3",
      from_node_id: "n-person",
      to_node_id: "n-hearing",
      relationship_type: "associated_with",
      verification_state: "unresolved",
      citation: unresolvedCitation,
      note: null,
    },
  ],
};

export const evidencePath: ApiEvidencePath = {
  found: true,
  nodes: network.nodes.slice(0, 2),
  hops: [network.edges[0]!],
};

export const search: ApiSearch = {
  query: "demo",
  hits: [
    {
      category: "documents",
      ref: "KSC-DEMO-0000/F-DEMO-001",
      title: "Demo judgment (synthetic)",
      context: "judgment",
      protected: false,
    },
    {
      category: "witnesses",
      ref: "W-DEMO-001",
      title: "W-DEMO-001",
      context: null,
      protected: true,
    },
    {
      category: "people",
      ref: "demo-person-a",
      title: "Demo Person A",
      context: "accused (synthetic)",
      protected: false,
    },
  ],
};

export function page<T>(items: T[]): ApiPage<T> {
  return { items, total: items.length, limit: 200, offset: 0 };
}

/** Route table for a stubbed fetch. Paths are relative to `/api/v1`. */
export const routes: Record<string, unknown> = {
  "/case": { case_number: "KSC-DEMO-0000" },
  "/documents": page<ApiDocumentSummary>([judgment]),
  "/documents/F-DEMO-001": judgment,
  "/documents/F-DEMO-004": notPublicDocument,
  "/document-versions/F-DEMO-001/RED/chunks": page(chunks),
  "/people": page([person]),
  "/people/demo-person-a": person,
  "/witnesses": page([protectedWitness, publicWitness]),
  "/witnesses/W-DEMO-001": protectedWitness,
  "/witnesses/W-DEMO-002": publicWitness,
  "/exhibits": page([exhibit]),
  "/incidents": page([incident]),
  "/findings": page([finding]),
  "/events": page(events),
  "/claims": page([claim]),
  "/network": network,
  "/network/path": evidencePath,
  "/search": search,
};

export function stubFetch(table: Record<string, unknown> = routes) {
  const calls: string[] = [];
  const fetchImpl = async (input: string): Promise<Response> => {
    const url = new URL(input);
    const path = url.pathname.replace(/^\/api\/v1/, "");
    calls.push(path + url.search);
    const body = table[path];
    if (body === undefined) {
      return new Response(JSON.stringify({ detail: "not found" }), { status: 404 });
    }
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };
  return { fetchImpl, calls };
}
