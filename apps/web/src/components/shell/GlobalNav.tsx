"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDownIcon, SearchIcon, UserIcon } from "@/components/primitives/icons";
import { PRIMARY_NAV, navKeyForPath, type NavItem } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { LanguageToggle } from "./LanguageToggle";
import { Logo } from "./Logo";

/**
 * 52px fixed GlobalNav: logo · nav links · right cluster (search affordance with
 * ⌘K, LanguageToggle, avatar).
 *
 * Constraints (COMPONENTS.md §1): links have no fixed width and 11px horizontal
 * padding so Albanian labels grow rather than truncate; trailing items collapse
 * into an overflow menu below 1280px — never ellipsis. The AI link is always
 * `--ai` coloured and never gets the active pill. Below 860px links hide and
 * the bottom tab bar takes over.
 */
export function GlobalNav() {
  const t = useTranslations("nav");
  const pathname = usePathname();
  const active = navKeyForPath(pathname ?? "/");

  const inline = PRIMARY_NAV.filter((i) => !i.overflow && !i.isAi);
  const overflow = PRIMARY_NAV.filter((i) => i.overflow);
  const ai = PRIMARY_NAV.find((i) => i.isAi);

  return (
    <header
      data-global-nav
      className="h-nav border-border-subtle bg-surface sticky top-0 z-30 flex shrink-0 items-center gap-3 border-b px-3"
    >
      <Logo />

      <nav
        aria-label={t("mainNavigation")}
        className="hidden min-w-0 flex-1 items-center gap-0.5 md:flex"
      >
        {inline.map((item) => (
          <NavLink key={item.key} item={item} active={active === item.key} label={t(item.key)} />
        ))}
        {/* Overflow items render inline at ≥1280px and in a menu below. */}
        <span className="hidden items-center gap-0.5 xl:flex">
          {overflow.map((item) => (
            <NavLink key={item.key} item={item} active={active === item.key} label={t(item.key)} />
          ))}
        </span>
        <span className="flex xl:hidden">
          <OverflowMenu items={overflow} active={active} />
        </span>
        {ai ? <NavLink item={ai} active={active === ai.key} label={t(ai.key)} /> : null}
      </nav>

      <div className="ml-auto flex shrink-0 items-center gap-2">
        <Link
          href="/search"
          aria-label={t("openSearch")}
          className="rounded-control border-border bg-surface-raised text-fg-secondary hover:bg-surface-high hover:text-fg hidden h-7 items-center gap-2 border px-2 text-[11px] sm:inline-flex"
        >
          <SearchIcon size={14} />
          <span className="hidden lg:inline">{t("openSearch")}</span>
          <kbd className="rounded-badge border-border text-fg-muted border px-1 font-sans text-[9.5px]">
            {t("searchShortcut")}
          </kbd>
        </Link>
        <LanguageToggle />
        <span
          aria-label={t("account")}
          role="img"
          className="border-border bg-surface-raised text-fg-secondary inline-flex size-7 items-center justify-center rounded-full border"
        >
          <UserIcon size={14} />
        </span>
      </div>
    </header>
  );
}

function NavLink({ item, active, label }: { item: NavItem; active: boolean; label: string }) {
  return (
    <Link
      href={item.href}
      aria-current={active ? "page" : undefined}
      data-nav={item.key}
      className={cn(
        "rounded-control inline-flex h-7 items-center px-[11px] text-[12px] font-medium whitespace-nowrap",
        item.isAi
          ? "text-ai hover:bg-ai-bg"
          : active
            ? "bg-surface-raised text-fg"
            : "text-fg-secondary hover:bg-surface-raised hover:text-fg",
      )}
    >
      {label}
    </Link>
  );
}

function OverflowMenu({ items, active }: { items: NavItem[]; active: string }) {
  const t = useTranslations("nav");
  const containsActive = items.some((i) => i.key === active);
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        aria-label={t("moreSections")}
        className={cn(
          "rounded-control inline-flex h-7 items-center gap-1 px-[11px] text-[12px] font-medium",
          containsActive
            ? "bg-surface-raised text-fg"
            : "text-fg-secondary hover:bg-surface-raised hover:text-fg",
        )}
      >
        {t("more")}
        <ChevronDownIcon size={12} />
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="start"
          sideOffset={6}
          className="rounded-card border-border bg-surface shadow-palette z-50 min-w-44 border p-1"
        >
          {items.map((item) => (
            <DropdownMenu.Item key={item.key} asChild>
              <Link
                href={item.href}
                aria-current={active === item.key ? "page" : undefined}
                className={cn(
                  "rounded-control data-[highlighted]:bg-surface-raised flex cursor-pointer items-center px-2.5 py-1.5 text-[12px] outline-none",
                  active === item.key ? "text-fg font-semibold" : "text-fg-body",
                )}
              >
                {t(item.key)}
              </Link>
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
