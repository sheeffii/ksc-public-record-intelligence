import { CASE_ID } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import type { ReactNode } from "react";
import { DemoDataFlag } from "./DemoDataFlag";

export interface Crumb {
  label: ReactNode;
  href?: string;
}

/**
 * 30–32px band below the nav: case identifier, breadcrumb trail, DemoDataFlag
 * pinned right (COMPONENTS.md §1). The case identifier is never translated.
 */
export function CaseStripe({
  crumbs = [],
  showDemoFlag = false,
}: {
  crumbs?: Crumb[];
  showDemoFlag?: boolean;
}) {
  const t = useTranslations("app");
  return (
    <div className="border-border-subtle bg-bg-deep flex h-8 shrink-0 items-center gap-3 border-b px-4 text-[11px]">
      <span className="flex min-w-0 items-center gap-2">
        <span className="section-label">{t("caseLabel")}</span>
        <span className="identifier text-fg">{CASE_ID}</span>
      </span>
      {crumbs.length > 0 ? (
        <nav
          aria-label="Breadcrumb"
          className="text-fg-secondary flex min-w-0 items-center gap-1.5"
        >
          {crumbs.map((c, i) => (
            <span key={i} className="flex min-w-0 items-center gap-1.5">
              <span aria-hidden className="text-fg-faint">
                /
              </span>
              {c.href ? (
                <Link href={c.href} className="hover:text-fg truncate">
                  {c.label}
                </Link>
              ) : (
                <span className="text-fg-body truncate">{c.label}</span>
              )}
            </span>
          ))}
        </nav>
      ) : null}
      {showDemoFlag ? <DemoDataFlag compact className="ml-auto" /> : null}
    </div>
  );
}
