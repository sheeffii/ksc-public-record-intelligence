"use client";

import type { MockDirectory, MockDirectoryRow } from "@/mock";
import { mockRepository } from "@/mock";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import {
  DataTable,
  DensityToggle,
  type Column,
  type Density,
} from "@/components/primitives/DataTable";
import { Panel } from "@/components/primitives/Panel";
import { VerificationBadge } from "@/components/provenance";
import { AppShell } from "@/components/shell/AppShell";
import { DemoNotice, ScreenHeader, WorkspaceGrid } from "./ScreenChrome";

export function DirectoryScreen({
  kind,
  screenTitle,
}: {
  kind: MockDirectory;
  screenTitle: string;
}) {
  const t = useTranslations("phase5");
  const tFooter = useTranslations("footer");
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [density, setDensity] = useState<Density>("compact");
  const [sortBy, setSortBy] = useState("title");
  const rows = useMemo(() => {
    const all = [...mockRepository.getDirectory(kind)];
    const filtered = all.filter((row) =>
      `${row.id} ${row.title} ${row.description}`.toLowerCase().includes(query.toLowerCase()),
    );
    const descending = sortBy.startsWith("-");
    const key = sortBy.replace(/^-/, "") as keyof MockDirectoryRow;
    return filtered.sort(
      (a, b) => String(a[key]).localeCompare(String(b[key])) * (descending ? -1 : 1),
    );
  }, [kind, query, sortBy]);
  const columns: readonly Column<MockDirectoryRow>[] = [
    {
      key: "id",
      header: "ID",
      identifier: true,
      minWidth: 120,
      sortable: true,
      cell: (row) => <span className="text-accent">{row.id}</span>,
    },
    {
      key: "title",
      header: screenTitle,
      minWidth: 210,
      sortable: true,
      cell: (row) => <span className="text-fg font-medium">{row.title}</span>,
    },
    { key: "description", header: t("viewDetails"), minWidth: 260, cell: (row) => row.description },
    { key: "date", header: t("document"), minWidth: 110, sortable: true, cell: (row) => row.date },
    {
      key: "references",
      header: t("sourcesUsed"),
      numeric: true,
      sortable: true,
      cell: (row) => row.references,
    },
    {
      key: "verification",
      header: t("verificationStatus"),
      minWidth: 160,
      cell: (row) => <VerificationBadge state={row.verification} />,
    },
  ];

  return (
    <AppShell footer={tFooter("referenceCounts")}>
      <ScreenHeader eyebrow={t("allRecords")} title={screenTitle} description={t("mockNotice")} />
      <WorkspaceGrid
        right={
          <Panel title={t("viewDetails")}>
            <p className="text-fg-secondary text-[11px]">{rows[0]?.description}</p>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
              <dt className="section-label">ID</dt>
              <dd className="identifier text-fg">{rows[0]?.id}</dd>
              <dt className="section-label">{t("verificationStatus")}</dt>
              <dd>{rows[0] ? <VerificationBadge state={rows[0].verification} /> : null}</dd>
            </dl>
          </Panel>
        }
      >
        <div className="flex flex-col gap-3">
          <DemoNotice />
          <div className="flex flex-wrap items-center gap-2">
            <label className="min-w-[220px] flex-1">
              <span className="sr-only">{t("searchRecords")}</span>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                type="search"
                placeholder={t("searchRecords")}
                className="border-border bg-surface text-fg rounded-control h-9 w-full border px-3 text-[12px]"
              />
            </label>
            <DensityToggle value={density} onChange={setDensity} />
            <button
              type="button"
              className="border-border bg-surface-raised text-fg rounded-control h-8 border px-3 text-[11px]"
            >
              {t("filter")}
            </button>
            <button
              type="button"
              className="border-border bg-surface-raised text-fg rounded-control h-8 border px-3 text-[11px]"
            >
              {t("export")}
            </button>
          </div>
          <Panel padded={false} footer={t("resultOrdering")}>
            <DataTable
              columns={columns}
              rows={rows}
              rowKey={(row) => row.id}
              rowLabel={(row) => row.title}
              density={density}
              sortBy={sortBy}
              onSort={setSortBy}
              onSelect={(row) => router.push(row.href)}
            />
          </Panel>
        </div>
      </WorkspaceGrid>
    </AppShell>
  );
}
