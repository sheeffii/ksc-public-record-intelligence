"use client";

import type { SourceType, VerificationState } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ActiveFilters,
  FilterOption,
  FilterRail,
  FilterSection,
} from "@/components/primitives/Filter";
import { Panel } from "@/components/primitives/Panel";
import { EmptyState, GapNotice } from "@/components/primitives/States";
import {
  AiAnalysisBlock,
  CitationChip,
  ProtectionNotice,
  RecordBlock,
  SourceBadge,
  VerificationBadge,
} from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { courtCitation, mockRepository, transcriptCitation, type MockSearchResult } from "@/mock";
import { ActionLink, DemoNotice, ScreenHeader, TabStrip } from "./ScreenChrome";
import { KeyValue, NoteStrip, SectionCard, Segmented, ToolButton, Toolbar } from "./Workspace";

// ------------------------------------------------------------ reader ------

const TOC = [
  { id: "intro", label: "I. Introduction", page: 1 },
  { id: "procedural", label: "II. Procedural history", page: 4 },
  { id: "findings", label: "III. Findings", page: 12 },
  { id: "disposition", label: "IV. Disposition", page: 48 },
];

export function DocumentReaderScreen({ id }: { id: string }) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const document = mockRepository.getDocument(id);
  const isTranscript = id.startsWith("T-");
  const [page, setPage] = useState(document.page);
  const [panelTab, setPanelTab] = useState<
    "summary" | "mentions" | "people" | "exhibits" | "findings" | "citations"
  >("summary");
  const [inDoc, setInDoc] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const total = 52;
  const paragraphs = document.paragraphs.filter(
    (p) => !inDoc || p.text.toLowerCase().includes(inDoc.toLowerCase()),
  );
  const panelTabs = ["summary", "mentions", "people", "exhibits", "findings", "citations"] as const;

  return (
    <AppShell
      mode="light"
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
            <ToolButton
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              ariaLabel={t("previous")}
            >
              ‹
            </ToolButton>
            <span className="tabular text-fg-secondary px-1 text-[11px]">
              {tb("pager", { n: page, total })}
            </span>
            <ToolButton
              onClick={() => setPage((p) => Math.min(total, p + 1))}
              ariaLabel={t("next")}
            >
              ›
            </ToolButton>
            <ToolButton onClick={() => navigator.clipboard?.writeText(document.citation.display)}>
              {t("copyCitation")}
            </ToolButton>
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
                    value: <span className="tabular">2024-01-15</span>,
                  },
                  {
                    key: "filing",
                    label: tb("docMeta.filingDate"),
                    value: <span className="tabular">2024-01-16</span>,
                  },
                  {
                    key: "pages",
                    label: tb("docMeta.pages"),
                    value: <span className="tabular">{total}</span>,
                  },
                  { key: "lang", label: tb("docMeta.language"), value: document.language },
                  { key: "version", label: tb("docMeta.version"), value: "RED" },
                  { key: "public", label: tb("docMeta.publicState"), value: tb("redactedVersion") },
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
            <Panel title={tb("docMeta.version")}>
              <ul className="space-y-1 text-[11px]">
                <li className="identifier text-fg">{document.id}/RED</li>
                <li className="identifier text-fg-muted">
                  {document.id} · {tb("notAvailable")}
                </li>
              </ul>
            </Panel>
          </aside>
          <div className="bg-surface-alt flex min-w-0 justify-center overflow-x-auto p-3 md:p-6">
            <article className="shadow-page bg-surface text-fg-body min-h-[760px] w-full max-w-[600px] px-6 py-8 md:px-[60px] md:py-[52px]">
              <div className="border-court bg-surface-raised text-fg rounded-card mb-4 border-l-2 px-3 py-2 text-[11px]">
                {tb("citedBanner", { ref: "F-DEMO-01" })} ·{" "}
                <Link href="/findings/F-DEMO-01" className="text-accent font-semibold">
                  {t("courtFindings")} →
                </Link>
              </div>
              <p className="identifier text-fg-muted mb-4 text-[10px]">
                {document.id} · {t("page")} {page}
              </p>
              {isTranscript ? (
                <TranscriptPage />
              ) : page === 2 ? (
                <GapNotice
                  kind="redaction"
                  reference={`${document.id}/RED`}
                  extent="p. 2, 2 lines"
                  reason={tb("redactedPage")}
                />
              ) : (
                paragraphs.map((paragraph) => (
                  <p
                    key={paragraph.number}
                    id={`para-${paragraph.number}`}
                    className="group relative mb-4 scroll-mt-24 pl-10 font-serif text-[13.5px] leading-[1.75] max-md:pl-8 max-md:text-[11.5px] max-md:leading-[1.85] md:text-[14px]"
                  >
                    <a
                      href={`#para-${paragraph.number}`}
                      className="tabular text-fg-muted group-hover:text-accent absolute top-0.5 left-0 text-[10px]"
                    >
                      ¶{paragraph.number}
                    </a>
                    {paragraph.text}
                  </p>
                ))
              )}
              <section className="border-border-faint mt-8 border-t pt-3">
                <h3 className="section-label mb-1">{tb("footnotes")}</h3>
                <p className="text-fg-secondary text-[10.5px] leading-relaxed">
                  1. Demo footnote; cites <CitationChip citation={transcriptCitation} size="sm" />.
                </p>
              </section>
            </article>
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
              {panelTab === "summary" ? (
                <AiAnalysisBlock citations={[courtCitation]}>
                  {"Demo AI summary of the sample document. Analysis only — never the record."}
                </AiAnalysisBlock>
              ) : null}
              {panelTab === "findings" || panelTab === "summary" ? (
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
              {panelTab === "people" || panelTab === "mentions" ? (
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
              {panelTab === "exhibits" ? (
                <Panel title={t("exhibits")}>
                  <Link
                    href="/documents/P00123?page=4"
                    className="text-accent identifier text-[11px]"
                  >
                    P00123
                  </Link>
                </Panel>
              ) : null}
              {panelTab === "citations" ? (
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
  "witnesses",
  "documents",
  "transcripts",
  "exhibits",
  "incidents",
  "findings",
  "locations",
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

export function SearchScreen({ initialQuery = "" }: { initialQuery?: string }) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const [query, setQuery] = useState(initialQuery);
  const [category, setCategory] = useState<Category | "all">("all");
  const [sources, setSources] = useState<Set<SourceType>>(new Set());
  const [verif, setVerif] = useState<Set<VerificationState>>(new Set());
  const results = useMemo(() => mockRepository.search(query), [query]);
  const filtered = results.filter(
    (r) =>
      (category === "all" || r.category === category) &&
      (sources.size === 0 || (r.citation && sources.has(r.citation.sourceType))) &&
      (verif.size === 0 || verif.has("verified")),
  );
  const groups = CATEGORIES.map((key) => ({
    key,
    rows: filtered.filter((r) => r.category === key),
  })).filter((g) => g.rows.length > 0);
  const pattern = PATTERNS.find((p) => p.re.test(query.trim()));
  const activeFilters = [
    ...[...sources].map((s) => ({ id: `src:${s}`, label: `${tb("sourceType")}: ${s}` })),
    ...[...verif].map((v) => ({ id: `ver:${v}`, label: `${tb("verification")}: ${v}` })),
  ];

  return (
    <AppShell>
      <ScreenHeader eyebrow={t("search")} title={t("search")} description={tb("searchSyntax")} />
      <form
        role="search"
        onSubmit={(e) => e.preventDefault()}
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
      </form>
      <TabStrip
        tabs={[
          { key: "all", label: `${tb("allCategories")} (${results.length})` },
          ...CATEGORIES.map((c) => ({
            key: c,
            label: `${tb(c)} (${results.filter((r) => r.category === c).length})`,
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
              onChange={setCategory}
              options={[
                { key: "all", label: tb("allCategories") },
                { key: "findings", label: tb("findings") },
                { key: "people", label: tb("people") },
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
                onChange={(c) =>
                  setSources((prev) => {
                    const n = new Set(prev);
                    if (c) n.add(s);
                    else n.delete(s);
                    return n;
                  })
                }
              />
            ))}
          </FilterSection>
          <FilterSection title={tb("verification")}>
            {(["verified", "unreviewed"] as const).map((v) => (
              <FilterOption
                key={v}
                label={v}
                count={v === "verified" ? results.length : 0}
                checked={verif.has(v)}
                onChange={(c) =>
                  setVerif((prev) => {
                    const n = new Set(prev);
                    if (c) n.add(v);
                    else n.delete(v);
                    return n;
                  })
                }
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
          <DemoNotice />
          <ActiveFilters
            filters={activeFilters}
            onRemove={(id) => {
              const [k, v] = id.split(":");
              if (k === "src") setSources((p) => new Set([...p].filter((s) => s !== v)));
              else setVerif((p) => new Set([...p].filter((s) => s !== v)));
            }}
            onClearAll={() => {
              setSources(new Set());
              setVerif(new Set());
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
                    setVerif(new Set());
                    setCategory("all");
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
                    {tb(group.key)}
                  </h2>
                  <span className="tabular text-fg-muted text-[10px]">{group.rows.length}</span>
                </header>
                {group.rows.map((row) => (
                  <ResultRow key={row.id} row={row} query={query} />
                ))}
              </section>
            ))
          )}
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
              <span className="section-label">{tb("variants")}</span> Demo location · Fshati Demo ·
              Demo-Village
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
            <ul className="space-y-1 text-[11px]">
              <li>
                <Link href="/people/demo-research-subject" className="text-accent">
                  Demo Research Subject
                </Link>
              </li>
              <li>
                <Link href="/witnesses/W01234" className="text-accent identifier">
                  W01234
                </Link>
              </li>
            </ul>
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}

function ResultRow({ row, query }: { row: MockSearchResult; query: string }) {
  const parts = query.trim()
    ? row.context.split(new RegExp(`(${query.trim().replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "i"))
    : [row.context];
  return (
    <Link
      href={row.href}
      className="border-border-faint hover:bg-surface-raised grid gap-x-3 gap-y-1 border-b px-3 py-2 text-[11px] last:border-b-0 sm:grid-cols-[minmax(0,1fr)_auto]"
    >
      <span className="min-w-0">
        <span className="text-fg block font-medium">{row.title}</span>
        <span className="text-fg-secondary block">
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
      </span>
      <span className="flex flex-wrap items-center gap-2 sm:justify-end">
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
