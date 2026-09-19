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

import type { AnswerBlock, Witness } from "@ksc/shared";
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

export interface ResearchRepository {
  getDirectory(kind: DirectoryKind): Promise<readonly DirectoryRow[]>;
  getPerson(slug: string): Promise<PersonDossier | null>;
  getWitness(code: string): Promise<Witness | null>;
  getDocument(id: string): Promise<DocumentView | null>;
  search(query: string): Promise<readonly SearchResult[]>;
  getNetwork(): Promise<NetworkView>;
  getPath(): Promise<readonly PathHop[]>;
  getTimeline(): Promise<readonly TimelineItem[]>;
  getEvidence(): Promise<readonly EvidenceRow[]>;
  getAnswer(): Promise<readonly AnswerBlock[]>;
}

export const REPOSITORY_METHODS = [
  "getDirectory",
  "getPerson",
  "getWitness",
  "getDocument",
  "search",
  "getNetwork",
  "getPath",
  "getTimeline",
  "getEvidence",
  "getAnswer",
] as const satisfies readonly (keyof ResearchRepository)[];
