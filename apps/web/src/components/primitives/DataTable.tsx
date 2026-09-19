"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export type Density = "compact" | "comfortable";

export interface Column<Row> {
  key: string;
  header: ReactNode;
  /** Right-aligned and tabular (DESIGN_SYSTEM.md §3). */
  numeric?: boolean;
  /** Identifier columns are source-coloured and 600 weight. */
  identifier?: boolean;
  /** Minimum width, set from the longest translation, never the English string. */
  minWidth?: number;
  sortable?: boolean;
  cell: (row: Row) => ReactNode;
}

export interface DataTableProps<Row> {
  columns: readonly Column<Row>[];
  rows: readonly Row[];
  rowKey: (row: Row) => string;
  rowLabel?: (row: Row) => string;
  density?: Density;
  /** Column key, prefixed with "-" for descending (ROUTE_MAP.md `sort`). */
  sortBy?: string;
  onSort?: (key: string) => void;
  selectedId?: string;
  onSelect?: (row: Row) => void;
  /** Source-coloured 3px left border on the selected row. */
  selectedAccentClass?: string;
  caption?: string;
  className?: string;
}

/**
 * Header 28–30px on `--bg-deep` with 9px uppercase labels. Rows 32px compact /
 * 44px comfortable, separated by `--border-faint`. Selected row `--surface-high`
 * with a 3px source-coloured left border (COMPONENTS.md §3).
 *
 * Sort is by record attribute only. No relevance, severity or significance
 * sort is ever offered here (HANDOFF.md §6).
 */
export function DataTable<Row>({
  columns,
  rows,
  rowKey,
  rowLabel,
  density = "compact",
  sortBy,
  onSort,
  selectedId,
  onSelect,
  selectedAccentClass = "border-l-accent",
  caption,
  className,
}: DataTableProps<Row>) {
  const t = useTranslations("table");
  const sortKey = sortBy?.replace(/^-/, "");
  const sortDesc = sortBy?.startsWith("-") ?? false;
  const compact = density === "compact";

  return (
    <div className={cn("w-full overflow-x-auto", className)}>
      <table data-density={density} className="w-full border-collapse text-left">
        {caption ? <caption className="sr-only">{caption}</caption> : null}
        <thead>
          <tr className="bg-bg-deep h-7">
            {columns.map((col) => {
              const isSorted = sortKey === col.key;
              const ariaSort = isSorted ? (sortDesc ? "descending" : "ascending") : undefined;
              const header = (
                <span className="inline-flex items-center gap-1">
                  {col.header}
                  {isSorted ? <span aria-hidden>{sortDesc ? "↓" : "↑"}</span> : null}
                </span>
              );
              return (
                <th
                  key={col.key}
                  scope="col"
                  aria-sort={ariaSort}
                  style={col.minWidth ? { minWidth: col.minWidth } : undefined}
                  className={cn(
                    "text-fg-muted px-2 text-[9px] font-semibold tracking-[0.1em] uppercase",
                    col.numeric && "text-right",
                  )}
                >
                  {col.sortable && onSort ? (
                    <button
                      type="button"
                      onClick={() => onSort(isSorted && !sortDesc ? `-${col.key}` : col.key)}
                      className="rounded-control hover:text-fg inline-flex items-center gap-1"
                      aria-label={t("sortBy", { column: String(col.header) })}
                    >
                      {header}
                    </button>
                  ) : (
                    header
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="text-fg-muted px-2 py-3 text-[11px]">
                {t("empty")}
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const id = rowKey(row);
              const selected = selectedId === id;
              return (
                <tr
                  key={id}
                  data-row-id={id}
                  aria-selected={onSelect ? selected : undefined}
                  onClick={onSelect ? () => onSelect(row) : undefined}
                  className={cn(
                    "border-border-faint border-b border-l-[3px] border-l-transparent",
                    compact ? "h-8 text-[11px] leading-none" : "h-11 text-[12px]",
                    onSelect && "hover:bg-surface-raised cursor-pointer",
                    selected && cn("bg-surface-high", selectedAccentClass),
                  )}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        "text-fg-body px-2",
                        compact ? "py-0" : "py-1.5",
                        col.numeric && "tabular text-right",
                        col.identifier && "identifier",
                      )}
                    >
                      {col.cell(row)}
                    </td>
                  ))}
                  {onSelect && rowLabel ? (
                    <td className="sr-only">
                      <button type="button" onClick={() => onSelect(row)} tabIndex={-1}>
                        {t("selectRow", { label: rowLabel(row) })}
                      </button>
                    </td>
                  ) : null}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

/** Compact / Comfortable. Persisted per table, not globally (COMPONENTS.md §3). */
export function DensityToggle({
  value,
  onChange,
  className,
}: {
  value: Density;
  onChange: (next: Density) => void;
  className?: string;
}) {
  const t = useTranslations("table");
  return (
    <div
      role="radiogroup"
      aria-label={t("density")}
      className={cn(
        "rounded-control border-border bg-surface-raised inline-flex border p-0.5",
        className,
      )}
    >
      {(["compact", "comfortable"] as const).map((d) => (
        <button
          key={d}
          type="button"
          role="radio"
          aria-checked={value === d}
          onClick={() => onChange(d)}
          className={cn(
            "rounded-[5px] px-2 py-0.5 text-[10.5px] font-medium",
            value === d ? "bg-surface-high text-fg" : "text-fg-secondary hover:text-fg",
          )}
        >
          {t(d)}
        </button>
      ))}
    </div>
  );
}
