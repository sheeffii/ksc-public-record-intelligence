import { expect, test } from "@playwright/test";

test.describe("Phase 12 real appeal research", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the controlled real corpus API");

  test("shows a source-backed issue with explicit record gaps", async ({ page }) => {
    await page.goto("/appeal");
    await expect(page.getByRole("heading", { name: "Potential Issues for Review" })).toBeVisible();
    await expect(
      page.getByRole("heading", {
        name: "Completeness of the public record for reviewing the First and Second Amendments",
      }),
    ).toBeVisible();
    await expect(page.getByText("Procedural Fairness").first()).toBeVisible();
    await expect(page.getByText("Addressed").first()).toBeVisible();
    await expect(page.getByText("Insufficient record").first()).toBeVisible();
    await expect(page.getByText(/F03743/).first()).toBeVisible();
    await expect(page.getByText(/F03746/).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Open exact source" }).first()).toHaveAttribute(
      "href",
      /\/documents\/F03752\?/,
    );
    await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
  });

  test("keeps all three red-team perspectives visible", async ({ page }) => {
    await page.goto("/appeal/argument/PIR-F03752-AMENDMENTS-RECORD");
    await expect(page.getByRole("heading", { name: "Defence Analyst" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "SPO Red Team" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Neutral Reviewer" })).toBeVisible();
    await expect(page.getByText("Insufficient record").first()).toBeVisible();
    await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
  });

  test("compares two exact passages without a credibility inference", async ({ page }) => {
    await page.goto("/witnesses/SC-F03752-P12-F03667-P160/compare");
    await expect(page.getByRole("heading", { name: "Statement Comparison" })).toBeVisible();
    await expect(page.getByText("Not Comparable", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Statement A" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Statement B" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Open exact source" })).toHaveCount(2);
    await expect(page.getByText(/No witness is labelled dishonest or unreliable/)).toBeVisible();
    await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
  });
});
