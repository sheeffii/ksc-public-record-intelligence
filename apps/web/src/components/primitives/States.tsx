import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Loading: skeleton blocks matching the final layout so nothing reflows.
 * Never a full-page spinner (PAGE_SPECS.md, Global States).
 */
export function SkeletonBlock({
  className,
  lines = 1,
  label,
}: {
  className?: string;
  lines?: number;
  label?: string;
}) {
  const t = useTranslations("states");
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className={cn("flex flex-col gap-2", className)}
    >
      <span className="sr-only">{label ? t("loadingScope", { scope: label }) : t("loading")}</span>
      {Array.from({ length: lines }).map((_, i) => (
        <span
          key={i}
          aria-hidden
          className="rounded-badge bg-surface-raised block h-3 animate-pulse last:w-4/5"
        />
      ))}
    </div>
  );
}

/** Counts render as a dimmed dash until resolved — never `0`, because 0 is meaningful. */
export function PendingCount({ className }: { className?: string }) {
  return (
    <span aria-hidden className={cn("tabular text-fg-muted", className)}>
      —
    </span>
  );
}

export interface EmptyStateProps {
  /** What is absent. */
  title: ReactNode;
  /** Why it may be absent — required and specific (COMPONENTS.md §12). */
  reason: ReactNode;
  /** One action. */
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ title, reason, action, className }: EmptyStateProps) {
  return (
    <div
      data-state="empty"
      className={cn(
        "rounded-card border-border bg-surface flex flex-col items-start gap-2 border px-4 py-5",
        className,
      )}
    >
      <p className="text-fg text-[13px] font-semibold">{title}</p>
      <p className="text-fg-secondary max-w-prose text-[12px] leading-relaxed">{reason}</p>
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}

export interface ErrorStateProps {
  /** The failing scope, named. Never "Something went wrong." */
  scope: string;
  detail?: ReactNode;
  action?: ReactNode;
  /** True when partial data renders above with the gap marked. */
  partial?: boolean;
  className?: string;
}

export function ErrorState({ scope, detail, action, partial, className }: ErrorStateProps) {
  const t = useTranslations("states");
  return (
    <div
      role="alert"
      data-state="error"
      className={cn(
        "rounded-card border-unresolved/60 bg-surface flex flex-col items-start gap-2 border border-dashed px-4 py-4",
        className,
      )}
    >
      <p className="text-fg text-[13px] font-semibold">{t("errorTitle", { scope })}</p>
      {detail ? <p className="text-fg-secondary text-[12px] leading-relaxed">{detail}</p> : null}
      {partial ? <p className="text-fg-muted text-[11px]">{t("partial")}</p> : null}
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}

export interface GapNoticeProps {
  kind: "closed-session" | "redaction" | "untranslated" | "unresolved-citation";
  /** The record reference the gap belongs to, e.g. "T. 4,511–4,552". */
  reference: string;
  extent: string;
  reason?: ReactNode;
  className?: string;
}

/** Dashed-border card naming material the system does not hold. Gaps are stated, never filled. */
export function GapNotice({ kind, reference, extent, reason, className }: GapNoticeProps) {
  const t = useTranslations("gap");
  return (
    <div
      data-gap={kind}
      className={cn(
        "rounded-card border-border bg-surface border border-dashed px-3 py-2.5 text-[11.5px]",
        className,
      )}
    >
      <div className="section-label">{t("title")}</div>
      <div className="text-fg mt-1 font-semibold">{t(kind)}</div>
      <div className="text-fg-secondary mt-0.5">
        <span className="identifier text-fg-body">{reference}</span>
        <span className="mx-1.5">·</span>
        <span>
          {t("extent")}: <span className="tabular">{extent}</span>
        </span>
      </div>
      {reason ? <p className="text-fg-secondary mt-1">{reason}</p> : null}
      <p className="governance-text mt-1.5">{t("rule")}</p>
    </div>
  );
}
