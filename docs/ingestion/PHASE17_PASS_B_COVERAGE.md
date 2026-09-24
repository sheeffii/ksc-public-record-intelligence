# Phase 17B official corpus expansion

Snapshot date: 2026-09-24
Case: `KSC-BC-2020-06`

## Outcome

The official operator workflow discovered 75 genuinely new public candidates.
It accepted 73 immutable PDFs (42,867,559 bytes) and quarantined 2. No duplicate,
missing PDF, failed acquisition, access-control bypass, or inferred metadata was
accepted. The tracked batch manifest is `manifests/phase17-corpus-03.json`; the
machine-readable reconciliation is `manifests/phase17-pass-b-coverage.json`.

The accepted batch contains 50 filings and 23 transcripts: EN 57 / SQ 16, across
2021 (16), 2022 (14), 2023 (21), 2024 (21), and 2025 (1).

## Exact official-case reconciliation

Historical/manual benchmark artifacts are excluded from every total below.

| Measure                          |     Before |      After |       Delta |
| -------------------------------- | ---------: | ---------: | ----------: |
| Source records                   |         62 |        135 |         +73 |
| Logical documents                |         56 |        116 |         +60 |
| Versions / PDFs                  |         61 |        134 |         +73 |
| Bytes                            | 36,443,971 | 79,311,530 | +42,867,559 |
| Pages                            |      2,832 |      5,725 |      +2,893 |
| Numbered paragraphs              |      2,019 |      3,133 |      +1,114 |
| Transcript segments / statements |      1,363 |      8,547 |      +7,184 |

All 134 official versions are parsed and indexed. Three require review: the
pre-existing photograph annex and two new transcripts whose native PDF page/line
structure is incomplete. No accepted version failed. Migration `0011` widened
`hearings.session_label` to 255 characters so the official 81-character session
title is stored without truncation.

## Structured projections and citations

| Projection    | Before | After |
| ------------- | -----: | ----: |
| People        |      0 |     0 |
| Witnesses     |      0 |     0 |
| Organizations |      0 |     0 |
| Exhibits      |      0 |     0 |
| Hearings      |      3 |    16 |
| Statements    |  1,363 | 8,547 |
| Events        |     54 |   127 |
| Relationships |    178 |   291 |

People, witness, organization, and exhibit rows remain zero because no approved
reviewed projection exists; the pipeline did not infer protected identities or
turn filing annexes into exhibits. Hearings retain official detail/PDF provenance,
statements retain exact PDF/page/line coordinates, events come from source
metadata, and relationships come only from exact resolved citations.

| Citation state | Before |  After |
| -------------- | -----: | -----: |
| Resolved       |    188 |    306 |
| Ambiguous      |      3 |      3 |
| Unresolved     | 15,420 | 16,831 |
| Invalid        |    119 |    141 |
| Total          | 15,730 | 17,281 |

Re-resolution and the deterministic evidence projection completed after parsing.

## Quarantine and quality gate

Records `r17` and `r22` remain outside ingestion because each Albanian transcript
failed the independent page-one identity gate: `transcript page 1 has no
open-session heading`. Their captured evidence remains in the local quarantine;
nothing was inferred or persisted for them.

The accepted bundle quality gate passed 73/73 records, covering 60 logical
documents and 73 versions. Phase 17 remains in progress; this pass does not
start another acquisition batch or claim exhaustive coverage.
