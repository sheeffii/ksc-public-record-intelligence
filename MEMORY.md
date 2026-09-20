# KSC Public Record Intelligence — Project Memory

Live checkpoint. Repository state wins over this note.

## Current status

- Current branch: `feat/phase-9-real-evidence-network-timeline`.
- Current milestone: **Phase 9 complete (2026-09-21)**. Stop before Phase 10.
- Completion tag: `phase-9-complete` at the final Phase 9 closeout commit.
- Final Phase 9 implementation commits: `431f1dd` and `ac59afa`; verified
  code/test baseline `548a151`; the subsequent roadmap closeout commit records
  the final audit and completion metadata.
- Migration head: `0005`.
- Phase 7 prerequisite: complete; tag `phase-7-complete` exists. The controlled
  bundle `data/captures/2026-09-20-corpus-01/` has 22 official public PDFs and
  the tracked reproducibility manifest is
  `docs/ingestion/manifests/phase7-controlled-corpus.json`.
- Phase 9 quality result: `docs/ingestion/PHASE9_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase9-controlled-corpus-quality.json`.
- Never push unless explicitly instructed.

## Phase 8 result

- All 22 held versions parsed with native text (`ksc-native-pdf/2`): 1,979
  pages, 1,233 numbered paragraphs, 1,592 structural chunks, 607 transcript
  segments; zero review-required versions and no OCR.
- Exact coordinate layers remain distinct: PDF index, printed/source page,
  paragraph, transcript page, and transcript line. Missing values stay NULL.
- Citation extraction stores exact raw text and source character/PDF coordinates.
  Persisted resolver counts: 14,205 total · 23 resolved · 0 ambiguous in the
  natural corpus · 14,105 unresolved · 77 invalid. Every non-resolved row is
  targetless and displays `UNRESOLVED`; ambiguity is integration-tested.
- PostgreSQL exact-ID + lexical FTS supports phrase/keyword search and document,
  language, party, source, and date filters. Results carry version and exact
  source-navigation coordinates. No embeddings or model calls exist.
- Search and Document Reader routes server-load the configured repository;
  real mode suppresses demo-only reader/search content.
- No additional material was fetched and the full KSC corpus was not ingested.

## Phase 9 result

- A deterministic database-only projection creates 13 public document nodes and
  22 `CITED_IN` edges from the controlled corpus's 23 resolved citations; one
  self-citation is omitted. No analytical or unsupported edge was created.
- Every edge retains subject/object, precise type, source category, verification,
  extraction origin, optional date, resolved target citation, and exact persisted
  citing-source coordinates/link.
- Evidence Path is bounded shortest-hop BFS over public, resolved, non-rejected,
  non-analytical edges. Every hop is independently cited and the required
  non-inference warning remains verbatim.
- Timeline has 19 source-record-backed real events: 11 document, 6 decision and
  2 testimony dates. All dates present in the controlled corpus are explicitly
  exact; missing categories remain absent.
- Network, Path and Timeline server-load real API data in API mode. Network has
  node search plus source, verification, true from/to date, entity and
  relationship filters, inspectors, expand/collapse, isolate, reset,
  exact-source links and a textual alternative.
- Measured graph scale is 13 nodes / 22 edges, so SVG remains appropriate.
  ADR-014 records this decision and the provenance/path rules.

## Verification

- Backend unit: 168 passed.
- Backend integration: 70 passed (238 backend total).
- Frontend: 191 passed; ESLint, TypeScript and Prettier pass.
- Final `make lint`, `make typecheck`, `make test`, production build, migration
  drift/round-trip, live stack health, real API/UI smoke checks, and Playwright
  (96 passed, 2 skipped) all passed before the checkpoint tag was created.
- The final roadmap closeout audit re-read the complete Phase 9 specification
  and verified every acceptance criterion against code, migration `0005`, tests,
  the live API/database, and the pinned real-corpus quality gate. The Phase 9
  roadmap and master roadmap carry current completion metadata.

## Architecture / decisions

- ADR-001–013 remain in force; ADR-014 records deterministic citation-backed
  edges, source-metadata timeline events, path eligibility and measured SVG scale.
- Migration `0005_real_evidence_network_timeline.py` adds relationship
  source/origin/date provenance and timeline source-record provenance.
- Parser/resolver/pipeline:
  `workers/ingestion/src/ksc_ingestion/{pdf_parser,citation_resolution,parse_pipeline,evidence_pipeline}.py`.
- Real-corpus bytes stay git-ignored and hash-addressed in MinIO. The Phase 7
  capture manifest remains the reproducibility anchor.

## Known limitations

- OCR is not implemented because none of the controlled PDFs needs it. A future
  OCR fallback must label extraction method and confidence/review state.
- The small natural corpus contains no ambiguous citation; an overlapping-page
  fixture verifies the fail-closed state.
- Most valid citations target records outside the controlled corpus and remain
  explicitly unresolved; Phase 9 creates no edge from them.
- The controlled corpus has no approximate/range/month/year timeline date and no
  supported historical, filing-date, trial-judgment or later-appeal milestone;
  none was fabricated. Uncertainty rendering is component-tested.

## Next

Phase 10 is **NEXT / PENDING**. Await explicit authorization, inspect repository
state, and read the complete Phase 10 roadmap. Do not begin Phase 10 from this
checkpoint.

## Non-negotiable rules

- Official public sources only; never bypass the court's access controls.
- Never fabricate identifiers, source coordinates, citations, quotes, or facts.
- Protected witnesses stay code-only. No person score/rank/weight/probability.
- Database + primary sources + persisted provenance are authoritative.
- Do not edit `docs/design/`; do not push without explicit instruction.
