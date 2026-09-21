# Phase 12 controlled-corpus appeal research quality gate

Date: 2026-09-21  
Result: **PASS, with explicit incomplete-record abstention**

The gate uses only the existing 22-record controlled public corpus. The
`ksc-ingest build-appeal` and `ksc-ingest gate-appeal` commands make no network
request and do not expand the corpus:

```bash
ksc-ingest build-appeal
ksc-ingest gate-appeal \
  --json docs/ingestion/manifests/phase12-controlled-corpus-quality.json
```

## Real benchmark

The held corpus does not contain the public Trial Judgment, so Phase 12 does
not claim a complete merits or sentencing review. The narrow real benchmark is
the existing human-verified Phase 10 finding at Court decision `F03752`,
paragraphs 12–16:

- 1 potential issue for review, classified as `procedural_fairness` and
  `NEEDS_MORE_EVIDENCE`;
- 5 exact, human-verified issue-source relationships: Court reasoning,
  Defence position, SPO position, evidence expressly cited by the Court, and
  Court response;
- 1 exact, human-verified statement comparison between the Court's paragraph
  12 characterization and the held corrected brief at `F03667/COR/RED`, page
  160;
- 1 human-verified red-team review with 4 findings across Defence analyst, SPO
  red team, and neutral reviewer perspectives;
- 7 unique resolved citations, all with exact-source navigation;
- 10 human-verified Phase 12 relationships in total;
- 1 incomplete-record abstention and 0 unsupported relationships surfaced;
- authoritative finding and finding-evidence state byte-stable by canonical
  fingerprint before and after the gate.

The issue result is `INSUFFICIENT RECORD`. It does not state that the Court
erred, that an appeal ground is valid, or that any outcome is likely.

## Statement comparison

The comparison is `NOT COMPARABLE`, not `CONSISTENT`: the held corrected brief
contains the `P00303_ET` reference described by the Panel, but the
pre-correction brief is absent. The comparison therefore cannot independently
establish the substitution. Both excerpts have separate exact citations and
the classification makes no credibility assessment.

## Court treatment and counter-material

Court treatment is `ADDRESSED` because paragraphs 12–16 contain an identifiable
response. This records the presence of reasoning, not whether the reasoning was
correct. The SPO red-team stage cites the Court's clerical-correction and
no-prejudice reasoning. The system supports `SUPPORTING`, `CONTRARY`, and
`QUALIFYING` source roles, but the real benchmark creates none because the held
record does not establish those relationships independently. Network proximity
and search similarity create no canonical evidence link.

## Missing official material

- public Trial Judgment for `KSC-BC-2020-06`;
- underlying Defence filing `F03743`;
- underlying SPO filing `F03746`;
- pre-correction SPO Final Trial Brief.

The two party positions remain labelled as exact Court summaries. Missing
Court treatment is never rewritten as “ignored.” The absent Trial Judgment
also means no real sentencing issue is asserted; the schema and API preserve a
sentencing category/context for future exact, reviewed material.

## Safety and immutability

Phase 12 reuses Phase 11's provider, retrieval whitelist, persisted run audit,
and fail-closed output validator rather than introducing a second AI path.
The real benchmark is human-authored and human-verified; no model run is needed
to fill missing material. Existing adversarial coverage rejects fabricated and
wrong-case identifiers, nonexistent pages/transcript lines, non-whitelist
sources, invented quotes, category conflation, evaluative conclusions, appeal
success claims, and credibility scoring. Database constraints additionally
reject uncited affirmative red-team findings and invalid comparison/treatment
states.

The machine-readable result is
`docs/ingestion/manifests/phase12-controlled-corpus-quality.json`.
