import { describe, expect, it } from "vitest";
import { citationHref, formatCitation } from "./citation";

describe("formatCitation — canonical forms from HANDOFF.md §7", () => {
  it("formats a judgment paragraph range", () => {
    expect(formatCitation({ ref: "Judgment", paraFrom: 8421, paraTo: 8427 })).toBe(
      "Judgment · ¶8,421–8,427",
    );
  });

  it("formats a transcript page and line range with a date", () => {
    expect(
      formatCitation({
        ref: "Transcript",
        date: "14 Mar 2024",
        page: 12453,
        lineFrom: 8,
        lineTo: 19,
      }),
    ).toBe("Transcript · 14 Mar 2024 · p. 12,453 · lines 8–19");
  });

  it("formats an exhibit page", () => {
    expect(formatCitation({ ref: "Exhibit P00123", page: 4 })).toBe("Exhibit P00123 · p. 4");
  });

  it("formats a filing reference with a single paragraph, identifier untouched", () => {
    expect(formatCitation({ ref: "KSC-BC-2020-06/F01234/RED", paraFrom: 45 })).toBe(
      "KSC-BC-2020-06/F01234/RED · ¶45",
    );
  });

  it("collapses a range whose ends are equal", () => {
    expect(formatCitation({ ref: "Judgment", paraFrom: 12, paraTo: 12 })).toBe("Judgment · ¶12");
  });
});

describe("citationHref — deep links into the Document Reader", () => {
  it("carries page and paragraph anchor", () => {
    expect(citationHref({ docId: "F00482", page: 894, paraFrom: 8422 })).toBe(
      "/documents/F00482?page=894&highlight=8422",
    );
  });

  it("carries a paragraph range", () => {
    expect(citationHref({ docId: "F00482", page: 894, paraFrom: 8421, paraTo: 8427 })).toBe(
      "/documents/F00482?page=894&highlight=8421-8427",
    );
  });

  it("uses the record's own identifier verbatim", () => {
    expect(citationHref({ docId: "KSC-BC-2020-06/F01234/RED" })).toBe(
      "/documents/KSC-BC-2020-06%2FF01234%2FRED",
    );
  });
});
