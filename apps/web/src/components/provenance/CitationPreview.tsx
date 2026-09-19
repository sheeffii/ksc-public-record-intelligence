"use client";

import type { Citation } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { useState } from "react";
import { citationHref } from "@/lib/citation";
import { CitationChip } from "./CitationChip";

export function CitationPreview({ citation, passage }: { citation: Citation; passage?: string }) {
  const t = useTranslations("citation");
  const [open, setOpen] = useState(false);
  if (!citation.resolved) return null;
  return (
    <span className="relative inline-flex">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="rounded-chip"
      >
        <CitationChip citation={citation} navigable={false} />
      </button>
      {open ? (
        <span
          role="dialog"
          aria-label={citation.display}
          className="shadow-palette border-border bg-surface rounded-card absolute top-full left-0 z-30 mt-2 block w-[min(340px,80vw)] border p-3 text-left"
        >
          <strong className="text-fg block text-[11px]">{citation.display}</strong>
          <span className="text-fg-secondary my-2 block font-serif text-[11px] leading-relaxed">
            {passage ?? "Generic surrounding passage from the demo record."}
          </span>
          <Link href={citationHref(citation)} className="text-accent text-[11px] font-semibold">
            {t("open")} →
          </Link>
        </span>
      ) : null}
    </span>
  );
}
