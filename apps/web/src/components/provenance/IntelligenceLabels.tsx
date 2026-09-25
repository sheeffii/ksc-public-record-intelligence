import { useTranslations } from "next-intl";
import Link from "next/link";
import type { EvidenceKind, ProvenanceView } from "@/data";
import { CitationChip } from "./CitationChip";

/**
 * The Phase 19 intelligence states. Each is a text label (never colour
 * alone), and a weaker state is never rendered as a stronger one.
 */
export type IntelligenceState =
  "VERIFIED" | "SEARCH_MATCH" | "REVIEW_REQUIRED" | "AMBIGUOUS" | "UNKNOWN";

export function IntelligenceStateLabel({ state }: { state: IntelligenceState }) {
  const t = useTranslations("phase19");
  return (
    <span
      data-intelligence-state={state}
      className="text-fg-secondary font-mono text-[10px] font-semibold"
    >
      {t(`state.${state}`)}
    </span>
  );
}

/** Which evidence row backs a relationship, and how many exact anchors it has. */
export function EvidenceBasis({ kind, count }: { kind?: EvidenceKind; count?: number }) {
  const t = useTranslations("phase19");
  if (!kind) return null;
  return (
    <span data-evidence-kind={kind} className="text-fg-tertiary font-mono text-[10px]">
      {t(`evidenceKind.${kind}`)}
      {count !== undefined ? ` · ${t("evidenceCount", { count })}` : ""}
    </span>
  );
}

/**
 * The answer to "why does this exist?": the verbatim source text, its exact
 * coordinate, the deterministic rule, and a link to that coordinate.
 */
export function ProvenanceSource({ provenance }: { provenance: ProvenanceView }) {
  const t = useTranslations("phase19");
  return (
    <div className="space-y-1.5">
      {provenance.text ? (
        <p className="text-fg font-mono text-[11px] break-words">{provenance.text}</p>
      ) : null}
      <div className="flex flex-wrap items-center gap-2">
        <CitationChip citation={provenance.citation} size="sm" />
        {provenance.rule ? (
          <span className="text-fg-tertiary font-mono text-[10px]">{provenance.rule}</span>
        ) : null}
        <Link
          href={provenance.href}
          className="text-accent text-[11px] font-semibold"
          data-provenance-kind={provenance.kind}
        >
          {t("openExactSource")}
        </Link>
      </div>
    </div>
  );
}
