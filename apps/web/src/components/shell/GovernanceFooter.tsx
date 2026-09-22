import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

/**
 * 24–26px band of 10px `--text-faint` text carrying the screen's required
 * neutrality note. Not decorative (COMPONENTS.md §1). Each screen's required
 * text is listed in PAGE_SPECS.md; the default is the general neutrality note.
 */
export function GovernanceFooter({ children }: { children?: ReactNode }) {
  const t = useTranslations("footer");
  return (
    <footer
      data-governance-footer
      className="governance-text border-border-subtle bg-bg-deep flex min-h-[26px] shrink-0 items-center border-t px-4 py-1"
    >
      <p>{children ?? t("neutrality")}</p>
    </footer>
  );
}

export function PublicDisclosure() {
  const t = useTranslations("footer");
  return (
    <aside
      aria-label={t("disclosure")}
      className="governance-text border-border-subtle bg-surface text-fg-secondary border-t px-4 py-1.5 text-center"
    >
      {t("disclosure")}
    </aside>
  );
}
