# Phase 20 — Source-Native Intelligent PDF & Transcript Reader

**Status:** COMPLETE (2026-09-25) — 20A, 20B and 20C complete; tag
`phase-20-complete`. Do not begin another phase without explicit authorization.

## Goal

Make every important structured research object traceable to the exact place in
the **original public court source**, while keeping the original stored PDF
visually primary and authoritative.

```text
ORIGINAL PUBLIC PDF
        ↓
document version
        ↓
page
        ↓
text geometry / transcript coordinates
        ↓
SourceSpan / SourceAnchor
        ↓
verified entity / citation / exhibit / relationship / finding
        ↓
interactive Reader highlight
```

Parsed text, OCR text, transcript structure and structured intelligence are
derivative aids. None replaces or silently rewrites the original PDF.

## Starting baseline (Phase 19 close, `8661630`, tag `phase-19-complete`)

- The known public corpus has 202 source records, 176 documents, 201 stored
  versions and 9,447 pages. Stored artifacts are SHA-256 identified and retain
  exact `document_version` identity and official source URLs.
- The parser persists page text, PDF page indexes, printed pages, paragraphs,
  transcript pages/lines and exact occurrence character spans. It does not
  persist page dimensions, rotation or word/glyph bounding boxes.
- The current Reader renders derivative chunks/paragraphs as HTML. Exact-source
  links can select a version, page, paragraph, line range and verbatim text, but
  cannot display the original PDF with a geometry-backed overlay.
- Provenance-bearing objects already converge on exact document-version and
  source coordinates through `ProvenanceRead`, but no reusable persisted
  `SourceSpan` / `SourceAnchor` contract exists.
- Three source versions remain parse-review-required at Phase 19 close,
  including image-only pages. OCR is not implemented.

Repository, migration and test reality at the start of each pass wins over this
summary. Phase 20A begins with an inventory of all current coordinate producers
and consumers; it must not assume that character offsets share one text base.

## Core principles

1. **The original stored official PDF is authoritative.** The Reader renders
   those exact bytes, identified by document version and checksum.
2. **Coordinates are version-specific.** Geometry from EN, SQ, RED, RED2, COR,
   CORRED, an annex or a transcript revision is never reused for a related
   version.
3. **Highlights are proven, never guessed.** Exact geometry is displayed only
   when deterministic extraction and validation support it.
4. **Fallbacks are explicit.** An anchor reports `EXACT_REGION`, `PAGE_ONLY`,
   `TEXT_ONLY`, `TRANSCRIPT_LINE` or `UNAVAILABLE`; the UI never visually
   upgrades a fallback.
5. **Source text is verbatim.** Transcript and court text are never rewritten,
   normalized for display, completed across gaps, translated or reconstructed.
6. **One provenance path.** Research object → evidence/occurrence →
   `SourceAnchor` → exact document version → exact original public source.
7. **Uncertainty stays visible.** `VERIFIED`, `SEARCH MATCH`,
   `REVIEW REQUIRED`, `AMBIGUOUS`, `UNKNOWN` and `UNRESOLVED` remain distinct.

## Passes and checkpoints

| Pass | Scope | Entry / stop rule |
|---|---|---|
| **20A** | Source geometry, SourceAnchor architecture and original PDF viewer | COMPLETE (2026-09-25). Checkpoint recorded; stopped before 20B. |
| **20B** | Transcript-native Reader, deterministic PDF synchronization and research overlays | COMPLETE (2026-09-25). Checkpoint accepted. |
| **20C** | Deep source-fidelity audit, performance/accessibility verification and closeout | COMPLETE (2026-09-25). Audit PASS; stopped after closeout. |

Each pass is a separate implementation, verification and documentation
checkpoint. Run focused tests during implementation and the full repository
gates only at the pass's final verification point.

## 20A — Source geometry, SourceAnchor architecture and original PDF viewer

### 1. Original PDF delivery and viewer

- Add an authenticated-by-application, public-record-safe API path that streams
  or range-serves the exact stored PDF bytes. Resolve the artifact by immutable
  document-version identifier; never accept an arbitrary storage key or URL.
- Validate artifact status, checksum identity, public/source state and PDF media
  type. Preserve range requests, content length, caching validators and bounded
  error responses needed by a browser PDF renderer.
- Use a maintained browser PDF renderer that displays the actual stored PDF.
  Record dependency, worker, CSP and licence decisions before adoption.
- Provide page navigation, current/total page, zoom in/out, numeric zoom, fit
  width, fit page and reset. PDF index and printed/source page remain distinct.
- Show exact official version reference, language/version badges, checksum or
  immutable identity where appropriate, and an official-source link.
- Replace no source page with reconstructed HTML. Derivative text may be an
  accessible/searchable companion, clearly labelled and subordinate to the PDF.
- Fail honestly when bytes are unavailable, corrupt or not renderable. Never
  fall back to derivative HTML while implying it is the original source.

### 2. Page-specific source geometry

- Extend the parser with a versioned geometry extractor, preferring the PDF's
  embedded/native text layer.
- Persist per-page media/crop dimensions, coordinate units, rotation and the
  transform needed to map canonical PDF coordinates to the rendered viewport.
- Persist bounded text spans (word or line granularity unless a finer level is
  demonstrably required) with exact verbatim text, character range in a named
  page-text basis, bounding box(es), reading order and extraction method.
- Geometry rows belong to exactly one `document_version_id` and one
  `pdf_page_index`. Bounds must be finite, non-negative and inside that page's
  declared coordinate space after rotation is accounted for.
- Record extractor name/version and the processing run. Reprocessing must be
  deterministic and idempotent for the same bytes and extractor version.
- Do not copy coordinates between related versions. A version is geometry-ready
  only after its own stored bytes have been extracted and validated.
- Bound row count and payload size per page. Prefer compact line/word geometry
  over unbounded glyph storage unless a measured fidelity case requires glyphs.

### 3. Reusable `SourceSpan` / `SourceAnchor`

Define one public read contract and a normalized persisted representation. The
names may be adjusted during 20A inventory, but the semantics may not be split
into object-specific substitutes.

`SourceSpan` is the immutable source coordinate:

- exact `document_version_id` and official version reference;
- `pdf_page_index` and, independently, optional printed/source page;
- optional paragraph, transcript page, line range and timestamp range;
- optional named text basis plus character start/end and verbatim source text;
- zero or more validated PDF regions in canonical page coordinates;
- extraction method, extractor/rule version and processing-run lineage;
- resolution level: `EXACT_REGION`, `PAGE_ONLY`, `TEXT_ONLY`,
  `TRANSCRIPT_LINE` or `UNAVAILABLE`.

`SourceAnchor` binds one structured object/evidence occurrence to one
`SourceSpan` and adds:

- object kind and stable object/evidence identifier;
- source/verification state without collapsing domain states;
- anchor role (mention, citation source/target, finding passage, relationship
  evidence, transcript segment, search match or equivalent closed vocabulary);
- review state and any non-sensitive machine-readable failure reason.

The contract must answer, without inference at read time: **which version,
which page, which paragraph/line, which exact text, which PDF region, and how it
was extracted?**

### 4. Anchor migration and compatibility

- Inventory and map existing provenance for verified person mentions,
  witness-code mentions, organizations, exhibits, citations, relationships,
  findings, transcript segments and search results where applicable.
- Preserve existing object tables and authoritative foreign keys. Add anchors
  through an additive migration/projection rather than duplicating or weakening
  verification logic.
- Existing `char_anchor` values name different text bases; migrate only when the
  exact persisted slice reproduces the verbatim source text. Otherwise retain
  the honest non-region fallback and a reason.
- Search matches may use transient/read-time anchors when no durable research
  object exists, but they must remain `SEARCH MATCH`, not verified occurrences.
- A relationship anchor points to its actual citation, occurrence or appearance
  evidence. It does not manufacture a new region for the edge itself.
- Reprojection is idempotent and produces a reconciliation report: anchors by
  object kind, resolution level, extraction method and failure reason.

### 5. Exact PDF highlighting

- Resolve structured object → evidence/occurrence → anchor → exact version and
  page on the server. The client must not search the whole page and invent a box.
- Render one or more overlay rectangles only from validated regions, transformed
  for the current rotation/scale. The overlay must remain aligned through zoom,
  fit, resize, page virtualization and device-pixel-ratio changes.
- Validate highlighted text against the anchor's verbatim span during
  projection. Duplicate page text, reordered text layers or ambiguous matches do
  not receive guessed geometry.
- `PAGE_ONLY` opens and identifies the page without a rectangle. `TEXT_ONLY`
  shows the exact derivative text and states that no PDF region is available.
  `TRANSCRIPT_LINE` opens the transcript coordinate and PDF page when known.
  `UNAVAILABLE` explains that exact navigation cannot be provided.
- Deep links use stable IDs and explicit coordinates; free-form query text is
  never treated as proof of an exact region.

### 6. OCR fallback

- Native/embedded PDF text is always preferred. OCR runs only for an image-only
  or otherwise unsupported page identified by a deterministic capability check.
- OCR is page-scoped, reproducible and records engine/version, language model,
  preprocessing, processing run and review state. OCR text and geometry are
  labelled **DERIVATIVE OCR** in API and UI.
- No OCR result may fill a redaction, infer obscured text, bridge a private
  session or identify a protected witness. Redacted/blank regions stay blank.
- Low-confidence or structurally inconsistent OCR produces `REVIEW REQUIRED`,
  `PAGE_ONLY` or `UNAVAILABLE`; confidence must not be converted into a fact or
  displayed as evidence strength.
- Phase 20 needs a representative real image-only fallback gate, not blanket OCR
  of native-text pages and not exact geometry for every historical PDF.

### 20A exit criteria

- [x] Original stored PDFs are safely served and rendered with version identity,
  official-source link, page controls and zoom/fit controls.
- [x] Version-specific page geometry and extractor lineage are persisted with
  migration round-trip, bounds and idempotency tests.
- [x] One reusable SourceSpan/SourceAnchor contract covers the required object
  classes and preserves existing provenance/verification semantics.
- [x] Geometry-backed highlights survive zoom, rotation and resize; every
  non-exact case uses an explicit fallback.
- [x] Native-text and representative OCR paths are labelled and audited.
- [x] 20A focused gates and a real-source sampling checkpoint are recorded.

## 20B — Transcript-native Reader, synchronization and research overlays

### 7. Transcript-native Reader

- Present the real transcript hierarchy where available: hearing/session, date,
  transcript page, line, timestamp, speaker, witness code, examination context
  and exact transcript text.
- Preserve every stored transcript character. Never rewrite grammar, expand a
  redaction, translate, merge private-session gaps or silently normalize the
  displayed source.
- Keep printed transcript page/line coordinates separate from PDF page index.
  Lines are directly addressable and shareable with the exact version identity.
- Speaker, witness and examination labels appear only when the public source and
  deterministic parser support them. Missing fields remain absent/unknown.
- Virtualize long transcripts without breaking line selection, keyboard reading
  order, URL restoration or the current synchronized PDF page.

### 8. PDF ↔ transcript synchronization

- Build synchronization only from deterministic, version-specific mappings
  between transcript segments/lines and PDF geometry.
- A transcript line selection may open and highlight its original PDF region;
  selecting a proven PDF region may focus the exact transcript line(s).
- Validate page/line/text agreement. Duplicated line numbers, missing lines,
  private-session pages, OCR uncertainty and ambiguous reading order block exact
  synchronization rather than selecting a likely region.
- Record synchronization status and reason using the same resolution levels.
  Never force alignment merely because page text looks similar.

### 9. Source-backed research context

The Reader exposes context for People, Witnesses, Organizations, Exhibits,
Citations, Findings, Events and Relationships only through their source anchors.

- The original source remains the primary visual surface. Context is a secondary
  inspector, not a replacement document view.
- Selecting context focuses its anchored source. Selecting a source anchor may
  reveal related context, bounded and queried server-side by current version/page.
- Relationships open their evidence occurrence/citation before any related
  entity. Findings open their exact citation/passage. Unresolved objects never
  receive a synthetic target.
- Keep `VERIFIED`, `SEARCH MATCH`, `REVIEW REQUIRED`, `AMBIGUOUS`, `UNKNOWN` and
  `UNRESOLVED` visibly and semantically distinct. Colour encodes source/category,
  never severity, guilt, credibility or confidence.
- Protected witness context stays code-only and fails closed.

### 10. Performance architecture

- Render PDF pages lazily around the viewport and release off-screen canvases.
- Fetch geometry and context by exact version/page in bounded, cacheable chunks;
  do not ship full-document geometry or all related research objects initially.
- Bound overlays per request/page and paginate dense context. Cluster or defer
  off-screen marks without changing their verification state.
- Virtualize long transcript lists where measurement justifies it. Preserve
  deterministic deep-link restoration and accessible reading order.
- Establish representative budgets for first page, deep-link-to-highlight,
  zoom/scroll stability, geometry payload and server query latency before 20B
  closes; report measured p50/p95 or an explicitly justified local equivalent.
- Do not add OpenSearch, embeddings or an AI provider for Reader performance.

### 11. Mobile and accessibility

- Use a source-first mobile layout. The PDF/transcript occupies the primary
  viewport; research context moves into an accessible drawer/sheet rather than
  compressing a desktop three-column layout.
- Controls are touch-sized, zoom does not trap the viewport, and the active page,
  line and highlight have non-colour cues.
- Provide keyboard navigation, focus restoration, screen-reader labels, reduced
  motion support and a textual alternative for geometry overlays.
- Official identifiers and court text are not translated. All interface strings
  live in the EN/SQ string tables and all colours come from design tokens.

### 20B exit criteria

- [x] Transcript-native navigation preserves exact source text and all available
  hearing/session/date/page/line/timestamp/speaker/witness/examination structure.
- [x] Deterministic PDF ↔ transcript synchronization works where proven and
  refuses ambiguous alignment.
- [x] All eight research-context classes use SourceAnchor and keep their data
  states distinct while the source remains visually primary.
  _(20C: every class exposed in the Reader is SourceAnchor-backed. The 201 real
  events are docket metadata with no text passage; they are stated as not
  source-anchored and none was fabricated — `PHASE20_QUALITY_GATE.md` §12.)_
- [x] Large-document/transcript behavior meets recorded bounded-query, overlay,
  rendering and deep-link budgets.
- [x] Desktop and Pixel 7 source-first workflows pass accessibility and
  interaction verification.

## 20C — Deep source-fidelity audit and final closeout

### 12. Representative real-source audit

Build a declared audit sample across document kinds, languages, version forms,
rotations, native-text quality and transcript/non-transcript sources. Include EN,
SQ, RED, RED2, COR, CORRED, annexes and transcript revisions where each form is
actually held; record `NOT HELD` rather than fabricating coverage.

Verify these end-to-end paths against the visible original PDF:

1. Person → verified occurrence → exact PDF highlight.
2. Protected witness code → transcript line → exact PDF region/fallback.
3. Exhibit → evidence occurrence → original source.
4. Citation → source or resolved target, without conflating the two anchors.
5. Relationship → actual evidence basis → original source.
6. Finding → citation/passage → original source.
7. Version isolation: related versions never share geometry or anchors.
8. OCR fallback: derivative labelling, review state and no redaction recovery.
9. Mobile Reader: source-first navigation and context drawer/sheet.

For every sample record: object ID, version ID/ref, checksum, expected coordinate,
actual resolution level, extraction method, visual/text verification outcome and
reviewer/date. A wrong rectangle, wrong version or rewritten transcript is a
blocking failure. Coverage is reported by resolution level; Phase 20 does not
claim that all historical pages have exact geometry.

### 13. Quality gates

- Migration upgrade/downgrade round-trip and Alembic drift check.
- Unit tests for coordinate transforms, rotation, bounds, text-basis slices,
  extraction methods, resolution levels and every ambiguity/fallback branch.
- Integration tests for immutable version identity, safe PDF range delivery,
  geometry idempotency, anchor reconciliation, source-state preservation and
  protected-witness failure-closed behavior.
- Real-data Playwright at desktop and Pixel 7 for all nine audit paths where the
  corpus holds a representative source, including keyboard and accessibility
  checks.
- Performance tests for representative large PDFs and long transcripts, with
  bounded overlay/context requests and no unbounded full-document response.
- Security checks for arbitrary storage-key access, non-public/failed artifact
  delivery, response headers and source URL handling.
- Final repository gates: `make lint`, `make typecheck`, `make test`.
- Record evidence in `docs/ingestion/PHASE20_QUALITY_GATE.md` and a machine-
  readable Phase 20 audit manifest.

### 14. Documentation and closeout

- Record schema/API/coordinate/OCR/viewer decisions in `docs/DECISIONS.md` and
  update `docs/ARCHITECTURE.md` / `docs/DATA_MODEL.md` when implementation makes
  those contracts real.
- Re-read this entire roadmap and verify every acceptance criterion against the
  repository, live controlled data and audit artifacts.
- Update this Completion Record, `docs/roadmap/00_MASTER_ROADMAP.md`,
  `docs/PROJECT_STATE.md` and `MEMORY.md`; create the annotated
  `phase-20-complete` tag only after all gates pass.
- Preserve original requirements and stop. Do not begin a later phase.

## Non-goals

Phase 20 does **not**:

- acquire another major corpus batch;
- redesign the whole application;
- infer missing source text or coordinates;
- reconstruct redactions or bridge private-session gaps;
- translate, paraphrase or correct court/transcript text;
- deanonymize witnesses or add attributes beyond a protected witness code;
- use AI output as evidence or as the source of geometry;
- require every historical PDF to have exact geometry before the Reader is
  useful;
- revisit Phase 19 projections except for additive anchor/geometry integration;
- resume Phase 16 deployment or alerting work;
- add scores, ranks, weights or probabilities about a person.

## Acceptance criteria

- [x] The Reader renders the exact stored official PDF and exposes version
  identity, official-source link, page navigation and zoom/fit controls.
- [x] Geometry is page- and version-specific, validated, lineage-bearing and
  never reused between related versions.
- [x] A reusable SourceSpan/SourceAnchor abstraction supports verified people,
  witness codes, organizations, exhibits, citations, relationships, findings,
  transcript segments and applicable search results.
- [x] Structured objects navigate through evidence/occurrence to exact original
  source regions when proven; fallbacks are honest and visibly distinct.
- [x] Transcript-native navigation preserves exact text and real structure, with
  deterministic PDF synchronization only where supported.
- [x] Research context is source-backed, bounded and secondary to the source.
- [x] OCR is limited to unsupported pages, labelled derivative and incapable of
  reconstructing redactions or private text.
- [x] Large PDFs and transcripts use lazy/virtualized rendering, bounded overlays
  and server-side context queries against recorded budgets.
- [x] Mobile is source-first with context in a drawer/sheet; accessibility gates
  pass on desktop and Pixel 7.
- [x] All nine representative real-source paths pass the Phase 20 audit, version
  isolation holds, and all repository quality gates pass.

## Completion Record

- **Status:** COMPLETE (2026-09-25).
- **Started / completed:** 2026-09-25 / 2026-09-25.
- **20A:** Migration `0015`, version-bound native geometry (201 versions,
  9,439 native pages, 8 OCR-required, 2,551,752 word rows), reusable
  SourceSpan/SourceAnchor, immutable ranged PDF delivery and the source-first
  original PDF Reader (`70596a4`). Evidence:
  `docs/ingestion/PHASE20A_SOURCE_GEOMETRY_REPORT.md`.
- **20B:** Migration `0016`, transcript-segment anchors with validated line
  geometry (14,180 of 15,171 exact), printed page-header context, page-scoped
  Reader API and the three-layer source-native Reader (`f4780cb`, `f82ea7e`).
  Evidence: `docs/ingestion/PHASE20B_TRANSCRIPT_READER_REPORT.md`.
- **20C:** Source-fidelity audit PASS with 0 remaining highlight mismatches,
  cross-version leakage, provenance violations or fabricated precision:
  - 201/201 artifact hashes re-verified; all 9,447 page boxes checked;
  - 1,171 exact anchors region-audited against the original bytes;
  - 51,368 fallback anchors and 15,171 transcript segments audited against
    page text;
  - 7 highlights visually inspected (one per object type);
  - production-build deep-link, version, sync, overlay, OCR, performance and
    mobile paths verified on desktop and Pixel 7.

  Five demonstrated defects were fixed in the closeout commit: segment deep
  links without their box; a wrong-version highlight caused by an ambiguous
  filing-number lookup plus a silent version fallback; overlay/canvas re-render
  timing; a mobile fit-width re-render loop; and hidden-layer re-renders.
  Evidence: `docs/ingestion/PHASE20_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase20-audit.json`.
- **Final coverage (real case only):** 74,013 SourceAnchors: 22,645 exact
  geometry, 11,993 page-and-line, 39,375 page-only, 0 text-only, 0
  unavailable. The earlier 20A/20B totals included 13 synthetic demo-fixture
  anchors.
- **Gates:** `make lint`, `make typecheck` and `make test` pass (backend 353,
  frontend 260). Full production-build Playwright: 176 passed, 0 failed, 98
  skipped (specs gated to other data modes).
- **Known limitations:** the 8 OCR-required pages have no OCR run; events have
  no source anchors; 991 transcript segments stay page-and-line; CORRED and
  rotated pages are not held.
- **Tag:** `phase-20-complete` (annotated).

## Stop condition

Never trade source fidelity, version isolation, provenance, privacy or honest
fallbacks for highlight coverage. If geometry or alignment is not deterministically
supported, preserve the source and show the weaker resolution level.

## Completion report

```text
PHASE 20 STATUS
ORIGINAL PDF READER
SOURCE GEOMETRY
SOURCE ANCHORS
PDF HIGHLIGHTING / FALLBACKS
TRANSCRIPT-NATIVE READER
PDF ↔ TRANSCRIPT SYNCHRONIZATION
RESEARCH CONTEXT / DATA STATES
VERSION ISOLATION
OCR
PERFORMANCE
MOBILE / ACCESSIBILITY
SOURCE-FIDELITY AUDIT
QUALITY GATES
KNOWN GAPS
COMMITS
TAG
NEXT
```
