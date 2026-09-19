import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface PanelProps extends Omit<HTMLAttributes<HTMLElement>, "title"> {
  title?: ReactNode;
  /** Section label rendered above the title (10 / 600 uppercase). */
  label?: ReactNode;
  actions?: ReactNode;
  footer?: ReactNode;
  /** Flat by default (DESIGN_SYSTEM.md §5). */
  padded?: boolean;
  as?: "section" | "aside" | "div";
}

/** Bordered card on `--surface`, 8px radius. The base container for rails and inspectors. */
export function Panel({
  title,
  label,
  actions,
  footer,
  padded = true,
  as: Tag = "section",
  className,
  children,
  ...rest
}: PanelProps) {
  const hasHeader = title || label || actions;
  return (
    <Tag
      className={cn(
        "rounded-card border-border bg-surface flex min-w-0 flex-col border",
        className,
      )}
      {...rest}
    >
      {hasHeader ? (
        <header className="border-border-subtle flex items-start justify-between gap-3 border-b px-3 py-2">
          <div className="min-w-0">
            {label ? <div className="section-label">{label}</div> : null}
            {title ? (
              <h2 className="text-fg text-[14px] font-semibold tracking-[-0.01em]">{title}</h2>
            ) : null}
          </div>
          {actions ? <div className="flex shrink-0 items-center gap-1">{actions}</div> : null}
        </header>
      ) : null}
      <div className={cn("min-w-0 flex-1", padded && "p-3")}>{children}</div>
      {footer ? (
        <footer className="governance-text border-border-subtle border-t px-3 py-1.5">
          {footer}
        </footer>
      ) : null}
    </Tag>
  );
}
