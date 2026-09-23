"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

export function CommandPalette() {
  const t = useTranslations("phase5");
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const returnFocus = useRef<HTMLElement | null>(null);
  function changeOpen(nextOpen: boolean) {
    setOpen(nextOpen);
    if (!nextOpen) requestAnimationFrame(() => returnFocus.current?.focus());
  }
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        returnFocus.current = document.activeElement as HTMLElement | null;
        setOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  if (!open) return null;
  const searchHref = `/search?q=${encodeURIComponent(query)}`;
  return (
    <Dialog.Root open={open} onOpenChange={changeOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="bg-scrim fixed inset-0 z-50" />
        <Dialog.Content
          aria-describedby={undefined}
          className="shadow-palette border-accent bg-surface rounded-palette fixed top-24 left-1/2 z-50 w-[calc(100%-32px)] max-w-[660px] -translate-x-1/2 border focus:outline-none"
        >
          <Dialog.Title className="sr-only">{t("searchRecords")}</Dialog.Title>
          <input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t("commandHint")}
            className="border-border-subtle text-fg h-14 w-full border-b bg-transparent px-4 text-[14px]"
          />
          <div className="p-2">
            <p className="section-label px-2 py-1">{t("bestMatch")}</p>
            <Link
              href={searchHref}
              onClick={() => changeOpen(false)}
              className="hover:bg-surface-raised rounded-control flex items-center justify-between px-3 py-2"
            >
              <span>
                <strong className="text-fg text-[12px]">{query || t("searchRecords")}</strong>
                <small className="text-fg-muted ml-2">{t("search")}</small>
              </span>
              <span className="text-accent">↵</span>
            </Link>
          </div>
          <footer className="governance-text border-border-subtle border-t px-4 py-2">
            {t("keyboardHelp")}
          </footer>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
