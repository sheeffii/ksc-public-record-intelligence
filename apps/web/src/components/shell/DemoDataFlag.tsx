import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

/**
 * Amber badge: `--demo-bg` / `--demo-border` / `--demo-fg`. Present on every
 * screen that displays a figure; removed from a screen only when every figure
 * on it is a live database read — never globally in one commit (HANDOFF.md §10).
 */
export function DemoDataFlag({
  compact = false,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  const t = useTranslations("demo");
  return (
    <span
      data-demo-flag
      title={t("description")}
      className={cn(
        "rounded-badge border-demo-border bg-demo-bg text-demo-fg inline-flex min-w-0 items-center gap-1 border px-1.5 py-0.5 text-[9.5px] font-semibold tracking-[0.05em] whitespace-normal uppercase",
        className,
      )}
    >
      <span aria-hidden className="bg-demo-fg size-1.5 shrink-0 rounded-full" />
      {compact ? t("short") : t("long")}
    </span>
  );
}
