"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { CloseIcon } from "./icons";

export interface FilterChipProps {
  label: string;
  /** Individually removable from the active-chip row (HANDOFF.md §6). */
  onRemove?: () => void;
  className?: string;
}

/** `--surface-raised` chip, 5px radius, with a remove control. */
export function FilterChip({ label, onRemove, className }: FilterChipProps) {
  const t = useTranslations("filters");
  return (
    <span
      className={cn(
        "rounded-chip border-border bg-surface-raised text-fg-body inline-flex min-w-0 items-center gap-1 border px-2 py-0.5 text-[11px]",
        className,
      )}
    >
      <span className="whitespace-normal">{label}</span>
      {onRemove ? (
        <button
          type="button"
          onClick={onRemove}
          aria-label={t("remove", { label })}
          className="rounded-badge text-fg-muted hover:bg-surface-high hover:text-fg -mr-0.5 p-0.5"
        >
          <CloseIcon size={12} />
        </button>
      ) : null}
    </span>
  );
}

export interface ActiveFiltersProps {
  filters: readonly { id: string; label: string }[];
  onRemove: (id: string) => void;
  onClearAll?: () => void;
  className?: string;
}

/** The active-chip row above a table or result list. */
export function ActiveFilters({ filters, onRemove, onClearAll, className }: ActiveFiltersProps) {
  const t = useTranslations("filters");
  if (filters.length === 0) {
    return <p className={cn("text-fg-muted text-[11px]", className)}>{t("none")}</p>;
  }
  return (
    <div className={cn("flex flex-wrap items-center gap-1.5", className)} aria-label={t("active")}>
      {filters.map((f) => (
        <FilterChip key={f.id} label={f.label} onRemove={() => onRemove(f.id)} />
      ))}
      {onClearAll ? (
        <button
          type="button"
          onClick={onClearAll}
          className="text-accent text-[11px] underline-offset-2 hover:underline"
        >
          {t("clearAll")}
        </button>
      ) : null}
    </div>
  );
}

export interface FilterSectionProps {
  title: ReactNode;
  children: ReactNode;
}

export function FilterSection({ title, children }: FilterSectionProps) {
  return (
    <fieldset className="min-w-0 border-0 p-0">
      <legend className="section-label mb-1.5">{title}</legend>
      <div className="flex flex-col gap-1">{children}</div>
    </fieldset>
  );
}

/** Left-rail container: category counts, date range, source type, verification… */
export function FilterRail({ children, className }: { children: ReactNode; className?: string }) {
  const t = useTranslations("filters");
  return (
    <aside aria-label={t("title")} className={cn("flex w-full min-w-0 flex-col gap-4", className)}>
      {children}
    </aside>
  );
}

export interface FilterOptionProps {
  label: ReactNode;
  count?: number | null;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

/** Checkbox row with a right-aligned tabular count. Null count renders a dash, never 0. */
export function FilterOption({ label, count, checked, onChange }: FilterOptionProps) {
  return (
    <label className="rounded-control text-fg-body hover:bg-surface-raised flex min-h-8 cursor-pointer items-center justify-between gap-2 px-1 text-[11.5px]">
      <span className="flex min-w-0 items-center gap-2">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="accent-accent size-3.5"
        />
        <span className="whitespace-normal">{label}</span>
      </span>
      {count !== undefined ? (
        <span className="tabular text-fg-muted shrink-0">{count === null ? "—" : count}</span>
      ) : null}
    </label>
  );
}
