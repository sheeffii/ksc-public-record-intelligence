# KSC Public Record Intelligence — Project Memory

Live checkpoint. Answers “where exactly did we stop?”. Keep concise; no logs.

## Current Status

Current branch: `feat/phase-6-evidence-model` (cut from `main` at `3e9f8f8`)
Phase 5 commit: `ee8a0e7`
Tag: `phase-5-complete` → `ee8a0e7`
Phase 4 tag: `phase-4-complete` → `b99f514`
Remote: origin configured; `main` = `origin/main` = `3e9f8f8` (Phase 5 landed on
main by the user). Never push without explicit instruction.
Roadmap: installed under `docs/roadmap/` (master + 15 phase files + usage guide).
Current milestone: Phase 5 functional implementation **COMPLETE**; Phase 5
visual parity **requires Phase 5B remediation** (scheduled after Phase 6).
Next milestone: Phase 6 — Real Database / Evidence Model
(`docs/roadmap/PHASE_06_REAL_DATABASE_AND_EVIDENCE_MODEL.md`). **Not started;
awaiting explicit authorisation.**
Planned order: 6 → 5B → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14.
Phase 7 is the first controlled real-KSC ingestion milestone; Phase 14 is the
later external-media / public-statements feature (post-core).
Current active task: None. Roadmap installed; stop at the Phase 6 boundary.
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
- Mock interaction state is intentionally not persistent. Real API/database wiring
  is Phase 6.
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

Only after explicit authorisation, begin Phase 6 by reading
`docs/roadmap/00_MASTER_ROADMAP.md` and then the complete
`docs/roadmap/PHASE_06_REAL_DATABASE_AND_EVIDENCE_MODEL.md`: design and migrate
the real database/evidence model and add the API-backed repository boundary while
keeping `MockRepository` working. Phase 5B follows Phase 6; Phase 7 follows 5B.
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
make lint
make typecheck
make test
pnpm build
pnpm e2e
```
