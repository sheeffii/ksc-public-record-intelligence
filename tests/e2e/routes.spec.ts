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

test("Flow A: search to person, network connection and source", async ({ page }) => {
  await page.goto("/search?q=Demo%20Research%20Subject");
  await page
    .getByRole("link", { name: /Demo Research Subject/ })
    .first()
    .click();
  await expect(page).toHaveURL(/\/people\/demo-research-subject/);
  await page.getByRole("link", { name: "View Network" }).click();
  await expect(page).toHaveURL(/\/network/);
  await expect(page.getByText("Why does this connection exist?")).toBeVisible();
  await page.getByRole("link", { name: "Open source" }).click();
  await expect(page).toHaveURL(/\/documents\//);
});

test("Flow B: protected witness testimony to statement comparison", async ({ page }) => {
  await page.goto("/witnesses/W01234");
  await expect(page.getByText("Protected Witness").first()).toBeVisible();
  await page.getByRole("link", { name: "Statement Comparison" }).last().click();
  await expect(page).toHaveURL(/\/witnesses\/W01234\/compare/);
  await expect(page.getByText("Prior Public Statements")).toBeVisible();
});

test("Flow C: judgment passage to finding and evidence", async ({ page }) => {
  await page.goto("/documents/F01234?page=12&highlight=45");
  await page
    .getByRole("link", { name: /Court Findings/ })
    .last()
    .click();
  await expect(page).toHaveURL(/\/findings\/F-DEMO-01/);
  await expect(page.getByText("Evidence Relied Upon").first()).toBeVisible();
});

test("Flow D: finding potential issue to red team workspace", async ({ page }) => {
  await page.goto("/findings/F-DEMO-01");
  await expect(page.getByText("Potential Issues for Review").first()).toBeVisible();
  await page.getByRole("link", { name: "Send to Argument Lab" }).click();
  await expect(page).toHaveURL(/\/appeal\/argument\/new/);
  await expect(page.getByText("SPO Red Team").first()).toBeVisible();
});

test("Flow E: AI citation preview before original source", async ({ page }) => {
  await page.goto("/ai");
  await expect(page.getByText("Below this line: generated analysis, not the record")).toBeVisible();
  await page
    .getByRole("button", { name: /F01234 · ¶45–46/ })
    .first()
    .click();
  await page.getByRole("link", { name: /Open document/ }).click();
  await expect(page).toHaveURL(/\/documents\/F01234/);
});

test("Flow F: dossier to evidence path with per-hop citations", async ({ page }) => {
  await page.goto("/people/demo-research-subject");
  await page.getByRole("link", { name: "Find Record Connection" }).click();
  await expect(page).toHaveURL(/\/network\/path/);
  await expect(
    page.getByText("These records reference one another. That is all a path shows."),
  ).toBeVisible();
  await expect(page.getByText("What a path cannot tell you")).toBeVisible();
});
