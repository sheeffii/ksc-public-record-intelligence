# Phase 10 — Judgment, Findings & Evidence Matrix

**Status:** Complete.

**Completed:** 2026-09-21.

**Completion commit:** `c8eaa1e` (final verified implementation/data baseline;
the subsequent roadmap closeout commit records completion metadata).

**Completion tag:** `phase-10-complete`.

## Goal

Turn the public judgment and related record into a structured finding-by-finding research system showing what the Court found, where it found it, which evidence it explicitly relied on, what the parties argued, and what other relevant public material exists.

This phase is the core legal-research layer before AI.

## Preconditions

- real documents/transcripts parsed;
- citations resolve;
- judgment paragraphs are addressable;
- real relationships/timeline work;
- public visibility rules are enforced.

## Judgment ingestion/structure

For the public judgment:

- preserve document/version;
- parse sections/headings;
- preserve paragraph numbers;
- create paragraph-level citation targets;
- map findings without replacing the original text with summaries.

## Finding model population

For each structured court finding, store:

- finding key;
- exact court finding text or precise referenced passage;
- judgment paragraph range;
- related charge/legal element/incident/person where public and appropriate;
- verification state.

Do not use AI-generated paraphrase as canonical finding text.

## Evidence relied upon

Create `FindingEvidenceLink` records for evidence the judgment explicitly relies on.

Distinguish:

- explicitly cited by Court;
- related but not explicitly cited;
- supporting;
- qualifying;
- contextual.

Do not silently label evidence “contradictory” as a Court relationship unless the Court/source supports that representation.

## Evidence Matrix

Build a matrix that can answer:

```text
Finding
→ judgment paragraphs
→ evidence explicitly cited
→ source type
→ witness/document/exhibit
→ exact citation
→ verification
→ relevant supporting/qualifying/contrary material
→ Defence argument
→ SPO argument
→ Court response
```

## Corroboration view

Allow researchers to inspect what types of material support a finding:

- witness testimony;
- documents;
- exhibits;
- video/media admitted into record if already modeled as court evidence;
- forensic/physical material if present in public record;
- other sources.

Use neutral wording such as:

> No additional corroborating source has been identified in the indexed public record.

Do not say “there was no evidence” merely because one category is absent.

Witness testimony is evidence; the platform should instead show how it was treated/corroborated/challenged in the public record.

## Party positions

Link:

- Defence submissions;
- SPO submissions;
- Court reasoning/response.

Keep each source category visually and structurally separate.

## Finding Detail real-data conversion

Replace mock Finding Detail with real structured data.

The UI should let users move from:

```text
Court Finding
  ↓
Exact judgment paragraph
  ↓
Evidence relied upon
  ↓
Open exact source
```

## Source Audit

Add a per-finding audit view:

- all citations resolve?;
- any source missing?;
- any ambiguous version?;
- any transcript coordinate missing?;
- any relationship unverified?;
- public/redacted version used?;
- source explicitly cited by Court vs merely related?

## Human review

Use verification states aggressively.

Do not auto-promote extracted finding/evidence links without review if extraction is uncertain.

## Tests / evaluation

Create hand-verified benchmark findings for the controlled corpus.

Verify:

- judgment paragraph mapping;
- evidence links;
- party-position links;
- exact-source opening;
- no source category conflation;
- no unsupported “Court relied on” labels;
- source-audit correctness.

## Acceptance criteria

- [x] judgment is structurally navigable;
- [x] findings are first-class real entities;
- [x] explicit evidence relied upon is source-backed;
- [x] party positions are linked separately;
- [x] Finding Detail is real-data-backed;
- [x] Evidence Matrix is queryable;
- [x] source audit identifies unresolved gaps;
- [x] tests/evaluation pass.

## Stop condition

Do not let AI generate canonical findings or legal conclusions. AI begins in Phase 11.

## Completion report

```text
PHASE 10 STATUS
JUDGMENT STRUCTURE
FINDINGS
EVIDENCE MATRIX
PARTY POSITIONS
CORROBORATION VIEW
SOURCE AUDIT
QUALITY REVIEW
TESTS
COMMITS
NEXT
MEMORY
```

## Completion Record

- Closeout audit: **PASS**, 2026-09-21. Every requirement and acceptance
  criterion above was re-read and checked against migration `0006`, the
  committed implementation, automated tests, live real-case database/API/UI,
  and the pinned controlled-corpus quality report.
- Corpus scope: the existing 22-record Phase 7 corpus was used unchanged. It
  contains no Trial Judgment. No trial brief was substituted for one and no
  additional record was fetched. The real benchmark is explicitly the public
  Court **decision** `KSC-BC-2020-06/F03752`, not a merits judgment.
- Judgment structure/finding: one human-verified first-class finding stores the
  exact persisted paragraphs 12–16, the exact `F03752` document/version, parsed
  section structure, page/PDF coordinates, and a resolved paragraph target.
  The quality gate confirms byte-for-text equality with the five stored
  paragraphs; zero canonical findings were generated by AI.
- Evidence matrix: one `FindingEvidenceLink` records an explicit Court citation
  at paragraph 12 to the exact held `F03667/COR/RED` version. It has exact
  source page/paragraph/character coordinates, a resolved target, relationship
  basis/category, neutral explanatory note, and human verification. Zero
  unsupported relied-upon or contrary links exist.
- Positions/response: one SPO and one Defence position are stored separately as
  exact Court summaries at paragraphs 7 and 6. Their unavailable underlying
  sources (`F03746`, `F03743`) are marked `court_summary` and reported missing.
  One exact Court response at paragraphs 14–16 is linked separately to both
  positions; all six matrix relationships are human verified.
- API/UI/audit: `GET /api/v1/findings/{finding_key}/matrix` is queryable. Real
  Finding Detail shows Court finding, exact structural passage, evidence matrix,
  supporting/qualifying/contrary/contextual categories, party positions, Court
  response, human-note and AI-analysis boundaries, exact-source navigation, and
  source audit. Real mode has no demo flag and generates no AI analysis.
- Audit limitation: all five distinct linked citations resolve, while the audit
  reports two missing underlying party sources. The quality report additionally
  identifies the missing public Trial Judgment. Neutral empty-category wording
  is preserved and no network path is treated as proof.
- Tests/gates: `make lint`, `make typecheck`, `make test`, `make build`, migration
  `0005 → 0006`, `0006 → 0005 → 0006`, model-drift checks, idempotent finding
  projection, the real-corpus gate, and Playwright passed. Counts: 238 backend
  tests; 194 frontend tests; standard Playwright 96 passed / 4 skipped; real-data
  Phase 10 Playwright 2 passed across desktop and mobile.
- Evidence: `docs/ingestion/PHASE10_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase10-controlled-corpus-quality.json`.
- Scope stop: no Phase 11 RAG, model call, generated legal conclusion, score,
  or prediction was introduced.
