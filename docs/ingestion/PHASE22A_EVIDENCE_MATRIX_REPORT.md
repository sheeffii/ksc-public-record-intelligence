# Phase 22A — Evidence Matrix Data Quality Report

**Date:** 2026-09-27  
**Case:** `KSC-BC-2020-06`  
**Scope:** Existing lawfully held public corpus only; no acquisition was run  
**Result:** PASS for the deliberately narrow architecture benchmark

## Purpose and interpretation boundary

This report measures source-backed research structure. It does not measure
whether a proposition is legally or factually true, whether testimony is
credible, or whether an issue would succeed. `VERIFIED_SOURCE_RELATION` means
that the recorded relationship and its source connection were verified. It is
not a legal-truth label.

The benchmark is Court decision `KSC-BC-2020-06/F03752`, finding
`FD-F03752-P12-16`. The held corpus still does not contain the public Trial
Judgment, underlying Defence filing `F03743`, underlying SPO filing `F03746`,
or the pre-correction SPO Final Trial Brief. Those absences remain explicit.

## Current usable structured coverage

| Structure                   | Real rows | Usable Phase 22A coverage                                         |
| --------------------------- | --------: | ----------------------------------------------------------------- |
| Court findings              |         1 | Human-verified F03752 paragraphs 12–16                            |
| Party/Court arguments       |         3 | 1 SPO, 1 Defence, 1 Court response/reasoning                      |
| Potential Issues for Review |         1 | 5 source links and 4 explicit missing-material rows               |
| Citations                   |    20,037 | 11,072 resolved; non-resolved rows remain fail-closed             |
| Relationships               |    12,120 | Includes 3 Phase 22A source-documented path edges                 |
| Exhibits                    |       902 | 2 admitted from official status sources; 900 unknown              |
| Transcript segments         |    15,171 | 0 segments carry a verified witness link usable by this finding   |
| Party filings               |        79 | SPO/Defence/Victims' Counsel documents in the case inventory      |
| Real-case SourceAnchors     |    74,023 | Existing corpus anchors plus typed Phase 22A legal-object anchors |

The existence of 902 exhibits, 15,171 transcript segments or 79 party filings
does not make them relevant to this finding. Phase 22A creates no relationship
from corpus proximity, identifier similarity or lexical overlap.

## Initial real finding matrix

The finding matrix returns 5 rows, bounded and paginated:

| Category            | Relationship      | Rows | Source scope                                     | SourceAnchor   |
| ------------------- | ----------------- | ---: | ------------------------------------------------ | -------------- |
| Court finding       | `court_finding`   |    1 | Direct Court passage                             | Page fallback  |
| SPO filing/material | `court_relies_on` |    1 | Court reasoning/citation to held corrected brief | Page fallback  |
| SPO argument        | `party_position`  |    1 | Court summary; F03746 missing                    | Page fallback  |
| Defence argument    | `party_position`  |    1 | Court summary; F03743 missing                    | Exact geometry |
| Court response      | `court_treatment` |    1 | Direct Court passage                             | Page fallback  |

All 5 returned rows have a version-bound SourceAnchor. The Court-reliance row
opens F03752 paragraph 12 as the relationship basis and separately opens held
version `F03667/COR/RED` as the cited material. Its Evidence Path is one
source-backed `RELIES_ON` hop from the finding node to the held filing node.

The legal-matrix projector creates 10 typed anchors for the real benchmark on
each idempotent run: 3 argument anchors, 1 finding-evidence-link anchor, 5
issue-source anchors and 1 relationship-evidence anchor. Current projection
precision is 2 exact-geometry and 8 page-only anchors. Page-only is an honest
fallback and is never presented as an exact highlight.

## Required count split

| Measure                                | Source-derived facts | Research classifications |
| -------------------------------------- | -------------------: | -----------------------: |
| Findings represented                   |                    1 |                        0 |
| Court-reliance links                   |                    1 |                        0 |
| Court-citation-only links              |                    0 |                        0 |
| Party arguments                        |                    2 |                        0 |
| Court response rows                    |                    1 |                        0 |
| Supporting classifications             |                    0 |                        0 |
| Qualifying classifications             |                    0 |                        0 |
| Contrary classifications               |                    0 |                        0 |
| Witness passages linked to the finding |                    0 |                        0 |
| Exhibit links to the finding           |                    0 |                        0 |
| Matrix rows with SourceAnchors         |                    5 |                        0 |

The existing issue matrix also returns 5 source-derived rows: Court reasoning,
Defence position, SPO position, evidence relied upon and Court response. It
does not convert the issue into an appeal ground or legal conclusion.

## Semantic and provenance controls

- Migration `0017` replaces the ambiguous finding-link vocabulary with
  `COURT_RELIES_ON`, `COURT_CITES`, `PARTY_CITES`, `SUPPORTS`, `QUALIFIES`,
  `CONTRARY` and `CONTEXT`.
- Database checks require Court relations to be source-derived and marked as
  Court-cited. `COURT_RELIES_ON` requires an explicit-reliance basis.
- `SUPPORTS`, `QUALIFIES`, `CONTRARY` and `CONTEXT` require a human-defined or
  AI-suggested origin and a named review process.
- An AI-suggested evidence classification cannot be stored as human-verified.
  It remains `AI_SUGGESTED` until a human creates/reclassifies the reviewed
  relationship through the human workflow.
- Issue definitions retain `HUMAN_DEFINED`, `SOURCE_DERIVED` or
  `AI_SUGGESTED`; no issue row asserts legal error or predicts outcome.
- Existing stable Finding, Argument and AppealIssue identifiers remain the
  proposition/passage identities. No disconnected generic proposition table
  was added for ordinary text.
- Party attribution and `direct_source` / `court_summary` / `source_missing`
  remain separate. The real SPO and Defence rows are Court summaries, not the
  unavailable underlying filings.
- The API returns SourceAnchor, classification origin, review process/status,
  verification state and separate cited-material navigation. The browser does
  not reconstruct matrix semantics.

## Honest absences and limitations

- No witness testimony is linked to the benchmark finding. The UI states this
  without inferring that no relevant testimony exists.
- No exhibit is linked to the benchmark finding. The text mentions exhibit
  identifiers, but Phase 22A does not infer exhibit identity or status.
- No supporting, qualifying or contrary research classification was created.
- No Victims' Counsel position is present for this benchmark.
- No human research note or AI analysis is attached to the finding matrix.
- The public Trial Judgment and three comparison/party sources remain missing;
  the application does not fill those gaps with Court summaries or AI output.

## Targeted verification

- Migration `0016 → 0017 → 0016 → 0017` succeeds; models match the migrated
  schema.
- Database tests reject unsupported Court reliance, source-derived research
  directions and human-verified AI suggestions.
- Finding and issue matrix filters, pagination and the 100-row bound pass.
- Real repository inspection confirms 5/5 matrix rows have SourceAnchors and
  the Court-reliance Evidence Path resolves in one cited hop.
- Finding UI component tests confirm semantic category separation,
  SourceAnchor navigation, Evidence Path navigation and neutral empty states.
- EN/SQ message parity, frontend mapping and repository tests pass.
- Final repository-wide gates pass: lint, Python/TypeScript typecheck, 357
  backend tests and 260 frontend tests.

## Conclusion

The architecture is proven against a small real source set without broad
corpus classification. The appropriate next checkpoint is 22B, which remains
unauthorized and unstarted.
