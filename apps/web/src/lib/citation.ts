/**
 * Canonical citation formatting (HANDOFF.md §7).
 *
 *   Judgment · ¶8421–8427
 *   Transcript · 14 Mar 2024 · p. 12,453 · lines 8–19
 *   Exhibit P00123 · p. 4
 *   KSC-BC-2020-06/F01234/RED · ¶45
 *
 * This module formats only. It never decides whether a citation resolves —
 * that is persisted at ingest (ADR-005) and arrives as `resolved`.
 */

import type { Citation } from "@ksc/shared";

const SEP = " · ";
const RANGE = "–";

const numberFormatter = new Intl.NumberFormat("en-GB");

function formatNumber(n: number): string {
  return numberFormatter.format(n);
}

function range(from: number | undefined, to: number | undefined): string | undefined {
  if (from === undefined) return undefined;
  if (to === undefined || to === from) return formatNumber(from);
  return `${formatNumber(from)}${RANGE}${formatNumber(to)}`;
}

export interface CitationParts {
  ref: string;
  page?: number;
  paraFrom?: number;
  paraTo?: number;
  lineFrom?: number;
  lineTo?: number;
  /** Already formatted, e.g. "14 Mar 2024". Never translated. */
  date?: string;
}

/** Build the canonical display string from citation parts. */
export function formatCitation(parts: CitationParts): string {
  const segments: string[] = [parts.ref];
  if (parts.date) segments.push(parts.date);
  if (parts.page !== undefined) segments.push(`p. ${formatNumber(parts.page)}`);
  const paras = range(parts.paraFrom, parts.paraTo);
  if (paras) segments.push(`¶${paras}`);
  const lines = range(parts.lineFrom, parts.lineTo);
  if (lines) segments.push(`lines ${lines}`);
  return segments.join(SEP);
}

/** Href for the Document Reader at the cited position (ROUTE_MAP.md §5). */
export function citationHref(
  citation: Pick<Citation, "docId" | "page" | "paraFrom" | "paraTo">,
): string {
  const params = new URLSearchParams();
  if (citation.page !== undefined) params.set("page", String(citation.page));
  if (citation.paraFrom !== undefined) {
    params.set(
      "highlight",
      citation.paraTo !== undefined && citation.paraTo !== citation.paraFrom
        ? `${citation.paraFrom}-${citation.paraTo}`
        : String(citation.paraFrom),
    );
  }
  const query = params.toString();
  return `/documents/${encodeURIComponent(citation.docId)}${query ? `?${query}` : ""}`;
}
