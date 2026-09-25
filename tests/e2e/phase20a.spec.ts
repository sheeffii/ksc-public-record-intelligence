import { expect, test } from "@playwright/test";

test.describe("Phase 20A source-native Reader", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the Phase 20A real corpus API");

  test("renders representative short, large and long-transcript PDFs one page at a time", async ({
    page,
  }) => {
    const sources = [
      "/documents/F03752?version=KSC-BC-2020-06%2FF03752&pdfPage=0",
      "/documents/F03667?version=KSC-BC-2020-06%2FF03667%2FCOR%2FRED&pdfPage=18",
      "/documents/transcript?document=T%2F2026-02-13&version=KSC-BC-2020-06%2FT%2F2026-02-13%2Fsqi&pdfPage=130",
    ];

    for (const source of sources) {
      await page.goto(source);
      await expect(page.getByLabel(/PDF page \d+/)).toBeVisible();
      await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 15_000 });
      await expect(page.getByRole("button", { name: "Original PDF" })).toHaveAttribute(
        "aria-pressed",
        "true",
      );
      await expect(page.getByRole("link", { name: "Official court source" })).toBeVisible();
      // Only one canvas is mounted: the Reader never eagerly renders the full PDF.
      await expect(page.locator("canvas")).toHaveCount(1);
    }
  });

  test("keeps an exact region aligned through zoom, fit and resize", async ({ page }) => {
    await page.goto("/documents/F03667?anchor=0024dd10-a85a-5b97-9025-df17bc8b27d3");
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 15_000 });
    const region = page.locator("[data-source-region]").first();
    await expect(region).toBeVisible({ timeout: 15_000 });
    const initial = await region.boundingBox();
    expect(initial).not.toBeNull();

    await page.getByRole("button", { name: "Zoom in" }).click();
    await expect(region).toBeVisible();
    await expect
      .poll(async () => (await region.boundingBox())?.width)
      .toBeGreaterThan(initial?.width ?? 0);

    await page.getByRole("button", { name: "Fit page" }).click();
    await expect(region).toBeVisible();
    await page.getByRole("button", { name: "Fit width" }).click();
    await expect(region).toBeVisible();
    await page.getByRole("button", { name: "Reset" }).click();
    await expect(region).toBeVisible();

    await page.setViewportSize({ width: 412, height: 915 });
    await expect(region).toBeVisible();
  });

  test("opens page-only evidence without manufacturing a rectangle", async ({ page }) => {
    await page.goto("/documents/F03752?anchor=36a0e299-42f5-5e2f-a1cc-0a6efcbafcc2");
    await expect(page.getByLabel("PDF page 5")).toBeVisible();
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/honest page_only fallback/)).toBeVisible();
    await expect(page.locator("[data-source-region]")).toHaveCount(0);
  });
});
