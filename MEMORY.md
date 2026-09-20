# KSC Public Record Intelligence — Project Memory

Live checkpoint. Repository state wins over this note.

## Current status

- Current branch: `feat/phase-8-parsing-search`.
- Current milestone: **Phase 8 complete (2026-09-20)**. Stop before Phase 9.
- Completion tag: `phase-8-complete` at the final Phase 8 documentation commit.
- Migration head: `0004`.
- Phase 7 prerequisite: complete; tag `phase-7-complete` exists. The controlled
  bundle `data/captures/2026-09-20-corpus-01/` has 22 official public PDFs and
  the tracked reproducibility manifest is
  `docs/ingestion/manifests/phase7-controlled-corpus.json`.
- Phase 8 quality result: `docs/ingestion/PHASE8_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase8-controlled-corpus-quality.json`.
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

## Verification

- Backend unit: 168 passed.
- Backend integration: 68 passed.
- Frontend: 188 passed; ESLint, TypeScript and Prettier pass.
- Final `make lint`, `make typecheck`, `make test`, production build, migration
  drift/round-trip, live stack health, real API/UI smoke checks, and Playwright
  (96 passed, 2 skipped) all passed before the checkpoint tag was created.

## Architecture / decisions

- ADR-001–012 remain in force; ADR-013 records native structural parsing,
  coordinate separation, deterministic persisted resolution, and lexical-only
  Phase 8 search.
- Migration `0004_parsing_citations_search.py` adds parsing provenance,
  `document_paragraphs`, exact source/target coordinates, and generated FTS
  indexes.
- Parser/resolver/pipeline:
  `workers/ingestion/src/ksc_ingestion/{pdf_parser,citation_resolution,parse_pipeline}.py`.
- Real-corpus bytes stay git-ignored and hash-addressed in MinIO. The Phase 7
  capture manifest remains the reproducibility anchor.

## Known limitations

- OCR is not implemented because none of the controlled PDFs needs it. A future
  OCR fallback must label extraction method and confidence/review state.
- The small natural corpus contains no ambiguous citation; an overlapping-page
  fixture verifies the fail-closed state.
- Most syntactically valid cited filings are outside the controlled corpus and
  correctly remain unresolved until a later authorized corpus expansion.
- Phase 9 real evidence-network/timeline work has not started.

## Next

Await explicit authorization for Phase 9. First inspect repository state and
read the complete Phase 9 roadmap. Do not bulk-ingest or begin AI work.

## Non-negotiable rules

- Official public sources only; never bypass the court's access controls.
- Never fabricate identifiers, source coordinates, citations, quotes, or facts.
- Protected witnesses stay code-only. No person score/rank/weight/probability.
- Database + primary sources + persisted provenance are authoritative.
- Do not edit `docs/design/`; do not push without explicit instruction.
