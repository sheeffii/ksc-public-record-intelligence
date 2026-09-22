import { expect, test } from "@playwright/test";

test.skip(Boolean(process.env.E2E_REAL_DATA), "legacy demo-mode visual coverage");

/**
 * Phase 5B visual checks. Each representative screen is rendered at the
 * project's viewport, its designed regions are asserted, and a full-page
 * screenshot is written to test-results/visual/ for side-by-side comparison
 * with docs/design/Design.html. Screenshots are artefacts, not baselines:
 * layout drift is caught by the region assertions, not by pixel diffs.
 */
const SCREENS: { route: string; name: string; regions: string[] }[] = [
  { route: "/", name: "home", regions: ["Explore the record", "Ingestion health"] },
  {
    route: "/search?q=demo",
    name: "search",
    regions: ["Query interpretation", "Syntax reference"],
  },
  {
    route: "/people/demo-research-subject",
    name: "person",
    regions: ["Record References", "Cited summary"],
  },
  { route: "/witnesses/W01234", name: "witness", regions: ["Protected Witness", "Chronology"] },
  {
    route: "/witnesses/W01234/compare",
    name: "comparison",
    regions: ["A · Prior public statement", "Reviewer label"],
  },
  { route: "/documents/F01234?page=12", name: "reader", regions: ["Contents", "Footnotes"] },
  { route: "/findings/F-DEMO-01", name: "finding", regions: ["Chain index", "Source Audit"] },
  { route: "/exhibits", name: "exhibits", regions: ["Exhibit ID", "Detail"] },
  {
    route: "/incidents/I-DEMO-01",
    name: "incident",
    regions: ["Evidence matrix", "Direction summary"],
  },
  { route: "/timeline", name: "timeline", regions: ["Historical Events", "Card detail"] },
  { route: "/network", name: "network", regions: ["Legend", "Why does this connection exist?"] },
  {
    route: "/network/path",
    name: "path",
    regions: ["Hop inspector", "What a path cannot tell you"],
  },
  {
    route: "/appeal",
    name: "appeal",
    regions: ["Issue categories", "What this screen will not do"],
  },
  {
    route: "/appeal/argument/new",
    name: "argument-lab",
    regions: ["Citation health", "Neutral Reviewer"],
  },
  {
    route: "/ai",
    name: "ai",
    regions: ["Sources Used", "Below this line: generated analysis, not the record"],
  },
  {
    route: "/public",
    name: "public",
    regions: ["Before you begin", "What this finding does not mean"],
  },
];

for (const screen of SCREENS) {
  test(`visual: ${screen.name}`, async ({ page }, testInfo) => {
    await page.goto(screen.route);
    for (const region of screen.regions) {
      await expect(page.getByText(region, { exact: false }).first()).toBeAttached();
    }
    await expect(page.locator("[data-global-nav]")).toBeVisible();
    await page.screenshot({
      path: `test-results/visual/${testInfo.project.name}-${screen.name}.png`,
      fullPage: true,
    });
  });
}

test("mobile: network inspector leaves most of the canvas visible", async ({ page, isMobile }) => {
  test.skip(!isMobile, "mobile project only");
  await page.goto("/network");
  const canvas = page.getByRole("main", { name: "Network" });
  const box = await canvas.boundingBox();
  expect(box?.height ?? 0).toBeGreaterThan(300);
  const sheet = page.locator("details");
  const sheetBox = await sheet.boundingBox();
  const viewport = page.viewportSize()!;
  expect((sheetBox?.height ?? 0) / viewport.height).toBeLessThan(0.45);
});

test("mobile: finding chain stacks with a scroll-spy strip", async ({ page, isMobile }) => {
  test.skip(!isMobile, "mobile project only");
  await page.goto("/findings/F-DEMO-01");
  const rail = page.getByRole("navigation", { name: "Chain index" });
  await expect(rail).toBeVisible();
  await expect(page.getByText("Source Audit").first()).toBeAttached();
});
