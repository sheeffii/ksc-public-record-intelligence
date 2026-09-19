import type { Citation } from "@ksc/shared";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { CitationChip } from "./CitationChip";
import { SourceBadge } from "./SourceBadge";

export interface AiAnalysisBlockProps {
  children: ReactNode;
  citations?: readonly Citation[];
  title?: ReactNode;
}

/** Generated analysis with all four mandatory provenance signals. */
export function AiAnalysisBlock({ children, citations = [], title }: AiAnalysisBlockProps) {
  const t = useTranslations("provenance");
  return (
    <section
      data-ai-analysis-block
      className="rounded-card border-ai-border bg-ai-surface overflow-hidden border-[1.5px] border-dashed"
    >
      <header className="border-ai-border bg-ai-bg flex flex-wrap items-center gap-2 border-b border-dashed px-3 py-2">
        <SourceBadge type="ai" />
        <div className="min-w-0">
          {title ? <h3 className="text-ai text-[12px] font-semibold">{title}</h3> : null}
          <p className="text-ai text-[10px]">{t("aiHeader")}</p>
        </div>
      </header>
      <div className="text-fg-body px-3 py-3 font-sans text-[12px] leading-relaxed">{children}</div>
      {citations.length ? (
        <footer className="border-ai-border flex flex-wrap gap-2 border-t border-dashed px-3 py-2">
          {citations.map((citation) => (
            <CitationChip key={`${citation.docId}-${citation.display}`} citation={citation} />
          ))}
        </footer>
      ) : null}
    </section>
  );
}
