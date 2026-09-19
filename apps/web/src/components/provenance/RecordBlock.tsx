import type { Citation, CitableSourceType } from "@ksc/shared";
import type { ReactNode } from "react";
import { CitationChip } from "./CitationChip";
import { SourceBadge } from "./SourceBadge";

export interface RecordBlockProps {
  sourceType: CitableSourceType;
  children: ReactNode;
  citations?: readonly Citation[];
  title?: ReactNode;
}

/** Solid, source-coloured container reserved for material from the public record. */
export function RecordBlock({ sourceType, children, citations = [], title }: RecordBlockProps) {
  return (
    <section
      data-record-block
      data-source={sourceType}
      className="rounded-card border-border bg-surface overflow-hidden border border-l-[3px]"
      style={{ borderLeftColor: `var(--${sourceType === "exhibit" ? "doc" : sourceType})` }}
    >
      <header className="border-border-subtle bg-surface-raised flex flex-wrap items-center gap-2 border-b px-3 py-2">
        <SourceBadge type={sourceType} />
        {title ? <h3 className="text-fg text-[12px] font-semibold">{title}</h3> : null}
      </header>
      <div className="text-fg-body px-3 py-3 text-[12px] leading-relaxed">{children}</div>
      {citations.length ? (
        <footer className="border-border-subtle flex flex-wrap gap-2 border-t px-3 py-2">
          {citations.map((citation) => (
            <CitationChip key={`${citation.docId}-${citation.display}`} citation={citation} />
          ))}
        </footer>
      ) : null}
    </section>
  );
}
