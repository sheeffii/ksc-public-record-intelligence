/**
 * Phase 20B Reader reads. Every call is scoped to one exact document version
 * and, for research context, one PDF page — the browser never receives a whole
 * document's anchors, the graph or another version's coordinates.
 *
 * Usable on the server (initial deep-link state) and in the browser (page
 * navigation), so it takes an explicit base URL instead of the repository.
 */

import { ApiClient, type FetchLike } from "./api/client";
import type { SourceRegionView } from "./contract";

export type SourcePrecision =
  "exact_geometry" | "ocr_geometry" | "page_and_line" | "page_only" | "text_only" | "unavailable";

/** Overlay data states. SEARCH_MATCH is never a verified research object. */
export type OverlayState =
  "VERIFIED" | "SEARCH_MATCH" | "REVIEW_REQUIRED" | "AMBIGUOUS" | "UNKNOWN" | "UNRESOLVED";

export type OverlayKind =
  "person" | "witness" | "organization" | "exhibit" | "citation" | "relationship" | "finding";

export interface ReaderAnchor {
  id: string;
  precision: SourcePrecision;
  failureReason?: string;
  pdfPageIndex?: number;
  lineFrom?: number;
  lineTo?: number;
  regions: readonly SourceRegionView[];
}

export interface TranscriptPageHeader {
  pdfPageIndex: number;
  pageNumber?: number;
  headerText: string;
  subject: string;
  subjectIsCode: boolean;
  sessionState: string;
  examination?: string;
  rule: string;
}

export interface TranscriptSegmentView {
  id: string;
  sequence: number;
  pdfPageIndex?: number;
  pageNumber?: number;
  lineFrom?: number;
  lineTo?: number;
  speaker?: string;
  witnessCode?: string;
  closedSession: boolean;
  text?: string;
  anchor?: ReaderAnchor;
}

export interface TranscriptSegmentPage {
  items: readonly TranscriptSegmentView[];
  total: number;
  limit: number;
  offset: number;
  filtered: boolean;
}

export interface TranscriptOutline {
  officialVersionRef: string;
  documentRef: string;
  language?: string;
  hearingDate: string;
  sessionLabel?: string;
  hearingType?: string;
  pageFrom?: number;
  pageTo?: number;
  segmentCount: number;
  closedSessionSegments: number;
  precision: Readonly<Record<string, number>>;
  speakers: readonly { label: string; segments: number }[];
  subjects: readonly {
    subject: string;
    subjectIsCode: boolean;
    pages: number;
    firstPdfPageIndex: number;
    firstPageNumber?: number;
  }[];
  examinations: readonly {
    examination: string;
    subject: string;
    subjectIsCode: boolean;
    pages: number;
    firstPdfPageIndex: number;
    firstPageNumber?: number;
  }[];
  pages: readonly TranscriptPageHeader[];
}

export interface EvidenceProvenance {
  kind: string;
  rule?: string;
  versionRef: string;
  pdfPageIndex?: number;
  page?: number;
  lineFrom?: number;
  text: string;
  targetPath: string;
}

export interface PageOverlay {
  anchorId: string;
  objectId: string;
  kind: OverlayKind;
  label: string;
  state: OverlayState;
  protected: boolean;
  precision: SourcePrecision;
  failureReason?: string;
  lineFrom?: number;
  lineTo?: number;
  transcriptSegmentId?: string;
  exactText?: string;
  regions: readonly SourceRegionView[];
  targetPath?: string;
  rule?: string;
  exhibitStatus?: string;
  resolutionState?: string;
  verificationState?: string;
  relationshipType?: string;
  evidenceCount?: number;
  fromLabel?: string;
  toLabel?: string;
  provenance?: EvidenceProvenance;
}

export interface PageContext {
  officialVersionRef: string;
  pdfPageIndex: number;
  pageNumber?: number;
  geometryState: string;
  pageWidth?: number;
  pageHeight?: number;
  pageRotation?: number;
  transcriptHeader?: TranscriptPageHeader;
  overlays: readonly PageOverlay[];
  totals: Readonly<Record<string, number>>;
  truncated: boolean;
}

export interface LocalSearchHit {
  matchType: "SEARCH_MATCH";
  pdfPageIndex?: number;
  pageNumber?: number;
  lineFrom?: number;
  lineTo?: number;
  transcriptSegmentId?: string;
  speaker?: string;
  excerpt: string;
  occurrences: number;
  precision: SourcePrecision;
}

export interface LocalSearchResult {
  query: string;
  items: readonly LocalSearchHit[];
  total: number;
  truncated: boolean;
}

export interface ParsedChunkView {
  number?: number;
  text: string;
  page?: number;
  pageTo?: number;
  pdfPageIndex?: number;
  pdfPageIndexTo?: number;
}

export interface SegmentQuery {
  pdfPageIndex?: number;
  page?: number;
  line?: number;
  segment?: string;
  speaker?: string;
  subject?: string;
  examination?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

/* eslint-disable @typescript-eslint/no-explicit-any -- snake_case wire records */
const opt = <T>(value: T | null | undefined): T | undefined => value ?? undefined;

function region(raw: any): SourceRegionView {
  return {
    x: raw.x,
    y: raw.y,
    width: raw.width,
    height: raw.height,
  };
}

function anchor(raw: any): ReaderAnchor | undefined {
  if (!raw) return undefined;
  return {
    id: raw.id,
    precision: raw.precision,
    failureReason: opt(raw.failure_reason),
    pdfPageIndex: opt(raw.pdf_page_index),
    lineFrom: opt(raw.line_from),
    lineTo: opt(raw.line_to),
    regions: (raw.regions ?? []).map(region),
  };
}

function header(raw: any): TranscriptPageHeader | undefined {
  if (!raw) return undefined;
  return {
    pdfPageIndex: raw.pdf_page_index,
    pageNumber: opt(raw.page_number),
    headerText: raw.header_text,
    subject: raw.subject,
    subjectIsCode: raw.subject_is_code,
    sessionState: raw.session_state,
    examination: opt(raw.examination),
    rule: raw.rule,
  };
}

export function toSegment(raw: any): TranscriptSegmentView {
  return {
    id: raw.id,
    sequence: raw.sequence,
    pdfPageIndex: opt(raw.pdf_page_index),
    pageNumber: opt(raw.page_number),
    lineFrom: opt(raw.line_from),
    lineTo: opt(raw.line_to),
    speaker: opt(raw.speaker),
    witnessCode: opt(raw.witness_code),
    closedSession: raw.closed_session,
    text: opt(raw.text),
    anchor: anchor(raw.anchor),
  };
}

export function toOverlay(raw: any): PageOverlay {
  return {
    anchorId: raw.anchor_id,
    objectId: raw.object_id,
    kind: raw.kind,
    label: raw.label,
    state: raw.state,
    protected: Boolean(raw.protected),
    precision: raw.precision,
    failureReason: opt(raw.failure_reason),
    lineFrom: opt(raw.line_from),
    lineTo: opt(raw.line_to),
    transcriptSegmentId: opt(raw.transcript_segment_id),
    exactText: opt(raw.exact_text),
    regions: (raw.regions ?? []).map(region),
    targetPath: opt(raw.target_path),
    rule: opt(raw.rule),
    exhibitStatus: opt(raw.exhibit_status),
    resolutionState: opt(raw.resolution_state),
    verificationState: opt(raw.verification_state),
    relationshipType: opt(raw.relationship_type),
    evidenceCount: opt(raw.evidence_count),
    fromLabel: opt(raw.from_label),
    toLabel: opt(raw.to_label),
    provenance: raw.provenance
      ? {
          kind: raw.provenance.kind,
          rule: opt(raw.provenance.rule),
          versionRef: raw.provenance.version_ref,
          pdfPageIndex: opt(raw.provenance.pdf_page_index),
          page: opt(raw.provenance.page),
          lineFrom: opt(raw.provenance.line_from),
          text: raw.provenance.text,
          targetPath: raw.provenance.target_path,
        }
      : undefined,
  };
}

export function toPageContext(raw: any): PageContext {
  return {
    officialVersionRef: raw.official_version_ref,
    pdfPageIndex: raw.pdf_page_index,
    pageNumber: opt(raw.page_number),
    geometryState: raw.geometry_state,
    pageWidth: opt(raw.page_width),
    pageHeight: opt(raw.page_height),
    pageRotation: opt(raw.page_rotation),
    transcriptHeader: header(raw.transcript_header),
    overlays: (raw.overlays ?? []).map(toOverlay),
    totals: raw.totals ?? {},
    truncated: Boolean(raw.truncated),
  };
}

function toOutline(raw: any): TranscriptOutline {
  const place = (item: any) => ({
    firstPdfPageIndex: item.first_pdf_page_index,
    firstPageNumber: opt(item.first_page_number),
    pages: item.pages,
    subjectIsCode: item.subject_is_code,
  });
  return {
    officialVersionRef: raw.official_version_ref,
    documentRef: raw.document_ref,
    language: opt(raw.language),
    hearingDate: raw.hearing_date,
    sessionLabel: opt(raw.session_label),
    hearingType: opt(raw.hearing_type),
    pageFrom: opt(raw.page_from),
    pageTo: opt(raw.page_to),
    segmentCount: raw.segment_count,
    closedSessionSegments: raw.closed_session_segments,
    precision: raw.precision ?? {},
    speakers: raw.speakers ?? [],
    subjects: (raw.subjects ?? []).map((item: any) => ({ subject: item.subject, ...place(item) })),
    examinations: (raw.examinations ?? []).map((item: any) => ({
      examination: item.examination,
      subject: item.subject,
      ...place(item),
    })),
    pages: (raw.pages ?? []).map(header),
  };
}
/* eslint-enable @typescript-eslint/no-explicit-any */

const versionPath = (ref: string) => `/document-versions/${ref}`;

export function createReaderClient(baseUrl: string, fetchImpl?: FetchLike) {
  const client = new ApiClient({ baseUrl, fetch: fetchImpl });
  return {
    async outline(versionRef: string): Promise<TranscriptOutline | null> {
      const raw = await client.get<unknown>(`${versionPath(versionRef)}/transcript`);
      return raw ? toOutline(raw) : null;
    },
    async segments(versionRef: string, query: SegmentQuery): Promise<TranscriptSegmentPage | null> {
      const raw = await client.get<{
        items: unknown[];
        total: number;
        limit: number;
        offset: number;
        filtered: boolean;
      }>(`${versionPath(versionRef)}/transcript/segments`, {
        pdf_page_index: query.pdfPageIndex,
        page: query.page,
        line: query.line,
        segment: query.segment,
        speaker: query.speaker,
        subject: query.subject,
        examination: query.examination,
        q: query.q,
        limit: query.limit,
        offset: query.offset,
      });
      return raw ? { ...raw, items: raw.items.map(toSegment) } : null;
    },
    async context(versionRef: string, pdfPageIndex: number): Promise<PageContext | null> {
      const raw = await client.get<unknown>(
        `${versionPath(versionRef)}/pages/${pdfPageIndex}/context`,
      );
      return raw ? toPageContext(raw) : null;
    },
    async search(versionRef: string, q: string): Promise<LocalSearchResult | null> {
      const raw = await client.get<{
        query: string;
        total: number;
        truncated: boolean;
        items: {
          pdf_page_index: number | null;
          page_number: number | null;
          line_from: number | null;
          line_to: number | null;
          transcript_segment_id: string | null;
          speaker: string | null;
          excerpt: string;
          occurrences: number;
          precision: SourcePrecision;
        }[];
      }>(`${versionPath(versionRef)}/source-search`, { q });
      return raw
        ? {
            query: raw.query,
            total: raw.total,
            truncated: raw.truncated,
            items: raw.items.map((item) => ({
              matchType: "SEARCH_MATCH" as const,
              pdfPageIndex: opt(item.pdf_page_index),
              pageNumber: opt(item.page_number),
              lineFrom: opt(item.line_from),
              lineTo: opt(item.line_to),
              transcriptSegmentId: opt(item.transcript_segment_id),
              speaker: opt(item.speaker),
              excerpt: item.excerpt,
              occurrences: item.occurrences,
              precision: item.precision,
            })),
          }
        : null;
    },
    async chunks(versionRef: string, pdfPageIndex: number): Promise<ParsedChunkView[]> {
      const raw = await client.get<{
        items: {
          para_from: number | null;
          text: string;
          page_from: number | null;
          page_to: number | null;
          pdf_page_index_from: number | null;
          pdf_page_index_to: number | null;
        }[];
      }>(`${versionPath(versionRef)}/chunks`, {
        limit: 200,
        offset: 0,
        pdf_page_index: pdfPageIndex,
      });
      return (raw?.items ?? []).map((chunk) => ({
        number: opt(chunk.para_from),
        text: chunk.text,
        page: opt(chunk.page_from),
        pageTo: opt(chunk.page_to),
        pdfPageIndex: opt(chunk.pdf_page_index_from),
        pdfPageIndexTo: opt(chunk.pdf_page_index_to),
      }));
    },
  };
}

export type ReaderClient = ReturnType<typeof createReaderClient>;
