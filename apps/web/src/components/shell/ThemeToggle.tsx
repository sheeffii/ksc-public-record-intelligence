"use client";

import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";
import { MoonIcon, SunIcon } from "@/components/primitives/icons";
import { cn } from "@/lib/utils";

/**
 * User-preference theme switch. Infrastructure only in Phase 4: the approved
 * design binds light/dark to the surface (reader and public mode are light,
 * everything else dark), so this control is not mounted in GlobalNav. See
 * docs/DECISIONS.md ADR-006.
 */
export function ThemeToggle({ className }: { className?: string }) {
  const t = useTranslations("theme");
  const { resolvedTheme, setTheme } = useTheme();
  // Hydration-safe "mounted" flag: the server snapshot is false, the client true.
  const mounted = useSyncExternalStore(subscribeNoop, getClientSnapshot, getServerSnapshot);

  const isDark = (mounted ? resolvedTheme : "dark") === "dark";
  const label = isDark ? t("switchToLight") : t("switchToDark");

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={label}
      title={label}
      data-theme-current={isDark ? "dark" : "light"}
      className={cn(
        "rounded-control border-border bg-surface-raised text-fg-body hover:bg-surface-high inline-flex size-7 items-center justify-center border",
        className,
      )}
    >
      {isDark ? <SunIcon size={14} /> : <MoonIcon size={14} />}
    </button>
  );
}

const subscribeNoop = () => () => {};
const getClientSnapshot = () => true;
const getServerSnapshot = () => false;
