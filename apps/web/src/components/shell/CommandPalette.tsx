"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useEffect, useState } from "react";
import { mockRepository } from "@/mock";

export function CommandPalette() {
  const t = useTranslations("phase5");
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
      }
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  if (!open) return null;
  const results = mockRepository.search(query).slice(0, 6);
  return (
    <div
      className="bg-scrim fixed inset-0 z-50 flex items-start justify-center p-4 pt-24"
      role="dialog"
      aria-modal="true"
      aria-label={t("searchRecords")}
      onMouseDown={() => setOpen(false)}
    >
      <div
        className="shadow-palette border-accent bg-surface rounded-palette w-full max-w-[660px] border"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <input
          autoFocus
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("commandHint")}
          className="border-border-subtle text-fg h-14 w-full border-b bg-transparent px-4 text-[14px]"
        />
        <div className="p-2">
          <p className="section-label px-2 py-1">{t("bestMatch")}</p>
          {results.map((result) => (
            <Link
              key={result.id}
              href={result.href}
              onClick={() => setOpen(false)}
              className="hover:bg-surface-raised rounded-control flex items-center justify-between px-3 py-2"
            >
              <span>
                <strong className="text-fg text-[12px]">{result.title}</strong>
                <small className="text-fg-muted ml-2">{result.category}</small>
              </span>
              <span className="text-accent">↵</span>
            </Link>
          ))}
        </div>
        <footer className="governance-text border-border-subtle border-t px-4 py-2">
          {t("keyboardHelp")}
        </footer>
      </div>
    </div>
  );
}
