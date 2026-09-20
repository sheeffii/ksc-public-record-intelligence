/**
 * Screen-facing repository contract (ADR-008, extended in Phase 6).
 *
 * The Phase 5 `MockRepository` is synchronous because its data is bundled.
 * A network-backed repository cannot be, so this is the same set of
 * domain-oriented reads with asynchronous results. Both adapters —
 * `createMockRepositoryAdapter()` and `createApiRepository()` — implement it,
 * and `getRepository()` picks one from configuration. Screens keep consuming
 * the same screen-facing types; nothing here changes what a screen renders.
 */

import type { AnswerBlock, Citation, VerificationState, Witness } from "@ksc/shared";
import type {
  MockDirectory,
  MockDirectoryRow,
  MockDocument,
  MockEvidenceRow,
  MockNetworkEdge,
  MockNetworkNode,
  MockPathHop,
  MockPerson,
  MockSearchResult,
  MockTimelineItem,
} from "@/mock/types";

export type DirectoryKind = MockDirectory;
export type DirectoryRow = MockDirectoryRow;
export type PersonDossier = MockPerson;
export type DocumentView = MockDocument;
export type SearchResult = MockSearchResult;
export type NetworkNode = MockNetworkNode;
export type NetworkEdge = MockNetworkEdge;
export type PathHop = MockPathHop;
export type TimelineItem = MockTimelineItem;
export type EvidenceRow = MockEvidenceRow;

export interface NetworkView {
  nodes: readonly NetworkNode[];
  edges: readonly NetworkEdge[];
}

export interface FindingCitationView {
  citation: Citation;
  targetPath?: string;
  sourcePath?: string;
  rawText: string;
  resolutionState: "resolved" | "unresolved" | "ambiguous" | "invalid";
}

export interface FindingEvidenceView {
  linkType: "relies_on" | "supports" | "qualifies" | "contrary" | "context";
  courtCited: boolean;
  courtCitedPara?: number;
  relationshipBasis: "explicit_court_citation" | "related_public_record";
  sourceCategory: string;
  note?: string;
  verification: VerificationState;
  source: FindingCitationView;
}

export interface FindingArgumentView {
  key: string;
  party: "spo" | "defence" | "victims_counsel" | "court" | "other";
  title: string;
  text: string;
  documentRef?: string;
  versionRef?: string;
  paraFrom?: number;
  paraTo?: number;
  sourceScope: "direct_source" | "court_summary" | "source_missing";
  underlyingSourceRef?: string;
  verification: VerificationState;
  source?: FindingCitationView;
}

export interface FindingAuditView {
  citationsTotal: number;
  citationsResolved: number;
  citationsUnresolved: number;
  citationsAmbiguous: number;
  sourcesMissing: number;
  relationshipsUnverified: number;
  publicRedactedSources: number;
  explicitlyCitedByCourt: number;
  relatedNotExplicit: number;
  issues: readonly { code: string; detail: string }[];
}

export interface FindingView {
  key: string;
  text: string;
  paraFrom: number;
  paraTo?: number;
  chargeRef?: string;
  legalElement?: string;
  modeOfLiability?: string;
  verification: VerificationState;
  source?: FindingCitationView;
  adjudicativeRecord: {
    ref: string;
    title: string;
    documentType: string;
    versionRef?: string;
    visibility: string;
    sourceUrl?: string;
    sections: readonly { heading: string; level: number; paraFrom?: number; paraTo?: number }[];
    paragraphs: readonly {
      number: number;
      page?: number;
      pdfPageIndex: number;
      text: string;
    }[];
  };
  evidence: readonly FindingEvidenceView[];
  arguments: readonly FindingArgumentView[];
  courtResponses: readonly {
    kind: string;
    response: FindingArgumentView;
    verification: VerificationState;
    source?: FindingCitationView;
  }[];
  humanNotes: readonly {
    author: string;
    title: string;
    body: string;
    sources: readonly FindingCitationView[];
  }[];
  audit: FindingAuditView;
  corroborationCategories: Readonly<Record<string, number>>;
  corroborationNote: string;
}

export interface ResearchRepository {
  getDirectory(kind: DirectoryKind): Promise<readonly DirectoryRow[]>;
  getPerson(slug: string): Promise<PersonDossier | null>;
  getWitness(code: string): Promise<Witness | null>;
  getDocument(id: string, versionRef?: string): Promise<DocumentView | null>;
  getFinding(key: string): Promise<FindingView | null>;
  search(query: string): Promise<readonly SearchResult[]>;
  getNetwork(): Promise<NetworkView>;
  getPath(fromNodeId?: string, toNodeId?: string, maxHops?: number): Promise<readonly PathHop[]>;
  getTimeline(): Promise<readonly TimelineItem[]>;
  getEvidence(): Promise<readonly EvidenceRow[]>;
  getAnswer(): Promise<readonly AnswerBlock[]>;
}

export const REPOSITORY_METHODS = [
  "getDirectory",
  "getPerson",
  "getWitness",
  "getDocument",
  "getFinding",
  "search",
  "getNetwork",
  "getPath",
  "getTimeline",
  "getEvidence",
  "getAnswer",
] as const satisfies readonly (keyof ResearchRepository)[];
