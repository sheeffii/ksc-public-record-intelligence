"use client";

import type { VerificationState } from "@ksc/shared";
import type { MockDirectory, MockDirectoryRow } from "@/mock";
import { mockRepository } from "@/mock";
import { useTranslations } from "next-intl";
import Link from "next/link";
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
import { CitationChip, SourceBadge, VerificationBadge } from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { courtCitation, exhibitCitation } from "@/mock";
import { ActionLink, DemoNotice, ScreenHeader } from "./ScreenChrome";
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
}: {
  kind: MockDirectory;
  screenTitle: string;
}) {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const tTable = useTranslations("table");
  const tFooter = useTranslations("footer");
  const [query, setQuery] = useState("");
  const [density, setDensity] = useState<Density>("compact");
  const [sortBy, setSortBy] = useState(kind === "findings" ? "id" : "title");
  const [states, setStates] = useState<Set<VerificationState>>(new Set());
  const [protectedOnly, setProtectedOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [selectedId, setSelectedId] = useState<string>();

  const all = useMemo(() => mockRepository.getDirectory(kind), [kind]);
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
    const head = ["id", "title", "date", "references", "verification", "citation"];
    const lines = rows.map((r) =>
      [r.id, r.title, r.date, r.references, r.verification, courtCitation.display]
        .map((v) => `"${String(v).replaceAll('"', '""')}"`)
        .join(","),
    );
    return `data:text/csv;charset=utf-8,${encodeURIComponent([head.join(","), ...lines].join("\n"))}`;
  }, [rows]);

  const columns: readonly Column<MockDirectoryRow>[] = [
    {
      key: "id",
      header: kind === "exhibits" ? tb("exhibitColumns.id") : "ID",
      identifier: true,
      minWidth: 120,
      sortable: true,
      cell: (row) => <span className="text-accent">{row.id}</span>,
    },
    {
      key: "title",
      header: screenTitle,
      minWidth: 200,
      sortable: true,
      cell: (row) => <span className="text-fg font-medium">{row.title}</span>,
    },
    {
      key: "description",
      header: tb("exhibitColumns.description"),
      minWidth: 240,
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

  return (
    <AppShell footer={tFooter("referenceCounts")}>
      <ScreenHeader
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
            download={`${kind}-demo.csv`}
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
          <DemoNotice />
          <Panel
            padded={false}
            footer={kind === "exhibits" ? tb("columnMeaning") : tTable("columnNote")}
          >
            {visible.length === 0 ? (
              <div className="p-4">
                <EmptyState
                  title={tb("noMatch")}
                  reason={tb("noMatchReason")}
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
                <SourceBadge
                  type={
                    kind === "exhibits" ? "exhibit" : kind === "witnesses" ? "witness" : "court"
                  }
                />
                <h2 className="identifier text-fg mt-2 text-[14px] font-semibold">
                  {selected.title}
                </h2>
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
                      {
                        key: "ver",
                        label: tb("verification"),
                        value: <VerificationBadge state={selected.verification} size="sm" />,
                      },
                    ]}
                  />
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <CitationChip citation={kind === "exhibits" ? exhibitCitation : courtCitation} />
                  <ActionLink href={selected.href} primary>
                    {selected.protected ? t("open") : tb("openFullDocument")}
                  </ActionLink>
                </div>
              </>
            ) : null}
          </Panel>
          <Panel title={tb("preview")}>
            <p className="text-fg-body font-serif text-[12px] leading-relaxed">
              {selected?.protected ? t("protectedOnly") : selected?.description}
            </p>
          </Panel>
          <Panel title={tb("linkedRecords")}>
            <ul className="space-y-1 text-[11px]">
              <li>
                <Link className="text-accent" href="/witnesses/W01234">
                  W01234
                </Link>{" "}
                · {t("testimony")}
              </li>
              <li>
                <Link className="text-accent" href="/incidents/I-DEMO-01">
                  I-DEMO-01
                </Link>{" "}
                · {t("incidents")}
              </li>
              <li>
                <Link className="text-accent" href="/findings/F-DEMO-01">
                  F-DEMO-01
                </Link>{" "}
                · {t("courtFindings")}
              </li>
            </ul>
          </Panel>
          <NoteStrip>{t("resultOrdering")}</NoteStrip>
        </aside>
      </div>
    </AppShell>
  );
}
