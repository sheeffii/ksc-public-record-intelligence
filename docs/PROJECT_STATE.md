# Project state

Long-term implementation tracker. `MEMORY.md` is the live checkpoint; this file
tracks milestones, features, debt and status across sessions.

Last updated: 2026-09-19

## Milestones

| Phase | Scope                                                                                                     | Status                       |
| ----- | --------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 1–3   | Product definition, design system, 21-artboard UX package, flow audit                                     | ✅ Delivered (docs/design)   |
| **4** | **Engineering foundation** — monorepo, shell, tokens, i18n, theme infra, API, DB, Docker, tests, CI, docs | ✅ **Complete (2026-09-19)** |
| 5     | Implement approved UI with mock data (all 21 screens + 5 directories, DemoDataFlag everywhere)            | ⏳ Next                      |
| 6     | Controlled ingestion: one public document end to end, citation extraction + resolution index              | Planned                      |
| 7     | Evidence schema (witnesses, exhibits, findings, incidents, citations, relationships) + real data wiring   | Planned                      |
| 8     | Search (PostgreSQL FTS + pgvector), network, evidence paths                                               | Planned                      |
| 9     | AI research layer (retrieval-before-composition, withhold-on-unresolved), evaluation sets                 | Planned                      |
| 10    | Review workflows, public mode content authoring, access control, hardening                                | Planned                      |

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

- All 21 screens' real content (Phase 5).
- Five undesigned directory screens (Phase 5, from the DataTable pattern; design
  review before shipping).
- CitationPreview popover, RecordBlock/AiAnalysisBlock pair, ProtectionNotice,
  WitnessHeaderProtected, DirectionBadge+ScopeNote, ReferenceCountStrip — the
  remaining foundational components from HANDOFF.md §3 (Phase 5 start).
- ⌘K command palette (Modal primitive exists; palette not built).
- Any data fetching from web → api.
- Ingestion, parsing, resolution index, search, network, AI (later phases).

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

| Suite                                    | Count            | Last result                                      |
| ---------------------------------------- | ---------------- | ------------------------------------------------ |
| Backend unit (pytest)                    | 10               | pass                                             |
| Backend integration (pytest, live infra) | 11               | pass                                             |
| Frontend (vitest)                        | 108              | pass                                             |
| E2E (playwright)                         | 25 specs written | not run in CI; requires running stack + browsers |
| Evaluation                               | 0                | reserved directory                               |

Lint/typecheck: ruff, ruff format, mypy --strict, eslint, tsc, prettier — all pass.

## Deployment state

Local only: `docker compose up --build` verified 2026-09-19 with all five services
healthy. Git: commit `b99f514`, tag `phase-4-complete`; remote `origin` configured
(github.com/sheeffii/ksc-public-record-intelligence) but nothing pushed. No remote
deployment, no production workflow.

## Verification limitations

`docs/design/DESIGN_SYSTEM.md`, `ROUTE_MAP.md`, `PAGE_SPECS.md` were re-transcribed
from a verbatim read after an accidental formatter pass; structurally verified
(line counts, sections, fences, spec fields) but not byte-verified because no
original copy exists locally. See MEMORY.md → Current Problems.

## Ingestion state

Documents discovered: 0 · downloaded: 0 · parsed: 0 · indexed: 0 ·
transcripts parsed: 0 · failed: 0. (Phase 4 ingests nothing by design.)
