import { describe, expect, it } from "vitest";
import { exactSourcePattern, splitExactSource, withExactSource } from "./exact-source";

describe("exact-source highlighting", () => {
  it("appends the verbatim slice to a Reader link", () => {
    expect(withExactSource("/documents/F1?page=2", "Hashim Thaçi")).toBe(
      "/documents/F1?page=2&hl=Hashim%20Tha%C3%A7i",
    );
    expect(withExactSource("/documents/F1", "W03877")).toBe("/documents/F1?hl=W03877");
    expect(withExactSource("/documents/F1", "x".repeat(201))).toBe("/documents/F1");
  });

  it("marks only the exact characters, tolerating re-flowed whitespace", () => {
    const pattern = exactSourcePattern("Hashim\nThaçi");
    expect(splitExactSource("Mr Hashim  Thaçi and Hashim Thaçit.", pattern)).toEqual([
      { text: "Mr ", exact: false },
      { text: "Hashim  Thaçi", exact: true },
      { text: " and Hashim Thaçit.", exact: false },
    ]);
    expect(splitExactSource("P01137 (a)", exactSourcePattern("P01137 (a)"))[0]).toEqual({
      text: "P01137 (a)",
      exact: true,
    });
    expect(splitExactSource("no match here", exactSourcePattern("W03877"))).toEqual([
      { text: "no match here", exact: false },
    ]);
    expect(exactSourcePattern("")).toBeNull();
  });
});
