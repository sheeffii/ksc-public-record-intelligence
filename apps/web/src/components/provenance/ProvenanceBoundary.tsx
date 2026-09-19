import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

/**
 * The labelled dashed divider — one of the four simultaneous signals that
 * separate record material from generated analysis (DESIGN_SYSTEM.md §6).
 * Required on any surface where both appear. Never omitted for space.
 */
export function ProvenanceBoundary({ className }: { className?: string }) {
  const t = useTranslations("provenance");
  return (
    <div
      role="separator"
      aria-label={t("boundary")}
      data-provenance-boundary
      className={cn("my-4 flex items-center gap-3", className)}
    >
      <span aria-hidden className="border-ai/40 h-px flex-1 border-t border-dashed" />
      <span className="text-ai shrink-0 text-[9.5px] font-semibold tracking-[0.06em] uppercase">
        ▼ {t("boundary")}
      </span>
      <span aria-hidden className="border-ai/40 h-px flex-1 border-t border-dashed" />
    </div>
  );
}
