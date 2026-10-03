import { describe, expect, it } from "vitest";
import type { DirectoryRow } from "./contract";
import { queryRows } from "./directory-query";

const row = (id: string, title: string, type: string, date: string): DirectoryRow => ({
  id,
  title,
  kind: "documents",
  description: type,
  date,
  references: 0,
  verification: "unreviewed",
  href: `/documents/${id}`,
  facets: { type },
});

const rows = [
  row("F00003", "Decision on detention", "decision", "2024-03-01"),
  row("F00001", "Order on scheduling", "order", "2022-01-05"),
  row("F00002", "Decision on disclosure", "decision", "2023-07-11"),
];

describe("queryRows", () => {
  it("pages a sorted result without losing or repeating rows", () => {
    const pages = [0, 1, 2].map(
      (offset) => queryRows(rows, { sort: "id", limit: 1, offset }).rows[0]?.id,
    );
    expect(pages).toEqual(["F00001", "F00002", "F00003"]);
    expect(queryRows(rows, { sort: "-date", limit: 3, offset: 0 }).rows.map((r) => r.id)).toEqual([
      "F00003",
      "F00002",
      "F00001",
    ]);
  });

  it("filters by facet and search with accurate totals", () => {
    const result = queryRows(rows, {
      q: "decision",
      facets: { type: ["decision"] },
      limit: 1,
      offset: 0,
    });
    expect(result.total).toBe(2);
    expect(result.unfilteredTotal).toBe(3);
    expect(result.rows).toHaveLength(1);
  });

  it("counts facet values over the rows matching the search text only", () => {
    expect(queryRows(rows, { limit: 10, offset: 0 }).facets.type).toEqual([
      ["decision", 2],
      ["order", 1],
    ]);
    expect(queryRows(rows, { q: "scheduling", limit: 10, offset: 0 }).facets.type).toEqual([
      ["order", 1],
    ]);
  });
});
