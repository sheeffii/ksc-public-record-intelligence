import { expect, test } from "@playwright/test";

test.describe("Phase 15 production real-data routes", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the controlled real corpus API");

  const productionRoutes = [
    "/",
    "/documents",
    "/people",
    "/witnesses",
    "/exhibits",
    "/incidents",
    "/findings",
    "/network",
    "/network/path",
    "/timeline",
    "/search?q=F03752",
    "/ai",
    "/appeal",
    "/media",
    "/public",
  ];

  for (const route of productionRoutes) {
    test(`${route} renders without demo fallback`, async ({ page }) => {
      const response = await page.goto(route);
      expect(response?.status()).toBe(200);
      await expect(page.locator("[data-global-nav]")).toBeVisible();
      await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
      await expect(page.locator("body")).not.toContainText(
        /demo-person-|Demo record|F-DEMO-|I-DEMO-/i,
      );
    });
  }

  test("reader renders parsed court text with exact-source metadata", async ({
    page,
    isMobile,
  }) => {
    await page.goto("/documents/F03752?pdfPage=0");
    await expect(page.locator('[data-surface="light"]')).toBeVisible();
    await expect(page.getByText("F03752 · PDF index 0", { exact: true })).toBeVisible();
    await expect(page.getByText("No parsed public content", { exact: false })).toHaveCount(0);
    if (isMobile) await page.getByRole("button", { name: "Research panel" }).click();
    await expect(page.getByRole("link", { name: /official source/i })).toHaveAttribute(
      "href",
      /^https:\/\//,
    );
    await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
  });

  test("network renders readable nodes and provenance-backed relationships", async ({ page }) => {
    await page.goto("/network");
    const graph = page.getByRole("region", { name: "Network" });
    await expect(graph.getByRole("button").first()).toBeVisible();
    await expect(page.getByText("Why does this connection exist?")).toBeVisible();
    await expect(page.getByText(/→.*· cited in/i).first()).toBeVisible();
    await expect(graph.locator("svg line").first()).toBeAttached();
  });

  test("empty source-backed directories stay honest", async ({ page }) => {
    for (const route of ["/people", "/witnesses", "/exhibits", "/incidents"]) {
      await page.goto(route);
      await expect(page.getByText(/No verified|No public|No source-backed/i).first()).toBeVisible();
      await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
    }
  });

  test("court findings and external sources remain visibly separated", async ({ page }) => {
    await page.goto("/findings/FD-F03752-P12-16");
    await expect(page.getByText("COURT FINDING").first()).toBeVisible();
    await expect(page.locator("[data-demo-flag]")).toHaveCount(0);

    await page.goto("/media");
    await expect(page.getByText("EXTERNAL PUBLIC SOURCE").first()).toBeVisible();
    await expect(page.getByText("EXTERNAL ONLY").first()).toBeVisible();
    await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
  });
});
