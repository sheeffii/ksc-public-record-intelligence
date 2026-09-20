# KSC Public Record Intelligence — Project Memory

Live checkpoint. Answers “where exactly did we stop?”. Keep concise; no logs.

## Current Status

Current branch: `feat/phase-7-controlled-ingestion` — fully merged (fast-forward)
into `main`; `main` = `origin/main` = `96e402a` (pushed 2026-09-20 on explicit
instruction). 5B and 7 are both on `main`.
Phase 7 commits: `86fbcfa` feat(api) · `fc4304b` feat(ingestion) · `448f5fb` docs ·
`f6ba449` feat(ingestion) real corpus · `7a867c9` test(ingestion) · `4979fc3` docs;
`3d05c4f` feat(ingestion) export-corpus · `96e402a` docs manifest.
Tags (all pushed): `phase-7-complete` → `96e402a` · `phase-5b-complete` → `eaeb4ce`
· `phase-6-complete` → `bdf7293` · `phase-5-complete` · `phase-4-complete`.
Remote: `main` = `origin/main` = `96e402a`. Never push without explicit instruction.
Migration head: `0003`.
Roadmap: `docs/roadmap/`.
Current milestone: **Phase 7 — COMPLETE (2026-09-20).** 22 real public records
of `KSC-BC-2020-06` ingested from operator capture bundle `2026-09-20-corpus-01`;
quality gate 22/22; idempotent re-run verified. Details:
`docs/ingestion/CONTROLLED_CORPUS.md`; tracked metadata manifest
`docs/ingestion/manifests/phase7-controlled-corpus.json` (`ksc-ingest export-corpus`).
Next milestone: Phase 8 — Parsing, exact citations, resolution index, search
(`docs/roadmap/PHASE_08_*.md`). **Not started; awaiting explicit authorisation.**
Current active task: None. Stop at the Phase 7 boundary.
Working tree at checkpoint: clean
Last updated: 2026-09-20

## Phase 7 — how it ended

- **Access:** both official hosts still served a Cloudflare challenge to any
  automated client on 2026-09-20 (ADR-011; never bypassed). The operator's
  interactive browser session on `repository.scp-ks.org` produced a 22-record
  capture (normalised detail-page snapshots + manifest + capture-time SHA-256 /
  sizes, no bytes) and the 22 PDFs were downloaded separately by the operator.
  Original capture stays in `~/Downloads/ksc-bc-2020-06-phase7-capture/`
  (untouched); the project copy is `data/captures/2026-09-20-corpus-01/`
  (git-ignored: PDFs, snapshots, manifests, `import_report.json`,
  `quality_gate_report.json`).
- **Matching:** `ksc-ingest import-capture` matched all 22 PDFs by exact
  SHA-256 (names never used), verified byte counts, re-hashed the copies,
  derived document / version references from the published id and confirmed
  19 against the reference printed in the PDF header (ADR-012); r16 adopted the
  header's `…/F03668/RED/A01/RED`; r09/r14 fell back to the published id;
  transcripts use `KSC-BC-2020-06/T/<date>[/sqi]`.
- **Real-case state (dev DB, bucket `ksc-documents`):** 22 source records ·
  19 documents (3 EN/SQ pairs share a document) · 22 versions, all `fetched` ·
  2 hearings (16 & 18 Feb 2026) · 3 transcripts · 22 MinIO objects
  (24,429,094 bytes) · jobs: 1 `live_probe` (blocked) + 3 `capture_bundle`
  (first run 22 downloaded; two re-runs 22 `skipped_duplicate` each) ·
  0 failed items in the bundle runs.
- **Quality gate:** `ksc-ingest gate` 22/22 PASS (32 checks per filing, 35 per
  transcript, incl. re-hash of the MinIO object = capture-time hash). Its first
  run caught a real defect (translation records overwrote the shared document's
  `source_url`) — fixed in `pipeline._upsert_document`, converged by re-run,
  covered by tests.
- **Idempotency:** third run left `source_records`, `documents`,
  `document_versions`, `hearings`, `transcripts` and the 22 objects
  byte-identical (incl. `updated_at`); only a new job with 22 `skipped_duplicate`.
- **Not a RED→RED2 pair:** r16 is Annex 1 of `F03668/RED` (itself redacted),
  r17 is `F03668/RED2`; stored as two documents, no `supersedes` link.
- **Not independently verified (operator observations only):** no public trial
  judgment on 2026-09-20; no public unredacted originals of redacted filings;
  the PCR search filters; corpus size 1,150+ decisions.

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

- Backend: 225 passed (160 unit incl. 129 `tests/unit/ingestion/` + 65
  integration incl. 14 `test_ingestion_pipeline.py`).
- Frontend: 188 passed (Vitest). Production `pnpm build` passes. E2E: 96 passed
  at the 5B checkpoint — not re-run for Phase 7 (no UI behaviour change; the
  ingestion status view is API + CLI only).
- Lint: ruff, ruff format, ESLint, Prettier clean. Typecheck: mypy strict
  (`ksc_api` + `ksc_ingestion`), tsc clean.
- Stack: api image at `0003`; `/ready` green; `/api/v1/ingestion/status` and
  `/api/v1/documents` serve the 19 real documents.

Last full verification: 2026-09-20.

## Known Differences / Follow-up

- Screens still read the synchronous `@/mock` repository; `getRepository()`
  (ADR-009) is proven by contract tests but not yet wired into screens. Real
  records now sit behind the API; wiring is a later-phase task.
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
- `capture_import.py` / `snapshot.py` (v0 capture → bundle), `quality_gate.py`.
- Real case: discovered 22 · downloaded 22 · parsed 0 · indexed 0 · transcripts
  parsed 0 (Phase 8) · failed 0.

## Important Decisions

- ADR-001…008 remain in force.
- ADR-009: async repository contract with mock + API adapters; mock default.
- ADR-010: node registry for polymorphic graph references; visibility
  vocabulary incl. `not_public`; human verification requires a reviewer; enum
  values persisted; in-place migration `0002`.
- ADR-011: official sites sit behind a Cloudflare challenge → never bypassed;
  ingestion is operator-assisted capture; metadata-only versions
  (`artifact_status = not_fetched`); failures are `ingestion_job_items` rows.
- ADR-012: version reference = the court's own header string (`/RED`, `/RED2`,
  `/COR/RED`, `/A01`, `/sqi`, `IA042/`); one document per filing/annex,
  translations are versions; transcripts keyed `…/T/<date>`; `reclassified`
  only on the court's stamp; PDFs matched to records by SHA-256 only.

## Exact Next Task

Only after explicit authorisation, begin Phase 8 by reading
`docs/roadmap/00_MASTER_ROADMAP.md` and the complete
`docs/roadmap/PHASE_08_PARSING_EXACT_CITATIONS_RESOLUTION_AND_SEARCH.md`, then
parse the 22 held versions (text layer present on all; transcripts carry
25-line pages and running page numbers, e.g. `Page 29148`). Nothing before that
authorisation may parse, segment, extract or index.

## Do Not Forget

- Never solve, spoof or proxy around the Cloudflare challenge; a blocked fetch
  is recorded, not retried (ADR-011). Bytes come only from operator captures.
- Only the controlled corpus is held; no bulk download; no parsing beyond
  validation until Phase 8 is authorised.
- `data/captures/` is git-ignored and holds real public court PDFs; never
  commit it. The Downloads originals are the operator's; never modify them.
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
.venv/bin/ksc-ingest import-capture <src> data/captures/<id> --pdf-dir ~/Downloads --bundle-id <id> --captured-by …
.venv/bin/ksc-ingest bundle data/captures/<id> [--dry-run] · ksc-ingest gate data/captures/<id> · ksc-ingest status
.venv/bin/ksc-ingest probe <official url> --record
make lint
make typecheck
make test
pnpm build
pnpm e2e
```
