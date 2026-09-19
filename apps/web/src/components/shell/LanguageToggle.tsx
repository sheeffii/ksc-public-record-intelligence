"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { setLocale } from "@/i18n/actions";
import type { Locale } from "@/i18n/config";
import { cn } from "@/lib/utils";

const OPTIONS: readonly {
  locale: Locale;
  labelKey: "english" | "albanian";
  subKey: "englishSub" | "albanianSub";
}[] = [
  { locale: "en", labelKey: "english", subKey: "englishSub" },
  { locale: "sq", labelKey: "albanian", subKey: "albanianSub" },
];

/**
 * Fixed 62px `EN / SQ` control that never reflows the nav. Expands to a menu
 * with English / Shqip, each with a sub-line, plus the note that switching
 * changes the interface only (COMPONENTS.md §1).
 */
export function LanguageToggle({ className }: { className?: string }) {
  const t = useTranslations("language");
  const locale = useLocale();
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  function choose(next: Locale) {
    if (next === locale) return;
    startTransition(async () => {
      await setLocale(next);
      router.refresh();
    });
  }

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger
        aria-label={t("label")}
        data-locale={locale}
        disabled={pending}
        className={cn(
          "rounded-control border-border bg-surface-raised text-fg-body hover:bg-surface-high inline-flex h-7 w-[62px] shrink-0 items-center justify-center border text-[10.5px] font-semibold tracking-[0.04em] disabled:opacity-60",
          className,
        )}
      >
        <span className={locale === "en" ? "text-fg" : "text-fg-muted"}>EN</span>
        <span className="text-fg-muted mx-1">/</span>
        <span className={locale === "sq" ? "text-fg" : "text-fg-muted"}>SQ</span>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={6}
          className="rounded-card border-border bg-surface shadow-palette z-50 w-64 border p-1"
        >
          <DropdownMenu.RadioGroup value={locale} onValueChange={(v) => choose(v as Locale)}>
            {OPTIONS.map((opt) => (
              <DropdownMenu.RadioItem
                key={opt.locale}
                value={opt.locale}
                lang={opt.locale}
                className="rounded-control data-[highlighted]:bg-surface-raised data-[state=checked]:bg-surface-high flex cursor-pointer flex-col gap-0.5 px-2.5 py-1.5 outline-none"
              >
                <span className="text-fg text-[12px] font-semibold">{t(opt.labelKey)}</span>
                <span className="text-fg-secondary text-[10.5px]">{t(opt.subKey)}</span>
              </DropdownMenu.RadioItem>
            ))}
          </DropdownMenu.RadioGroup>
          <DropdownMenu.Separator className="bg-border-subtle my-1 h-px" />
          <p className="governance-text px-2.5 py-1">{t("note")}</p>
          <p className="governance-text px-2.5 pb-1">{t("provisional")}</p>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
