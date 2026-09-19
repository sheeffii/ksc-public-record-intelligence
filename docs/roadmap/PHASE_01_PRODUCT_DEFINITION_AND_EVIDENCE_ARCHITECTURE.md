# Phase 1 — Product Definition & Evidence/Safety Architecture

**Status:** Historically completed. Keep this file as the conceptual contract for all later work.

## Goal

Define what KSC Public Record Intelligence is, what it is not, which users it serves, what counts as evidence, how provenance is represented, and what safety/neutrality rules must exist before any design or implementation begins.

## Why this phase exists

A court-record research system becomes unreliable if its core definitions are vague. Before UI, database, ingestion, or AI work, the project must decide:

- what the source of truth is;
- how record material differs from analysis;
- how public/redacted/protected information is handled;
- what a citation must contain;
- what claims the product may and may not make;
- what the initial case scope is;
- how future AI must behave.

## Initial scope

Primary initial case:

```text
KSC-BC-2020-06
```

Initial corpus policy:

```text
Lawfully public KSC records only.
```

The architecture may support future cases, but early product behavior should be optimized for one case so provenance and legal-research workflows can be proven correctly.

## Product users

Design for several user types without changing the truth model:

- lawyers and legal researchers;
- journalists/researchers;
- academics;
- technically sophisticated investigators working only from public records;
- ordinary users who need a simpler public mode.

The public/simple mode can simplify language and layout, but it must not weaken citations or change the underlying legal wording.

## Evidence hierarchy

The permanent hierarchy is:

```text
PRIMARY PUBLIC COURT SOURCE
        ↓
PERSISTED SOURCE RECORD
        ↓
STRUCTURED EVIDENCE
        ↓
PROVENANCE / CITATION
        ↓
SEARCH / NETWORK / ANALYSIS
        ↓
AI
```

AI output is not a primary source and does not become evidence merely because it is stored.

## Required source categories

The product must distinguish at least:

- `COURT_FINDING`
- `WITNESS_TESTIMONY`
- `SPO_ARGUMENT`
- `DEFENCE_ARGUMENT`
- `DOCUMENT_EXHIBIT`
- `HUMAN_NOTE`
- `AI_ANALYSIS`

Other categories may be added later, but these distinctions must remain visible and queryable.

## Protected witnesses

A protected witness may exist as a public code without a public person identity.

Example:

```text
W01234
```

If this is all the public record reveals, display only the code and a neutral label such as `Protected Witness`.

Never:

- infer the identity;
- correlate unrelated sources to deanonymize the person;
- reconstruct redactions;
- store speculative names in hidden fields;
- use AI to guess identity.

## Citation principle

Every material factual/legal-research output should eventually be traceable to source coordinates where available.

Examples:

```text
Case number
Official document ID
Document version
Page
Paragraph
Transcript page
Transcript lines
Exhibit ID
Witness code
Official source URL
```

Missing coordinates remain missing. Never invent them.

Citation states should eventually support:

- `RESOLVED`
- `UNRESOLVED`
- `AMBIGUOUS`
- `INVALID`

## Neutrality / non-inference rules

The system must not contain:

- guilt scores;
- suspicion scores;
- credibility percentages;
- “importance” scores that imply culpability;
- appeal-success probabilities;
- automatic labels such as liar/dishonest;
- graph-edge semantics that imply guilt merely from connection.

Use neutral wording such as:

```text
Potential Issue for Review
Possible inconsistency
Qualification
Timeline difference
Requires human review
```

## Court finding vs claim

A later database must distinguish:

- a proposition that exists in the record (`Claim`);
- a finding made by the Court (`Finding`);
- an argument advanced by a party (`Argument`);
- an analytical observation made by AI (`AI Analysis`).

Persistence does not equal truth.

## Network principle

A graph edge means only that a source-backed relationship exists.

The UI disclaimer should communicate:

> A connection does not itself imply guilt, wrongdoing, agreement, endorsement, or responsibility.

Every production relationship should eventually carry provenance.

## Core workflows defined in this phase

The product should eventually support:

1. search record → open exact source;
2. person/witness dossier → related public materials;
3. document reader → exact citations and context;
4. transcript viewer → page/line-level source navigation;
5. finding → evidence relied upon → source audit;
6. network/path → each hop independently cited;
7. timeline → distinguish event date from filing/testimony/decision dates;
8. appeal research → issue identification without outcome prediction;
9. AI research → source-grounded answer with visible citations;
10. public mode → simplified explanation with unchanged source integrity.

## Out of scope in Phase 1

- implementation;
- crawling;
- database migrations;
- real data ingestion;
- AI integration;
- visual design;
- prediction of legal outcomes.

## Deliverables

- project mission;
- public-only policy;
- evidence/source taxonomy;
- protected-witness rules;
- citation-first principle;
- neutrality rules;
- initial case scope;
- high-level workflows;
- AI separation principle.

## Acceptance criteria

Phase 1 is considered complete when all later contributors can answer:

- What is authoritative?
- What is AI allowed to do?
- How are protected witnesses handled?
- What qualifies as a citation?
- What must never be inferred?
- What does a graph edge mean?
- What is the initial case?

## Stop condition

Do not start product design until these principles are explicit.

## Completion report

```text
PHASE 1 STATUS
MISSION
SCOPE
EVIDENCE RULES
CITATION RULES
PROTECTED-WITNESS RULES
NEUTRALITY RULES
NEXT
```
