# Phase 22B — Legal Research Data Report

Date: 2026-09-27  
Scope: controlled public corpus; no new court material acquired

## Result

Phase 22B now provides a source-first witness appearance workflow, explicit
party-position mapping, neutral passage-comparison candidate semantics and an
issue-centred Potential Issue for Review workspace. Court findings, testimony,
party arguments, Court treatment, human classification, AI suggestions and
external public sources remain separate categories.

The real corpus does **not** currently support a witness passage comparison.
It contains 28 persisted appearance rows for 6 witnesses, but only 2 transcript
segments linked to one witness and neither segment has the SourceAnchor required
for publication as an exact comparison passage. The UI therefore shows the
hearing/session/examination trail and exact transcript navigation, then an
explicit no-comparable-passages state. It does not infer relationships across
redactions, private sessions or missing statements.

## Actual data counts

| Measure | Count |
| --- | ---: |
| Witnesses comparison-ready | 0 |
| Comparable passage groups | 0 |
| Party-position rows | 2 |
| SPO positions | 1 |
| Defence positions | 1 |
| Victims' Counsel positions | 0 |
| Issues | 1 |
| Issue/finding links | 1 |
| Review candidates (`POTENTIAL_*` or human-reviewed `CONTRADICTION`) | 0 |
| SourceAnchors | 74,036 |
| AI-suggested candidates | 0 |
| Human-reviewed comparison records | 1 |

The one human-reviewed comparison is `NOT_COMPARABLE`; it is not counted as a
comparable passage group or review candidate. The issue also preserves 4
missing-material rows. Court reasoning and Court response are displayed
separately from the 2 party positions.

## Semantic and source controls

- Candidate labels are `POTENTIAL_TENSION`, `POTENTIAL_DIFFERENCE` and
  `POTENTIAL_QUALIFICATION`. `CONTRADICTION` requires a human-verified record
  with an identified reviewer.
- `AI_SUGGESTED` comparisons cannot become verified through the database model.
- Direct party text remains distinct from a Court summary through
  `source_scope`; SPO and Defence attribution remains separate and Victims'
  Counsel remains a first-class empty category where no source exists.
- Exact excerpts remain primary. Each displayed issue source exposes its
  SourceAnchor identifier and Reader link. No generated paraphrase replaces a
  source passage.
- No credibility, reliability, guilt, outcome or appeal-success score exists.

## Targeted verification

- Alembic `0017 -> 0018 -> 0017 -> 0018`: PASS.
- Phase 12 appeal and Phase 22A matrix integration slice: 7 passed.
- Appeal UI, repository mapping and EN/SQ parity slice: 19 passed.
- Changed Python files: Ruff PASS.
- Changed web files: ESLint PASS.
- Frontend TypeScript: PASS.

The repository-wide `make lint`, `make typecheck` and `make test` checkpoint is
intentionally deferred at the operator's request. Phase 22B is implemented but
not marked complete; Phase 22C has not started.
