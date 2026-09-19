# Phase 12 — Appeal Research, Red Team & Statement Comparison

**Status:** Pending.

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

- Appeal Research uses real record data;
- issue categories work;
- Argument Lab is source-backed;
- Red Team provides multiple perspectives without winner/prediction;
- Statement Comparison uses exact citations;
- sentencing/finding research is traceable;
- citation audit blocks unsupported outputs;
- human review state is first-class;
- no prohibited scores/predictions exist.

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
