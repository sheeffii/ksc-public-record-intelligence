"use client";

/**
 * Phase 20B source-native Reader.
 *
 *   SOURCE           the exact stored official PDF (always primary)
 *   STRUCTURED TEXT  verbatim parsed transcript segments / paragraphs
 *   RESEARCH CONTEXT source-anchored objects on the current PDF page
 *
 * Every read is scoped to one exact version and one PDF page. A PDF rectangle
 * is drawn only from persisted, validated regions of that version/page; every
 * weaker precision is stated, never visually upgraded.
 */

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Panel } from "@/components/primitives/Panel";
import { EmptyState, GapNotice } from "@/components/primitives/States";
import { CitationChip, SourceBadge } from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { KeyValue, Segmented, ToolButton, Toolbar } from "@/components/screens/phase5/Workspace";
import {
  OriginalPdfPage,
  type PdfFit,
  type PdfHighlight,
} from "@/components/source/OriginalPdfPage";
import type { DocumentView, SourceAnchorView } from "@/data";
import {
  createReaderClient,
  type LocalSearchResult,
  type OverlayKind,
  type PageContext,
  type PageOverlay,
  type ParsedChunkView,
  type SourcePrecision,
  type TranscriptOutline,
  type TranscriptSegmentPage,
  type TranscriptSegmentView,
} from "@/data/reader";
import { exactSourcePattern, splitExactSource } from "@/lib/exact-source";

type Pane = "source" | "text" | "context";
type ContextTab = "summary" | "mentions" | "people" | "exhibits" | "findings" | "citations";

const CONTEXT_TABS: readonly ContextTab[] = [
  "summary",
  "mentions",
  "people",
  "exhibits",
  "findings",
  "citations",
];
const TAB_KINDS: Record<ContextTab, readonly OverlayKind[]> = {
  summary: ["relationship", "finding"],
  mentions: ["person", "witness", "organization", "exhibit"],
  people: ["person", "witness"],
  exhibits: ["exhibit"],
  findings: ["finding"],
  citations: ["citation"],
};
const EXACT: readonly SourcePrecision[] = ["exact_geometry", "ocr_geometry"];

/** What the PDF currently highlights, and why. */
interface ActiveSource {
  key: string;
  kind: OverlayKind | "segment" | "anchor";
  label: string;
  pdfPageIndex?: number;
  precision: SourcePrecision;
  failureReason?: string;
  regions: PdfHighlight["regions"];
  segmentId?: string;
  pageWidth?: number;
  pageHeight?: number;
}

interface Filters {
  speaker: string;
  subject: string;
  examination: string;
  q: string;
}
const NO_FILTERS: Filters = { speaker: "", subject: "", examination: "", q: "" };

export interface SourceReaderProps {
  routeId: string;
  document: DocumentView;
  apiBaseUrl: string;
  initialPdfPage: number;
  initialPara?: number;
  initialLine?: number;
  highlight?: string;
  sourceAnchor?: SourceAnchorView;
  focusSegmentId?: string;
  outline: TranscriptOutline | null;
  initialSegments: TranscriptSegmentPage | null;
  initialChunks: readonly ParsedChunkView[];
  initialContext: PageContext | null;
}

function segmentKey(segment: TranscriptSegmentView): string {
  return `seg-${segment.id}`;
}

function inRegion(regions: PdfHighlight["regions"], x: number, y: number): boolean {
  return regions.some(
    (r) => x >= r.x && x <= r.x + r.width && y >= r.y - 2 && y <= r.y + r.height + 2,
  );
}

export function SourceReader(props: SourceReaderProps) {
  const {
    routeId,
    document,
    apiBaseUrl,
    outline,
    sourceAnchor,
    initialPara,
    initialLine,
    highlight,
  } = props;
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const t15 = useTranslations("phase15");
  const t19 = useTranslations("phase19");
  const t20 = useTranslations("phase20");
  const reader = useMemo(() => createReaderClient(apiBaseUrl), [apiBaseUrl]);
  const versionRef = document.versionRef ?? "";
  const isTranscript = outline !== null;

  const [pdfPage, setPdfPage] = useState(props.initialPdfPage);
  const [sourceView, setSourceView] = useState<"original" | "parsed">(
    document.artifactUrl ? "original" : "parsed",
  );
  const [showText, setShowText] = useState(true);
  const [showContext, setShowContext] = useState(true);
  const [pane, setPane] = useState<Pane>("source");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [pdfFit, setPdfFit] = useState<PdfFit>("width");
  const [pdfZoom, setPdfZoom] = useState(1);
  const [pdfScale, setPdfScale] = useState(1);
  const [pdfPages, setPdfPages] = useState<number>();
  const [pdfError, setPdfError] = useState<string>();
  const onPdfPages = useCallback((count: number) => setPdfPages(count), []);
  const onPdfScale = useCallback((scale: number) => setPdfScale(scale), []);
  const onPdfError = useCallback((message: string) => setPdfError(message), []);

  const [context, setContext] = useState<PageContext | null>(props.initialContext);
  const [contextFailed, setContextFailed] = useState(false);
  const [segments, setSegments] = useState<readonly TranscriptSegmentView[]>(
    props.initialSegments?.items ?? [],
  );
  const [chunks, setChunks] = useState<readonly ParsedChunkView[]>(props.initialChunks);
  const [loading, setLoading] = useState(false);
  const [contextTab, setContextTab] = useState<ContextTab>("summary");
  const [focusSegment, setFocusSegment] = useState<string | undefined>(props.focusSegmentId);
  const [active, setActive] = useState<ActiveSource | undefined>(() =>
    sourceAnchor
      ? {
          key: `anchor-${sourceAnchor.id}`,
          kind: "anchor",
          label: sourceAnchor.exactText ?? sourceAnchor.officialVersionRef,
          pdfPageIndex: sourceAnchor.pdfPageIndex,
          precision: sourceAnchor.precision,
          failureReason: sourceAnchor.failureReason,
          regions: sourceAnchor.regions,
          segmentId: sourceAnchor.transcriptSegmentId,
          pageWidth: sourceAnchor.pageWidth,
          pageHeight: sourceAnchor.pageHeight,
        }
      : undefined,
  );
  const [draftFilters, setDraftFilters] = useState<Filters>(NO_FILTERS);
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  const [filtered, setFiltered] = useState<TranscriptSegmentPage | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [search, setSearch] = useState<LocalSearchResult | null>(null);
  const firstLoad = useRef(true);

  const pageCount = document.pageCount ?? pdfPages;
  const lastPage = pageCount !== undefined ? Math.max(0, pageCount - 1) : pdfPage;
  const pageWidth = context?.pageWidth ?? active?.pageWidth;
  const pageHeight = context?.pageHeight ?? active?.pageHeight;
  const header = context?.transcriptHeader;
  const exactPattern = useMemo(() => exactSourcePattern(highlight), [highlight]);

  // ------------------------------------------------ page-scoped loading --
  useEffect(() => {
    if (firstLoad.current) {
      firstLoad.current = false;
      return;
    }
    let cancelled = false;
    setLoading(true);
    setContextFailed(false);
    const loads: Promise<unknown>[] = [
      reader
        .context(versionRef, pdfPage)
        .then((value) => !cancelled && setContext(value))
        .catch(() => !cancelled && (setContext(null), setContextFailed(true))),
    ];
    if (isTranscript) {
      loads.push(
        reader
          .segments(versionRef, { pdfPageIndex: pdfPage, limit: 200 })
          .then((value) => !cancelled && setSegments(value?.items ?? [])),
      );
    } else {
      loads.push(
        reader.chunks(versionRef, pdfPage).then((value) => !cancelled && setChunks(value)),
      );
    }
    void Promise.allSettled(loads).then(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [reader, versionRef, pdfPage, isTranscript]);

  // Deep-link restoration: the URL always names version, PDF page and focus.
  // Link-carried coordinates (anchor, hl, para, page, line) describe the page
  // the link opened; they are dropped once the reader leaves that page.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (pdfPage !== props.initialPdfPage) {
      for (const key of ["anchor", "hl", "para", "page", "line"]) params.delete(key);
    }
    if (versionRef) params.set("version", versionRef);
    params.set("pdfPage", String(pdfPage));
    if (focusSegment) params.set("segment", focusSegment);
    else params.delete("segment");
    window.history.replaceState(null, "", `${window.location.pathname}?${params.toString()}`);
  }, [pdfPage, focusSegment, versionRef, props.initialPdfPage]);

  // Focus the selected transcript segment in the text layer.
  useEffect(() => {
    if (!focusSegment) return;
    window.document
      .getElementById(`seg-${focusSegment}`)
      ?.scrollIntoView?.({ block: "nearest", inline: "nearest" });
  }, [focusSegment, segments]);

  const goToPage = useCallback(
    (next: number, focus?: string) => {
      const target = Math.min(Math.max(0, next), lastPage);
      setFocusSegment(focus);
      setActive((current) => (current && current.pdfPageIndex === target ? current : undefined));
      setPdfError(undefined);
      setPdfPage(target);
    },
    [lastPage],
  );

  const selectSegment = useCallback(
    (segment: TranscriptSegmentView) => {
      setFocusSegment(segment.id);
      if (!segment.anchor) return;
      setActive({
        key: segmentKey(segment),
        kind: "segment",
        label: [
          segment.pageNumber ? t20("transcriptPage", { page: segment.pageNumber }) : null,
          segment.lineFrom
            ? t20("lines", { from: segment.lineFrom, to: segment.lineTo ?? segment.lineFrom })
            : null,
          segment.speaker,
        ]
          .filter(Boolean)
          .join(" · "),
        pdfPageIndex: segment.pdfPageIndex,
        precision: segment.anchor.precision,
        failureReason: segment.anchor.failureReason,
        regions: segment.anchor.regions,
        segmentId: segment.id,
      });
    },
    [t20],
  );

  const showOverlay = useCallback(
    (overlay: PageOverlay) => {
      setActive({
        key: `overlay-${overlay.anchorId}`,
        kind: overlay.kind,
        label: overlay.label,
        pdfPageIndex: pdfPage,
        precision: overlay.precision,
        failureReason: overlay.failureReason,
        regions: overlay.regions,
        segmentId: overlay.transcriptSegmentId,
      });
      if (overlay.transcriptSegmentId) setFocusSegment(overlay.transcriptSegmentId);
      setPane("source");
    },
    [pdfPage],
  );

  // Reverse synchronization: only validated segment line geometry responds.
  const onPdfPoint = useCallback(
    (x: number, y: number) => {
      const hit = segments.find(
        (segment) =>
          segment.anchor &&
          EXACT.includes(segment.anchor.precision) &&
          inRegion(segment.anchor.regions, x, y),
      );
      if (hit) selectSegment(hit);
    },
    [segments, selectSegment],
  );

  const pdfHighlight: PdfHighlight | undefined =
    active &&
    EXACT.includes(active.precision) &&
    active.pdfPageIndex === pdfPage &&
    active.regions.length &&
    pageWidth &&
    pageHeight
      ? {
          key: active.key,
          regions: active.regions,
          pageWidth,
          pageHeight,
          label: active.label,
        }
      : undefined;

  const applyFilters = useCallback(
    async (next: Filters) => {
      setFilters(next);
      if (!next.speaker && !next.subject && !next.examination && next.q.trim().length < 2) {
        setFiltered(null);
        return;
      }
      setFiltered(
        await reader.segments(versionRef, {
          speaker: next.speaker || undefined,
          subject: next.subject || undefined,
          examination: next.examination || undefined,
          q: next.q.trim().length >= 2 ? next.q.trim() : undefined,
          limit: 100,
        }),
      );
    },
    [reader, versionRef],
  );

  const runSearch = useCallback(async () => {
    const q = searchQuery.trim();
    setSearch(q.length >= 2 ? await reader.search(versionRef, q) : null);
  }, [reader, searchQuery, versionRef]);

  const precisionLabel = (precision: SourcePrecision) => t20(`precisionLabel.${precision}`);
  const kindLabel = (kind: ActiveSource["kind"]) => t20(`kind.${kind}`);
  const tabOverlays = (context?.overlays ?? []).filter((overlay) =>
    TAB_KINDS[contextTab].includes(overlay.kind),
  );
  const hasFilters = Boolean(
    filters.speaker || filters.subject || filters.examination || filters.q,
  );

  // ---------------------------------------------------------- render --
  const sourceColumn = (
    <section
      aria-label={t20("sourceLayer")}
      className="min-w-0 space-y-2"
      data-reader-layer="source"
    >
      {document.artifactUrl ? (
        <>
          <OriginalPdfPage
            url={document.artifactUrl}
            pageIndex={pdfPage}
            fit={pdfFit}
            zoom={pdfZoom}
            highlight={pdfHighlight}
            pageSize={
              pageWidth && pageHeight ? { width: pageWidth, height: pageHeight } : undefined
            }
            onPointClick={isTranscript ? onPdfPoint : undefined}
            onPageCount={onPdfPages}
            onScale={onPdfScale}
            onError={onPdfError}
          />
          <div className="border-border bg-surface rounded-card flex flex-wrap items-center gap-2 border p-2 text-[11px]">
            <span className="identifier">{versionRef}</span>
            <span className="text-fg-secondary">
              {t20("pdfPage", { page: pdfPage + 1, total: pageCount ?? "—" })}
            </span>
            {context?.pageNumber ? (
              <span className="text-fg-secondary tabular">
                {isTranscript
                  ? t20("transcriptPage", { page: context.pageNumber })
                  : `p. ${context.pageNumber}`}
              </span>
            ) : null}
            {document.sourceUrl ? (
              <a
                className="text-accent ml-auto"
                href={document.sourceUrl}
                target="_blank"
                rel="noreferrer"
              >
                {t20("officialCourtSource")}
              </a>
            ) : null}
          </div>
          {context?.geometryState === "ocr_required" ? (
            <div
              data-ocr-required
              className="border-border bg-surface-raised rounded-card border border-dashed p-3 text-[11px]"
            >
              {t20("ocrRequired")}
            </div>
          ) : null}
          {active && active.pdfPageIndex === pdfPage ? (
            <div
              data-active-source={active.kind}
              data-active-precision={active.precision}
              className="border-border bg-surface rounded-card border p-3 text-[11px]"
            >
              <p className="section-label">{t20("whyHighlight")}</p>
              <p className="text-fg mt-1 break-words">
                {t20("highlightReason", {
                  kind: kindLabel(active.kind),
                  label: active.label,
                  precision: precisionLabel(active.precision),
                })}
              </p>
              {pdfHighlight ? null : (
                <p className="text-fg-secondary mt-1">
                  {t20("honestFallback", { precision: active.precision })}
                  {active.failureReason ? (
                    <span className="text-fg-tertiary ml-1 font-mono">
                      ({active.failureReason})
                    </span>
                  ) : null}
                </p>
              )}
            </div>
          ) : null}
          {isTranscript ? (
            <p className="text-fg-tertiary text-[10.5px]">{t20("pdfClickHint")}</p>
          ) : null}
          {pdfError ? <EmptyState title={t20("pdfUnavailable")} reason={pdfError} /> : null}
        </>
      ) : (
        <EmptyState title={t20("pdfCoordinateUnavailable")} reason={versionRef || document.id} />
      )}
    </section>
  );

  const transcriptText = (
    <div className="space-y-3">
      {outline ? (
        <div className="text-fg-secondary space-y-1 text-[11px]">
          <p className="text-fg font-semibold">
            {t20("hearing")} · <span className="tabular">{outline.hearingDate}</span>
            {outline.sessionLabel ? ` · ${outline.sessionLabel}` : ""}
          </p>
          {outline.pageFrom && outline.pageTo ? (
            <p className="tabular">
              {t20("printedRange", { from: outline.pageFrom, to: outline.pageTo })}
            </p>
          ) : null}
        </div>
      ) : null}
      {header ? (
        <div
          data-page-header
          className="border-border-subtle bg-surface rounded-card border p-2 text-[11px]"
        >
          <p className="section-label">{t20("pageHeader")}</p>
          <p className="text-fg mt-1">
            <Link
              className="identifier text-accent"
              href={
                header.subjectIsCode
                  ? `/witnesses/${encodeURIComponent(header.subject)}`
                  : `/search?q=${encodeURIComponent(header.subject)}`
              }
            >
              {header.subject}
            </Link>
            {" · "}
            {t20(`session.${header.sessionState}`)}
            {header.examination ? ` · ${header.examination}` : ""}
          </p>
          <p className="text-fg-tertiary mt-1 font-mono text-[10px] break-words">
            {header.headerText} · {header.rule}
          </p>
          <p className="text-fg-tertiary mt-1 text-[10px]">{t20("pageHeaderNote")}</p>
        </div>
      ) : null}
      {hasFilters && filtered ? (
        <div className="space-y-2">
          <div
            data-filtered-view
            role="status"
            className="border-border bg-surface-raised rounded-card border p-2 text-[11px]"
          >
            {t20("filteredNotice", { shown: filtered.items.length, total: filtered.total })}{" "}
            <button
              type="button"
              className="text-accent font-semibold"
              onClick={() => {
                setDraftFilters(NO_FILTERS);
                void applyFilters(NO_FILTERS);
              }}
            >
              {t20("clearFilters")}
            </button>
          </div>
          <ol className="space-y-2">
            {filtered.items.map((segment) => (
              <li key={segment.id}>
                <button
                  type="button"
                  className="border-border-faint hover:bg-surface-raised w-full rounded border p-2 text-left"
                  onClick={() => {
                    setDraftFilters(NO_FILTERS);
                    void applyFilters(NO_FILTERS);
                    if (segment.pdfPageIndex !== undefined)
                      goToPage(segment.pdfPageIndex, segment.id);
                  }}
                >
                  <SegmentCoordinates segment={segment} />
                  {segment.speaker ? (
                    <span className="text-fg ml-2 font-sans text-[10.5px] font-bold">
                      {segment.speaker}
                    </span>
                  ) : null}
                  <span className="text-fg-body mt-1 block font-serif text-[12.5px] leading-relaxed whitespace-pre-wrap">
                    {segment.text}
                  </span>
                </button>
              </li>
            ))}
          </ol>
        </div>
      ) : (
        <ol aria-label={t20("synchronizedText")} className="space-y-1" data-transcript-segments>
          {segments.length === 0 ? (
            <li>
              <EmptyState title={t20("noSegments")} reason={`${versionRef} · PDF ${pdfPage + 1}`} />
            </li>
          ) : null}
          {segments.map((segment) => {
            const focused = focusSegment === segment.id;
            const marksHere =
              initialLine === undefined ||
              (segment.lineFrom !== undefined &&
                segment.lineFrom <= initialLine &&
                (segment.lineTo ?? segment.lineFrom) >= initialLine);
            return (
              <li
                key={segment.id}
                id={`seg-${segment.id}`}
                data-segment-id={segment.id}
                data-segment-precision={segment.anchor?.precision}
                aria-current={focused ? "location" : undefined}
                className={`scroll-mt-24 rounded ${focused ? "bg-surface-high ring-accent ring-1" : ""}`}
              >
                {segment.closedSession ? (
                  <GapNotice
                    kind="closed-session"
                    reference={`${t20("transcriptPage", { page: segment.pageNumber ?? "—" })} ${t20("lines", { from: segment.lineFrom ?? "—", to: segment.lineTo ?? segment.lineFrom ?? "—" })}`}
                    extent={t20("lines", {
                      from: segment.lineFrom ?? "—",
                      to: segment.lineTo ?? segment.lineFrom ?? "—",
                    })}
                    reason={t20("closedSegment")}
                  />
                ) : (
                  <button
                    type="button"
                    onClick={() => selectSegment(segment)}
                    className="hover:bg-surface-raised flex w-full gap-2 rounded p-1.5 text-left"
                  >
                    <SegmentCoordinates segment={segment} compact />
                    <span className="min-w-0 flex-1">
                      {segment.speaker ? (
                        <span className="text-fg block font-sans text-[10.5px] font-bold">
                          {segment.speaker}
                          {segment.witnessCode ? (
                            <span className="identifier text-fg-secondary ml-1">
                              {segment.witnessCode}
                            </span>
                          ) : null}
                        </span>
                      ) : null}
                      <span className="text-fg-body block font-serif text-[12.5px] leading-relaxed whitespace-pre-wrap">
                        {splitExactSource(segment.text ?? "", marksHere ? exactPattern : null).map(
                          (part, index) =>
                            part.exact ? (
                              <mark
                                key={index}
                                data-exact-source
                                className="bg-surface-high text-fg ring-accent rounded px-0.5 ring-1"
                              >
                                {part.text}
                              </mark>
                            ) : (
                              part.text
                            ),
                        )}
                      </span>
                      <span className="text-fg-tertiary font-mono text-[9.5px]">
                        {segment.anchor ? precisionLabel(segment.anchor.precision) : null}
                      </span>
                    </span>
                  </button>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );

  const paragraphText = (
    <div className="space-y-3">
      {chunks.length === 0 ? (
        <EmptyState
          title={document.parseRequiresReview ? t15("parsedReviewRequired") : t20("noParsedText")}
          reason={`${versionRef || document.id} · PDF ${pdfPage + 1}`}
        />
      ) : null}
      {chunks.map((paragraph, index) => (
        <p
          key={`${paragraph.pdfPageIndex ?? pdfPage}-${paragraph.number ?? index}`}
          id={paragraph.number ? `para-${paragraph.number}` : `chunk-${index}`}
          className="group relative scroll-mt-24 pl-10 font-serif text-[13px] leading-[1.75] max-md:pl-8 max-md:text-[11.5px] max-md:leading-[1.85]"
        >
          {paragraph.number ? (
            <a
              href={`#para-${paragraph.number}`}
              className="tabular text-fg-muted group-hover:text-accent absolute top-0.5 left-0 text-[10px]"
            >
              ¶{paragraph.number}
            </a>
          ) : (
            <span className="tabular text-fg-muted absolute top-0.5 left-0 text-[9px]">
              {t20("pdfIndex", { page: (paragraph.pdfPageIndex ?? pdfPage) + 1 })}
            </span>
          )}
          {splitExactSource(
            paragraph.text,
            initialPara === undefined || paragraph.number === initialPara ? exactPattern : null,
          ).map((part, partIndex) =>
            part.exact ? (
              <mark
                key={partIndex}
                data-exact-source
                className="bg-surface-high text-fg ring-accent rounded px-0.5 ring-1"
              >
                {part.text}
              </mark>
            ) : (
              part.text
            ),
          )}
        </p>
      ))}
    </div>
  );

  const highlightOutside =
    highlight &&
    exactPattern &&
    pdfPage === props.initialPdfPage &&
    !(isTranscript
      ? segments.some((segment) =>
          splitExactSource(segment.text ?? "", exactPattern).some((part) => part.exact),
        )
      : chunks.some(
          (paragraph) =>
            (initialPara === undefined || paragraph.number === initialPara) &&
            splitExactSource(paragraph.text, exactPattern).some((part) => part.exact),
        ));

  const textColumn = (
    <section
      aria-label={t20("synchronizedText")}
      data-reader-layer="text"
      className="bg-surface border-border rounded-card min-w-0 border p-3"
    >
      <header className="mb-3 flex flex-wrap items-center gap-2">
        <h2 className="section-label">{t20("synchronizedText")}</h2>
        {loading ? <span className="text-fg-tertiary text-[10px]">{t20("loading")}</span> : null}
        <p className="text-fg-tertiary w-full text-[10.5px]">{t20("derivativeTextNote")}</p>
      </header>
      {highlightOutside ? (
        // The exact span lies outside the rendered text (running header,
        // heading or footnote). Say so; never mark a guess.
        <div
          data-exact-source-outside
          className="border-border-subtle bg-surface-raised rounded-card mb-3 border p-3"
        >
          <p className="text-fg-secondary text-[11px]">{t19("exactSourceOutside")}</p>
          <p className="text-fg mt-1 font-mono text-[11px] break-words">{highlight}</p>
        </div>
      ) : null}
      {isTranscript ? transcriptText : paragraphText}
    </section>
  );

  const contextColumn = (
    <aside
      aria-label={t("researchContext")}
      data-reader-layer="context"
      className="bg-surface min-h-full min-w-0"
    >
      <div
        role="tablist"
        aria-label={t("researchContext")}
        className="border-border-faint flex flex-wrap gap-1 border-b p-2"
      >
        {CONTEXT_TABS.map((tab) => (
          <button
            key={tab}
            role="tab"
            type="button"
            aria-selected={contextTab === tab}
            onClick={() => setContextTab(tab)}
            className={`rounded-control min-h-8 px-2 py-1 text-[10px] ${contextTab === tab ? "bg-surface-high text-fg" : "text-fg-secondary"}`}
          >
            {tb(`researchTabs.${tab}`)}
            {TAB_KINDS[tab].reduce((sum, kind) => sum + (context?.totals[kind] ?? 0), 0) ? (
              <span className="tabular text-fg-tertiary ml-1">
                {TAB_KINDS[tab].reduce((sum, kind) => sum + (context?.totals[kind] ?? 0), 0)}
              </span>
            ) : null}
          </button>
        ))}
      </div>
      <div className="space-y-3 p-3" role="tabpanel">
        {contextFailed ? (
          <EmptyState title={t20("contextUnavailable")} reason={versionRef} />
        ) : null}
        {contextTab === "summary" && context ? (
          <Panel title={t20("pageContextTotals")}>
            <ul className="space-y-1 text-[11px]" data-context-totals>
              {Object.entries(context.totals).map(([kind, count]) => (
                <li key={kind} className="flex justify-between">
                  <span>{t20(`kind.${kind}`)}</span>
                  <span className="tabular">{count}</span>
                </li>
              ))}
            </ul>
            <p className="text-fg-tertiary mt-2 text-[10px]">{t20("eventsUnsupported")}</p>
          </Panel>
        ) : null}
        {context && tabOverlays.length === 0 && !contextFailed ? (
          <EmptyState title={tb(`researchTabs.${contextTab}`)} reason={t20("pageContextEmpty")} />
        ) : null}
        {tabOverlays.some((overlay) => overlay.kind === "relationship") ? (
          <p className="governance-text">{t20("relationshipNeutral")}</p>
        ) : null}
        <ul className="divide-border-faint divide-y" data-page-overlays>
          {tabOverlays.map((overlay) => (
            <OverlayRow
              key={`${overlay.kind}-${overlay.anchorId}`}
              overlay={overlay}
              active={active?.key === `overlay-${overlay.anchorId}`}
              onShow={() => showOverlay(overlay)}
              precisionLabel={precisionLabel}
            />
          ))}
        </ul>
        {context?.truncated ? (
          <p className="text-fg-tertiary text-[10px]">{t20("contextTruncated")}</p>
        ) : null}
        {document.sourceUrl ? (
          <a className="text-accent text-[11px]" href={document.sourceUrl}>
            {t15("officialSource")}
          </a>
        ) : null}
      </div>
    </aside>
  );

  const sidebar = (
    <aside
      className={`border-border bg-surface-alt space-y-3 border-b p-3 lg:block lg:border-r lg:border-b-0 ${sidebarOpen ? "block" : "hidden"}`}
    >
      <Panel title={t("metadata")}>
        <KeyValue
          rows={[
            { key: "type", label: tb("docMeta.type"), value: document.type },
            {
              key: "doc",
              label: tb("docMeta.docDate"),
              value: <span className="tabular">{document.documentDate ?? "—"}</span>,
            },
            {
              key: "pages",
              label: tb("docMeta.pages"),
              value: <span className="tabular">{pageCount ?? "—"}</span>,
            },
            {
              key: "lang",
              label: tb("docMeta.language"),
              value: outline?.language ?? document.language,
            },
            {
              key: "version",
              label: tb("docMeta.version"),
              value:
                [document.versionRef, document.versionType, document.versionLabel]
                  .filter(Boolean)
                  .join(" · ") || "—",
            },
            {
              key: "parser",
              label: t15("parser"),
              value: document.parserName
                ? `${document.parserName}/${document.parserVersion ?? "—"}`
                : "—",
            },
          ]}
        />
      </Panel>
      {document.versions && document.versions.length > 1 ? (
        <Panel title={t20("versions")}>
          <ul className="space-y-1 text-[11px]" data-version-switcher>
            {document.versions.map((version) => (
              <li key={version.ref}>
                {version.ref === versionRef ? (
                  <span className="identifier text-fg break-all" aria-current="true">
                    {version.ref} · {t20("currentVersion")}
                  </span>
                ) : version.fetched ? (
                  <Link
                    className="identifier text-accent break-all"
                    href={`${routeId === "transcript" ? `/documents/transcript?document=${encodeURIComponent(document.citation.docId ?? document.id)}&` : `/documents/${encodeURIComponent(routeId)}?`}version=${encodeURIComponent(version.ref)}&pdfPage=0`}
                  >
                    {version.ref}
                  </Link>
                ) : (
                  <span className="identifier text-fg-muted break-all">
                    {version.ref} · {tb("notAvailable")}
                  </span>
                )}
                {version.label || version.type ? (
                  <span className="text-fg-tertiary ml-1">
                    {[version.type, version.label].filter(Boolean).join(" · ")}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
          <p className="text-fg-tertiary mt-2 text-[10px]">{t20("versionSwitchNote")}</p>
        </Panel>
      ) : null}
      <Panel title={t20("localSearch")}>
        <form
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            void runSearch();
          }}
          className="flex gap-1"
        >
          <label className="min-w-0 flex-1">
            <span className="sr-only">{t20("localSearch")}</span>
            <input
              type="search"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder={tb("inDocSearch")}
              className="border-border bg-surface text-fg rounded-control h-8 w-full border px-2 text-[11px]"
            />
          </label>
          <ToolButton onClick={() => void runSearch()}>{t20("applyFilters")}</ToolButton>
        </form>
        <p className="text-fg-tertiary mt-1 text-[10px]">{t20("localSearchNote")}</p>
        {search ? (
          <div className="mt-2 space-y-2" data-local-search>
            <p className="text-fg-secondary text-[10.5px]">
              {search.total
                ? t20("localSearchResults", { total: search.total })
                : t20("localSearchNone")}
            </p>
            <ol className="space-y-2">
              {search.items.map((hit, index) => (
                <li key={`${hit.transcriptSegmentId ?? hit.pdfPageIndex}-${index}`}>
                  <button
                    type="button"
                    className="border-border-faint hover:bg-surface-raised w-full rounded border p-2 text-left text-[10.5px]"
                    onClick={() => {
                      if (hit.pdfPageIndex !== undefined) {
                        goToPage(hit.pdfPageIndex, hit.transcriptSegmentId);
                        setPane("text");
                      }
                    }}
                  >
                    <span className="flex flex-wrap items-center gap-2">
                      <span
                        data-overlay-state={hit.matchType}
                        className="text-fg-secondary font-mono text-[9.5px] font-semibold"
                      >
                        {t20(`state.${hit.matchType}`)}
                      </span>
                      <span className="tabular">
                        {hit.pageNumber
                          ? isTranscript
                            ? t20("transcriptPage", { page: hit.pageNumber })
                            : `p. ${hit.pageNumber}`
                          : t20("pdfIndex", { page: (hit.pdfPageIndex ?? 0) + 1 })}
                      </span>
                      {hit.lineFrom ? (
                        <span className="tabular">
                          {t20("lines", { from: hit.lineFrom, to: hit.lineTo ?? hit.lineFrom })}
                        </span>
                      ) : null}
                      <span className="text-fg-tertiary font-mono">
                        {precisionLabel(hit.precision)}
                      </span>
                      <span className="text-fg-tertiary">
                        {t20("occurrences", { count: hit.occurrences })}
                      </span>
                    </span>
                    <span className="text-fg-body mt-1 block font-serif break-words">
                      {splitExactSource(hit.excerpt, exactSourcePattern(search.query)).map(
                        (part, partIndex) =>
                          part.exact ? (
                            <mark
                              key={partIndex}
                              className="bg-surface-high text-fg rounded px-0.5"
                            >
                              {part.text}
                            </mark>
                          ) : (
                            part.text
                          ),
                      )}
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </Panel>
      {outline ? (
        <Panel title={t20("transcriptNavigation")}>
          <div className="space-y-3 text-[11px]" data-transcript-navigation>
            <p className="text-fg-tertiary tabular">
              {t20("segmentCount", { count: outline.segmentCount })}
            </p>
            {outline.subjects.length ? (
              <ul className="space-y-1">
                {outline.subjects.map((subject) => (
                  <li key={subject.subject}>
                    <button
                      type="button"
                      className="text-accent identifier"
                      onClick={() => goToPage(subject.firstPdfPageIndex)}
                    >
                      {subject.subject}
                    </button>{" "}
                    <span className="text-fg-tertiary">
                      {subject.firstPageNumber
                        ? t20("fromPage", { page: subject.firstPageNumber })
                        : null}{" "}
                      · {t20("pagesCount", { count: subject.pages })}
                    </span>
                  </li>
                ))}
              </ul>
            ) : null}
            {outline.examinations.length ? (
              <ul className="space-y-1">
                {outline.examinations.map((exam) => (
                  <li key={`${exam.subject}-${exam.examination}`}>
                    <button
                      type="button"
                      className="text-accent text-left"
                      onClick={() => goToPage(exam.firstPdfPageIndex)}
                    >
                      {exam.examination}
                    </button>{" "}
                    <span className="identifier text-fg-tertiary">{exam.subject}</span>
                  </li>
                ))}
              </ul>
            ) : null}
            <form
              className="space-y-2"
              onSubmit={(event) => {
                event.preventDefault();
                void applyFilters(draftFilters);
                setPane("text");
              }}
            >
              <FilterSelect
                label={t20("speaker")}
                empty={t20("allSpeakers")}
                value={draftFilters.speaker}
                options={outline.speakers.map((speaker) => ({
                  value: speaker.label,
                  label: `${speaker.label} (${speaker.segments})`,
                }))}
                onChange={(speaker) => setDraftFilters((current) => ({ ...current, speaker }))}
              />
              <FilterSelect
                label={t20("headerSubject")}
                empty={t20("allSubjects")}
                value={draftFilters.subject}
                options={outline.subjects.map((subject) => ({
                  value: subject.subject,
                  label: subject.subject,
                }))}
                onChange={(subject) => setDraftFilters((current) => ({ ...current, subject }))}
              />
              <FilterSelect
                label={t20("examination")}
                empty={t20("allExaminations")}
                value={draftFilters.examination}
                options={[...new Set(outline.examinations.map((exam) => exam.examination))].map(
                  (examination) => ({ value: examination, label: examination }),
                )}
                onChange={(examination) =>
                  setDraftFilters((current) => ({ ...current, examination }))
                }
              />
              <label className="block">
                <span className="text-fg-secondary text-[10.5px]">{t20("textFilter")}</span>
                <input
                  type="search"
                  value={draftFilters.q}
                  onChange={(event) =>
                    setDraftFilters((current) => ({ ...current, q: event.target.value }))
                  }
                  className="border-border bg-surface text-fg rounded-control mt-1 h-8 w-full border px-2 text-[11px]"
                />
              </label>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-surface-high text-fg rounded-control min-h-8 px-3 text-[11px]"
                >
                  {t20("applyFilters")}
                </button>
                {hasFilters ? (
                  <button
                    type="button"
                    className="text-accent text-[11px]"
                    onClick={() => {
                      setDraftFilters(NO_FILTERS);
                      void applyFilters(NO_FILTERS);
                    }}
                  >
                    {t20("clearFilters")}
                  </button>
                ) : null}
              </div>
            </form>
          </div>
        </Panel>
      ) : null}
    </aside>
  );

  const textVisible = sourceView === "parsed" || showText;
  return (
    <AppShell
      mode="light"
      showDemoFlag={false}
      crumbs={[{ label: t("documents"), href: "/documents" }, { label: document.id }]}
    >
      <div className="flex min-w-0 flex-1 flex-col" data-source-reader>
        <Toolbar className="bg-surface">
          <nav
            aria-label={tb("breadcrumb")}
            className="flex min-w-0 flex-wrap items-center gap-2 text-[11px]"
          >
            <Link href="/documents" className="text-accent">
              {t("documents")}
            </Link>
            <span className="text-fg-muted">/</span>
            <span className="identifier text-fg">{document.id}</span>
            {/* A transcript mixes Court, party and witness speech: no single source
                category applies, so none is claimed. */}
            {isTranscript ? null : <SourceBadge type={document.citation.sourceType} size="sm" />}
            <span className="rounded-badge bg-surface-raised text-fg-secondary px-1.5 py-0.5 text-[10px]">
              {document.type}
            </span>
          </nav>
          <div className="ml-auto flex flex-wrap items-center gap-1">
            <span className="rounded-badge bg-surface-high text-fg-secondary px-2 py-1 text-[10px]">
              {tb("realDataNotice")}
            </span>
            <ToolButton
              onClick={() => goToPage(pdfPage - 1)}
              ariaLabel={t("previous")}
              disabled={pdfPage <= 0}
            >
              ‹
            </ToolButton>
            <span className="tabular text-fg-secondary px-1 text-[11px]">
              {tb("pager", { n: pdfPage + 1, total: pageCount ?? "—" })}
            </span>
            <ToolButton
              onClick={() => goToPage(pdfPage + 1)}
              ariaLabel={t("next")}
              disabled={pageCount !== undefined && pdfPage >= lastPage}
            >
              ›
            </ToolButton>
            <ToolButton onClick={() => navigator.clipboard?.writeText(window.location.href)}>
              {t20("lineLink")}
            </ToolButton>
            {document.artifactUrl ? (
              <>
                <ToolButton
                  onClick={() => setSourceView("original")}
                  pressed={sourceView === "original"}
                >
                  {t20("originalPdf")}
                </ToolButton>
                <ToolButton
                  onClick={() => setSourceView("parsed")}
                  pressed={sourceView === "parsed"}
                >
                  {t20("parsedText")}
                </ToolButton>
                <ToolButton
                  onClick={() => {
                    setPdfFit("custom");
                    setPdfZoom(Math.max(0.5, pdfScale - 0.1));
                  }}
                >
                  {t("zoomOut")}
                </ToolButton>
                <ToolButton
                  onClick={() => {
                    setPdfFit("custom");
                    setPdfZoom(Math.min(3, pdfScale + 0.1));
                  }}
                >
                  {t("zoomIn")}
                </ToolButton>
                <ToolButton onClick={() => setPdfFit("page")} pressed={pdfFit === "page"}>
                  {t20("fitPage")}
                </ToolButton>
                <ToolButton onClick={() => setPdfFit("width")} pressed={pdfFit === "width"}>
                  {t20("fitWidth")}
                </ToolButton>
                <ToolButton
                  onClick={() => {
                    setPdfFit("custom");
                    setPdfZoom(1);
                  }}
                >
                  {t("reset")}
                </ToolButton>
                <span className="tabular text-fg-secondary px-1 text-[11px]">
                  {Math.round(pdfScale * 100)}%
                </span>
              </>
            ) : null}
            <ToolButton
              className="hidden lg:inline-flex"
              onClick={() => setShowText((value) => !value)}
              pressed={showText}
            >
              {t20("textPanel")}
            </ToolButton>
            <ToolButton
              className="hidden lg:inline-flex"
              onClick={() => setShowContext((value) => !value)}
              pressed={showContext}
            >
              {t20("contextPanel")}
            </ToolButton>
            <ToolButton
              onClick={() => setSidebarOpen((value) => !value)}
              pressed={sidebarOpen}
              className="lg:hidden"
            >
              {tb("sidebarToggle")}
            </ToolButton>
          </div>
        </Toolbar>
        <div className="border-border-faint bg-surface border-b px-3 py-2 lg:hidden">
          <Segmented
            label={t20("readerLayers")}
            value={pane}
            onChange={setPane}
            options={[
              { key: "source", label: t20("sourceLayer") },
              { key: "text", label: t20("textLayer") },
              { key: "context", label: t20("contextLayer") },
            ]}
          />
        </div>
        <div
          className={`grid min-w-0 flex-1 ${showContext ? "lg:grid-cols-[240px_minmax(0,1fr)_300px]" : "lg:grid-cols-[240px_minmax(0,1fr)]"}`}
        >
          {sidebar}
          <div className="bg-surface-alt min-w-0 p-3 md:p-4">
            <div
              className={`mx-auto grid w-full gap-3 ${sourceView === "original" && showText ? "max-w-[1400px] xl:grid-cols-[minmax(0,1fr)_minmax(320px,400px)]" : "max-w-[960px]"}`}
            >
              {sourceView === "original" ? (
                <div className={pane === "source" ? "block" : "hidden lg:block"}>
                  {sourceColumn}
                </div>
              ) : null}
              {textVisible ? (
                <div
                  className={`${pane === "text" || sourceView === "parsed" ? "block" : "hidden"} lg:block ${sourceView === "original" ? "xl:max-h-[calc(100vh-180px)] xl:overflow-y-auto" : ""}`}
                >
                  {textColumn}
                </div>
              ) : null}
            </div>
          </div>
          <div
            className={`border-border border-t lg:border-t-0 lg:border-l ${showContext ? "lg:block" : "lg:hidden"} ${pane === "context" ? "block" : "hidden"}`}
          >
            {contextColumn}
          </div>
        </div>
        {document.citation ? (
          <div className="sr-only">
            <CitationChip citation={document.citation} />
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}

function SegmentCoordinates({
  segment,
  compact,
}: {
  segment: TranscriptSegmentView;
  compact?: boolean;
}) {
  const t20 = useTranslations("phase20");
  return (
    <span
      className={`tabular text-fg-secondary shrink-0 font-sans text-[10px] ${compact ? "w-[4.5rem]" : ""}`}
    >
      {segment.pageNumber ? t20("transcriptPage", { page: segment.pageNumber }) : null}
      {segment.lineFrom ? (
        <span className="block">
          {segment.lineTo && segment.lineTo !== segment.lineFrom
            ? t20("lines", { from: segment.lineFrom, to: segment.lineTo })
            : t20("line", { line: segment.lineFrom })}
        </span>
      ) : null}
    </span>
  );
}

function FilterSelect({
  label,
  empty,
  value,
  options,
  onChange,
}: {
  label: string;
  empty: string;
  value: string;
  options: readonly { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-fg-secondary text-[10.5px]">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="border-border bg-surface text-fg rounded-control mt-1 h-8 w-full border px-1 text-[11px]"
      >
        <option value="">{empty}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function OverlayRow({
  overlay,
  active,
  onShow,
  precisionLabel,
}: {
  overlay: PageOverlay;
  active: boolean;
  onShow: () => void;
  precisionLabel: (precision: SourcePrecision) => string;
}) {
  const t20 = useTranslations("phase20");
  const targetLabel =
    overlay.kind === "citation"
      ? t20("openCitedSource")
      : overlay.kind === "finding"
        ? t20("openFinding")
        : overlay.kind === "relationship"
          ? t20("openEvidence")
          : t20("openDossier");
  return (
    <li
      className={`space-y-1.5 py-2 first:pt-0 last:pb-0 ${active ? "bg-surface-high -mx-1 rounded px-1" : ""}`}
      data-overlay-kind={overlay.kind}
      data-overlay-precision={overlay.precision}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-fg-tertiary text-[10px]">{t20(`kind.${overlay.kind}`)}</span>
        <span
          data-overlay-state={overlay.state}
          className="text-fg-secondary font-mono text-[9.5px] font-semibold"
        >
          {t20(`state.${overlay.state}`)}
        </span>
        <span className="text-fg-tertiary font-mono text-[9.5px]">
          {precisionLabel(overlay.precision)}
        </span>
        {overlay.lineFrom ? (
          <span className="tabular text-fg-tertiary text-[9.5px]">
            {t20("lines", { from: overlay.lineFrom, to: overlay.lineTo ?? overlay.lineFrom })}
          </span>
        ) : null}
      </div>
      <p
        className={`text-fg text-[11px] font-semibold break-words ${overlay.kind === "witness" || overlay.kind === "exhibit" || overlay.kind === "citation" ? "identifier" : ""}`}
      >
        {overlay.kind === "relationship"
          ? `${overlay.fromLabel ?? "—"} · ${overlay.label.replaceAll("_", " ")} · ${overlay.toLabel ?? "—"}`
          : overlay.label}
      </p>
      {overlay.kind === "exhibit" ? (
        <p className="text-fg-secondary text-[10.5px]">
          {t20("exhibitStatus", {
            status: (overlay.exhibitStatus ?? "unknown").toUpperCase(),
          })}
        </p>
      ) : null}
      {overlay.kind === "citation" && overlay.resolutionState ? (
        <p className="text-fg-secondary font-mono text-[10px]">
          {overlay.resolutionState.toUpperCase()}
        </p>
      ) : null}
      {overlay.kind === "relationship" && overlay.provenance ? (
        <div className="text-fg-secondary space-y-0.5 text-[10.5px]">
          <p>
            {t20("evidenceCount", { count: overlay.evidenceCount ?? 1 })} ·{" "}
            {t20("evidenceBasis", { kind: overlay.provenance.kind.replaceAll("_", " ") })}
          </p>
          <p className="text-fg-tertiary" data-evidence-path>
            {t20("evidencePath")}: {t20(`kind.${overlay.kind}`)} →{" "}
            {overlay.provenance.kind.replaceAll("_", " ")} →{" "}
            <span className="identifier">{overlay.provenance.versionRef}</span>
          </p>
          {overlay.provenance.rule ? (
            <p className="text-fg-tertiary font-mono text-[9.5px]">{overlay.provenance.rule}</p>
          ) : null}
        </div>
      ) : null}
      {overlay.rule && overlay.kind !== "relationship" ? (
        <p className="text-fg-tertiary font-mono text-[9.5px]">{overlay.rule}</p>
      ) : null}
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={onShow}
          aria-pressed={active}
          className="text-accent min-h-8 text-[11px] font-semibold"
        >
          {t20("showInSource")}
        </button>
        {overlay.targetPath ? (
          <Link href={overlay.targetPath} className="text-accent text-[11px]">
            {targetLabel}
          </Link>
        ) : overlay.kind === "citation" ? (
          <span className="text-fg-tertiary text-[10.5px]">{t20("noResolvedTarget")}</span>
        ) : null}
      </div>
    </li>
  );
}
