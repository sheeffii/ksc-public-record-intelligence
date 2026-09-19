"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  DocumentIcon,
  HomeIcon,
  NetworkIcon,
  SearchIcon,
  SparkIcon,
  type IconProps,
} from "@/components/primitives/icons";
import { MOBILE_NAV, navKeyForPath } from "@/lib/routes";
import { cn } from "@/lib/utils";

type MobileKey = (typeof MOBILE_NAV)[number]["key"];

const ICONS: Record<MobileKey, (p: IconProps) => React.JSX.Element> = {
  home: HomeIcon,
  search: SearchIcon,
  network: NetworkIcon,
  docs: DocumentIcon,
  ai: SparkIcon,
};

/** Maps bottom-tab keys onto the nav sections used for the active state. */
const SECTION_FOR: Record<MobileKey, string> = {
  home: "home",
  search: "search",
  network: "network",
  docs: "documents",
  ai: "ai",
};

/**
 * Five-item bottom tab bar (Home · Search · Network · Docs · AI) replacing the
 * top nav links below 860px. Touch targets ≥44px (PAGE_SPECS.md §17).
 */
export function MobileTabBar() {
  const t = useTranslations("mobileNav");
  const tNav = useTranslations("nav");
  const pathname = usePathname();
  const active = navKeyForPath(pathname ?? "/");

  return (
    <nav
      aria-label={tNav("mobileNavigation")}
      data-mobile-tab-bar
      className="border-border-subtle bg-surface fixed inset-x-0 bottom-0 z-30 grid h-14 grid-cols-5 border-t pb-[env(safe-area-inset-bottom)] md:hidden"
    >
      {MOBILE_NAV.map((item) => {
        const Icon = ICONS[item.key];
        const isActive = SECTION_FOR[item.key] === active;
        const isAi = item.key === "ai";
        return (
          <Link
            key={item.key}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "flex min-h-11 flex-col items-center justify-center gap-0.5 text-[10px] font-medium",
              isAi ? "text-ai" : isActive ? "text-fg" : "text-fg-secondary",
            )}
          >
            <Icon size={20} />
            <span>{t(item.key)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
