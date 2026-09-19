# Phase 10 — Judgment, Findings & Evidence Matrix

**Status:** Pending.

## Goal

Turn the public judgment and related record into a structured finding-by-finding research system showing what the Court found, where it found it, which evidence it explicitly relied on, what the parties argued, and what other relevant public material exists.

This phase is the core legal-research layer before AI.

## Preconditions

- real documents/transcripts parsed;
- citations resolve;
- judgment paragraphs are addressable;
- real relationships/timeline work;
- public visibility rules are enforced.

## Judgment ingestion/structure

For the public judgment:

- preserve document/version;
- parse sections/headings;
- preserve paragraph numbers;
- create paragraph-level citation targets;
- map findings without replacing the original text with summaries.

## Finding model population

For each structured court finding, store:

- finding key;
- exact court finding text or precise referenced passage;
- judgment paragraph range;
- related charge/legal element/incident/person where public and appropriate;
- verification state.

Do not use AI-generated paraphrase as canonical finding text.

## Evidence relied upon

Create `FindingEvidenceLink` records for evidence the judgment explicitly relies on.

Distinguish:

- explicitly cited by Court;
- related but not explicitly cited;
- supporting;
- qualifying;
- contextual.

Do not silently label evidence “contradictory” as a Court relationship unless the Court/source supports that representation.

## Evidence Matrix

Build a matrix that can answer:

```text
Finding
→ judgment paragraphs
→ evidence explicitly cited
→ source type
→ witness/document/exhibit
→ exact citation
→ verification
→ relevant supporting/qualifying/contrary material
→ Defence argument
→ SPO argument
→ Court response
```

## Corroboration view

Allow researchers to inspect what types of material support a finding:

- witness testimony;
- documents;
- exhibits;
- video/media admitted into record if already modeled as court evidence;
- forensic/physical material if present in public record;
- other sources.

Use neutral wording such as:

> No additional corroborating source has been identified in the indexed public record.

Do not say “there was no evidence” merely because one category is absent.

Witness testimony is evidence; the platform should instead show how it was treated/corroborated/challenged in the public record.

## Party positions

Link:

- Defence submissions;
- SPO submissions;
- Court reasoning/response.

Keep each source category visually and structurally separate.

## Finding Detail real-data conversion

Replace mock Finding Detail with real structured data.

The UI should let users move from:

```text
Court Finding
  ↓
Exact judgment paragraph
  ↓
Evidence relied upon
  ↓
Open exact source
```

## Source Audit

Add a per-finding audit view:

- all citations resolve?;
- any source missing?;
- any ambiguous version?;
- any transcript coordinate missing?;
- any relationship unverified?;
- public/redacted version used?;
- source explicitly cited by Court vs merely related?

## Human review

Use verification states aggressively.

Do not auto-promote extracted finding/evidence links without review if extraction is uncertain.

## Tests / evaluation

Create hand-verified benchmark findings for the controlled corpus.

Verify:

- judgment paragraph mapping;
- evidence links;
- party-position links;
- exact-source opening;
- no source category conflation;
- no unsupported “Court relied on” labels;
- source-audit correctness.

## Acceptance criteria

- judgment is structurally navigable;
- findings are first-class real entities;
- explicit evidence relied upon is source-backed;
- party positions are linked separately;
- Finding Detail is real-data-backed;
- Evidence Matrix is queryable;
- source audit identifies unresolved gaps;
- tests/evaluation pass.

## Stop condition

Do not let AI generate canonical findings or legal conclusions. AI begins in Phase 11.

## Completion report

```text
PHASE 10 STATUS
JUDGMENT STRUCTURE
FINDINGS
EVIDENCE MATRIX
PARTY POSITIONS
CORROBORATION VIEW
SOURCE AUDIT
QUALITY REVIEW
TESTS
COMMITS
NEXT
MEMORY
```
