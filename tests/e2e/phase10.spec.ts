import { expect, test } from "@playwright/test";

test.describe("Phase 10 real finding matrix", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the controlled real corpus API");

  test("opens the real Court finding with exact provenance and explicit source gaps", async ({
    page,
  }) => {
    await page.goto("/findings/FD-F03752-P12-16");
    await expect(page.getByRole("heading", { name: /COURT FINDING/ }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: /SPO \/ DEFENCE ARGUMENTS/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /COURT RESPONSE/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: "AI ANALYSIS" })).toBeVisible();
    await expect(page.getByText("No AI analysis is generated in Phase 10.")).toBeVisible();
    await expect(page.getByText(/F03743 is not held in the controlled corpus/)).toBeVisible();
    await expect(page.getByText(/F03746 is not held in the controlled corpus/)).toBeVisible();
    const exactSource = page.getByRole("link", { name: "Open exact source" });
    await expect(exactSource).toHaveAttribute("href", /F03667/);
    await expect(page.locator("[data-demo-flag]")).toHaveCount(0);
  });
});
