# Phase 11 — Citation-First AI / RAG

**Status:** Complete.

**Completed:** 2026-09-21.

**Completion commit:** `58ed7a8` (final verified implementation/data baseline;
the subsequent roadmap closeout commit records completion metadata).

**Completion tag:** `phase-11-complete`.

## Goal

Add AI research capabilities **on top of** the verified public-record retrieval system without allowing AI to become the source of truth.

## Preconditions

Do not begin until:

- parsing/citation resolution is reliable;
- search works;
- judgment/findings are structured;
- sources can open at exact coordinates;
- AI audit tables exist.

## Provider abstraction

Support provider-neutral interfaces, e.g.:

- OpenAI-compatible;
- Anthropic-compatible.

Do not couple domain logic directly to one provider.

## Prompt/version governance

Production prompts should live in versioned repository files, e.g. `packages/prompts/`.

Record for each run:

- provider;
- model;
- temperature/parameters;
- prompt version;
- system prompt hash;
- query/input;
- retrieved source IDs/chunks;
- retrieval scores;
- structured output;
- token counts;
- cost estimate where available;
- timestamp.

## Retrieval pipeline

Recommended shape:

```text
User question
   ↓
Query analysis
   ↓
Hybrid retrieval
   ↓
Visibility filter
   ↓
Source/citation validation
   ↓
Context assembly
   ↓
LLM
   ↓
Structured answer
   ↓
Citation validator
   ↓
Render answer + sources
```

## Evidence category separation

AI response schema should distinguish:

- Court Finding;
- Witness Testimony;
- SPO Position;
- Defence Position;
- Document/Exhibit;
- AI Analysis.

Do not blend these into one narrative without labels.

## Citation requirements

Material claims should carry citation references where the source supports them.

If source support cannot be found:

- omit claim;
- label unresolved;
- or explicitly state that the indexed public record did not provide a verified citation.

Never fabricate a citation.

## Quote handling

Separate:

- verbatim quote;
- source paraphrase;
- AI analysis.

Verify quoted text against parsed source before rendering it as a quote when practical.

## Hallucination defenses

Implement:

- source whitelist from retrieval;
- citation target validation;
- structured output schemas;
- required claim→citation linkage where appropriate;
- unsupported-claim detector;
- quote verification;
- unresolved-citation flagging;
- refusal/abstention when evidence is insufficient.

## Error flags

Support flags such as:

- `UNSUPPORTED_CLAIM`;
- `CITATION_NOT_FOUND`;
- `CITATION_DOES_NOT_SUPPORT_CLAIM`;
- `QUOTE_NOT_VERIFIED`;
- `DOCUMENT_NOT_FOUND`;
- `TRANSCRIPT_LOCATION_NOT_FOUND`;
- `EXHIBIT_NOT_FOUND`.

## AI Research UI

Connect the Phase 5/5B workspace to real AI runs.

Show:

- query;
- structured answer;
- source categories;
- sources used;
- retrieved documents;
- citation status;
- verification status;
- AI-specific visual boundary;
- “Open Source” actions.

## Save/export behavior

Research note created from AI output should remain a research note, not evidence.

If users save AI analysis into an argument workspace, preserve its AI origin.

## Evaluation

Create an evaluation set using known public-record questions.

Score dimensions such as:

- citation correctness;
- source-category correctness;
- unsupported-claim rate;
- exact-source navigation;
- quote accuracy;
- completeness;
- abstention quality.

Do not evaluate based on whether AI reaches a preferred legal conclusion.

## Security / prompt injection

Treat ingested documents as untrusted content.

Defend against instructions embedded inside source text.

The model should not follow document text as system instructions.

## Acceptance criteria

- provider abstraction exists; ✅ `AiProvider` protocol with deterministic,
  OpenAI-compatible and Anthropic-compatible implementations
  (`services/ai_providers.py`); selection is configuration only.
- audited AI runs are persisted; ✅ `ai_runs` records provider, model,
  parameters, prompt version + hash, question, input hash, ranked
  `ai_retrieval_sources` with scores/anchors, structured output, validation
  errors, tokens and timestamps (migration `0007`).
- RAG uses verified public sources; ✅ retrieval is restricted to public /
  public-redacted held versions, non-rejected structured records and FTS
  chunks; every snapshot carries the version hash and verification state.
- citations are validated; ✅ whitelist, category, exact-quote and
  paraphrase checks (`services/ai_validation.py`); a fabricated ID, unmatched
  quote or conflated category withholds the whole answer.
- unsupported claims are flagged/abstained; ✅ `UNSUPPORTED_CLAIM`,
  `CITATION_NOT_FOUND`, `CITATION_DOES_NOT_SUPPORT_CLAIM`,
  `QUOTE_NOT_VERIFIED`, `DOCUMENT_NOT_FOUND` are persisted; missing
  Trial Judgment / filings abstain before generation.
- AI vs record is visually distinct; ✅ real `/ai` renders record blocks,
  a provenance boundary, then the AI block; no demo flag in real mode
  (component + Playwright tested).
- evaluation suite exists; ✅ `tests/evaluation/phase11_questions.json`,
  `ksc-ingest gate-ai`, report `docs/ingestion/PHASE11_QUALITY_GATE.md`.
- AI never changes source records or human verification automatically. ✅
  gate fingerprints and live before/after checks show zero mutation; saved
  output is an `ai_assisted` research note, never evidence.

## Stop condition

Do not yet build a full appellate-argument generator or outcome predictor.

## Completion report

```text
PHASE 11 STATUS
PROVIDERS
RETRIEVAL
PROMPTS
CITATION VALIDATION
AI RESEARCH UI
AUDIT TRAIL
EVALUATION
SAFETY
TESTS
COMMITS
NEXT
MEMORY
```

## Completion Record

- Closeout audit: **PASS**, 2026-09-21. Every requirement and acceptance
  criterion above was re-read and checked against migration `0007`, the
  committed implementation, automated tests, the rebuilt live stack
  (PostgreSQL/pgvector, Redis, MinIO, API, web all healthy), the real-case
  database, API and UI, and the pinned real-corpus quality report.
- Corpus scope: the existing 22-record Phase 7 corpus was used unchanged. No
  record was fetched; no embedding was created. The supported benchmark is the
  Phase 10 Court decision `KSC-BC-2020-06/F03752`; the Trial Judgment and the
  underlying filings `F03743` / `F03746` remain explicitly absent.
- Providers/prompts: `AiProvider` protocol; deterministic extractive provider
  is the verified default; OpenAI-/Anthropic-compatible HTTP adapters are
  opt-in configuration. Prompts `citation-first-answer` v1/v2 live in
  `packages/prompts/`; v2 hash
  `eff0529c200169302b0587c9116512c01c113a485c4eca7d1eb93f6f006b1af5` is
  persisted per run and a content change without a version bump is refused.
- Retrieval: structured verified findings/arguments plus PostgreSQL FTS chunks
  and open-session transcript segments, public-only, ranked and persisted with
  exact page/PDF/paragraph/line anchors. Repeated runs of the same question
  return identical ranked snapshots, excerpt hashes and blocks.
- Validation/safety: whitelist, category, exact-quote, paraphrase, evaluative
  language and fixed AI-boundary checks. Live adversarial providers
  (fabricated ID, invented Court finding, category conflation, injected
  exhibit, broken output) were all withheld with zero outputs. Source text is
  passed as untrusted data; embedded instructions are not followed.
- API/UI: `POST/GET /api/v1/ai/runs`, `GET /api/v1/ai/runs/{id}`,
  `POST /api/v1/ai/runs/{id}/notes`. `POST` mirrors the persisted audit
  record exactly. Real `/ai` and `/ai/{id}` show retrieved sources first,
  distinct Court finding / SPO / Defence / Court response / exhibit blocks,
  a provenance boundary, the AI block, citation status, run audit,
  exact-source links and known gaps; withheld runs render no block.
- Quality gate: 4 audited runs; 1 grounded answer with 8 held-version
  sources and 13 validated claim-source links; 3/3 correct abstentions;
  100% citation, category, quote and navigation rates; source records and
  human verification unchanged. Re-run on the rebuilt stack with an
  identical substantive result.
- Tests/gates: `make lint`, `make typecheck`, `make test`, `make build`,
  migration `0006 → 0007 → 0006 → 0007`, live model-drift check, standard
  Playwright and the real-data Playwright all passed. Counts: 250 backend
  tests; 197 frontend tests; standard Playwright 96 passed / 8 skipped
  (real-data-gated); real-data Phase 11 Playwright 4 passed and Phase 10
  Playwright 2 passed across desktop and mobile.
- Evidence: `docs/ingestion/PHASE11_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase11-controlled-corpus-quality.json`.
- Scope stop: no appellate-argument generator, outcome predictor, score,
  embedding, or Phase 12 work was introduced.
