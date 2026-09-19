# Phase 13 — Gradual Full Public Corpus Ingestion & Production Hardening

**Status:** Pending.

## Goal

Scale from the validated controlled corpus toward the complete lawfully public corpus relevant to `KSC-BC-2020-06`, while preserving data quality, provenance, versioning, monitoring, security, and recoverability.

This is not “download everything as fast as possible.” It is a controlled scale-out phase.

## Preconditions

Do not begin until:

- Phase 7 controlled ingestion passed;
- Phase 8 parsing/citation quality passed;
- Phase 9 graph/timeline are provenance-safe;
- Phase 10 findings/evidence matrix is reliable;
- Phase 11/12 AI/research layers cannot bypass citation rules.

## Gradual scale plan

Increase in batches, for example:

```text
20 validated records
   ↓
50–100
   ↓
several hundred
   ↓
larger historical corpus
   ↓
full relevant public corpus
```

Advance only when error metrics remain acceptable.

## Corpus definition

“Full public corpus” means all relevant public material discoverable through authorized official KSC public surfaces for the scoped case, subject to technical/legal availability.

It does **not** mean confidential, sealed, ex parte, inaccessible, removed, or redacted-away content.

## Ingestion scheduling

Support:

- initial historical backfill;
- resumable jobs;
- periodic discovery of new/changed public records;
- version detection;
- corrected/redacted/new versions;
- job checkpoints;
- retry/backoff;
- rate limiting.

Respect public-site stability and terms.

## Change detection

When a source changes:

- preserve prior downloaded version/hash;
- ingest the new public version;
- never silently mutate old evidence;
- record discovery timestamps and source history.

## Data-quality monitoring

Track metrics such as:

- discovery count;
- download success/failure;
- duplicate rate;
- parse success/failure;
- OCR fallback rate;
- unresolved citation rate;
- ambiguous citation rate;
- transcript line-parse success;
- missing metadata;
- version-linking failures;
- graph relationships without verified provenance (should be zero for production-verified edges).

## Quarantine

Records with serious parse/provenance problems should enter quarantine/review state rather than contaminating trusted search/AI.

Examples:

- corrupted PDF;
- impossible page mapping;
- ambiguous official ID;
- wrong case;
- unknown visibility;
- citation resolver conflict.

## Reprocessing

Parser/resolver improvements should support deterministic reprocessing while preserving:

- original artifact;
- hash;
- ingestion history;
- previous parser run/audit where needed.

## Search/index scaling

Measure PostgreSQL FTS/pgvector performance.

Only introduce a separate search engine if real metrics justify it.

Do not add infrastructure because it seems fashionable.

## Graph scaling

Measure real network size and interaction performance.

Move to Sigma.js/Graphology/WebGL or optimize indexes/caches if actual scale requires it.

## Caching

Cache derived views carefully:

- search responses;
- network neighborhoods;
- evidence paths;
- citation resolution lookups;
- document metadata.

Do not cache in ways that hide updated verification/version status.

## Security / operational hardening

Implement/verify:

- secrets management;
- non-root containers where practical;
- object-store access controls;
- backup/restore;
- database migrations in deployment;
- audit logging;
- dependency scanning;
- input/file validation;
- request limits;
- secure headers;
- observability;
- structured logs;
- alerting.

## Backups

Test restore, not just backup creation.

Protect:

- PostgreSQL;
- object storage;
- configuration/secret references;
- migration state.

## Production observability

Monitor:

- API latency/error rate;
- ingestion jobs;
- parser failures;
- citation-resolution failures;
- queue depth;
- storage usage;
- DB performance;
- AI errors/costs;
- failed source opens;
- background job health.

## Human verification workflow

At corpus scale, prioritize review queues for:

- ambiguous citations;
- important findings;
- high-impact relationship edges;
- AI-flagged contradictions;
- unresolved transcript mappings;
- source version conflicts.

## Data exports / reproducibility

Where useful, support research exports containing:

- query/filters;
- source IDs;
- citations;
- verification state;
- generated-at timestamp.

Avoid exporting hidden/internal/private data.

## Performance / load testing

Test realistic corpus size for:

- document search;
- exact citation lookup;
- finding detail;
- network neighborhood;
- evidence path;
- transcript loading;
- AI retrieval.

## Acceptance criteria

- corpus ingestion scales gradually and safely;
- public-only rule holds;
- version history is preserved;
- data-quality metrics exist;
- quarantine/reprocessing exists;
- search/network remain performant;
- backups restore successfully;
- observability is production-ready;
- source/audit lineage remains intact at scale;
- AI never bypasses verification/citation layers.

## Stop condition

Core KSC public-record platform is considered mature after this phase. Optional expansions such as external media intelligence belong in Phase 14.

## Completion report

```text
PHASE 13 STATUS
CORPUS COVERAGE
INGESTION SCALE
DATA QUALITY
VERSIONS / CHANGE DETECTION
SEARCH PERFORMANCE
GRAPH PERFORMANCE
OPERATIONS
BACKUP / RESTORE
OBSERVABILITY
SECURITY
KNOWN GAPS
COMMITS
NEXT
MEMORY
```
