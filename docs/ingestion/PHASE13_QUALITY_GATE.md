# Phase 13 real-corpus quality gate

Date: 2026-09-22

Status: **PASS — 61 accepted real public records (required: 50)**

This gate uses the actual lawfully captured `KSC-BC-2020-06` corpus: the
controlled bundle `2026-09-20-corpus-01` (22 records) plus the
operator-assisted bundle `2026-09-21-corpus-02` (40 selected, 39 accepted).
Synthetic fixtures live in another case and can never satisfy the threshold.
The machine-readable result is `phase13-quality-gate.json`.

## Actual corpus

- source records: 62 · documents: 56 · versions: 61 (all fetched, all parsed)
- accepted real records (public, hash-verified, not quarantined): **61 / 50**
- immutable objects: 61, 36,443,971 bytes
- pages: 2,832; paragraphs: 2,019; transcript segments: 1,363
- citations: 15,730 — 188 resolved, 3 ambiguous, 15,420 unresolved, 119 invalid
- fetched non-public versions: 0
- missing objects / hash mismatches: 0 / 0
- open quarantine: 1 (nothing stored for it) · quarantined parsed versions: 0
- parser review required: 1 (`F00002/A03`, an image-only annex)

Every held object's SHA-256 was recomputed from MinIO and matched its immutable
version row, and each matched a local capture file byte for byte. The scale
gate counts only versions that are explicitly public, hash-verified and free of
open quarantine.

## Corpus-02 acceptance

40 records were captured; 39 were accepted and one was refused. The refusal is
`r31` (published `F03734RED`), whose PDF header prints
`KSC-BC-2020-06/F03734` while the repository publishes `F03734RED`. The
importer marked the reference ambiguous, normalisation failed closed, ingestion
recorded `ambiguous_mapping`, an open quarantine row was created and **no
DocumentVersion, object or citation was written**. No mapping was guessed and
no rule was relaxed to reach the threshold.

A second record, `r37` (`PL003-F00004`), was initially unrecognised because the
importer knew only the `IA` sub-file series. The protection-of-legality series
follows the same published convention and the PDF header confirms
`KSC-BC-2020-06/PL003/F00004/sqi`, so `PL` was added alongside `IA` in the
importer and the citation resolver, with unit tests.

## Idempotency

Re-running the same bundle produced 39 `skipped_duplicate` outcomes and one
unchanged refusal: no new source records, documents, versions or objects, no
rewritten hashes or object keys, and exactly one open quarantine row.

## Lineage safety

Every citation referenced by a Phase 9–12 row is still `resolved` and still
points at a pre-existing target (relationships 34, events 5, findings 2,
evidence links 4, argument responses 5, appeal issue sources 5, statement
comparisons 2, AI output citations 120, research-note citations 6). Fingerprints
over the authoritative Phase 10–12 tables and over the 22 corpus-01 versions are
unchanged through ingestion, forced reparse and re-resolution. The Phase 9
deterministic projection was rebuilt from the larger corpus: 48 nodes, 178
citation-backed edges, 54 source-backed events, and no edge rests on a
non-resolved citation.

## Performance

On the local PostgreSQL corpus at 61 held versions: document FTS 1.16 ms, exact
identifier lookup 0.75 ms, 100-row network neighbourhood 1.17 ms; threshold
500 ms. PostgreSQL FTS still needs no separate search engine and the graph
stays within SVG range. These are local single-node figures, not a claim about
production hardware or a several-hundred-record corpus.

## Access and acquisition

The official repository continues to answer automated clients with a Cloudflare
challenge; two live-probe items remain `blocked_by_access_control`. Capture is
operator-assisted: the operator's own visible Chrome, with any challenge
completed by hand (ADR-019). No bypass was attempted at any point.

## Backup / restore

A checksum-verified backup of the scaled corpus was restored into an isolated
PostgreSQL database and MinIO bucket: migration `0009`, 61/61 objects verified
by SHA-256, 36,443,971 bytes, matching row counts. The isolated database,
bucket and temporary backup were removed afterwards.

## Downstream gates

The Phase 10, 11 and 12 real-corpus gates were re-run against the combined
pinned manifest `manifests/phase13-controlled-corpus.json` (61 verified
records) and all pass, with AI audit history and human-verification states
unchanged.

## Decision

Integrity, operational architecture, observability, lineage safety and
current-corpus performance pass, and the genuine scale criterion passes at
61/50 accepted records. Phase 13 is complete and tagged `phase-13-complete`.
Phase 14 does not begin.
