# Phase 22C — Legal and Source Fidelity Audit

Date: 2026-09-27

Corpus: `KSC-BC-2020-06` public records held in the local controlled corpus

Result: **AUDIT COMPLETE; PHASE CLOSEOUT BLOCKED**

## Executive result

The evidence-matrix, party-position, issue, witness and SourceAnchor boundaries
pass the focused legal/source audit. One relationship required correction:
F03752 paragraph 12 expressly identifies the corrected SPO brief but does not
expressly say that the Court relied on the filing. Migration `0019` therefore
downgrades the real relationship from `COURT_RELIES_ON` to `COURT_CITES`,
updates the issue role to `court_cited_material`, and changes the graph edge
from `RELIES_ON` to `CITED_IN`. The ingestion projectors now reproduce that
conservative classification.

Phase 22 cannot yet be closed. The real AI audit found that all 25 answered runs
retain source links, but every answered run includes at least one low-relevance
retrieval passage while its AI-analysis block says the retrieved passages
address the question. The exact source is visible, so this is not fabricated
provenance; however, the system has not demonstrated that unsupported material
fails closed. The operator also deferred the full repository gate. No
`phase-22-complete` tag is permitted until both conditions are cleared.

## Semantic separation

- Database categories remain distinct for Court findings, witness testimony,
  SPO argument, Defence argument, Victims' Counsel argument, documents/exhibits,
  human notes, AI analysis and external public sources.
- The real SPO and Defence rows are expressly `court_summary`, not direct party
  filings. Their unavailable underlying filings remain recorded as missing.
- The sole issue is `human_defined` and uses “Potential Issue for Review”; its
  text says that no error, valid ground or predicted outcome is asserted.
- The three external-public-source records remain `EXTERNAL_ONLY`, with no
  citation, document, exhibit or finding bridge.
- No guilt, credibility, reliability, suspicion or outcome score was found.

## Source samples

### Court finding and citation

Finding `FD-F03752-P12-16` exactly matches its verified SourceAnchor in public
version `KSC-BC-2020-06/F03752`, printed page 5, paragraphs 12–16. Paragraph 12
identifies the “Corrected Version of the SPO Final Trial Brief”. This supports
`COURT_CITES`; it does not independently support `COURT_RELIES_ON`.

### Party positions

The Defence position exactly matches F03752 paragraph 6 and the SPO position
exactly matches paragraph 7. Both stored excerpts equal their SourceAnchor text,
are attributed separately, and are labelled as Court summaries. Court reasoning
and Court response remain separate rows.

### Witness comparison

The real case contains 9 appearance rows across 4 witnesses, but no publishable
witness comparison group. The corpus has no pair of witness-linked transcript
segments with the required SourceAnchors. The UI therefore exposes only the
source-backed hearing/session/examination trail and does not claim a
contradiction, credibility conclusion or hidden identity.

### SourceAnchor integrity

Focused equality checks found zero mismatches for finding text, finding-link
text, party-argument text and all 5 issue-source excerpts. No real matrix or
issue row is missing its required SourceAnchor. Each sampled span remains bound
to the exact document version and Reader coordinates.

## AI audit

- Completed runs: 64.
- Source-backed answered runs: 25.
- Withheld or insufficient-evidence runs: 39.
- Answered runs containing at least one uncited but exact retrieval-source
  block: 25. These blocks retain `ai_output_sources`, exact excerpts and Reader
  paths, but some are not relevant to the question.
- AI outputs with a recorded unresolved-citation claim: 0.
- AI-suggested legal comparison candidates: 0.

The reviewed question asks what the Panel said about amendments to the corrected
SPO final brief. Ranks 1–4 resolve to the exact F03752 finding, Defence summary,
Court response and SPO summary. Lower-ranked material includes unrelated public
record passages. Because the analysis block characterises the retrieved set as
addressing the question, the fail-closed criterion is not yet satisfied.

## Final real-data counts

| Measure | Count |
| --- | ---: |
| Findings in matrices | 1 |
| Court-relied-on links | 0 |
| Court-citation links | 1 |
| Party positions | 2 |
| Legal issues | 1 |
| Supporting classifications | 0 |
| Qualifying classifications | 0 |
| Contrary/tension candidates | 0 |
| Witness comparison groups | 0 |
| Review issues | 1 |
| Source-backed AI responses | 25 |
| AI-suggested candidates | 0 |
| SourceAnchors, corpus-wide | 74,036 |

## Focused verification

- Migration `0018 -> 0019 -> 0018 -> 0019`: PASS.
- Changed Python files, Ruff: PASS.
- Phase 22A matrix, Phase 12 appeal and appeal safety: 9 passed.
- Finding/appeal UI and EN/SQ parity: 7 passed.
- Exact-text/SourceAnchor mismatch checks: 0 mismatches.
- Generic administration UI review: no new table surface; Phase 21 cards,
  panels, source badges and Reader navigation remain in use.

The full `make lint`, `make typecheck` and `make test` gate, broad responsive,
accessibility, performance and security checks were not run at the operator's
request. This report records the blocker instead of claiming completion.

## Required next action

Constrain or validate AI retrieval/output relevance so unrelated source blocks
are excluded or the answer abstains, rerun a real citation-first AI sample, then
run the deferred Phase 22 closeout gates. Only after those checks pass may Phase
22 be marked complete and tagged.
