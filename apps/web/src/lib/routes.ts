/**
 * Route registry — transcribed from docs/design/ROUTE_MAP.md §2.
 *
 * Every approved route renders the application shell. The case prefix is
 * omitted: everything is scoped to KSC-BC-2020-06. Identifiers in routes are
 * the record's own (W01234, P00441, F00482) and are never re-keyed.
 */

import type { Messages } from "@/i18n/messages";

export type ScreenKey = keyof Messages["screens"];
export type NavKey = keyof Messages["nav"];

export type SurfaceMode = "dark" | "light";

export interface RouteSpec {
  key: ScreenKey;
  /** Path pattern as written in ROUTE_MAP.md. */
  pattern: string;
  /** Artboard number, or null for the five undesigned directory routes. */
  artboard: string | null;
  mode: SurfaceMode;
  /** Section the GlobalNav highlights for this route. */
  nav: NavKey;
  /** Tab set for ?tab= (ROUTE_MAP.md §4). */
  tabs?: readonly string[];
}

export const ROUTES: readonly RouteSpec[] = [
  { key: "home", pattern: "/", artboard: "02", mode: "dark", nav: "home" },
  { key: "search", pattern: "/search", artboard: "06", mode: "dark", nav: "search" },
  { key: "people", pattern: "/people", artboard: null, mode: "dark", nav: "people" },
  {
    key: "personDossier",
    pattern: "/people/:slug",
    artboard: "07",
    mode: "dark",
    nav: "people",
    tabs: [
      "overview",
      "documents",
      "testimony",
      "exhibits",
      "incidents",
      "timeline",
      "findings",
      "arguments",
      "network",
      "appeal",
    ],
  },
  { key: "witnesses", pattern: "/witnesses", artboard: null, mode: "dark", nav: "witnesses" },
  {
    key: "witnessDossier",
    pattern: "/witnesses/:code",
    artboard: "08",
    mode: "dark",
    nav: "witnesses",
    tabs: [
      "overview",
      "testimony",
      "cross",
      "prior-statements",
      "exhibits",
      "findings",
      "comparison",
      "timeline",
      "network",
      "ai",
    ],
  },
  {
    key: "statementComparison",
    pattern: "/witnesses/:code/compare",
    artboard: "09",
    mode: "dark",
    nav: "witnesses",
  },
  { key: "documents", pattern: "/documents", artboard: null, mode: "dark", nav: "documents" },
  {
    key: "documentReader",
    pattern: "/documents/:id",
    artboard: "04",
    mode: "light",
    nav: "documents",
  },
  { key: "exhibits", pattern: "/exhibits", artboard: "10", mode: "dark", nav: "exhibits" },
  { key: "incidents", pattern: "/incidents", artboard: null, mode: "dark", nav: "incidents" },
  {
    key: "incidentDetail",
    pattern: "/incidents/:id",
    artboard: "11",
    mode: "dark",
    nav: "incidents",
    tabs: [
      "overview",
      "findings",
      "witnesses",
      "evidence",
      "spo",
      "defence",
      "timeline",
      "network",
      "issues",
    ],
  },
  { key: "timeline", pattern: "/timeline", artboard: "12", mode: "dark", nav: "timeline" },
  { key: "findings", pattern: "/findings", artboard: null, mode: "dark", nav: "findings" },
  {
    key: "findingDetail",
    pattern: "/findings/:id",
    artboard: "05",
    mode: "dark",
    nav: "findings",
    tabs: ["chain", "quotes", "arguments", "annotations"],
  },
  { key: "network", pattern: "/network", artboard: "03", mode: "dark", nav: "network" },
  { key: "evidencePath", pattern: "/network/path", artboard: "20", mode: "dark", nav: "network" },
  { key: "appeal", pattern: "/appeal", artboard: "13", mode: "dark", nav: "appeal" },
  { key: "media", pattern: "/media", artboard: null, mode: "dark", nav: "media" },
  {
    key: "argumentLab",
    pattern: "/appeal/argument/:id",
    artboard: "14",
    mode: "dark",
    nav: "appeal",
  },
  { key: "ai", pattern: "/ai", artboard: "15", mode: "dark", nav: "ai" },
  { key: "aiSession", pattern: "/ai/:sessionId", artboard: "15", mode: "dark", nav: "ai" },
  { key: "public", pattern: "/public", artboard: "16", mode: "light", nav: "public" },
  { key: "publicTopic", pattern: "/public/:topic", artboard: "16", mode: "light", nav: "public" },
] as const;

export function getRoute(key: ScreenKey): RouteSpec {
  const route = ROUTES.find((r) => r.key === key);
  if (!route) throw new Error(`Unknown route key: ${key}`);
  return route;
}

/** Primary navigation, in display order. AI is always last and always AI-coloured. */
export interface NavItem {
  key: NavKey;
  href: string;
  /** Rendered in --ai and never given the active pill (COMPONENTS.md §1). */
  isAi?: boolean;
  /** Collapses into the overflow menu first at narrow widths. */
  overflow?: boolean;
}

export const PRIMARY_NAV: readonly NavItem[] = [
  { key: "home", href: "/" },
  { key: "people", href: "/people" },
  { key: "witnesses", href: "/witnesses" },
  { key: "documents", href: "/documents" },
  { key: "exhibits", href: "/exhibits" },
  { key: "timeline", href: "/timeline", overflow: true },
  { key: "network", href: "/network" },
  { key: "findings", href: "/findings" },
  { key: "incidents", href: "/incidents", overflow: true },
  { key: "appeal", href: "/appeal", overflow: true },
  { key: "media", href: "/media", overflow: true },
  { key: "ai", href: "/ai", isAi: true },
];

/** Five-item bottom tab bar (PAGE_SPECS.md §17). */
export const MOBILE_NAV = [
  { key: "home", href: "/" },
  { key: "search", href: "/search" },
  { key: "network", href: "/network" },
  { key: "docs", href: "/documents" },
  { key: "ai", href: "/ai" },
] as const;

/** Which nav section a pathname belongs to. */
export function navKeyForPath(pathname: string): NavKey {
  if (pathname === "/") return "home";
  const first = `/${pathname.split("/")[1] ?? ""}`;
  if (first === "/organizations") return "people";
  const match = ROUTES.find((r) => r.pattern === first || r.pattern.startsWith(`${first}/`));
  return match?.nav ?? "home";
}

/** Resolve `?tab=` against a route's tab set; unknown values fall back silently. */
export function resolveTab(route: RouteSpec, value: string | null | undefined): string | undefined {
  if (!route.tabs) return undefined;
  const fallback = route.tabs[0];
  if (!value) return fallback;
  return route.tabs.includes(value) ? value : fallback;
}
