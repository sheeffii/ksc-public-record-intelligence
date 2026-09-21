# AI methods

**Status: Phase 11 citation-first retrieval and answer validation is implemented;
Phase 12 reuses the same boundary for appeal research and red-team audit.**

The safe default is the offline deterministic extractive provider. Configurable
OpenAI-compatible and Anthropic-compatible adapters implement the same
structured provider contract, but no external provider is required for the
controlled-corpus benchmark and no secret is stored in a run.

## Position in the architecture

```text
primary sources → database → structured evidence → provenance/citations
                → structured + PostgreSQL FTS retrieval → provider
                → deterministic claim/citation validation → UI
```

Primary sources, the database, provenance, and citations remain authoritative.
Model memory is not evidence. AI never writes a source record, finding,
relationship, citation resolution, or human verification state.

Phase 12 does not introduce a parallel model path. A red-team review with
`origin = ai_assisted` must reference an existing audited `ai_run`, remains
separate from canonical findings/evidence, and cannot auto-promote its own
verification state. The controlled-corpus Phase 12 benchmark is human-reviewed;
the missing Trial Judgment, F03743, F03746 and earlier trial brief produce an
`insufficient_record` result rather than model-completed content.

## Retrieval before composition

1. Resolve explicitly requested filing references against the held case. A
   missing filing or Trial Judgment causes an immediate audited abstention.
2. Retrieve non-rejected structured findings and party/Court arguments plus
   chunks and open-session transcript segments from public or public-redacted,
   fully parsed held versions.
3. Persist the ranked retrieval set before generation. Each snapshot stores the
   exact anchor, coordinates, source/version identifiers, visibility, excerpt
   and SHA-256, retrieval method/value, category, and copied verification state
   and reviewer metadata.
4. Supply only those snapshots to the provider, with source text serialized as
   untrusted data.
5. Validate the provider response against the persisted source whitelist. The
   UI lists sources before answer blocks and can open the exact record target.

The Phase 11 baseline uses structured retrieval plus PostgreSQL full-text
search. No embedding is created. An embedding provider may be added later only
after a measured retrieval evaluation shows a need; it must not weaken the
same visibility, provenance, citation, or validation boundary.

## Answer and citation validation

Record categories remain separate and ordered:

`COURT FINDING` · `DOCUMENT / EXHIBIT` · `WITNESS TESTIMONY` · `SPO ARGUMENT` ·
`DEFENCE ARGUMENT` · `COURT RESPONSE` · `HUMAN NOTE` · `AI ANALYSIS`

The validator independently enforces:

- source IDs belong to the exact retrieval whitelist;
- every material block links to a source;
- record block kind matches the persisted source category;
- verbatim text exactly matches a retrieved excerpt after whitespace
  normalization;
- unreviewed paraphrases are rejected;
- record categories cannot contain AI analysis;
- AI analysis is limited to the versioned non-factual boundary sentence;
- prohibited guilt, credibility, judicial-quality, or outcome conclusions are
  rejected;
- provider abstentions and all validation failures withhold the entire answer.

Validation flags include `UNSUPPORTED_CLAIM`, `CITATION_NOT_FOUND`,
`CITATION_DOES_NOT_SUPPORT_CLAIM`, `QUOTE_NOT_VERIFIED`,
`DOCUMENT_NOT_FOUND`, `TRANSCRIPT_LOCATION_NOT_FOUND`, and
`EXHIBIT_NOT_FOUND`. No partial answer is rendered after a failure.

## Prompt and run governance

Prompts are immutable repository files in `packages/prompts/`. A changed prompt
gets a new integer version and file. Every run persists provider, model,
temperature/parameters, prompt row and system-prompt SHA-256, question, input
hash, ranked source snapshots, structured provider output, validation errors,
token counts when reported, timestamps, and claim-to-source links. Provider
credentials and raw secret-bearing requests are not persisted.

## Save behavior

Saving a valid answer creates a `research_notes` row with provenance
`ai_assisted` and a required `origin_ai_run_id`. It remains a research note and
never becomes evidence. A withheld or empty answer cannot be saved.

## Protected material and gaps

Only public/public-redacted held versions enter retrieval. Closed-session
segments are excluded. Protected witnesses remain code-only; internal witness
UUIDs are not supplied to providers. Redactions, unresolved citations, absent
records, and the known missing Trial Judgment, F03743, and F03746 are reported
as gaps rather than reconstructed.

## Evaluation

`tests/evaluation/phase11_questions.json` is the real-corpus evaluation set.
`ksc-ingest gate-ai` checks citation correctness, source-category correctness,
quote accuracy, exact-source navigation, unsupported-claim rendering, and
abstention quality. It also fingerprints source rows and human verification
before and after every run. The pinned result is documented in
`docs/ingestion/PHASE11_QUALITY_GATE.md`.
