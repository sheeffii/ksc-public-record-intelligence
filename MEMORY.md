# KSC Public Record Intelligence — Project Memory

Live checkpoint. Repository state wins over this note.

## Current status

- Current branch: `feat/phase-13-full-public-corpus-ingestion-hardening`; its
  preserved branch-start checkpoint is `2adb1f1` from `main` = `bac0b0f`.
- Current milestone: **Phase 13 IN PROGRESS (2026-09-21)**. Architecture,
  operations and the real gate are implemented; completion is blocked at 22/50
  lawfully available real records.
- Push state (2026-09-21): `main` fast-forwarded to `bac0b0f` and pushed;
  annotated tag `phase-12-complete` pushed. The Phase 13 branch is local.
- Latest completion tag: `phase-12-complete` at `bac0b0f`. There is deliberately
  no `phase-13-complete` tag.
- Final Phase 12 implementation commit: `7a9779b`; the subsequent roadmap
  closeout commit records the final audit and completion metadata.
- Phase 12 is on `main`; its feature branch was not pushed separately.
- Previous checkpoints: `phase-10-complete` (implementation `c8eaa1e`).
- Migration head: `0009`.
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
- Phase 12 quality result: `docs/ingestion/PHASE12_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase12-controlled-corpus-quality.json`.
- Phase 13 in-progress result: `docs/ingestion/phase13-quality-gate.json` and
  `docs/ingestion/PHASE13_OPERATIONS.md`.
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

## Phase 12 result

- Migration `0008` adds source-backed appeal issues, exact issue-source roles,
  explicit missing material, two-source statement comparisons, red-team
  reviews/findings and optional appeal-issue linkage on research notes.
- One real `NEEDS_MORE_EVIDENCE` potential issue over the F03752 paragraphs
  12–16 finding has 5 exact human-verified source links: Court reasoning,
  Defence/SPO positions (kept as Court summaries), the expressly cited
  F03667/COR/RED source, and Court response. Court treatment is `addressed`,
  not an assessment that the reasoning was correct.
- The issue records 4 missing sources: F03743, F03746, the pre-correction SPO
  Final Trial Brief, and the public Trial Judgment. Its review result is
  `insufficient_record`; no legal error, valid ground or outcome is asserted.
- The Red Team has Defence analyst, SPO red-team and neutral-reviewer stages,
  with 4 human-verified findings. Supporting/contrary/qualifying source roles
  exist, but the real benchmark creates none because the held record does not
  independently establish them.
- One human-verified comparison uses exact F03752 paragraph 12 and
  F03667/COR/RED page 160 citations. It is `not_comparable` because the earlier
  brief is absent and makes no credibility inference.
- Real Appeal Research, Argument Lab and Statement Comparison routes expose
  exact navigation, missing material, Court treatment, human review and source
  audit with no demo flag. Phase 11 remains the only AI architecture;
  AI-assisted reviews require an audited run and cannot auto-verify evidence.
- Real gate: 1 issue · 5 source links · 1 comparison · 1 review · 4 red-team
  findings · 7/7 citations resolved/navigable · 10 human-verified relationships
  · 1 abstention · authoritative finding/evidence state unchanged.

## Phase 13 in-progress result

- Migration `0009` adds immutable source snapshots, lease-based artifact
  acquisition, quarantine, and processing-run history without changing
  authoritative artifact/version identity.
- `ksc-ingest inventory`, `queue-artifacts`, and `browser-plan` separate official
  inventory from local bytes. Only explicitly public versions queue. Leases use
  bounded `SKIP LOCKED` claims, expiry and capped retry; access control is
  terminal and routed to the existing lawful operator-capture path.
- `parse --force` and `reresolve` rebuild derived parser/citation state from
  immutable held bytes and record runs. Open-quarantine versions are excluded
  from both selections (`select_processable_versions`); a version quarantined
  after parsing is flagged by the gate as `quarantined_parsed_versions`.
- Status/API metrics now include verified bytes, metadata snapshots, duplicates,
  parser review, queue states, quarantine and processing runs. API responses add
  secure headers and a 10 MiB declared-body limit; Dependabot covers
  `apps/api`, `workers/ingestion`, pnpm and Actions.
- PostgreSQL/MinIO backup writes per-file SHA-256 evidence and no secret values;
  guarded restore was tested in an isolated database/bucket. It restored
  migration `0009`, 22 objects and 24,429,094 object bytes, then the isolated
  targets were removed.
- Real gate: 22 source records · 19 documents · 22 fetched/parsed versions ·
  1,979 pages · 1,233 paragraphs · 607 transcript segments · 14,212 citations
  (30 resolved · 0 ambiguous · 14,105 unresolved · 77 invalid) · 22 verified
  objects · 24,429,094 bytes · 0 missing/hash-mismatched objects · 0 fetched
  non-public versions · 0 open quarantine. Search, exact lookup and network
  queries were all under 3 ms locally.
- A fresh identified probe of `repository.scp-ks.org/robots.txt` returned HTTP
  403 with `cf-mitigated: challenge`; failure job
  `4134154a-5026-4ebc-ba04-75a20bcc42ca` records it. No bypass was attempted.
- Architecture/integrity/performance gates pass, but the genuine real-scale gate
  is 22/50 and fails. Phase 13 remains in progress; no completion tag.
- Resumed closeout audit (2026-09-21): forced reparse + reresolve left every
  downstream Phase 8–12 row byte-identical (fingerprint diff; only
  `processing_runs` 3 → 5); gate re-run identical; second isolated
  backup/restore verified 22/22 objects by hash; fresh identified probe still
  `cf-mitigated: challenge`. Per-criterion audit is in the Phase 13 roadmap
  file. No larger lawful batch exists locally (`data/captures/` holds only the
  22-PDF bundle; no inventory manifest).

## Verification

- Backend unit: 180 passed.
- Backend integration: 81 passed (261 backend total).
- Frontend: 199 passed; ESLint, TypeScript and Prettier pass.
- Phase 13 checkpoint reran `make lint`, `make typecheck`, `make test` (261
  backend + 199 frontend), production build, migration round-trip/model drift,
  checksum backup/isolated restore, real-corpus force reparse/re-resolution and
  gate, rebuilt stack health, API security-header/status/413 smoke and web
  health.
- The Phase 12 closeout additionally passed standard Playwright (96 passed, 14
  skipped) and real-data Phase 10–12 Playwright (12 passed across
  desktop/mobile) before its tag.
- Real-data Playwright needs a host web on port 3000 in API mode
  (`NEXT_PUBLIC_DATA_SOURCE=api … next dev -p 3000`, Docker web stopped)
  because `CORS_ORIGINS` allows only `http://localhost:3000`.
- The final roadmap closeout audit re-read the complete Phase 12 specification
  and verified every acceptance criterion against code, migration `0008`, tests,
  the live API/database/UI and the pinned real-corpus quality gate.

## Architecture / decisions

- ADR-001–016 remain in force; ADR-017 records human-verified potential issues,
  exact source roles, neutral Court treatment/comparison semantics and the
  shared Phase 11 AI boundary.
- Migration `0008_appeal_research_red_team.py` adds the Phase 12 tables on top
  of `0007_citation_first_ai_rag.py`.
- AI layer: `apps/api/src/ksc_api/services/{ai_providers,ai_research,ai_validation}.py`,
  router `routers/ai.py`, gate `workers/ingestion/src/ksc_ingestion/ai_quality_gate.py`,
  UI `apps/web/src/components/screens/phase5/AiResearchReal.tsx`.
- Appeal layer: `apps/api/src/ksc_api/{models/appeal.py,services/appeal_research.py}`,
  gate `workers/ingestion/src/ksc_ingestion/appeal_quality_gate.py`, UI
  `apps/web/src/components/screens/phase5/AppealResearchReal.tsx`.
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
- Phase 12 proves a narrow procedural review workflow, not a full merits or
  sentencing analysis. The public Trial Judgment, F03743, F03746 and the
  pre-correction brief are absent; the comparison therefore remains
  `not_comparable` and the issue remains `NEEDS_MORE_EVIDENCE`.
- Phase 13 reprocessing reconciles derived rows by stable ID and never deletes:
  a parser-origin citation that a newer parser no longer extracts stays in
  place (still resolved deterministically) until explicit review. Observability
  is partial: plain-text logs, no metrics endpoint, no alerting integration.
  Scale claims (performance, lineage) are proven at 22 records only.

## Next

Phase 13 is **IN PROGRESS / BLOCKED ON LAWFUL REAL SCALE**. Resume only when an
authorized official inventory/capture can raise the real public corpus from 22
to at least 50 records. Run the inventory/capture pipeline in bounded batches,
repeat the real gate and full quality gates, then complete/tag only if every
criterion passes. Do not bypass Cloudflare and do not begin Phase 14.

## Non-negotiable rules

- Official public sources only; never bypass the court's access controls.
- Never fabricate identifiers, source coordinates, citations, quotes, or facts.
- Protected witnesses stay code-only. No person score/rank/weight/probability.
- Database + primary sources + persisted provenance are authoritative.
- Do not edit `docs/design/`; do not push without explicit instruction.
