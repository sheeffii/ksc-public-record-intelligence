# Phase 20B transcript-native Reader checkpoint

> **Erratum (20C, 2026-09-25):** "All SourceAnchors" (74,026; 13 `TEXT_ONLY`)
> and the 20,037 citation overlays include 13 anchors from the synthetic
> `KSC-DEMO-0000` fixture (6 of them citations). Real case: 74,013 anchors,
> 0 `TEXT_ONLY`, 20,031 citation overlays. See `PHASE20_QUALITY_GATE.md`.

Date: 2026-09-25

Case: `KSC-BC-2020-06`

Status: **20B implementation checkpoint. Phase 20 remains IN PROGRESS, 20C has
not started, and no `phase-20-complete` tag exists.**

No record was acquired and no original artifact was modified. Phase 20A was
not redone: its idempotent projection was re-run once, only to prove that the
now-scoped delete leaves 20B anchors intact, and it reproduced the 20A
checkpoint exactly (58,855 anchors; 8,465 / 11,002 / 39,375 / 13 by
precision). Decision record: ADR-028. Migration: `0016`.

## What was built

| Area                | Implementation                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Transcript anchors  | `ksc-ingest project-transcript-sync` gives each of the 15,171 case transcript segments a `transcript_segment` SourceAnchor. Line boxes are stored only when the segment's own version has exactly one right-aligned printed line-number column (1..N, strictly descending), every segment line exists, and the words on those lines reproduce `speaker: text` whitespace-insensitively.         |
| Page-header context | `transcript_page_contexts` stores each page's official running header (`witness.transcript_page_header/1`): subject, session state, examination heading and exact page-text offsets. It is never used to name a speaker label.                                                                                                                                                                  |
| Reader API          | Version- and page-scoped: `/document-versions/{ref}/transcript`, `…/transcript/segments` (PDF page, printed page+line, segment, verbatim speaker, header subject, examination, text), `…/pages/{i}/context` and `…/source-search`.                                                                                                                                                              |
| Reader UI           | `SourceReader` has three layers. The **Source** layer is the original PDF and stays primary. **Structured text** shows verbatim segments or paragraphs. **Research context** holds page-local overlays in six tabs. On desktop the layers sit side by side and the text/context panels collapse. On mobile they are Source/Text/Context tabs, with metadata, search and navigation in a drawer. |
| Deep links          | `?version=…&pdfPage=…`, `&page=<T. page>&line=<n>`, `&segment=<id>` and `&anchor=<id>` resolve on the server against that version only. The URL follows navigation. A version switch remounts the Reader, so no page, focus or highlight crosses versions.                                                                                                                                      |
| Sync                | Transcript → PDF draws the segment's validated line boxes. PDF → transcript hit-tests only validated segment boxes.                                                                                                                                                                                                                                                                             |
| Honest states       | Each highlight states its kind, label and precision. Weaker precisions show the explicit fallback and its reason, with no box drawn. OCR-required pages show that no native geometry exists; the PDF page stays viewable and no OCR text is shown.                                                                                                                                              |

Not displayed, because the source does not state them: the parser's sticky
`examination_type`, and `speaker_role` values derived from labels. Speaker
labels appear verbatim. "THE WITNESS" is never mapped to the page-header
witness code.

## Data quality (actual counts, local corpus, 2026-09-25)

### Transcript segments

| Measure                                             |   Count |
| --------------------------------------------------- | ------: |
| Transcript segments (44 public transcript versions) |  15,171 |
| Segments with `EXACT_GEOMETRY`                      |  14,180 |
| Segments with `PAGE_AND_LINE`                       |     991 |
| Segments with `PAGE_ONLY`                           |       0 |
| Validated line regions                              | 113,487 |
| Transcript pages with a persisted printed header    |   2,519 |

The 991 `PAGE_AND_LINE` segments break down as follows: 804 closed/private
session (text withheld; never boxed), 157 no line grid on the page, 27 text
mismatches, 2 ambiguous grids and 1 missing line. Header pages break down as
646 protected witness codes (193 open / 255 private / 198 closed) and 1,873
pages whose official header prints a witness's name (1,731 open / 142 private).

### Overlays available to the Reader

"Served" means the row passes the same read filters as the page-context API:
a rule-lineaged mention, not human-rejected, the public typed-edge rule for
relationships, and a public version.

| Overlay                                 | EXACT_GEOMETRY | PAGE_AND_LINE |  PAGE_ONLY | TEXT_ONLY |      Total |
| --------------------------------------- | -------------: | ------------: | ---------: | --------: | ---------: |
| Person, VERIFIED                        |          2,134 |         5,935 |      1,528 |         0 |      9,597 |
| Person, REVIEW REQUIRED                 |              0 |         4,373 |          0 |         0 |      4,373 |
| Witness code, VERIFIED                  |          1,188 |            96 |      4,268 |         0 |      5,552 |
| Organization, VERIFIED                  |            588 |           220 |        143 |         0 |        951 |
| **Visible verified entity overlays**    |      **3,910** |     **6,251** |  **5,939** |     **0** | **16,100** |
| Exhibit overlays (VERIFIED mention)     |            260 |           225 |      5,735 |         0 |      6,220 |
| Citation overlays, resolved             |          1,570 |             0 |      9,496 |         4 |     11,070 |
| Citation overlays, UNRESOLVED / invalid |            498 |             0 |      8,284 |         1 |      8,783 |
| Citation overlays, AMBIGUOUS            |             12 |             0 |        171 |         1 |        184 |
| **Citation overlays**                   |      **2,080** |         **0** | **17,951** |     **6** | **20,037** |
| Relationship overlays (`CITED_IN`)      |          1,568 |             0 |      9,486 |         0 |     11,054 |
| Relationship overlays (`MENTIONED_IN`)  |            628 |           153 |        261 |         0 |      1,042 |
| Relationship overlays (`TESTIFIED_AT`)  |             19 |             0 |          2 |         0 |         21 |
| **Relationship overlays served**        |      **2,215** |       **153** |  **9,749** |     **0** | **12,117** |
| Finding overlays                        |              0 |             0 |          1 |         0 |          1 |

The seven relationship anchors not counted are synthetic `KSC-DEMO-0000`
fixture edges with `TEXT_ONLY` anchors; the Reader never serves them for the
real case. Unresolved, invalid and ambiguous citations appear in their source location
but never link to a target. Exhibit status comes from the exhibit record (case
exhibits: 900 `unknown`, 2 source-backed `admitted`), and `UNKNOWN` is
displayed as such. Events have no source anchors in this corpus and are
reported as unsupported.

### Source links by precision (all SourceAnchors)

| Precision        |    Anchors |
| ---------------- | ---------: |
| `EXACT_GEOMETRY` |     22,645 |
| `OCR_GEOMETRY`   |          0 |
| `PAGE_AND_LINE`  |     11,993 |
| `PAGE_ONLY`      |     39,375 |
| `TEXT_ONLY`      |         13 |
| `UNAVAILABLE`    |          0 |
| **Total**        | **74,026** |

By object type: 26,693 entity occurrences, 20,037 citations, 12,124
relationships, 1 finding and 15,171 transcript segments.

### Unmapped / review-required source links

| Object type        | Span state                                  | Anchors |
| ------------------ | ------------------------------------------- | ------: |
| Entity occurrence  | `review_required` (mention REVIEW REQUIRED) |   4,373 |
| Entity occurrence  | `unavailable` (no validated region)         |  18,150 |
| Citation           | `unavailable`                               |  17,957 |
| Relationship       | `unavailable`                               |   9,909 |
| Transcript segment | `unavailable`                               |     991 |
| Finding            | `unavailable`                               |       1 |

"Unavailable" means no PDF region was proven. Each of these links still opens
the exact version plus page/line (or page, or text) at its stated precision.

### Integrity checks (full table, all 0)

- regions on non-exact spans;
- exact spans without regions;
- transcript-segment anchors whose span version differs from the transcript's
  version (cross-version leakage);
- regions outside declared page bounds;
- regions on closed/private-session segments.

The projection is idempotent. An immediate re-run produced identical counts
(15,171; 14,180 / 991; the same reasons; 2,519 page contexts) and the same
deterministic IDs.

## Representative real-source verification (Playwright, desktop + Pixel 7)

| Path                                        | Real object                                                   | Result                                                                                                                                            |
| ------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| A Person → Reader → exact highlight         | anchor `0024dd10-…`, `F03667/COR/RED` PDF 18, "Rexhep SELIMI" | Region drawn; reason states EXACT GEOMETRY; URL names version + page                                                                              |
| B Protected witness → transcript line → PDF | anchor `00190b83-…`, `T/2026-02-13` PDF 130, `W04747`         | Region drawn; the containing segment is focused; overlay shows code only                                                                          |
| C Exhibit → occurrence → PDF                | `F03065` PDF 5, exact exhibit occurrence                      | Region drawn; "Status: UNKNOWN" retained                                                                                                          |
| D Resolved citation → cited record          | `F02222/RED` PDF 3, "KSC-BC-2020-06/F02198, para.9"           | Region drawn; "Open cited source" lands on `F02198` ¶9; unresolved citations show "No resolved target — withheld" with no link                    |
| E Network edge → evidence → source          | `F02222/RED` PDF 3 `CITED_IN` edge                            | Evidence path shown; the edge's citation evidence region is drawn; neutrality notice present                                                      |
| F Finding → passage                         | anchor `36a0e299-…`, `F03752` PDF 4                           | Finding overlay is `PAGE_ONLY` and links to `/findings/…`                                                                                         |
| G PAGE_AND_LINE fallback                    | `T/2024-04-29` PDF 4, "Judge Smith" speaker-label mention     | No box; the fallback is stated; the line is focused in the text layer                                                                             |
| H PAGE_ONLY fallback                        | `F03752` finding anchor                                       | No box; the fallback is stated                                                                                                                    |
| I Version switch                            | `T/2024-04-29` → `T/2024-04-29/sqi`                           | Opens at PDF page 0; `line`, `segment` and `anchor` dropped; no region or active highlight                                                        |
| Transcript deep link + two-way sync         | `…&page=14987&line=3`                                         | Lands on PDF 4, segment "Of my testimony." with header W03877. Transcript → PDF draws the line box; a PDF click on that box refocuses the segment |
| Filter / search                             | speaker "THE WITNESS"; search "solemnly"                      | Filtered view says surrounding lines are hidden. Search hits are labelled SEARCH MATCH and draw no box                                            |
| OCR fallback                                | `T/2024-04-29` PDF 37                                         | Page renders, and the Reader states OCR is required with no native geometry                                                                       |
| Accessibility                               | transcript Reader Source / Text / Context                     | axe WCAG 2 A/AA: no serious or critical violations at either size                                                                                 |

`tests/e2e/phase20b.spec.ts` passes 26/26 (13 × desktop and Pixel 7). The
Phase 20A (6) and Phase 19 (8) Reader-dependent suites pass unchanged, and the
route accessibility suite passes 18/18.

## Performance (local, host API, 20 samples each)

| Read                                                                   |     p50 |     p95 |  Payload |
| ---------------------------------------------------------------------- | ------: | ------: | -------: |
| Transcript outline (139 pp)                                            | 24.6 ms | 29.1 ms | 31.0 KiB |
| Segments of one PDF page                                               | 19.2 ms | 21.5 ms | 10.1 KiB |
| Segment by printed page/line                                           | 16.4 ms | 18.3 ms |  0.5 KiB |
| Page context, dense filing page (`F03667/COR/RED` p. 138, 102 objects) | 85.3 ms | 95.7 ms | 79.2 KiB |
| Page context, transcript page                                          | 71.1 ms | 99.8 ms | 10.5 KiB |
| Local search, transcript                                               | 17.8 ms | 21.1 ms | 20.7 KiB |
| Local search, 716-page filing                                          | 75.1 ms | 95.0 ms | 22.0 KiB |

These were measured while the 20A re-projection was running against the same
database, so they are local checkpoint figures, not production SLOs. The
recorded checkpoint budget is page-scoped reads at p95 < 250 ms and < 256 KiB,
and all pass. The browser renders one PDF page at a time, reuses one opened
PDF per artifact URL across page changes, and never loads the network graph or
whole-document anchors. The Reader previously fetched a focused network per
document; that fetch is gone. Transcript pages hold at most about 30 segments,
so the per-page text layer is not virtualized. Filtered views are paginated
server-side (100 per request).

## Known gaps / next

- Entity/citation anchors inside a transcript line keep their own precision
  (for example, speaker-label person mentions are `PAGE_AND_LINE`). They are
  not upgraded to the segment's line box.
- The eight OCR-required pages still have no OCR run.
- The mobile toolbar is dense (the 20A zoom/fit controls wrap to three rows
  before the layer tabs).
- Browser deep-link-to-highlight timing on a production build, the full
  source-fidelity audit and closeout belong to 20C, which has not started.
