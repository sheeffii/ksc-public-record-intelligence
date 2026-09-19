# KSC Public Record Intelligence — Project Memory

Live checkpoint. Answers "where exactly did we stop?". Keep concise; no logs.

## Current Status

Current branch: main
Current commit: none yet — all 173 files are staged for the initial commit, awaiting user review (`git commit -m "feat: phase 4 engineering foundation"`)
Current milestone: Phase 4 — Engineering Foundation — **COMPLETE**
Current active task: None. Phase 4 stopped deliberately; Phase 5 not started.
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
E2E: 25 Playwright specs written in tests/e2e; not executed in CI (needs browsers)
Evaluation: none (reserved)

Last full test result: 2026-09-19 — all passing (`make test`).

## Current Problems / Known Bugs

- None blocking. See "Technical debt" in docs/PROJECT_STATE.md.
- Playwright e2e has not been run in this session (infrastructure only).

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
4. Run Playwright once against `make up` (`pnpm exec playwright install chromium`)
   and decide whether to add it to CI.
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
make test-backend                       # 21 passed
pnpm --filter @ksc/web test             # 108 passed
pnpm --filter @ksc/web build            # standalone build ok
make lint && make typecheck             # clean
```
