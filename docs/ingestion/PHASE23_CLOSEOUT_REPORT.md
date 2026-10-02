# Phase 23 closeout report (23C)

Branch `feat/phase-23-closeout`, cut from `main` at `78b192c` on 2026-10-02.
This report covers 23A–23C. The 23A pilot report the roadmap asked for was
never written separately; its numbers are in `MEMORY.md` and are summarised
here.

**Result: NOT READY for `phase-23-complete`.** Reconciliation, integrity and
the repository gates pass. Three acceptance items stay open (see "Open
issues").

## Acquisition (23A–23B)

| Batch                        | Bundles | Verified versions | Refused |
| ---------------------------- | ------- | ----------------- | ------- |
| 23A pilot                    | 1       | 93                | —       |
| `2026-09-30-phase23b-*`      | 6 + 6   | 494 + 470         | —       |
| `2026-09-30-phase23c-01..11` | 11      | 960               | 13      |
| `2026-10-01-ltd-01..17`      | 17      | 1,590             | 21      |
| `2026-10-02-ltd-01..04`      | 4       | 351               | 4       |
| `2026-10-02-official-gap-01` | 1       | 1                 | 0       |

Legal Tools acquisition is exhausted. Mirror paging is unstable, so six
metadata sweeps were unioned; the union observed all 5,049 mirror records and
leaves 0 genuinely eligible records (7 listed records are byte-identical to
held ones). The one record whose mirror PDF returned 404 (F03256/RED) was
captured from the official repository with the operator collector.

## Reconciliation (23C)

Canonical order, corpus-wide: structured projection → re-resolve →
re-resolve → mentions → evidence → intelligence → legal matrix → transcript
sync → SourceAnchors.

|                            | Before  | After   |
| -------------------------- | ------- | ------- |
| Citations resolved         | 94,697  | 119,427 |
| Citations unresolved       | 44,077  | 19,201  |
| Citations ambiguous        | 6,093   | 6,159   |
| Citations invalid          | 7,816   | 7,896   |
| Relationships              | 113,315 | 138,299 |
| `cited_in` edges           | 94,447  | 119,177 |
| Entity occurrences         | 222,494 | 226,759 |
| SourceAnchors              | 480,574 | 678,936 |
| Transcript-segment anchors | 15,171  | 161,202 |

The second re-resolve reproduced the first exactly, so resolution is stable.
Transcript sync covers 496 transcripts and 161,202 segments (146,332 exact
geometry, 14,870 page and line); 13,188 closed-session segments stay withheld.
`process-new` never ran transcript sync, which is why segment anchors were
missing for mirror transcripts until now.

Findings (2), incidents (1), appeal issues (1), arguments, research notes,
AI runs and outputs, external sources and human-verified relationships kept
their content; the only change on human-curated rows is `source_anchor_id`,
which the legal-matrix projection re-points (it writes no other column).

## Integrity

- 4,160 KSC-BC-2020-06 versions, 3,516 documents, all parsed.
- Missing v2 geometry: only the synthetic demo fixture
  `KSC-DEMO-0000/F-DEMO-001/RED`.
- 0 duplicate anchor keys, 0 anchors without a span, 0 relationship, mention,
  citation or transcript-segment anchors off their evidence version.
- 0 deterministic citation edges on unresolved citations; 0 AI-originated
  relationships.
- 60 ingestion jobs, all completed. Three processing runs interrupted by a host
  reboot, a manual stop and a 2026-09-24 run that never finished are marked
  `failed` with the reason in `detail`.

## Gates

| Gate                              | Result                                                        |
| --------------------------------- | ------------------------------------------------------------- |
| `make lint`                       | pass                                                          |
| `make typecheck`                  | pass                                                          |
| `make test`                       | pass — 408 backend, 272 frontend                              |
| `gate-phase17c` (structured)      | pass                                                          |
| `gate-phase19a` (mentions)        | pass — 0 provenance violations, 0 dedup conflicts             |
| `gate-phase13` (real scale)       | pass — 4,160 accepted, integrity/performance/completion ready |
| `gate-phase14` (external sources) | pass                                                          |
| `gate-appeal`                     | pass                                                          |
| `gate-findings` (Phase 10)        | **fail** — see open issue 1                                   |
| `gate-ai` (Phase 11)              | **fail** — see open issue 2                                   |

## Scale

API, warm (live stack): `/documents` 0.8 s (50 rows; total 3,516), `/people`,
`/witnesses` 0.4–0.5 s (200 rows), `/events` 0.1–0.2 s (200 rows; total
3,757), `/search` 0.1–0.6 s, `/network?limit=500` 0.5 s. API totals equal the
per-case database counts for documents, people, witnesses, exhibits, events
and organisations. Web: `/timeline` 2.5 s, `/documents` 5.2 s, both showing
the same totals.

## Fixes made during 23C

- `abb7bbf` — the legal-matrix projection also replaces the edges it owns by
  deterministic id; migration 0019 had rewritten one edge's note, so the
  projection had collided on every run since Phase 22C.
- `222916b` — migration 0020 indexes `source_anchors.source_span_id`; cascaded
  span deletes scanned the whole anchor table, which made a full anchor rebuild
  take hours. The case seed no longer claims no documents are ingested (live
  row corrected with an audit entry).
- `56edc82`, `6b53b56`, `4c73761`, `656f024` — formatting already failing the
  lint gate on `main`, migration-head assertions stuck at `0017`, and tests
  that left demo-case state behind in the persistent test database.

## Open issues (block the tag)

1. **Findings gate.** It requires the held corpus to equal the 22-version
   Phase 7 manifest, which corpus expansion breaks by design. Separately, the
   hand-verified text of finding `FD-F03752-P12-16` includes the heading
   "B. THIRD AMENDMENT", which parser v4 (2026-09-28, before Phase 23) now
   keeps out of the paragraph text, so the exact paragraph mapping is 0/1.
   Needs an owner decision on the pinned-corpus criterion and on how the
   finding text maps to v4 paragraphs.
2. **AI gate.** Two of three expected abstentions now answer: F03743 and
   F03746 were acquired in Phase 23, so "missing filing" no longer applies.
   The answers are grounded and correctly labelled (citation, category and
   quote accuracy 1.0) but come from the Court's summary of each party's
   position in F03752, not from the newly held filings. The evaluation set
   needs new expectations, and retrieval should prefer the requested filing's
   own text.
3. **Directory scale.** Web directories load every row (18 sequential requests
   for documents) and filter in the browser. Usable at 3,516 documents
   (5.2 s) but this is the server-driven directory work the 23B plan asked for.

Also open, not blocking: `process-new` does not run transcript sync, so new
transcripts need `project-transcript-sync` until it does.
