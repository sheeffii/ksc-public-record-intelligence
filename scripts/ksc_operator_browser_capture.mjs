#!/usr/bin/env node
/**
 * Operator-assisted KSC public-record collector (Phase 13 capture-v0 producer).
 *
 * Drives the operator's own installed Google Chrome, visibly, through Playwright
 * with a dedicated persistent profile. Every official request is an ordinary
 * navigation of that visible browser. There is no HTTP client, no cookie or
 * token handling, no user-agent change, no proxy and no challenge automation:
 * when Cloudflare presents a challenge the script pauses, tells the operator,
 * and continues only once the normal public page is back.
 *
 * Output is a capture-v0 bundle (manifest.json + pages/rNN.html snapshots +
 * files/rNN.pdf + files/sha256sums.txt + raw_pages/ + CAPTURE_NOTES.md) that
 * `ksc-ingest import-capture` already understands. Nothing is ingested here.
 *
 * Two ways to get a browser:
 *   launch  — Playwright starts Chrome itself. Chrome then carries the automation
 *             flag (`navigator.webdriver`), which Cloudflare Turnstile refuses to
 *             clear, so this mode only works when no challenge is active.
 *   attach  — the operator starts their installed Chrome normally, with this
 *             collector's dedicated profile and Chrome's standard remote-debugging
 *             port, passes any challenge as an ordinary visitor, and the script
 *             attaches to that same window over CDP. Nothing is hidden, spoofed,
 *             injected or copied; if the site re-challenges while attached the
 *             script pauses again and the operator decides.
 *
 *   pnpm exec node scripts/ksc_operator_browser_capture.mjs --print-chrome-command
 *   pnpm exec node scripts/ksc_operator_browser_capture.mjs --probe --attach
 *   pnpm exec node scripts/ksc_operator_browser_capture.mjs --attach \
 *     --case KSC-BC-2020-06 --target-new 3 --output ~/Downloads/ksc-bc-2020-06-phase13-corpus-02
 */

import { chromium } from "@playwright/test";
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const OFFICIAL_HOSTS = new Set(["repository.scp-ks.org", "www.scp-ks.org"]);
const REPOSITORY = "https://repository.scp-ks.org/";
const PUBLIC_STATUSES = new Set([
  "public",
  "public_redacted",
  "public_redacted_v2",
  "public_redacted_corrected",
]);

// ------------------------------------------------------------------ args --
function parseArgs(argv) {
  const args = {
    case: "KSC-BC-2020-06",
    targetNew: 40,
    maxTotal: 60,
    output: join(process.env.HOME ?? ".", "Downloads", "ksc-bc-2020-06-phase13-corpus-02"),
    profile: join(ROOT, ".tmp", "ksc-operator-browser-profile"),
    exclude: join(ROOT, "docs", "ingestion", "manifests", "phase7-controlled-corpus.json"),
    excludeInventory: null,
    bundleId: "2026-09-21-corpus-02",
    paceMs: 2500,
    probe: false,
    capturedBy: null,
    maxListingPages: 6,
    attach: null,
    printChromeCommand: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === "--case") args.case = next();
    else if (a === "--target-new") args.targetNew = Number(next());
    else if (a === "--max-total") args.maxTotal = Number(next());
    else if (a === "--output") args.output = resolve(next().replace(/^~/, process.env.HOME ?? "~"));
    else if (a === "--profile") args.profile = resolve(next());
    else if (a === "--exclude") args.exclude = resolve(next());
    else if (a === "--exclude-inventory") args.excludeInventory = resolve(next());
    else if (a === "--bundle-id") args.bundleId = next();
    else if (a === "--pace-ms") args.paceMs = Number(next());
    else if (a === "--captured-by") args.capturedBy = next();
    else if (a === "--max-listing-pages") args.maxListingPages = Number(next());
    else if (a === "--probe") args.probe = true;
    else if (a === "--attach") {
      args.attach = argv[i + 1] && !argv[i + 1].startsWith("--") ? next() : "http://127.0.0.1:9222";
    } else if (a === "--print-chrome-command") args.printChromeCommand = true;
    else if (a === "-h" || a === "--help") {
      console.log(readFileSync(fileURLToPath(import.meta.url), "utf8").split("*/")[0]);
      process.exit(0);
    } else throw new Error(`unknown argument ${a}`);
  }
  if (!/^KSC-BC-\d{4}-\d{2}$/.test(args.case)) throw new Error(`bad case number ${args.case}`);
  if (!args.capturedBy) {
    try {
      args.capturedBy = execSync("git config user.name", { cwd: ROOT }).toString().trim();
    } catch {
      args.capturedBy = "operator";
    }
  }
  return args;
}

// --------------------------------------------------------------- helpers --
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...m) => console.log(new Date().toISOString().slice(11, 19), ...m);
const sha256 = (buf) => createHash("sha256").update(buf).digest("hex");
const escapeHtml = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );

function assertOfficial(url) {
  const u = new URL(url);
  if (u.protocol !== "https:" || !OFFICIAL_HOSTS.has(u.hostname)) {
    throw new Error(`refusing non-official URL ${url}`);
  }
  return u.toString();
}

function docIdOf(url) {
  try {
    const u = new URL(url);
    return u.pathname === "/details.php"
      ? (u.searchParams.get("doc_id")?.toLowerCase() ?? null)
      : null;
  } catch {
    return null;
  }
}

/** Chrome setting "Download PDF files instead of automatically opening them",
 *  written into the dedicated profile so a PDF navigation yields the exact
 *  bytes as a download. Ordinary user preference, nothing else is touched. */
function preparePdfDownloadPreference(profileDir) {
  const prefPath = join(profileDir, "Default", "Preferences");
  let prefs = {};
  if (existsSync(prefPath)) {
    try {
      prefs = JSON.parse(readFileSync(prefPath, "utf8"));
    } catch {
      prefs = {};
    }
  }
  prefs.plugins = { ...(prefs.plugins ?? {}), always_open_pdf_externally: true };
  mkdirSync(dirname(prefPath), { recursive: true });
  writeFileSync(prefPath, JSON.stringify(prefs));
}

// ------------------------------------------------------- challenge gate --
async function looksLikeChallenge(page, response) {
  const headers = response ? response.headers() : {};
  if ((headers["cf-mitigated"] ?? "").toLowerCase() === "challenge") return true;
  try {
    const title = (await page.title()) ?? "";
    if (/just a moment|attention required|verify you are human|checking your browser/i.test(title))
      return true;
    return await page.evaluate(() => {
      const q = (s) => document.querySelector(s) !== null;
      return (
        q("#challenge-running") ||
        q("#challenge-form") ||
        q("#cf-chl-widget") ||
        q('iframe[src*="challenges.cloudflare.com"]') ||
        (q('script[src*="/cdn-cgi/challenge-platform/"]') &&
          document.body.innerText.trim().length < 400)
      );
    });
  } catch {
    return false;
  }
}

async function waitForOperatorEnter() {
  if (!process.stdin.isTTY) return new Promise(() => {}); // never resolves; polling decides
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolveEnter) =>
    rl.question("", () => {
      rl.close();
      resolveEnter();
    }),
  );
}

/** Pause until the normal public page is accessible. Never touches the challenge. */
async function ensurePublic(page, response, { timeoutMs = 15 * 60 * 1000 } = {}) {
  if (!(await looksLikeChallenge(page, response))) return;
  console.log("\n=================================================================");
  console.log("Cloudflare/access challenge detected in the visible Chrome window.");
  console.log("Complete the browser challenge manually, then press ENTER here.");
  console.log("(No TTY: the script also resumes by itself once the public page is back.)");
  console.log("=================================================================\n");
  const started = Date.now();
  const enter = waitForOperatorEnter();
  for (;;) {
    const cleared = !(await looksLikeChallenge(page, null));
    if (cleared) break;
    if (Date.now() - started > timeoutMs)
      throw new Error("challenge not completed within the timeout");
    await Promise.race([enter, sleep(2000)]);
  }
  log("public page accessible again; continuing");
}

async function go(page, url, pace) {
  assertOfficial(url);
  await sleep(pace);
  const response = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90_000 });
  await ensurePublic(page, response);
  return response;
}

// -------------------------------------------------------- pdf acquisition --
/**
 * Open the public PDF URL in the same visible browser context. Chrome receives
 * the response; the bytes come back either as the navigation response body or
 * as Chrome's own download of that response. Nothing is re-fetched elsewhere.
 */
async function acquirePdf(context, url, pace) {
  assertOfficial(url);
  await sleep(pace);
  const page = await context.newPage();
  let observed = null;
  page.on("response", (r) => {
    if (r.url() === url || r.request().isNavigationRequest()) observed = observed ?? r;
  });
  try {
    const downloadPromise = page.waitForEvent("download", { timeout: 60_000 }).catch(() => null);
    let response = null;
    let navigationError = null;
    try {
      response = await page.goto(url, { waitUntil: "commit", timeout: 90_000 });
    } catch (err) {
      navigationError = err;
    }
    if (response && (await looksLikeChallenge(page, response))) {
      await ensurePublic(page, response);
      return { ok: false, reason: "challenge_on_pdf_url; retry" };
    }
    const download = await downloadPromise;
    let bytes = null;
    let method = null;
    if (download) {
      const path = await download.path();
      bytes = readFileSync(path);
      method = "chrome_download";
    } else if (response) {
      bytes = await response.body();
      method = "navigation_response_body";
    } else {
      return { ok: false, reason: `no response: ${navigationError?.message ?? "unknown"}` };
    }
    const status = observed?.status() ?? response?.status() ?? null;
    const contentType =
      observed?.headers()["content-type"] ?? response?.headers()["content-type"] ?? null;
    if (status !== null && status !== 200) return { ok: false, reason: `http ${status}` };
    if (contentType && !/pdf|octet-stream/i.test(contentType))
      return { ok: false, reason: `content-type ${contentType}` };
    if (!bytes || bytes.length === 0) return { ok: false, reason: "empty body" };
    if (bytes.subarray(0, 5).toString("latin1") !== "%PDF-")
      return { ok: false, reason: "not a PDF (magic bytes)" };
    return { ok: true, bytes, status: status ?? 200, contentType, method };
  } finally {
    await page.close().catch(() => {});
  }
}

// ---------------------------------------------------------- probe mode --
async function dumpProbe(page, outDir, name) {
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, `${name}.html`), await page.content());
  const summary = await page.evaluate(() => {
    const text = (el) => (el?.innerText ?? el?.textContent ?? "").replace(/\s+/g, " ").trim();
    const forms = [...document.querySelectorAll("form")].map((f) => ({
      action: f.getAttribute("action"),
      method: f.getAttribute("method"),
      id: f.id || null,
      fields: [...f.querySelectorAll("input,select,textarea,button")].map((el) => ({
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute("type"),
        name: el.getAttribute("name"),
        id: el.id || null,
        placeholder: el.getAttribute("placeholder"),
        label: el.labels?.[0] ? text(el.labels[0]) : el.getAttribute("aria-label"),
        value: el.tagName === "SELECT" ? undefined : el.value?.slice(0, 80),
        options:
          el.tagName === "SELECT"
            ? [...el.options].slice(0, 60).map((o) => `${o.value}=${text(o)}`)
            : undefined,
      })),
    }));
    const links = [...document.querySelectorAll("a[href]")]
      .map((a) => ({ href: a.getAttribute("href"), text: text(a).slice(0, 120) }))
      .filter((l) => /details\.php|\/LW\/|page=|\.pdf|lang=|icc_filters/i.test(l.href));
    const tables = [...document.querySelectorAll("table")].map((t) => ({
      id: t.id || null,
      cls: t.className || null,
      headers: [...t.querySelectorAll("th")].map(text).slice(0, 30),
      rows: t.querySelectorAll("tr").length,
      firstRow: [...(t.querySelector("tbody tr, tr:nth-child(2)")?.querySelectorAll("td") ?? [])]
        .map(text)
        .slice(0, 20),
    }));
    const dl = [...document.querySelectorAll("dl")].map((d) => text(d).slice(0, 600));
    return {
      title: document.title,
      url: location.href,
      forms,
      links: links.slice(0, 200),
      tables,
      dl,
    };
  });
  writeFileSync(join(outDir, `${name}.json`), JSON.stringify(summary, null, 2));
  try {
    const aria = await page.locator("body").ariaSnapshot();
    writeFileSync(join(outDir, `${name}.aria.yaml`), aria);
  } catch {
    /* older Playwright */
  }
  log(
    `probe saved: ${name} (${summary.forms.length} forms, ${summary.links.length} links, ${summary.tables.length} tables)`,
  );
}

async function runProbe(context, page, args) {
  const outDir = join(args.output, "probe");
  const r = await go(page, REPOSITORY, args.paceMs);
  await dumpProbe(page, outDir, "01-root");
  const known = JSON.parse(readFileSync(args.exclude, "utf8"));
  const sample = known.records.find((x) => x.record_id === "r03") ?? known.records[0];
  await go(page, sample.detail_page_url, args.paceMs);
  await dumpProbe(page, outDir, "02-detail-known");
  // Integrity self-test: re-acquire one already-held public PDF and compare with the tracked hash.
  const pdf = await acquirePdf(context, sample.artifact_url, args.paceMs);
  const result = pdf.ok
    ? {
        ok: true,
        method: pdf.method,
        status: pdf.status,
        contentType: pdf.contentType,
        bytes: pdf.bytes.length,
        sha256: sha256(pdf.bytes),
        expected: sample.sha256,
        expectedBytes: sample.byte_size,
        match: sha256(pdf.bytes) === sample.sha256,
      }
    : pdf;
  writeFileSync(join(outDir, "03-pdf-selftest.json"), JSON.stringify(result, null, 2));
  log("pdf self-test:", JSON.stringify(result));

  // Listing structure: submit the real public search form for the case.
  await go(page, REPOSITORY, args.paceMs);
  await page.getByLabel("File (Case) number").selectOption(args.case);
  await page.getByLabel("Sort By").selectOption("_sort_date_newest");
  await sleep(args.paceMs);
  await page.getByRole("button", { name: "Search" }).click();
  await page.waitForLoadState("domcontentloaded");
  await ensurePublic(page, null);
  await dumpProbe(page, outDir, "04-listing-p1");
  // Transcript listing and one transcript detail page (structure only).
  await page.getByLabel("Record Type").selectOption("stl_transcript");
  await sleep(args.paceMs);
  await page.getByRole("button", { name: "Search" }).click();
  await page.waitForLoadState("domcontentloaded");
  await ensurePublic(page, null);
  await dumpProbe(page, outDir, "05-listing-transcripts");
  const transcriptLink = page.locator('a[href*="details.php"][href*="stl_transcript"]').first();
  if (await transcriptLink.count()) {
    const href = await transcriptLink.getAttribute("href");
    await go(page, new URL(href, REPOSITORY).toString(), args.paceMs);
    await dumpProbe(page, outDir, "06-detail-transcript");
  }
  return r;
}

// ---------------------------------------------------- listing & detail --
// Filled in from the probe output: see docs/ingestion/CAPTURE_PLAN_2026-09-21-corpus-02.md.
// Real public UI, established by the probe on 2026-09-22:
//   search form GET / with icc_filters[case_number|record_type_short|language_short|sort_order]
//   filing-only filters: icc_filters[filing_submitter|filing_court_level|filing_type[]|filing_number]
//   results: ul.teasers li.teaser-list-item (.title h2 a, .date-info, .type-info,
//            .filing-id-info, .language-info), pagination &page=N, .results-total-number
//   detail: div.detail-row > .detail-label + .detail-value; one a[href^="/LW/Published/"]
//   translations: .detail-row "Translations" > .list-wrapper (.list-title + a[href*=details.php])
const STRATA = [
  {
    key: "lead_f01771",
    quota: 1,
    record: "stl_filing",
    filingNumber: "F01771",
    sort: "oldest",
    desc: "Known Phase 17 lead F01771",
  },
  {
    key: "lead_f02082",
    quota: 1,
    record: "stl_filing",
    filingNumber: "F02082",
    sort: "oldest",
    desc: "Known Phase 17 lead F02082/RED",
  },
  {
    key: "transcripts_2021",
    quota: 6,
    record: "stl_transcript",
    sort: "oldest",
    startPage: 2,
    maxPages: 2,
    year: 2021,
    desc: "2021 transcripts, historically paged",
  },
  {
    key: "filings_2021_early",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 50,
    maxPages: 2,
    year: 2021,
    desc: "2021 filings, early-year historical page",
  },
  {
    key: "filings_2021_late",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 80,
    maxPages: 2,
    year: 2021,
    desc: "2021 filings, late-year historical page",
  },
  {
    key: "transcripts_2022",
    quota: 6,
    record: "stl_transcript",
    sort: "oldest",
    startPage: 5,
    maxPages: 3,
    year: 2022,
    desc: "2022 transcripts, historically paged",
  },
  {
    key: "filings_2022_early",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 100,
    maxPages: 2,
    year: 2022,
    desc: "2022 filings, early-year historical page",
  },
  {
    key: "filings_2022_late",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 130,
    maxPages: 2,
    year: 2022,
    desc: "2022 filings, late-year historical page",
  },
  {
    key: "transcripts_2023_opening",
    quota: 6,
    record: "stl_transcript",
    sort: "oldest",
    startPage: 9,
    maxPages: 2,
    year: 2023,
    desc: "2023 opening/trial transcripts, historically paged",
  },
  {
    key: "filings_2023_early",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 150,
    maxPages: 2,
    year: 2023,
    desc: "2023 filings, early-year historical page",
  },
  {
    key: "filings_2023_mid",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 180,
    maxPages: 2,
    year: 2023,
    desc: "2023 filings, mid-year historical page",
  },
  {
    key: "filings_2023_late",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 210,
    maxPages: 2,
    year: 2023,
    desc: "2023 filings, late-year historical page",
  },
  {
    key: "transcripts_2024",
    quota: 6,
    record: "stl_transcript",
    sort: "oldest",
    startPage: 40,
    maxPages: 2,
    year: 2024,
    desc: "2024 transcripts, historically paged",
  },
  {
    key: "filings_2024_early",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 240,
    maxPages: 2,
    year: 2024,
    desc: "2024 filings, early-year historical page",
  },
  {
    key: "filings_2024_mid",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 260,
    maxPages: 2,
    year: 2024,
    desc: "2024 filings, mid-year historical page",
  },
  {
    key: "filings_2024_late",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 280,
    maxPages: 2,
    year: 2024,
    desc: "2024 filings, late-year historical page",
  },
  {
    key: "transcripts_2025",
    quota: 6,
    record: "stl_transcript",
    sort: "oldest",
    startPage: 70,
    maxPages: 2,
    year: 2025,
    desc: "2025 transcripts, historically paged",
  },
  {
    key: "filings_2025_early",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 300,
    maxPages: 2,
    year: 2025,
    desc: "2025 filings, early-year historical page",
  },
  {
    key: "filings_2025_mid",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 340,
    maxPages: 2,
    year: 2025,
    desc: "2025 filings, mid-year historical page",
  },
  {
    key: "filings_2025_late",
    quota: 5,
    record: "stl_filing",
    sort: "oldest",
    startPage: 370,
    maxPages: 2,
    year: 2025,
    desc: "2025 filings, late-year historical page",
  },
  {
    key: "chambers_newest",
    quota: 6,
    record: "stl_filing",
    submitter: "ch",
    sort: "newest",
    desc: "Submitted by Specialist Chambers, newest first",
  },
  {
    key: "defence_newest",
    quota: 8,
    record: "stl_filing",
    submitter: "co",
    sort: "newest",
    perAccused: 2,
    desc: "Submitted by Specialist Counsel (Defence), newest first",
  },
  {
    key: "spo_newest",
    quota: 5,
    record: "stl_filing",
    submitter: "spo",
    sort: "newest",
    desc: "Submitted by Specialist Prosecutor, newest first",
  },
  {
    key: "appeals",
    quota: 5,
    record: "stl_filing",
    level: "ca",
    sort: "newest",
    desc: "Court of Appeal Chamber level, newest first",
  },
  {
    key: "transcripts_newest",
    quota: 3,
    record: "stl_transcript",
    sort: "newest",
    desc: "Transcripts, newest first",
  },
  {
    key: "registrar",
    quota: 3,
    record: "stl_filing",
    submitter: "reg",
    sort: "newest",
    desc: "Submitted by Registrar, newest first",
  },
  {
    key: "victims_counsel",
    quota: 3,
    record: "stl_filing",
    submitter: "vc",
    sort: "newest",
    desc: "Submitted by Victims Counsel, newest first",
  },
  {
    key: "albanian_newest",
    quota: 4,
    record: "stl_filing",
    language: "sqi",
    sort: "newest",
    desc: "Language Albanian (sqi), newest first",
  },
  {
    key: "annexes",
    quota: 3,
    record: "stl_filing",
    filingType: "Filing Annex",
    sort: "newest",
    desc: "Filing Type Filing Annex, newest first",
  },
  {
    key: "chambers_oldest",
    quota: 3,
    record: "stl_filing",
    submitter: "ch",
    sort: "oldest",
    desc: "Submitted by Specialist Chambers, oldest first",
  },
  {
    key: "spo_oldest",
    quota: 2,
    record: "stl_filing",
    submitter: "spo",
    sort: "oldest",
    desc: "Submitted by Specialist Prosecutor, oldest first",
  },
  {
    key: "defence_oldest",
    quota: 4,
    record: "stl_filing",
    submitter: "co",
    sort: "oldest",
    perAccused: 1,
    desc: "Submitted by Specialist Counsel (Defence), oldest first",
  },
  {
    key: "transcripts_oldest",
    quota: 3,
    record: "stl_transcript",
    sort: "oldest",
    desc: "Transcripts, oldest first",
  },
  {
    key: "president",
    quota: 1,
    record: "stl_filing",
    submitter: "pres",
    sort: "newest",
    desc: "Submitted by President, newest first",
  },
  {
    key: "supreme",
    quota: 1,
    record: "stl_filing",
    level: "sc",
    sort: "newest",
    desc: "Supreme Court Chamber level, newest first",
  },
  {
    key: "constitutional",
    quota: 1,
    record: "stl_filing",
    level: "cc",
    sort: "newest",
    desc: "Constitutional Court Chamber level, newest first",
  },
];
const SQI_QUOTA = 6;
const ACCUSED = [/Tha[cçҫ]i/i, /Veseli/i, /Selimi/i, /Krasniqi/i];

function listingUrl(args, stratum, pageNo) {
  const u = new URL(REPOSITORY);
  u.searchParams.set("lang", "eng");
  u.searchParams.set("icc_filters[case_number]", args.case);
  u.searchParams.set("icc_filters[record_type_short]", stratum.record);
  u.searchParams.set("icc_filters[language_short]", stratum.language ?? "_all");
  u.searchParams.set(
    "icc_filters[sort_order]",
    stratum.sort === "oldest" ? "_sort_date_oldest" : "_sort_date_newest",
  );
  if (stratum.submitter) u.searchParams.set("icc_filters[filing_submitter]", stratum.submitter);
  if (stratum.level) u.searchParams.set("icc_filters[filing_court_level]", stratum.level);
  if (stratum.filingType) u.searchParams.append("icc_filters[filing_type][]", stratum.filingType);
  if (stratum.filingNumber) u.searchParams.set("icc_filters[filing_number]", stratum.filingNumber);
  if (pageNo > 1) u.searchParams.set("page", String(pageNo));
  return u.toString();
}

async function readListing(page) {
  return page.evaluate(() => {
    const text = (el) =>
      (el?.innerText ?? el?.textContent ?? "").replace(/\s+/g, " ").trim() || null;
    const total = text(document.querySelector(".results-total-number"));
    const items = [...document.querySelectorAll("ul.teasers li.teaser-list-item")].map((li) => ({
      href: li.querySelector(".title h2 a, .title a")?.getAttribute("href") ?? null,
      title: text(li.querySelector(".title h2 a, .title a")),
      case_number: text(li.querySelector(".case-number-info")),
      date: text(li.querySelector(".date-info")),
      type: text(li.querySelector(".type-info")),
      filing_id: text(li.querySelector(".filing-id-info")),
      language: text(li.querySelector(".language-info")),
      format: text(li.querySelector(".file-format-info")),
    }));
    return { total: total ? Number(total.replace(/\D/g, "")) : null, items };
  });
}

async function readDetail(page) {
  return page.evaluate(() => {
    const text = (el) =>
      (el?.innerText ?? el?.textContent ?? "").replace(/\s+/g, " ").trim() || null;
    const rows = {};
    const translations = [];
    for (const row of document.querySelectorAll(".detail-row")) {
      const label = text(row.querySelector(".detail-label"));
      const value = row.querySelector(".detail-value");
      if (!label || !value) continue;
      if (label === "Translations") {
        for (const wrap of value.querySelectorAll(".list-wrapper")) {
          translations.push({
            language: text(wrap.querySelector(".list-title")),
            links: [...wrap.querySelectorAll('a[href*="details.php"]')].map((a) => ({
              href: a.getAttribute("href"),
              title: text(a),
            })),
          });
        }
        continue;
      }
      if (label === "Rule/Article" || label === "Filing Items" || label === "Related Filings")
        continue;
      rows[label] = text(value);
    }
    const downloads = [...document.querySelectorAll('a[href^="/LW/Published/"]')].map((a) =>
      a.getAttribute("href"),
    );
    return { rows, translations, downloads: [...new Set(downloads)] };
  });
}

function parseLanguage(value) {
  const m = /^(.*)\((\w+)\)$/.exec(value ?? "");
  return m ? { code: m[2].toLowerCase(), name: m[1].trim() } : null;
}

function publicStatusFor(documentId, title) {
  const id = (documentId ?? "").toUpperCase();
  if (id.endsWith("CORRED")) return "public_redacted_corrected";
  if (id.endsWith("RED2")) return "public_redacted_v2";
  if (id.endsWith("RED")) return "public_redacted";
  // Transcripts carry no filing-number suffix; the published title says it.
  if (/public\s+redacted|redaktuar\s+publik/i.test(title ?? "")) return "public_redacted";
  return "public";
}

function filingKey(documentId) {
  const m = /^(?:(IA\d{3})-)?(F\d{5})/.exec((documentId ?? "").toUpperCase());
  return m ? (m[1] ? `${m[1]}-${m[2]}` : m[2]) : null;
}

async function collect(context, page, args) {
  const known = JSON.parse(readFileSync(args.exclude, "utf8"));
  const heldDocIds = new Set(known.records.map((r) => r.external_record_id));
  if (args.excludeInventory) {
    const inventory = JSON.parse(readFileSync(args.excludeInventory, "utf8"));
    for (const record of inventory.inventory ?? []) heldDocIds.add(record.source_record_id);
  }
  const heldHashes = new Set(known.records.map((r) => r.sha256));
  const heldFilings = new Set(
    known.records.map((r) => filingKey(r.published_document_id)).filter(Boolean),
  );
  const seenDocIds = new Set();
  const selected = [];
  const skipped = [];
  const events = { challenges: 0, listings: 0, details: 0, pdfs: 0, missingPdf: 0, duplicates: 0 };
  const sqiQueue = [];
  const counts = { new: 0, counterpart: 0, sqi: 0 };
  const stopReached = () => counts.new >= args.targetNew || selected.length >= args.maxTotal;
  const nextId = () => `r${String(selected.length + 1).padStart(2, "0")}`;
  const rawDir = join(args.output, "raw_pages");
  const filesDir = join(args.output, "files");
  mkdirSync(rawDir, { recursive: true });
  mkdirSync(filesDir, { recursive: true });

  async function capture(detailHref, hint, reason, extraChecks) {
    const detailUrl = new URL(detailHref, REPOSITORY).toString();
    const docId = docIdOf(detailUrl);
    if (!docId || seenDocIds.has(docId)) return null;
    seenDocIds.add(docId);
    if (heldDocIds.has(docId)) {
      events.duplicates += 1;
      skipped.push({ docId, title: hint.title, why: "already held (doc_id)" });
      return null;
    }
    await go(page, detailUrl, args.paceMs);
    events.details += 1;
    const detail = await readDetail(page);
    const rows = detail.rows;
    const html = await page.content();
    const caseNumber = rows["Case Number"];
    if (caseNumber !== args.case) {
      skipped.push({ docId, title: hint.title, why: `case ${caseNumber}` });
      return null;
    }
    if (detail.downloads.length !== 1) {
      skipped.push({
        docId,
        title: hint.title,
        why: `${detail.downloads.length} public download links`,
      });
      return null;
    }
    if (!/pdf/i.test(rows["File Format"] ?? "")) {
      skipped.push({ docId, title: hint.title, why: `file format ${rows["File Format"]}` });
      return null;
    }
    const language = parseLanguage(rows["Language"]);
    if (!language) {
      skipped.push({ docId, title: hint.title, why: "language not published" });
      return null;
    }
    const recordType = rows["Record Type"];
    const documentId = rows["Filing Number"] ?? null;
    const publicStatus = publicStatusFor(documentId, rows["Title"] ?? hint.title);
    if (!PUBLIC_STATUSES.has(publicStatus)) return null;
    if (extraChecks && !extraChecks({ rows, language })) {
      skipped.push({ docId, title: hint.title, why: "stratum check" });
      return null;
    }
    const pdfUrl = new URL(detail.downloads[0], REPOSITORY).toString();
    const pdf = await acquirePdf(context, pdfUrl, args.paceMs);
    events.pdfs += 1;
    if (!pdf.ok) {
      events.missingPdf += 1;
      skipped.push({ docId, title: hint.title, why: `pdf: ${pdf.reason}`, detailUrl, pdfUrl });
      return null;
    }
    const digest = sha256(pdf.bytes);
    if (heldHashes.has(digest)) {
      events.duplicates += 1;
      skipped.push({ docId, title: hint.title, why: "already held (sha256)" });
      return null;
    }
    if (selected.some((r) => r.sha256 === digest)) {
      skipped.push({ docId, title: hint.title, why: "same bytes as another selected record" });
      return null;
    }
    const recordId = nextId();
    writeFileSync(join(filesDir, `${recordId}.pdf`), pdf.bytes);
    writeFileSync(join(rawDir, `${recordId}.html`), html);
    const key = filingKey(documentId);
    const status = key && heldFilings.has(key) ? "counterpart" : "new";
    const rec = {
      record_id: recordId,
      case_number: caseNumber,
      title: rows["Title"] ?? hint.title,
      document_id: documentId,
      record_type: recordType,
      filing_type: rows["Filing Type"] ?? null,
      filing_party: rows["Filing Party"] ?? null,
      court_level: rows["Court Level"] ?? null,
      date: rows["Document Date"] ?? rows["Hearing Date"] ?? null,
      hearing_date: recordType === "Transcript" ? (rows["Hearing Date"] ?? null) : null,
      language,
      public_status: publicStatus,
      detail_page_url: detailUrl,
      pdf_url: pdfUrl,
      sha256: digest,
      bytes: pdf.bytes.length,
      http_status_verified: pdf.status,
      selection_reason: reason,
      acquisition_method: pdf.method,
      content_type: pdf.contentType,
      classification: status,
      translations: detail.translations,
    };
    selected.push(rec);
    counts[status] += 1;
    if (language.code === "sqi") counts.sqi += 1;
    log(
      `${recordId} ${status.padEnd(11)} ${String(documentId ?? "—").padEnd(16)} ${language.code} ${recordType} ${pdf.bytes.length}B ${rec.title.slice(0, 60)}`,
    );
    const sqi = detail.translations.find((t) => /\(sqi\)/i.test(t.language ?? ""));
    if (language.code === "eng" && sqi?.links?.[0]) {
      sqiQueue.push({
        href: sqi.links[0].href,
        title: sqi.links[0].title,
        of: recordId,
        documentId,
      });
    }
    return rec;
  }

  for (const stratum of STRATA) {
    if (stopReached()) break;
    let taken = 0;
    const perAccused = new Map();
    const firstPage = stratum.startPage ?? 1;
    const pageLimit = stratum.maxPages ?? args.maxListingPages;
    for (let offset = 0; offset < pageLimit && taken < stratum.quota && !stopReached(); offset++) {
      const pageNo = firstPage + offset;
      const url = listingUrl(args, stratum, pageNo);
      await go(page, url, args.paceMs);
      events.listings += 1;
      const listing = await readListing(page);
      if (!listing.items.length) break;
      for (const item of listing.items) {
        if (taken >= stratum.quota || stopReached()) break;
        if (!item.href || item.case_number !== args.case) continue;
        if (!/pdf/i.test(item.format ?? "")) continue;
        if (stratum.year && !item.date?.endsWith(String(stratum.year))) continue;
        // Scope: English and Albanian only (the project's languages; the
        // importer's classification parser is EN/SQ).
        if (!/\((eng|sqi)\)/i.test(item.language ?? "")) continue;
        let bucket = null;
        if (stratum.perAccused) {
          const idx = ACCUSED.findIndex((re) => re.test(item.title ?? ""));
          bucket = idx >= 0 ? String(idx) : "other";
          if ((perAccused.get(bucket) ?? 0) >= (bucket === "other" ? 1 : stratum.perAccused))
            continue;
        }
        const reason =
          `Listed in the public repository for ${args.case} under: ${stratum.desc}` +
          (stratum.perAccused ? "; one of a per-accused spread" : "");
        const rec = await capture(item.href, item, reason);
        if (rec) {
          taken += 1;
          if (bucket !== null) perAccused.set(bucket, (perAccused.get(bucket) ?? 0) + 1);
        }
      }
      if (listing.items.length < 10) break;
    }
    log(
      `stratum ${stratum.key}: took ${taken}/${stratum.quota} (new=${counts.new} total=${selected.length})`,
    );
  }

  // Albanian counterparts published on the detail pages of selected English records.
  for (const q of sqiQueue) {
    if (counts.sqi >= SQI_QUOTA || selected.length >= args.maxTotal) break;
    await capture(
      q.href,
      { title: q.title },
      `Albanian (sqi) translation listed on the detail page of ${q.of} (${q.documentId})`,
      ({ language }) => language.code === "sqi",
    );
  }

  const summary = {
    total_selected: selected.length,
    new: counts.new,
    counterparts: counts.counterpart,
    albanian: counts.sqi,
    duplicates_skipped: events.duplicates,
    pdfs_missing: events.missingPdf,
    navigations: events,
    by_record_type: Object.fromEntries(
      selected.reduce((m, r) => m.set(r.record_type, (m.get(r.record_type) ?? 0) + 1), new Map()),
    ),
    by_filing_type: Object.fromEntries(
      selected.reduce(
        (m, r) => m.set(r.filing_type ?? "—", (m.get(r.filing_type ?? "—") ?? 0) + 1),
        new Map(),
      ),
    ),
    by_party: Object.fromEntries(
      selected.reduce(
        (m, r) => m.set(r.filing_party ?? "—", (m.get(r.filing_party ?? "—") ?? 0) + 1),
        new Map(),
      ),
    ),
    by_language: Object.fromEntries(
      selected.reduce(
        (m, r) => m.set(r.language.code, (m.get(r.language.code) ?? 0) + 1),
        new Map(),
      ),
    ),
    skipped,
  };
  writeFileSync(
    join(args.output, "collector_summary.json"),
    JSON.stringify(summary, null, 2) + "\n",
  );
  const notes = captureNotes(args, selected, summary);
  return { records: selected, notes, summary };
}

function captureNotes(args, selected, summary) {
  const lines = [
    `# KSC Public Record Intelligence — Phase 17 operator-assisted capture \`${args.bundleId}\``,
    "",
    `**Case:** ${args.case}`,
    `**Captured:** ${new Date().toISOString().slice(0, 10)} by ${args.capturedBy}`,
    `**Records:** ${selected.length} (new filings/transcripts: ${summary.new}; counterparts of held filings: ${summary.counterparts}; Albanian: ${summary.albanian})`,
    "",
    "## Method",
    "",
    "The operator started their installed Google Chrome normally with this collector's dedicated",
    "profile and Chrome's standard remote-debugging port, opened the Public Court Records",
    "repository and completed the Cloudflare check as an ordinary visitor. The collector",
    "(`scripts/ksc_operator_browser_capture.mjs --attach`) then attached to that same window and",
    "performed ordinary navigations: the public search form filtered on the case number, record",
    "type, submitter, court level and sort order; each selected record's public detail page was",
    "opened and saved verbatim (`raw_pages/`); the page's single official Download link was opened",
    "in the same browser and the bytes Chrome received were saved unaltered (`files/`) and hashed.",
    "No HTTP client, cookie or token handling, proxy, user-agent change, stealth tooling or",
    "challenge automation was used. Navigations were paced at " + `${args.paceMs} ms.`,
    "",
    "## Selection",
    "",
    "Records were taken from these public listings, in order, with per-listing quotas:",
    ...STRATA.map((s) => `- ${s.desc} (quota ${s.quota})`),
    `- Albanian translations linked from selected English detail pages (quota ${SQI_QUOTA})`,
    "",
    "Records already represented in the configured corpus/inventory were skipped by repository doc_id and by",
    "SHA-256. `selection_reason` states the listing a record came from; nothing else was inferred.",
    "",
    "## Boundaries observed",
    "",
    "- Only records the public repository lists and offers a public Download for were opened;",
    "  no confidential, strictly confidential, ex parte or restricted record was selected.",
    "- Redaction status is recorded from the published filing number suffix (RED/RED2/CORRED)",
    "  exactly as published; nothing was reconstructed or cross-referenced between versions.",
    "- The importer independently checks the classification stamp on page 1 of every PDF.",
    "- No metadata field was inferred; unpublished fields are null.",
    "",
    "## Counts",
    "",
    "```json",
    JSON.stringify(
      {
        by_record_type: summary.by_record_type,
        by_filing_type: summary.by_filing_type,
        by_party: summary.by_party,
        by_language: summary.by_language,
        duplicates_skipped: summary.duplicates_skipped,
        pdfs_missing: summary.pdfs_missing,
        navigations: summary.navigations,
      },
      null,
      2,
    ),
    "```",
    "",
    "Skipped candidates and reasons: `collector_summary.json`.",
    "",
  ];
  return lines.join("\n");
}

// ------------------------------------------------------------- bundle --
function snapshotHtml(rec) {
  const row = (label, value) =>
    `<tr><th>${escapeHtml(label)}</th><td>${value == null ? "— (not published)" : escapeHtml(value)}</td></tr>`;
  const lang = rec.language ? `${rec.language.name} (${rec.language.code})` : null;
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>${escapeHtml(rec.record_id)} — ${escapeHtml(rec.document_id ?? rec.record_type)}</title>
<style>body{font:14px/1.5 system-ui,sans-serif;margin:2rem;max-width:60rem;color:#111}
h1{font-size:1.15rem}table{border-collapse:collapse;width:100%}
th,td{border:1px solid #ccc;padding:.45rem .6rem;text-align:left;vertical-align:top}
th{background:#f2f4f7;width:14rem;font-weight:600}
a{color:#0b57d0;word-break:break-all}.src{margin-top:1rem;font-size:.85rem;color:#555}</style></head>
<body>
<h1>${escapeHtml(rec.title)}</h1>
<table>${row("Record ID", rec.record_id)}${row("Case Number", rec.case_number)}${row("Title", rec.title)}${row("Document / Filing ID", rec.document_id)}${row("Record Type", rec.record_type)}${row("Filing Type", rec.filing_type)}${row("Filing Party", rec.filing_party)}${row("Court Level", rec.court_level)}${row("Date", rec.date)}${row("Language", lang)}${row("Public / Redacted Status", rec.public_status)}${row("SHA-256", rec.sha256)}${row("Bytes", rec.bytes == null ? null : String(rec.bytes))}${row("Selection Reason", rec.selection_reason)}</table>
<p class="src"><strong>Official detail page:</strong> <a href="${escapeHtml(rec.detail_page_url)}">${escapeHtml(rec.detail_page_url)}</a></p>
<p class="src"><strong>Official PDF:</strong> <a href="${escapeHtml(rec.pdf_url)}">${escapeHtml(rec.pdf_url)}</a></p>
<p class="src">Normalised snapshot of the fields published on the official detail page, written by scripts/ksc_operator_browser_capture.mjs from the visible browser session; raw DOM in raw_pages/${escapeHtml(rec.record_id)}.html.</p>
</body></html>
`;
}

function writeBundle(args, records, notes) {
  const out = args.output;
  for (const d of ["pages", "raw_pages", "files"]) mkdirSync(join(out, d), { recursive: true });
  const manifest = {
    bundle: {
      name: `${args.case.toLowerCase()}-${args.bundleId}`,
      project: "KSC Public Record Intelligence",
      phase: "Phase 17 operator-assisted public capture",
      bundle_id: args.bundleId,
      case_number: args.case,
      capture_date: new Date().toISOString().slice(0, 10),
      captured_by: args.capturedBy,
      capture_method:
        "Visible Google Chrome driven by Playwright with a dedicated persistent profile; every official request is an ordinary browser navigation. No HTTP client, cookies, tokens, proxies, user-agent changes or challenge automation; challenges were completed manually by the operator.",
      sources: [REPOSITORY, "https://www.scp-ks.org/"],
      record_count: records.length,
      structure: {
        "pages/": "Normalised snapshot per record (capture-v0 field table).",
        "raw_pages/": "Raw page.content() of the official detail page as rendered in the browser.",
        "files/": "Exact PDF bytes received by the browser, rNN.pdf, plus sha256sums.txt.",
        "manifest.json": "This file.",
      },
    },
    records: records.map((r) => ({
      record_id: r.record_id,
      case_number: r.case_number,
      title: r.title,
      document_id: r.document_id,
      record_type: r.record_type,
      filing_type: r.filing_type,
      filing_party: r.filing_party,
      court_level: r.court_level,
      date: r.date,
      language: r.language,
      public_status: r.public_status,
      confidential_content_included: false,
      detail_page_url: r.detail_page_url,
      pdf_url: r.pdf_url,
      artifact_path: decodeURIComponent(new URL(r.pdf_url).pathname),
      local_file: `files/${r.record_id}.pdf`,
      local_page_snapshot: `pages/${r.record_id}.html`,
      sha256: r.sha256,
      bytes: r.bytes,
      http_status_verified: r.http_status_verified,
      selection_reason: r.selection_reason,
      hearing_date: r.hearing_date ?? null,
    })),
  };
  writeFileSync(join(out, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
  writeFileSync(
    join(out, "files", "sha256sums.txt"),
    records.map((r) => `${r.sha256}  files/${r.record_id}.pdf`).join("\n") + "\n",
  );
  for (const r of records)
    writeFileSync(join(out, "pages", `${r.record_id}.html`), snapshotHtml(r));
  writeFileSync(join(out, "CAPTURE_NOTES.md"), notes);
  return manifest;
}

/** Fail-closed page-1 stamp check (scripts/check_capture_pdfs.py). Flagged
 *  records are moved to quarantine/ and the bundle is rewritten without them. */
function quarantineFlagged(args, records, notes) {
  const py = join(ROOT, ".venv", "bin", "python");
  const reportPath = join(args.output, "pdf_check.json");
  let out = "";
  try {
    out = execSync(
      `"${py}" "${join(ROOT, "scripts", "check_capture_pdfs.py")}" "${args.output}" --json "${reportPath}"`,
      { cwd: ROOT, encoding: "utf8" },
    );
  } catch (err) {
    out = (err.stdout ?? "") + (err.stderr ?? "");
    if (!existsSync(reportPath)) throw new Error(`pdf check failed to run: ${out}`);
  }
  console.log("check_capture_pdfs:\n" + out);
  const report = JSON.parse(readFileSync(reportPath, "utf8"));
  const flagged = new Set(report.flagged.map((r) => r.record_id));
  if (!flagged.size) return records;
  const qDir = join(args.output, "quarantine");
  mkdirSync(qDir, { recursive: true });
  for (const rid of flagged) {
    for (const [dir, ext] of [
      ["files", "pdf"],
      ["pages", "html"],
      ["raw_pages", "html"],
    ]) {
      const from = join(args.output, dir, `${rid}.${ext}`);
      if (existsSync(from)) renameSync(from, join(qDir, `${rid}.${dir}.${ext}`));
    }
  }
  writeFileSync(join(qDir, "flagged.json"), JSON.stringify(report.flagged, null, 2) + "\n");
  const kept = records.filter((r) => !flagged.has(r.record_id));
  writeBundle(
    args,
    kept,
    notes +
      `\n## Quarantined at capture\n\n${[...flagged].join(", ")} — see quarantine/flagged.json.\n`,
  );
  log(`quarantined ${flagged.size} flagged record(s); bundle rewritten with ${kept.length}`);
  return kept;
}

// --------------------------------------------------------------- main --
function chromeCommand(args) {
  const port = new URL(args.attach ?? "http://127.0.0.1:9222").port || "9222";
  return `google-chrome --user-data-dir="${args.profile}" --remote-debugging-port=${port} --no-first-run --new-window ${REPOSITORY}`;
}

async function openBrowser(args) {
  if (args.attach) {
    log(`attaching to the operator's Chrome at ${args.attach}`);
    const browser = await chromium.connectOverCDP(args.attach, { timeout: 15_000 });
    const context = browser.contexts()[0] ?? (await browser.newContext({ acceptDownloads: true }));
    const official = context.pages().find((p) => {
      try {
        return OFFICIAL_HOSTS.has(new URL(p.url()).hostname);
      } catch {
        return false;
      }
    });
    const page = official ?? context.pages()[0] ?? (await context.newPage());
    return { context, page, close: () => browser.close() };
  }
  const context = await chromium.launchPersistentContext(args.profile, {
    headless: false,
    channel: "chrome",
    acceptDownloads: true,
    viewport: null,
  });
  return {
    context,
    page: context.pages()[0] ?? (await context.newPage()),
    close: () => context.close(),
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  mkdirSync(args.output, { recursive: true });
  mkdirSync(args.profile, { recursive: true });
  if (args.printChromeCommand) {
    preparePdfDownloadPreference(args.profile);
    console.log(chromeCommand(args));
    return;
  }
  if (!args.attach) preparePdfDownloadPreference(args.profile);
  log(`case=${args.case} target-new=${args.targetNew} output=${args.output}`);
  log(`profile=${args.profile} (dedicated; not your normal Chrome profile)`);

  const { context, page, close } = await openBrowser(args);
  try {
    if (args.probe) {
      await runProbe(context, page, args);
      log(`probe complete → ${join(args.output, "probe")}`);
      return;
    }
    const { records, notes, summary } = await collect(context, page, args);
    writeBundle(args, records, notes);
    log(`bundle written → ${args.output} (${records.length} records)`);
    const kept = quarantineFlagged(args, records, notes);
    console.log(
      JSON.stringify(
        {
          ...summary,
          skipped: undefined,
          quarantined: records.length - kept.length,
          kept: kept.length,
        },
        null,
        2,
      ),
    );
    try {
      const py = join(ROOT, ".venv", "bin", "python");
      const out = execSync(
        `"${py}" "${join(ROOT, "scripts", "compare_capture.py")}" "${join(args.output, "manifest.json")}" --json "${join(args.output, "comparison.json")}"`,
        { cwd: ROOT, encoding: "utf8" },
      );
      console.log("compare_capture:\n" + out);
    } catch (err) {
      console.log("compare_capture:\n" + (err.stdout ?? "") + (err.stderr ?? err.message));
    }
  } finally {
    await close().catch(() => {});
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((err) => {
    console.error(`\nERROR: ${err.message}`);
    process.exit(1);
  });
}

export { acquirePdf, docIdOf, publicStatusFor, snapshotHtml, writeBundle };
