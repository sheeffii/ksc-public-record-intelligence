# KSC Public Record Intelligence — Project Memory

Live checkpoint. Answers “where exactly did we stop?”. Keep concise; no logs.

## Current Status

Current branch: `feat/phase-5b-visual-parity` (cut from `main` at `bdf7293`)
Phase 5B tag: `phase-5b-complete` → see `git tag --list`
Phase 6 tag: `phase-6-complete` → `bdf7293` (on `main`, pushed)
Phase 5 tag: `phase-5-complete` → `ee8a0e7` · Phase 4 tag: `phase-4-complete` → `b99f514`
Remote: `main` = `origin/main` = `bdf7293`. Phase 5B is local only; never push
without explicit instruction.
Roadmap: `docs/roadmap/`.
Current milestone: Phase 5B — UI/UX Visual Parity Remediation **COMPLETE**
(2026-09-20).
Next milestone: Phase 7 — KSC Public Record Discovery + Controlled 10–20
Document Ingestion (`docs/roadmap/PHASE_07_KSC_DISCOVERY_AND_CONTROLLED_INGESTION.md`).
**Not started; awaiting explicit authorisation.** This is the first phase that
touches real KSC material.
Current active task: None. Stop at the Phase 5B boundary.
Working tree at checkpoint: clean
Last updated: 2026-09-20

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

- Backend: 82 passed (31 unit + 51 integration).
- Frontend: 188 passed (Vitest; 176 prior + 12 Phase 5B composition / interaction).
- E2E: 96 passed (62 prior + 32 visual screenshots × desktop / Pixel 7 + 2
  mobile layout checks); screenshots land in `test-results/visual/`.
- Lint: ruff, ruff format, ESLint, Prettier clean. Typecheck: mypy strict, tsc clean.
- Production Next.js build passes.

Last full verification: 2026-09-20.

## Known Differences / Follow-up

- Screens still read the synchronous `@/mock` repository; `getRepository()`
  (ADR-009) is proven by contract tests but not yet wired into screens. Wire
  it when Phase 7 puts real records behind the API.
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
- Documents discovered/downloaded/parsed/indexed and transcripts parsed: all 0.

## Important Decisions

- ADR-001…008 remain in force.
- ADR-009: async repository contract with mock + API adapters; mock default.
- ADR-010: node registry for polymorphic graph references; visibility
  vocabulary incl. `not_public`; human verification requires a reviewer; enum
  values persisted; in-place migration `0002`.

## Exact Next Task

Only after explicit authorisation, begin Phase 7 by reading
`docs/roadmap/00_MASTER_ROADMAP.md` and the complete
`docs/roadmap/PHASE_07_KSC_DISCOVERY_AND_CONTROLLED_INGESTION.md`. Phase 7 is
the first controlled contact with real KSC public material: public-only,
official sources, 10–20 documents, every rule in `docs/SECURITY.md` and the
roadmap's public-only requirement applies. Nothing before that authorisation
may fetch anything.

## Do Not Forget

- Do not scrape, download, parse or ingest court material before Phase 7.
- Database and primary sources are authoritative; AI is analysis only.
- Protected witnesses remain W-code only and fail closed.
- Never fabricate identifiers, citations, quotes or figures; unresolved remains
  `UNRESOLVED`.
- No score/rank/weight/probability field about a person, anywhere.
- Never push unless explicitly told.

## Blockers

None.

## Useful Commands

```text
make up / down
make migrate · make seed · make demo-fixture
make lint
make typecheck
make test
pnpm build
pnpm e2e
```
