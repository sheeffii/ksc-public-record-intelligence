# AI methods

**Status: no AI exists in this codebase.** Phase 4 makes no provider call, computes
no embedding, and requires no API key. This document fixes the rules any future AI
layer must satisfy so they are designed in, not retrofitted.

## Position in the architecture

AI is the top of the hierarchy and reads only:

```
primary sources → database → structured evidence → provenance/citations → search/network → AI
```

AI output is `AI ANALYSIS`. It is never a court finding, never testimony, never a
document. It is never a source of truth and is never written back into an evidence
table. "AI memory" is not evidence.

## Retrieval before composition

1. The question is scoped (case, entity, date range).
2. Sources are retrieved from the record (lexical + pgvector) and **listed to the
   user before any answer text exists**.
3. Composition may only cite items in the retrieved set.
4. Every citation is checked against the persisted resolution index (ADR-005).
5. If any citation in any block is not `resolved`, **the whole answer is
   withheld** and the gap reported. Partial answers are more dangerous than none.

## Answer structure

The API returns ordered `AnswerBlock`s (`packages/shared`): `court`, `evidence`,
`testimony`, `spo`, `defence`, then a boundary, then `ai`. The client never
reorders. `kind: ai` renders in the dashed AI container after the labelled
boundary — four simultaneous signals, never fewer.

## Neutrality

The AI layer must always distinguish:

`COURT FINDING` · `WITNESS TESTIMONY` · `SPO ARGUMENT` · `DEFENCE ARGUMENT` ·
`DOCUMENT / EXHIBIT` · `AI ANALYSIS`

It must never produce guilt scores, suspicion scores, credibility scores, importance
rankings, or appeal success probabilities — and the schema has no field to hold
them. Appeal-adjacent output is titled _Potential Issues for Review_. In its own
voice it never uses _lying, dishonest, false, unreliable, guilty, culpable,
suspicious, likely, probable, strong, weak_; such words appear only inside a quoted
court finding with its citation and badge.

## Protected witnesses

Prompts and retrieval sets contain only W-codes for protected witnesses. The model
is never asked to, and retrieval never enables it to, resolve a code to a name.
Closed-session and redacted ranges are excluded from retrieval and listed to the
user as gaps.

## Gaps

Closed sessions, redactions, untranslated documents and unresolved citations are
returned alongside the answer as `Gap` objects and always rendered. The model is
never asked to fill them.

## Evaluation (planned, `tests/evaluation/`)

- Citation accuracy: every cited page/¶/line contains the quoted text.
- Withhold rate: answers containing an unresolved citation are withheld 100 %.
- Neutrality lint: banned-vocabulary scan over generated text outside quotations.
- Boundary integrity: every `ai` block follows the boundary in the payload.

## Provider configuration

`AI_PROVIDER`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `EMBEDDING_MODEL` exist in
`.env.example` as placeholders. Nothing reads them. Every AI run will be recorded
in `ai_runs` with model, prompt version, retrieval set and unresolved count.
