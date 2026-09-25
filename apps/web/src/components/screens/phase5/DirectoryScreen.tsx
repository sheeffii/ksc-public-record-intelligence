"use client";

import type { VerificationState } from "@ksc/shared";
import type { MockDirectory, MockDirectoryRow } from "@/mock";
import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import {
  DataTable,
  DensityToggle,
  type Column,
  type Density,
} from "@/components/primitives/DataTable";
import {
  ActiveFilters,
  FilterOption,
  FilterRail,
  FilterSection,
} from "@/components/primitives/Filter";
import { Panel } from "@/components/primitives/Panel";
import { EmptyState } from "@/components/primitives/States";
import { CloseIcon, SearchIcon } from "@/components/primitives/icons";
import { SourceBadge, VerificationBadge } from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { cn } from "@/lib/utils";
import { ActionLink, ScreenHeader } from "./ScreenChrome";
import { KeyValue, NoteStrip, Pager, SelectControl, ToolButton, Toolbar } from "./Workspace";

const STATES: readonly VerificationState[] = [
  "verified",
  "unreviewed",
  "needs-evidence",
  "ai-flagged",
  "unresolved",
];
const PAGE_SIZES = [10, 25, 50] as const;

/**
 * Dense table workspace (PAGE_SPECS §10 and the five directory routes built
 * from it): toolbar with counts, search, filters, active chips, density and
 * export; sortable table; detail panel; required column-meaning footer.
 */
export function DirectoryScreen({
  kind,
  screenTitle,
  initialRows = [],
}: {
  kind: MockDirectory;
  screenTitle: string;
  initialRows?: readonly MockDirectoryRow[];
}) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const tTable = useTranslations("table");
  const tFooter = useTranslations("footer");
  const t15 = useTranslations("phase15");
  const t18 = useTranslations("phase18");
  const t21 = useTranslations("phase21");
  const [query, setQuery] = useState("");
  const [density, setDensity] = useState<Density>("compact");
  const [sortBy, setSortBy] = useState(kind === "findings" ? "id" : "title");
  const [states, setStates] = useState<Set<VerificationState>>(new Set());
  const [protectedOnly, setProtectedOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [selectedId, setSelectedId] = useState<string>();
  const [mobileInspectorOpen, setMobileInspectorOpen] = useState(false);

  const all = useMemo(() => initialRows, [initialRows]);
  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = all.filter(
      (row) =>
        (!needle || `${row.id} ${row.title} ${row.description}`.toLowerCase().includes(needle)) &&
        (states.size === 0 || states.has(row.verification)) &&
        (!protectedOnly || row.protected === true),
    );
    const descending = sortBy.startsWith("-");
    const key = sortBy.replace(/^-/, "") as keyof MockDirectoryRow;
    return [...filtered].sort((a, b) => {
      const av = a[key];
      const bv = b[key];
      const cmp =
        typeof av === "number" && typeof bv === "number"
          ? av - bv
          : String(av ?? "").localeCompare(String(bv ?? ""));
      return cmp * (descending ? -1 : 1);
    });
  }, [all, query, states, protectedOnly, sortBy]);
  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  const current = Math.min(page, pageCount);
  const visible = rows.slice((current - 1) * pageSize, current * pageSize);
  const selected = rows.find((r) => r.id === selectedId) ?? visible[0];
  const activeFilters = [
    ...[...states].map((s) => ({ id: `state:${s}`, label: `${tb("verification")}: ${s}` })),
    ...(protectedOnly ? [{ id: "protected", label: tb("protectedOnly") }] : []),
    ...(query ? [{ id: "q", label: `${t("search")}: ${query}` }] : []),
  ];
  function removeFilter(id: string) {
    if (id === "q") setQuery("");
    else if (id === "protected") setProtectedOnly(false);
    else setStates((prev) => new Set([...prev].filter((s) => `state:${s}` !== id)));
    setPage(1);
  }
  const csv = useMemo(() => {
    const head = ["id", "title", "date", "references", "verification", "source_url"];
    const lines = rows.map((r) =>
      [r.id, r.title, r.date, r.references, r.verification, r.href]
        .map((v) => `"${String(v).replaceAll('"', '""')}"`)
        .join(","),
    );
    return `data:text/csv;charset=utf-8,${encodeURIComponent([head.join(","), ...lines].join("\n"))}`;
  }, [rows]);

  const identityColumns: readonly Column<MockDirectoryRow>[] = [
    {
      key: "id",
      header: kind === "exhibits" ? tb("exhibitColumns.id") : t21("identifier"),
      identifier: true,
      minWidth: 100,
      sortable: true,
      cell: (row) => <span className="text-accent-bright">{row.id}</span>,
    },
    {
      key: "title",
      header: screenTitle,
      minWidth: 170,
      sortable: true,
      cell: (row) => (
        <span className="text-fg line-clamp-2 font-medium">
          {kind === "findings" ? (
            <span className="text-court mr-2 text-[9px] font-bold tracking-wide uppercase">
              {t("courtFinding")}
            </span>
          ) : null}
          {row.title}
        </span>
      ),
    },
    {
      key: "description",
      header: tb("exhibitColumns.description"),
      minWidth: 180,
      cell: (row) => row.description,
    },
    {
      key: "date",
      header: tb("exhibitColumns.date"),
      minWidth: 100,
      sortable: true,
      cell: (row) => <span className="tabular">{row.date}</span>,
    },
    {
      key: "references",
      header: kind === "exhibits" ? tb("exhibitColumns.judgment") : t("sourcesUsed"),
      numeric: true,
      sortable: true,
      cell: (row) => row.references,
    },
    {
      key: "verification",
      header: tb("exhibitColumns.verification"),
      minWidth: 150,
      cell: (row) => <VerificationBadge state={row.verification} size="sm" />,
    },
  ];
  const countColumn = (
    key: string,
    header: string,
    value: (row: MockDirectoryRow) => number | undefined,
  ): Column<MockDirectoryRow> => ({
    key,
    header,
    numeric: true,
    minWidth: 90,
    cell: (row) => <span className="tabular">{value(row) ?? 0}</span>,
  });
  const columns: readonly Column<MockDirectoryRow>[] =
    kind === "people"
      ? [
          ...identityColumns.slice(0, 2),
          { ...identityColumns[2]!, header: t18("role") },
          countColumn("documents", t18("documents"), (row) => row.counts?.documentMentions),
          countColumn(
            "transcripts",
            t18("transcriptOccurrences"),
            (row) => row.counts?.transcriptMentions,
          ),
          countColumn("relationships", t18("relationshipCount"), (row) => row.relationshipCount),
        ]
      : kind === "witnesses"
        ? [
            ...identityColumns.slice(0, 2),
            countColumn(
              "transcripts",
              t18("testimonyOccurrences"),
              (row) => row.counts?.transcriptMentions,
            ),
            countColumn("documents", t18("relatedFilings"), (row) => row.counts?.documentMentions),
            countColumn("relationships", t18("relationshipCount"), (row) => row.relationshipCount),
          ]
        : kind === "exhibits"
          ? [
              ...identityColumns.slice(0, 3),
              {
                key: "status",
                header: t18("status"),
                minWidth: 120,
                cell: (row) => (
                  <span className="rounded-badge border-border bg-surface-raised text-fg-secondary inline-flex border px-1.5 py-0.5 text-[9px] font-semibold tracking-wide uppercase">
                    {row.status?.toUpperCase() ?? t18("unknown")}
                  </span>
                ),
              },
              {
                key: "witness",
                header: t18("throughWitness"),
                minWidth: 110,
                cell: (row) => (
                  <span className="identifier text-witness">{row.relatedWitness ?? "—"}</span>
                ),
              },
              countColumn(
                "documents",
                t18("documentOccurrences"),
                (row) => row.counts?.documentMentions,
              ),
            ]
          : kind === "findings"
            ? [
                ...identityColumns.slice(0, 2),
                {
                  ...identityColumns[2]!,
                  header: t18("findingSummary"),
                  cell: (row) => (
                    <span className="line-clamp-3 leading-relaxed">{row.description}</span>
                  ),
                },
                identityColumns[4]!,
                identityColumns[5]!,
              ]
            : identityColumns;

  const usesResearchExplorer = [
    "documents",
    "exhibits",
    "people",
    "witnesses",
    "findings",
  ].includes(kind);

  if (usesResearchExplorer) {
    return (
      <AppShell footer={tFooter("referenceCounts")}>
        <div className="border-border-subtle bg-bg-deep flex min-h-[52px] flex-wrap items-center gap-2 border-b px-4 py-2">
          <div className="mr-2 min-w-[190px]">
            <div className="flex items-baseline gap-2">
              <h1 className="text-fg text-[19px] font-bold tracking-[-0.02em]">{screenTitle}</h1>
              <span className="text-fg-secondary tabular text-[10.5px]">
                {t21("corpusCount", { count: all.length })}
              </span>
              <span className="sr-only">
                {tb("rowsShown", {
                  from: rows.length ? (current - 1) * pageSize + 1 : 0,
                  to: Math.min(current * pageSize, rows.length),
                  total: rows.length,
                })}
              </span>
            </div>
          </div>
          <label className="relative min-w-[220px] flex-1 xl:max-w-[420px]">
            <span className="sr-only">{t("searchRecords")}</span>
            <SearchIcon
              size={14}
              className="text-fg-muted pointer-events-none absolute top-1/2 left-3 -translate-y-1/2"
            />
            <input
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              type="search"
              placeholder={t("searchRecords")}
              className="border-border bg-surface text-fg rounded-control h-8 w-full border pr-3 pl-9 text-[11px]"
            />
          </label>
          <label className="text-fg-secondary inline-flex items-center gap-1 text-[10.5px]">
            <span className="sr-only">{tb("verification")}</span>
            <select
              value={[...states][0] ?? "all"}
              onChange={(event) => {
                setStates(
                  event.target.value === "all"
                    ? new Set()
                    : new Set([event.target.value as VerificationState]),
                );
                setPage(1);
              }}
              className="border-border bg-surface-raised text-fg rounded-control h-8 border px-2"
            >
              <option value="all">{tb("allCategories")}</option>
              {STATES.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
          </label>
          {kind === "witnesses" ? (
            <label className="border-border bg-surface-raised text-fg-secondary rounded-control inline-flex h-8 items-center gap-2 border px-2 text-[10.5px]">
              <input
                type="checkbox"
                checked={protectedOnly}
                onChange={(event) => {
                  setProtectedOnly(event.target.checked);
                  setPage(1);
                }}
              />
              {tb("protectedOnly")}
            </label>
          ) : null}
          <DensityToggle value={density} onChange={setDensity} />
          <a
            href={csv}
            download={`${kind}.csv`}
            className="border-border bg-surface-raised text-fg rounded-control inline-flex h-8 items-center border px-3 text-[10.5px]"
          >
            {tb("exportCsv")}
          </a>
          {activeFilters.length ? (
            <ActiveFilters
              className="basis-full"
              filters={activeFilters}
              onRemove={removeFilter}
              onClearAll={() => {
                setQuery("");
                setStates(new Set());
              }}
            />
          ) : null}
        </div>

        <div className="grid min-h-[calc(100dvh-168px)] min-w-0 flex-1 xl:grid-cols-[minmax(0,1fr)_376px]">
          <section className="border-border-subtle min-w-0 border-r" aria-label={screenTitle}>
            {visible.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  title={tb("noMatch")}
                  reason={query || states.size ? t15("noFilteredRecords") : t15(`empty.${kind}`)}
                  action={
                    <ToolButton
                      onClick={() => {
                        setQuery("");
                        setStates(new Set());
                      }}
                    >
                      {tTable("empty")}
                    </ToolButton>
                  }
                />
              </div>
            ) : (
              <DataTable
                columns={columns}
                rows={visible}
                rowKey={(row) => row.id}
                rowLabel={(row) => row.title}
                density={density}
                sortBy={sortBy}
                onSort={(key) => {
                  setSortBy(key);
                  setPage(1);
                }}
                selectedId={selected?.id}
                selectedAccentClass={
                  kind === "exhibits"
                    ? "border-l-doc"
                    : kind === "witnesses"
                      ? "border-l-witness"
                      : kind === "findings"
                        ? "border-l-court"
                        : "border-l-accent"
                }
                onSelect={(row) => {
                  setSelectedId(row.id);
                  setMobileInspectorOpen(true);
                }}
              />
            )}
            <div className="border-border-subtle mt-auto border-t">
              <Pager
                page={current}
                pageCount={pageCount}
                onChange={setPage}
                prevLabel={tb("prevPage")}
                nextLabel={tb("nextPage")}
                summary={tb("rowsShown", {
                  from: rows.length ? (current - 1) * pageSize + 1 : 0,
                  to: Math.min(current * pageSize, rows.length),
                  total: rows.length,
                })}
              />
              <p className="governance-text border-border-faint border-t px-3 py-1.5">
                {kind === "exhibits" ? tb("columnMeaning") : tTable("columnNote")}
              </p>
            </div>
          </section>

          <aside
            aria-label={t21("selectedRecord")}
            className={cn(
              "border-border-subtle bg-surface min-w-0 border-l",
              mobileInspectorOpen
                ? "rounded-card shadow-sheet fixed inset-x-3 top-[92px] bottom-16 z-40 block overflow-y-auto border"
                : "hidden",
              "xl:static xl:z-auto xl:block xl:overflow-visible xl:rounded-none xl:border-y-0 xl:border-r-0 xl:shadow-none",
            )}
          >
            <div className="border-border-subtle flex min-h-12 items-start justify-between gap-3 border-b px-4 py-3">
              <div>
                <p className="section-label">{t21("selectedRecord")}</p>
                {selected ? (
                  <p
                    className={cn(
                      "identifier mt-1 text-[16px]",
                      kind === "exhibits"
                        ? "text-doc"
                        : kind === "witnesses"
                          ? "text-witness"
                          : kind === "findings"
                            ? "text-court"
                            : "text-accent",
                    )}
                  >
                    {selected.id}
                  </p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => setMobileInspectorOpen(false)}
                aria-label={t21("closeInspector")}
                className="border-border text-fg-secondary rounded-control inline-flex size-8 items-center justify-center border xl:hidden"
              >
                <CloseIcon size={14} />
              </button>
            </div>
            {selected ? (
              <div className="space-y-5 p-4">
                <div>
                  {kind === "exhibits" ? <SourceBadge type="exhibit" /> : null}
                  {kind === "witnesses" ? <SourceBadge type="witness" /> : null}
                  {kind === "findings" ? <SourceBadge type="court" /> : null}
                  <h2 className="text-fg mt-2 text-[14px] leading-snug font-semibold">
                    {selected.title}
                  </h2>
                  <p className="text-fg-secondary mt-1 text-[11px] leading-relaxed">
                    {selected.description}
                  </p>
                </div>
                <section>
                  <h3 className="section-label mb-2">{t("metadata")}</h3>
                  <KeyValue
                    rows={[
                      {
                        key: "id",
                        label: t21("identifier"),
                        value: <span className="identifier">{selected.id}</span>,
                      },
                      {
                        key: "date",
                        label: t21("recordDate"),
                        value: <span className="tabular">{selected.date}</span>,
                      },
                      ...(selected.status
                        ? [
                            {
                              key: "status",
                              label: t21("recordStatus"),
                              value: selected.status.toUpperCase(),
                            },
                          ]
                        : []),
                      ...(selected.party
                        ? [{ key: "party", label: t18("tenderedBy"), value: selected.party }]
                        : []),
                      ...(selected.relatedWitness
                        ? [
                            {
                              key: "witness",
                              label: t18("throughWitness"),
                              value: (
                                <span className="identifier text-witness">
                                  {selected.relatedWitness}
                                </span>
                              ),
                            },
                          ]
                        : []),
                      {
                        key: "refs",
                        label: kind === "exhibits" ? t18("documentOccurrences") : t("sourcesUsed"),
                        value: <span className="tabular">{selected.references}</span>,
                      },
                      ...(selected.counts
                        ? [
                            {
                              key: "documents",
                              label: t18("documentOccurrences"),
                              value: (
                                <span className="tabular">
                                  {selected.counts.documentMentions ?? 0}
                                </span>
                              ),
                            },
                            {
                              key: "transcripts",
                              label: t18("testimonyOccurrences"),
                              value: (
                                <span className="tabular">
                                  {selected.counts.transcriptMentions ?? 0}
                                </span>
                              ),
                            },
                            {
                              key: "relationships",
                              label: t18("openRelationships"),
                              value: (
                                <span className="tabular">{selected.relationshipCount ?? 0}</span>
                              ),
                            },
                          ]
                        : []),
                      {
                        key: "ver",
                        label: tb("verification"),
                        value: <VerificationBadge state={selected.verification} size="sm" />,
                      },
                    ]}
                  />
                </section>
                {selected.status?.toUpperCase() === "UNKNOWN" ? (
                  <NoteStrip>{t18("unknownStatus")}</NoteStrip>
                ) : null}
                <section>
                  <h3 className="section-label mb-2">{tb("linkedRecords")}</h3>
                  <p className="text-fg-secondary text-[11px]">{t15("linkedRecordsUnavailable")}</p>
                </section>
                <ActionLink href={selected.href} primary>
                  {kind === "documents" ? t21("openExactSource") : t21("openDossier")}
                </ActionLink>
              </div>
            ) : (
              <p className="text-fg-secondary p-4 text-[11px]">{t21("selectRecord")}</p>
            )}
          </aside>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell footer={tFooter("referenceCounts")}>
      <ScreenHeader
        realData
        eyebrow={t("allRecords")}
        title={screenTitle}
        description={
          <span className="tabular">
            {tb("rowsShown", {
              from: rows.length ? (current - 1) * pageSize + 1 : 0,
              to: Math.min(current * pageSize, rows.length),
              total: rows.length,
            })}
          </span>
        }
        actions={
          <a
            href={csv}
            download={`${kind}.csv`}
            className="border-border bg-surface-raised text-fg rounded-control inline-flex h-8 items-center border px-3 text-[11px]"
          >
            {tb("exportCsv")}
          </a>
        }
      />
      <Toolbar>
        <label className="min-w-[220px] flex-1">
          <span className="sr-only">{t("searchRecords")}</span>
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            type="search"
            placeholder={t("searchRecords")}
            className="border-border bg-surface text-fg rounded-control h-8 w-full border px-3 text-[12px]"
          />
        </label>
        <DensityToggle value={density} onChange={setDensity} />
        <SelectControl
          label={tb("pageSize")}
          value={String(pageSize)}
          onChange={(v) => {
            setPageSize(Number(v));
            setPage(1);
          }}
          options={PAGE_SIZES.map((n) => ({ key: String(n), label: String(n) }))}
        />
        {kind === "findings" ? <ToolButton pressed>{tb("sortJudgmentOrder")}</ToolButton> : null}
        <ActiveFilters
          filters={activeFilters}
          onRemove={removeFilter}
          onClearAll={() => {
            setQuery("");
            setStates(new Set());
            setProtectedOnly(false);
            setPage(1);
          }}
        />
      </Toolbar>
      <div className="mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4 lg:grid-cols-[200px_minmax(0,1fr)] xl:grid-cols-[200px_minmax(0,1fr)_376px]">
        <FilterRail>
          <FilterSection title={tb("verification")}>
            {STATES.map((s) => (
              <FilterOption
                key={s}
                label={s}
                count={all.filter((r) => r.verification === s).length}
                checked={states.has(s)}
                onChange={(checked) => {
                  setStates((prev) => {
                    const next = new Set(prev);
                    if (checked) next.add(s);
                    else next.delete(s);
                    return next;
                  });
                  setPage(1);
                }}
              />
            ))}
          </FilterSection>
          {kind === "witnesses" ? (
            <FilterSection title={t("protectedOnly")}>
              <FilterOption
                label={tb("protectedOnly")}
                count={all.filter((r) => r.protected).length}
                checked={protectedOnly}
                onChange={(c) => {
                  setProtectedOnly(c);
                  setPage(1);
                }}
              />
            </FilterSection>
          ) : null}
        </FilterRail>
        <div className="flex min-w-0 flex-col gap-3">
          <Panel padded={false} footer={tTable("columnNote")}>
            {visible.length === 0 ? (
              <div className="p-4">
                <EmptyState
                  title={tb("noMatch")}
                  reason={
                    query || states.size || protectedOnly
                      ? t15("noFilteredRecords")
                      : t15(`empty.${kind}`)
                  }
                  action={
                    <ToolButton
                      onClick={() => {
                        setQuery("");
                        setStates(new Set());
                        setProtectedOnly(false);
                      }}
                    >
                      {tTable("empty")}
                    </ToolButton>
                  }
                />
                <ActiveFilters
                  className="mt-3"
                  filters={activeFilters.slice(0, 2)}
                  onRemove={removeFilter}
                />
              </div>
            ) : (
              <DataTable
                columns={columns}
                rows={visible}
                rowKey={(row) => row.id}
                rowLabel={(row) => row.title}
                density={density}
                sortBy={sortBy}
                onSort={(key) => {
                  setSortBy(key);
                  setPage(1);
                }}
                selectedId={selected?.id}
                onSelect={(row) => setSelectedId(row.id)}
              />
            )}
            <Pager
              page={current}
              pageCount={pageCount}
              onChange={setPage}
              prevLabel={tb("prevPage")}
              nextLabel={tb("nextPage")}
              summary={tb("rowsShown", {
                from: rows.length ? (current - 1) * pageSize + 1 : 0,
                to: Math.min(current * pageSize, rows.length),
                total: rows.length,
              })}
            />
          </Panel>
        </div>
        <aside className="min-w-0 space-y-3 lg:col-span-2 xl:col-span-1">
          <Panel title={tb("detail")}>
            {selected ? (
              <>
                {kind !== "people" && kind !== "incidents" ? (
                  <SourceBadge type={kind === "witnesses" ? "witness" : "court"} />
                ) : null}
                <h2 className="text-fg mt-2 text-[14px] font-semibold">{selected.title}</h2>
                <p className="text-fg-secondary mt-1 text-[11px]">{selected.description}</p>
                <div className="mt-3">
                  <KeyValue
                    rows={[
                      {
                        key: "id",
                        label: "ID",
                        value: <span className="identifier">{selected.id}</span>,
                      },
                      {
                        key: "date",
                        label: tb("exhibitColumns.date"),
                        value: <span className="tabular">{selected.date}</span>,
                      },
                      {
                        key: "refs",
                        label: t("sourcesUsed"),
                        value: <span className="tabular">{selected.references}</span>,
                      },
                      ...(selected.status
                        ? [
                            {
                              key: "status",
                              label: t18("status"),
                              value: selected.status,
                            },
                            {
                              key: "party",
                              label: t18("tenderedBy"),
                              value: selected.party ?? "—",
                            },
                            {
                              key: "witness",
                              label: t18("throughWitness"),
                              value: selected.relatedWitness ?? "—",
                            },
                          ]
                        : []),
                      {
                        key: "ver",
                        label: tb("verification"),
                        value: <VerificationBadge state={selected.verification} size="sm" />,
                      },
                    ]}
                  />
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <ActionLink href={selected.href} primary>
                    {t("open")}
                  </ActionLink>
                </div>
              </>
            ) : null}
          </Panel>
          {selected?.status?.toUpperCase() === "UNKNOWN" ? (
            <NoteStrip>{t18("unknownStatus")}</NoteStrip>
          ) : null}
          <Panel title={tb("linkedRecords")}>
            <p className="text-fg-secondary text-[11px]">{t15("linkedRecordsUnavailable")}</p>
          </Panel>
          <NoteStrip>{t("resultOrdering")}</NoteStrip>
        </aside>
      </div>
    </AppShell>
  );
}
