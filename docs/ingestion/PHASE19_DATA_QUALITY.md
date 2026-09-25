# Phase 19 — Pass B data quality and architecture report

Snapshot: 2026-09-24. Case `KSC-BC-2020-06`, known public corpus (no acquisition
in this pass; see "Corpus batch" below). Machine-readable source:
`manifests/phase19b-corpus-intelligence.json` (`ksc-ingest report-phase19b`).
Capture plan: `manifests/phase19-corpus-04-strata.json`.

Reconciliation gate: **PASS** (17 invariants, all zero; Phase 19A gate PASS).

## Corpus coverage

116 logical documents / 134 versions / 16 hearings.

| Year    | Transcripts | Decisions / orders | Party & registry filings | Appeal / subcase | Annex |
| ------- | ----------: | -----------------: | -----------------------: | ---------------: | ----: |
| 2020    |           – |                  2 |                        – |                – |     – |
| 2021    |           3 |                  1 |                        3 |                5 |     – |
| 2022    |           2 |                  4 |                        6 |                – |     – |
| 2023    |           4 |                  2 |                       10 |                2 |     – |
| 2024    |           3 |                  2 |                       12 |                – |     – |
| 2025    |           1 |                  – |                        – |                5 |     – |
| 2026    |           3 |                 11 |                       26 |                4 |     – |
| undated |           – |                  – |                        – |                – |     5 |

Findings:

- **2025 is the thinnest year**: 1 transcript, no main-case decision or party
  filing. 2020–2022 are also thin. 2026 (closing phase) holds 38% of documents.
- **Trial evidence is under-represented.** Only 4 of 16 hearings are trial
  hearings with witness evidence. The other 12 are status, preparation, opening
  or closing sessions. The trial ran for hundreds of hearing days.
- **Party filings have no Albanian counterparts** (0 of 57). Decisions have 4 of
  22, transcripts 13 of 16. SQ-only records: 7.
- **Parties**: defence 34, court 29, SPO 22, unstated 22, other 6, victims'
  counsel 3.
- **Extraction weaknesses**: 3 versions still require parse review
  (`F00002/A03`, `T/2024-04-29`, `T/2024-04-30/sqi`); 8 pages have no text;
  every transcript segment has line coordinates.

## Entity coverage and identity

| Entity            | Registered | Verified mention | Other                                        |
| ----------------- | ---------: | ---------------: | -------------------------------------------- |
| People            |         49 |               11 | 38 people have review-required mentions only |
| Witnesses (codes) |        201 |              201 | 2 with a recorded appearance                 |
| Organizations     |          6 |                6 | presence only                                |
| Exhibits          |        981 |              860 | 5 with status events; 1 admitted             |

Identity basis for the 49 people:

- 5 with a source-backed full name: the four accused from the case caption,
  plus 1 publicly named witness from a transcript header.
- 6 role-qualified speaker labels (judges).
- 38 surname-level labels (counsel). These stay REVIEW_REQUIRED.

Identity states now live in one module (`identity.py`):

- VERIFIED;
- REVIEW_REQUIRED;
- AMBIGUOUS (never assigned);
- SEARCH_ONLY (never stored).

The four `Smith` counsel rows remain review-required. The caption binder refuses
to bind in three cases: another case's caption, a repeated surname, and a
homoglyph spelling (Cyrillic `ҫ` in 11 cover pages).

## Verified mentions

19,137 rows (16,939 verified, 2,198 review-required). The new rule
`person.full_name.exact` adds 2,725 verified person mentions in body text, for
example "Hashim Thaçi" and "Jakup KRASNIQI". It matches only recorded spellings,
whitespace-tolerant, whole-token. Speaker labels are unchanged.

## Witness / hearing coverage

The appearance signal is the transcript's own page header (`Witness: W03877
(Private Session) Page 15003 Examination by Mr. Capin`). Rows are stored per
transcript version:

| Subject                | Hearing    | EN pages      | SQ pages | Sessions (EN)        |
| ---------------------- | ---------- | ------------- | -------- | -------------------- |
| W03877                 | 2024-04-29 | 14,987–15,071 | 4–102    | 4 open / 73 private  |
| Nuredin Abazi (public) | 2024-04-29 | 15,077–15,120 | 107–157  | 42 open              |
| Nuredin Abazi (public) | 2024-04-30 | 15,135–15,242 | 14–139   | 103 open / 2 private |
| W04371                 | 2024-04-30 | 15,245–15,261 | 142–160  | 17 closed            |
| W04371                 | 2024-05-01 | 15,266–15,344 | 4–93     | 75 closed            |

- **Totals:** 10 appearance rows, covering 3 hearings with a recorded public
  appearance and 5 TESTIFIED_AT edges.
- **Nothing bridged or read:** pages without the header are not bridged, and
  private or closed content is never read.
- **Named witness:** the witness named in the header became a public person. No
  witness code was invented for them, and no code is linked to them.
- **Examinations:** examination headers are kept verbatim ("Cross-examination by
  Mr. Misetic").

## Exhibit status coverage

`exhibit_status_events` keeps a history of explicit court-record statements. Only
the bench or the court officer can produce an event:

- 16 `number_assigned` events (8 bound to a registered exhibit), with
  classification where stated;
- 7 `admitted` events (3 bound).

Status is derived from these events, and `admitted_date` is never inferred. The
statement date is the hearing date, which may be later than the admission itself.

The Phase 17 proximity heuristic was retired after a demonstrated false
positive: `P01355` had been "admitted" because a nearby sentence read "Mr. Zyrapi
admits a number of facts". With the heuristic gone:

- P01136 and P01355 → `unknown`;
- P01137 → `admitted` (bench: "Proofing Note 1 was admitted as Exhibit P01137").

Sub-numbers (`P01136.1`–`.4`) and one transcript typo (`P00136.1`) are stated by
the court but are not in the registry. They are kept verbatim and unbound.

## Relationship types

| Type         | Evidence            |  Edges | Evidence anchors |
| ------------ | ------------------- | -----: | ---------------: |
| CITED_IN     | citation            | 10,555 |           10,555 |
| MENTIONED_IN | verified occurrence |    596 |            3,268 |
| TESTIFIED_AT | witness appearance  |      5 |               10 |

- **Evidence contract:** every edge now has exactly one evidence anchor, enforced
  by the CHECK `num_nonnulls(citation, occurrence, appearance) = 1`. It also
  carries an `evidence_count` (a count, never a weight).
- **What produces no edge:** speaker labels, co-occurrence and proximity.
- **What an edge never implies:** MENTIONED_IN records presence only. It never
  states institutional responsibility, membership or involvement.

## Citation failure classes

Every terminal state now records a machine-readable `resolution_rule`.

| State      | Rule                                        |  Count |
| ---------- | ------------------------------------------- | -----: |
| resolved   | identifier.exact                            | 10,299 |
| resolved   | identifier.zero_padded (`P1070` = `P01070`) |    166 |
| resolved   | transcript.page_range / page_line           |     69 |
| resolved   | transcript.hearing_date (`T.20240429`)      |     29 |
| ambiguous  | subcase_bare_filing                         |    157 |
| unresolved | transcript_page_not_held                    |  2,621 |
| unresolved | target_not_held                             |  2,456 |
| unresolved | transcript_date_not_held                    |  1,296 |
| unresolved | malformed_transcript_reference              |     22 |
| unresolved | version_not_held                            |     14 |
| invalid    | other_case / line_grid / coordinate_missing |    141 |

Two correctness defects were found and fixed:

1. **Annex alias.** The bare alias `F00002` pointed at annex `F00002/A01`
   (annexes carry the base filing number). As a result, 7 citations of base
   filings resolved to an annex. They are now unresolved, because the base
   filing is not held.
2. **Subcase context.** Bare `F#####` inside appeal/subcase filings (IA/PL) had
   resolved into the main case. 13 were resolved that way and 144 were
   unresolved; all 157 are now AMBIGUOUS, with both candidates recorded.

Where the unresolved citations come from:

- **Concentration:** two sources account for 63% of all unresolved citations.
  The Final Trial Brief `F03667/COR/RED` has 2,660 and `F03668/RED2` has 1,385.
  Both cite unheld trial-transcript pages and filings.
- **Unheld targets:** 548 distinct unheld filings and 160 distinct unheld
  hearing dates.
- **Most-cited unheld filings:** F03699, F00777, F00455, F00026, IA003/F00005.
- **Most-cited unheld hearing dates:** 2024-07-10, 2024-07-15, 2024-12-03,
  2024-12-02.
- **No fuzzy resolution:** there is none, and no forced resolution of ambiguous
  citations.

## Provenance completeness

Every Phase 19 object answers "why" with the same contract (`ProvenanceRead`):
kind, rule, document, version, page / paragraph / line, character range, and text.

| Object                | Exact provenance                                   |
| --------------------- | -------------------------------------------------- |
| Verified mentions     | 100% (version + anchor + char range; slice = text) |
| Full-name aliases     | 100% (page + char range)                           |
| Witness appearances   | 100% (header page + exact span)                    |
| Exhibit status events | 100% (segment + line + span)                       |
| Typed edges           | 100% (exactly one evidence row)                    |
| Citation edges        | citation source version + char range               |

Differences that remain:

- **Citation character ranges:** they index the source text after running
  headers are blanked with equal-length spaces, so offsets are preserved.
- **Phase 9 events:** they still use source metadata rather than an occurrence.

## Language / version coverage

- **Variants:** BASE 64, RED 45, SQI 25, A01 3, RED2 2, COR 1.
- **Language/version mapping:** Albanian translations are versions of the same
  logical document (not separate documents). Annexes are separate documents
  whose reference proves their parent. No merge is made without that evidence.
- **Unused supersession:** `supersedes_version_id` is unset for every real-case
  version. RED → RED2 supersession is not asserted (no source states it).
- **Language metadata conflicts:** 13 versions whose official `/sqi` marker
  contradicts the recorded language. The marker wins; the metadata is reported,
  not rewritten.

## Most important remaining structural weaknesses

1. **Held trial evidence is thin.** 4 trial hearings, 2 coded witnesses with an
   appearance, 1 admitted exhibit. Acquisition, not inference, is the fix.
2. **Counsel identity.** 38 people are surname-level. No official source in the
   corpus records their full names.
3. **Exhibit sub-numbers.** `P01136.1` has no registry row or parent link. It
   needs an explicit, source-backed exhibit-part model.
4. **The Reader ignores exact spans.** It navigates to page/line, but does not
   yet highlight the character range (19D).
5. **Language coverage.** No Albanian counterpart for party filings.
6. **The UI does not consume the new APIs yet.** Appearances, status history and
   the network edges service are available but not shown (19D).

## Corpus batch (acquisition)

No batch was acquired in this pass. The official repository answers automated
clients with a Cloudflare challenge. The lawful path is the operator-attached
browser (ADR-011, `docs/ingestion/OPERATOR_CAPTURE.md`), and no operator session
was available.

The gap-driven plan is ready: `manifests/phase19-corpus-04-strata.json`. It asks
for up to 70 records plus up to 6 Albanian counterparts:

- 45 of the most-cited unheld main-case filings;
- the transcripts of the 15 most-cited unheld hearing dates;
- 11 filings from 2025.

Run it through the new collector flag:

```bash
pnpm exec node scripts/ksc_operator_browser_capture.mjs --attach \
  --strata docs/ingestion/manifests/phase19-corpus-04-strata.json \
  --bundle-id 2026-09-25-corpus-04 --target-new 90 --max-total 100 \
  --output ~/Downloads/ksc-bc-2020-06-phase19-corpus-04
```

Then run `import-capture` → `parse` → `reresolve` → `build-evidence` →
`build-intelligence` → `report-phase19b`.

## Before / after (this pass, no new records)

| Measure                           | Before |   After |                                             Δ |
| --------------------------------- | -----: | ------: | --------------------------------------------: |
| Citations resolved                | 10,395 |  10,570 |                                          +175 |
| Citations ambiguous               |      3 |     160 |                                          +157 |
| Citations unresolved              |  6,742 |   6,410 |                                          −332 |
| Citations invalid                 |    141 |     141 |                                             0 |
| CITED_IN edges                    | 10,380 |  10,555 | +175 (10,360 ids kept, 20 removed, 195 added) |
| MENTIONED_IN / TESTIFIED_AT edges |  0 / 0 | 596 / 5 |                                          +601 |
| Graph nodes                       |  1,272 |   1,311 |                            +39 (none removed) |
| People / full-name aliases        | 48 / 0 |  49 / 5 |                                       +1 / +5 |
| Witness appearances               |      0 |      10 |                                           +10 |
| Exhibit status events / admitted  |  0 / 3 |  23 / 1 |                                      +23 / −2 |
| Verified mentions                 | 14,214 |  16,939 |                                        +2,725 |
| Review-required mentions          |  2,198 |   2,198 |                                             0 |

## Acquisition checkpoint — batch `2026-09-25-corpus-04`

The batch was captured through the operator-attached browser (ADR-011). The
operator passed the Cloudflare check; the collector then made only ordinary
navigations, with 0 challenges during the run. Manifest:
`manifests/phase19-corpus-04.json` (metadata only; bytes live in object storage
by SHA-256).

Two collector defects found and fixed before the successful run:

- **Filing-number filter.** The public form matches digits only (`03667`).
  `F03667` returns nothing, which is why every lead in corpus-03 had silently
  captured nothing.
- **Hearing dates.** These now use the form's own date range. Paging oldest-first
  could not reach 2024 within the page budget.

| Stage                                        |                                               Count |
| -------------------------------------------- | --------------------------------------------------: |
| Selected by the ranked strata                |         67 (66 new, 1 counterpart of a held filing) |
| Filing leads captured                        | 37 of 45 (8 had no public English non-annex record) |
| Hearing-date transcripts captured            |                                            15 of 15 |
| 2025 filings                                 |                                            11 of 11 |
| Albanian counterparts                        |                                                   6 |
| Duplicates of held records                   |                                                   0 |
| Accepted, stored, parsed, indexed            |                                                  63 |
| Quarantined for human review (not persisted) |                                                   4 |
| Failed downloads / hash mismatches           |                                                   0 |

The 4 quarantined records:

- 3 records with no official reference: the records listed under leads F01534
  (an annex), F03176 and F02426.
- 1 Albanian F00026 translation, whose PDF header
  `KSC-BC-2020-06/F00026/RED/sqi/COR` contradicts its published ID
  `F00026RED`.

The pipeline does not derive references, so these wait for a human.

Two ingestion defects were found and fixed:

1. **Repeated printed page numbers.** A reclassified filing (`F02198`) stamps
   "1 of 8" on every page. Repeated printed numbers are now withheld: the pages
   keep their exact PDF index and the version is flagged for review. Before the
   fix this aborted the parse run.
2. **Phase 17 builder state.** The builder wrote review-required legacy rows
   without the Phase 19A state, which the consistency CHECK rejected.

Reconciliation ran in this order: `parse` → `reresolve` → `build-structured`
(registries) → `reresolve` → `build-evidence` → `build-intelligence` →
`report-phase19b` / `gate-phase19a`. Both gates pass: all 17 invariants are 0,
with 0 provenance violations and 0 duplicate conflicts.

### Corpus before / after

| Measure             |     Before |       After |           Δ |
| ------------------- | ---------: | ----------: | ----------: |
| Source records      |        135 |         202 |         +67 |
| Documents           |        116 |         173 |         +57 |
| Versions            |        134 |         197 |         +63 |
| Bytes               | 79,311,530 | 118,310,439 | +38,998,909 |
| Pages               |      5,725 |       8,943 |      +3,218 |
| Transcript segments |      8,547 |      15,171 |      +6,624 |
| Hearings            |         16 |          31 |         +15 |

### Intelligence before / after

| Measure                                |           Before |                                   After |
| -------------------------------------- | ---------------: | --------------------------------------: |
| Verified mentions                      |           16,939 |                                  22,322 |
| Review-required mentions               |            2,198 | 4,373 (new surname-only counsel labels) |
| People                                 |               49 |     62 (8 new publicly named witnesses) |
| Witness codes                          |              201 |                                     212 |
| Witness appearance rows                |               10 |                                      26 |
| Hearings with a recorded appearance    |                3 |                                      18 |
| Exhibits                               |              981 |                                   1,032 |
| Exhibit status events / admitted       |           23 / 1 |        31 / 2 (P01277, bench statement) |
| Organizations                          |                6 |                                       6 |
| CITED_IN / MENTIONED_IN / TESTIFIED_AT | 10,555 / 596 / 5 |                     13,124 / 1,022 / 21 |

### Citations before / after

| State      | Before |                                     After |
| ---------- | -----: | ----------------------------------------: |
| Resolved   | 10,570 |                                    13,142 |
| Ambiguous  |    160 |                                       194 |
| Unresolved |  6,410 |                                     6,308 |
| Invalid    |    141 | 218 (mostly citations of other KSC cases) |

Newly resolved by rule:

- hearing-date transcript citations: 29 → 548;
- transcript page ranges: 62 → 510;
- zero-padded identifiers: 166 → 257.

### Coverage after the batch

- **Trial hearings:** 4 → 19. Hearings by year: 2021 3, 2022 2, 2023 6,
  2024 15, 2025 2, 2026 3.
- **2025 main case:** 2 decisions, 10 party filings and 2 transcripts. Before
  this batch it had 0, 0 and 1.
- **Languages:** documents with both EN and SQ went 18 → 24. Party filings still
  have no Albanian counterpart (0 of 77).
- **Parse review:** 5 versions need it (`F00002/A03`, `F02198`, `T/2024-04-29`,
  `T/2024-04-30/sqi`, `T/2024-07-15`).

## Phase 19C — final review (2026-09-25)

A review of real records, not a new acquisition. Machine-readable evidence:
`manifests/phase19c-review.json`, plus the refreshed
`manifests/phase19b-corpus-intelligence.json` (report PASS, 17 invariants 0) and
`manifests/phase19a-verified-mentions-quality.json` (gate PASS, 0 provenance
violations, 0 dedup conflicts).

### Quarantine review

Each record was checked against its captured detail page and the running
header of every PDF page. All four are **ACCEPT**. Each one rests on two
official signals that agree, and each rule is narrow and unit-tested:

| Record | Adopted version                    | Why it had failed                            | Deciding evidence                                                                                            |
| ------ | ---------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| r11    | `F01534/A02/RED`                   | Title "Public Redacted Version of ANNEX 2 …" | Record type _Filing Annex_; header `F01534/A02/RED` on 224/224 pages                                         |
| r12    | `F03176/COR2/RED`                  | `COR2` was not a suffix token                | Header `F03176/COR2/RED` on 33/33 pages; classification Public                                               |
| r20    | `F02426/CONF/RED` (reclassified)   | `CONF` was not a suffix token                | Header on 8/8 pages; court stamp "Reclassified as Public … CRSPD546". `CONF` without that stamp fails closed |
| r63    | `F00026/RED/sqi/COR` (translation) | Header extends the published id with `/COR`  | Header on 239/239 pages; published title ends "- COR"; "Date corr. translation 24/02/2022"                   |

- **Import:** the bundle was re-derived, and only these four records changed;
  all 63 other records and every hash are identical. Resumed ingestion
  downloaded 4 artifacts with 0 failures.
- **Quarantine rows:** set to `released`, with reviewer, date and the adopted
  reference.
- **Still open:** one quarantine item, the Phase 17 `F03734`, which is out of
  scope.

### Parse-review versions

| Version            | Result          | Cause                                                                                |
| ------------------ | --------------- | ------------------------------------------------------------------------------------ |
| `F00002/A03`       | REVIEW_REQUIRED | The page 2 text layer is drawn twice ("`2 ofof 55`"). The printed page can't be read |
| `F02198`           | REVIEW_REQUIRED | Source defect: the stamp prints "1 of 8" on every page. The PDF index is kept        |
| `T/2024-04-29`     | REVIEW_REQUIRED | 8 image-only pages (JPEG, no text layer). No OCR                                     |
| `T/2024-04-30/sqi` | resolved        | p. 112 is a private-session page with an empty 1–25 line grid (parser v3)            |
| `T/2024-07-15`     | resolved        | p. 69 is the same case (parser v3)                                                   |

The v3 reparse updated rows in place under stable ids. It changed no segment
count (15,171).

### Human sampling audit

Each sample was traced along this chain:

1. structured row;
2. evidence row;
3. version;
4. page / paragraph / line / char range;
5. the exact slice of the stored text;
6. the same text on that PDF page of the original bytes, located by SHA-256;
7. a reading of the surrounding context.

| Object                      | Checked | Result                                                                |
| --------------------------- | ------- | --------------------------------------------------------------------- |
| Person (full name, speaker) | 10      | 10/10 slice, PDF page and token boundary                              |
| Person review-required      | 5       | Surname-level counsel labels, correctly not verified                  |
| Organization                | 8       | 8/8                                                                   |
| Witness code                | 6       | 6/6 slice and PDF page; code only                                     |
| Exhibit occurrence          | 8       | **1 false positive** (see below)                                      |
| Witness appearance          | all 26  | 26/26 slice, PDF page and hearing date                                |
| Public named witness        | all 9   | Header-backed; none linked to a code                                  |
| Exhibit status event        | all 31  | 31/31 slice; bench or officer only                                    |
| CITED_IN / MENTIONED_IN     | 8 + 8   | All pass; full-table direction, anchor and count checks: 0 violations |
| TESTIFIED_AT                | all 21  | Subject, hearing and `evidence_count` all correct                     |

**False positive, fixed.** "IT-04-84 P00340" in `F01475/RED` is an exhibit of
the ICTY _Haradinaj_ case, not this case's `P00340`. The defect was
systematic: 177 identifiers printed right after another court's case number had
become this case's verified exhibit mentions, resolved citations and CITED_IN
edges.

- A bare identifier immediately after another court's case number (ICTY /
  ICTR / MICT / STL / ICC / SCSL, or another KSC case) is now
  `invalid.other_case`. The exhibit rule is now `exhibit.identifier.exact` v2.
- Only whitespace may separate the two. "IT-04-84bis, P00119", with a comma,
  still binds; that is a residual risk.
- No finding, appeal, AI or research-note row referenced the 177 citations.

**False negative (conservative).** The bench said "admitted as P1277 and
P189". P189 is not captured.

### Other defects fixed

- **Language marker.** `version_language()` honoured `/sqi` only as a suffix,
  so the corrected translation `…/RED/sqi/COR` was labelled English
  (27 mentions). The marker is now matched as a path segment.
- **Reader coordinates.** When a link carried both `pdfPage` and a printed
  `page`, the Reader started from the printed page but filtered by PDF index.
  Every exact-source link opened one page off where the two numberings differ.

### Final policy checks

- **Person identity.** Full names come only from the case caption (4) and
  transcript witness headers (9), each with an exact span. The 101 rule-less
  aliases are exact speaker labels held in transcripts. The four `Smith`
  shared-surname rows stay REVIEW_REQUIRED. No witness code is linked to a
  person.
- **Citations.** No bare F-number resolves to an annex, and none cited in a
  subcase resolves. All 194 ambiguous rows keep their candidates. No
  non-resolved row has a target. Every resolver-produced state carries a rule.
  The 7 hand-verified Phase 10/12 citations carry their reviewer instead.
- **Versions.** No `supersedes_version_id` is set, and no RED → RED2 is
  inferred. The 6 annexes are separate documents.
- **Language marker conflicts.** There are now 20, up from 13. All are `/sqi`
  translation versions of documents whose recorded language is the English
  original. Each has its English sibling on the same logical document, and the
  marker wins.

### Integrity cleanup (operator-approved, 2026-09-25)

- **Withdrawn exhibits.** 12 exhibit rows that existed only from other-court
  identifiers: `P00050`, `P00064`, `P00082`, `P00119`, `P00126`, `P00161`,
  `P00240`, `P00248`, `P00340`, `P00803`, `P00931` and `P02662`.
  - Re-verified first: the selection was exactly these 12, with 0 relationships,
    0 status or description data, and 0 live citations naming them.
  - One `audit_log` row per exhibit (`exhibit.withdrawn`, reason
    "other-case contamination / invalid case binding").
  - Their `record_identifiers` and `graph_nodes` cascaded.
  - `build-structured` did not recreate them.
- **Root cause.** The other-case guard now accepts _binding_ separators:
  - whitespace;
  - one comma or colon ("IT-04-84bis, P00119");
  - parentheses on either side.

  A semicolon starts a new citation and is not binding. The exhibit mention
  rule is now v3. The same rule also caught the standard KSC style
  "KSC-BC-2020-05, F00494" (the _Mustafa_ trial judgment) and
  "KSC-CC-2022-13, F00001". These had resolved to, or been counted as, this
  case's F00494 / F00001 / IA003/F00005. `invalid.other_case` is now 453.

- **Stale citation.** Re-resolution now retires a citation it no longer
  extracts, but only when that row is:
  - unreviewed, and
  - unreferenced by any of the 17 referencing columns.

  Each retirement writes an `audit_log` row (`citation.retired`). Curated,
  reviewed or referenced rows are kept. One row was retired
  (`IA042/F00005/RED`, "F00005").

- **Checks after reconciliation, all 0.** Withdrawn exhibits reappearing;
  exhibits or witness codes without any case-local support; exhibit citations
  resolved after a foreign case number; edges on unverified occurrences;
  edges without exactly one evidence basis; non-resolved citations with a
  target. The one edge on an unresolved citation is the synthetic
  `KSC-DEMO-0000` fixture.

### Final counts (database, case-scoped, after the cleanup)

| Measure                                               | Phase 19B                  | Final 19C                  |
| ----------------------------------------------------- | -------------------------- | -------------------------- |
| Documents / versions                                  | 173 / 197                  | 176 / 201                  |
| Bytes                                                 | 118,310,439                | 125,250,466                |
| Pages / transcript segments                           | 8,943 / 15,171             | 9,447 / 15,171             |
| Exhibits (admitted) / status events                   | 1,032 (2) / 31             | 1,020 (2) / 31             |
| Verified / review-required mentions                   | 22,322 / 4,373             | 22,320 / 4,373             |
| Appearances / hearings with appearance                | 26 / 18                    | 26 / 18                    |
| CITED_IN / MENTIONED_IN / TESTIFIED_AT                | 13,124 / 1,022 / 21        | 13,089 / 1,042 / 21        |
| Citations resolved / ambiguous / unresolved / invalid | 13,142 / 194 / 6,308 / 218 | 13,107 / 183 / 6,221 / 526 |

- The people (62), witness codes (212), organizations (6) and hearings (31)
  counts are unchanged.
- Citations total 20,037.
- CITED_IN = 13,100 machine-resolved citations − 12 self-citations + 1 curated
  edge.

### Open

- **Decision required: exhibit sub-numbers.** 2,035 of 5,351 resolved exhibit
  citations, and the same number of CITED_IN edges, bind a sub-numbered
  reference ("P00099.1") to the base exhibit P00099. The citation extractor
  keeps the base prefix, while the mention and status rules leave sub-numbers
  unbound. 118 exhibit registry rows are supported only by such references.
  A fix re-resolves about 2,035 citations and leaves those 118 rows
  unsupported.
- **Known gaps.**
  - 3 parse-review versions (source defects / image pages).
  - "P189" in "admitted as P1277 and P189" is not captured.
