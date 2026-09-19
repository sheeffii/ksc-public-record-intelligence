# Project state

Long-term implementation tracker. `MEMORY.md` is the live checkpoint; this file
tracks milestones, features, debt and status across sessions.

Last updated: 2026-09-20

## Milestones

| Phase | Scope                                                                                                     | Status                                                                                    |
| ----- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 1–3   | Product definition, design system, 21-artboard UX package, flow audit                                     | ✅ Delivered (docs/design)                                                                |
| **4** | **Engineering foundation** — monorepo, shell, tokens, i18n, theme infra, API, DB, Docker, tests, CI, docs | ✅ **Complete (2026-09-19)**                                                              |
| **5** | **Implement approved UI with mock data (all 21 screens + 5 directories, DemoDataFlag everywhere)**        | ✅ **Functionally complete (2026-09-19)** — visual parity: remediation pending (Phase 5B) |
| **6** | **Real database / evidence model and API-backed repository contracts**                                    | ✅ **Complete (2026-09-20)**                                                              |
| 5B    | UI/UX visual parity remediation against `docs/design/Design.html`                                         | **Next** (not started); before Phase 7                                                    |
| 7     | KSC public record discovery + controlled 10–20 document ingestion (first real KSC data)                   | Not started                                                                               |
| 8     | Parsing, exact citations, resolution index, search                                                        | Planned                                                                                   |
| 9     | Real evidence network and timeline                                                                        | Planned                                                                                   |
| 10    | Judgment, findings and evidence matrix                                                                    | Planned                                                                                   |
| 11    | Citation-first AI / RAG                                                                                   | Planned                                                                                   |
| 12    | Appeal research, red team and statement comparison                                                        | Planned                                                                                   |
| 13    | Gradual full public corpus ingestion and production hardening                                             | Planned                                                                                   |
| 14    | External media and public statements intelligence                                                         | Post-core / later                                                                         |

## Roadmap

The persistent execution plan is `docs/roadmap/` (installed 2026-09-19):
`00_MASTER_ROADMAP.md` is the high-level plan and each `PHASE_*.md` is the
execution specification for one milestone. Planned order from here:
6 → 5B → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14. The table above is the status
record; the roadmap files hold scope and acceptance criteria. Repository code,
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
- Search over real records, production-scale graph rendering and real AI retrieval
  remain later phases.
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

None — nothing parsed.

## Test / evaluation status

| Suite                                    | Count        | Last result                                        |
| ---------------------------------------- | ------------ | -------------------------------------------------- |
| Backend unit (pytest)                    | 31           | pass                                               |
| Backend integration (pytest, live infra) | 51           | pass                                               |
| Frontend (vitest)                        | 176          | pass                                               |
| E2E (playwright)                         | 31 specs × 2 | 62 pass locally; requires running stack + browsers |
| Evaluation                               | 0            | reserved directory                                 |

Lint/typecheck: ruff, ruff format, mypy --strict, eslint, tsc, prettier — all pass.

## Deployment state

Local only: stack verified 2026-09-20 with all five services healthy after
rebuilding the API image (migration `0002` applied by the entrypoint). Git:
Phase 6 is on `feat/phase-6-evidence-model`, tag `phase-6-complete`; `main` =
`origin/main` = `3e9f8f8` (Phase 5). Phase 6 is not pushed. No remote deployment
or production workflow.

## Verification limitations

`docs/design/DESIGN_SYSTEM.md`, `ROUTE_MAP.md`, `PAGE_SPECS.md` were re-transcribed
from a verbatim read after an accidental formatter pass; structurally verified
(line counts, sections, fences, spec fields) but not byte-verified because no
original copy exists locally. See MEMORY.md → Current Problems.

## Ingestion state

Documents discovered: 0 · downloaded: 0 · parsed: 0 · indexed: 0 ·
transcripts parsed: 0 · failed: 0. (Phase 4 ingests nothing by design.)
