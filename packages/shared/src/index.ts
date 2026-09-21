/**
 * @ksc/shared — contract types shared across the TypeScript side of the monorepo.
 *
 * These mirror the data shapes in docs/design/HANDOFF.md §9. They are the
 * vocabulary of the product; do not extend the unions without a matching
 * design-system entry. No type here has — or may ever gain — a field for a
 * score, rank, rating or weight of any person (DESIGN_DECISIONS.md §2).
 */

/** Deployment constant. The case is never a route segment (ROUTE_MAP.md §1). */
export const CASE_ID = "KSC-BC-2020-06" as const;

// ---------------------------------------------------------------- sources ---

/** Where a piece of information came from. Drives colour, badge and container. */
export const SOURCE_TYPES = [
  "court",
  "witness",
  "spo",
  "defence",
  "exhibit",
  "ai",
  "incident",
  "location",
  "organisation",
] as const;
export type SourceType = (typeof SOURCE_TYPES)[number];

/** Subset of source types that can back a citation. AI never cites itself. */
export const CITABLE_SOURCE_TYPES = ["court", "witness", "spo", "defence", "exhibit"] as const;
export type CitableSourceType = (typeof CITABLE_SOURCE_TYPES)[number];

// ----------------------------------------------------------- verification ---

export const VERIFICATION_STATES = [
  "verified",
  "ai-flagged",
  "unresolved",
  "needs-evidence",
  "unreviewed",
] as const;
export type VerificationState = (typeof VERIFICATION_STATES)[number];

export interface VerificationMeta {
  state: VerificationState;
  reviewedBy?: string[];
  reviewedAt?: string; // ISO 8601
}

// --------------------------------------------------------------- citation ---

/**
 * The universal citation type. `resolved === false` means the chip is NOT
 * rendered and the surrounding content is withheld or marked with a gap.
 */
export interface Citation {
  sourceType: CitableSourceType;
  /** The record's own reference: "P00441", "F02219", "Judgment". */
  ref: string;
  /** Resolves to /documents/:id. */
  docId: string;
  page?: number;
  paraFrom?: number;
  paraTo?: number;
  lineFrom?: number;
  lineTo?: number;
  resolved: boolean;
  /** Pre-formatted canonical string, e.g. "Judgment · ¶8421–8427". */
  display: string;
}

/** Literal shown wherever a citation cannot be resolved. Never replaced. */
export const UNRESOLVED = "UNRESOLVED" as const;

// -------------------------------------------------------------- direction ---

export const DIRECTIONS = ["supports", "contradicts", "qualifies", "neutral"] as const;
export type Direction = (typeof DIRECTIONS)[number];

/** Direction is meaningless without the claim it is measured against. */
export interface EvidenceDirection {
  claimId: string;
  direction: Direction;
  sourceType: CitableSourceType;
  ref: string;
  citation: Citation;
  courtCited: boolean;
  courtCitedPara?: number;
  verification: VerificationMeta;
}

// ---------------------------------------------------------------- witness ---

/**
 * Protection is structural: when `protected` is true the `public` object is
 * omitted from the payload entirely, never null-filled.
 */
export type Witness =
  | {
      code: string;
      protected: true;
      protectiveMeasures: string[];
    }
  | {
      code: string;
      protected: false;
      protectiveMeasures: string[];
      public: {
        displayName: string;
        statedOccupation?: string;
        expertField?: string;
        calledBy: "spo" | "defence";
      };
    };

// ------------------------------------------------------- reference counts ---

/** Counts only. Never a score, weight, rank, centrality or priority. */
export interface ReferenceCounts {
  documentMentions: number;
  transcriptMentions: number;
  exhibitRefs: number;
  findings: number;
  witnessesWhoReferred: number;
  incidents: number;
  citationsResolved: number;
}

// -------------------------------------------------------------- AI answer ---

export const ANSWER_BLOCK_KINDS = [
  "court",
  "evidence",
  "testimony",
  "spo",
  "defence",
  "court_response",
  "human_note",
  "ai",
] as const;
export type AnswerBlockKind = (typeof ANSWER_BLOCK_KINDS)[number];

/** The API returns block order; the client never reorders. */
export interface AnswerBlock {
  kind: AnswerBlockKind;
  text: string;
  citations: Citation[];
}

// -------------------------------------------------------------------- gap ---

export const GAP_KINDS = [
  "closed-session",
  "redaction",
  "untranslated",
  "unresolved-citation",
] as const;
export type GapKind = (typeof GAP_KINDS)[number];

/** Gaps are returned alongside content, never instead of it, and always rendered. */
export interface Gap {
  kind: GapKind;
  ref: string;
  extent: string;
  reason: string;
}

// ------------------------------------------------------------- date types ---

/** Five date types. Never merged (DESIGN_DECISIONS.md §7). */
export const DATE_TYPES = ["event", "document", "filing", "testimony", "decision"] as const;
export type DateType = (typeof DATE_TYPES)[number];

// ----------------------------------------------------------------- locale ---

export const LOCALES = ["en", "sq"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";
