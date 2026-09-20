import { useTranslations } from "next-intl";
import Link from "next/link";
import type { ReactNode } from "react";
import { DemoDataFlag } from "@/components/shell/DemoDataFlag";
import { cn } from "@/lib/utils";

export function ScreenHeader({
  eyebrow,
  title,
  description,
  actions,
  realData = false,
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  realData?: boolean;
}) {
  return (
    <header className="border-border-subtle bg-bg-deep border-b px-4 py-4">
      <div className="mx-auto flex w-full max-w-[1440px] flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          {eyebrow ? <p className="section-label mb-1">{eyebrow}</p> : null}
          <h1 className="text-fg text-[24px] leading-tight font-bold tracking-[-0.02em] md:text-[28px]">
            {title}
          </h1>
          {description ? (
            <p className="text-fg-secondary mt-1 max-w-3xl text-[12px] leading-relaxed">
              {description}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {realData ? null : <DemoDataFlag />}
          {actions}
        </div>
      </div>
    </header>
  );
}

export function DemoNotice() {
  const t = useTranslations("phase5");
  return (
    <div className="border-demo-border bg-demo-bg/50 text-fg-body rounded-card border px-3 py-2 text-[11px]">
      {t("mockNotice")}
    </div>
  );
}

export function ActionLink({
  href,
  children,
  primary = false,
}: {
  href: string;
  children: ReactNode;
  primary?: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "rounded-control inline-flex h-8 items-center justify-center border px-3 text-[11px] font-semibold",
        primary
          ? "border-accent bg-accent hover:bg-accent-bright text-white"
          : "border-border bg-surface-raised text-fg hover:bg-surface-high",
      )}
    >
      {children}
    </Link>
  );
}

export function TabStrip({
  tabs,
  active,
}: {
  tabs: readonly { key: string; label: string; href?: string }[];
  active?: string;
}) {
  return (
    <nav aria-label="Sections" className="border-border-subtle bg-bg-deep overflow-x-auto border-b">
      <div className="mx-auto flex h-10 w-full max-w-[1440px] min-w-max items-end gap-1 px-4">
        {tabs.map((tab) => {
          const isActive = (active ?? tabs[0]?.key) === tab.key;
          const classes = cn(
            "border-b-2 px-3 py-2 text-[11px] font-medium whitespace-nowrap",
            isActive
              ? "border-accent text-fg"
              : "border-transparent text-fg-secondary hover:text-fg",
          );
          return tab.href ? (
            <Link key={tab.key} href={tab.href} className={classes}>
              {tab.label}
            </Link>
          ) : (
            <span key={tab.key} className={classes} aria-current={isActive ? "page" : undefined}>
              {tab.label}
            </span>
          );
        })}
      </div>
    </nav>
  );
}

export function WorkspaceGrid({
  left,
  children,
  right,
  className,
}: {
  left?: ReactNode;
  children: ReactNode;
  right?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mx-auto grid w-full max-w-[1440px] min-w-0 flex-1 gap-3 p-3 md:p-4",
        left && right
          ? "xl:grid-cols-[236px_minmax(0,1fr)_300px]"
          : left
            ? "lg:grid-cols-[236px_minmax(0,1fr)]"
            : right
              ? "lg:grid-cols-[minmax(0,1fr)_320px]"
              : "grid-cols-1",
        className,
      )}
    >
      {left ? <aside className="min-w-0">{left}</aside> : null}
      <div className="min-w-0">{children}</div>
      {right ? <aside className="min-w-0">{right}</aside> : null}
    </div>
  );
}
