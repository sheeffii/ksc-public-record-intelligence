import { expect, test } from "@playwright/test";

test.describe("Phase 19 verified intelligence consumption", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the Phase 19 real corpus API");

  test("protected witness → header-backed appearance → exact transcript span", async ({ page }) => {
    await page.goto("/witnesses/W03877");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("W03877");
    const panel = page
      .locator("section")
      .filter({ hasText: "Hearings with a recorded public appearance" });
    await expect(panel.getByText("1 hearing · 2 transcript versions")).toBeVisible();
    await expect(panel.getByText("VERIFIED").first()).toBeVisible();
    const source = panel.getByRole("link", { name: "Open exact source" }).first();
    await expect(source).toHaveAttribute("href", /\/documents\/transcript\?.*page=\d+.*hl=/);
    await source.click();
    await expect(page).toHaveURL(/\/documents\/transcript\?/);
    // The appearance signal is the page's running header, outside the rendered
    // segments: the Reader states that and shows the verbatim header text.
    await expect(
      page.locator("mark[data-exact-source], [data-exact-source-outside]").first(),
    ).toContainText("W03877");
  });

  test("verified mention opens the Reader with the exact span marked", async ({ page }) => {
    await page.goto("/people/accused-krasniqi");
    const verified = page.locator("section").filter({ hasText: "Verified mentions" }).first();
    await expect(verified.getByText("VERIFIED MENTION").first()).toBeVisible();
    const inParagraph = verified.locator('a[href*="para="][href*="hl="]').first();
    const para = /[?&]para=(\d+)/.exec((await inParagraph.getAttribute("href")) ?? "")?.[1];
    await inParagraph.click();
    await expect(page).toHaveURL(/\/documents\/.*hl=/);
    const mark = page.locator(`#para-${para} mark[data-exact-source]`).first();
    await expect(mark).toBeVisible();
    await expect(mark).toHaveText(/Jakup\s+(Krasniqi|KRASNIQI)/);
  });

  test("exhibit status history comes from court statements; UNKNOWN stays UNKNOWN", async ({
    page,
  }) => {
    await page.goto("/exhibits/P01137");
    const history = page.locator("section").filter({ hasText: "Status history" });
    await expect(history.getByText("Admitted").first()).toBeVisible();
    await expect(history.getByText("was admitted as Exhibit P01137").first()).toBeVisible();

    await page.goto("/exhibits/P01355");
    const unknown = page.locator("section").filter({ hasText: "Status history" });
    await expect(unknown.getByText("The status is not inferred", { exact: false })).toBeVisible();
    await expect(page.locator('[data-intelligence-state="UNKNOWN"]').first()).toBeVisible();
  });

  test("network reads are bounded, filtered and paginated server-side", async ({ page }) => {
    await page.goto("/network?focus=W03877");
    const controls = page.locator("[data-network-page]");
    await expect(controls).toContainText("the full graph is never loaded");
    await controls.getByRole("link", { name: /testified at/ }).click();
    await expect(page).toHaveURL(/type=testified_at/);
    await expect(page.locator("[data-network-page]")).toContainText("1 relationship match");

    await page.goto("/network");
    const overview = page.locator("[data-network-page]");
    await expect(overview).toContainText("No entity is focused");
    await overview.getByRole("link", { name: "Next page" }).click();
    await expect(page).toHaveURL(/cursor=[0-9a-f-]{36}/);
    await expect(page.locator("[data-network-page]").getByText("First page")).toBeVisible();
  });
});
