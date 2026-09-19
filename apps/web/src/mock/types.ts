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
}

export interface MockPerson {
  slug: string;
  displayName: string;
  role: string;
  aliases: string[];
  counts: ReferenceCounts;
}

export interface MockDocument {
  id: string;
  title: string;
  type: string;
  language: string;
  page: number;
  paragraphs: { number: number; text: string }[];
  citation: Citation;
}

export interface MockSearchResult {
  id: string;
  category: MockDirectory | "locations";
  title: string;
  context: string;
  href: string;
  citation?: Citation;
}

export interface MockNetworkNode {
  id: string;
  label: string;
  type: SourceType | "person" | "protected";
  x: number;
  y: number;
}

export interface MockNetworkEdge {
  id: string;
  from: string;
  to: string;
  relation: string;
  sourceType: Exclude<SourceType, "ai">;
  citation: Citation;
  verification: VerificationState;
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
