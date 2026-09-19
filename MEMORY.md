# KSC Public Record Intelligence — Project Memory

Live checkpoint. Answers “where exactly did we stop?”. Keep concise; no logs.

## Current Status

Current branch: `feat/phase-6-evidence-model` (cut from `main` at `3e9f8f8`)
Phase 6 tag: `phase-6-complete` → see Git (`git tag --list`)
Phase 5 tag: `phase-5-complete` → `ee8a0e7` · Phase 4 tag: `phase-4-complete` → `b99f514`
Remote: origin configured; `main` = `origin/main` = `3e9f8f8`. Phase 6 is local
only. Never push without explicit instruction.
Roadmap: `docs/roadmap/` (master + 15 phase files + usage guide).
Current milestone: Phase 6 — Real Database / Evidence Model **COMPLETE**
(2026-09-20). Phase 5 functional implementation complete; Phase 5 visual parity
requires Phase 5B.
Next milestone: Phase 5B — UI/UX Visual Parity Remediation
(`docs/roadmap/PHASE_05B_UI_UX_VISUAL_PARITY_REMEDIATION.md`). **Not started;
awaiting explicit authorisation.** Then Phase 7 (first controlled real-KSC
ingestion), 8 … 13, then 14 (post-core external media).
Current active task: None. Stop at the Phase 6 boundary.
Working tree at checkpoint: clean
Last updated: 2026-09-20

## What Works

- Phase 5 UI unchanged: all 23 routes render the approved mock-data screens;
  Cmd/Ctrl+K search, directories, dossiers, readers, evidence explorer, network,
  path, timeline, appeal/argument/red-team workspaces, AI research, public mode.
- **Database (Phase 6)**: Alembic `0002` on top of `0001`; 37 tables — source
  records, documents / versions / pages / sections / chunks, hearings /
  transcripts / segments / appearances, persons / aliases / witnesses /
  organizations / locations, exhibits, incidents, events, claims / mentions,
  findings / evidence links, arguments / responses, citations +
  record_identifiers, graph_nodes / relationships, research notes, prompt
  versions / ai_runs / ai_outputs, ingestion_jobs, audit_log. Provenance,
  visibility, verification (with reviewer) and versioning are columns with
  CHECKs; protected witnesses cannot carry identity; every relationship needs a
  citation; polymorphic references go through a node registry with real FKs.
- **Read API** `/api/v1/*` (case, documents + version pages/chunks, people,
  witnesses, exhibits, incidents, findings, claims, arguments, events,
  transcripts, citations + resolve, network, relationships, search) — paginated,
  case-scoped, fail-closed (public/public_redacted only; rejected facts and
  unresolved-citation dependants withheld; not-public documents stated, not 404).
- **Synthetic fixture** `KSC-DEMO-0000` (`make demo-fixture`) proves the five
  roadmap traversals; nothing in it is a real record.
- **Frontend boundary** `apps/web/src/data/`: async `ResearchRepository` with
  mock adapter (default) and `ApiRepository`; `NEXT_PUBLIC_DATA_SOURCE=api`
  switches. Screens still use the sync mock (Phase 5B moves them).
- Docker stack healthy with the rebuilt API image; real case serves 0 records.
  No court document was discovered, downloaded, parsed or indexed; no model
  provider is called.

## Tests

- Backend: 82 passed (31 unit + 51 integration: migrations, constraints,
  traversal, read API).
- Frontend: 176 passed (Vitest; 147 Phase 5 + 29 data-boundary).
- E2E: 62 passed (31 workflows × desktop + Pixel 7 Chromium).
- Lint: ruff, ruff format, ESLint, Prettier clean. Typecheck: mypy strict, tsc clean.
- `alembic check`: no drift. Production Next.js build passes.

Last full verification: 2026-09-20.

## Known Differences / Follow-up

- Phase 5 is functionally complete but visually simplified against
  `docs/design/Design.html` on several screens; the page-by-page gap list is in
  `docs/roadmap/PHASE_05B_UI_UX_VISUAL_PARITY_REMEDIATION.md`.
- Network currently uses a lightweight accessible SVG implementation over the typed
  mock graph. Reconsider Sigma.js/Graphology when real graph scale is known.
- The five directory routes reuse the approved DataTable language because they had
  no individual artboards.
- Mobile sidebars use native disclosure controls and the network inspector uses a
  fixed bottom sheet; these preserve the approved behavior with simpler Phase 5
  mechanics.
- Albanian legal terminology still requires verification against official KSC
  Albanian publications.
- Mock interaction state is intentionally not persistent. Screens are not yet
  wired to `getRepository()`; the API adapter is proven by contract tests only.
- `ApiRepository.getPath()` and `getAnswer()` return empty (no path engine before
  Phase 9, no AI run before Phase 11). Reader paragraphs come from chunk spans
  (`para_from`), not per-paragraph rows. A public witness without a calling
  party maps to code-only (shared `Witness` requires `calledBy`).
- `document_chunks` has no embedding column yet; search is ILIKE on identifiers
  and titles until Phase 8.
- Design-package provenance limitation remains: three Markdown files were
  structurally, but not byte-for-byte, restored during Phase 4. Do not rewrite
  `docs/design/`; see `docs/PROJECT_STATE.md`.

## Architecture State

- `apps/api/src/ksc_api/models/` — evidence model (see `docs/DATA_MODEL.md`);
  `db_enum()` persists enum values; `VerificationMixin` + reviewer CHECK.
- `apps/api/src/ksc_api/{schemas,repositories,routers/records.py}` — read API;
  `repositories/filters.py` holds the fail-closed rules.
- `apps/api/src/ksc_api/fixtures/demo.py` — synthetic case; `ksc-demo-fixture`.
- `apps/web/src/data/` — `ResearchRepository` contract, mock adapter,
  `api/{client,mappers,repository}.ts`, `getRepository()`.
- `apps/web/src/mock/` remains the Phase 5 boundary screens import.
- Documents discovered/downloaded/parsed/indexed and transcripts parsed: all 0.

## Important Decisions

- ADR-001…008 remain in force.
- ADR-009: async repository contract with mock + API adapters; mock default.
- ADR-010: node registry for polymorphic graph references; visibility
  vocabulary incl. `not_public`; human verification requires a reviewer; enum
  values persisted; in-place migration `0002`.

## Exact Next Task

Only after explicit authorisation, begin Phase 5B by reading
`docs/roadmap/00_MASTER_ROADMAP.md` and the complete
`docs/roadmap/PHASE_05B_UI_UX_VISUAL_PARITY_REMEDIATION.md`: page-by-page visual
parity against `docs/design/Design.html`, moving screens onto `getRepository()`
where convenient, without schema changes or real ingestion. Phase 7 follows 5B.
Do not ingest real KSC material before Phase 7.

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
