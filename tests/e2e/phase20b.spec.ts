import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

/**
 * Phase 20B real-source verification. Every object below is a persisted
 * record of the held public corpus (see
 * docs/ingestion/PHASE20B_TRANSCRIPT_READER_REPORT.md for the audit table).
 */

const TRANSCRIPT_EN =
  "/documents/transcript?document=T%2F2024-04-29&version=KSC-BC-2020-06%2FT%2F2024-04-29";

async function pdfReady(page: Page) {
  await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
}

/** On mobile the three layers are tabs; on desktop they are all visible. */
async function layer(page: Page, name: "Source" | "Text" | "Context") {
  const tabs = page.getByRole("radiogroup", { name: "Reader layers" });
  if (await tabs.isVisible()) await tabs.getByRole("radio", { name, exact: true }).click();
}

/** The metadata/search/navigation sidebar is a drawer below the desktop breakpoint. */
async function openSidebar(page: Page) {
  const toggle = page.getByRole("button", { name: "Document navigation" });
  if (await toggle.isVisible()) await toggle.click();
}

async function contextTab(page: Page, tab: string) {
  await layer(page, "Context");
  await page.locator('[data-reader-layer="context"]').getByRole("tab", { name: tab }).click();
}

test.describe("Phase 20B transcript-native Reader", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the Phase 20B real corpus API");

  test("A: verified person → Reader → exact PDF highlight with its reason", async ({ page }) => {
    await page.goto("/documents/F03667?anchor=0024dd10-a85a-5b97-9025-df17bc8b27d3");
    await pdfReady(page);
    await expect(page.locator("[data-source-region]").first()).toBeVisible();
    const why = page.locator("[data-active-source]");
    await expect(why).toHaveAttribute("data-active-precision", "exact_geometry");
    await expect(why).toContainText("Rexhep SELIMI");
    await expect(page).toHaveURL(/version=KSC-BC-2020-06%2FF03667%2FCOR%2FRED.*pdfPage=18/);
  });

  test("B: protected witness code → transcript line → exact PDF source", async ({ page }) => {
    await page.goto(
      "/documents/transcript?document=T%2F2026-02-13&anchor=00190b83-cc92-50f2-a62c-d960989327f7",
    );
    await pdfReady(page);
    await expect(page.locator("[data-source-region]").first()).toBeVisible();
    await layer(page, "Text");
    const focused = page.locator('[data-transcript-segments] li[aria-current="location"]');
    await expect(focused).toHaveCount(1);
    await expect(focused).toContainText("W04747");
    await contextTab(page, "People");
    const witness = page.locator('[data-overlay-kind="witness"]').filter({ hasText: "W04747" });
    await expect(witness.first()).toBeVisible();
    // Code only: the overlay never expands a protected identity.
    await expect(witness.first().locator("p").first()).toHaveText("W04747");
  });

  test("C: exhibit → source occurrence → PDF; UNKNOWN status stays UNKNOWN", async ({ page }) => {
    await page.goto("/documents/F03065?version=KSC-BC-2020-06%2FF03065&pdfPage=5");
    await pdfReady(page);
    await contextTab(page, "Exhibits");
    const exhibit = page
      .locator('[data-overlay-kind="exhibit"][data-overlay-precision="exact_geometry"]')
      .first();
    await expect(exhibit).toContainText("Status: UNKNOWN");
    await exhibit.getByRole("button", { name: "Show in source" }).click();
    await layer(page, "Source");
    await expect(page.locator("[data-source-region]").first()).toBeVisible();
    await expect(page.locator("[data-active-source]")).toHaveAttribute(
      "data-active-source",
      "exhibit",
    );
  });

  test("D: resolved citation → cited record; unresolved stays withheld", async ({ page }) => {
    await page.goto("/documents/F02222?version=KSC-BC-2020-06%2FF02222%2FRED&pdfPage=3");
    await pdfReady(page);
    await contextTab(page, "Citations");
    const unresolved = page.locator('[data-overlay-kind="citation"]').filter({
      has: page.locator('[data-overlay-state="UNRESOLVED"]'),
    });
    await expect(unresolved.first()).toContainText("No resolved target — withheld");
    await expect(unresolved.first().getByRole("link")).toHaveCount(0);
    const resolved = page
      .locator('[data-overlay-kind="citation"][data-overlay-precision="exact_geometry"]')
      .filter({ hasText: "F02198, para.9" })
      .first();
    await resolved.getByRole("button", { name: "Show in source" }).click();
    await layer(page, "Source");
    await expect(page.locator("[data-source-region]").first()).toBeVisible();
    await layer(page, "Context");
    await resolved.getByRole("link", { name: "Open cited source" }).click();
    await expect(page).toHaveURL(/\/documents\/F02198\?.*para=9/);
  });

  test("E: network edge → evidence → exact source", async ({ page }) => {
    await page.goto("/documents/F02222?version=KSC-BC-2020-06%2FF02222%2FRED&pdfPage=3");
    await pdfReady(page);
    await contextTab(page, "Summary");
    const edge = page
      .locator('[data-overlay-kind="relationship"][data-overlay-precision="exact_geometry"]')
      .first();
    await expect(edge.locator("[data-evidence-path]")).toContainText("citation");
    await edge.getByRole("button", { name: "Show in source" }).click();
    await layer(page, "Source");
    await expect(page.locator("[data-source-region]").first()).toBeVisible();
    await expect(page.getByText(/implies no guilt/).first()).toBeAttached();
  });

  test("F + H: finding → passage → PAGE_ONLY without a rectangle", async ({ page }) => {
    await page.goto("/documents/F03752?anchor=36a0e299-42f5-5e2f-a1cc-0a6efcbafcc2");
    await pdfReady(page);
    await expect(page.locator("[data-source-region]")).toHaveCount(0);
    await expect(page.getByText(/honest page_only fallback/)).toBeVisible();
    await contextTab(page, "Findings");
    const finding = page.locator('[data-overlay-kind="finding"]').first();
    await expect(finding).toHaveAttribute("data-overlay-precision", "page_only");
    await expect(finding.getByRole("link", { name: "Open finding" })).toHaveAttribute(
      "href",
      /\/findings\//,
    );
  });

  test("G: PAGE_AND_LINE opens page and line without a box", async ({ page }) => {
    await page.goto(`${TRANSCRIPT_EN}&pdfPage=4`);
    await pdfReady(page);
    await contextTab(page, "People");
    const judge = page
      .locator('[data-overlay-kind="person"][data-overlay-precision="page_and_line"]')
      .first();
    await judge.getByRole("button", { name: "Show in source" }).click();
    await layer(page, "Source");
    await expect(page.locator("[data-active-source]")).toHaveAttribute(
      "data-active-precision",
      "page_and_line",
    );
    await expect(page.locator("[data-source-region]")).toHaveCount(0);
    await expect(page.getByText(/honest page_and_line fallback/)).toBeVisible();
    await layer(page, "Text");
    await expect(
      page.locator('[data-transcript-segments] li[aria-current="location"]'),
    ).toHaveCount(1);
  });

  test("transcript page/line deep link lands on the exact segment and syncs both ways", async ({
    page,
  }) => {
    await page.goto(`${TRANSCRIPT_EN}&page=14987&line=3`);
    await pdfReady(page);
    await expect(page).toHaveURL(/pdfPage=4/);
    await layer(page, "Text");
    const focused = page.locator('[data-transcript-segments] li[aria-current="location"]');
    await expect(focused).toContainText("Of my testimony.");
    await expect(page.locator("[data-page-header]")).toContainText("W03877");
    // Transcript → PDF: the focused segment's validated line box.
    await focused.getByRole("button").click();
    await layer(page, "Source");
    const region = page.locator("[data-source-region]").first();
    await expect(region).toBeVisible();
    const box = await region.boundingBox();
    // PDF → transcript: select another line, then click the first line's box.
    await layer(page, "Text");
    await page
      .locator('[data-transcript-segments] li[data-segment-precision="exact_geometry"]')
      .nth(5)
      .getByRole("button")
      .click();
    await layer(page, "Source");
    await page.mouse.click(box!.x + box!.width / 2, box!.y + box!.height / 2);
    await layer(page, "Text");
    await expect(
      page.locator('[data-transcript-segments] li[aria-current="location"]'),
    ).toContainText("Of my testimony.");
  });

  test("speaker filter states that surrounding source lines are hidden", async ({ page }) => {
    await page.goto(`${TRANSCRIPT_EN}&pdfPage=4`);
    await pdfReady(page);
    await openSidebar(page);
    const nav = page.locator("[data-transcript-navigation]");
    await nav.getByLabel("Speaker (verbatim label)").selectOption("THE WITNESS");
    await nav.getByRole("button", { name: "Apply" }).click();
    await layer(page, "Text");
    await expect(page.locator("[data-filtered-view]")).toContainText("Surrounding source lines");
    await page
      .locator("[data-filtered-view]")
      .getByRole("button", { name: "Clear filters" })
      .click();
    await expect(page.locator("[data-filtered-view]")).toHaveCount(0);
  });

  test("local source search returns SEARCH MATCH hits that never draw a box", async ({ page }) => {
    await page.goto(`${TRANSCRIPT_EN}&pdfPage=0`);
    await pdfReady(page);
    await openSidebar(page);
    await page.getByRole("searchbox", { name: "Search this version" }).fill("solemnly");
    await page.getByRole("search").getByRole("button", { name: "Apply" }).click();
    const results = page.locator("[data-local-search]");
    await expect(results.locator('[data-overlay-state="SEARCH_MATCH"]').first()).toBeVisible();
    await results.getByRole("button").first().click();
    await expect(page).toHaveURL(/pdfPage=4/);
    await expect(page.locator("[data-source-region]")).toHaveCount(0);
  });

  test("I: version switch opens the other version without carrying coordinates", async ({
    page,
  }) => {
    await page.goto(`${TRANSCRIPT_EN}&page=14987&line=3`);
    await pdfReady(page);
    await openSidebar(page);
    await page
      .locator("[data-version-switcher]")
      .getByRole("link", { name: "KSC-BC-2020-06/T/2024-04-29/sqi" })
      .click();
    await expect(page).toHaveURL(/version=KSC-BC-2020-06%2FT%2F2024-04-29%2Fsqi/);
    await expect(page).toHaveURL(/pdfPage=0/);
    await expect(page).not.toHaveURL(/line=|segment=|anchor=/);
    await pdfReady(page);
    await expect(page.locator("[data-source-region]")).toHaveCount(0);
    await expect(page.locator("[data-active-source]")).toHaveCount(0);
  });

  test("OCR-required page stays viewable and says no native geometry exists", async ({ page }) => {
    await page.goto(`${TRANSCRIPT_EN}&pdfPage=37`);
    await pdfReady(page);
    await expect(page.locator("[data-ocr-required]")).toContainText("requires OCR");
    await expect(page.locator("canvas")).toHaveCount(1);
  });

  test("transcript Reader layers have no serious or critical axe violations", async ({ page }) => {
    await page.goto(`${TRANSCRIPT_EN}&page=14987&line=3`);
    await pdfReady(page);
    for (const name of ["Source", "Text", "Context"] as const) {
      await layer(page, name);
      const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
      const blocking = result.violations.filter(
        ({ impact }) => impact === "serious" || impact === "critical",
      );
      expect(blocking.map((violation) => violation.id)).toEqual([]);
    }
  });
});
