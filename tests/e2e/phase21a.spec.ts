import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test.describe("Phase 21A design parity and real research flows", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the real corpus API");

  test("captures Home, Search, Documents and Evidence at 1440, 1024 and Pixel 7", async ({
    browser,
  }, testInfo) => {
    test.skip(testInfo.project.name !== "desktop", "one capture matrix is sufficient");
    const routes = [
      ["home", "/"],
      ["search", "/search?q=F03668"],
      ["documents", "/documents"],
      ["evidence", "/exhibits"],
    ] as const;
    const viewports = [
      ["desktop-1440", 1440, 1000],
      ["laptop-1024", 1024, 900],
      ["pixel-7", 412, 915],
    ] as const;
    for (const [viewportName, width, height] of viewports) {
      const page = await browser.newPage({ viewport: { width, height } });
      for (const [routeName, path] of routes) {
        await page.goto(path);
        await expect(page.locator("main")).toBeVisible();
        expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
          width,
        );
        await testInfo.attach(`${viewportName}-${routeName}`, {
          body: await page.screenshot(),
          contentType: "image/png",
        });
      }
      await page.close();
    }
  });

  test("global command search returns real best matches and opens the source", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Control+K");
    const input = page.getByPlaceholder("Type an identifier, name or phrase");
    await input.fill("F03668");
    await expect(page.getByText("Record pattern detected")).toBeVisible();
    const bestMatch = page.getByRole("link", { name: /KSC-BC-2020-06\/F03668/ }).first();
    await expect(bestMatch).toBeVisible();
    await bestMatch.click();
    await expect(page).toHaveURL(/\/documents\//);
    await expect(page.getByRole("button", { name: "Original PDF" })).toBeVisible();
  });

  test("Search and Documents retain exact Phase 20 source navigation", async ({ page }) => {
    await page.goto("/search?q=F03668");
    const source = page.getByRole("link", { name: /Open exact source/ }).first();
    await expect(source).toHaveAttribute("href", /\/documents\//);
    await source.click();
    await expect(page.getByRole("button", { name: "Original PDF" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(page.getByLabel(/PDF page/)).toBeVisible();

    await page.goto("/documents");
    await page.locator("tr[data-row-id]").first().click();
    await page.getByRole("link", { name: "Open exact source" }).click();
    await expect(page).toHaveURL(/\/documents\//);
    await expect(page.getByLabel(/PDF page/)).toBeVisible();
  });

  test("Evidence preserves real status and dossier actions", async ({ page }) => {
    await page.goto("/exhibits");
    const search = page.getByRole("searchbox");
    await search.fill("P01137");
    await expect(page.locator('tr[data-row-id="P01137"]')).toBeVisible();
    await page.locator('tr[data-row-id="P01137"]').click();
    await page.getByRole("link", { name: "Open dossier" }).click();
    await expect(page).toHaveURL(/\/exhibits\/P01137/);
    const history = page.locator("section").filter({ hasText: "Status history" });
    await expect(history.getByText("Admitted").first()).toBeVisible();
  });

  test("changed research entry routes have no automated accessibility violations", async ({
    page,
  }) => {
    for (const path of ["/", "/search?q=F03668", "/documents", "/exhibits"]) {
      await page.goto(path);
      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations, `${path}: ${JSON.stringify(results.violations)}`).toEqual([]);
    }
  });
});
