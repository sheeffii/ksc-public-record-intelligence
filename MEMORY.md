# KSC Public Record Intelligence — Project Memory

Live checkpoint. Repository state wins over this note.

## Current status

- Current branch: `feat/phase-12-appeal-research-red-team` (created from `main`
  = `277686b`; Phase 12 not started).
- Current milestone: **Phase 11 complete (2026-09-21)**. Stop before Phase 12.
- Push state (2026-09-21): `main` fast-forwarded to `277686b` and pushed;
  `phase-11-complete` and `feat/phase-11-citation-first-ai-rag` pushed.
- Completion tag: `phase-11-complete` at the final Phase 11 closeout commit.
- Final Phase 11 implementation commit: `58ed7a8`; the subsequent roadmap
  closeout commit records the final audit and completion metadata.
- Previous checkpoints: `phase-10-complete` (implementation `c8eaa1e`).
- Migration head: `0007`.
- Phase 7 prerequisite: complete; tag `phase-7-complete` exists. The controlled
  bundle `data/captures/2026-09-20-corpus-01/` has 22 official public PDFs and
  the tracked reproducibility manifest is
  `docs/ingestion/manifests/phase7-controlled-corpus.json`.
- Phase 9 quality result: `docs/ingestion/PHASE9_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase9-controlled-corpus-quality.json`.
- Phase 10 quality result: `docs/ingestion/PHASE10_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase10-controlled-corpus-quality.json`.
- Phase 11 quality result: `docs/ingestion/PHASE11_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase11-controlled-corpus-quality.json`.
- Never push unless explicitly instructed.

## Phase 8 result

- All 22 held versions parsed with native text (`ksc-native-pdf/2`): 1,979
  pages, 1,233 numbered paragraphs, 1,592 structural chunks, 607 transcript
  segments; zero review-required versions and no OCR.
- Exact coordinate layers remain distinct: PDF index, printed/source page,
  paragraph, transcript page, and transcript line. Missing values stay NULL.
- Citation extraction stores exact raw text and source character/PDF coordinates.
  Persisted resolver counts: 14,205 total · 23 resolved · 0 ambiguous in the
  natural corpus · 14,105 unresolved · 77 invalid. Every non-resolved row is
  targetless and displays `UNRESOLVED`; ambiguity is integration-tested.
- PostgreSQL exact-ID + lexical FTS supports phrase/keyword search and document,
  language, party, source, and date filters. Results carry version and exact
  source-navigation coordinates. No embeddings or model calls exist.
- Search and Document Reader routes server-load the configured repository;
  real mode suppresses demo-only reader/search content.
- No additional material was fetched and the full KSC corpus was not ingested.

## Phase 9 result

- A deterministic database-only projection creates 13 public document nodes and
  22 `CITED_IN` edges from the controlled corpus's 23 resolved citations; one
  self-citation is omitted. No analytical or unsupported edge was created.
- Every edge retains subject/object, precise type, source category, verification,
  extraction origin, optional date, resolved target citation, and exact persisted
  citing-source coordinates/link.
- Evidence Path is bounded shortest-hop BFS over public, resolved, non-rejected,
  non-analytical edges. Every hop is independently cited and the required
  non-inference warning remains verbatim.
- Timeline has 19 source-record-backed real events: 11 document, 6 decision and
  2 testimony dates. All dates present in the controlled corpus are explicitly
  exact; missing categories remain absent.
- Network, Path and Timeline server-load real API data in API mode. Network has
  node search plus source, verification, true from/to date, entity and
  relationship filters, inspectors, expand/collapse, isolate, reset,
  exact-source links and a textual alternative.
- Measured graph scale is 13 nodes / 22 edges, so SVG remains appropriate.
  ADR-014 records this decision and the provenance/path rules.

## Phase 10 result

- Migration `0006` adds first-class findings, finding-evidence links, party and
  Court argument records, Court-response links, and exact provenance constraints.
- The held 22-record corpus has no Trial Judgment. The real quality benchmark is
  explicitly Court decision `KSC-BC-2020-06/F03752`; no party brief was
  substituted for a judgment and no additional record was fetched.
- One human-verified finding preserves the exact F03752 paragraphs 12–16. One
  exact, resolved, human-verified Court-cited link targets the held
  `F03667/COR/RED` version with exact source coordinates.
- One Defence and one SPO position are stored separately as exact Court
  summaries. Their unavailable underlying filings F03743 and F03746 remain
  explicitly missing. One Court-response passage has two separately verified
  response links.
- The real Finding Detail, matrix API, exact-source navigation and source audit
  expose the benchmark without unsupported evidence links, category conflation,
  AI-generated canonical findings, legal conclusions or scores.

## Phase 11 result

- Migration `0007` adds `ai_retrieval_sources` (ranked, hashed, exactly one
  source anchor, exact coordinates, verification/reviewer state) and
  `ai_output_sources`; extends `ai_runs` (question, prompt hash, parameters,
  structured output, validation errors, withheld/insufficient flags) and
  `ai_outputs` (content type, claim key); allows `ai_assisted` research notes
  with a mandatory `origin_ai_run_id`.
- `AiProvider` protocol; `DeterministicExtractiveProvider` is the default and
  quality-gate provider; OpenAI-/Anthropic-compatible adapters are opt-in via
  `AI_PROVIDER`. Prompts `packages/prompts/citation-first-answer-v{1,2}.txt`
  are immutable; v2 hash `eff0529c…` is persisted per run and a silent content
  change is refused.
- Retrieval = structured verified findings/arguments (score 100/90 + match)
  plus PostgreSQL FTS chunks and open-session transcript segments; public-only,
  max 8, deterministic ordering. Known-missing material (Trial Judgment,
  unheld filings) abstains before generation.
- Validation rejects non-whitelist sources, unmatched quotes, paraphrases,
  category conflation, evaluative language and any AI text other than the
  fixed boundary statement; any error withholds the whole answer. Live
  adversarial providers were all withheld with zero outputs.
- API `POST/GET /api/v1/ai/runs`, `GET /runs/{id}`, `POST /runs/{id}/notes`;
  `POST` mirrors the persisted audit record (score quantized to 8 dp). Real
  `/ai` and `/ai/{id}` show sources first, distinct record blocks, provenance
  boundary, AI block, citation status, run audit, exact-source links, no demo
  flag.
- Real gate: 4 runs · 1 grounded answer (8 sources, 13 links) · 3/3
  abstentions · 100% citation/category/quote/navigation · zero source or
  verification mutation.

## Verification

- Backend unit: 176 passed.
- Backend integration: 74 passed (250 backend total).
- Frontend: 197 passed; ESLint, TypeScript and Prettier pass.
- Final `make lint`, `make typecheck`, `make test`, production build, migration
  `0006 → 0007 → 0006 → 0007` round-trip, live-DB model drift check, rebuilt
  stack health, real API/UI smoke checks, the re-run real-corpus AI gate,
  standard Playwright (96 passed, 8 skipped) and the real-data Phase 11
  (4 passed) and Phase 10 (2 passed) runs all passed before the tag.
- Real-data Playwright needs a host web on port 3000 in API mode
  (`NEXT_PUBLIC_DATA_SOURCE=api … next dev -p 3000`, Docker web stopped)
  because `CORS_ORIGINS` allows only `http://localhost:3000`.
- The final roadmap closeout audit re-read the complete Phase 11 specification
  and verified every acceptance criterion against code, migration `0007`, tests,
  the live API/database/UI and the pinned real-corpus quality gate.

## Architecture / decisions

- ADR-001–015 remain in force; ADR-016 records persisted retrieval snapshots,
  the deterministic evidence boundary and fail-closed AI answers.
- Migration `0007_citation_first_ai_rag.py` adds the Phase 11 audit tables on
  top of `0006_judgment_findings_matrix.py`.
- AI layer: `apps/api/src/ksc_api/services/{ai_providers,ai_research,ai_validation}.py`,
  router `routers/ai.py`, gate `workers/ingestion/src/ksc_ingestion/ai_quality_gate.py`,
  UI `apps/web/src/components/screens/phase5/AiResearchReal.tsx`.
- Parser/resolver/pipeline:
  `workers/ingestion/src/ksc_ingestion/{pdf_parser,citation_resolution,parse_pipeline,evidence_pipeline}.py`.
- Real-corpus bytes stay git-ignored and hash-addressed in MinIO. The Phase 7
  capture manifest remains the reproducibility anchor.

## Known limitations

- OCR is not implemented because none of the controlled PDFs needs it. A future
  OCR fallback must label extraction method and confidence/review state.
- The small natural corpus contains no ambiguous citation; an overlapping-page
  fixture verifies the fail-closed state.
- Most valid citations target records outside the controlled corpus and remain
  explicitly unresolved; Phase 9 creates no edge from them.
- The controlled corpus has no approximate/range/month/year timeline date and no
  supported historical, filing-date, trial-judgment or later-appeal milestone;
  none was fabricated. Uncertainty rendering is component-tested.
- The controlled corpus has no public Trial Judgment and does not hold underlying
  public filings F03743 or F03746. Phase 10 therefore proves the matrix capability
  only against the narrow F03752 Court-decision benchmark, not a full merits matrix.
- Phase 11 evaluates one supported F03752 question and three abstentions; no
  embedding exists and the deterministic provider is the only verified
  completion path. External adapters are configuration with test doubles; no
  paid provider or model-quality claim is made. AI analysis is limited to a
  fixed non-factual boundary statement.

## Next

Phase 12 is **NEXT / PENDING**. Await explicit authorization, inspect repository
state, and read the complete Phase 12 roadmap. Do not begin Phase 12 from this
checkpoint.

## Non-negotiable rules

- Official public sources only; never bypass the court's access controls.
- Never fabricate identifiers, source coordinates, citations, quotes, or facts.
- Protected witnesses stay code-only. No person score/rank/weight/probability.
- Database + primary sources + persisted provenance are authoritative.
- Do not edit `docs/design/`; do not push without explicit instruction.
