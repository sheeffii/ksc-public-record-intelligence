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

export type MockDirectory =
  "people" | "witnesses" | "documents" | "findings" | "exhibits" | "incidents";

export interface MockDirectoryRow {
  id: string;
  title: string;
  kind: MockDirectory;
  description: string;
  date: string;
  references: number;
  verification: VerificationState;
  href: string;
  protected?: boolean;
  status?: string;
  party?: string;
  relatedWitness?: string;
  counts?: ReferenceCounts;
  relationshipCount?: number;
}

export interface MockPerson {
  slug: string;
  displayName: string;
  role: string;
  aliases: string[];
  counts: ReferenceCounts;
  relationshipCount?: number;
}

export interface MockDocument {
  id: string;
  title: string;
  type: string;
  language: string;
  page: number;
  coordinateKind?: "source" | "pdf";
  paragraphs: {
    number?: number;
    text: string;
    page?: number;
    pageTo?: number;
    pdfPageIndex?: number;
    pdfPageIndexTo?: number;
  }[];
  citation: Citation;
  /**
   * Set by the API repository. `not_public` means the record exists in the
   * public docket but its text is not public (ROUTE_MAP.md §8); paragraphs are
   * then empty. Absent for bundled mock data, which is always public.
   */
  visibility?: "public" | "public_redacted" | "not_public";
  pageCount?: number;
  documentDate?: string;
  filingDate?: string;
  versionRef?: string;
  versionType?: string;
  versionLabel?: string;
  sourceUrl?: string;
  artifactStatus?: "not_fetched" | "fetched" | "failed";
  parsedAt?: string;
  parserName?: string;
  parserVersion?: string;
  parseRequiresReview?: boolean;
  extractionMethod?: string;
  artifactUrl?: string;
  /** Held versions of the same document; coordinates never cross between them. */
  versions?: { ref: string; type?: string; label?: string; fetched: boolean }[];
}

export interface MockSearchResult {
  id: string;
  category: MockDirectory | "locations" | "transcripts" | "organizations" | "external";
  title: string;
  context: string;
  href: string;
  citation?: Citation;
  matchKind?: "exact_identifier" | "title" | "phrase" | "keyword";
}

export interface MockNetworkNode {
  id: string;
  label: string;
  type: SourceType | "person" | "protected";
  x: number;
  y: number;
  ref?: string;
  entityKind?: string;
}

export interface MockNetworkEdge {
  id: string;
  from: string;
  to: string;
  relation: string;
  sourceType: Exclude<SourceType, "ai">;
  citation: Citation;
  verification: VerificationState;
  extractionOrigin?:
    "source_documented" | "deterministic_citation" | "deterministic_occurrence" | "analytical";
  relationshipDate?: string;
  datePrecision?: string;
  note?: string;
  sourcePath?: string;
  sourceCoordinate?: string;
}

export interface MockPathHop extends MockNetworkEdge {
  index: number;
  date: string;
  dateType: DateType;
}

export interface MockTimelineItem {
  id: string;
  label: string;
  date: string;
  dateType: DateType;
  href: string;
  dateTo?: string;
  datePrecision?: string;
  sourceUrl?: string;
  sourceSystem?: string;
  extractionOrigin?: string;
}

export interface MockEvidenceRow {
  id: string;
  claim: string;
  direction: Direction;
  sourceType: Exclude<SourceType, "ai">;
  citation: Citation;
  verification: VerificationState;
}

export interface MockRepository {
  getDirectory(kind: MockDirectory): readonly MockDirectoryRow[];
  getPerson(slug: string): MockPerson;
  getWitness(code: string): Witness;
  getDocument(id: string): MockDocument;
  search(query: string): readonly MockSearchResult[];
  getNetwork(): { nodes: readonly MockNetworkNode[]; edges: readonly MockNetworkEdge[] };
  getPath(): readonly MockPathHop[];
  getTimeline(): readonly MockTimelineItem[];
  getEvidence(): readonly MockEvidenceRow[];
  getAnswer(): readonly AnswerBlock[];
}
