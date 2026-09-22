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

import type {
  AnswerBlock,
  Citation,
  ReferenceCounts,
  VerificationState,
  Witness,
} from "@ksc/shared";
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

export interface IncidentView {
  slug: string;
  title: string;
  summary?: string;
  location?: string;
  dateFrom?: string;
  dateTo?: string;
  datePrecision: string;
  charges: readonly Record<string, unknown>[];
  counts: ReferenceCounts;
}

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

export type AiSourceCategory =
  | "court_finding"
  | "witness_testimony"
  | "spo_argument"
  | "defence_argument"
  | "document_exhibit"
  | "court_response"
  | "human_note";

export interface AiResearchSource {
  id: string;
  rank: number;
  category: AiSourceCategory;
  ref: string;
  versionRef?: string;
  display: string;
  targetPath: string;
  excerpt: string;
  verification: VerificationState;
  sourceScope?: string;
  underlyingSourceRef?: string;
}

export interface AiResearchBlock {
  id: string;
  sequence: number;
  kind: AnswerBlock["kind"];
  contentType: "verbatim_quote" | "source_paraphrase" | "ai_analysis" | "abstention";
  text: string;
  verification: VerificationState;
  sources: readonly AiResearchSource[];
}

export interface AiResearchRun {
  id: string;
  question: string;
  provider: string;
  model: string;
  promptVersion: number;
  status: "pending" | "completed" | "failed";
  createdAt: string;
  answerWithheld: boolean;
  insufficientEvidence: boolean;
  sources: readonly AiResearchSource[];
  blocks: readonly AiResearchBlock[];
  citationStatus: {
    produced: number;
    resolved: number;
    quotationsMatched: number;
    unresolved: number;
    humanVerifiedSources: number;
    unreviewedSources: number;
  };
  errors: readonly { code: string; detail: string }[];
  gaps: readonly string[];
}

export interface AiRunSummaryView {
  id: string;
  question: string;
  status: "pending" | "completed" | "failed";
  answerWithheld: boolean;
  createdAt: string;
}

export interface AppealIssueSummaryView {
  id: string;
  key: string;
  category: string;
  context: string;
  title: string;
  description: string;
  findingKey: string;
  paraFrom: number;
  paraTo?: number;
  courtTreatment: string;
  courtTreatmentNote: string;
  redTeamResult: string;
  verification: VerificationState;
}

export interface StatementComparisonView {
  id: string;
  key: string;
  issueKey?: string;
  title: string;
  type: string;
  classification: string;
  statementA: { excerpt: string; speaker?: string; source: FindingCitationView };
  statementB: { excerpt: string; speaker?: string; source: FindingCitationView };
  explanation: string;
  verification: VerificationState;
}

export interface AppealIssueView extends AppealIssueSummaryView {
  notes?: string;
  sources: readonly {
    id: string;
    sequence: number;
    role: string;
    category: string;
    excerpt: string;
    note?: string;
    verification: VerificationState;
    source: FindingCitationView;
  }[];
  missingMaterial: readonly { reference: string; kind: string; reason: string; state: string }[];
  comparisons: readonly StatementComparisonView[];
  redTeam: readonly {
    result: string;
    summary: string;
    origin: string;
    verification: VerificationState;
    findings: readonly {
      sequence: number;
      perspective: string;
      category: string;
      text: string;
      verification: VerificationState;
      source?: FindingCitationView;
    }[];
  }[];
  audit: {
    citationsTotal: number;
    citationsResolved: number;
    quotesVerified: number;
    sourcesHumanVerified: number;
    unresolved: number;
    unsupportedRelationships: number;
    readyForHumanReview: boolean;
    issues: readonly string[];
  };
}

export interface AppealWorkspaceView {
  issues: readonly AppealIssueSummaryView[];
  coverage: {
    issues: number;
    sourceBackedLinks: number;
    comparisons: number;
    redTeamReviews: number;
    citationsResolved: number;
    citationsUnresolved: number;
    humanVerifiedRelationships: number;
    needsMoreEvidence: number;
  };
  limitations: readonly string[];
}

export type CourtMediaStatus =
  | "external_only"
  | "mentioned"
  | "tendered"
  | "admitted"
  | "rejected"
  | "discussed"
  | "relied_upon"
  | "unknown";

export interface MediaWorkspaceView {
  items: readonly {
    id: string;
    title: string;
    publisher: string;
    canonicalUrl: string;
    publishedAt?: string;
    capturedAt: string;
    sourceType: string;
    language: string;
    courtStatuses: readonly CourtMediaStatus[];
    verification: VerificationState;
  }[];
  comparisons: readonly {
    id: string;
    key: string;
    title: string;
    classification: string;
    statementA: string;
    statementB?: string;
    explanation: string;
    verification: VerificationState;
  }[];
  coverage: {
    sources: number;
    items: number;
    statements: number;
    courtLinks: number;
    citationBackedCourtLinks: number;
    comparisons: number;
  };
  taxonomy: readonly CourtMediaStatus[];
  limitations: readonly string[];
}

export interface ArgumentLabView {
  issue: AppealIssueSummaryView;
  title: string;
  draft: string;
  citations: readonly FindingCitationView[];
  unsupportedSentences: readonly string[];
  stages: readonly {
    sequence: number;
    perspective: string;
    category: string;
    text: string;
    verification: VerificationState;
    source?: FindingCitationView;
  }[];
  result: string;
  notice: string;
}

export interface ResearchRepository {
  getDirectory(kind: DirectoryKind): Promise<readonly DirectoryRow[]>;
  getPerson(slug: string): Promise<PersonDossier | null>;
  getWitness(code: string): Promise<Witness | null>;
  getIncident(slug: string): Promise<IncidentView | null>;
  getDocument(
    id: string,
    versionRef?: string,
    page?: number,
    pdfPageIndex?: number,
  ): Promise<DocumentView | null>;
  getFinding(key: string): Promise<FindingView | null>;
  search(query: string): Promise<readonly SearchResult[]>;
  getNetwork(): Promise<NetworkView>;
  getPath(fromNodeId?: string, toNodeId?: string, maxHops?: number): Promise<readonly PathHop[]>;
  getTimeline(): Promise<readonly TimelineItem[]>;
  getEvidence(): Promise<readonly EvidenceRow[]>;
  getAnswer(): Promise<readonly AnswerBlock[]>;
  createAiRun(question: string): Promise<AiResearchRun>;
  getAiRun(id: string): Promise<AiResearchRun | null>;
  listAiRuns(): Promise<readonly AiRunSummaryView[]>;
  saveAiRunAsNote(id: string, title: string): Promise<{ id: string; provenance: string }>;
  listAppealIssues(): Promise<AppealWorkspaceView>;
  getAppealIssue(key: string): Promise<AppealIssueView | null>;
  getArgumentLab(key: string): Promise<ArgumentLabView | null>;
  listStatementComparisons(issueKey?: string): Promise<readonly StatementComparisonView[]>;
  getMediaWorkspace(query?: string, courtStatus?: CourtMediaStatus): Promise<MediaWorkspaceView>;
}

export const REPOSITORY_METHODS = [
  "getDirectory",
  "getPerson",
  "getWitness",
  "getIncident",
  "getDocument",
  "getFinding",
  "search",
  "getNetwork",
  "getPath",
  "getTimeline",
  "getEvidence",
  "getAnswer",
  "createAiRun",
  "getAiRun",
  "listAiRuns",
  "saveAiRunAsNote",
  "listAppealIssues",
  "getAppealIssue",
  "getArgumentLab",
  "listStatementComparisons",
  "getMediaWorkspace",
] as const satisfies readonly (keyof ResearchRepository)[];
