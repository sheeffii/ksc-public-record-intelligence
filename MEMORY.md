# KSC Public Record Intelligence — Project Memory

Live checkpoint. Answers “where exactly did we stop?”. Keep concise; no logs.

## Current Status

Current branch: `feat/phase-7-controlled-ingestion` (cut from `eaeb4ce`, the
Phase 5B checkpoint on `feat/phase-5b-visual-parity`).
Phase 7 commits so far: `86fbcfa` feat(api) · `fc4304b` feat(ingestion) ·
docs commit (this checkpoint) — see `git log --oneline -3`.
Tags: `phase-5b-complete` → `eaeb4ce` · `phase-6-complete` → `bdf7293` (on `main`,
pushed) · `phase-5-complete` → `ee8a0e7` · `phase-4-complete` → `b99f514`.
No `phase-7-complete` tag: Phase 7 is not complete.
Remote: `main` = `origin/main` = `bdf7293`. Nothing since is pushed; never push
without explicit instruction.
Roadmap: `docs/roadmap/`.
Current milestone: **Phase 7 — KSC Public Record Discovery + Controlled 10–20
Document Ingestion — IN PROGRESS** (started 2026-09-20, authorised by the user).
Capture-independent work is complete; real-record ingestion is **blocked on an
operator browser capture bundle** (ADR-011).
Current active task: waiting for `data/captures/<bundle-id>/` from the operator;
then write the PCR detail-page parser against the saved pages, ingest, run the
quality gate, commit, tag `phase-7-complete`.
Working tree at checkpoint: clean (Phase 7 capture-independent work committed)
Last updated: 2026-09-20

## Phase 7 — where exactly we stopped

- **Discovery finding (2026-09-20):** `www.scp-ks.org` and `repository.scp-ks.org`
  (detail pages, PDF paths, and both `robots.txt`) answer identified automated
  clients with `HTTP 403` + `cf-mitigated: challenge` (Cloudflare managed
  challenge). This is an access control → never bypassed (ADR-011). Records
  therefore enter via **operator capture bundles** saved by a human in a normal
  browser (`docs/ingestion/OPERATOR_CAPTURE.md`); URL shapes and what is still
  unverified are in `docs/ingestion/OFFICIAL_SOURCES.md`.
- **Built and tested:** `workers/ingestion` (`ksc_ingestion`: sources, fetch,
  discovery, normalize, capture, artifacts, storage, pipeline, probe, cli);
  migration `0003` (`document_versions.artifact_status|byte_size|fetched_at|
fetch_method`, `ingestion_job_items`); read API exposes `artifact_status` /
  `fetched_at` on versions and `GET /api/v1/ingestion/status`; web API types
  mirrored; CLI `ksc-ingest bundle|probe|status`.
- **Real-case state:** `KSC-BC-2020-06`: 0 source records, 0 documents,
  0 versions; 1 `live_probe` job with 1 `blocked_by_access_control` item
  (recorded 2026-09-20 09:26 UTC, one request to `robots.txt`).
- **Blocked only by captures:** PCR detail-page / listing / case-page parsers
  (`DetailPageParser` interface exists; implement against real saved HTML, not
  guesses), the 10–20-record selection list with reasons, real ingestion, the
  manual quality gate, `docs/ingestion/OFFICIAL_SOURCES.md` "not yet inspected"
  section, real Albanian-variant handling, `phase-7-complete` tag.

## What Works

- **Phase 5B screens** (`apps/web/src/components/screens/phase5/`): every
  authoritative screen rebuilt to PAGE_SPECS composition over the same mock
  boundary — home (quick-search pills, 7-stat row, recent panels, ingestion
  health); grouped search with category tabs, filter rail, query interpretation,
  syntax reference, ranking disclaimer; directories / evidence explorer as a
  dense table workspace with working filters, sort, density, page size,
  pagination, CSV export, detail / preview / linked panels and the column-meaning
  footer over 24 generated demo rows per kind; person dossier (hex avatar, role
  badges, aliases, 4 quick actions, Record References strip, 10 tabs, cited
  summary, judgment-order findings table, typed dates, network preview, rail,
  no-score footer); witness dossier (two header states, 7-stat strip,
  Compare / Ask AI, 10 tabs, chronology rail with closed-session rows,
  testimony reader, findings-citing / prior-statement / comparison panels);
  statement comparison (topic rail, three columns, diff span, AI band, label
  picker + mark reviewed, legend, language rules, Chamber-attributed
  credibility card); document reader (breadcrumb + type badges, pager, copy
  citation, sidebar with metadata / in-doc search / ToC / versions, 600px
  page with ¶ anchors, cited banner, footnotes, redaction gap, six research
  tabs); finding detail (01–09 numbered spine, scroll-spy rail, related
  findings, analysis rail); incident (header, charge chips, 9 tabs, direction
  summary, matrix with direction / court-cited filters and sort, positions
  rail, required notes); timeline (7 toggleable lanes, dual-era axis with
  per-era zoom, date-type legend, empty lanes kept, card detail rail with
  attached dates, mobile vertical list); network (toolbar: layout, depth,
  filters, save view, export, fullscreen, resolving chip; legend rail with
  date slider and verification filter; node / edge inspectors; minimap;
  three-detent mobile sheet); evidence path (entity picker, max hops, banner,
  canvas, expandable hop inspector, composition, alternates, cannot-tell card);
  appeal (category rail with counts, expandable issue cards with six sections,
  review actions, coverage / will-not-do / status rail, legal strip); argument
  lab (editor flagging uncited sentences, citation health, 8 actions, stepper,
  three stage columns, neutral review rows with apply, required notes); AI
  research (session rail, question, retrieved-first list, record blocks →
  boundary → AI block, sources / citation status / verification / not-available
  rail, action bar); public mode (dedicated light composition: mode toggle,
  hero, before-you-begin, six entry cards, worked example with term tooltips,
  original text, does-not-mean, where-from, other-side).
- Phase 6 backend, read API and `apps/web/src/data/` boundary unchanged.
- Docker stack healthy with rebuilt web + api images; no court document was
  discovered, downloaded, parsed or indexed; no model provider is called.

## Tests

- Backend: 203 passed (140 unit incl. 109 `tests/unit/ingestion/` + 63
  integration incl. 12 `test_ingestion_pipeline.py`).
- Frontend: 188 passed (Vitest). E2E: 96 passed at the 5B checkpoint (not re-run
  for Phase 7 — no UI change).
- Lint: ruff, ruff format, ESLint, Prettier clean. Typecheck: mypy strict
  (`ksc_api` + `ksc_ingestion`), tsc clean.
- Stack: api image rebuilt with `0003`; `/ready` green; status endpoint live.

Last full verification: 2026-09-20.

## Known Differences / Follow-up

- Screens still read the synchronous `@/mock` repository; `getRepository()`
  (ADR-009) is proven by contract tests but not yet wired into screens. Wire
  it once real records sit behind the API (after the Phase 7 quality gate).
- No admin/data-status UI yet: the internal view is the API endpoint
  `/api/v1/ingestion/status` and `ksc-ingest status` (roadmap: "if useful").
- Visual checks are screenshot artefacts plus region assertions, not pixel
  baselines; compare against `docs/design/Design.html` by eye.
- Network graph remains the accessible SVG implementation (engine choice
  deferred until real scale). Timeline positions are illustrative.
- Search date-range inputs, Save view, Export (network) and stage "Compare"
  are present but inert until real data exists.
- Albanian strings for `phase5b` are provisional and need review against
  official KSC Albanian texts.
- Design-package provenance limitation from Phase 4 remains; do not rewrite
  `docs/design/`.

## Architecture State

- `apps/api/src/ksc_api/models/` — evidence model (see `docs/DATA_MODEL.md`);
  `db_enum()` persists enum values; `VerificationMixin` + reviewer CHECK.
- `apps/api/src/ksc_api/{schemas,repositories,routers/records.py}` — read API;
  `repositories/filters.py` holds the fail-closed rules.
- `apps/api/src/ksc_api/fixtures/demo.py` — synthetic case; `ksc-demo-fixture`.
- `apps/web/src/data/` — `ResearchRepository` contract, mock adapter,
  `api/{client,mappers,repository}.ts`, `getRepository()`.
- `apps/web/src/mock/` remains the boundary screens import; `mock/volume.ts`
  generates demo table volume. `screens/phase5/Workspace.tsx` holds the shared
  5B building blocks (toolbar, stat strip, rail index, stepper, pager…).
- `workers/ingestion/src/ksc_ingestion/` — Phase 7 pipeline (see
  `workers/ingestion/README.md`); `tests/support/synthetic.py` builds the
  synthetic `KSC-DEMO-0000` capture bundle the tests ingest.
- `apps/api/src/ksc_api/{schemas,repositories,routers}/ingestion.py` — internal
  data-status read (not public-filtered; identifiers and URLs only).
- Documents discovered/downloaded/parsed/indexed and transcripts parsed for the
  real case: all 0 (1 blocked live probe recorded).

## Important Decisions

- ADR-001…008 remain in force.
- ADR-009: async repository contract with mock + API adapters; mock default.
- ADR-010: node registry for polymorphic graph references; visibility
  vocabulary incl. `not_public`; human verification requires a reviewer; enum
  values persisted; in-place migration `0002`.
- ADR-011: official sites sit behind a Cloudflare challenge → never bypassed;
  ingestion is operator-assisted capture; metadata-only versions
  (`artifact_status = not_fetched`); failures are `ingestion_job_items` rows.

## Exact Next Task

1. Operator produces `data/captures/<bundle-id>/` per
   `docs/ingestion/OPERATOR_CAPTURE.md` (listing pages, case page, user guide,
   10–20 detail pages + PDFs, manifest).
2. Read the saved pages; document real metadata fields / version linking in
   `OFFICIAL_SOURCES.md`; implement `PcrDetailPageParser` (+ listing / case
   page parsers) with fixtures cut from the saved HTML; register them in the CLI.
3. `ksc-ingest bundle … --dry-run`, then ingest; run the quality gate per record;
   record the corpus list with reasons in `docs/ingestion/CONTROLLED_CORPUS.md`.
4. Update MEMORY / PROJECT_STATE / INGESTION counts; tag `phase-7-complete`;
   write the completion report. Do **not** start Phase 8.

## Do Not Forget

- Never solve, spoof or proxy around the Cloudflare challenge; a blocked fetch
  is recorded, not retried (ADR-011). Bytes come only from operator captures.
- Only the controlled 10–20 records in Phase 7; no bulk download; no parsing
  beyond validation until Phase 8 is authorised.
- Database and primary sources are authoritative; AI is analysis only.
- Protected witnesses remain W-code only and fail closed.
- Never fabricate identifiers, citations, quotes or figures; unresolved remains
  `UNRESOLVED`.
- No score/rank/weight/probability field about a person, anywhere.
- Never push unless explicitly told.

## Blockers

- Real-record ingestion needs an operator capture bundle (human browser
  session on the official site). Everything else in Phase 7 is done.

## Useful Commands

```text
make up / down
make migrate · make seed · make demo-fixture
.venv/bin/ksc-ingest bundle data/captures/<id> [--dry-run] · ksc-ingest status
.venv/bin/ksc-ingest probe <official url> --record
make lint
make typecheck
make test
pnpm build
pnpm e2e
```
