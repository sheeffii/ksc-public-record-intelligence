import type { Direction } from "@ksc/shared";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

const GLYPH: Record<Direction, string> = {
  supports: "↑",
  contradicts: "↓",
  qualifies: "~",
  neutral: "—",
};
const COLOR: Record<Direction, string> = {
  supports: "text-supports",
  contradicts: "text-contradicts",
  qualifies: "text-qualifies",
  neutral: "text-neutral",
};

export function DirectionBadge({ direction }: { direction: Direction }) {
  const t = useTranslations("direction");
  return (
    <span
      data-direction={direction}
      className={cn(
        "rounded-badge bg-surface-raised inline-flex items-center gap-1 px-1.5 py-0.5 text-[9.5px] font-semibold tracking-[0.05em] uppercase",
        COLOR[direction],
      )}
    >
      <span aria-hidden>{GLYPH[direction]}</span>
      {t(direction)}
    </span>
  );
}

export function ScopeNote() {
  const t = useTranslations("direction");
  return (
    <p className="governance-text" data-direction-scope>
      {t("scopeNote")}
    </p>
  );
}
