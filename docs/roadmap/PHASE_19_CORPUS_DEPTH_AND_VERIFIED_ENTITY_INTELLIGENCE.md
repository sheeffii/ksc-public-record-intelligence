# Phase 19 — Corpus Depth & Verified Entity Intelligence

**Status:** IN PROGRESS — 19A, 19B (with the corpus-04 batch) and the 19C final review are recorded (2026-09-25); the approved integrity cleanup is done; closeout awaits the operator decision on exhibit sub-number bindings (see `docs/PROJECT_STATE.md`).

## Goal

Deepen the public `KSC-BC-2020-06` record and turn entity presence from
"search matched this text" into **verified, coordinate-exact entity mentions**,
while keeping every Phase 7–18 guarantee: provenance, privacy and fail-closed
behaviour.

```text
MORE PUBLIC DATA
+ VERIFIED ENTITY MENTIONS
+ WITNESS ↔ HEARING LINKAGE
+ SAFER, BROADER CITATION RESOLUTION
+ SCALABLE PROVENANCE NETWORK
```

## Starting baseline (Phase 18 close, `1cb4cc4`, tag `phase-18-complete`)

| Measure | Value |
|---|---|
| Source records / documents / versions | 135 / 116 / 134 |
| Pages / paragraphs / transcript segments | 5,725 / 3,133 / 8,547 |
| People / witnesses / organizations / exhibits | 48 / 201 / 6 / 981 |
| Hearings / events / relationships | 16 / 127 / 10,380 |
| Citations resolved / ambiguous / unresolved / invalid | 10,395 / 3 / 6,742 / 141 |
| `entity_occurrences` (migration `0012`) | person 4,800 (4 review-required) · witness 5,204 · exhibit 4,885 · organization 135 |
| `witness_appearances` | 2 |

Repository reality at the start of each pass wins over this table.

### Known gaps this phase addresses

- Dossiers list occurrences from lexical search, not from `entity_occurrences`.
- Witness hearing totals are withheld: `witness_appearances` is nearly empty.
- Four surname-only `Smith` occurrences remain review-required.
- Unfocused `/network` loads a bounded 500-edge default.
- 6,742 citations are unresolved, mostly because targets are outside the corpus.

## Core principle

A **verified mention** is a persisted row that says: *this exact character
range, in this exact source version, refers to this exact entity, by this
named deterministic rule*. Anything weaker is a **search match** and must be
labelled as one. The two are never merged in storage, API or UI.

## Passes

| Pass | Scope |
|---|---|
| 19A | Verified mention model hardening + deterministic extractors (people, witness codes, organizations, exhibits) + reconciliation |
| 19B | Witness ↔ hearing linkage |
| 19C | Balanced acquisition batch + reprocessing + safe citation-resolver improvements |
| 19D | API/UI consumption of verified mentions + scalable focused-network reads |
| 19E | Quality gate and closeout |

Each pass is a separate checkpoint. Do not start the next pass automatically.

## 1. Verified entity-occurrence projection

Extend `entity_occurrences`; do not create a parallel table.

- Every row keeps: `document_version_id`, optional `transcript_segment_id`,
  `pdf_page_index`, printed `page_number`, paragraph (add if missing),
  `line_from`/`line_to`, `char_start`/`char_end`, verbatim `occurrence_text`.
- Add `rule_id` + `rule_version` (which deterministic rule produced it) and
  `projection_run_id` for lineage and reproducible re-runs.
- Add `mention_state`: `verified` · `review_required` · `rejected`. Only
  `verified` rows are shown as mentions; `review_required` is visible as such;
  `rejected` is retained for audit and never displayed as a mention.
- `extraction_origin` stays `deterministic`; no model-generated rows.
- Missing coordinates stay NULL; a row without `char_start`/`char_end` and a
  source version is invalid and is not written.
- Re-projection is idempotent per `(source version, char range, entity, rule)`.

## 2. Deterministic person mentions

- Match only against recorded public names and `person_aliases` from official
  public sources, as whole-token, case/diacritic-aware exact matches.
- A full name or registered alias → `verified`.
- Surname-only, initials, or a string shared by more than one known person →
  `review_required`, never auto-assigned. The four `Smith` rows stay
  review-required unless a human reviewer with an official source resolves them.
- No fuzzy, phonetic or embedding match. No automatic person merging.
- Albanian/English spelling variants are separate recorded variants, never
  inferred.

## 3. Deterministic witness-code mentions

- Exact `W` + digits code pattern bound to an existing witness record.
- Protected witnesses: the code is the only identity. No name, role, location,
  age, relative, or co-occurring-text attribute is stored or inferred.
- A code that does not exist in the witness registry is recorded as
  unresolved, not auto-created as a witness.
- No co-occurrence analysis that could narrow a protected witness's identity.

## 4. Deterministic organization mentions

- Exact match against the organization's official name and recorded variants
  (for example `NATO`, `KLA`/`UÇK` only where recorded as variants).
- Acronyms that collide with ordinary words or other bodies →
  `review_required`.
- A mention records presence only. It never states institutional
  responsibility, membership, command or involvement.

## 5. Deterministic exhibit mentions

- Exact official exhibit identifiers (e.g. `P00003`, including registered
  ERN/prefix forms) bound to an existing exhibit.
- A mention never changes or implies exhibit status. `UNKNOWN` remains
  `UNKNOWN`; status only comes from an official record stating it.

## 6. Witness ↔ hearing linkage

Populate `witness_appearances` deterministically from public transcripts:

- Accept only explicit structural signals: a transcript witness heading or
  swearing-in/examination marker that states the witness code, on a hearing
  date, with transcript page/line coordinates.
- Store `hearing_id`, `transcript_id`, `testimony_date`, `page_from`/`page_to`
  and the source coordinate of the signal.
- A witness code merely mentioned in a transcript is a mention, not an
  appearance.
- Private-session gaps and redactions are never bridged or guessed.
- Hearing totals may be displayed only as a count of stored appearances, labelled
  as "hearings with a recorded public appearance", with each hearing linkable to
  its source. No estimates or extrapolations.

## 7. Balanced acquisition batch

Follow the Phase 7 and Phase 17 acquisition rules unchanged:

- official public KSC sources only; respect robots/terms; no bypass of
  Cloudflare, CAPTCHA, authentication or access controls; no guessed URLs;
  no confidential, ex parte or non-public material; no redaction reconstruction;
- declared batch manifest before acquisition; checksum, capture record and
  version handling as in Phase 17;
- balanced across filings, decisions, transcripts (both languages where
  public), with priority given to the most frequently cited unresolved targets
  and transcripts of hearings that have witness testimony;
- batch gate before any record is indexed; failures quarantine the batch.

Target size is set in the 19C manifest, not here; coverage claims stay
"known public corpus", never "complete".

## 8. Safe citation-resolver improvements

- Re-run resolution after acquisition; newly held targets may resolve.
- Add deterministic forms only (for example additional official filing-number
  and transcript-page formats), each covered by tests.
- A citation with more than one candidate stays `AMBIGUOUS`; a citation with no
  held target stays `UNRESOLVED`. No fuzzy or nearest-match resolution.
- Record before/after counts per state and per rule; any drop in resolved
  counts must be explained before the pass closes.

## 9. Scalable focused-network reads

- Keep `focus_ref` exact-match semantics (Phase 18B).
- Add server-side pagination/cursor for neighbourhood edges, a depth limit
  (default 1, maximum 2) and filters by relationship type, source category and date.
- Replace the unfocused 500-edge default with an explicit overview (for example
  hub nodes by edge count with a textual summary) or a required focus. Do not
  render the full graph at once.
- Optional derived edges from verified co-mentions are out of scope unless a
  later ADR defines them. Co-occurrence is never an evidentiary relationship.
- Every returned edge keeps its citation and source coordinates.

## 10. Provenance and reconciliation

- Each projection run records inputs (corpus manifest, parser version, rule
  versions), outputs (counts by entity kind and state) and a diff against the
  previous run.
- Reconciliation checks: every verified mention resolves to a live source
  version and valid coordinates; no protected witness row carries identity
  text beyond its code; count drift beyond the declared threshold blocks the
  pass.
- A source version that disappears or is superseded is handled by the Phase 17
  rules. Its mentions are retained for audit but no longer displayed as current.

## 11. API/UI consumption

- API: `GET /api/v1/{people|witnesses|organizations|exhibits}/{id}/mentions`
  with pagination, returning mention state, rule, and exact coordinates.
  Witnesses also get `/appearances`.
- UI: dossiers show **Verified mentions** (from the projection) separately from
  **Search matches** (from lexical search, labelled with match type). A
  review-required mention is shown with a review state, never as verified.
- Every row links to the Reader at the exact coordinate, and the Reader
  highlights the character range.
- Hearing totals appear only when backed by stored appearances (§6).
- Strings in `en.json`/`sq.json`; tokens only; Design System components.

## 12. Quality gates

- `make lint`, `make typecheck`, `make test` green. Migration round-trip and
  Alembic drift check pass.
- Extractor unit tests per rule, including negative cases (surname-only,
  colliding acronyms, unknown codes, redacted spans).
- Integration tests: idempotent re-projection; no protected-witness identity
  leakage; review-required never exposed as verified; no status inference.
- Sampling audit: at least 100 random verified mentions per entity kind checked
  against the source, with a recorded precision, and zero protected-witness
  violations tolerated. The threshold is declared in the 19A checkpoint.
- Citation state counts recorded before and after 19C.
- Real-data Playwright desktop + Pixel 7: dossier → verified mention → exact
  Reader coordinate; witness → appearance → transcript line; focused network
  pagination.
- Quality evidence recorded in `docs/ingestion/PHASE19_QUALITY_GATE.md` plus a
  JSON manifest.

## 13. Privacy and safety

Never:

- deanonymize protected witnesses or infer hidden identities;
- store or display any attribute of a protected witness beyond the code;
- merge ambiguous people automatically;
- infer exhibit status;
- infer guilt, wrongdoing, credibility, motive, coordination or responsibility,
  or add any field that could hold such a score;
- bypass Cloudflare, CAPTCHA or authentication, or access confidential, ex parte
  or non-public material;
- present a search match as a verified mention.

Protection state fails closed to the protected treatment.

## 14. Non-goals

- AI/LLM entity extraction, embeddings or fuzzy matching.
- New AI provider or OpenSearch.
- Exhaustive-corpus claims.
- Co-mention or proximity edges as evidence.
- Phase 16 deployment/alerting work.
- Redesigning Phase 18 screens beyond adding the mention/appearance surfaces.

## Acceptance criteria

- [ ] `entity_occurrences` carries rule, run and mention-state lineage. Every
  verified row has exact coordinates.
- [ ] Deterministic extractors for people, witness codes, organizations and
  exhibits, with review-required handling for ambiguity.
- [ ] `witness_appearances` populated only from explicit transcript signals.
  Hearing totals are shown only from stored appearances.
- [ ] One balanced official acquisition batch passes its batch gate.
- [ ] Citation re-resolution with before/after counts. No fuzzy resolution.
- [ ] Paginated, depth-bounded focused-network reads. The unfocused view no
  longer depends on a 500-edge default.
- [ ] Reconciliation and sampling audit recorded.
- [ ] Mentions/appearances APIs and dossier UI keep verified mentions and search
  matches visibly distinct.
- [ ] All quality gates pass on desktop and Pixel 7. Privacy/safety rules hold.

## Completion Record

- **Status:** —
- **Completion date:** —
- **Commits:** —
- **Tag:** `phase-19-complete` (not yet created)

## Stop condition

Never trade provenance, privacy or fail-closed behaviour for mention coverage or
corpus size.

## Completion report

```text
PHASE 19 STATUS
CORPUS DELTA
VERIFIED MENTIONS
PERSON / WITNESS / ORGANIZATION / EXHIBIT
REVIEW-REQUIRED
WITNESS ↔ HEARING
CITATION RESOLUTION
NETWORK
API / UI
RECONCILIATION / SAMPLING
PRIVACY / SAFETY
QUALITY GATES
KNOWN GAPS
COMMITS
TAG
NEXT
```
