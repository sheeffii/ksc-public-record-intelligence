import { describe, expect, it } from "vitest";
import { ROUTES, getRoute, navKeyForPath, resolveTab } from "./routes";

const ROUTE_MAP_PATTERNS = [
  "/",
  "/search",
  "/people",
  "/people/:slug",
  "/witnesses",
  "/witnesses/:code",
  "/witnesses/:code/compare",
  "/documents",
  "/documents/:id",
  "/exhibits",
  "/incidents",
  "/incidents/:id",
  "/timeline",
  "/findings",
  "/findings/:id",
  "/network",
  "/network/path",
  "/appeal",
  "/media",
  "/appeal/argument/:id",
  "/ai",
  "/ai/:sessionId",
  "/public",
  "/public/:topic",
];

describe("route registry mirrors ROUTE_MAP.md §2 plus the Phase 14 extension", () => {
  it("contains every approved route exactly once", () => {
    expect(ROUTES.map((r) => r.pattern).sort()).toEqual([...ROUTE_MAP_PATTERNS].sort());
  });

  it("marks only the Document Reader and Public mode as light surfaces", () => {
    const light = ROUTES.filter((r) => r.mode === "light").map((r) => r.pattern);
    expect(light.sort()).toEqual(["/documents/:id", "/public", "/public/:topic"]);
  });

  it("leaves the directory-style and Phase 14 extension routes without an artboard", () => {
    const undesigned = ROUTES.filter((r) => r.artboard === null).map((r) => r.pattern);
    expect(undesigned.sort()).toEqual([
      "/documents",
      "/findings",
      "/incidents",
      "/media",
      "/people",
      "/witnesses",
    ]);
  });
});

describe("tab resolution (ROUTE_MAP.md §4)", () => {
  it("defaults to the first tab and falls back silently on unknown values", () => {
    const route = getRoute("witnessDossier");
    expect(resolveTab(route, undefined)).toBe("overview");
    expect(resolveTab(route, "cross")).toBe("cross");
    expect(resolveTab(route, "nonsense")).toBe("overview");
  });
});

describe("navKeyForPath", () => {
  it("maps nested routes to their section", () => {
    expect(navKeyForPath("/")).toBe("home");
    expect(navKeyForPath("/witnesses/W01234/compare")).toBe("witnesses");
    expect(navKeyForPath("/network/path")).toBe("network");
    expect(navKeyForPath("/appeal/argument/new")).toBe("appeal");
    expect(navKeyForPath("/media")).toBe("media");
    expect(navKeyForPath("/ai/abc")).toBe("ai");
  });
});
