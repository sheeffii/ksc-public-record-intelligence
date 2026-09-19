# Phase 11 — Citation-First AI / RAG

**Status:** Pending.

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

- provider abstraction exists;
- audited AI runs are persisted;
- RAG uses verified public sources;
- citations are validated;
- unsupported claims are flagged/abstained;
- AI vs record is visually distinct;
- evaluation suite exists;
- AI never changes source records or human verification automatically.

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
