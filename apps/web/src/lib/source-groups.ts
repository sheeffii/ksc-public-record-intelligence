/**
 * Group source-backed occurrences by the exact document version they come
 * from, so "1 document, 8 occurrences" replaces eight repeated cards.
 *
 * Rules: groups never merge different versions or languages (the key is the
 * exact version reference); every occurrence stays in its group, in order;
 * callers keep semantic states apart by grouping each state separately.
 */

export interface SourceLocation {
  /** Grouping key; defaults to `versionRef`. It must include the version so
   * different versions or languages never share a group. */
  key?: string;
  /** Exact version reference (e.g. `KSC-BC-2020-06/F00002/RED/A01`). */
  versionRef: string;
  title: string;
  /** Link to the version itself (no anchor). */
  documentHref: string;
  page?: number;
}

export interface SourceGroup<T> {
  key: string;
  versionRef: string;
  title: string;
  documentHref: string;
  items: readonly T[];
  /** Page tallies in page order; occurrences without a page are counted apart. */
  pages: readonly { page: number; count: number }[];
  withoutPage: number;
}

export function groupBySource<T>(
  items: readonly T[],
  locate: (item: T) => SourceLocation,
): SourceGroup<T>[] {
  const groups = new Map<
    string,
    { first: SourceLocation; items: T[]; pages: Map<number, number>; withoutPage: number }
  >();
  for (const item of items) {
    const location = locate(item);
    const key = location.key ?? location.versionRef;
    let group = groups.get(key);
    if (!group) {
      group = { first: location, items: [], pages: new Map(), withoutPage: 0 };
      groups.set(key, group);
    }
    group.items.push(item);
    if (location.page === undefined) group.withoutPage += 1;
    else group.pages.set(location.page, (group.pages.get(location.page) ?? 0) + 1);
  }
  return [...groups.entries()].map(([key, group]) => ({
    key,
    versionRef: group.first.versionRef,
    title: group.first.title,
    documentHref: group.first.documentHref,
    items: group.items,
    pages: [...group.pages.entries()]
      .sort(([a], [b]) => a - b)
      .map(([page, count]) => ({ page, count })),
    withoutPage: group.withoutPage,
  }));
}

/** `p.3 ×4, p.4 ×3, p.13` — page numbers are official printed pages. */
export function pageTally(pages: SourceGroup<unknown>["pages"]): string {
  return pages
    .map(({ page, count }) => (count > 1 ? `p.${page} ×${count}` : `p.${page}`))
    .join(", ");
}

/** The version link behind an exact-occurrence link: same document and
 * version, without the page/anchor that point at one occurrence. */
export function versionHref(href: string): string {
  const cut = href.indexOf("?");
  if (cut < 0) return href;
  const path = href.slice(0, cut);
  const params = new URLSearchParams(href.slice(cut + 1));
  for (const key of ["anchor", "pdfPage", "page", "line", "paragraph", "hl"]) {
    params.delete(key);
  }
  const rest = params.toString();
  return rest ? `${path}?${rest}` : path;
}
