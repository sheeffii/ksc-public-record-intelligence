# Phase 15 real-data route audit

Final acceptance audit, completed 2026-09-22 after the Phase 15B verification
pass. Counts were rechecked against the controlled real-case database.
`EMPTY` means the real API currently has no verified source-backed rows; the UI
shows an honest empty state. Explicit `NEXT_PUBLIC_DATA_SOURCE=mock` remains
available only for tests, stories and visual QA. The unset/default mode is API.
Counts of zero for Person, Witness and Exhibit refer only to the current
structured / verified projections; they do not establish that the underlying
public court record contains none.

| Production route            | Classification | API endpoint                                               |                       Real record count | Demo dependency | Provenance support                                                         | Desktop test                | Mobile test                 | Status |
| --------------------------- | -------------- | ---------------------------------------------------------- | --------------------------------------: | --------------- | -------------------------------------------------------------------------- | --------------------------- | --------------------------- | ------ |
| `/`                         | REAL           | aggregate repository reads                                 |      56 documents; 1 finding; 178 edges | None            | API records and verification state                                         | Focused component           | Phase 15 E2E PASS           | PASS   |
| `/documents`                | REAL           | `GET /api/v1/documents`                                    |                                      56 | None            | Official ref, public state, source path, counts                            | Focused component           | Phase 15 E2E PASS           | PASS   |
| `/documents/[id]`           | REAL           | `GET /api/v1/documents/{ref}` + coordinate-filtered chunks |                      61 parsed versions | None            | Source/PDF page, paragraph ranges, parser and artifact state, official URL | Focused component           | Phase 15 E2E PASS           | PASS   |
| `/people`                   | EMPTY          | `GET /api/v1/people`                                       |             0 verified projected people | None            | Entity counts and aliases when reviewed records exist                      | Focused empty state         | Phase 15 E2E PASS           | PASS   |
| `/people/[slug]`            | EMPTY          | `GET /api/v1/people/{slug}`                                |                                       0 | None            | Fail-closed 404; source-backed profile only                                | Focused component           | Phase 15 E2E PASS           | PASS   |
| `/witnesses`                | EMPTY          | `GET /api/v1/witnesses`                                    |                   0 projected witnesses | None            | Structural code-only protection                                            | Focused empty state         | Phase 15 E2E PASS           | PASS   |
| `/witnesses/[code]`         | EMPTY          | `GET /api/v1/witnesses/{code}`                             |                                       0 | None            | Protected payload omits public identity                                    | Focused component           | Phase 15 E2E PASS           | PASS   |
| `/witnesses/[code]/compare` | REAL           | `GET /api/v1/statement-comparisons`                        |                            1 comparison | None            | Two exact resolved Court citations; neutral classification                 | Existing Phase 12 component | Phase 15 E2E PASS           | PASS   |
| `/exhibits`                 | EMPTY          | `GET /api/v1/exhibits`                                     |                    0 projected exhibits | None            | Exhibit and court-document categories remain distinct                      | Focused empty state         | Phase 15 E2E PASS           | PASS   |
| `/incidents`                | EMPTY          | `GET /api/v1/incidents`                                    |                    0 verified incidents | None            | No keyword-proximity inference                                             | Focused empty state         | Phase 15 E2E PASS           | PASS   |
| `/incidents/[id]`           | EMPTY          | `GET /api/v1/incidents/{slug}`                             |                                       0 | None            | Fail-closed 404; source-backed fields only                                 | Focused component           | Phase 15 E2E PASS           | PASS   |
| `/findings`                 | REAL           | `GET /api/v1/findings`                                     |                                       1 | None            | Human-verified Court finding and exact citation                            | Existing Phase 10 component | Phase 15 E2E PASS           | PASS   |
| `/findings/[id]`            | REAL           | `GET /api/v1/findings/{key}/matrix`                        |                                       1 | None            | Court finding, arguments and evidence remain separate                      | Existing Phase 10 component | Phase 15 E2E PASS           | PASS   |
| `/network`                  | REAL           | `GET /api/v1/network`                                      |                    48 nodes / 178 edges | None            | Resolved citation required per edge                                        | Existing Phase 9 component  | Phase 15 E2E PASS           | PASS   |
| `/network/path`             | REAL           | `GET /api/v1/network/path`                                 |                         Query-dependent | None            | Independently cited hops                                                   | Existing Phase 9 component  | Phase 15 E2E PASS           | PASS   |
| `/timeline`                 | REAL           | `GET /api/v1/events`                                       |                                      54 | None            | Source-backed typed dates; no inferred events                              | Existing Phase 9 component  | Phase 15 E2E PASS           | PASS   |
| `/search`                   | REAL           | `GET /api/v1/search`; `GET /api/v1/media`                  |                         Query-dependent | None            | Court, External and Both-separated modes                                   | Focused component           | Phase 15 E2E PASS           | PASS   |
| `/ai`                       | REAL           | `GET/POST /api/v1/ai/runs`                                 |                     Audited run history | None            | Retrieval snapshots and exact source links                                 | Existing Phase 11 component | Phase 15 E2E PASS           | PASS   |
| `/ai/[sessionId]`           | REAL           | `GET /api/v1/ai/runs/{id}`                                 |                         Query-dependent | None            | Withheld/insufficient state and citation audit                             | Existing Phase 11 component | Phase 15 E2E PASS           | PASS   |
| `/appeal`                   | REAL           | `GET /api/v1/appeal/issues`                                |                                       1 | None            | Exact sources, missing material and human review                           | Existing Phase 12 component | Phase 15 E2E PASS           | PASS   |
| `/appeal/argument/[id]`     | REAL           | `GET /api/v1/appeal/issues/{key}/argument-lab`             |                                       1 | None            | Human-reviewed stages and citations                                        | Existing Phase 12 component | Phase 15 E2E PASS           | PASS   |
| `/media`                    | REAL           | `GET /api/v1/media`                                        |                        3 external items | None            | Separate external provenance; all `EXTERNAL_ONLY`                          | Existing Phase 14 component | Existing Phase 14 component | PASS   |
| `/public`                   | REAL           | paginated repository reads by category                     |              Same as source directories | None            | Simplified view retains links and verification-backed rows                 | Focused component           | Phase 15 E2E PASS           | PASS   |
| `/public/[topic]`           | REAL           | paginated repository reads for the selected category       | Category-dependent; honest empty states | None            | Source category stays explicit; no substitute records                      | Focused component           | Phase 15 E2E PASS           | PASS   |

Normal production route sources are guarded by
`apps/web/src/app/phase15-route-gate.test.ts`: the API is the default, route
files may not import fixture data directly, synthetic identifiers are refused,
and this audit may not contain a `MIXED` or `DEMO` classification row.

## Phase 15B verification checkpoint

- Desktop and mobile real-data Playwright: **PASS**, 38/38 Phase 15 checks.
- Search and Reader: real results/content, no production demo badge, exact
  coordinate and official-source checks pass.
- Network: 48 human-readable document nodes and 178 citation-backed edges are
  visible after correcting the API-coordinate adapter; inspector provenance is
  preserved and UUID endpoints are not the primary presentation.
- Findings: one verified finding; the directory uses a concise judgment/paragraph
  label and excerpt while the canonical full text remains on the detail route.
- The current structured / verified projections contain 0 Person, Witness,
  Exhibit and Claim records. This does not establish that the underlying public
  court record contains none. Rows present in those tables belong only to
  `KSC-DEMO-0000`, so production keeps honest empty states rather than projecting
  unreviewed entities.
- Homepage again presents the approved three-panel summary row, with live
  ingestion counts in the third panel.
