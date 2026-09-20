# Phase 8 — Parsing, Exact Citations, Resolution & Search

**Status:** Complete.

**Completed:** 2026-09-20.

**Completion commit:** `02ab3c8` (final verified code/test baseline; Phase 8
implementation ended at `9fc67c5`).

**Completion tag:** `phase-8-complete`.

## Goal

Transform the controlled real corpus into auditable structured text with exact source coordinates, build deterministic citation resolution, and provide reliable hybrid search over the real public records.

This is the phase where the platform becomes able to answer: “Where exactly in the public record is this?”

## Parsing hierarchy

Prefer structural parsing over blind chunking.

```text
DocumentVersion
  ↓
Pages
  ↓
Sections / paragraphs
  ↓
Transcript segments where applicable
  ↓
Structural chunks for retrieval
```

## PDF/text extraction

Use robust parsers such as PyMuPDF/pypdf/pdfplumber as appropriate.

OCR is fallback only.

If OCR is used:

- mark text as OCR-derived;
- preserve original page/image reference;
- do not pretend OCR text is exact when confidence is poor;
- route low-confidence extraction for review.

## Page preservation

Maintain the distinction between:

- PDF page index;
- printed/source page number;
- transcript page number;
- judgment paragraph number.

Never replace one with another silently.

## Transcript parser

Extract where possible:

- hearing date;
- transcript page;
- line numbers;
- speaker;
- witness code/public identity where lawful;
- examination type;
- segment sequence;
- text.

Never invent a line number.

When a transcript layout cannot be parsed confidently, mark the segment/record for review.

## Citation extraction

Identify references such as:

- document IDs;
- version IDs;
- exhibit IDs;
- witness codes;
- judgment paragraphs;
- transcript pages/lines;
- cross-case references.

Store the raw citation exactly enough for audit, plus normalized representation.

## Citation resolver

Implement the architecture planned since Phase 4:

```text
Raw citation
   ↓
Normalization
   ↓
Candidate lookup
   ↓
Deterministic resolution
   ↓
RESOLVED / AMBIGUOUS / UNRESOLVED / INVALID
   ↓
Persisted resolution
```

Do not re-resolve every citation on every request.

## Fake citation rejection

Create tests proving that plausible-looking but nonexistent identifiers do not resolve.

Examples should cover:

- wrong case;
- unknown filing;
- unknown witness code;
- impossible page/line;
- version suffix mismatch.

## Citation support validation

Begin building utilities that can verify whether a citation target exists and open the exact source coordinate.

Do not yet make AI judgments about semantic support unless clearly marked as later functionality.

## Search

Start with PostgreSQL-based search architecture:

- FTS;
- normalized identifiers/names;
- exact ID lookup;
- filters;
- pgvector semantic retrieval if and only if embeddings are explicitly authorized in this phase and source auditability is preserved.

Recommended approach is hybrid search later combining lexical + vector results with transparent rank fusion.

If embeddings are introduced:

- generate only from public parsed text;
- record model/version;
- retain chunk/source linkage;
- embeddings never replace exact citations.

## Search modes

Support:

- exact official ID;
- witness/exhibit code;
- phrase search;
- keyword search;
- filtered document search;
- transcript search;
- source-type filtering.

## Structured chunks

Chunk boundaries should prefer legal structure:

- section;
- paragraph group;
- transcript page/segment;
- exhibit/document subsection.

Avoid arbitrary fixed-size chunks that break citations across boundaries when possible.

## Quality evaluation

For the controlled corpus manually verify:

- parsed page text;
- paragraph mapping;
- transcript page/lines;
- citation resolution;
- exact-source opening;
- search ranking for known queries;
- fake-citation rejection.

## UI integration

Begin switching selected Document Reader / Transcript / Search screens from mock to real API data for the controlled corpus.

Keep a clear demo/real indicator if mixed data remains.

## Tests

Add:

- parser fixtures;
- version-specific parsing;
- transcript line tests;
- OCR fallback tests if used;
- citation normalization;
- deterministic resolution;
- ambiguity handling;
- unresolved handling;
- fake-citation rejection;
- search exact ID;
- search phrase;
- search filters;
- source-coordinate navigation.

## Acceptance criteria

- [x] controlled real documents are parsed;
- [x] transcript page/line model works on real samples;
- [x] citation extraction/resolution is persisted;
- [x] unresolved/ambiguous states are reliable;
- [x] fake citations fail;
- [x] exact source navigation works;
- [x] search works on real corpus;
- [x] selected UI screens can consume real structured data;
- [x] all prior tests continue to pass.

## Stop condition

Do not bulk-ingest the corpus and do not build broad AI analysis yet.

## Completion report

```text
PHASE 8 STATUS
PARSING
TRANSCRIPTS
CITATION EXTRACTION
CITATION RESOLUTION
SEARCH
REAL UI INTEGRATION
QUALITY EVALUATION
TESTS
KNOWN FAILURES
COMMITS
NEXT
MEMORY
```

## Completion Record

- Closeout audit: **PASS**, 2026-09-20. Every acceptance criterion above was
  checked against migration `0004`, repository code, automated tests, the live
  database, and the controlled-corpus quality gate.
- Controlled corpus: 22 records / 19 documents / 22 versions; all 22 parsed
  with `ksc-native-pdf/2` using native text. The persisted result contains
  1,979 pages, 1,233 numbered paragraphs, 1,592 structural chunks, and 607
  transcript segments; zero versions require review and no OCR was used.
- Citations: 14,205 persisted; 23 resolved, 14,105 unresolved, 77 invalid, and
  zero naturally ambiguous. Every non-resolved real-corpus citation is
  targetless and displays `UNRESOLVED`; deterministic ambiguity is verified by
  an integration fixture.
- Search/navigation: exact identifier, phrase, keyword, filtered document,
  transcript, source-type, and exact-coordinate navigation checks pass on the
  real corpus. The known phrase probe opens transcript page 29,009, line 8.
- Real UI: the selected Search and Document Reader/Transcript routes consume
  the API repository in real-data mode and display a real/mixed-data notice.
- Tests/gates: `make lint`, `make typecheck`, `make test`, and `make build`
  passed; 236 backend tests and 188 frontend tests passed; Playwright reported
  96 passed and 2 skipped. Migration downgrade/re-upgrade and model/schema
  drift checks passed. The five-service local stack and readiness checks passed.
- Scope: no additional court material was fetched, no bulk corpus was ingested,
  no embeddings or broad AI analysis were added, and Phase 9 was not started.
- Evidence: `docs/ingestion/PHASE8_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase8-controlled-corpus-quality.json`.
