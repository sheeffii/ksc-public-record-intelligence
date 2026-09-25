"use client";

import type { SourceType } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActiveFilters,
  FilterOption,
  FilterRail,
  FilterSection,
} from "@/components/primitives/Filter";
import { Panel } from "@/components/primitives/Panel";
import { EmptyState, GapNotice } from "@/components/primitives/States";
import {
  EvidenceBasis,
  AiAnalysisBlock,
  CitationChip,
  ProtectionNotice,
  RecordBlock,
  SourceBadge,
  VerificationBadge,
} from "@/components/provenance";
import { exactSourcePattern, splitExactSource } from "@/lib/exact-source";
import { AppShell } from "@/components/shell/AppShell";
import {
  courtCitation,
  mockRepository,
  transcriptCitation,
  type MockDocument,
  type MockSearchResult,
} from "@/mock";
import { ActionLink, DemoNotice, ScreenHeader, TabStrip } from "./ScreenChrome";
import { KeyValue, NoteStrip, SectionCard, Segmented, ToolButton, Toolbar } from "./Workspace";
import type { NetworkView } from "@/data";
import type { SourceAnchorView } from "@/data";
import { OriginalPdfPage, type PdfFit } from "@/components/source/OriginalPdfPage";

// ------------------------------------------------------------ reader ------

const TOC = [
  { id: "intro", label: "I. Introduction", page: 1 },
  { id: "procedural", label: "II. Procedural history", page: 4 },
  { id: "findings", label: "III. Findings", page: 12 },
  { id: "disposition", label: "IV. Disposition", page: 48 },
];

export function DocumentReaderScreen({
  id,
  initialDocument,
  initialPage,
  initialPdfPage,
  initialPara,
  highlight,
  contextNetwork,
  sourceAnchor,
}: {
  id: string;
  initialDocument?: MockDocument;
  initialPage?: number;
  initialPdfPage?: number;
  /** Paragraph named by a provenance link; the exact slice is marked only there. */
  initialPara?: number;
  /** Verbatim persisted source slice to mark (see `lib/exact-source`). */
  highlight?: string;
  contextNetwork?: NetworkView;
  sourceAnchor?: SourceAnchorView;
}) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const t15 = useTranslations("phase15");
  const t18 = useTranslations("phase18");
  const isReal = initialDocument !== undefined;
  const document = initialDocument ?? mockRepository.getDocument(id);
  const isTranscript = !isReal && id.startsWith("T-");
  const coordinateKind =
    initialPdfPage !== undefined || (initialPage === undefined && document.coordinateKind === "pdf")
      ? "pdfPage"
      : "page";
  // The page state is in the coordinate system the Reader filters by: a link
  // carrying both `pdfPage` and printed `page` navigates by the PDF index.
  const [page, setPage] = useState(
    coordinateKind === "pdfPage"
      ? (initialPdfPage ?? document.page)
      : (initialPage ?? initialPdfPage ?? document.page),
  );
  const [panelTab, setPanelTab] = useState<
    "summary" | "mentions" | "people" | "exhibits" | "findings" | "citations"
  >("summary");
  const [inDoc, setInDoc] = useState("");
  const exactPattern = useMemo(
    () => (isReal ? exactSourcePattern(highlight) : null),
    [isReal, highlight],
  );
  const t19 = useTranslations("phase19");
  const t20 = useTranslations("phase20");
  const [sourceView, setSourceView] = useState<"original" | "parsed">(
    document.artifactUrl ? "original" : "parsed",
  );
  const [pdfFit, setPdfFit] = useState<PdfFit>("width");
  const [pdfZoom, setPdfZoom] = useState(1);
  const [pdfRenderedScale, setPdfRenderedScale] = useState(1);
  const [pdfPages, setPdfPages] = useState<number>();
  const [pdfError, setPdfError] = useState<string>();
  const onPdfPages = useCallback((count: number) => setPdfPages(count), []);
  const onPdfScale = useCallback((scale: number) => setPdfRenderedScale(scale), []);
  const onPdfError = useCallback((message: string) => setPdfError(message), []);
  useEffect(() => {
    const target =
      window.document.querySelector("[data-exact-source]") ??
      (initialPara !== undefined ? window.document.getElementById(`para-${initialPara}`) : null);
    target?.scrollIntoView?.({ block: "center" });
  }, [initialPara, highlight]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const total = document.pageCount ?? (isReal ? undefined : 52);
  const coordinateLast =
    total === undefined ? page : coordinateKind === "pdfPage" ? Math.max(0, total - 1) : total;
  const paragraphs = document.paragraphs.filter(
    (p) =>
      (!isReal ||
        (coordinateKind === "pdfPage"
          ? p.pdfPageIndex === undefined ||
            (p.pdfPageIndex <= page && (p.pdfPageIndexTo ?? p.pdfPageIndex) >= page)
          : p.page === undefined || (p.page <= page && (p.pageTo ?? p.page) >= page))) &&
      (!inDoc || p.text.toLowerCase().includes(inDoc.toLowerCase())),
  );
  const sourcePdfIndex =
    coordinateKind === "pdfPage"
      ? page
      : paragraphs.find((paragraph) => paragraph.pdfPageIndex !== undefined)?.pdfPageIndex;
  const panelTabs = ["summary", "mentions", "people", "exhibits", "findings", "citations"] as const;
  const contextNode = contextNetwork?.nodes.find(
    (node) => node.ref === id || node.ref?.endsWith(`/${id}`),
  );
  const contextEdges = contextNode
    ? (contextNetwork?.edges.filter(
        (edge) => edge.from === contextNode.id || edge.to === contextNode.id,
      ) ?? [])
    : [];
  const contextRows = contextEdges.flatMap((edge) => {
    const otherId = edge.from === contextNode?.id ? edge.to : edge.from;
    const node = contextNetwork?.nodes.find((candidate) => candidate.id === otherId);
    if (!node) return [];
    const matchesTab =
      panelTab === "summary" ||
      panelTab === "mentions" ||
      panelTab === "citations" ||
      (panelTab === "people" && (node.entityKind === "person" || node.entityKind === "witness")) ||
      (panelTab === "exhibits" && node.entityKind === "exhibit") ||
      (panelTab === "findings" && node.entityKind === "finding");
    return matchesTab ? [{ edge, node }] : [];
  });

  return (
    <AppShell
      mode="light"
      showDemoFlag={!isReal}
      crumbs={[{ label: t("documents"), href: "/documents" }, { label: document.id }]}
    >
      <div className="flex min-w-0 flex-1 flex-col">
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
            <SourceBadge type="court" size="sm" />
            <span className="rounded-badge bg-surface-raised text-fg-secondary px-1.5 py-0.5 text-[10px]">
              {document.type}
            </span>
          </nav>
          <div className="ml-auto flex flex-wrap items-center gap-1">
            {isReal ? (
              <span className="rounded-badge bg-surface-high text-fg-secondary px-2 py-1 text-[10px]">
                {tb("realDataNotice")}
              </span>
            ) : null}
            <ToolButton
              href={
                isReal
                  ? `/documents/${encodeURIComponent(id)}?${coordinateKind}=${Math.max(coordinateKind === "pdfPage" ? 0 : 1, page - 1)}${document.versionRef ? `&version=${encodeURIComponent(document.versionRef)}` : ""}`
                  : undefined
              }
              onClick={isReal ? undefined : () => setPage((p) => Math.max(1, p - 1))}
              ariaLabel={t("previous")}
            >
              ‹
            </ToolButton>
            <span className="tabular text-fg-secondary px-1 text-[11px]">
              {tb("pager", { n: page, total: total ?? "—" })}
            </span>
            <ToolButton
              href={
                isReal
                  ? `/documents/${encodeURIComponent(id)}?${coordinateKind}=${Math.min(coordinateLast, page + 1)}${document.versionRef ? `&version=${encodeURIComponent(document.versionRef)}` : ""}`
                  : undefined
              }
              onClick={isReal ? undefined : () => setPage((p) => Math.min(total ?? 52, p + 1))}
              ariaLabel={t("next")}
            >
              ›
            </ToolButton>
            <ToolButton onClick={() => navigator.clipboard?.writeText(document.citation.display)}>
              {t("copyCitation")}
            </ToolButton>
            {isReal && document.artifactUrl ? (
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
                    setPdfZoom(Math.max(0.5, pdfRenderedScale - 0.1));
                  }}
                >
                  {t("zoomOut")}
                </ToolButton>
                <ToolButton
                  onClick={() => {
                    setPdfFit("custom");
                    setPdfZoom(Math.min(3, pdfRenderedScale + 0.1));
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
                  {Math.round(pdfRenderedScale * 100)}%
                </span>
              </>
            ) : null}
            <ToolButton href={`/network?focus=${document.id}`}>{t("viewNetwork")}</ToolButton>
            <ToolButton
              onClick={() => setSidebarOpen((v) => !v)}
              pressed={sidebarOpen}
              className="lg:hidden"
            >
              {tb("sidebarToggle")}
            </ToolButton>
            <ToolButton
              onClick={() => setPanelOpen((v) => !v)}
              pressed={panelOpen}
              className="lg:hidden"
            >
              {tb("panelToggle")}
            </ToolButton>
          </div>
        </Toolbar>
        <div className="grid min-w-0 flex-1 lg:grid-cols-[240px_minmax(0,1fr)_300px]">
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
                    key: "filing",
                    label: tb("docMeta.filingDate"),
                    value: <span className="tabular">{document.filingDate ?? "—"}</span>,
                  },
                  {
                    key: "pages",
                    label: tb("docMeta.pages"),
                    value: <span className="tabular">{total ?? "—"}</span>,
                  },
                  { key: "lang", label: tb("docMeta.language"), value: document.language },
                  {
                    key: "version",
                    label: tb("docMeta.version"),
                    value:
                      [document.versionRef, document.versionType, document.versionLabel]
                        .filter(Boolean)
                        .join(" · ") || "—",
                  },
                  {
                    key: "public",
                    label: tb("docMeta.publicState"),
                    value: document.visibility ?? "—",
                  },
                  {
                    key: "artifact",
                    label: t15("artifact"),
                    value: document.artifactStatus ?? "—",
                  },
                  {
                    key: "parser",
                    label: t15("parser"),
                    value: document.parserName
                      ? `${document.parserName}/${document.parserVersion ?? "—"}`
                      : "—",
                  },
                  {
                    key: "review",
                    label: t15("parseReview"),
                    value: document.parseRequiresReview
                      ? t15("reviewRequired")
                      : t15("reviewNotRequired"),
                  },
                ]}
              />
            </Panel>
            <label className="block">
              <span className="sr-only">{tb("inDocSearch")}</span>
              <input
                type="search"
                value={inDoc}
                onChange={(e) => setInDoc(e.target.value)}
                placeholder={tb("inDocSearch")}
                className="border-border bg-surface text-fg rounded-control h-8 w-full border px-3 text-[11px]"
              />
            </label>
            {!isReal ? (
              <Panel title={tb("tableOfContents")}>
                <ol className="space-y-1 text-[11px]">
                  {TOC.map((item) => (
                    <li key={item.id}>
                      <button
                        type="button"
                        onClick={() => setPage(item.page)}
                        aria-current={page >= item.page ? "location" : undefined}
                        className={`flex w-full justify-between gap-2 text-left ${page >= item.page ? "text-fg" : "text-fg-secondary"}`}
                      >
                        <span>{item.label}</span>
                        <span className="tabular text-fg-muted">p. {item.page}</span>
                      </button>
                    </li>
                  ))}
                </ol>
              </Panel>
            ) : null}
            {!isReal ? (
              <Panel title={tb("docMeta.version")}>
                <ul className="space-y-1 text-[11px]">
                  <li className="identifier text-fg">{document.id}/RED</li>
                  <li className="identifier text-fg-muted">
                    {document.id} · {tb("notAvailable")}
                  </li>
                </ul>
              </Panel>
            ) : null}
          </aside>
          <div className="bg-surface-alt min-w-0 overflow-x-auto p-3 md:p-6">
            <div className="mx-auto flex w-full max-w-[960px] flex-col gap-3">
              {isReal && sourceView === "original" ? (
                document.artifactUrl && sourcePdfIndex !== undefined ? (
                  <section aria-label={t20("originalPdf")} className="min-w-0">
                    <OriginalPdfPage
                      url={document.artifactUrl}
                      pageIndex={sourcePdfIndex}
                      fit={pdfFit}
                      zoom={pdfZoom}
                      anchor={sourceAnchor}
                      onPageCount={onPdfPages}
                      onScale={onPdfScale}
                      onError={onPdfError}
                    />
                    <div className="border-border bg-surface rounded-card mt-2 flex flex-wrap items-center gap-2 border p-2 text-[11px]">
                      <span className="identifier">{document.versionRef}</span>
                      <span className="text-fg-secondary">
                        {t20("pdfPage", { page: sourcePdfIndex + 1, total: pdfPages ?? "—" })}
                      </span>
                      {sourceAnchor ? (
                        <span className="text-fg-secondary">
                          {t20("precision", { precision: sourceAnchor.precision })}
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
                    {sourceAnchor &&
                    sourceAnchor.precision !== "exact_geometry" &&
                    sourceAnchor.precision !== "ocr_geometry" ? (
                      <div className="border-border bg-surface-raised rounded-card mt-2 border p-3 text-[11px]">
                        {t20("honestFallback", { precision: sourceAnchor.precision })}
                      </div>
                    ) : null}
                    {pdfError ? (
                      <EmptyState title={t20("pdfUnavailable")} reason={pdfError} />
                    ) : null}
                  </section>
                ) : (
                  <EmptyState
                    title={t20("pdfCoordinateUnavailable")}
                    reason={document.versionRef ?? document.id}
                  />
                )
              ) : null}
              <article
                className={`${isReal && sourceView === "original" ? "hidden" : "block"} shadow-page bg-surface text-fg-body min-h-[760px] w-full max-w-[600px] self-center px-6 py-8 md:px-[60px] md:py-[52px]`}
              >
                {!isReal ? (
                  <div className="border-court bg-surface-raised text-fg rounded-card mb-4 border-l-2 px-3 py-2 text-[11px]">
                    {tb("citedBanner", { ref: "F-DEMO-01" })} ·{" "}
                    <Link href="/findings/F-DEMO-01" className="text-accent font-semibold">
                      {t("courtFindings")} →
                    </Link>
                  </div>
                ) : null}
                <p className="identifier text-fg-muted mb-4 text-[10px]">
                  {document.id} · {coordinateKind === "pdfPage" ? t15("pdfIndex") : t("page")}{" "}
                  {page}
                </p>
                {isReal ? (
                  <div className="mb-4">
                    <CitationChip
                      citation={{
                        ...document.citation,
                        page: coordinateKind === "page" ? page : undefined,
                        display: `${document.citation.ref} · ${coordinateKind === "pdfPage" ? `PDF ${page}` : `p. ${page}`}`,
                      }}
                    />
                  </div>
                ) : null}
                {isTranscript ? (
                  <TranscriptPage />
                ) : !isReal && page === 2 ? (
                  <GapNotice
                    kind="redaction"
                    reference={`${document.id}/RED`}
                    extent="p. 2, 2 lines"
                    reason={tb("redactedPage")}
                  />
                ) : (
                  paragraphs.map((paragraph, index) => (
                    <p
                      key={`${paragraph.pdfPageIndex ?? page}-${paragraph.number ?? index}`}
                      id={paragraph.number ? `para-${paragraph.number}` : `chunk-${index}`}
                      className="group relative mb-4 scroll-mt-24 pl-10 font-serif text-[13.5px] leading-[1.75] max-md:pl-8 max-md:text-[11.5px] max-md:leading-[1.85] md:text-[14px]"
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
                          PDF {paragraph.pdfPageIndex ?? page}
                        </span>
                      )}
                      {splitExactSource(
                        paragraph.text,
                        initialPara === undefined || paragraph.number === initialPara
                          ? exactPattern
                          : null,
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
                  ))
                )}
                {highlight &&
                exactPattern &&
                !paragraphs.some(
                  (paragraph) =>
                    (initialPara === undefined || paragraph.number === initialPara) &&
                    splitExactSource(paragraph.text, exactPattern).some((part) => part.exact),
                ) ? (
                  // The exact span lies outside the rendered paragraphs (running
                  // header, heading or footnote). Say so; never mark a guess.
                  <div
                    data-exact-source-outside
                    className="border-border-subtle bg-surface-raised rounded-card mb-4 border p-3"
                  >
                    <p className="text-fg-secondary text-[11px]">{t19("exactSourceOutside")}</p>
                    <p className="text-fg mt-1 font-mono text-[11px] break-words">{highlight}</p>
                  </div>
                ) : null}
                {isReal && paragraphs.length === 0 ? (
                  <EmptyState
                    title={
                      document.parseRequiresReview
                        ? t15("parsedReviewRequired")
                        : t15("noParsedCoordinate")
                    }
                    reason={`${document.versionRef ?? document.id} · page ${page}`}
                  />
                ) : null}
                {!isReal ? (
                  <section className="border-border-faint mt-8 border-t pt-3">
                    <h3 className="section-label mb-1">{tb("footnotes")}</h3>
                    <p className="text-fg-secondary text-[10.5px] leading-relaxed">
                      1. Demo footnote; cites{" "}
                      <CitationChip citation={transcriptCitation} size="sm" />.
                    </p>
                  </section>
                ) : null}
              </article>
            </div>
          </div>
          <aside
            className={`border-border bg-surface-alt border-t lg:block lg:border-t-0 lg:border-l ${panelOpen ? "block" : "hidden"}`}
          >
            <div
              role="tablist"
              aria-label={t("researchContext")}
              className="border-border-faint flex flex-wrap gap-1 border-b p-2"
            >
              {panelTabs.map((tab) => (
                <button
                  key={tab}
                  role="tab"
                  type="button"
                  aria-selected={panelTab === tab}
                  onClick={() => setPanelTab(tab)}
                  className={`rounded-control px-2 py-1 text-[10px] ${panelTab === tab ? "bg-surface-high text-fg" : "text-fg-secondary"}`}
                >
                  {tb(`researchTabs.${tab}`)}
                </button>
              ))}
            </div>
            <div className="space-y-3 p-3">
              {isReal && contextRows.length === 0 ? (
                <EmptyState
                  title={tb(`researchTabs.${panelTab}`)}
                  reason={t18("readerContextUnavailable")}
                />
              ) : null}
              {isReal && contextRows.length ? (
                <ul className="divide-border-faint divide-y">
                  {contextRows.map(({ edge, node }) => (
                    <li key={edge.id} className="space-y-2 py-2 first:pt-0 last:pb-0">
                      <p className="text-fg text-[11px] font-semibold">{node.label}</p>
                      <p className="text-fg-secondary text-[10px]">
                        {edge.relation.replaceAll("_", " ")}
                      </p>
                      <div className="flex flex-wrap items-center gap-2">
                        <SourceBadge type={edge.sourceType} size="sm" />
                        <VerificationBadge state={edge.verification} size="sm" />
                        <EvidenceBasis kind={edge.evidenceKind} count={edge.evidenceCount} />
                        <CitationChip citation={edge.citation} size="sm" />
                        {edge.sourcePath ? (
                          <ActionLink href={edge.sourcePath}>{t("openSource")}</ActionLink>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : null}
              {!isReal && panelTab === "summary" ? (
                <AiAnalysisBlock citations={[courtCitation]}>
                  {"Demo AI summary of the sample document. Analysis only — never the record."}
                </AiAnalysisBlock>
              ) : null}
              {!isReal && (panelTab === "findings" || panelTab === "summary") ? (
                <RecordBlock sourceType="court" title={t("courtFindings")}>
                  <Link
                    href="/findings/F-DEMO-01"
                    className="text-accent text-[11px] font-semibold"
                  >
                    F-DEMO-01 · Illustrative finding →
                  </Link>
                  <div className="mt-2">
                    <CitationChip citation={courtCitation} />
                  </div>
                </RecordBlock>
              ) : null}
              {!isReal && (panelTab === "people" || panelTab === "mentions") ? (
                <Panel title={tb("researchTabs.people")}>
                  <ul className="space-y-2 text-[11px]">
                    <li>
                      <Link href="/people/demo-research-subject" className="text-accent">
                        Demo Research Subject
                      </Link>
                    </li>
                    <li>
                      <Link href="/witnesses/W01234" className="text-accent identifier">
                        W01234
                      </Link>{" "}
                      · {t("protectedOnly")}
                    </li>
                  </ul>
                </Panel>
              ) : null}
              {!isReal && panelTab === "exhibits" ? (
                <Panel title={t("exhibits")}>
                  <Link
                    href="/documents/P00123?page=4"
                    className="text-accent identifier text-[11px]"
                  >
                    P00123
                  </Link>
                </Panel>
              ) : null}
              {!isReal && panelTab === "citations" ? (
                <Panel title={t("citationStatus")}>
                  <KeyValue
                    rows={[
                      { key: "p", label: tb("citationCounts.produced"), value: 3 },
                      { key: "r", label: tb("citationCounts.resolved"), value: 3 },
                      { key: "u", label: tb("citationCounts.unresolved"), value: 0 },
                    ]}
                  />
                </Panel>
              ) : null}
              <div className="flex flex-wrap gap-2">
                {isReal && document.sourceUrl ? (
                  <ActionLink href={document.sourceUrl}>{t15("officialSource")}</ActionLink>
                ) : null}
                <ActionLink href="/ai">{t("askAi")}</ActionLink>
                <ActionLink href="/appeal/argument/new">{t("addNote")}</ActionLink>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

function TranscriptPage() {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  return (
    <div className="space-y-3 font-serif text-[13px] leading-relaxed">
      <p className="section-label font-sans">{t("examination")} · T. 24</p>
      {[
        [12, "Q", "Generic demo question text."],
        [15, "A", "Generic demo answer given by W01234 in open session."],
      ].map(([line, role, text]) => (
        <p key={String(line)} className="flex gap-3">
          <span className="tabular text-fg-muted w-8 font-sans text-[10px]">{line}</span>
          <strong className="font-sans text-[11px]">{role}</strong>
          <span>{text}</span>
        </p>
      ))}
      <GapNotice
        kind="closed-session"
        reference="T. 25–27"
        extent="3 pages"
        reason={tb("closedSession")}
      />
    </div>
  );
}

// ------------------------------------------------------------ search ------

const CATEGORIES = [
  "people",
  "organizations",
  "witnesses",
  "documents",
  "transcripts",
  "exhibits",
  "incidents",
  "findings",
  "locations",
  "external",
] as const;
type Category = (typeof CATEGORIES)[number];
const PATTERNS: readonly { re: RegExp; kind: string }[] = [
  { re: /^W\d{4,5}$/i, kind: "W#####" },
  { re: /^F\d{4,5}$/i, kind: "F#####" },
  { re: /^P\d{4,5}$/i, kind: "P#####" },
  { re: /^D\d{4,5}$/i, kind: "D#####" },
  { re: /^¶\d+$/, kind: "¶####" },
  { re: /^".+"$/, kind: '"exact phrase"' },
];

export function SearchScreen({
  initialQuery = "",
  initialResults,
  sourceScope = "court",
}: {
  initialQuery?: string;
  initialResults?: readonly MockSearchResult[];
  sourceScope?: "court" | "external" | "both";
}) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const t15 = useTranslations("phase15");
  const t18 = useTranslations("phase18");
  const router = useRouter();
  const [query, setQuery] = useState(initialQuery);
  const [category, setCategory] = useState<Category | "all">("all");
  const [sources, setSources] = useState<Set<SourceType>>(new Set());
  const [page, setPage] = useState(1);
  const results = useMemo(
    () => initialResults ?? mockRepository.search(query),
    [initialResults, query],
  );
  const filtered = results.filter(
    (r) =>
      (category === "all" || r.category === category) &&
      (sources.size === 0 || (r.citation && sources.has(r.citation.sourceType))),
  );
  const pageSize = 12;
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, pageCount);
  const visible = filtered.slice((safePage - 1) * pageSize, safePage * pageSize);
  const groups = CATEGORIES.map((key) => ({
    key,
    rows: visible.filter((r) => r.category === key),
  })).filter((g) => g.rows.length > 0);
  const pattern = PATTERNS.find((p) => p.re.test(query.trim()));
  const activeFilters = [
    ...[...sources].map((s) => ({ id: `src:${s}`, label: `${tb("sourceType")}: ${s}` })),
  ];
  return (
    <AppShell showDemoFlag={initialResults === undefined}>
      <ScreenHeader
        realData={initialResults !== undefined}
        eyebrow={t("search")}
        title={t("search")}
        description={tb("searchSyntax")}
      />
      <form
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          router.push(`/search?q=${encodeURIComponent(query)}&scope=${sourceScope}`);
        }}
        className="border-border-subtle bg-bg-deep border-b px-4 py-3"
      >
        <div className="mx-auto flex w-full max-w-[1440px] flex-wrap gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("commandHint")}
            aria-label={t("searchRecords")}
            className="border-border bg-surface text-fg rounded-inset h-11 min-w-[240px] flex-1 border px-4 text-[13px]"
          />
          <ToolButton primary onClick={() => undefined}>
            {t("search")}
          </ToolButton>
        </div>
        <p className="text-fg-secondary tabular mx-auto mt-2 w-full max-w-[1440px] text-[11px]">
          {tb("resultSummary", { count: filtered.length, groups: groups.length, ms: 3 })}
        </p>
        <div className="mx-auto mt-2 flex w-full max-w-[1440px] gap-2">
          {(["court", "external", "both"] as const).map((scope) => (
            <ActionLink
              key={scope}
              href={`/search?q=${encodeURIComponent(query)}&scope=${scope}`}
              primary={sourceScope === scope}
            >
              {scope === "court"
                ? t15("courtRecord")
                : scope === "external"
                  ? t15("externalSources")
                  : t15("bothSeparated")}
            </ActionLink>
          ))}
        </div>
      </form>
      <TabStrip
        tabs={[
          { key: "all", label: `${tb("allCategories")} (${results.length})` },
          ...CATEGORIES.map((c) => ({
            key: c,
            label: `${c === "external" ? t15("externalSources") : tb(c)} (${results.filter((r) => r.category === c).length})`,
          })),
        ].map((tab) => ({ ...tab, href: undefined }))}
        active={category}
      />
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[238px_minmax(0,1fr)] xl:grid-cols-[238px_minmax(0,1fr)_262px]">
        <FilterRail>
          <FilterSection title={tb("allCategories")}>
            <Segmented
              label={tb("allCategories")}
              value={category}
              onChange={(next) => {
                setCategory(next);
                setPage(1);
              }}
              options={[
                { key: "all", label: tb("allCategories") },
                ...CATEGORIES.map((key) => ({
                  key,
                  label: key === "external" ? t15("externalSources") : tb(key),
                })),
              ]}
            />
          </FilterSection>
          <FilterSection title={tb("sourceType")}>
            {(["court", "witness", "spo", "defence", "exhibit"] as const).map((s) => (
              <FilterOption
                key={s}
                label={s}
                count={results.filter((r) => r.citation?.sourceType === s).length}
                checked={sources.has(s)}
                onChange={(c) => {
                  setPage(1);
                  setSources((prev) => {
                    const n = new Set(prev);
                    if (c) n.add(s);
                    else n.delete(s);
                    return n;
                  });
                }}
              />
            ))}
          </FilterSection>
          <FilterSection title={tb("dateRange")}>
            <div className="flex gap-1">
              <input
                aria-label={tb("from")}
                type="date"
                className="border-border bg-surface rounded-control h-8 min-w-0 flex-1 border px-1 text-[10px]"
              />
              <input
                aria-label={tb("to")}
                type="date"
                className="border-border bg-surface rounded-control h-8 min-w-0 flex-1 border px-1 text-[10px]"
              />
            </div>
          </FilterSection>
        </FilterRail>
        <div className="min-w-0 space-y-3">
          {initialResults === undefined ? <DemoNotice /> : null}
          {initialResults !== undefined ? <NoteStrip>{tb("realDataNotice")}</NoteStrip> : null}
          <ActiveFilters
            filters={activeFilters}
            onRemove={(id) => {
              const [k, v] = id.split(":");
              if (k === "src") {
                setSources((p) => new Set([...p].filter((s) => s !== v)));
                setPage(1);
              }
            }}
            onClearAll={() => {
              setSources(new Set());
              setPage(1);
            }}
          />
          {groups.length === 0 ? (
            <EmptyState
              title={tb("noRecordsMatch")}
              reason={t("searchedVariants")}
              action={
                <ToolButton
                  onClick={() => {
                    setQuery("");
                    setSources(new Set());
                    setCategory("all");
                    setPage(1);
                  }}
                >
                  {tb("allCategories")}
                </ToolButton>
              }
            />
          ) : (
            groups.map((group) => (
              <section
                key={group.key}
                aria-labelledby={`group-${group.key}`}
                className="border-border-subtle bg-surface rounded-card border"
              >
                <header className="border-border-faint flex items-center justify-between border-b px-3 py-1.5">
                  <h2 id={`group-${group.key}`} className="section-label">
                    {group.key === "external" ? t15("externalSources") : tb(group.key)}
                  </h2>
                  <span className="tabular text-fg-muted text-[10px]">{group.rows.length}</span>
                </header>
                {group.rows.map((row) => (
                  <ResultRow key={row.id} row={row} query={query} />
                ))}
              </section>
            ))
          )}
          {filtered.length > pageSize ? (
            <nav aria-label={t18("pagination")} className="flex items-center justify-between gap-3">
              <ToolButton
                onClick={() => setPage((value) => Math.max(1, value - 1))}
                disabled={safePage === 1}
              >
                {t("previous")}
              </ToolButton>
              <span className="tabular text-fg-secondary text-[11px]">
                {t18("pageOf", { page: safePage, total: pageCount })}
              </span>
              <ToolButton
                onClick={() => setPage((value) => Math.min(pageCount, value + 1))}
                disabled={safePage === pageCount}
              >
                {t("next")}
              </ToolButton>
            </nav>
          ) : null}
          <NoteStrip>{tb("rankingDisclaimer")}</NoteStrip>
        </div>
        <aside className="min-w-0 space-y-3 lg:col-span-2 xl:col-span-1">
          <Panel title={t("queryInterpretation")}>
            <KeyValue
              rows={[
                {
                  key: "raw",
                  label: t("search"),
                  value: <span className="identifier">{query || "—"}</span>,
                },
                {
                  key: "as",
                  label: tb("parsedAs"),
                  value: pattern ? `${tb("identifier")} ${pattern.kind}` : tb("freeText"),
                },
              ]}
            />
            <p className="text-fg-secondary mt-2 text-[11px]">
              <span className="section-label">{tb("variants")}</span> {query || "—"}
            </p>
          </Panel>
          <Panel title={tb("syntaxReference")}>
            <ul className="identifier text-fg-secondary space-y-1 text-[11px]">
              {PATTERNS.map((p) => (
                <li key={p.kind}>{p.kind}</li>
              ))}
              <li>free text</li>
            </ul>
          </Panel>
          <Panel title={tb("relatedEntities")}>
            <p className="text-fg-secondary text-[11px]">{t15("sourceBackedOnly")}</p>
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}

function ResultRow({ row, query }: { row: MockSearchResult; query: string }) {
  const t15 = useTranslations("phase15");
  const t18 = useTranslations("phase18");
  const parts = query.trim()
    ? row.context.split(new RegExp(`(${query.trim().replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "i"))
    : [row.context];
  return (
    <Link
      href={row.href}
      className="border-border-faint hover:bg-surface-raised grid gap-x-3 gap-y-1 border-b px-3 py-2 text-[11px] last:border-b-0 sm:grid-cols-[minmax(0,1fr)_auto]"
    >
      <span className="min-w-0 space-y-1">
        <span className="block">
          <span className="section-label block">{t18("whatMatched")}</span>
          <span className="text-fg block font-medium">{row.title}</span>
        </span>
        <span className="text-fg-secondary block leading-relaxed">
          <span className="section-label mr-2">{t18("whereMatched")}</span>
          {parts.map((part, i) =>
            i % 2 === 1 ? (
              <mark key={i} className="bg-surface-high text-fg rounded px-0.5">
                {part}
              </mark>
            ) : (
              <span key={i}>{part}</span>
            ),
          )}
        </span>
        <span className="text-fg-muted block text-[10px]">
          {t18("matchedBy")}
          {row.matchKind ? ` · ${t18(`matchKind.${row.matchKind}`)}` : ""}
        </span>
      </span>
      <span className="flex flex-wrap items-center gap-2 sm:justify-end">
        <span className="section-label">{t18("source")}</span>
        {row.category === "external" ? (
          <span className="rounded-badge border-border bg-surface-raised border px-1.5 py-0.5 text-[10px]">
            {t15("externalSource")}
          </span>
        ) : null}
        {row.citation ? <SourceBadge type={row.citation.sourceType} size="sm" /> : null}
        {row.citation ? <CitationChip citation={row.citation} navigable={false} size="sm" /> : null}
      </span>
    </Link>
  );
}

// ------------------------------------------------------- comparison -------

const LABELS = [
  "possibleContradiction",
  "qualification",
  "timelineDifference",
  "consistent",
  "notComparable",
] as const;
const TOPICS = [
  { id: "t1", label: "Demo topic: location on the stated date", label2: "possibleContradiction" },
  { id: "t2", label: "Demo topic: persons present", label2: "consistent" },
  { id: "t3", label: "Demo topic: sequence of events", label2: "notComparable" },
] as const;

export function StatementComparisonScreen({ code }: { code: string }) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const [topic, setTopic] = useState(0);
  const [label, setLabel] = useState<(typeof LABELS)[number]>(TOPICS[0].label2);
  const [reviewed, setReviewed] = useState(false);
  const [column, setColumn] = useState<"A" | "B" | "C">("B");
  const current = TOPICS[topic]!;
  const columns = [
    {
      key: "A" as const,
      title: tb("columnA"),
      source: "witness" as const,
      excerpt: current.id === "t3" ? null : "Generic prior public statement excerpt (demo).",
      elapsed: "≈ 2 years",
    },
    {
      key: "B" as const,
      title: tb("columnB"),
      source: "witness" as const,
      excerpt: "Generic trial testimony excerpt given in open session (demo).",
      elapsed: null,
    },
    {
      key: "C" as const,
      title: tb("columnC"),
      source: "defence" as const,
      excerpt: "Generic cross-examination excerpt (demo).",
      elapsed: null,
    },
  ];
  return (
    <AppShell
      crumbs={[
        { label: tb("witnesses"), href: "/witnesses" },
        { label: code, href: `/witnesses/${code}` },
        { label: t("statementComparison") },
      ]}
    >
      <ScreenHeader
        eyebrow={<span className="identifier">{code}</span>}
        title={t("statementComparison")}
        description={t("comparisonNeutral")}
        actions={<ActionLink href={`/witnesses/${code}`}>{t("testimony")}</ActionLink>}
      />
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[246px_minmax(0,1fr)] xl:grid-cols-[246px_minmax(0,1fr)_264px]">
        <aside className="min-w-0 space-y-3">
          <Panel title={tb("topics")}>
            <ol className="space-y-1">
              {TOPICS.map((tp, i) => (
                <li key={tp.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setTopic(i);
                      setLabel(tp.label2);
                      setReviewed(false);
                    }}
                    aria-current={i === topic ? "true" : undefined}
                    className={`rounded-control w-full px-2 py-1.5 text-left text-[11px] ${i === topic ? "bg-surface-high text-fg" : "text-fg-secondary"}`}
                  >
                    {tp.label}
                    <span className="text-fg-muted block text-[10px]">{t(tp.label2)}</span>
                  </button>
                </li>
              ))}
            </ol>
          </Panel>
          <ProtectionNotice />
        </aside>
        <div className="min-w-0 space-y-3">
          <DemoNotice />
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-fg text-[13px] font-semibold">{current.label}</h2>
            <div className="flex items-center gap-1">
              <ToolButton
                onClick={() => setTopic((v) => Math.max(0, v - 1))}
                ariaLabel={t("previous")}
              >
                ‹
              </ToolButton>
              <span className="tabular text-fg-secondary text-[11px]">
                {tb("stepSegment", { n: topic + 1, total: TOPICS.length })}
              </span>
              <ToolButton
                onClick={() => setTopic((v) => Math.min(TOPICS.length - 1, v + 1))}
                ariaLabel={t("next")}
              >
                ›
              </ToolButton>
            </div>
          </div>
          <div className="md:hidden">
            <Segmented
              label={tb("topics")}
              value={column}
              onChange={setColumn}
              options={[
                { key: "A", label: "A" },
                { key: "B", label: "B" },
                { key: "C", label: "C" },
              ]}
            />
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {columns.map((col) => (
              <div key={col.key} className={col.key === column ? "" : "max-md:hidden"}>
                <RecordBlock sourceType={col.source} title={col.title}>
                  <p className="text-fg-muted tabular text-[10px]">
                    {col.key === "A" ? "2022-03-01" : "2024-05-14"}
                    {col.elapsed ? ` · ${tb("elapsed")}: ${col.elapsed}` : ""}
                  </p>
                  {col.excerpt ? (
                    <p className="text-fg-body mt-2 font-serif text-[12.5px] leading-relaxed">
                      {col.key === "B" ? (
                        <>
                          <mark className="bg-surface-high rounded px-0.5">
                            {col.excerpt.slice(0, 30)}
                          </mark>
                          {col.excerpt.slice(30)}
                        </>
                      ) : (
                        col.excerpt
                      )}
                    </p>
                  ) : (
                    <p className="text-fg-secondary mt-2 text-[11px] italic">{tb("silent")}</p>
                  )}
                  <div className="mt-2">
                    <CitationChip citation={transcriptCitation} size="sm" />
                  </div>
                </RecordBlock>
              </div>
            ))}
          </div>
          <AiAnalysisBlock title={tb("aiBand")} citations={[transcriptCitation]}>
            {
              "Demo comparison note: the three excerpts differ in wording about the location; the system reports the difference and makes no assessment of the witness."
            }
          </AiAnalysisBlock>
          <SectionCard title={tb("reviewBar")}>
            <div className="flex flex-wrap items-center gap-2">
              <Segmented
                label={tb("reviewBar")}
                value={label}
                onChange={setLabel}
                options={LABELS.map((l) => ({ key: l, label: t(l) }))}
              />
              <ToolButton primary={!reviewed} pressed={reviewed} onClick={() => setReviewed(true)}>
                {reviewed ? tb("reviewed") : tb("markReviewed")}
              </ToolButton>
              <span className="text-fg-muted text-[10px]">{t("humanReview")}</span>
            </div>
          </SectionCard>
        </div>
        <aside className="min-w-0 space-y-3 lg:col-span-2 xl:col-span-1">
          <Panel title={tb("labelLegend")}>
            <ul className="space-y-1 text-[11px]">
              {LABELS.map((l) => (
                <li key={l} className="text-fg-secondary">
                  {t(l)}
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title={tb("languageRules")}>
            <p className="text-fg-secondary text-[11px]">{tb("languageRule1")}</p>
            <p className="text-fg-secondary mt-1 text-[11px]">{tb("languageRule2")}</p>
          </Panel>
          <RecordBlock sourceType="court" title={tb("courtCredibility")}>
            <p className="text-fg-body font-serif text-[12px] leading-relaxed">
              “Generic demo wording of a Chamber assessment, quoted verbatim.”
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <CitationChip citation={courtCitation} size="sm" />
              <VerificationBadge state="verified" size="sm" />
            </div>
            <p className="text-fg-muted mt-2 text-[10px]">{tb("chamberAssessment")}</p>
          </RecordBlock>
          <Panel title={t("priorStatements")}>
            <p className="text-fg-secondary text-[11px]">{tb("noPriorStatement")}</p>
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}
