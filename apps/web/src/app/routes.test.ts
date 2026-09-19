import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { ROUTES } from "@/lib/routes";

/** ROUTE_MAP.md pattern → App Router directory. */
function appDirFor(pattern: string): string {
  if (pattern === "/") return "";
  return pattern
    .split("/")
    .filter(Boolean)
    .map((seg) => (seg.startsWith(":") ? `[${seg.slice(1)}]` : seg))
    .join("/");
}

describe("App Router has a page for every approved route", () => {
  it.each(ROUTES.map((r) => r.pattern))("%s", (pattern) => {
    const file = path.join(__dirname, appDirFor(pattern), "page.tsx");
    expect(existsSync(file), `missing ${file}`).toBe(true);
  });

  it.each(ROUTES.filter((route) => route.pattern !== "/").map((route) => route.pattern))(
    "%s no longer renders the Phase 4 placeholder",
    (pattern) => {
      const file = path.join(__dirname, appDirFor(pattern), "page.tsx");
      expect(readFileSync(file, "utf8")).not.toContain("PlaceholderScreen");
    },
  );
});
