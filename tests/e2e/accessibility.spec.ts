import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const routes = ["/", "/search?q=F00001", "/documents", "/network", "/timeline", "/ai"];

for (const route of routes) {
  test(`${route} has no serious or critical automated accessibility violations`, async ({
    page,
  }) => {
    await page.goto(route);
    await expect(page.locator("main")).toBeVisible();
    const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    const blocking = result.violations.filter(
      ({ impact }) => impact === "serious" || impact === "critical",
    );
    expect(blocking).toEqual([]);
  });
}
