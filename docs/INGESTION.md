# Ingestion

**Status: not implemented.** No crawler, downloader, parser, OCR or indexer exists.
Ingestion counts are 0. This document is the plan and the rules.

## Rules that precede any code

- Official public sources only (docs/SECURITY.md). Never bypass access controls,
  never guess URLs, never reconstruct redactions.
- Controlled before bulk (ADR-003): one document end to end, human-checked, before
  any corpus-wide run.
- Every stored object carries `source_url`, `sha256`, fetch time and an audit-log
  entry.
- Respect the court website: rate limits, robots rules, identifying user agent,
  no parallel hammering.

## Planned pipeline

```
discover      list public filings/decisions/transcripts/exhibits for the case
download      fetch one official public URL; verify content type; hash
store         MinIO object under documents/<official_ref>/<sha256>.pdf
parse         text + layout per page; running heads; page numbers; footnotes
segment       paragraphs (¶), transcript Q/A blocks with T. page + line ranges
redactions    detect and record extents; never fill
extract       raw citations: F#####, F#####/RED, P#####, D#####, W#####,
              ¶ ranges, T. page/lines, decision references
resolve       deterministic lookup against held records → citations table
              (resolved | unresolved | ambiguous, with confidence + method)
index         full-text + (later) embeddings; protected witnesses in an index
              with no name field
verify        human review queue for parse quality and ambiguous citations
```

Each stage updates `documents.ingestion_state` and writes to `audit_log`.

Since Phase 6 the schema the pipeline writes into exists (`docs/DATA_MODEL.md`):
`source_records` for discovery provenance (source system, external id, discovery
URL, canonical URL, raw metadata) kept separate from the normalized
`documents` / `document_versions` and from the stored object; `ingestion_jobs`
for cursor / checkpoint / counts; `record_identifiers` for the identifier index
the resolver reads; `citations` for the persisted resolution. No code that
fetches, parses or resolves exists yet.

## Citation resolution at ingest (ADR-005)

Resolution is part of ingestion, not of request handling. Re-ingesting a document
re-runs resolution for citations that target it, so earlier `UNRESOLVED` rows can
resolve without editing the citing text. Nothing fabricates a target.

## Date types

A document's own date and its filing date are separate fields from the first byte.
Transcript dates are testimony dates. Decision dates are decision dates. The
pipeline never infers one from another.

## Language

Documents are stored in the language filed. Official translations filed by the
court are stored as separate documents linked by `translationOf`. The pipeline
never machine-translates a court document.

## Failure handling

Failures are recorded (`ingestion_state = failed`, reason in `audit_log.detail`)
and surfaced in the ingestion panel on the homepage. Nothing is silently skipped.

## Status tracking

`MEMORY.md → Ingestion State` and `docs/PROJECT_STATE.md` carry the live counts:
discovered / downloaded / parsed / indexed / transcripts parsed / failed.
