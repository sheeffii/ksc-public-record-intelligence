"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { SearchIcon } from "@/components/primitives/icons";
import { cn } from "@/lib/utils";

type CommandHit = {
  category:
    | "documents"
    | "transcripts"
    | "people"
    | "organizations"
    | "witnesses"
    | "exhibits"
    | "incidents"
    | "findings"
    | "locations";
  ref: string;
  title: string;
  protected: boolean;
  target_path: string | null;
};

function fallbackHref(hit: CommandHit): string {
  const segment: Record<CommandHit["category"], string> = {
    documents: "documents",
    transcripts: "documents",
    people: "people",
    organizations: "organizations",
    witnesses: "witnesses",
    exhibits: "exhibits",
    incidents: "incidents",
    findings: "findings",
    locations: "search",
  };
  return hit.category === "locations"
    ? `/search?q=${encodeURIComponent(hit.ref)}`
    : `/${segment[hit.category]}/${encodeURIComponent(hit.ref)}`;
}

export function CommandPalette() {
  const t = useTranslations("phase5");
  const tb = useTranslations("phase5b");
  const t21 = useTranslations("phase21");
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<CommandHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
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

  useEffect(() => {
    const needle = query.trim();
    if (!open || needle.length < 2) {
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setLoading(true);
      try {
        const base = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
          /\/+$/,
          "",
        );
        const response = await fetch(`${base}/api/v1/search?q=${encodeURIComponent(needle)}`, {
          headers: { accept: "application/json" },
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`search ${response.status}`);
        const payload = (await response.json()) as { hits?: CommandHit[] };
        setHits((payload.hits ?? []).slice(0, 8));
        setActiveIndex(0);
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) setHits([]);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 180);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [open, query]);

  const pattern = useMemo(() => {
    const value = query.trim();
    if (/^W\d{4,5}$/i.test(value)) return "W#####";
    if (/^F\d{4,5}(?:\/[A-Z0-9]+)*$/i.test(value)) return "F#####";
    if (/^[PD]\d{4,5}$/i.test(value)) return "P##### / D#####";
    if (/^¶\d+$/.test(value)) return "¶####";
    return null;
  }, [query]);
  const searchHref = `/search?q=${encodeURIComponent(query)}`;
  const destinations = hits.map((hit) => hit.target_path ?? fallbackHref(hit));

  if (!open) return null;
  return (
    <Dialog.Root open={open} onOpenChange={changeOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="bg-scrim fixed inset-0 z-50 backdrop-blur-[3px]" />
        <Dialog.Content
          aria-describedby={undefined}
          className="shadow-palette border-accent bg-surface rounded-palette fixed top-24 left-1/2 z-50 flex max-h-[calc(100dvh-120px)] w-[calc(100%-32px)] max-w-[660px] -translate-x-1/2 flex-col overflow-hidden border focus:outline-none"
        >
          <Dialog.Title className="sr-only">{t("searchRecords")}</Dialog.Title>
          <div className="border-border-subtle flex h-14 items-center gap-3 border-b px-4">
            <SearchIcon size={20} className="text-accent shrink-0" />
            <input
              autoFocus
              value={query}
              onChange={(event) => {
                const value = event.target.value;
                setQuery(value);
                if (value.trim().length < 2) {
                  setHits([]);
                  setLoading(false);
                }
              }}
              onKeyDown={(event) => {
                if (event.key === "ArrowDown") {
                  event.preventDefault();
                  setActiveIndex((value) => Math.min(destinations.length - 1, value + 1));
                }
                if (event.key === "ArrowUp") {
                  event.preventDefault();
                  setActiveIndex((value) => Math.max(0, value - 1));
                }
                if (event.key === "Enter" && destinations[activeIndex]) {
                  event.preventDefault();
                  window.location.assign(destinations[activeIndex]);
                }
              }}
              placeholder={t21("commandHint")}
              className="text-fg placeholder:text-fg-muted min-w-0 flex-1 bg-transparent text-[14px]"
            />
            <kbd className="rounded-badge border-border text-fg-muted border px-1.5 py-0.5 text-[9px]">
              esc
            </kbd>
          </div>
          {pattern ? (
            <div className="border-border-subtle bg-bg-deep text-fg-secondary flex items-center gap-2 border-b px-4 py-2 text-[10.5px]">
              <span className="rounded-badge border-witness text-witness border px-1.5 py-0.5 text-[9px] font-semibold tracking-wide uppercase">
                {t21("commandDetected")}
              </span>
              <span className="identifier">{pattern}</span>
            </div>
          ) : null}
          <div className="min-h-40 flex-1 overflow-y-auto py-2">
            {loading ? (
              <p className="text-fg-secondary px-4 py-6 text-[11px]">{t21("commandLoading")}</p>
            ) : null}
            {!loading && hits.length ? (
              <>
                <p className="section-label px-4 py-1.5">{t("bestMatch")}</p>
                {hits.map((hit, index) => {
                  const href = destinations[index]!;
                  return (
                    <Link
                      key={`${hit.category}:${hit.ref}:${index}`}
                      href={href}
                      onClick={() => changeOpen(false)}
                      className={cn(
                        "border-l-accent flex min-h-12 items-center justify-between gap-3 border-l-2 px-4 py-2",
                        activeIndex === index ? "bg-surface-high" : "hover:bg-surface-raised",
                      )}
                    >
                      <span className="min-w-0">
                        <span className="flex items-center gap-2">
                          <strong className="identifier text-accent text-[12px]">{hit.ref}</strong>
                          <span className="section-label text-[8.5px]">{tb(hit.category)}</span>
                        </span>
                        <small className="text-fg-secondary mt-0.5 block truncate text-[10.5px]">
                          {hit.protected ? hit.ref : hit.title}
                        </small>
                      </span>
                      <span className="text-accent">↵</span>
                    </Link>
                  );
                })}
              </>
            ) : null}
            {!loading && query.trim().length >= 2 && !hits.length ? (
              <p className="text-fg-secondary px-4 py-6 text-[11px]">{t21("commandEmpty")}</p>
            ) : null}
            {!query.trim() ? (
              <div className="px-4 py-5">
                <p className="section-label mb-2">{tb("syntaxReference")}</p>
                <p className="text-fg-secondary text-[11px]">
                  W##### · F##### · P##### · D##### · ¶#### · &quot;exact phrase&quot;
                </p>
              </div>
            ) : null}
          </div>
          <footer className="governance-text border-border-subtle bg-bg-deep flex items-center justify-between gap-3 border-t px-4 py-2">
            <span>{t("keyboardHelp")}</span>
            <Link
              href={searchHref}
              onClick={() => changeOpen(false)}
              className="text-accent font-medium"
            >
              {t21("commandFullResults")} →
            </Link>
          </footer>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
