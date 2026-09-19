import type { SourceType } from "@ksc/shared";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { SOURCE_BG, SOURCE_DOT, SOURCE_TEXT } from "./source-styles";

export interface SourceBadgeProps {
  type: SourceType;
  size?: "sm" | "md";
  /** `dot` shows the colour dot before the label; `plain` is label only. */
  variant?: "dot" | "plain";
  className?: string;
}

/**
 * The provenance vocabulary. Uppercase 9–9.5px / 600, 0.05–0.06em tracking,
 * 3px radius. `min-width`, never fixed width: Albanian labels run up to 60 %
 * longer and must wrap rather than truncate (COMPONENTS.md §2).
 */
export function SourceBadge({ type, size = "md", variant = "dot", className }: SourceBadgeProps) {
  const t = useTranslations("source");
  return (
    <span
      data-source={type}
      className={cn(
        "rounded-badge inline-flex min-w-0 items-center gap-1.5 px-1.5 py-0.5 align-middle font-semibold tracking-[0.06em] whitespace-normal uppercase",
        size === "sm" ? "text-[9px]" : "text-[9.5px]",
        SOURCE_TEXT[type],
        SOURCE_BG[type],
        className,
      )}
    >
      {variant === "dot" ? (
        <span aria-hidden className={cn("size-1.5 shrink-0 rounded-full", SOURCE_DOT[type])} />
      ) : null}
      <span>{t(type)}</span>
    </span>
  );
}
