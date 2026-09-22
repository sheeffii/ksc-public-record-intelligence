import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { resolveDataSource } from "@/data";

const appRoot = resolve(process.cwd(), "src/app");
const productionPages = [
  "page.tsx",
  "documents/page.tsx",
  "documents/[id]/page.tsx",
  "people/page.tsx",
  "people/[slug]/page.tsx",
  "witnesses/page.tsx",
  "witnesses/[code]/page.tsx",
  "witnesses/[code]/compare/page.tsx",
  "exhibits/page.tsx",
  "incidents/page.tsx",
  "incidents/[id]/page.tsx",
  "findings/page.tsx",
  "findings/[id]/page.tsx",
  "network/page.tsx",
  "network/path/page.tsx",
  "timeline/page.tsx",
  "search/page.tsx",
  "ai/page.tsx",
  "ai/[sessionId]/page.tsx",
  "appeal/page.tsx",
  "appeal/argument/[id]/page.tsx",
  "media/page.tsx",
  "public/page.tsx",
  "public/[topic]/page.tsx",
];

describe("Phase 15 route-level real-data gate", () => {
  it("defaults normal execution to the real API", () => {
    expect(resolveDataSource({})).toBe("api");
    expect(resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: "invalid" })).toBe("api");
    expect(resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: "mock" })).toBe("mock");
  });

  it.each(productionPages)("%s has no direct fixture dependency", (relativePath) => {
    const source = readFileSync(resolve(appRoot, relativePath), "utf8");
    expect(source).not.toMatch(/from ["']@\/mock/);
    expect(source).not.toMatch(/demo-person-|Demo record|F-DEMO-|I-DEMO-/);
  });

  it("tracks every audited normal route with no approved production demo dependency", () => {
    const audit = readFileSync(
      resolve(process.cwd(), "../../docs/quality/REAL_DATA_ROUTE_AUDIT.md"),
      "utf8",
    );
    for (const route of [
      "/documents",
      "/people",
      "/witnesses",
      "/exhibits",
      "/incidents",
      "/findings",
      "/network",
      "/timeline",
      "/search",
      "/ai",
      "/appeal",
      "/media",
      "/public",
    ]) {
      expect(audit).toContain(`\`${route}`);
    }
    expect(audit).not.toMatch(/\|\s*(MIXED|DEMO)\s*\|/);
  });
});
