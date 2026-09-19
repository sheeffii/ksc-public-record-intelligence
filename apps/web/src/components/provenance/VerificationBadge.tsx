import type { VerificationState } from "@ksc/shared";
import { useTranslations } from "next-intl";
import {
  AlertCircleIcon,
  CheckCircleIcon,
  CrossCircleIcon,
  DashedCircleIcon,
  type IconProps,
} from "@/components/primitives/icons";
import { cn } from "@/lib/utils";

export interface VerificationBadgeProps {
  state: VerificationState;
  size?: "sm" | "md";
  className?: string;
}

/**
 * Five states, each with a distinct glyph so they are separable without
 * colour (COMPONENTS.md §2). Colours are tokens: `--verified`, `--ai`,
 * `--unresolved`, `--doc`, `--text-secondary`.
 */
const STATE_STYLE: Record<
  VerificationState,
  { color: string; Icon: (p: IconProps) => React.JSX.Element }
> = {
  verified: { color: "text-verified", Icon: CheckCircleIcon },
  "ai-flagged": { color: "text-ai", Icon: CrossCircleIcon },
  unresolved: { color: "text-unresolved", Icon: AlertCircleIcon },
  "needs-evidence": { color: "text-doc", Icon: AlertCircleIcon },
  unreviewed: { color: "text-fg-secondary", Icon: DashedCircleIcon },
};

export function VerificationBadge({ state, size = "md", className }: VerificationBadgeProps) {
  const t = useTranslations("verification");
  const { color, Icon } = STATE_STYLE[state];
  return (
    <span
      data-verification={state}
      className={cn(
        "rounded-badge inline-flex min-w-0 items-center gap-1 align-middle font-semibold tracking-[0.05em] whitespace-normal uppercase",
        size === "sm" ? "text-[9px]" : "text-[9.5px]",
        color,
        className,
      )}
    >
      <Icon size={12} className="shrink-0" />
      <span>{t(state)}</span>
    </span>
  );
}
