# KSC Public Record Intelligence — Project Memory

Live checkpoint. Answers "where exactly did we stop?". Keep concise; no logs.

## Current Status

Current branch: main
Current commit: HEAD of main = `docs: record phase 4 checkpoint` (run `git log --oneline -1`; the hash cannot be embedded in its own commit) · Phase 4 commit: b99f514 `feat: complete phase 4 engineering foundation`
Tag: phase-4-complete → b99f514
Remote: origin = https://github.com/sheeffii/ksc-public-record-intelligence.git (configured, **never pushed**)
Current milestone: Phase 4 — Engineering Foundation — **COMPLETE**
Next milestone: Phase 5 — Approved UI implementation with mock data (not started)
Current active task: None. Phase 4 closed deliberately; Phase 5 not started.
Working tree: clean after the checkpoint commit
Last updated: 2026-09-19

## What Works

Only what was verified on 2026-09-19:

- `docker compose up --build` → postgres, redis, minio (+bucket), api, web all healthy.
- `GET /health` → 200; `GET /version` → case_id KSC-BC-2020-06; `GET /ready` → 200 with
  database / pgvector (0.8.6) / redis / minio all ok.
- Alembic `0001` applied; tables cases, documents, audit_log; `vector` extension enabled.
- Seed idempotent: one `cases` row (KSC-BC-2020-06), one `audit_log` row, zero documents.
- Web: all 23 ROUTE_MAP routes return 200 with the shell; `/nope` → 404 page;
  cookie `ksc_locale=sq` renders Albanian chrome and `lang="sq"`; `/documents/:id`
  and `/public*` render `data-surface="light"`.
- `pnpm build` (Next 16 standalone) succeeds.
- Backend: 21 pytest pass (10 unit + 11 integration). Frontend: 108 vitest pass.
- Playwright E2E executed against the running Docker stack: 50 passed
  (25 desktop Chromium 1440px + 25 mobile Pixel 7). Mobile project switched from
  iPhone 12 (WebKit, not installed) to Pixel 7 (Chromium).
- ruff, ruff format, mypy --strict, eslint, tsc, prettier --check all clean.

## Completed Since Previous Checkpoint

Everything — this is the first checkpoint. Full list in docs/PROJECT_STATE.md.

## Frontend State

`apps/web`: shell + tokens + i18n + theme infra + provenance/primitive components +
placeholder pages for every approved route. No data fetching. No real screens.
ThemeToggle exists but is not mounted (ADR-006).

## Backend State

`apps/api`: system endpoints only. Models Case / Document / AuditLog. Seed script.
No domain endpoints, no ingestion, no AI.

## Infrastructure State

docker-compose with healthchecks (web/api checks use 127.0.0.1). MinIO images from
quay.io. Makefile covers dev/up/down/test/lint/typecheck/migrate/seed/reset-db/
logs/format/e2e/ci. CI workflow at .github/workflows/ci.yml (not yet run remotely —
never pushed).

## Database / Migration State

Head: `0001` (initial foundation). pgvector enabled. `ksc_test` database is created
by integration tests on the same Postgres.

## Ingestion State

Documents discovered: 0
Documents downloaded: 0
Documents parsed: 0
Documents indexed: 0
Transcripts parsed: 0
Failed documents: 0

## Tests

Frontend: 108 passed (vitest) — `pnpm --filter @ksc/web test`
Backend: 21 passed (pytest: 10 unit, 11 integration) — `make test-backend`
Integration: included above; needs `make infra`
E2E: 50 passed (25 specs × desktop + mobile, Chromium) — `pnpm e2e` against `make up`; not in CI
Evaluation: none (reserved)

Last full test result: 2026-09-19 (checkpoint) — lint, typecheck, 21 backend, 108 frontend, 50 e2e all passing.

## Current Problems / Known Bugs

- None blocking. See "Technical debt" in docs/PROJECT_STATE.md.
- **Design-file verification limitation.** `docs/design/DESIGN_SYSTEM.md`,
  `ROUTE_MAP.md` and `PAGE_SPECS.md` were re-transcribed from a verbatim in-session
  read after an accidental Prettier pass; no original copy exists locally, so a
  byte-for-byte check was impossible. Structural inspection passed (line counts
  238/239/602 equal the originals; all sections present; code fences balanced;
  all 11 spec fields on each of the 16 authoritative screens; no duplicated
  lines; trailing newlines intact; 26 token rows). `COMPONENTS.md`, `HANDOFF.md`,
  `UX_FLOWS.md`, `DESIGN_DECISIONS.md` and `Design.html` are byte-exact. If the
  user still holds the original download, a `diff`/`sha256` against those three
  files would close this. Do NOT rewrite them again.
- `git diff --cached --check` reports trailing whitespace at `Design.html:26` —
  this is the handed-off file as delivered; left untouched on purpose.

## Important Recent Decisions

- ADR-001 citation-first hierarchy; ADR-002 Postgres+pgvector, no OpenSearch;
  ADR-003 controlled ingestion first (nothing ingested in Phase 4);
  ADR-004 docs/design is read-only source of truth (excluded from Prettier);
  ADR-005 citation resolution index computed at ingest (schema planned in
  docs/DATA_MODEL.md, resolver not built); ADR-006 theme is surface-semantic,
  toggle not mounted; ADR-007 language is a cookie, not a route prefix.
- Incident during Phase 4: `pnpm format` reformatted docs/design/*.md once. All
  seven files were restored (four byte-exact from saved output, three re-transcribed
  from the verbatim read; line counts match originals). `docs/design/` is now in
  `.prettierignore`.

## Files Changed Recently

Entire repository created in Phase 4. Key entry points:
`apps/web/src/app/layout.tsx`, `apps/web/src/components/shell/AppShell.tsx`,
`apps/web/src/styles/globals.css`, `apps/web/src/lib/routes.ts`,
`apps/web/src/i18n/messages/{en,sq}.json`, `apps/api/src/ksc_api/main.py`,
`apps/api/alembic/versions/0001_initial_foundation.py`, `docker-compose.yml`,
`Makefile`, `docs/*.md`, `CLAUDE.md`.

## Current Working Context

Phase 4 finished and verified end to end. The next phase (5) implements the
approved UI with mock data. Nothing from Phase 5 has been started: no screen beyond
the placeholder and the foundation homepage exists, no mock data files exist.

## Next Actions

1. **Start Phase 5 only when instructed.** First task: build the remaining
   foundational components from HANDOFF.md §3 in `apps/web/src/components/provenance/`
   — `RecordBlock` + `AiAnalysisBlock` (matched pair, four-signal boundary),
   `CitationPreview` (popover before navigation), `ProtectionNotice`,
   `WitnessHeaderProtected` (no identity markup), `DirectionBadge` + `ScopeNote`,
   `ReferenceCountStrip` (disclaimer inside the component) — each with tests
   encoding its rule, strings added to both message tables.
2. Create `apps/web/src/mock/` with clearly-labelled mock data typed by
   `@ksc/shared`; every screen showing a figure keeps `DemoDataFlag`.
3. Implement screens in HANDOFF.md §11 order: Document Reader (04) → Global Search
   (06) + ⌘K (06b) → Finding Detail (05) → dossiers (07, 08) → Evidence Explorer
   (10) + the five directories → Network (03) + Evidence Path (20) → 11, 12, 09 →
   13, 14, 15 → Public mode (16). Mobile throughout.
4. Decide whether to add Playwright (`pnpm e2e`, already passing locally) to CI.
5. Have Albanian legal terminology reviewed against official KSC publications.

## Do Not Forget

- Do not bulk ingest. Do not scrape. Do not download court documents.
- Do not add AI yet. No provider key is required or read.
- Database and primary sources are authoritative; AI is analysis only.
- Preserve protected witness identities — W-code only, fail closed.
- Approved frontend design lives under docs/design — read-only, never formatted.
- Citation resolution should eventually occur during ingestion and be persisted;
  `UNRESOLVED` is never replaced.
- No score/rank/weight field of any person, anywhere (a unit test scans columns).
- Interface strings only from the string tables; identifiers never translated.
- Never `git push` unless explicitly told; no AI attribution in commits.

## Blockers

None.

## Useful Commands

```
make help            list targets
make infra           postgres+redis+minio in Docker
make dev             api (reload) + web (next dev) on the host
make up / down       full stack in Docker
make test            backend (unit+integration) + frontend
make lint / typecheck / format
make migrate / seed / reset-db
pnpm --filter @ksc/web test -- --watch
docker compose ps    service health
```

## Last Successful Commands

```
docker compose up --build -d            # all five services healthy
make lint && make typecheck             # clean
make test-backend                       # 21 passed
pnpm --filter @ksc/web test             # 108 passed
pnpm e2e                                # 50 passed (stack running)
git commit / git tag phase-4-complete   # b99f514
```
