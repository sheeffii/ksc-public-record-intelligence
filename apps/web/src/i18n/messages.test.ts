import { describe, expect, it } from "vitest";
import en from "./messages/en.json";
import sq from "./messages/sq.json";

function flatten(obj: Record<string, unknown>, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === "object"
      ? flatten(v as Record<string, unknown>, `${prefix}${k}.`)
      : [`${prefix}${k}`],
  );
}

describe("string tables", () => {
  it("English and Albanian carry exactly the same keys", () => {
    expect(flatten(sq).sort()).toEqual(flatten(en).sort());
  });

  it("never translate the UNRESOLVED literal", () => {
    expect(en.citation.unresolved).toBe("UNRESOLVED");
    expect(sq.citation.unresolved).toBe("UNRESOLVED");
  });

  it("never use predictive appeal language in the system's own voice", () => {
    const banned = /appeal (risk|strength)|success (score|probability)|likelihood of success/i;
    for (const table of [en, sq]) {
      for (const value of flatten(table).map((k) =>
        k
          .split(".")
          .reduce(
            (o, p) => (o as Record<string, unknown>)[p] as Record<string, unknown>,
            table as unknown as Record<string, unknown>,
          ),
      )) {
        expect(String(value)).not.toMatch(banned);
      }
    }
    expect(en.screens.appeal).toBe("Potential Issues for Review");
  });
});
