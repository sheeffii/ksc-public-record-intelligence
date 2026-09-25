# Phase 20A source geometry and original PDF Reader checkpoint

> **Erratum (20C, 2026-09-25):** the anchor totals below (58,855; 13 `TEXT_ONLY`)
> include 13 anchors from the synthetic `KSC-DEMO-0000` test fixture. The real
> case has 58,842 20A anchors and 0 `TEXT_ONLY`. See
> `PHASE20_QUALITY_GATE.md` for the final real-case figures.

Date: 2026-09-25

Case: `KSC-BC-2020-06`

Status: **PASS — 20A complete; Phase 20 remains IN PROGRESS; 20B not started**

No record was acquired and no original artifact was changed. The projection read
only the 201 already-held public/public-redacted, fetched and parsed versions.
The final idempotent run is `a7774d5a-d206-43b2-b162-65e5146a9626` using
`ksc-native-pdf-geometry/1` (`pdfminer.six` 20260107, `pypdf` 6.19.0).

## Capability audit at entry

| Coordinate                        | Actual entry capability                                                                                  |
| --------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Exact document version / artifact | Yes: 201 SHA-256-identified stored public versions and official source URLs                              |
| PDF page                          | Yes: 9,447 version-bound zero-based PDF page indexes; printed page remained a separate optional value    |
| Parsed text                       | Yes: page text plus structural chunks                                                                    |
| Paragraph                         | Yes where numbered by the source: 5,818 stored numbered paragraphs                                       |
| Transcript line                   | Yes where parsed: 15,171 transcript segments with source page/line coordinates                           |
| Character offset                  | Yes against named derivative bases: 26,693 entity occurrences and 20,031 citations had start/end offsets |
| Bounding box                      | **No**                                                                                                   |
| OCR geometry                      | **No**; three versions were parse-review-required                                                        |
| Original PDF rendering            | **No**; the Reader rendered derivative HTML                                                              |

Character offsets did not imply PDF rectangles. Page text, transcript segment
text and speaker-label offsets were kept as different bases.

## Implemented contract

- Migration `0015` adds version/page-bound dimensions, rotation, geometry text,
  extraction state and processing-run lineage to `document_pages`.
- `page_text_geometry` stores word text, explicit `page_geometry_text` offsets,
  reading sequence and bounded top-left PDF-point rectangles. It has both an
  exact version/page foreign key and an exact version foreign key.
- `SourceSpan` stores one immutable version coordinate, optional page,
  paragraph/transcript lines, verbatim text and named character basis, method,
  extractor version, precision, failure reason and processing run.
- `SourceRegion` stores only validated rectangles. `SourceAnchor` binds a typed
  research object to a span; relationship anchors reuse their actual evidence
  span rather than manufacturing a new region.
- Native embedded text is preferred. Native-empty pages become `ocr_required`;
  no OCR text or rectangle is fabricated.
- The API resolves a public version reference, never a storage key, validates
  hash-addressed key/size/media type, and streams the original PDF with byte
  ranges, SHA-256 ETag and immutable cache metadata.
- The Reader uses locally bundled `pdfjs-dist` 5.7.284 (Apache-2.0), renders one
  selected original page, offers previous/next, numeric zoom, fit page, fit
  width and reset, and shows exact version/source metadata. Parsed text and
  research context are secondary views.

## Coverage

### Geometry

| Measure                                               |    Actual |
| ----------------------------------------------------- | --------: |
| Public PDF versions with native geometry              |       201 |
| Corpus pages                                          |     9,447 |
| Pages with native geometry                            |     9,439 |
| Native-empty / OCR-required pages                     |         8 |
| Pages with OCR geometry                               |         0 |
| Word geometry rows                                    | 2,551,752 |
| Pages missing dimensions or rotation after projection |         0 |

Every held real page has rotation `0`; no rotated real source is held. The
extractor has a focused rotated-PDF test and persists source rotation without
claiming a real rotated-path audit.

### Source anchors

| Precision        |    Anchors |
| ---------------- | ---------: |
| `EXACT_GEOMETRY` |      8,465 |
| `OCR_GEOMETRY`   |          0 |
| `PAGE_AND_LINE`  |     11,002 |
| `PAGE_ONLY`      |     39,375 |
| `TEXT_ONLY`      |         13 |
| `UNAVAILABLE`    |          0 |
| **Total**        | **58,855** |

There are 46,752 reusable spans and 9,471 regions. The lower region count is
expected: an exact span may have multiple word rectangles and a relationship
may reuse an occurrence/citation span.

| Object binding     | Anchors |
| ------------------ | ------: |
| Entity occurrences |  26,693 |
| Citations          |  20,037 |
| Relationships      |  12,124 |
| Findings           |       1 |

Entity-occurrence anchors cover 13,970 person, 5,552 witness, 951 organization
and 6,220 exhibit occurrences. Fallbacks were not promoted: 26,127 spans report
`geometry_text_not_found`, 14,350 report `geometry_text_not_unique`, and six
report `pdf_page_unavailable`.

## Representative mappings

| Path                    | Anchor                                 | Version / coordinate                                   | Result                                 |
| ----------------------- | -------------------------------------- | ------------------------------------------------------ | -------------------------------------- |
| Verified person mention | `0024dd10-a85a-5b97-9025-df17bc8b27d3` | `F03667/COR/RED`, PDF 18 / printed 19, “Rexhep SELIMI” | `EXACT_GEOMETRY`, two regions          |
| Witness occurrence      | `00190b83-cc92-50f2-a62c-d960989327f7` | `T/2026-02-13`, PDF 130 / printed 28987, `W04747`      | `EXACT_GEOMETRY`                       |
| Organization mention    | `00311f9d-0f7f-5659-a82a-af5b2d33d8a1` | `F01594`, PDF 0 / printed 1                            | `EXACT_GEOMETRY`                       |
| Exhibit occurrence      | `00545b83-b4cb-59e6-8b60-ef5b60041210` | `T/2026-02-16`, PDF 105 / printed 29113, `P27684`      | `EXACT_GEOMETRY`                       |
| Citation                | `002c3446-28d8-50b6-bc25-f07c6aa30519` | `T/2024-02-22`, PDF 0 / printed 12810, `W04576`        | `EXACT_GEOMETRY`                       |
| Relationship evidence   | `0040000e-408a-59ed-a62f-cfca79eae079` | `F03664/RED2`, PDF 162 / printed 163                   | Reuses exact evidence span             |
| Finding passage         | `36a0e299-42f5-5e2f-a1cc-0a6efcbafcc2` | `F03752`, PDF 4 / printed 5                            | `PAGE_ONLY`; no rectangle manufactured |

## OCR audit

The eight native-empty pages are PDF indexes 37, 44, 59, 67, 72, 73, 80 and
89 of exact version `KSC-BC-2020-06/T/2024-04-29`. They are explicitly
`ocr_required`; none currently has a research anchor. The schema/API/UI support
distinct `OCR_GEOMETRY` and OCR extraction labels, but Phase 20A did not add an
OCR engine or reconstruct any content. OCR execution and review remain a known
gap, not exact-geometry coverage.

## Integrity and version safety

Full-table checks returned zero for:

- geometry or source regions outside declared page bounds;
- exact/OCR spans without regions;
- fallback spans carrying regions;
- geometry pages or source spans whose processing run is not completed.

Foreign keys bind geometry and spans to their exact version; coordinates are
never copied between related versions. Documents with multiple held versions
(including `F00026` and transcript language/version pairs) retain independent
geometry rows and exact artifact identity.

## Reader and delivery verification

- `HEAD` returned `200`, exact content length, `Accept-Ranges`, immutable
  SHA-256 ETag and `application/pdf`.
- `Range: bytes=0-65535` returned `206`, an exact 65,536-byte body and correct
  `Content-Range`. Multi-range returned `416`; an arbitrary storage-key-shaped
  route returned `404`.
- The SourceAnchor API returned the exact `F03667/COR/RED` version, PDF page 18,
  dimensions, extraction/run lineage and the two persisted rectangles.
- Real-data Playwright passed 6/6 on desktop and Pixel 7: short filing
  `F03752` (7 pages), large filing `F03667/COR/RED` (716 pages), and long
  transcript `T/2026-02-13/sqi` (172 pages); one canvas only; exact highlight
  through zoom/fit/reset/resize; and page-only fallback with zero rectangles.

Local five-sample 64 KiB range medians were 27.248 ms (short), 25.842 ms
(large), and 28.777 ms (long transcript). The representative three-document
browser test completed in 9.4 s on desktop and 8.4 s on the Pixel 7 profile
while four Playwright workers contended locally. These are local checkpoint
measurements, not production SLOs.

## Targeted gates

- Migration upgrade/downgrade and model drift, geometry/rotation and byte-range
  tests: 11 passed.
- Geometry projector: 201/201 selected and processed, zero failures; immediate
  re-run returned identical counts and deterministic IDs.
- Backend: Ruff clean; strict MyPy clean across API and ingestion worker.
- Frontend: ESLint and Prettier clean; strict TypeScript clean; 256 Vitest tests
  passed; production Next build passed and emitted the local PDF worker.
- Final repository regression: 342 backend tests and 256 frontend tests passed;
  `make lint`, `make typecheck` and `make test` passed.
- Browser: Phase 20A real-data suite 6/6 on desktop and Pixel 7. The Phase 19
  source-link regression suite is retained and updated for source-first Reader
  behavior.

## Open gaps / stop point

- Eight pages require an approved OCR engine/language/preprocessing/review run
  before any `OCR_GEOMETRY` can exist.
- Most historical anchors honestly remain page/line/page-only because native
  PDF token order does not deterministically reproduce the derivative span or
  the text repeats.
- Transcript-native rendering, PDF↔transcript synchronization and broader
  research overlays belong to 20B and were not started.

Phase 20 is not complete. Stop before 20B pending explicit authorization.
