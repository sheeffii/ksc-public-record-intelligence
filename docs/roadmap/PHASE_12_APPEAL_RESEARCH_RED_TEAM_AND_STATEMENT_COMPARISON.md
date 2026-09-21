# Phase 12 — Appeal Research, Red Team & Statement Comparison

**Status:** Complete.

**Completed:** 2026-09-21.

**Completion commit:** `7a9779b` (final verified implementation/data baseline;
the subsequent roadmap closeout commit records completion metadata).

**Completion tag:** `phase-12-complete`.

## Goal

Build a neutral, source-backed appellate research workspace that helps lawyers/researchers inspect potential issues, compare the record, test arguments, and find counterarguments **without predicting the appeal outcome or telling users what political/legal choice to make**.

## Core principle

The application may identify:

```text
Potential Issue for Review
```

It must not output:

- appeal success probability;
- “winning ground” ranking;
- predicted appellate result;
- guilt/innocence score;
- credibility score.

## Preconditions

- judgment/findings are structured;
- evidence matrix works;
- source citations resolve;
- RAG is audited;
- statement/transcript sources are available.

## Appeal issue model

Support categories such as:

- ERROR_OF_LAW;
- ERROR_OF_FACT;
- SENTENCING;
- PROCEDURAL_FAIRNESS;
- EVIDENCE_ASSESSMENT;
- REASONING;
- DISCLOSURE;
- LEGAL_STANDARD;
- CAUSATION;
- MODE_OF_LIABILITY;
- OTHER.

These categories organize research; they do not establish that an error occurred.

## Per-issue research structure

For each potential issue:

```text
Challenged finding / decision
  ↓
Exact judgment paragraphs
  ↓
Applicable legal standard / public authority where available
  ↓
Evidence relied upon
  ↓
Defence position
  ↓
SPO position
  ↓
Court response
  ↓
Relevant contrary/qualifying material
  ↓
Potential issue for review
  ↓
Counterargument
  ↓
Missing research / unresolved citations
  ↓
Human review
```

## Argument Lab

Provide tools such as:

- Research Support;
- Find Contrary Evidence;
- Check Citations;
- Find Defence Position;
- Find SPO Response;
- Find Court Response;
- Save research note;
- Draft source-backed argument outline.

AI-generated language must remain clearly labeled.

## Red Team workflow

### Agent A — Defence Analyst

Task:

- formulate the strongest source-backed version of a potential issue;
- identify supporting public-record citations;
- expose missing support rather than invent it.

### Agent B — SPO Red Team

Task:

- identify counterarguments;
- locate record material supporting the challenged reasoning;
- challenge unsupported assertions;
- identify waiver/procedural/standard-of-review issues where source-backed.

### Agent C — Neutral Reviewer

Task:

- list unsupported assertions;
- missing citations;
- ignored evidence;
- unanswered counterarguments;
- factual disputes;
- legal questions requiring human research;
- unresolved source issues.

Do not declare a winner.

## Statement Comparison

Compare source-backed statements from the same witness/person where lawfully public, e.g.:

- prior public statement;
- direct examination;
- cross-examination;
- redirect;
- another public record statement.

Allowed classifications:

- Possible Contradiction;
- Qualification;
- Timeline Difference;
- Consistent;
- Not Comparable.

Each comparison item must show:

- Statement A + citation;
- Statement B + citation;
- neutral explanation;
- verification state;
- human-review status.

Never automatically label a witness liar/dishonest.

## Counter-evidence discovery

For a finding or argument, search the indexed public record for:

- evidence relied upon;
- related evidence not explicitly cited;
- qualifying material;
- contrary statements;
- alternative timeline evidence;
- Defence/SPO treatment;
- Court response.

Use wording like:

> No additional corroborating source identified in the indexed public record.

Do not equate lack of one evidence category with “no evidence.”

## Sentencing research

Where the public judgment provides sentencing reasoning, allow structured inspection of:

- sentence imposed;
- exact judgment paragraphs;
- offenses/findings linked to sentencing;
- aggravating/mitigating factors stated by Court;
- party submissions;
- sentencing-law issues;
- potential issues for review.

Do not predict whether a sentence will be reduced.

## Citation audit

Before an argument can be treated as “ready for human review,” verify:

- all citations resolve;
- quotes match sources;
- source type is correct;
- Court finding is not confused with party argument;
- AI statements are labeled;
- unresolved items are explicit.

## Human workflow

Everything remains research assistance.

Provide verification states such as:

- UNREVIEWED;
- AI_FLAGGED;
- HUMAN_VERIFIED;
- HUMAN_REJECTED;
- NEEDS_MORE_EVIDENCE.

No AI output auto-promotes itself.

## Evaluation

Create benchmark issues where researchers manually know:

- relevant judgment paragraphs;
- Defence/SPO submissions;
- evidence links;
- expected counterarguments.

Evaluate citation coverage and source fidelity, not desired outcomes.

## Acceptance criteria

- Appeal Research uses real record data; ✅ the API/UI serve one narrow,
  human-reviewed issue over the real F03752 finding and exact held sources.
- issue categories work; ✅ all roadmap categories and legal/factual/sentencing/
  procedural/other contexts are constrained in schema and typed in API/UI;
  category filtering is supported.
- Argument Lab is source-backed; ✅ its outline and red-team stages reuse the
  issue's canonical citation whitelist, expose audit state, and save only human
  notes with resolved issue-source citations.
- Red Team provides multiple perspectives without winner/prediction; ✅ Defence
  analyst, SPO red team, and neutral reviewer remain separate; the real result
  is `insufficient_record` and the UI states that it declares no winner.
- Statement Comparison uses exact citations; ✅ the real comparison preserves
  separate exact citations/excerpts for F03752 paragraph 12 and
  F03667/COR/RED page 160 and is human verified.
- sentencing/finding research is traceable; ✅ every issue requires a canonical
  finding and exact sources; sentencing category/context and the same source
  roles are supported, while no sentencing issue is fabricated without the
  absent Trial Judgment.
- citation audit blocks unsupported outputs; ✅ unresolved or unverified links
  and missing material prevent ready-for-review state; note citations are
  whitelist-enforced and affirmative uncited red-team findings are rejected by
  the database.
- human review state is first-class; ✅ issues, source links, comparisons,
  reviews and findings preserve verification state/reviewer metadata; AI output
  cannot auto-promote itself.
- no prohibited scores/predictions exist. ✅ model scans, provider-validation
  adversarial tests, API/UI tests and the real gate confirm no credibility,
  person, judicial-quality, appeal-success or outcome score/prediction.

## Stop condition

Do not yet assume the entire public corpus is ingested. Phase 13 scales ingestion after quality gates.

## Completion report

```text
PHASE 12 STATUS
APPEAL RESEARCH
ARGUMENT LAB
RED TEAM
STATEMENT COMPARISON
COUNTER-EVIDENCE
SENTENCING RESEARCH
CITATION AUDIT
HUMAN REVIEW
EVALUATION
COMMITS
NEXT
MEMORY
```

## Completion Record

- Closeout audit: **PASS**, 2026-09-21. The complete phase specification and
  every acceptance criterion above were checked against migration `0008`,
  implementation commit `7a9779b`, the migrated real database, API/UI,
  automated tests, exact-source navigation, the rebuilt healthy stack and the
  pinned controlled-corpus quality report.
- Corpus scope: the existing 22-record public corpus was used unchanged. No
  discovery, download, scraping, full-corpus ingestion or Phase 13 work was
  performed. The public Trial Judgment, F03743, F03746 and the pre-correction
  SPO Final Trial Brief remain explicit missing material.
- Appeal research: one real potential procedural-fairness issue links the
  canonical F03752 paragraphs 12–16 finding to 5 exact, human-verified source
  roles. It is `NEEDS_MORE_EVIDENCE`, records Court treatment as `addressed`,
  and asserts no error or valid ground.
- Argument Lab / Red Team: source-backed outline, citation audit, resolved-only
  note whitelist, three visible perspectives, 4 human-verified findings and an
  `insufficient_record` result. Supporting/contrary/qualifying roles are
  available but no such real relationship was created without independent
  support.
- Statement comparison: one human-verified comparison with two distinct exact
  citations. It is `not_comparable` because the earlier brief is absent, and it
  makes no witness/person credibility inference.
- AI boundary: Phase 11 provider/retrieval/validation and persisted run audit
  remain the only AI path. `ai_assisted` reviews require an `ai_run_id`; the
  real benchmark is human-reviewed and no model fills corpus gaps or mutates
  findings/evidence.
- Quality gate: 1 issue, 5 source-backed links, 1 comparison, 1 red-team review,
  4 red-team findings, 7/7 resolved navigable citations, 10 human-verified
  relationships, 1 incomplete-record abstention, 0 unsupported relationships,
  and unchanged authoritative finding/evidence fingerprint.
- Tests/gates: `make lint`, `make typecheck`, `make test`, `make build`,
  migration `0007 → 0008 → 0007 → 0008`, `alembic check`, live API/UI smoke,
  standard Playwright and real-data desktop/mobile Playwright passed. Counts:
  255 backend and 199 frontend tests; standard Playwright 96 passed / 14
  real-data-gated skipped; Phase 12 real-data Playwright 6 passed, with Phase
  10/11 regression flows also passing in the combined real-data run.
- Evidence: `docs/ingestion/PHASE12_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase12-controlled-corpus-quality.json`.
- Scope stop: Phase 13 is not started. No full merits appeal analysis,
  sentencing conclusion, credibility assessment, outcome predictor, score or
  ranking was introduced.
