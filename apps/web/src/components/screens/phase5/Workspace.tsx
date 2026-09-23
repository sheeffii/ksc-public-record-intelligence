"use client";

/**
 * Phase 5B building blocks shared by the remediated screens: dense toolbars,
 * scroll-spy rails, stat strips, steppers and note strips. Every colour comes
 * from a token class; every string from the caller.
 */

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Toolbar({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "border-border-subtle bg-bg-deep flex flex-wrap items-center gap-2 border-b px-4 py-2",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function ToolButton({
  children,
  onClick,
  pressed,
  href,
  primary,
  className,
  ariaLabel,
}: {
  children: ReactNode;
  onClick?: () => void;
  pressed?: boolean;
  href?: string;
  primary?: boolean;
  className?: string;
  ariaLabel?: string;
}) {
  const classes = cn(
    "rounded-control inline-flex h-8 min-w-11 items-center justify-center gap-1 border px-2.5 text-[11px] font-medium",
    primary
      ? "border-accent bg-accent text-bg-deep hover:bg-accent-bright"
      : pressed
        ? "border-accent bg-surface-high text-fg"
        : "border-border bg-surface-raised text-fg hover:bg-surface-high",
    className,
  );
  if (href) {
    return (
      <Link href={href} className={classes} aria-label={ariaLabel}>
        {children}
      </Link>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={pressed}
      aria-label={ariaLabel}
      className={classes}
    >
      {children}
    </button>
  );
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
}: {
  options: readonly { key: T; label: string }[];
  value: T;
  onChange: (next: T) => void;
  label: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="border-border rounded-control inline-flex border"
    >
      {options.map((o) => (
        <button
          key={o.key}
          type="button"
          role="radio"
          aria-checked={value === o.key}
          onClick={() => onChange(o.key)}
          className={cn(
            "first:rounded-l-control last:rounded-r-control h-8 min-w-11 px-2.5 text-[11px]",
            value === o.key ? "bg-surface-high text-fg" : "bg-surface-raised text-fg-secondary",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function SelectControl({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (next: string) => void;
  options: readonly { key: string; label: string }[];
}) {
  return (
    <label className="inline-flex items-center gap-1 text-[11px]">
      <span className="text-fg-secondary">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-border bg-surface-raised text-fg rounded-control h-8 border px-2 text-[11px]"
      >
        {options.map((o) => (
          <option key={o.key} value={o.key}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

/** 7-stat row: single row on desktop, 2-up on phones. Counts only. */
export function StatStrip({
  items,
  label,
  disclaimer,
  columns = 7,
}: {
  items: readonly { key: string; label: string; value: ReactNode; href?: string }[];
  label?: string;
  disclaimer?: string;
  /** 7 (single desktop row) or 4 (direction counts); 2 in narrow rails. */
  columns?: 2 | 4 | 7;
}) {
  const grid =
    columns === 7
      ? "grid-cols-2 sm:grid-cols-4 lg:grid-cols-7"
      : columns === 4
        ? "grid-cols-2 sm:grid-cols-4"
        : "grid-cols-2";
  return (
    <section aria-label={label} className="border-border-subtle bg-surface rounded-card border">
      {label ? (
        <div className="border-border-faint flex flex-wrap items-baseline justify-between gap-2 border-b px-3 py-1.5">
          <span className="section-label">{label}</span>
          {disclaimer ? <span className="text-fg-muted text-[10px]">{disclaimer}</span> : null}
        </div>
      ) : null}
      <dl className={cn("grid", grid)}>
        {items.map((item) => {
          const body = (
            <>
              <dd className="tabular text-fg text-[20px] leading-none font-semibold">
                {item.value}
              </dd>
              <dt className="text-fg-secondary mt-1 text-[10px] leading-tight">{item.label}</dt>
            </>
          );
          return (
            <div
              key={item.key}
              className="border-border-faint min-w-0 border-r border-b px-3 py-2 last:border-r-0"
            >
              {item.href ? (
                <Link href={item.href} className="block hover:underline">
                  {body}
                </Link>
              ) : (
                body
              )}
            </div>
          );
        })}
      </dl>
    </section>
  );
}

/** Numbered rail index with scroll-spy over `#id` sections. */
export function RailIndex({
  items,
  label,
  extra,
}: {
  items: readonly { id: string; label: string; number?: string }[];
  label: string;
  extra?: ReactNode;
}) {
  const [active, setActive] = useState(items[0]?.id);
  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-20% 0px -60% 0px" },
    );
    for (const item of items) {
      const el = document.getElementById(item.id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, [items]);
  return (
    <nav aria-label={label} className="lg:sticky lg:top-[92px]">
      <ol className="border-border-subtle bg-surface rounded-card flex gap-1 overflow-x-auto border p-1 lg:flex-col">
        {items.map((item) => (
          <li key={item.id} className="min-w-max">
            <a
              href={`#${item.id}`}
              aria-current={active === item.id ? "location" : undefined}
              onClick={() => setActive(item.id)}
              className={cn(
                "rounded-control flex items-center gap-2 px-2 py-1.5 text-[11px]",
                active === item.id ? "bg-surface-high text-fg" : "text-fg-secondary hover:text-fg",
              )}
            >
              {item.number ? (
                <span className="tabular text-fg-muted w-5 text-[10px]">{item.number}</span>
              ) : null}
              <span className="whitespace-nowrap">{item.label}</span>
            </a>
          </li>
        ))}
      </ol>
      {extra ? <div className="mt-3">{extra}</div> : null}
    </nav>
  );
}

export function NoteStrip({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "neutral" | "legal" | "demo";
  className?: string;
}) {
  return (
    <p
      className={cn(
        "rounded-card border px-3 py-2 text-[11px] leading-relaxed",
        tone === "legal" && "border-border bg-surface-raised text-fg-body",
        tone === "demo" && "border-demo-border bg-demo-bg/50 text-fg-body",
        tone === "neutral" && "border-border-subtle bg-surface text-fg-secondary",
        className,
      )}
    >
      {children}
    </p>
  );
}

export function KeyValue({
  rows,
}: {
  rows: readonly { key: string; label: string; value: ReactNode }[];
}) {
  return (
    <dl className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-1 text-[11px]">
      {rows.map((r) => (
        <div key={r.key} className="contents">
          <dt className="text-fg-secondary">{r.label}</dt>
          <dd className="text-fg min-w-0 text-right">{r.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Stepper({
  steps,
  active,
  label,
}: {
  steps: readonly { key: string; label: string; state?: string }[];
  active: string;
  label: string;
}) {
  return (
    <ol aria-label={label} className="flex flex-wrap gap-2">
      {steps.map((s, i) => (
        <li
          key={s.key}
          aria-current={active === s.key ? "step" : undefined}
          className={cn(
            "rounded-control flex items-center gap-2 border px-2.5 py-1.5 text-[11px]",
            active === s.key
              ? "border-accent bg-surface-high text-fg"
              : "border-border bg-surface text-fg-secondary",
          )}
        >
          <span className="tabular bg-surface-raised inline-flex size-5 items-center justify-center rounded-full text-[10px]">
            {i + 1}
          </span>
          <span>{s.label}</span>
          {s.state ? <span className="text-fg-muted text-[10px]">· {s.state}</span> : null}
        </li>
      ))}
    </ol>
  );
}

export function HexAvatar({ initials, dashed }: { initials: string; dashed?: boolean }) {
  return (
    <span
      aria-hidden
      className={cn(
        "text-fg inline-flex size-12 shrink-0 items-center justify-center border text-[13px] font-semibold",
        dashed ? "border-witness border-dashed" : "border-accent bg-surface-raised",
      )}
      style={{ clipPath: "polygon(25% 5%, 75% 5%, 100% 50%, 75% 95%, 25% 95%, 0 50%)" }}
    >
      {initials}
    </span>
  );
}

export function Pager({
  page,
  pageCount,
  onChange,
  prevLabel,
  nextLabel,
  summary,
}: {
  page: number;
  pageCount: number;
  onChange: (next: number) => void;
  prevLabel: string;
  nextLabel: string;
  summary: string;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-[11px]">
      <span className="text-fg-secondary tabular">{summary}</span>
      <div className="flex gap-1">
        <ToolButton onClick={() => onChange(Math.max(1, page - 1))}>{prevLabel}</ToolButton>
        <span className="tabular text-fg-secondary inline-flex h-8 items-center px-2">
          {page} / {pageCount}
        </span>
        <ToolButton onClick={() => onChange(Math.min(pageCount, page + 1))}>{nextLabel}</ToolButton>
      </div>
    </div>
  );
}

export function SectionCard({
  id,
  number,
  title,
  children,
  aside,
}: {
  id?: string;
  number?: string;
  title: ReactNode;
  children: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <section id={id} className="border-border-subtle bg-surface rounded-card scroll-mt-24 border">
      <header className="border-border-faint flex flex-wrap items-center justify-between gap-2 border-b px-3 py-2">
        <h2 className="text-fg flex items-center gap-2 text-[12px] font-semibold">
          {number ? <span className="tabular text-fg-muted text-[10px]">{number}</span> : null}
          {title}
        </h2>
        {aside}
      </header>
      <div className="p-3">{children}</div>
    </section>
  );
}
