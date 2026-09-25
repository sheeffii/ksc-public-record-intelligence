# Phase 19 quality gate

Phase 19 is **COMPLETE** (2026-09-25, tag `phase-19-complete`). This file records
each pass's checkpoint evidence.
Machine-readable manifests live in `docs/ingestion/manifests/`.

## Pass A — verified entity mentions (2026-09-24)

Scope: the known public corpus of `KSC-BC-2020-06` (baseline unchanged, no
acquisition). Projection: `ksc-ingest project-mentions`, processor
`phase19a-mentions` v1. Gate: `ksc-ingest gate-phase19a`. Manifest:
`manifests/phase19a-verified-mentions-quality.json` (run
`3a669fd5-10a3-4fd4-a0f3-e632442e7280`).

Result: **PASS**.

### Occurrence model

| Class              | Meaning                                                                                                     | Where it lives                                               |
| ------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `VERIFIED_MENTION` | A named deterministic rule binds this exact character range in this public version to one registered entity | `entity_occurrences`, `mention_state = verified`             |
| `REVIEW_REQUIRED`  | Same exact provenance, but the binding is surname-level or shared by more than one recorded entity          | `entity_occurrences`, `mention_state = review_required`      |
| `SEARCH_MATCH`     | A lexical hit on a name or code. Discovery only                                                             | Not stored. `/search` hits carry `match_class: SEARCH_MATCH` |

`rejected` is reserved for audit and is never served.

### Counts

| Entity        | Verified | Review-required | Search-only | Not bound (not in registry) |
| ------------- | -------: | --------------: | ----------: | --------------------------: |
| People        |    2,602 |           2,198 |      14,194 |            0 speaker labels |
| Witnesses     |    5,175 |               0 |           0 |                     0 codes |
| Organizations |      543 |               0 |           — |                           — |
| Exhibits      |    5,894 |               0 |           — |           2,357 identifiers |

- Total rows: 16,412 (14,214 verified, 2,198 review-required, 0 rejected).
- Rules: witness code 5,175; exhibit identifier 5,894; organization name 318;
  organization acronym 225; person role-qualified label 2,602; person
  honorific label 2,194; person shared surname 4.
- Anchors: page text 11,236; transcript segment text 376; speaker label 4,800.
- Language: en 13,961; sq 2,451. There are 13 version-language metadata
  conflicts (for example, a `/sqi` version recorded as `en`). The version marker
  is used, and the metadata is left as it is and reported here.
- Coordinates: every row has version + character range; 2,978 verified rows
  carry transcript lines; 439 page-anchored verified rows carry a paragraph
  number (the rest are mostly footnote citations; paragraph stays NULL).
- The four `Smith` counsel rows remain `review_required`
  (`person.speaker_label.shared_surname`).
- 15,024 legacy Phase 17C rows were superseded (backup taken before migration).
- "Search-only" counts lexical hits in public body text that no persisted
  mention covers. For people, this is whole-word surname hits, which include
  ordinary words such as "Young" and "Quick". For witnesses, it is lowercase or
  otherwise non-canonical forms of registered codes.

### Checks

| Check                                                                              | Result                               |
| ---------------------------------------------------------------------------------- | ------------------------------------ |
| Provenance violations (anchor missing, non-public, slice ≠ text, bad rule/version) | 0                                    |
| Protected-witness identity violations (witness row text not code-only)             | 0                                    |
| Deduplication conflicts (same span → two entities of one kind, verified)           | 0                                    |
| Review-state violations (state ≠ rule's declared state or flag mismatch)           | 0                                    |
| Legacy (rule-less) rows remaining                                                  | 0                                    |
| Idempotency: second run, identical ids/spans/states (content hash)                 | identical                            |
| Seeded sampling re-derivation, 100 per kind (seed 19), threshold 1.0               | 100/100 each                         |
| Exhibit status after projection                                                    | admitted 3 · unknown 978 (unchanged) |
| Phase 17C gate after supersession                                                  | PASS                                 |

The sampling check is **automated**: it re-runs the rules on the stored anchor
text. It proves the rows are reproducible and have exact provenance. It does
not prove semantic precision against the PDF. The roadmap §12 human sampling
audit is still open.

### Tests

- Unit: `tests/unit/ingestion/test_verified_mentions.py` (8 tests, including
  negative cases: unknown codes, near-miss identifiers, lowercase acronyms,
  shared variants, surname-only and unregistered labels, non-unique paragraphs).
- Integration: `tests/integration/test_phase19a_mentions.py`. It covers
  idempotent re-projection, public-only and closed-session exclusion, no
  auto-created witnesses, no status inference, language precedence, the gate,
  and the mentions API (state filter, 404, `SEARCH_MATCH` on search).
- Migration round-trip `0013` and `alembic check` (no drift).
- Web: `phase19.test.tsx` covers the mapper, and verified / review-required /
  search panels rendered separately.

Final checkpoint run: backend pytest 313 passed; frontend vitest 246 passed;
`make lint` (ruff, ruff format, eslint, prettier) and `make typecheck` (mypy
strict, tsc) pass. Real-data Playwright was not run in this pass.

### Open items for later passes

- Human sampling audit (≥100 per kind) against the source PDFs.
- 2,194 honorific counsel labels stay review-required until an official
  source records a full public name.
- 2,357 exhibit-shaped identifiers are not in the exhibit registry. They are
  not auto-created.
- Reader character-range highlighting and real-data Playwright (19D / 19E).

## Pass B — corpus intelligence and architecture (2026-09-24)

Result: **PASS**. There are 17 reconciliation invariants and all are zero; the
Phase 19A gate also passes. The full report is `PHASE19_DATA_QUALITY.md`, and
the manifest is `manifests/phase19b-corpus-intelligence.json`.

After Pass B, the verified-mention totals are 19,137 rows (16,939 verified,
2,198 review-required). This includes 2,725 `person.full_name.exact` mentions of
source-backed full names. The Pass A manifest has been regenerated to match.

Targeted verification:

- `tests/unit/ingestion` (173). Phase 19B rules are covered in
  `test_phase19b_rules.py`: identity, headers, exhibit status, resolver helpers,
  and their negative cases.
- `tests/integration/test_phase19b_intelligence.py` (3): idempotent pipeline,
  provenance checks, resolver rules against a real alias index, and API cursor,
  provenance and endpoints.
- Existing suites touching changed code: migrations round-trip `0014`, database
  head, Phase 8 resolution, Phase 9 evidence, read API, 19A mentions,
  constraints, model/contract/mapper unit tests.
- `ruff`, `ruff format --check`, `mypy --strict`, `alembic check`.

The full frontend/backend suites and browser suites were not rerun, by design
for this pass.

## Pass C — final review and application integration (2026-09-25)

Scope: a review of the held corpus plus the four quarantined corpus-04 records.
No new acquisition. Evidence: `manifests/phase19c-review.json`, and the
refreshed `manifests/phase19b-corpus-intelligence.json` and
`manifests/phase19a-verified-mentions-quality.json`. Full narrative:
`PHASE19_DATA_QUALITY.md` → "Phase 19C".

Result: **PASS; Phase 19 closed** after the operator-approved integrity cleanup.

### Gates

| Gate                               | Result                                                        |
| ---------------------------------- | ------------------------------------------------------------- |
| `report-phase19b` (17 invariants)  | PASS, all 0                                                   |
| `gate-phase19a`                    | PASS: 26,693 rows, 0 provenance violations, 0 dedup conflicts |
| Relationship evidence (full table) | 0 edges without exactly one evidence basis                    |
| Sampling audit                     | 1 systematic false positive found and fixed (other-court ids) |

### Tests (focused, plus one backend run for the cross-cutting changes)

- `make lint` and `make typecheck`: pass.
- Backend `pytest` (unit + integration): 329 passed.
- Frontend `vitest`: 256 passed.
- Real-data Playwright (`E2E_REAL_DATA=1`, desktop + Pixel 7): `phase19.spec.ts`
  8/8 and `phase18.spec.ts` 28/28. The phase18 spec's stale "Source
  occurrences" expectation (renamed in 19A) was updated.
  `routes` / `accessibility` / `phase15`: 56 passed, 62 mock-only skipped.

### Application integration

- **Dossiers.**
  - Witness and person dossiers show hearings with a recorded public
    appearance: hearing, transcript version, header pages, session page
    counts, verbatim examination headers and the exact header source.
  - Exhibit dossiers show the status history with the court statement behind
    each event. `UNKNOWN` is shown as a state, never inferred.
- **Relationships.** Dossier relationship panels, the Reader context panel and
  the Network screen read `/network/edges`. That brings in MENTIONED_IN and
  TESTIFIED_AT edges, which the citation-only `/network` never returned. Each
  row carries its evidence kind, `evidence_count` and `ProvenanceRead`.
- **Network.** Reads are bounded (100 per page), filtered server-side by
  relationship type and evidence kind, and cursor-paginated. The unfocused
  view is one labelled page, not a graph dump.
- **Evidence Path.** Hops now carry `ProvenanceRead` too, so one exact-source
  contract serves dossiers, Reader, Network and Path.
- **Reader.** It marks the verbatim slice, whole-token and within the
  targeted paragraph. When the span lies outside the rendered paragraphs
  (running header, heading), it says so and shows the verbatim text.
- **States.** VERIFIED · SEARCH MATCH · REVIEW REQUIRED · AMBIGUOUS · UNKNOWN
  are text labels in EN and SQ. A search match is never shown as verified.

### Integrity cleanup (operator-approved)

- **Withdrawn exhibits.** 12 exhibits withdrawn with audit rows; not
  recreated.
- **Other-case guard.** It now accepts binding punctuation, which brings
  `invalid.other_case` to 453 and includes "KSC-BC-2020-05, F00494"-style
  references.
- **Stale citations.** Re-resolution retires stale, unreviewed, unreferenced
  citations with an audit row (1 retired).
- **Gates.** `report-phase19b` PASS (all 17 checks 0); `gate-phase19a` PASS.
- **Focused tests.** 241 passed: ingestion units, and the Phase 8 / 19A / 19B /
  ingestion-pipeline / constraints / read-API integration suites. Ruff and
  mypy are clean.

### Exhibit sub-number fix and closeout

- **The fix.** Citations keep the exhibit sub-number ("P01136.1" is not
  P01136). 2,038 truncated rows were retired together with their 2,035 derived
  CITED_IN edges, and 118 orphaned base exhibits were withdrawn with approval.
- **Final gates.** `report-phase19b` PASS (all checks 0) and `gate-phase19a`
  PASS (0 provenance violations). The full-table integrity checks are all 0.
- **Targeted tests.** 248 passed: ingestion unit tests, and the Phase 8 /
  19A / 19B / evidence / constraints / read-API / ingestion-pipeline /
  migration integration suites. Ruff and mypy are clean.
- **Browser suites.** The Playwright suites were not re-run for the last two
  changes, which are ingestion-only; the last real-data run passed 36/36 on
  desktop and Pixel 7.
