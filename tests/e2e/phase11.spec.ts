import { expect, test } from "@playwright/test";

test.describe("Phase 11 real citation-first AI", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the controlled real corpus API");

  test("retrieves real sources before distinct record and AI blocks", async ({ page }) => {
    await page.goto("/ai");
    await page
      .getByLabel("Research question")
      .fill(
        "What did the Panel say about amendments to the Corrected Version of the SPO Final Trial Brief?",
      );
    await page.getByRole("button", { name: "Retrieve and answer" }).click();
    await expect(page.getByText("COURT FINDING").first()).toBeVisible();
    await expect(page.getByText("SPO ARGUMENT").first()).toBeVisible();
    await expect(page.getByText("DEFENCE ARGUMENT").first()).toBeVisible();
    await expect(page.getByText("COURT RESPONSE").first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "AI ANALYSIS" })).toBeVisible();
    await expect(page.locator("[data-demo-flag]")).toHaveCount(0);

    const sources = page.getByRole("heading", { name: "Retrieved sources" });
    const analysis = page.getByRole("heading", { name: "AI ANALYSIS" });
    expect((await sources.boundingBox())!.y).toBeLessThan((await analysis.boundingBox())!.y);

    await page
      .getByRole("button", { name: /F03752/ })
      .first()
      .click();
    await expect(page.getByRole("link", { name: /Open exact source/ })).toHaveAttribute(
      "href",
      /para=/,
    );
  });

  test("withholds the whole answer for known missing official material", async ({ page }) => {
    await page.goto("/ai");
    await page.getByLabel("Research question").fill("What does the Trial Judgment find?");
    await page.getByRole("button", { name: "Retrieve and answer" }).click();
    await expect(page.getByRole("heading", { name: "Answer withheld" })).toBeVisible();
    await expect(page.getByText(/does not contain the public Trial Judgment/)).toBeVisible();
    await expect(page.getByRole("heading", { name: "AI ANALYSIS" })).toHaveCount(0);
  });
});
