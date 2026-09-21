# Phase 13 real-corpus quality gate

Date: 2026-09-21

Status: **FAIL — REAL SCALE UNAVAILABLE; ARCHITECTURE / INTEGRITY / PERFORMANCE READY**

This gate uses the actual lawfully captured `KSC-BC-2020-06` corpus. Synthetic
fixtures test mechanics only and are excluded from the completion threshold.
The machine-readable result is `phase13-quality-gate.json`.

## Actual corpus

- source records: 22 (required first scale step: 50)
- documents: 19
- versions: 22, all fetched and parsed
- immutable objects: 22, 24,429,094 bytes
- pages: 1,979; paragraphs: 1,233; transcript segments: 607
- citations: 14,212 — 30 resolved, 0 ambiguous, 14,105 unresolved, 77 invalid
- fetched non-public versions: 0
- missing objects / hash mismatches: 0 / 0
- open quarantine / quarantined parsed versions: 0 / 0

Every held object's SHA-256 was recomputed from MinIO and matched its immutable
version row. A repeat capture-bundle run produced 22 duplicate outcomes, no new
bytes, and populated 22 immutable source snapshots. Re-resolution preserved all
downstream foreign keys. Forced parsing reconciles stable derived-row IDs in
place and refuses structural identity changes that need explicit review.

## Performance

On the local PostgreSQL corpus, document FTS, exact identifier lookup and a
100-row network-neighborhood query each completed below 3 ms. The gate threshold
is 500 ms. These figures demonstrate the current corpus needs no separate search
engine; they are not a claim about untested production hardware or 50+ records.

## Access and acquisition

An identified, robots-aware probe on 2026-09-21 received HTTP 403 for
`https://repository.scp-ks.org/robots.txt` with `cf-mitigated: challenge`.
Failure job `4134154a-5026-4ebc-ba04-75a20bcc42ca` records the evidence. The
client stopped and did not retry or evade the challenge. Metadata inventory,
bounded queueing and browser-assisted operator capture are ready for the next
authorized lawful batch.

## Backup / restore

A checksum-verified backup was restored into an isolated PostgreSQL database
and MinIO bucket. The restore reached migration `0009`, recovered all 22 objects
and 24,429,094 object bytes, and retained the complete database corpus. The
isolated database, bucket and temporary backup were removed after verification.

## Resumed verification (same day)

The closeout audit re-ran the gate after a forced reparse of all 22 versions
and a citation re-resolution: the report was identical apart from latency
figures (1.1–1.7 ms). A lineage fingerprint over every downstream table
(citations with resolution state and targets, relationships, events, findings,
evidence links, arguments, AI runs/sources/output citations, appeal issue
sources, statement comparison, red-team findings, research-note citations,
parser rows and version hashes) was byte-identical before and after; only
`processing_runs` grew from 3 to 5. A second checksum backup restored into an
isolated database and bucket with the same fingerprint, migration `0009`, and
22/22 objects verified by SHA-256 (24,429,094 bytes); the isolated targets were
removed. A single identified probe again received HTTP 403
`cf-mitigated: challenge`. Open-quarantine versions are now excluded from
parse/resolution selection by code, not only by construction.

## Decision

Integrity, operational architecture and current-corpus performance pass. The
mandatory genuine scale criterion fails because 22 is below 50. Phase 13 stays
in progress, no completion tag is created, and Phase 14 does not begin. The gate
must be rerun after a lawful official inventory/capture expands the corpus.
