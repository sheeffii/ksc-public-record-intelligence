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
