import { expect, test } from "@playwright/test";

test.describe("Phase 18 Pass B research experience gate", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the Phase 17 real corpus API");

  const routes = [
    "/",
    "/search?q=P00003",
    "/documents/F03752?pdfPage=0",
    "/people/accused-krasniqi",
    "/witnesses/W00016",
    "/exhibits/P00003",
    "/organizations/nato",
    "/findings/FD-F03752-P12-16",
    "/network?focus=P00003",
    "/timeline",
  ];

  for (const route of routes) {
    test(`${route} renders real data without UUID-first presentation`, async ({ page }) => {
      const response = await page.goto(route);
      expect(response?.status()).toBe(200);
      await expect(page.locator("[data-global-nav]")).toBeVisible();
      await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
      await expect(page.locator("body")).not.toContainText(
        /demo-person-|Demo record|F-DEMO-|I-DEMO-/i,
      );
      const visibleText = await page.locator("body").innerText();
      expect(visibleText).not.toMatch(
        /\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b/i,
      );
    });
  }

  test("search reaches an exhibit dossier and its exact court source", async ({ page }) => {
    await page.goto("/search?q=P00003");
    await page
      .getByRole("link", { name: /Exhibit P00003/i })
      .first()
      .click();
    await expect(page).toHaveURL(/\/exhibits\/P00003/);
    await expect(page.getByText("Source occurrences")).toBeVisible();
    const source = page.getByRole("link", { name: "Open exact source" }).first();
    await expect(source).toHaveAttribute("href", /\/documents\//);
    await source.click();
    await expect(page).toHaveURL(/\/documents\//);
    await expect(page.locator('[data-surface="light"]')).toBeVisible();
  });

  test("person occurrence opens the exact court source", async ({ page }) => {
    await page.goto("/people/accused-krasniqi");
    await expect(page.getByText("Source occurrences")).toBeVisible();
    const source = page.getByRole("link", { name: "Open exact source" }).first();
    await expect(source).toHaveAttribute("href", /\/documents\/.*pdfPage=\d+/);
    await source.click();
    await expect(page).toHaveURL(/\/documents\/.*pdfPage=\d+/);
    await expect(page.locator('[data-surface="light"]')).toBeVisible();
  });

  test("protected witness testimony opens the exact transcript line", async ({ page }) => {
    await page.goto("/witnesses/W03865");
    await expect(page.getByRole("heading", { name: "W03865" }).first()).toBeVisible();
    const transcript = page
      .getByRole("link", { name: "Open exact source" })
      .and(page.locator('[href*="/documents/transcript"]'))
      .first();
    await expect(transcript).toHaveAttribute("href", /line=\d+/);
    await transcript.click();
    await expect(page).toHaveURL(/\/documents\/transcript\?.*line=\d+/);
    await expect(page.locator('[data-surface="light"]')).toBeVisible();
  });

  test("focused network exposes edge provenance on desktop and mobile", async ({
    page,
    isMobile,
  }) => {
    await page.goto("/network?focus=P00003");
    await expect(page.getByRole("region", { name: "Network" })).toBeVisible();
    await expect(page.getByText("Why does this connection exist?")).toBeVisible();
    if (isMobile) {
      await page.getByRole("button", { name: "peek" }).click();
      await page.getByRole("button", { name: "half" }).click();
    }
    await expect(
      page.getByRole("region", { name: "Network" }).getByRole("button", { name: "P00003" }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: /Open source/i }).first()).toBeVisible();
  });
});
