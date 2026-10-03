import type { DirectoryQuery, DirectoryResult, DirectoryRow } from "./contract";

/**
 * The directory search/filter/sort/page semantics the API implements, applied
 * to rows already in memory (fixture mode). Search matches the identifier,
 * title and description; facet counts cover the rows matching the search text.
 */
export function queryRows(rows: readonly DirectoryRow[], query: DirectoryQuery): DirectoryResult {
  const needle = (query.q ?? "").trim().toLowerCase();
  const searched = rows.filter(
    (row) => !needle || `${row.id} ${row.title} ${row.description}`.toLowerCase().includes(needle),
  );
  const facets = query.facets ?? {};
  const filtered = searched.filter((row) =>
    Object.entries(facets).every(
      ([key, values]) => !values.length || values.includes(row.facets?.[key] ?? ""),
    ),
  );
  const sort = query.sort ?? "";
  const descending = sort.startsWith("-");
  const key = sort.replace(/^-/, "") as keyof DirectoryRow;
  const ordered = sort
    ? [...filtered].sort((a, b) => {
        const av = a[key];
        const bv = b[key];
        const cmp =
          typeof av === "number" && typeof bv === "number"
            ? av - bv
            : String(av ?? "").localeCompare(String(bv ?? ""));
        return (cmp || a.id.localeCompare(b.id)) * (descending ? -1 : 1);
      })
    : filtered;
  const counts: Record<string, Map<string, number>> = {};
  for (const row of searched) {
    for (const [facet, value] of Object.entries(row.facets ?? {})) {
      if (!value) continue;
      const map = (counts[facet] ??= new Map());
      map.set(value, (map.get(value) ?? 0) + 1);
    }
  }
  return {
    rows: ordered.slice(query.offset, query.offset + query.limit),
    total: filtered.length,
    unfilteredTotal: rows.length,
    facets: Object.fromEntries(
      Object.entries(counts).map(([facet, map]) => [
        facet,
        [...map.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])),
      ]),
    ),
  };
}
