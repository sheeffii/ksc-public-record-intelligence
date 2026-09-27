import { describe, expect, it } from "vitest";

import { groupBySource, pageTally, versionHref } from "./source-groups";

type Row = { id: string; version: string; page?: number };

const locate = (row: Row) => ({
  versionRef: row.version,
  title: `Title ${row.version}`,
  documentHref: `/documents/x?version=${row.version}`,
  page: row.page,
});

describe("groupBySource", () => {
  it("keeps every occurrence, in order, under one group per exact version", () => {
    const rows: Row[] = [
      { id: "1", version: "F00002/RED/A01", page: 3 },
      { id: "2", version: "F00045/RED", page: 1 },
      { id: "3", version: "F00002/RED/A01", page: 4 },
      { id: "4", version: "F00002/RED/A01", page: 3 },
      { id: "5", version: "F00002/RED/A01" },
    ];
    const groups = groupBySource(rows, locate);
    expect(groups.map((g) => g.versionRef)).toEqual(["F00002/RED/A01", "F00045/RED"]);
    expect(groups[0]!.items.map((r) => r.id)).toEqual(["1", "3", "4", "5"]);
    expect(groups.flatMap((g) => g.items)).toHaveLength(rows.length);
    expect(pageTally(groups[0]!.pages)).toBe("p.3 ×2, p.4");
    expect(groups[0]!.withoutPage).toBe(1);
  });

  it("never merges different versions or languages of one filing", () => {
    const groups = groupBySource(
      [
        { id: "en", version: "F00026/RED" },
        { id: "sq", version: "F00026/RED/sqi" },
        { id: "red2", version: "F00026/RED2" },
      ],
      locate,
    );
    expect(groups).toHaveLength(3);
  });

  it("keeps semantic states apart when the key says so", () => {
    const rows = [
      { id: "a", version: "F1", state: "verified" },
      { id: "b", version: "F1", state: "review_required" },
    ];
    const groups = groupBySource(rows, (r) => ({ ...locate(r), key: `${r.version}|${r.state}` }));
    expect(groups).toHaveLength(2);
  });
});

describe("versionHref", () => {
  it("drops only the occurrence coordinates, keeping document and version", () => {
    expect(
      versionHref(
        "/documents/transcript?document=F00002%2FA01&version=KSC-BC-2020-06%2FF00002%2FRED%2FA01&pdfPage=2&page=3&anchor=abc&hl=Krasniqi",
      ),
    ).toBe(
      "/documents/transcript?document=F00002%2FA01&version=KSC-BC-2020-06%2FF00002%2FRED%2FA01",
    );
    expect(versionHref("/documents/F00001")).toBe("/documents/F00001");
  });
});
