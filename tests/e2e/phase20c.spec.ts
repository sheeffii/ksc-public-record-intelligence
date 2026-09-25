import { appendFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

/**
 * Phase 20C source-fidelity audit against the production build. Every
 * identifier is a persisted record of the held public corpus; the audit table
 * lives in docs/ingestion/PHASE20_QUALITY_GATE.md.
 */

const API = process.env.E2E_API_URL ?? "http://localhost:8000";
const TRANSCRIPT_EN =
  "/documents/transcript?document=T%2F2024-04-29&version=KSC-BC-2020-06%2FT%2F2024-04-29";

/** Records every Reader render state from the first DOM mutation onward. */
async function watchRenders(page: Page) {
  await page.addInitScript(() => {
    const log: { t: number; state: string }[] = [];
    (window as unknown as { __reader: typeof log }).__reader = log;
    new MutationObserver(() => {
      const host = document.querySelector("[data-pdf-rendered]");
      const canvas = document.querySelector('canvas[aria-label^="PDF page"]');
      const state = `${canvas?.getAttribute("aria-label") ?? "-"}|${host?.getAttribute("data-pdf-rendered") ?? "-"}|${document.querySelectorAll("[data-source-region]").length}`;
      if (log.at(-1)?.state !== state) log.push({ t: performance.now(), state });
    }).observe(document, { subtree: true, childList: true, attributes: true });
  });
}

async function renders(page: Page) {
  return page.evaluate(
    () => (window as unknown as { __reader: { t: number; state: string }[] }).__reader,
  );
}

async function layer(page: Page, name: "Source" | "Text" | "Context") {
  const tabs = page.getByRole("radiogroup", { name: "Reader layers" });
  if (await tabs.isVisible()) await tabs.getByRole("radio", { name, exact: true }).click();
}

async function contextTab(page: Page, tab: string) {
  await layer(page, "Context");
  await page.locator('[data-reader-layer="context"]').getByRole("tab", { name: tab }).click();
}

async function openSidebar(page: Page) {
  const toggle = page.getByRole("button", { name: "Document navigation" });
  if (await toggle.isVisible()) await toggle.click();
}

function record(entry: object) {
  if (process.env.PHASE20C_AUDIT_OUT) {
    appendFileSync(process.env.PHASE20C_AUDIT_OUT, `${JSON.stringify(entry)}\n`);
  }
}

test.describe("Phase 20C source-fidelity audit", () => {
  test.skip(!process.env.E2E_REAL_DATA, "requires the Phase 20 real corpus API");

  test("the Reader loads the exact stored artifact and its official source", async ({
    page,
    request,
  }, info) => {
    const sources = [
      { doc: "F03752", ref: "KSC-BC-2020-06/F03752", pdfPage: 0 },
      { doc: "F03667", ref: "KSC-BC-2020-06/F03667/COR/RED", pdfPage: 18 },
      { doc: "T/2026-02-13", ref: "KSC-BC-2020-06/T/2026-02-13/sqi", pdfPage: 130 },
    ];
    for (const source of sources) {
      const detail = await (await request.get(`${API}/api/v1/documents/${source.doc}`)).json();
      const version = detail.versions.find(
        (v: { official_version_ref: string }) => v.official_version_ref === source.ref,
      );
      const artifacts: { url: string; status: number; etag: string | null }[] = [];
      page.on("response", (response) => {
        if (response.url().includes("/artifact")) {
          artifacts.push({
            url: response.url(),
            status: response.status(),
            etag: response.headers()["etag"] ?? null,
          });
        }
      });
      const route = source.doc.startsWith("T/")
        ? `/documents/transcript?document=${encodeURIComponent(source.doc)}`
        : `/documents/${source.doc}`;
      await page.goto(
        `${route}${route.includes("?") ? "&" : "?"}version=${encodeURIComponent(source.ref)}&pdfPage=${source.pdfPage}`,
      );
      await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
      await expect(page.getByLabel(`PDF page ${source.pdfPage + 1}`)).toBeVisible();
      expect(artifacts.length).toBeGreaterThan(0);
      for (const artifact of artifacts) {
        expect(artifact.url).toContain(`/api/v1/document-versions/${source.ref}/artifact`);
        expect([200, 206]).toContain(artifact.status);
        expect(artifact.etag).toContain(version.sha256);
      }
      await expect(page.getByRole("link", { name: "Official court source" })).toHaveAttribute(
        "href",
        version.source_url,
      );
      await expect(page.locator('[data-reader-layer="source"] canvas')).toHaveCount(1);
      record({
        check: "artifact",
        project: info.project.name,
        ref: source.ref,
        sha256: version.sha256,
        requests: artifacts.length,
      });
    }
  });

  const deepLinks = [
    {
      name: "anchor exact (person, F03667/COR/RED)",
      url: "/documents/F03667?anchor=0024dd10-a85a-5b97-9025-df17bc8b27d3",
      page: 19,
      region: true,
    },
    {
      name: "anchor exact (witness, SQ transcript)",
      url: "/documents/transcript?document=T%2F2026-02-13&anchor=00190b83-cc92-50f2-a62c-d960989327f7",
      page: 131,
      region: true,
    },
    {
      name: "anchor transcript segment",
      url: "/documents/transcript?document=T%2F2024-04-29&anchor=8a3edddc-6c4a-57be-8a48-2285d242baed",
      page: 5,
      region: true,
    },
    {
      name: "transcript page+line",
      url: `${TRANSCRIPT_EN}&page=14987&line=3`,
      page: 5,
      region: true,
    },
    {
      name: "segment id",
      url: `${TRANSCRIPT_EN}&segment=a5367f62-4fd5-5bc7-a50f-4f73978fb1c9`,
      page: 5,
      region: true,
    },
    { name: "pdfPage only", url: `${TRANSCRIPT_EN}&pdfPage=4`, page: 5, region: false },
    {
      name: "anchor page_only (finding)",
      url: "/documents/F03752?anchor=36a0e299-42f5-5e2f-a1cc-0a6efcbafcc2",
      page: 5,
      region: false,
    },
    {
      name: "anchor page_and_line (speaker-label person)",
      url: "/documents/transcript?document=T%2F2024-04-29&anchor=a2b28aa4-19df-5f84-b087-b5f5cf6059f3",
      page: 5,
      region: false,
    },
  ];

  for (const link of deepLinks) {
    test(`fresh deep link renders only its page and settles its highlight: ${link.name}`, async ({
      page,
    }, info) => {
      await watchRenders(page);
      const started = Date.now();
      await page.goto(link.url);
      await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
      if (link.region) {
        await expect(page.locator("[data-source-region]").first()).toBeVisible({ timeout: 10_000 });
      } else {
        await expect(
          page.locator("[data-active-source], [data-pdf-rendered]").first(),
        ).toBeVisible();
        await page.waitForTimeout(1_500);
        await expect(page.locator("[data-source-region]")).toHaveCount(0);
      }
      const settled = Date.now() - started;
      const log = await renders(page);
      // No other page ever rendered, and no region appeared before its page.
      const labels = new Set(
        log.map((entry) => entry.state.split("|")[0]).filter((l) => l !== "-"),
      );
      expect([...labels]).toEqual([`PDF page ${link.page}`]);
      for (const entry of log) {
        const [, rendered, regions] = entry.state.split("|");
        if (Number(regions) > 0) expect(rendered).toBe("true");
        if (!link.region) expect(Number(regions)).toBe(0);
      }
      const firstRender = log.find((entry) => entry.state.includes("|true|"));
      const firstRegion = log.find((entry) => Number(entry.state.split("|")[2]) > 0);
      record({
        check: "deep-link",
        project: info.project.name,
        name: link.name,
        rendered_ms: firstRender ? Math.round(firstRender.t) : null,
        highlight_ms: firstRegion ? Math.round(firstRegion.t) : null,
        settled_wall_ms: settled,
      });
    });
  }

  test("an anchor on a filing that shares its number with an annex opens its own version", async ({
    page,
  }) => {
    // Found by the 20C visual audit: F03668 and F03668/A01 share a filing number.
    await page.goto("/documents/F03668?anchor=c8f34508-c8fc-5d88-b238-e017147f0c52");
    await expect(page.getByLabel("PDF page 221")).toBeVisible();
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('[data-reader-layer="source"] .identifier').first()).toHaveText(
      "KSC-BC-2020-06/F03668/RED2",
    );
    await expect(page.locator("[data-source-region]").first()).toBeVisible();
    // A version this document does not hold is not found, never substituted.
    const missing = await page.goto(
      "/documents/F03668?version=KSC-BC-2020-06%2FF03668%2FRED%2FA01%2FRED&pdfPage=0",
    );
    expect(missing?.status()).toBe(404);
  });

  test("exact overlay stays on its persisted region through zoom and fit", async ({
    page,
    request,
  }) => {
    const anchor = await (
      await request.get(`${API}/api/v1/source-anchors/0024dd10-a85a-5b97-9025-df17bc8b27d3`)
    ).json();
    await page.goto("/documents/F03667?anchor=0024dd10-a85a-5b97-9025-df17bc8b27d3");
    await expect(page.locator("[data-source-region]").first()).toBeVisible({ timeout: 20_000 });
    // Canvas and regions are read in one frame, after the layout is stable
    // (the highlight scrolls itself into view after each render).
    const snapshot = () =>
      page.evaluate(() => {
        const canvas = document
          .querySelector('[data-reader-layer="source"] canvas')!
          .getBoundingClientRect()
          .toJSON();
        const boxes = [...document.querySelectorAll("[data-source-region]")].map((node) =>
          node.getBoundingClientRect().toJSON(),
        );
        return JSON.stringify({ canvas, boxes });
      });
    const check = async () => {
      await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible();
      let previous = "";
      await expect
        .poll(
          async () => {
            const current = await snapshot();
            const stable = current === previous;
            previous = current;
            return stable;
          },
          { intervals: [250] },
        )
        .toBe(true);
      const { canvas, boxes } = JSON.parse(previous) as {
        canvas: DOMRect;
        boxes: DOMRect[];
      };
      expect(boxes).toHaveLength(anchor.regions.length);
      anchor.regions.forEach(
        (region: { x: number; y: number; width: number; height: number }, index: number) => {
          const box = boxes[index];
          const sx = canvas.width / anchor.page_width;
          const sy = canvas.height / anchor.page_height;
          expect(Math.abs(box.x - (canvas.x + region.x * sx))).toBeLessThan(1.5);
          expect(Math.abs(box.y - (canvas.y + region.y * sy))).toBeLessThan(1.5);
          expect(Math.abs(box.width - region.width * sx)).toBeLessThan(1.5);
          expect(Math.abs(box.height - region.height * sy)).toBeLessThan(1.5);
        },
      );
    };
    await check();
    await page.getByRole("button", { name: "Zoom in" }).click();
    await check();
    await page.getByRole("button", { name: "Zoom in" }).click();
    await check();
    await page.getByRole("button", { name: "Fit page" }).click();
    await check();
    await page.getByRole("button", { name: "Fit width" }).click();
    await check();
    await page.getByRole("button", { name: "Reset" }).click();
    await check();
  });

  test("page navigation and history never re-attach a stale highlight", async ({ page }) => {
    await page.goto(
      "/documents/transcript?document=T%2F2024-04-29&anchor=8a3edddc-6c4a-57be-8a48-2285d242baed",
    );
    await expect(page.locator("[data-source-region]").first()).toBeVisible({ timeout: 20_000 });
    await page.getByRole("button", { name: "Next" }).click();
    await expect(page.getByLabel("PDF page 6")).toBeVisible();
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible();
    await expect(page.locator("[data-source-region]")).toHaveCount(0);
    await page.getByRole("button", { name: "Previous" }).click();
    await expect(page.getByLabel("PDF page 5")).toBeVisible();
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible();
    await expect(page.locator("[data-source-region]")).toHaveCount(0);

    await openSidebar(page);
    await page
      .locator("[data-version-switcher]")
      .getByRole("link", { name: "KSC-BC-2020-06/T/2024-04-29/sqi" })
      .click();
    await expect(page).toHaveURL(/%2Fsqi&pdfPage=0$/);
    await expect(page.getByLabel("PDF page 1")).toBeVisible();
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator("[data-source-region]")).toHaveCount(0);

    await page.goBack();
    await expect(page).toHaveURL(/version=KSC-BC-2020-06%2FT%2F2024-04-29(&|$)/);
    await expect(page.getByLabel("PDF page 5")).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await page.goForward();
    await expect(page).toHaveURL(/%2Fsqi&pdfPage=0$/);
    await expect(page.getByLabel("PDF page 1")).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator("[data-source-region]")).toHaveCount(0);
    await expect(page.locator("[data-active-source]")).toHaveCount(0);
  });

  test("a PDF click selects a segment only inside validated line geometry", async ({ page }) => {
    // T/2023-07-14 PDF 73: open segments, but no usable printed line grid.
    await page.goto(
      "/documents/transcript?document=T%2F2023-07-14&version=KSC-BC-2020-06%2FT%2F2023-07-14&pdfPage=72",
    );
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await layer(page, "Text");
    await expect(
      page.locator('[data-transcript-segments] li[data-segment-precision="page_and_line"]').first(),
    ).toBeAttached();
    await expect(
      page.locator('[data-transcript-segments] li[data-segment-precision="exact_geometry"]'),
    ).toHaveCount(0);
    await layer(page, "Source");
    const canvas = (await page.locator('[data-reader-layer="source"] canvas').boundingBox())!;
    for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) {
      await page.mouse.click(canvas.x + canvas.width * 0.5, canvas.y + canvas.height * fy);
    }
    await layer(page, "Text");
    await expect(
      page.locator('[data-transcript-segments] li[aria-current="location"]'),
    ).toHaveCount(0);
    await expect(page.locator("[data-source-region]")).toHaveCount(0);

    // A page with a validated grid: the running header is outside every line box.
    await page.goto(`${TRANSCRIPT_EN}&pdfPage=4`);
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await layer(page, "Source");
    const grid = (await page.locator('[data-reader-layer="source"] canvas').boundingBox())!;
    await page.mouse.click(grid.x + grid.width * 0.3, grid.y + grid.height * 0.05);
    await layer(page, "Text");
    await expect(
      page.locator('[data-transcript-segments] li[aria-current="location"]'),
    ).toHaveCount(0);
  });

  test("RED ↔ COR version switch clears state and reads only the new version", async ({ page }) => {
    const contextRequests: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("/pages/") && request.url().includes("/context")) {
        contextRequests.push(request.url());
      }
    });
    await page.goto("/documents/F00026?version=KSC-BC-2020-06%2FF00026%2FRED&pdfPage=2");
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await page.getByRole("button", { name: "Next" }).click();
    await expect(page.getByLabel("PDF page 4")).toBeVisible();
    await openSidebar(page);
    contextRequests.length = 0;
    await page
      .locator("[data-version-switcher]")
      .getByRole("link", { name: "KSC-BC-2020-06/F00026/RED/sqi/COR" })
      .click();
    await expect(page).toHaveURL(/version=KSC-BC-2020-06%2FF00026%2FRED%2Fsqi%2FCOR&pdfPage=0$/);
    await expect(page.getByLabel("PDF page 1")).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('[data-reader-layer="source"] .identifier').first()).toHaveText(
      "KSC-BC-2020-06/F00026/RED/sqi/COR",
    );
    await expect(page.locator("[data-source-region]")).toHaveCount(0);
    for (const url of contextRequests) expect(url).not.toMatch(/F00026\/RED\/pages/);
  });

  test("overlay states stay distinct and protected witnesses stay code-only", async ({ page }) => {
    await page.goto(
      "/documents/transcript?document=T%2F2023-07-14&version=KSC-BC-2020-06%2FT%2F2023-07-14&pdfPage=92",
    );
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await contextTab(page, "People");
    const review = page.locator('[data-overlay-kind="person"]').filter({
      has: page.locator('[data-overlay-state="REVIEW_REQUIRED"]'),
    });
    await expect(review.first()).toContainText("REVIEW REQUIRED");
    await expect(review.first()).not.toContainText("VERIFIED");
    for (const label of await page
      .locator('[data-overlay-kind="witness"] > p:first-of-type')
      .first()
      .allTextContents()) {
      expect(label).toMatch(/^W\d{5}$/);
    }

    await page.goto("/documents/F03667?version=KSC-BC-2020-06%2FF03667%2FCOR%2FRED&pdfPage=412");
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await contextTab(page, "Citations");
    const ambiguous = page.locator('[data-overlay-kind="citation"]').filter({
      has: page.locator('[data-overlay-state="AMBIGUOUS"]'),
    });
    await expect(ambiguous.first()).toContainText("No resolved target — withheld");
    await expect(ambiguous.first().getByRole("link")).toHaveCount(0);
    await contextTab(page, "People");
    for (const label of await page
      .locator('[data-overlay-kind="witness"] > p:first-of-type')
      .allTextContents()) {
      expect(label).toMatch(/^W\d{5}$/);
    }
  });

  test("witness and exhibit navigation reach their dossiers from the source", async ({ page }) => {
    await page.goto(`${TRANSCRIPT_EN}&pdfPage=4`);
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await layer(page, "Text");
    await page.locator("[data-page-header]").getByRole("link", { name: "W03877" }).click();
    await expect(page).toHaveURL(/\/witnesses\/W03877$/);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("W03877");

    await page.goto("/documents/F03065?version=KSC-BC-2020-06%2FF03065&pdfPage=5");
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    await contextTab(page, "Exhibits");
    const exhibit = page.locator('[data-overlay-kind="exhibit"]').first();
    const label = (await exhibit.locator("> p").first().textContent())!.trim();
    await exhibit.getByRole("link", { name: "Open dossier" }).click();
    await expect(page).toHaveURL(new RegExp(`/exhibits/${label}$`));
    await expect(page.getByRole("heading", { level: 1 })).toContainText(label);
  });

  test("all eight OCR-required pages render the PDF, state OCR, and invent nothing", async ({
    page,
  }) => {
    for (const index of [37, 44, 59, 67, 72, 73, 80, 89]) {
      await page.goto(`${TRANSCRIPT_EN}&pdfPage=${index}`);
      await expect(page.getByLabel(`PDF page ${index + 1}`)).toBeVisible();
      await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
      await expect(page.locator("[data-ocr-required]")).toContainText("requires OCR");
      await expect(page.locator("[data-source-region]")).toHaveCount(0);
      await layer(page, "Text");
      await expect(page.locator("[data-transcript-segments] li[data-segment-id]")).toHaveCount(0);
      await layer(page, "Source");
    }
  });

  test("a 716-page filing navigates one page at a time with page-local reads", async ({
    page,
  }, info) => {
    const calls: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("/api/v1/")) calls.push(new URL(request.url()).pathname);
    });
    await page.goto("/documents/F03667?version=KSC-BC-2020-06%2FF03667%2FCOR%2FRED&pdfPage=700");
    await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
    const timings: number[] = [];
    for (let step = 0; step < 4; step++) {
      const started = Date.now();
      await page.getByRole("button", { name: "Next" }).click();
      await expect(page.getByLabel(`PDF page ${702 + step}`)).toBeVisible();
      await expect(page.locator('[data-pdf-rendered="true"]')).toBeVisible({ timeout: 20_000 });
      timings.push(Date.now() - started);
      await expect(page.locator("canvas")).toHaveCount(1);
    }
    expect(calls.some((path) => path.startsWith("/api/v1/network"))).toBe(false);
    expect(calls.filter((path) => path.endsWith("/context"))).toHaveLength(4);
    record({ check: "large-filing-next-page", project: info.project.name, ms: timings });
  });
});
