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
  EvidenceRow,
  NetworkEdge,
  NetworkNode,
  PersonDossier,
  SearchResult,
  TimelineItem,
} from "../contract";
import type {
  ApiCitation,
  ApiClaim,
  ApiDocumentChunk,
  ApiDocumentDetail,
  ApiDocumentSummary,
  ApiDocumentVersion,
  ApiEvent,
  ApiExhibit,
  ApiFindingSummary,
  ApiGraphNode,
  ApiIncident,
  ApiParty,
  ApiPerson,
  ApiReferenceCounts,
  ApiRelationship,
  ApiSearchHit,
  ApiStance,
  ApiVerificationState,
  ApiWitness,
} from "./types";

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
    description: document.document_type,
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
  };
}

export function exhibitRow(exhibit: ApiExhibit): DirectoryRow {
  return {
    id: exhibit.official_exhibit_id,
    title: exhibit.title,
    kind: "exhibits",
    description: exhibit.official_exhibit_id,
    date: exhibit.admitted_date ?? exhibit.document_date ?? NO_DATE,
    references: references(exhibit.counts),
    verification: "unreviewed",
    href: exhibit.document_version_ref
      ? `/documents/${documentRouteId(exhibit.document_version_ref)}`
      : "/exhibits",
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

export function findingRow(finding: ApiFindingSummary): DirectoryRow | null {
  const verification = toVerification(finding.verification_state);
  if (verification === null) return null;
  return {
    id: finding.finding_key,
    title: finding.finding_key,
    kind: "findings",
    description: finding.text,
    date: NO_DATE,
    references: references(finding.counts),
    verification,
    href: `/findings/${finding.finding_key}`,
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
    page: chunks[0]?.page_from ?? 1,
    paragraphs: isPublic
      ? chunks.map((chunk, index) => ({
          number: chunk.para_from ?? index + 1,
          text: chunk.text,
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
    sourceUrl: version?.source_url ?? document.source_url ?? undefined,
  };
}

const SEARCH_HREF: Record<ApiSearchHit["category"], (ref: string) => string> = {
  documents: (ref) => documentHref(ref),
  transcripts: (ref) => documentHref(ref),
  people: (ref) => `/people/${ref}`,
  witnesses: (ref) => `/witnesses/${ref}`,
  exhibits: (ref) => `/exhibits?q=${encodeURIComponent(ref)}`,
  incidents: (ref) => `/incidents/${ref}`,
  findings: (ref) => `/findings/${ref}`,
  locations: (ref) => `/search?q=${encodeURIComponent(ref)}`,
};

export function toSearchResult(hit: ApiSearchHit): SearchResult {
  return {
    id: hit.category === "documents" ? documentRouteId(hit.ref) : hit.ref,
    category: hit.category,
    title: hit.protected ? hit.ref : hit.title,
    context: hit.protected ? "" : (hit.context ?? ""),
    href: hit.target_path ?? SEARCH_HREF[hit.category](hit.ref),
  };
}

/** Deterministic ring layout; a real layout engine is a later phase. */
export function toNetworkNode(node: ApiGraphNode, index: number, total: number): NetworkNode {
  const angle = (2 * Math.PI * index) / Math.max(total, 1);
  const type =
    node.entity_kind === "witness" && node.protected ? "protected" : NODE_TYPE[node.entity_kind];
  return {
    id: node.id,
    label: node.protected ? node.ref : node.label,
    type: type ?? "court",
    x: Math.round(400 + 300 * Math.cos(angle)),
    y: Math.round(300 + 220 * Math.sin(angle)),
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

/** No AI run exists in Phase 6; the answer surface stays empty, never invented. */
export const NO_ANSWER: readonly AnswerBlock[] = [];
