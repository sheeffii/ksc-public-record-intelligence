import Link from "next/link";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { pageTally, type SourceGroup } from "@/lib/source-groups";

/**
 * One compact row per exact document version: title, version reference, a
 * count and page tallies, with every underlying occurrence one click away.
 * Nothing is merged or dropped — expanding lists each occurrence with its own
 * exact-source link.
 */
export function GroupedSourceList<T>({
  groups,
  countLabel,
  itemKey,
  renderItem,
}: {
  groups: readonly SourceGroup<T>[];
  /** e.g. `(n) => t("verifiedMentionCount", { count: n })` */
  countLabel: (count: number) => string;
  itemKey: (item: T) => string;
  renderItem: (item: T) => ReactNode;
}) {
  const t = useTranslations("sourceGroups");
  return (
    <ul className="divide-border-faint divide-y" data-testid="grouped-source-list">
      {groups.map((group) => {
        const tally = pageTally(group.pages);
        return (
          <li key={group.key} className="py-2 first:pt-0 last:pb-0">
            <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
              <Link href={group.documentHref} className="text-accent text-[11px] font-semibold">
                {group.title}
              </Link>
              <span className="text-fg-secondary font-mono text-[10px] font-semibold">
                {countLabel(group.items.length)}
              </span>
            </div>
            <p className="text-fg-tertiary mt-0.5 font-mono text-[10px] break-words">
              {group.versionRef}
              {tally ? ` · ${tally}` : ""}
              {group.withoutPage ? ` · ${t("withoutPage", { count: group.withoutPage })}` : ""}
            </p>
            <details className="group mt-1">
              <summary className="text-accent cursor-pointer text-[10px] font-semibold select-none">
                <span className="group-open:hidden">
                  {t("show", { count: group.items.length })}
                </span>
                <span className="hidden group-open:inline">{t("hide")}</span>
              </summary>
              <ul className="border-border-faint mt-1.5 space-y-2 border-l pl-3">
                {group.items.map((item) => (
                  <li key={itemKey(item)}>{renderItem(item)}</li>
                ))}
              </ul>
            </details>
          </li>
        );
      })}
    </ul>
  );
}
