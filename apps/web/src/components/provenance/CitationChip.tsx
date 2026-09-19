import type { Citation } from "@ksc/shared";
import { useTranslations } from "next-intl";
import Link from "next/link";
import { ArrowRightIcon } from "@/components/primitives/icons";
import { citationHref } from "@/lib/citation";
import { cn } from "@/lib/utils";
import { SOURCE_TEXT } from "./source-styles";

export interface CitationChipProps {
  citation: Citation;
  size?: "sm" | "md";
  /** Sits inside flowing prose without breaking the line box. */
  inline?: boolean;
  /** Renders a link to the Document Reader at the cited position. */
  navigable?: boolean;
  className?: string;
}

/**
 * The most-used component in the product.
 *
 * Rule 1 (HANDOFF.md §1): a citation that does not resolve is not rendered —
 * not degraded, not greyed. This component returns `null` for
 * `resolved === false`; the surrounding surface is responsible for withholding
 * its content or showing a GapNotice.
 */
export function CitationChip({
  citation,
  size = "md",
  inline = false,
  navigable = true,
  className,
}: CitationChipProps) {
  const t = useTranslations("citation");
  if (!citation.resolved) return null;

  const classes = cn(
    "inline-flex max-w-full items-center gap-1 rounded-chip border border-border bg-surface-raised px-1.5 py-0.5 font-semibold tabular-nums",
    size === "sm" ? "text-[10px]" : "text-[10.5px]",
    inline ? "align-middle leading-none" : "",
    SOURCE_TEXT[citation.sourceType],
    navigable ? "hover:border-accent hover:bg-surface-high" : "",
    className,
  );

  const label = <span className="truncate">{citation.display}</span>;

  if (!navigable) {
    return (
      <span data-citation={citation.ref} className={classes}>
        {label}
      </span>
    );
  }

  return (
    <Link
      href={citationHref(citation)}
      data-citation={citation.ref}
      className={classes}
      aria-label={t("opens", { reference: citation.display })}
    >
      {label}
      <ArrowRightIcon size={12} className="shrink-0 opacity-70" />
    </Link>
  );
}
