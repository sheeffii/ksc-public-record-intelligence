import { expect, test } from "@playwright/test";

/** Every approved route (ROUTE_MAP.md §2) with a representative identifier. */
const ROUTES = [
  "/",
  "/search",
  "/people",
  "/people/example-slug",
  "/witnesses",
  "/witnesses/W01234",
  "/witnesses/W01234/compare",
  "/documents",
  "/documents/F00482",
  "/exhibits",
  "/incidents",
  "/incidents/I-0042",
  "/timeline",
  "/findings",
  "/findings/F00482",
  "/network",
  "/network/path",
  "/appeal",
  "/appeal/argument/new",
  "/ai",
  "/ai/session-1",
  "/public",
  "/public/what-the-court-decided",
];

for (const route of ROUTES) {
  test(`${route} renders the application shell`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response?.status()).toBe(200);
    await expect(page.locator("[data-global-nav]")).toBeVisible();
    await expect(page.getByText("KSC-BC-2020-06").first()).toBeVisible();
  });
}

test("language toggle switches the interface to Shqip and back", async ({ page }) => {
  await page.goto("/findings");
  await page.getByRole("button", { name: "Interface language" }).click();
  await page.getByRole("menuitemradio", { name: /Shqip/ }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "sq");
  // The case stripe label is visible at every width (nav links hide below 860px).
  await expect(page.getByText("Çështja")).toBeVisible();
  await page.getByRole("button", { name: "Gjuha e ndërfaqes" }).click();
  await page.getByRole("menuitemradio", { name: /English/ }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByText("Case", { exact: true })).toBeVisible();
});

test("document reader renders on the light surface", async ({ page }) => {
  await page.goto("/documents/F00482");
  await expect(page.locator('[data-surface="light"]')).toBeVisible();
});
