# Ingestion

**Status (Phase 8 complete, 2026-09-20): 22 real public records of
`KSC-BC-2020-06` ingested from operator capture bundle `2026-09-20-corpus-01`
— 22 source records, 19 documents, 22 versions (all bytes held), 2 hearings,
3 transcripts; quality gate 22/22; idempotent re-run verified
(`docs/ingestion/CONTROLLED_CORPUS.md`).** No crawler runs: the official sites
answer automated clients with a Cloudflare challenge, which is an access
control (ADR-011, `docs/ingestion/OFFICIAL_SOURCES.md`). Records enter through
operator capture bundles (`docs/ingestion/OPERATOR_CAPTURE.md`), imported with
`ksc-ingest import-capture` and verified with `ksc-ingest gate`. All 22 held
versions are parsed and indexed; see `docs/ingestion/PHASE8_QUALITY_GATE.md`.

## Rules that precede any code

- Official public sources only (docs/SECURITY.md): `www.scp-ks.org`,
  `repository.scp-ks.org`. Never bypass access controls or challenges, never
  guess URLs, never reconstruct redactions, never infer a protected identity.
- Controlled before bulk (ADR-003): 10–20 human-selected records, each
  human-checked, before any wider run (Phase 13).
- Every stored object carries the official artifact URL, SHA-256, byte size,
  fetch time, fetch method and an audit-log entry.
- Respect the court website: identified user agent, one request at a time,
  robots first. If robots cannot be read, the host is closed.

## Pipeline (`workers/ingestion`, `ksc_ingestion`)

```text
import       operator capture (snapshots + manifest + separately downloaded PDFs)
             → PDFs matched by exact SHA-256 → references derived from the
             published id and confirmed against the PDF header (ADR-012)
             → project bundle data/captures/<id>/ (capture_import)
discover     capture bundle → DiscoveredRecord (official detail URL, listing URL,
             external record id, metadata snapshot, artifacts with official URLs)
source       upsert source_records (case, source_system, external_record_id):
             discovery provenance, kept separate from the entity and the file
normalize    official_ref / filing_number / version refs / version type /
             party / dates; visibility from the classification text, fail closed
gate         PUBLIC or PUBLIC_REDACTED only; NOT_PUBLIC / UNKNOWN → the document
             is *stated* (identifier known, nothing held), never fetched
bytes        captured file → PDF check → SHA-256 → object storage
             documents/<case>/<version ref>/<sha256>.pdf (hash-addressed, never overwritten)
persist      documents (case, official_ref) · document_versions (document,
             official_version_ref) · hearings / transcripts for transcript records
job          ingestion_jobs (cursor, checkpoint, counts) · ingestion_job_items
             (one terminal status per record) · audit_log
gate         re-read every record from the database and the object store and
             compare with the bundle (quality_gate)
parse        held MinIO PDF only → native text pages → numbered paragraphs /
             sections → structural chunks; transcripts additionally preserve
             printed page and explicit line ranges (pdf_parser, parse_pipeline)
resolve      exact citation extraction → record_identifiers / held-coordinate
             lookup → persisted RESOLVED / AMBIGUOUS / UNRESOLVED / INVALID
index        generated PostgreSQL tsvector columns + GIN indexes; no embeddings
```

Item statuses: `downloaded` · `metadata_only` (URLs recorded, bytes not
fetched) · `skipped_duplicate` · `not_public` · `failed_download` ·
`blocked_by_access_control` · `invalid_metadata` · `unsupported_artifact` ·
`ambiguous_mapping`. The last five are failures and count in
`ingestion_jobs.failed_count`; nothing is discarded silently.

## Identity and idempotency

| thing                | identity                                                           |
| -------------------- | ------------------------------------------------------------------ |
| discovery provenance | (`case`, `source_system`, `external_record_id`) — the PCR `doc_id` |
| document             | (`case`, `official_ref`) — e.g. `KSC-BC-2020-06/F00005`            |
| version              | (`document`, `official_version_ref`) — e.g. `…/F00005/RED`         |
| bytes                | `sha256` (unique across all versions)                              |

Re-running a bundle re-uses an unfinished job (resume: items already terminal
are skipped) or, once a job completed, opens a new job whose items all resolve
to `skipped_duplicate` / `metadata_only`. A version that already holds
different bytes is `ambiguous_mapping` — never overwritten. Identical bytes
under a second reference are `skipped_duplicate` with a pointer to the held
version. A `not_fetched` version is filled in place when its bytes arrive later.

## Versions

Original, public redacted (`/RED`), corrected (`/COR`), reclassified and
translated variants are separate `document_versions` rows of one document, each
with its own official URL, hash and visibility. Type precedence when the source
does not state it: public redacted > corrected > reclassified > translation
(artifact language ≠ record language) > original.

## Metadata provenance

`source_records.raw_metadata.metadata_source` says where the record's metadata
came from: `official_page` (parsed from a saved raw official page — interface
only, no such page captured yet), `capture_snapshot` (normalised snapshot of the
official detail page built in the browser session — the 2026-09-20 corpus),
`operator_manifest` (typed into the manifest), `synthetic_fixture` (tests
only). The quality gate compares `official_page` values against the page; it
treats `operator_manifest` values as needing a second look.

## Live requests

`ksc-ingest probe <official url> [--record]` makes one identified request. A
challenge is reported as `blocked_by_access_control`; `--record` persists it as
a one-item job. This is the only network path and it stores no record.

## Phase 8 parsing and indexing

`ksc-ingest parse` reads only already-held objects; it has no network path.
Parser name/version, timestamp, extraction method, review state, and notes are
persisted per version. PDF page index is always present; printed page is nullable
and is never backfilled from the PDF index. Citation source character spans and
all target coordinates are persisted. Non-resolved citations keep no target and
display `UNRESOLVED`. Search is lexical PostgreSQL FTS plus exact normalized
identifier lookup (ADR-013); embeddings remain unauthorized and absent.

## Date and language rules

A document's own date, its filing date and its public date are separate columns
and are never inferred from one another. Documents are stored in the language
filed; official translations are separate versions (`translation`). Nothing is
machine-translated.

## Status tracking

`GET /api/v1/ingestion/status` (internal) and `ksc-ingest status` show counts,
jobs, items and held versions with provenance. `MEMORY.md → Ingestion State`
and `docs/PROJECT_STATE.md` carry the live counts.
