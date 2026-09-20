# Phase 7 — KSC Public Record Discovery + Controlled 10–20 Document Ingestion

**Status:** Complete.

**Completed:** 2026-09-20.

**Completion commit:** `96e402a`.

**Completion tag:** `phase-7-complete`.

**Historical prerequisite:** Execute only after Phase 6 and Phase 5B are
complete; both prerequisites were satisfied.

## Goal

Connect the platform to **official public KSC sources** for the first time, discover the real public-record structure for `KSC-BC-2020-06`, and ingest only a carefully selected **10–20 representative public records**.

This is a controlled quality-gate phase, not a bulk-download phase.

## Official source scope

Prioritize official KSC public sources, especially:

1. official case page for `KSC-BC-2020-06`;
2. official Public Court Records repository;
3. official public transcript/hearing pages linked by those sources.

Do not treat search-engine cache or third-party copies as authoritative when the official source is available.

## Public-only requirement

Never:

- bypass authentication;
- access non-public/private APIs without authorization;
- guess confidential URLs;
- defeat robots/access controls;
- reconstruct redactions;
- deanonymize protected witnesses;
- ingest confidential/ex parte/sealed content.

If a public-redacted artifact exists, ingest only the public artifact and record its visibility/version accurately.

## Discovery research

Before coding a crawler, inspect normal public behavior.

Determine:

- how case pages list hearings/transcripts;
- how PCR searches/filtering work;
- how detail pages identify metadata;
- how PDFs/public versions are linked;
- whether the public UI uses a machine-readable endpoint;
- pagination behavior;
- language variants;
- stable external identifiers;
- document/version relationships;
- rate-limit/robots expectations;
- whether source URLs are canonical/stable.

Use only endpoints actually exposed to the public interface. Do not assume a private API exists.

Document discovery findings before scaling ingestion.

## Controlled corpus selection

Select 10–20 representative records covering several types, for example:

- a major public decision/judgment section if publicly available;
- trial transcript(s);
- Defence filing(s);
- SPO filing(s);
- order/decision(s);
- public-redacted version(s);
- corrected/versioned document if available;
- exhibit/public supporting material if straightforward and public.

The exact list should be documented with reasons for selection.

## Ingestion pipeline

Implement:

```text
Discovery
  ↓
Source record
  ↓
Metadata normalization
  ↓
Public visibility check
  ↓
Download
  ↓
SHA-256
  ↓
Object storage
  ↓
Document + DocumentVersion
  ↓
Ingestion audit/job state
```

Parsing depth can remain limited until Phase 8, but basic extraction may be used for validation if clearly separated.

## Idempotency

Re-running ingestion must not duplicate the same public artifact.

Use stable external identifiers + SHA-256 + scoped uniqueness.

## Version preservation

If both original and public-redacted/corrected variants are discovered:

- keep both;
- link them;
- do not overwrite;
- preserve individual source URLs/hashes/visibility.

## Provenance

Persist:

- discovery source/system;
- detail-page URL;
- canonical artifact URL;
- external record ID;
- official document/version ID;
- language;
- dates;
- filing party/type where available;
- visibility;
- original metadata snapshot where useful;
- downloaded-at timestamp;
- SHA-256.

## Failure handling

Ingestion job should track:

- discovered;
- downloaded;
- skipped duplicates;
- failed downloads;
- invalid metadata;
- unsupported artifact;
- ambiguous mapping.

Do not silently discard failures.

## Quality gate

Manually inspect the first corpus.

Verify for each record:

- correct case;
- correct title;
- correct official ID;
- correct version;
- correct filing date/party/type where available;
- public visibility;
- correct source URL;
- PDF/artifact opens;
- hash stored;
- re-run is idempotent.

## Transcript discovery

Use the official case/hearing pages to identify public transcripts.

Do not assume all hearings have transcripts or that all hearing portions are public.

Record hearing date/session and transcript artifact relationship.

Detailed page/line parsing happens in Phase 8.

## Videos

Do not bulk-download public videos in this phase.

It is sufficient to preserve public video metadata/links if useful for future work.

The core platform remains document/transcript-first.

## UI integration

Create an internal/admin data-status view if useful, showing:

- real records ingested;
- ingestion jobs;
- versions;
- failures;
- provenance.

Do not replace all demo UI with real data yet unless clearly isolated.

## Tests

Add fixtures/tests for:

- discovery parser;
- metadata mapping;
- public-only filtering;
- version mapping;
- idempotent ingestion;
- hash duplicate behavior;
- failed downloads;
- source-origin persistence;
- language/metadata variants;
- resume/checkpoint behavior.

Avoid tests that depend heavily on live network responses; capture representative lawful fixtures where permitted.

## Acceptance criteria

Phase 7 is complete only when:

- official public source behavior is documented;
- first 10–20 real public records are ingested;
- no private/confidential material is accessed;
- hashes and provenance are stored;
- versions are preserved;
- source-origin is preserved;
- ingestion is idempotent;
- failures are visible;
- corpus is manually spot-checked;
- tests pass;
- ingestion remains intentionally small.

## Do not do yet

- bulk/full corpus ingestion;
- deep citation resolution;
- production AI;
- broad graph extraction;
- appeal analysis;
- social/media crawling.

## Stop condition

Stop after the 10–20-record quality gate. Phase 8 must explicitly authorize deeper parsing.

## Completion report

```text
PHASE 7 STATUS
OFFICIAL SOURCES DISCOVERED
CONTROLLED CORPUS
DOCUMENT TYPES
VERSIONS
INGESTION PIPELINE
QUALITY CHECK
TESTS
FAILURES / LIMITATIONS
COMMITS
NEXT
MEMORY
```
