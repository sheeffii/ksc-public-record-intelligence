# Phase 8 — Parsing, Exact Citations, Resolution & Search

**Status:** Pending.

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

- controlled real documents are parsed;
- transcript page/line model works on real samples;
- citation extraction/resolution is persisted;
- unresolved/ambiguous states are reliable;
- fake citations fail;
- exact source navigation works;
- search works on real corpus;
- selected UI screens can consume real structured data;
- all prior tests continue to pass.

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
