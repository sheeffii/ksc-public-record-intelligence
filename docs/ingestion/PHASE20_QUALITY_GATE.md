# Phase 20 quality gate — source-native PDF and transcript Reader

Date: 2026-09-25 · Case: `KSC-BC-2020-06` · Pass: 20C (audit and closeout)

Status: **PASS — Phase 20 COMPLETE.** Tag `phase-20-complete`.

Machine-readable record: `docs/ingestion/manifests/phase20-audit.json`
(includes all 1,171 region-audited anchors with version, SHA-256, page and
verdict). Earlier checkpoints: `PHASE20A_SOURCE_GEOMETRY_REPORT.md`,
`PHASE20B_TRANSCRIPT_READER_REPORT.md`.

No records were acquired, no stored artifact was modified, and Phases 20A and
20B were not re-implemented. Fixes were limited to the defects this audit
demonstrated (listed at the end).

## Count correction

The 20A and 20B checkpoints reported 58,855 and 74,026 anchors, including 13
`TEXT_ONLY` anchors. Those 13 belong to the synthetic `KSC-DEMO-0000` test
fixture, not to the real corpus. Every figure below is restricted to
`KSC-BC-2020-06`: the real corpus has **0 `TEXT_ONLY` anchors**, 20,031
citation anchors (not 20,037) and 12,117 relationship anchors.

## Final coverage (actual)

| Measure                                                       |            Count |
| ------------------------------------------------------------- | ---------------: |
| Document versions (stored, public)                            |              201 |
| Native-geometry pages                                         |            9,439 |
| OCR-required pages                                            |                8 |
| Word geometry rows                                            |        2,551,752 |
| SourceAnchors                                                 |           74,013 |
| — `EXACT_GEOMETRY`                                            |           22,645 |
| — `OCR_GEOMETRY`                                              |                0 |
| — `PAGE_AND_LINE`                                             |           11,993 |
| — `PAGE_ONLY`                                                 |           39,375 |
| — `TEXT_ONLY`                                                 |                0 |
| — `UNAVAILABLE`                                               |                0 |
| Transcript segments                                           |           15,171 |
| — exact geometry / page-and-line / page-only                  | 14,180 / 991 / 0 |
| Verified entity overlays (person, witness code, organization) |           16,100 |
| Review-required person overlays                               |            4,373 |
| Exhibit overlays                                              |            6,220 |
| Citation overlays                                             |           20,031 |
| Relationship overlays                                         |           12,117 |
| Finding overlays                                              |                1 |

| Audit outcome                                               |                   Count |
| ----------------------------------------------------------- | ----------------------: |
| Anchors independently region-audited against original bytes |                   1,171 |
| Anchors visually inspected in the production Reader         | 7 (one per object type) |
| Fallback anchors audited against page text                  |                  51,368 |
| Transcript segments audited against printed numbered lines  |                  15,171 |
| Highlight mismatches (after fixes)                          |                       0 |
| Cross-version leakage (after fixes)                         |                       0 |
| Provenance violations                                       |                       0 |
| Fabricated precision violations                             |                       0 |

The visual audit found one wrong-version highlight. It was fixed and
re-verified; see "Defects found and fixed".

## 1. Original source fidelity

- All 201 stored artifacts were re-read from object storage, and each SHA-256
  and byte size matches its version record. Across all 9,447 pages, the MediaBox
  origin is `(0,0)`, CropBox equals MediaBox, and stored width, height and
  rotation match the PDF. The canonical region space and the space PDF.js
  renders are therefore the same everywhere.
- In the production browser (desktop and Pixel 7), `F03752`,
  `F03667/COR/RED` and `T/2026-02-13/sqi` load only
  `/api/v1/document-versions/{exact ref}/artifact`, with 200/206 responses and
  an ETag equal to that version's SHA-256. The official source link equals the
  version's recorded `source_url`. One canvas is mounted, and parsed text is
  labelled as a derivative layer.
- Artifact endpoint checks:
  - `HEAD` returns 200 with exact length, `Accept-Ranges`, an immutable ETag,
    `nosniff` and `default-src 'none'` CSP.
  - A single range returns 206.
  - Multi-range and out-of-range requests return 416.
  - Storage-key-shaped and traversal paths return 404.
  - The real case has no non-public or unfetched version to exercise. That
    path is covered by the integration suite.

## 2–3. SourceAnchor → PDF and exact highlights

**Independent region audit.** For each exact anchor on the sampled pages, the
check re-opened the original bytes and collected, with pdfminer, the characters
whose centres fall inside the persisted rectangles. It then compared them,
whitespace-insensitively, with the anchor's expected text: the occurrence or
citation text, or `speaker: text` for a transcript segment.

- The sample was 118 pages across 71 versions: at most three pages per version
  and 30 per object type, plus all 144 pages of the revised transcript
  `T/2021-03-24` (EN and SQ).
- Results: 1,171 anchors, of which 1,170 match exactly and 1 has the same
  characters in a different stream order. There are 0 mismatches and 0 boxes
  containing neighbouring text.
- By type: 228 entity occurrences, 136 citations, 143 relationships and 664
  transcript segments.
- Version forms covered: base filing, RED, RED2, COR, annex, SQ, EN
  transcript and a revised transcript. **CORRED is NOT HELD.**
- The finding has only `PAGE_ONLY` precision (see section 15).

**Browser alignment.** In the production Reader, each rendered overlay equals
the persisted PDF-point region scaled to the canvas, to within 1.5 px. This
holds at load, after two zoom steps, and through fit page, fit width and reset
on desktop and Pixel 7, stable across three repeats.

**Navigation.** Next/previous and browser back/forward never re-attach a
highlight to another page or version.

**Visual inspection.** One random real anchor per type was rendered and
inspected: person `cee46ba0…`, witness `b4af184f…`, organization `36cdc8de…`,
exhibit `c8f34508…`, citation `df4db62b…`, relationship `28511352…` and
transcript segment `2101faaa…` (four line boxes, lines 22–25). Each box covers
exactly its text; for example, only the first "P00687" in ¶525 is boxed, not the
later "P00687's".

## 4–5. Fallbacks

The fallback audit covers all 51,368 non-exact real anchors:

- 0 carry a region.
- 0 have a printed-page mismatch.
- All 11,993 `PAGE_AND_LINE` anchors have their stated lines present on the
  stated page.
- 50,338 anchors' text occurs verbatim on the page, and 223 more once printed
  transcript line numbers are skipped. 805 carry no text (804 closed-session
  segments plus one other text-less anchor).
- Two divergences are explained:
  - The finding passage is ¶¶12–16 on the same PDF page, with footnote
    markers interleaved.
  - One segment's numbered lines differ in order from an unnumbered wrapped
    redaction notice. It correctly stays `PAGE_AND_LINE`
    (`geometry_line_text_mismatch`).

In the browser, `PAGE_AND_LINE` and `PAGE_ONLY` links open the correct version
and page and focus the line. They draw no box, state their precision, and
state "no highlight was manufactured". `TEXT_ONLY` does not occur in the real
corpus.

## 6. Transcript fidelity

- All 14,367 open-session segments reproduce, character for character
  (whitespace-insensitive), the numbered lines `line_from..line_to` printed on
  their stated page. This holds for 14,180 exact and 187 page-and-line
  segments.
- All 804 closed-session segments carry no text. No printed page number
  mismatches.
- The persisted page headers cover open (1,924), private (397) and closed (198)
  pages, for coded (646) and publicly named (1,873) witnesses, including
  examination headings.
- No real segment carries a witness link, so "THE WITNESS" is never shown with
  a code.
- Neither the Reader API nor the UI reads the parser's sticky
  `examination_type` or label-derived `speaker_role`.
- The pages with no line grid are shown with verbatim text at
  `PAGE_AND_LINE`.

## 7. Two-way sync

- Transcript → PDF draws only the segment's validated line boxes.
- PDF → transcript: clicks on `T/2023-07-14` PDF 73 (open segments, no line
  grid) select nothing and draw nothing. A click on the running header of a
  gridded page selects nothing. A click inside a validated box selects exactly
  that segment, computed from its persisted region.

## 8. Deep links (production build)

A render log recorded every page, render state and region from the first DOM
mutation. For every link type, the only page ever rendered was the target
page, and no region appeared before its page finished rendering.

| Deep link                                              | Desktop render / highlight (ms) | Pixel 7 render / highlight (ms) |
| ------------------------------------------------------ | ------------------------------- | ------------------------------- |
| anchor, exact person (716-page `F03667/COR/RED`, cold) | 5,163 / 5,163                   | 1,314 / 1,314                   |
| anchor, exact witness (SQ transcript)                  | 1,036 / 1,036                   | 940 / 940                       |
| anchor, transcript segment                             | 1,697 / 1,697                   | 1,022 / 1,022                   |
| transcript page + line                                 | 1,671 / 1,671                   | 1,301 / 1,301                   |
| segment id                                             | 1,399 / 1,399                   | 1,187 / 1,187                   |
| pdfPage only                                           | 1,418 / —                       | 805 / —                         |
| anchor, `PAGE_ONLY` finding                            | 1,403 / —                       | 809 / —                         |
| anchor, `PAGE_AND_LINE` mention                        | 1,287 / —                       | 850 / —                         |

These times run from page start (`performance.now()`) and were measured on a
local production build under three parallel workers. Warm repeats of the
716-page anchor on desktop took 2.3–3.0 s to the highlight (about 0.8 s of that
was the server response). Next/previous within that filing took 132–161 ms on
desktop and 71–136 ms on mobile.

## 9. Version safety

- EN ↔ SQ (`T/2024-04-29`) and RED ↔ COR (`F00026/RED` → `F00026/RED/sqi/COR`)
  switches open page 1 of the new version. `line`, `segment` and `anchor` are
  dropped, no region or active highlight remains, and page-context reads
  target only the new version.
- Back/forward restores each version's own state.
- The Reader now refuses to draw an anchor on any version but its own
  (defect 2 below).

## 10–11. Overlay safety and weak entity precision

- VERIFIED, SEARCH MATCH, REVIEW REQUIRED, AMBIGUOUS, UNKNOWN and UNRESOLVED
  are each displayed as distinct text labels. REVIEW REQUIRED is never labelled
  VERIFIED.
- Search hits are labelled SEARCH MATCH and never draw a box.
- Every witness overlay label is a bare code, both on pages that also have
  review-required mentions and on dense filing pages.
- AMBIGUOUS and UNRESOLVED citations show "No resolved target — withheld" with
  no link. Exhibit status UNKNOWN is shown as UNKNOWN.
- 10,698 `PAGE_AND_LINE` entity anchors lie inside exact transcript lines, and
  none has a region. The 13 exact entity anchors inside `PAGE_AND_LINE`
  segments rely on their own unique geometry.
- A PAGE_AND_LINE entity link focuses its line but shows its own precision.
  This separation is intentional and not a blocker.

## 12. Events

All 201 real events are docket-metadata events (`source_metadata`: filing,
decision or testimony date), tied to a whole document or hearing. None has a
text passage to anchor. The roadmap's final acceptance list names people,
witness codes, organizations, exhibits, citations, relationships, findings,
transcript segments and search results; it does not name events. The Reader
states that events are not source-anchored, and no event anchor was
fabricated. This is a known limitation, not a blocker.

## 13. Exhibits and citations

- Exhibit → occurrence → exact source and citation → resolution → target →
  source highlight were verified in the browser.
- All 1,980 sub-numbered exhibit citations remain unresolved: no sub-number
  exhibit is held, and none falls back to its base.
- 0 non-resolved citations carry a target, and 0 exhibit statuses exist
  without a status event.

## 14. Relationships and evidence path

Each typed edge was traced as edge → evidence → `ProvenanceRead` → the anchor
the edge reuses → PDF. The region audit covered all three types, with every
region matching its evidence text exactly: 90 `CITED_IN`, 51 `MENTIONED_IN` and
2 `TESTIFIED_AT`. In the browser:

- `CITED_IN`: `F02222/RED` p. 3, and the random `CITED_IN` edge `28511352…`
  on `F01532/RED` p. 2.
- `TESTIFIED_AT`: the header-backed appearance on `T/2024-04-29`.

Every served edge passes the shared public typed-edge rule. The Reader states
the neutrality notice and adds no guilt, coordination, responsibility or
credibility wording.

## 15. Finding

Finding `FD-F03752-P12-16` → passage ¶¶12–16 → anchor `36a0e299…` → exact
version `F03752`, PDF page 5. The finding text equals the concatenation of
those five paragraphs. Its precision is `PAGE_ONLY`, and no geometry was
manufactured.

## 16. OCR

All eight OCR-required pages (PDF indexes 37, 44, 59, 67, 72, 73, 80 and 89 of
`T/2024-04-29`) render the original page, state "requires OCR — no native text
geometry", show no parsed segments and draw no region. No OCR text exists, and
no redacted or private material is reconstructed.

## 17–18. Performance and mobile

- One canvas renders one page at a time. Context and segments are read per
  page, and filtered views are paginated on the server.
- Four page steps on the 716-page filing made exactly four page-context
  requests and no network or global-anchor reads.
- On mobile, Source, Text and Context are separate tabs. Witness (page header →
  `/witnesses/W03877`) and exhibit (overlay → dossier) navigation works, and
  search, highlight and OCR flows pass on Pixel 7. The toolbar wraps, but it
  remains usable.

## 19. Source-of-truth contract

The original PDF comes first: exact bytes by version, and highlights only from
persisted regions of that version. Parsed text is labelled "Derivative aid —
the PDF remains authoritative". Structured intelligence is shown with its
state, rule and precision. The Reader renders no AI output, and no derived
text is presented as court text.

## Defects found and fixed in 20C

1. **Deep links without their segment box.** Transcript page+line and
   `segment` links landed on the right segment, but its validated line box
   appeared only after a click. The Reader now seeds the highlight from that
   segment's own anchor. An `anchor` link keeps its own precision.
2. **Wrong-version highlight (blocking; found by the visual audit).**
   `/documents/F03668?anchor=…` (`F03668/RED2`) rendered annex
   `F03668/RED/A01/RED` and drew the RED2 region on it. There were two causes.
   The API resolved a shared filing number (`F03668`, `F03668/A01`)
   arbitrarily, and the web repository silently fell back to another version
   when the requested one was not held.
   - Fixed: an exact official reference wins, and a bare filing number
     resolves only when unambiguous (`F00002` now returns 404).
   - Fixed: a requested version that is not held is not found.
   - Fixed: an anchor is served and drawn only on its own version.
   - Regression tests at the API, repository and browser levels.
3. **Overlay/canvas timing during zoom.** The canvas CSS size changed before
   the overlay's viewport did. Both now change in one commit, and regions stay
   hidden until the bitmap is drawn.
4. **Mobile re-render loop.** On pages 704–705 of `F03667/COR/RED`, the
   implicit (content-sized) grid column let fit-width feed back into the host
   width. The grid columns are now `minmax(0,1fr)`, and the resize observer
   only reacts to real width changes.
5. **Hidden-layer re-render.** A hidden mobile layer (width 0) re-rendered the
   PDF at the minimum size. Zero widths are now ignored.

The Phase 15 Reader route test asserted on literal strings from the pre-20B
Reader. It was updated to assert the same intent (exact version and page
metadata, parsed court text, official source link, no demo data) against the
source-native Reader.

## Gates

- `make lint`, `make typecheck` and `make test` pass: backend 353 passed,
  frontend 260 passed.
- Full Playwright on the production build (desktop and Pixel 7): 176 passed,
  0 failed, 98 skipped (specs gated to other data modes). This includes
  `phase20c.spec.ts`, `phase20b.spec.ts`, `phase20a.spec.ts`,
  `phase19.spec.ts`, `phase15.spec.ts` and route accessibility.

## Known limitations

- The eight OCR-required pages have no OCR run, and no OCR geometry exists.
- Events are docket metadata with no text passage, so they have no source
  anchors.
- 991 transcript segments remain `PAGE_AND_LINE` (804 closed session, 157 with
  no line grid, 27 text mismatches, 2 ambiguous grids, 1 missing line).
- Most historical mentions and citations are `PAGE_ONLY` or `PAGE_AND_LINE`
  because their text repeats on the page or does not appear in the native
  token order.
- CORRED versions are NOT HELD. Every held page has rotation 0, so a real
  rotated page could not be audited.
- The desktop first load of the 716-page filing takes about 2.3–3.0 s warm.
- The mobile toolbar wraps onto several rows.
