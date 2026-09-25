/**
 * Exact-source highlighting for the Reader.
 *
 * Provenance links carry the verbatim persisted source slice (`hl`). The
 * Reader marks that exact text inside the targeted paragraph (or page). Only
 * whitespace may differ, because parsed paragraphs re-flow line breaks; the
 * characters themselves must match exactly. Nothing fuzzy is ever marked.
 */

export const MAX_HIGHLIGHT_LENGTH = 200;

/** Adds the verbatim slice to a Reader link so the Reader can mark it. */
export function withExactSource(href: string, text: string): string {
  const slice = text.trim();
  if (!slice || slice.length > MAX_HIGHLIGHT_LENGTH) return href;
  return `${href}${href.includes("?") ? "&" : "?"}hl=${encodeURIComponent(slice)}`;
}

export function exactSourcePattern(text: string | undefined): RegExp | null {
  const tokens = (text ?? "").trim().split(/\s+/u).filter(Boolean);
  if (!tokens.length || text!.length > MAX_HIGHLIGHT_LENGTH) return null;
  const escaped = tokens.map((token) => token.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&"));
  // Whole tokens only: "Hashim Thaçi" is never marked inside "Hashim Thaçit".
  return new RegExp(`(?<![\\p{L}\\p{N}])${escaped.join("\\s+")}(?![\\p{L}\\p{N}])`, "gu");
}

/** Splits `text` into plain and exact-match parts, in order. */
export function splitExactSource(
  text: string,
  pattern: RegExp | null,
): { text: string; exact: boolean }[] {
  if (!pattern) return [{ text, exact: false }];
  const parts: { text: string; exact: boolean }[] = [];
  let last = 0;
  for (const match of text.matchAll(pattern)) {
    const start = match.index ?? 0;
    if (start > last) parts.push({ text: text.slice(last, start), exact: false });
    parts.push({ text: match[0], exact: true });
    last = start + match[0].length;
  }
  if (last < text.length) parts.push({ text: text.slice(last), exact: false });
  return parts.length ? parts : [{ text, exact: false }];
}
