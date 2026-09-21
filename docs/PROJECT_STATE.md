# Project state

Long-term implementation tracker. `MEMORY.md` is the live checkpoint; this file
tracks milestones, features, debt and status across sessions.

Last updated: 2026-09-21 (Phase 10 complete)

## Milestones

| Phase  | Scope                                                                                                     | Status                                                                                                   |
| ------ | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 1–3    | Product definition, design system, 21-artboard UX package, flow audit                                     | ✅ Delivered (docs/design)                                                                               |
| **4**  | **Engineering foundation** — monorepo, shell, tokens, i18n, theme infra, API, DB, Docker, tests, CI, docs | ✅ **Complete (2026-09-19)**                                                                             |
| **5**  | **Implement approved UI with mock data (all 21 screens + 5 directories, DemoDataFlag everywhere)**        | ✅ **Functionally complete (2026-09-19)** — visual parity: remediation pending (Phase 5B)                |
| **6**  | **Real database / evidence model and API-backed repository contracts**                                    | ✅ **Complete (2026-09-20)**                                                                             |
| **5B** | **UI/UX visual parity remediation against `docs/design/Design.html`**                                     | ✅ **Complete (2026-09-20)**                                                                             |
| **7**  | **KSC public record discovery + controlled document ingestion (first real KSC data)**                     | ✅ **Complete (2026-09-20)** — 22 real public records, quality gate 22/22, idempotent (ADR-011, ADR-012) |
| **8**  | **Parsing, exact citations, resolution index, search**                                                    | ✅ **Complete (2026-09-20)** — controlled-corpus quality gate PASS (ADR-013)                             |
| **9**  | **Real evidence network and timeline**                                                                    | ✅ **Complete (2026-09-21)** — controlled-corpus quality gate PASS (ADR-014)                             |
| **10** | **Judgment, findings and evidence matrix**                                                                | ✅ **Complete (2026-09-21)** — real Court-decision quality gate PASS (ADR-015)                           |
| 11     | Citation-first AI / RAG                                                                                   | **Next / pending**                                                                                       |
| 12     | Appeal research, red team and statement comparison                                                        | Planned                                                                                                  |
| 13     | Gradual full public corpus ingestion and production hardening                                             | Planned                                                                                                  |
| 14     | External media and public statements intelligence                                                         | Post-core / later                                                                                        |

## Roadmap

The persistent execution plan is `docs/roadmap/` (installed 2026-09-19):
`00_MASTER_ROADMAP.md` is the high-level plan and each `PHASE_*.md` is the
execution specification for one milestone. Phases 6, 5B, 7, 8, 9, and 10 are
complete. Remaining planned order: 11 → 12 → 13 → 14.
The table above is the status record; the roadmap files hold scope and acceptance
criteria. Phase 10 is complete; Phase 11 is next/pending. Repository code,
migrations, tests and Git state win over stale roadmap text.

## Completed features (Phase 4)

Frontend (`apps/web`)

- Next.js 16 / React 19 / TS strict / Tailwind 4; standalone Docker build.
- Design tokens transcribed from DESIGN_SYSTEM.md (dark + light sets, source palette,
  direction colours, AI surfaces, radii, elevation, chrome heights, breakpoints).
- Two font families via next/font (DM Sans, Libre Baskerville).
- Application shell: GlobalNav (52px, overflow menu <1280px, AI link styling),
  CaseStripe with untranslated case id + DemoDataFlag, GovernanceFooter, five-item
  MobileTabBar (<860px), skip link, SurfaceTheme (light for reader/public).
- Theme infrastructure: next-themes provider (dark default) + tested ThemeToggle
  (not mounted — ADR-006).
- i18n: next-intl without routing, cookie locale, EN/SQ tables (166 keys, parity-tested),
  LanguageToggle with server action.
- Provenance primitives: SourceBadge (9 types), VerificationBadge (5 states, glyphs),
  CitationChip (null when unresolved, deep-links to reader), ProvenanceBoundary.
- Primitives: Button, Panel, DataTable + DensityToggle, FilterChip/ActiveFilters/
  FilterRail/FilterOption, SkeletonBlock, PendingCount, EmptyState, ErrorState,
  GapNotice, Modal, Drawer (Radix).
- 23 route pages per ROUTE_MAP.md rendering PlaceholderScreen inside the shell;
  homepage foundation (hero, search → /search, pending-dash stats, explore grid);
  not-found page; /api/health.
- Route registry with tab sets and light/dark modes; citation formatter for the
  four canonical forms.

Backend (`apps/api`)

- FastAPI app factory; `/health`, `/ready` (db, pgvector, redis, minio → 503 on
  failure), `/version`; CORS from env.
- pydantic-settings config; no AI key required.
- SQLAlchemy 2 (sync, psycopg 3); models Case, Document, AuditLog.
- Alembic `0001`: `CREATE EXTENSION vector`, three tables, two enums.
- Idempotent seed of KSC-BC-2020-06 public metadata + audit entry; container
  entrypoint runs migrate + seed.

Infrastructure

- docker-compose: postgres (pgvector/pg16), redis, minio (quay.io) + bucket init,
  api, web — all with healthchecks; `.env.example`; Makefile (dev/up/down/test/
  lint/migrate/reset-db/logs/format/typecheck/seed/e2e/ci).
- GitHub Actions CI: frontend format/lint/typecheck/test/build; backend ruff/mypy/
  pytest with postgres+redis services and MinIO container.

Shared / docs

- `@ksc/shared` contract types (Citation, VerificationState, Witness, Direction,
  ReferenceCounts, AnswerBlock, Gap, DateType, Locale).
- CLAUDE.md, AGENTS.md, MEMORY.md, README.md, docs/ARCHITECTURE.md, DATA_MODEL.md,
  DECISIONS.md (ADR-001…007), SECURITY.md, AI_METHODS.md, INGESTION.md,
  DEVELOPMENT.md.

## Unfinished / deferred (by design)

- Screens reading through `getRepository()` and persistent interaction state
  (Phase 5B / Phase 7).
- Ingestion, parsing and the citation resolver that fills `citations` and
  `record_identifiers` (Phase 7 / Phase 8).
- Production-scale graph rendering and real AI retrieval remain later phases.
- Albanian legal terminology needs specialist review against official KSC texts.

## Completed features (Phase 5)

- Branch `feat/phase-5-approved-ui` created from the verified Phase 4 checkpoint.
- Added the matched `RecordBlock` / `AiAnalysisBlock` provenance pair,
  `CitationPreview`, `ProtectionNotice`, `DirectionBadge` + `ScopeNote`, and
  `ReferenceCountStrip`.
- Added a typed `MockRepository` boundary and centralized generic demo records under
  `apps/web/src/mock/`; no real court material or provider call is involved.
- Replaced every generic route placeholder with the approved mock-data experience:
  overview, search and command palette, directories, dossiers, comparison, readers,
  evidence, network/path, timeline, incident/finding chain, appeal, argument/red
  team, AI research and public/simple mode.
- Implemented desktop and representative mobile states, including collapsible
  reader context and a network bottom-sheet inspector.
- Added keyboard-accessible controls, semantic tables/headings, non-color badge
  labels, reduced-motion handling and a textual graph alternative.
- Added six major E2E workflows across desktop and mobile and regression tests for
  provenance, protected-witness safety, repository validity and prohibited scoring.
- Documentation discrepancy retained without redesign: `HANDOFF.md` says 83
  components while `COMPONENTS.md` inventories 91; its “Nine rules” summary lists ten.

## Completed features (Phase 6)

- Branch `feat/phase-6-evidence-model` from `main` (`3e9f8f8`); tag
  `phase-6-complete`.
- Alembic `0002`: 34 new tables on top of the Phase 4 three; `documents`
  migrated in place (`public_state` → `visibility`, artifact columns →
  `document_versions`); 23 explicit enum types; upgrade with data, `alembic
check` and `head → base → head` are integration-tested.
- Models under `apps/api/src/ksc_api/models/` with schema-level rules:
  protected witness without identity, page/line validation, unique SHA-256,
  resolved-only targets, mandatory relationship provenance, node registry with
  real FKs, reviewer-required human verification, human-only research notes.
- Read API `/api/v1` (24 routes) with Pydantic contracts, case scoping,
  pagination, public-only filtering and structural witness protection.
- Synthetic fixture `KSC-DEMO-0000` (`ksc-demo-fixture`) covering the five
  required traversals plus rejected / unresolved negative rows.
- Frontend `apps/web/src/data/`: `ResearchRepository`, mock adapter (default),
  `ApiRepository` with fail-closed mappers, `getRepository()` selection,
  swap-ability contract test.
- Docs: `DATA_MODEL.md` rewritten, `ARCHITECTURE.md`, `DEVELOPMENT.md`,
  `INGESTION.md`, ADR-009, ADR-010.
- Not done by design: screens still read the sync mock; no path engine; no AI
  run; no embedding column; no real record.

## Completed features (Phase 5B)

- Branch `feat/phase-5b-visual-parity` from `main` (`bdf7293`); tag
  `phase-5b-complete`.
- Every authoritative screen recomposed to PAGE_SPECS regions, rails and
  controls (see MEMORY.md → What Works); five directory routes share one dense
  table workspace with functioning filter / sort / density / pagination /
  export over generated demo volume.
- Shared 5B building blocks in `screens/phase5/Workspace.tsx`; `phase5b`
  string namespace (333 keys, EN/SQ parity); date-type glyph utilities on the
  source palette tokens.
- Mobile: three-detent network sheet, reader sidebar / panel toggles,
  comparison A/B/C control, stage tabs, timeline vertical list, appeal category
  dropdown, term tooltips as bottom sheets.
- Tests: 12 composition / interaction tests, 16-screen visual screenshot spec
  across desktop and Pixel 7, two mobile layout assertions. All prior tests
  green; design docs untouched.
- Not done by design: screens still consume the sync mock; no pixel baselines.

## Completed features (Phase 7)

- Discovery: both official hosts serve a Cloudflare managed challenge to
  automated clients (`HTTP 403`, `cf-mitigated: challenge`), including
  `robots.txt`. Treated as an access control — never bypassed (ADR-011).
  Findings, confirmed URL shapes and open questions:
  `docs/ingestion/OFFICIAL_SOURCES.md`.
- Decision: records enter through **operator capture bundles** (a human saving
  official pages and PDFs in a normal browser; `docs/ingestion/OPERATOR_CAPTURE.md`).
- Delivered: `workers/ingestion` (`ksc_ingestion`) — host allowlist / URL
  classification, identified fetcher with challenge detection that fails
  closed, capture manifest schema + validation, discovery contract,
  normalization (version types, visibility fail-closed, dates, parties),
  SHA-256 + PDF validation, hash-addressed MinIO storage, resumable /
  idempotent pipeline writing `source_records` · `documents` ·
  `document_versions` · `hearings` / `transcripts` · `ingestion_jobs` ·
  `ingestion_job_items` · `audit_log`; CLI `ksc-ingest bundle|probe|status`.
- Schema: migration `0003` — `document_versions.artifact_status`
  (`not_fetched|fetched|failed`, CHECK-tied to hash + object), `byte_size`,
  `fetched_at`, `fetch_method`; new `ingestion_job_items`.
- API: `artifact_status` / `fetched_at` on version reads;
  `GET /api/v1/ingestion/status` (internal data-status view). Web API types
  mirrored.
- Tests: 109 unit (sources, fetch, normalize, artifacts, capture, probe) +
  12 integration (full synthetic bundle, idempotent re-run, crash → resume,
  metadata-only fill, never-overwrite, duplicate bytes, fail-closed
  visibility, wrong case, other-case refusal, dry run, recorded blocked probe,
  status endpoint) over the synthetic `KSC-DEMO-0000` bundle
  (`tests/support/synthetic.py`). No real record is described by any fixture.
- Real capture (2026-09-20): operator browser session → 22-record capture
  (normalised detail-page snapshots, manifest, capture-time SHA-256 / sizes)
  plus 22 separately downloaded PDFs. `ksc-ingest import-capture` matched all
  22 by exact SHA-256, confirmed references against the PDF headers (ADR-012)
  and wrote bundle `2026-09-20-corpus-01` (git-ignored).
- Ingested: 22 source records · 19 documents · 22 versions (all fetched) ·
  2 hearings · 3 transcripts · 22 MinIO objects (24,429,094 bytes). Coverage:
  indictment annex EN/SQ, SPO (incl. 716-page final trial brief COR/RED),
  Defence for all four accused, Pre-Trial Judge / Trial Panel / President
  decisions, Court of Appeals (IA042), Registrar, Victims' Counsel, transcripts
  EN/SQ, RED2 generations, three court-stamped reclassifications. No trial
  judgment and no public unredacted original were found in this capture
  (operator observation, not independently verified).
- `ksc-ingest gate`: 22/22 PASS (32–35 checks per record incl. MinIO object
  re-hash). Idempotent re-run: all record tables and objects byte-identical.
- Tracked metadata manifest `docs/ingestion/manifests/phase7-controlled-corpus.json`
  (`ksc-ingest export-corpus`, schema-validated by a unit test); no PDFs or
  captured pages in Git.
- New modules: `snapshot.py`, `capture_import.py`, `quality_gate.py`,
  `corpus_manifest.py`; tests
  +17 (15 unit, 2 integration). Docs: `CONTROLLED_CORPUS.md`,
  `OFFICIAL_SOURCES.md` (verified vs not yet verified), ADR-012.
- No admin UI (API + CLI status view); raw PCR DOM parser interface remains
  unfilled because no raw official PCR page is held.

## Completed features (Phase 8)

- Final closeout audit completed 2026-09-20: all nine Phase 8 acceptance
  criteria verified against implementation commit `9fc67c5`, final verified
  code/test baseline `02ab3c8`, migration `0004`, automated tests, live
  service/database probes, and the pinned controlled-corpus quality gate. The
  Phase 8 roadmap was marked COMPLETE before Phase 9 began.

- Migration `0004` adds parser provenance, exact PDF/source coordinate layers,
  numbered paragraphs, citation audit fields, and generated PostgreSQL FTS
  vectors with GIN indexes.
- The held-object parser processed all 22 controlled versions using native text:
  1,979 pages, 1,233 numbered paragraphs, 1,592 structural chunks, and 607
  transcript segments. No OCR was needed and no version requires review.
- Deterministic extraction persists exact raw references and source character
  spans. The resolver uses `record_identifiers` and held coordinates only;
  resolved, ambiguous, unresolved, and invalid are terminal persisted states.
- PostgreSQL search supports exact identifiers, phrases, keywords, document/date/
  party/language/source filters, transcript text, and exact reader target paths.
- The server-rendered Search and Document Reader routes now use the configured
  repository (`mock` or `api`); real mode does not render demo content panels.
- Real-corpus evaluation: `docs/ingestion/PHASE8_QUALITY_GATE.md` and the tracked
  `phase8-controlled-corpus-quality.json` report. No new documents were fetched.

## Completed features (Phase 9)

- Final closeout audit completed 2026-09-21 against implementation commits
  `431f1dd` and `ac59afa`, verified code/test baseline `548a151`, migration
  `0005`, all automated gates, live real-case API/database probes and the pinned
  controlled-corpus quality report.
- `ksc-ingest build-evidence` deterministically projects already-persisted Phase
  8 data only. The controlled graph has 13 document nodes and 22 exact-citation
  `CITED_IN` edges; one self-citation is omitted and zero analytical,
  unsupported, self, or citation-less edges were created.
- Relationship contracts carry source category, extraction origin, optional
  typed date, exact resolved target citation and exact citing-source coordinates.
  Evidence paths use bounded neutral BFS over eligible public source-backed
  edges; every hop is independently cited.
- The real timeline contains 19 source-record-backed events: 11 document dates,
  6 decisions/orders and 2 hearing/testimony dates. Date types and precision
  remain distinct; absent categories remain absent.
- Network, Evidence Path and Timeline use the API repository in real mode and
  suppress demo content. Network supports node search; source, verification,
  true from/to date, entity and relationship filters; inspectors;
  expand/collapse; isolate; reset; exact-source links; and a textual alternative.
- The required neutrality warning is unchanged. No person relationship,
  co-mention, guilt, responsibility, agreement, importance, or evidential weight
  is inferred.
- The measured graph is 13 nodes / 22 edges, so the accessible SVG renderer is
  retained. `docs/ingestion/PHASE9_QUALITY_GATE.md` records the PASS result.
- Final gates: 238 backend tests, 191 frontend tests, production build, lint,
  typecheck, migration round-trip/drift checks, real API smoke and Playwright
  (96 passed, 2 skipped) all pass.

## Completed features (Phase 10)

- Final closeout audit completed 2026-09-21 against implementation commit
  `c8eaa1e`, migration `0006`, automated gates, live real-case database/API/UI
  probes and the pinned controlled-corpus quality report.
- The 22-record corpus has no Trial Judgment. The real benchmark is explicitly
  Court decision `KSC-BC-2020-06/F03752`; no brief was substituted and no new
  material was ingested.
- One human-verified finding preserves exact paragraphs 12–16. One exact
  resolved Court-cited evidence link targets held version `F03667/COR/RED` with
  source coordinates and verification provenance.
- One Defence and one SPO position are stored separately as exact Court
  summaries; missing underlying filings F03743/F03746 remain explicit. One exact
  Court response is linked independently to both positions.
- The queryable matrix API and real Finding Detail provide structural navigation,
  exact-source opening, evidence categories and a source audit. No unsupported
  evidence link, AI-generated canonical finding, legal conclusion or score exists.
- Final gates: 238 backend tests, 194 frontend tests, production build, lint,
  typecheck, migration round-trip/drift checks, real-corpus gate, standard
  Playwright (96 passed / 4 skipped), and real-data Phase 10 Playwright (2 passed).

## Technical debt / notes

- `next/font/google` fetches fonts at build time; builds need network access.
- Playwright e2e passes locally (Chromium only; mobile project uses Pixel 7) but is not in CI.
- Albanian strings are provisional pending review against official KSC texts.
- `eslint` pinned to 9.x: `eslint-config-next@16.3.5` → `eslint-plugin-react@7`
  is incompatible with ESLint 10.
- MinIO images pulled from `quay.io/minio/*` (Docker Hub pull was denied).
- Web/API healthchecks use `127.0.0.1` (busybox `wget` resolves `localhost` to ::1).
- Container image sizes: api 364 MB, web 296 MB (not yet optimised).

## Known parser / data issues

- The controlled corpus produced no naturally ambiguous citation. The state is
  exercised with an overlapping-transcript fixture and always remains targetless.
- Native-text parsing is deliberately conservative. Unrecognized structures stay
  as page chunks; speaker, line, paragraph, and printed-page coordinates are never
  inferred. OCR is not implemented because none of the 22 inputs requires it.
- Citation extraction is intentionally broad and preserves 14,105 syntactically
  valid references as unresolved; corpus expansion, not fuzzy matching, may resolve
  them in Phase 13.

## Test / evaluation status

| Suite                                    | Count        | Last result                                   |
| ---------------------------------------- | ------------ | --------------------------------------------- |
| Backend unit (pytest)                    | 168          | pass                                          |
| Backend integration (pytest, live infra) | 70           | pass                                          |
| Frontend (vitest)                        | 194          | pass                                          |
| E2E (playwright)                         | 50 specs × 2 | 96 pass / 4 skip; Phase 10 real-data 2/2 pass |
| Evaluation                               | 0            | reserved directory                            |

Lint/typecheck: ruff, ruff format, mypy --strict, eslint, tsc, prettier — all pass.

## Deployment state

Local only: stack verified 2026-09-21 with all five services healthy after
rebuilding the API image (migration `0006` applied; ingestion status endpoint
live). Git:
Phase 6 tag `phase-6-complete` = `bdf7293`. Phase 5B is on `feat/phase-5b-visual-parity`, tag
`phase-5b-complete`, not pushed. Phase 5B and Phase 7 were
fast-forwarded into `main` on 2026-09-20: `main` = `origin/main` = `96e402a`,
tags `phase-5b-complete` and `phase-7-complete` pushed. No remote deployment
or production workflow. Phase 10 is complete on
`feat/phase-10-judgment-findings-matrix`; local tag `phase-10-complete` marks
its final documentation checkpoint. The Phase 10 branch/tag have not been
pushed or merged.

## Verification limitations

`docs/design/DESIGN_SYSTEM.md`, `ROUTE_MAP.md`, `PAGE_SPECS.md` were re-transcribed
from a verbatim read after an accidental formatter pass; structurally verified
(line counts, sections, fences, spec fields) but not byte-verified because no
original copy exists locally. See MEMORY.md → Current Problems.

## Ingestion state

Real case `KSC-BC-2020-06` (bundle `2026-09-20-corpus-01`): source records 22 ·
documents 19 · versions 22 (fetched 22 · parsed 22 · not_fetched 0 · failed 0) ·
hearings 2 · transcripts 3 · MinIO objects 22 · indexed documents 19 · pages
1,979 · paragraphs 1,233 · chunks 1,592 · transcript segments 607 · citations
14,205 (23 resolved · 0 ambiguous · 14,105 unresolved · 77 invalid) · failed 0.
Bytes came from the operator's browser downloads matched by SHA-256; the
pipeline itself fetched nothing from the court site (ADR-011).

Phase 9 projection: graph nodes 13 · citation-backed edges 22 · source-backed
timeline events 19 (document 11 · decision 6 · testimony 2). No additional
record was ingested.

Phase 10 projection: findings 1 · exact paragraph mappings 1 · explicit
Court-cited evidence links 1 · party positions 2 (Defence 1 · SPO 1) · Court
response links 2 · human-verified relationships 6. All five distinct linked
citations resolve; missing underlying filings F03743/F03746 and the absent Trial
Judgment remain explicit. No additional record was ingested.
