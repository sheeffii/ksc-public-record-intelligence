import { expect, test } from "@playwright/test";

test.describe("Phase 14 external public sources", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the controlled real public-source API");

  test("keeps external material visibly separate from the court record", async ({ page }) => {
    await page.goto("/media");

    await expect(
      page.getByRole("heading", { name: "External media and public statements" }),
    ).toBeVisible();
    await expect(page.getByText("EXTERNAL PUBLIC SOURCE").first()).toBeVisible();
    await expect(page.getByText("EXTERNAL ONLY").first()).toBeVisible();
    await expect(page.getByRole("link", { name: /Open public source/ }).first()).toHaveAttribute(
      "href",
      /^https:\/\//,
    );
    await expect(page.getByText("NOT COMPARABLE")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Coverage limitations" })).toBeVisible();
    await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
  });

  test("offers explicit source-scope modes without combining result panels", async ({ page }) => {
    await page.goto("/media");
    const sourceScope = page.getByLabel("Source scope");

    await expect(sourceScope).toHaveValue("external");
    await expect(sourceScope.locator("option")).toHaveText([
      "Court Record Only",
      "External Public Sources",
      "Both — clearly separated",
    ]);

    await sourceScope.selectOption("court");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(page).toHaveURL(/scope=court/);
    await expect(page.getByRole("heading", { name: "Court-record results" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "External public sources" })).toHaveCount(0);
  });
});
