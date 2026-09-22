# KSC Public Record Intelligence — Project Memory

Live checkpoint. Repository state wins over this note.

## Current status

- Current branch: `feat/phase-15-real-data-ui-completion-and-demo-removal`,
  created from updated `main` = `efc4ee3`. Phase 15 implementation commits are
  `5470511` and `0c2c40d`; closeout is complete.
- Current milestone: **Phase 15 COMPLETE (2026-09-22)**. Production routes
  default to real APIs or honest empty states, demo fallbacks are absent from
  normal routes, parsed Reader content is coordinate-filtered, and entity views
  remain honest and privacy-safe. Phase 16 is next/pending and has not started.
- Push state (2026-09-22): `main` fast-forwarded to `efc4ee3` and pushed with
  Phase 14 plus the Phase 15–17 roadmap files; annotated tag
  `phase-14-complete` and the Phase 14 feature branch were pushed.
- Latest completion tag: annotated `phase-15-complete`, local and not pushed.
- Phase 14 is on `main`; its feature branch is preserved on `origin`.
- Previous checkpoints: `phase-10-complete` (implementation `c8eaa1e`).
- Phase 14 implementation commit: `9ff9a2b`.
- Migration head and live database revision: `0010`.
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
- Phase 13 result: `docs/ingestion/PHASE13_QUALITY_GATE.md`,
  `docs/ingestion/phase13-quality-gate.json`, `docs/ingestion/PHASE13_OPERATIONS.md`,
  manifests `phase13-corpus-02.json` and combined `phase13-controlled-corpus.json`.
- Phase 14 result: `docs/ingestion/PHASE14_QUALITY_GATE.md`,
  `docs/ingestion/phase14-quality-gate.json`, operations guide and controlled
  manifest `docs/ingestion/manifests/phase14-external-media.json`.
- Second lawful capture `2026-09-21-corpus-02` lives at
  `~/Downloads/ksc-bc-2020-06-phase13-corpus-02` and imported bundle
  `data/captures/2026-09-21-corpus-02` (git-ignored).
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

## Phase 13 result

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
- Scale-out (2026-09-22): the attached-browser collector (ADR-019) captured
  `2026-09-21-corpus-02` — 40 public records, 39 accepted, 1 refused. Import,
  dry-run, ingestion, bundle gate (40/40 PASS), parse, re-resolution and the
  Phase 9 rebuild all ran locally; nothing was fetched by the pipeline itself.
- Real gate PASS: 62 source records · 56 documents · 61 fetched/parsed versions
  · 61 accepted (threshold 50) · 2,832 pages · 2,019 paragraphs · 1,363
  transcript segments · 15,730 citations (188 resolved · 3 ambiguous · 15,420
  unresolved · 119 invalid) · 61 objects · 36,443,971 bytes · 0 missing/
  hash-mismatched · 0 fetched non-public · 1 open quarantine · 1 parser review.
  Search 1.16 ms · exact lookup 0.75 ms · network 1.17 ms.
- Phase 9 projection rebuilt from the larger corpus: 48 nodes · 178 edges · 54
  events; no edge rests on a non-resolved citation. Phase 10/11/12 gates pass
  against the combined pinned manifest; AI audit history unchanged.
- `r31` (`F03734RED`) is refused and quarantined: its PDF header prints
  `KSC-BC-2020-06/F03734`, contradicting the published id. Nothing stored, no
  guess made. `r37` (`PL003-F00004`) resolved once the `PL` sub-file series was
  added alongside `IA` in the importer and resolver (unit-tested).
- Observability completed (ADR-020): `/metrics` Prometheus exposition,
  structured JSON access logs with request ids, `ops/alerts/ksc-api.rules.yml`.
- Backup/restore re-verified on the scaled corpus: isolated restore at `0009`
  with 61/61 objects and 36,443,971 bytes; isolated targets removed.

## Phase 14 result

- Migration `0010` adds a separate external provenance domain:
  `external_sources`, `media_items`, exact `media_statements`, the sole
  external-to-court bridge `court_media_links`, and neutral
  `media_statement_comparisons`.
- The explicit taxonomy is `EXTERNAL_ONLY`, `MENTIONED`, `TENDERED`, `ADMITTED`,
  `REJECTED`, `DISCUSSED`, `RELIED_UPON`, `UNKNOWN`. Any stronger-than-
  external/unknown status requires an exact citation and human verification in
  PostgreSQL; reads also require a resolved citation from the same case.
- Manual public-URL ingestion is deterministic and fail-closed: public HTTPS
  only, no URL credentials/local/non-global IP, distinct publication/capture
  timestamps, exact excerpt/hash validation, duplicate rejection, terms and
  coverage notes, and no automatic strong court-status assignment.
- The controlled real set contains 2 BIRN reports and 1 Human Rights Watch
  institutional release. All remain `EXTERNAL_ONLY`; no court relationship was
  invented. Three exact statements and one human-reviewed `NOT COMPARABLE`
  comparison are stored. The court-bridge network has zero edges.
- `/api/v1/media` exposes list/detail, comparison, timeline and verified bridge
  network reads. `/media` provides Court Record Only, External Public Sources,
  and Both — clearly separated modes, status filters, explicit badges, source
  links and visible limitations in EN/SQ. External material is excluded from
  the Phase 11 court-record RAG whitelist and creates no appeal/red-team claim.
- Real gate PASS: 2 sources · 3 items · 3 exact statements · 3 court-status
  rows · 1 comparison · 0 citation-backed/invalid links · 0 duplicates · 0
  manifest mismatches · 0 verification/access violations · 0 external court-
  record AI retrieval sources.

## Verification

- Phase 15 final evidence: lint/format, 283 backend tests, 236 frontend tests,
  strict typecheck and production build pass. Targeted frontend verification is
  28/28 and Phase 15 desktop/mobile Playwright is 38/38.
- The route gate confirms real API or honest empty-state behavior with no normal
  production demo dependency. Reader exact-source access, 48 readable Network
  nodes / 178 provenance-backed edges, Findings list/detail hierarchy, Search
  source separation and the approved homepage hierarchy pass verification.
- The current structured / verified projections contain 0 Person, Witness and
  Exhibit records. This does not establish that the underlying public court
  record contains none. Protected-witness safeguards remain intact.
- Phase 14 closeout ran `make lint`, `make typecheck`, `make test` (283 backend
  - 204 frontend), `make build`, migration `0009 → 0010 → 0009 → 0010`,
    `alembic check`, the real-data gate, rebuilt Docker API/web readiness and live
    media API checks.
- Phase 14 Playwright: 4/4 passed across desktop and Pixel 7, covering exact
  public-source navigation, source/status badges, limitations, neutral
  comparison and separate source-scope modes.
- The Phase 12 closeout additionally passed standard Playwright (96 passed, 14
  skipped) and real-data Phase 10–12 Playwright (12 passed across
  desktop/mobile) before its tag.
- Real-data Playwright needs a host web on port 3000 in API mode
  (`NEXT_PUBLIC_DATA_SOURCE=api … next dev -p 3000`, Docker web stopped)
  because `CORS_ORIGINS` allows only `http://localhost:3000`.
- The final roadmap closeout audit re-read the complete Phase 14 specification
  and verified every acceptance criterion against code, migration `0010`, tests,
  the live API/database/UI and the pinned real-public-source quality gate.

## Architecture / decisions

- ADR-001–020 remain in force; ADR-021 records the separate external provenance
  domain, exact-citation court bridge, dedicated media namespace, court-RAG
  exclusion and lawful manual-URL acquisition boundary.
- Migration `0010_external_media_public_statements.py` adds the Phase 14 tables
  on top of `0009_full_corpus_hardening.py`.
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
- Ambiguous citations now exist in the real corpus (3, from overlapping
  transcript-page references); they stay fail-closed and create no edge. An
  overlapping-page fixture also verifies the state.
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
- Phase 13's corpus is a lawful sample, not the complete public corpus: 37 of
  the 40 corpus-02 records are 2025–2026, there is still no public Trial
  Judgment, and the three ambiguous citations are real overlapping
  transcript-page references kept fail-closed. Performance figures are local
  single-node measurements at 61 versions.
- Phase 13 reprocessing reconciles derived rows by stable ID and never deletes:
  a parser-origin citation that a newer parser no longer extracts stays in
  place (still resolved deterministically) until explicit review.
- Phase 14 is a capability proof over 3 manually submitted public webpages,
  not a comprehensive media archive. It includes no Facebook, TikTok or X
  collection, no private/restricted/deleted source, and no external item with a
  verified court relationship. Future platform connectors or external-AI use
  require a new explicit milestone and terms/privacy review.

## Next

Phase 15 is complete. Phase 16 is next/pending; do not begin it without explicit
authorization. Existing non-blocking follow-ups remain: review quarantined
`r31`; the court corpus and external media set are samples; performance figures
are local only.

## Non-negotiable rules

- Official public sources only; never bypass the court's access controls.
- Never fabricate identifiers, source coordinates, citations, quotes, or facts.
- Protected witnesses stay code-only. No person score/rank/weight/probability.
- Database + primary sources + persisted provenance are authoritative.
- Do not edit `docs/design/`; do not push without explicit instruction.
