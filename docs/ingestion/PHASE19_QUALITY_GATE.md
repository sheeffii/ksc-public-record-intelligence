# Phase 19 quality gate

Phase 19 is **IN PROGRESS**. This file records each pass's checkpoint evidence.
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
