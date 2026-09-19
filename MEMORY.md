# KSC Public Record Intelligence — Project Memory

Live checkpoint. Answers “where exactly did we stop?”. Keep concise; no logs.

## Current Status

Current branch: `feat/phase-5-approved-ui`
Current commit: Phase 5 checkpoint (see `git rev-parse HEAD`)
Phase 4 tag: `phase-4-complete` → `b99f514`
Remote: origin configured, **never pushed**
Current milestone: Phase 5 — Approved UI implementation with mock data — **COMPLETE**
Next milestone: Phase 6 — Real database / evidence model (**not authorised**)
Current active task: None. Stop at the Phase 5 boundary.
Working tree at checkpoint: clean
Last updated: 2026-09-19

## What Works

- All 23 registered routes render purpose-built Phase 5 screens; no generic route
  placeholders remain.
- Home, grouped global search and Cmd/Ctrl+K, reusable directories, person and
  witness dossiers, statement comparison, document/judgment/transcript reading,
  evidence explorer, network, evidence path, timeline, incident/finding research,
  appeal research, argument/red-team workspaces, AI research and public mode work
  with typed generic demo data.
- Network supports search, zoom, drag-pan, node/edge selection, isolate,
  expand/collapse, reset, inspectors and a textual relationship alternative.
- Provenance is consistent: record material, citations and verification are
  visually distinct from AI analysis. Unresolved citations fail closed.
- Protected witness examples render by W-code only. No identity-bearing mock field
  or person score/rank/probability was added.
- English and Albanian string tables remain in parity; light reading/public and
  dark research surfaces remain semantic.
- Docker stack remains healthy. No court document was discovered, downloaded,
  parsed or indexed; no model provider is called.

## Tests

- Frontend: 147 passed (Vitest).
- Backend: 21 passed (10 unit + 11 integration).
- E2E: 62 passed (31 workflows × desktop Chromium + Pixel 7 Chromium).
- Lint: ruff, ruff format, ESLint and Prettier clean.
- Typecheck: mypy strict and TypeScript clean.
- Production Next.js build passes.

Last full verification: 2026-09-19.

## Known Differences / Follow-up

- The network uses a lightweight accessible SVG implementation over the typed mock
  graph rather than adding Sigma.js/Graphology for five demo nodes. The required
  interaction contract is implemented; a production graph engine remains a later
  data-scale decision.
- The five directory routes reuse the approved DataTable language because they had
  no individual artboards.
- Mobile sidebars use native disclosure controls and the network inspector uses a
  fixed bottom sheet; these preserve the approved behavior with simpler Phase 5
  mechanics.
- Albanian legal terminology is provisional pending review against official KSC
  publications.
- Mock state is local and intentionally not persisted. Real API/database wiring is
  Phase 6.
- Design-package provenance limitation remains: three Markdown files were
  structurally, but not byte-for-byte, restored during Phase 4. Do not rewrite
  `docs/design/`; see `docs/PROJECT_STATE.md`.

## Architecture State

- `apps/web/src/mock/` is the typed replaceable `MockRepository` boundary.
- Phase 5 provenance and screen components live under
  `apps/web/src/components/{provenance,screens/phase5}`.
- Backend remains Phase 4 foundation only: system endpoints, Case / Document /
  AuditLog models, migration `0001`, and no domain or AI endpoints.
- Documents discovered/downloaded/parsed/indexed and transcripts parsed: all 0.

## Important Decisions

- ADR-001…007 remain in force.
- ADR-008 records the replaceable Phase 5 repository contract.
- Approved design remains read-only. Interface copy stays in EN/SQ string tables;
  colors stay tokenized.

## Exact Next Task

Only after explicit authorisation, begin Phase 6: design and migrate the real
database/evidence model and replace mock repository contracts with API-backed
repositories. Do not ingest real KSC material before Phase 7.

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
make lint
make typecheck
make test
pnpm build
pnpm e2e
```
