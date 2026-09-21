# Phase 13 — Gradual Full Public Corpus Ingestion & Production Hardening

**Status:** IN PROGRESS — architecture/operations implemented; real-corpus scale gate blocked at 22/50 lawfully available records (2026-09-21).

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

## Execution checkpoint — 2026-09-21

Implemented migration `0009`, separate metadata inventory and artifact state,
immutable source snapshots, a bounded lease/retry queue, access-control-terminal
behavior, browser-capture plans, quarantine, deterministic force reprocessing,
citation re-resolution, processing history, operational metrics, secure API
headers/request limits, dependency monitoring, and checksum-verified database
plus object-store backup/restore tooling.

The real gate verified all 22 held public artifacts (24,429,094 bytes), public-only
and quarantine isolation, and measured document search, exact lookup and network
queries below the 500 ms local threshold. An isolated restore recovered migration
`0009`, the database corpus and all 22 objects with matching total bytes.

The official repository's `robots.txt` still returns a Cloudflare 403 challenge
(`cf-mitigated: challenge`). No bypass was attempted. The largest lawful real
sample remains 22 records, below the first 50-record gradual-scale gate. Therefore
this phase is not complete, no `phase-13-complete` tag exists, and Phase 14 must
not start. Machine evidence: `docs/ingestion/phase13-quality-gate.json`.

## Verification checkpoint — 2026-09-21 (resumed closeout audit)

Repository reality was re-inspected independently of the earlier run: branch
`feat/phase-13-full-public-corpus-ingestion-hardening`, branch-start commit
`2adb1f1` preserved, migration head and live database both at `0009`,
`alembic check` reports no model drift, and the `base → 0009` round-trip is
integration-tested. `make lint`, `make typecheck`, `make test` (260 backend
+ 199 frontend) and `make build` pass.

Runtime re-verification on the real corpus: `ksc-ingest parse --force` (22/22
versions) followed by `ksc-ingest reresolve` left every downstream row
byte-identical — citations (IDs, resolution state, targets), relationships,
events, findings, evidence links, arguments, AI runs/sources/output citations,
appeal issue sources, statement comparison, red-team findings, research-note
citations, page/paragraph/chunk/segment IDs and text, and version hashes —
with only `processing_runs` growing (3 → 5). The Phase 13 gate re-run produced
the same report as `docs/ingestion/phase13-quality-gate.json` apart from
sub-3 ms latency figures. A fresh checksum backup restored into an isolated
database and bucket at `0009` with an identical lineage fingerprint and 22/22
objects (24,429,094 bytes) verified by SHA-256; the isolated targets were
removed. A single identified, non-recorded probe of the official host again
returned HTTP 403 `cf-mitigated: challenge` on `robots.txt`; the client stopped.

Two hardening gaps were found and closed: open-quarantine versions are now
excluded from parse and citation-resolution selection (integration-tested), and
Dependabot now also scans `workers/ingestion` (httpx, pypdf, beautifulsoup4).
Documentation was corrected to state that quarantine exclusion is enforced at
parse/resolution and detected by the gate, not enforced inside search/AI query
paths.

Acceptance criteria against repository/runtime reality:

- corpus ingestion scales gradually and safely — **NOT MET**: mechanism
  implemented (bounded leases, retry, checkpoints), but no batch beyond the 22
  lawful records has been possible; 22/50 for the first scale step.
- public-only rule holds — MET (0 fetched non-public; inventory/queue accept
  explicit public versions only; challenge is terminal).
- version history is preserved — MET (immutable SHA versions, 22 source
  snapshots, duplicate detection, no silent mutation on reparse).
- data-quality metrics exist — MET for discovery, download, duplicate, parse
  review, unresolved/ambiguous citations, queue depth, quarantine, bytes,
  processing runs; OCR fallback rate is not applicable (no OCR exists).
- quarantine/reprocessing exists — MET and verified live.
- search/network remain performant — MET at 22 records only (< 3 ms locally);
  untested at 50+.
- backups restore successfully — MET (isolated restore verified twice).
- observability is production-ready — **PARTIAL**: health/ready/version,
  status metrics, audit log and processing-run history exist; logs are plain
  text, and there is no metrics endpoint or alerting integration.
- source/audit lineage remains intact at scale — MET at 22 records; not
  demonstrated at scale.
- AI never bypasses verification/citation layers — MET (Phase 11/12 gates and
  tests unchanged; quarantine cannot feed parsed output).

Decision: Phase 13 remains **IN PROGRESS — BLOCKED ON LAWFUL REAL SCALE**. No
`phase-13-complete` tag exists. Next required action: an authorized official
inventory/capture that lawfully raises the corpus to at least 50 records, then
a bounded batch, the real gate and the full quality gates. Phase 14 does not
begin.
