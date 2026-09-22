# Phase 17 — Historical Corpus Expansion, Coverage & Continuous Sync

**Status:** Pending. Execute after Phase 16, or as an explicitly approved post-beta expansion milestone.

## Goal

Expand from the validated representative public corpus to broad historical coverage of the lawfully public KSC record while preserving the integrity guarantees proved in Phases 7–16.

This is not:

```text
download everything as fast as possible
```

It is:

```text
DISCOVER
↓
COMPARE
↓
ACQUIRE LAWFULLY
↓
VERIFY
↓
PARSE
↓
INDEX
↓
RE-RESOLVE
↓
QUALITY SAMPLE
↓
EXPAND
```

## Core principle

Corpus size is not the quality metric.

Never claim `complete corpus` unless official discovery coverage for the declared scope is reproducible and demonstrably complete.

## Declare scope first

Define the exact scope before collection, for example:

- all public records for `KSC-BC-2020-06`;
- all public transcripts for that case;
- all public filings/annexes;
- EN + SQ;
- selected additional KSC cases only after a separate explicit decision.

Do not silently broaden scope.

## Source hierarchy

Prioritize official KSC public sources.

Preserve separately:

- where an item was discovered;
- what it represents;
- where the artifact was obtained;
- where it is stored.

Do not replace official provenance with third-party copies when official material is available.

## Access rules

Never:

- bypass Cloudflare/CAPTCHA;
- reuse stolen/private session material;
- defeat login/access controls;
- access restricted/confidential/ex parte material;
- reconstruct redactions;
- infer protected identities.

Use only lawful public access, approved browser-assisted collection, or official bulk/API/export if one becomes available.

## Durable discovery inventory

For every discovered record preserve, where available:

- case;
- official reference;
- title;
- date;
- filing/document type;
- party;
- chamber/court level;
- language;
- public state;
- official detail URL;
- official artifact URL;
- version identity;
- discovery source;
- first seen;
- last seen;
- artifact state;
- parse/index state.

## Coverage accounting

Report separately:

- discovered;
- new;
- known unchanged;
- new versions;
- not fetched;
- fetched;
- verified;
- parsed;
- indexed;
- failed;
- quarantined;
- review required.

Never equate `not discovered` with `does not exist`.

## Historical backfill

Use explicit strata, for example:

```text
recent period
↓
previous year
↓
earlier trial period
↓
pre-trial period
↓
historical completion pass
```

Do not collect only recent/easy material and imply historical completeness.

## Progressive batch gates

Scale progressively, for example:

- 100;
- 250;
- 500;
- 1,000;
- 2,500;
- larger.

Adjust to actual source/runtime characteristics.

Each step requires a quality gate.

## Batch quality gate

Measure:

- inventory accuracy;
- duplicates;
- ambiguous mapping;
- public/private classification;
- SHA integrity;
- object storage;
- parser success;
- parser review;
- language/version correctness;
- citation extraction;
- citation resolution;
- search;
- lineage safety;
- quarantine;
- runtime;
- storage growth.

Stop expansion if integrity degrades.

## Version handling

Preserve every distinct public version separately, including where applicable:

- original public;
- RED;
- RED2;
- COR;
- CORRED;
- translation;
- reclassified;
- public annex;
- transcript revision.

Never overwrite an earlier public version.

## Language coverage

Declare supported languages explicitly.

For EN + SQ:

- report missing counterparts honestly;
- do not infer translations;
- do not treat one language as legally canonical beyond source metadata.

## Transcript expansion

Preserve:

- hearing date;
- session identity;
- printed page;
- line coordinates;
- language;
- open/public boundaries;
- artifact/version provenance.

Do not expose closed-session text.

## OCR

Operationalize OCR if expanded public documents are image-only.

Requirements:

- public pages only;
- preserve original artifact and coordinates;
- mark OCR provenance;
- confidence/review state;
- manual review for low-confidence/high-impact material;
- OCR text is never more authoritative than the original artifact.

## Parser versioning / reprocessing

Track parser version/provenance.

When parser logic changes:

```text
identify affected versions
↓
reprocess
↓
stable-ID reconciliation
↓
lineage audit
```

Never destructively rebuild downstream identity.

## Citation re-resolution

After each batch:

- retry eligible unresolved citations;
- preserve stable citation IDs;
- resolve only deterministic matches;
- keep ambiguity fail-closed;
- report before/after counts.

Previously resolved citations must not silently retarget.

## Search growth

Measure:

- exact identifier;
- phrase;
- keyword;
- filtered search;
- transcript search;
- external-vs-court separation.

Optimize only demonstrated bottlenecks.

## Network / timeline growth

Rebuild deterministic projections where appropriate.

Do not automatically create canonical findings, evidence classifications, appeal issues or credibility judgments.

Human-verification rules remain binding.

## Findings / Appeal / AI lineage

Corpus expansion must not silently mutate:

- canonical findings;
- evidence roles;
- human-verified appeal issues;
- red-team conclusions;
- research notes.

New material may create a `candidate for review`, not an authoritative conclusion.

## AI/RAG eligibility

New content becomes retrievable only after:

- public state validated;
- artifact verified;
- parsing successful;
- provenance present;
- quarantine clear;
- indexing complete.

Never retrieve failed/quarantined/unverified artifacts.

## External-media boundary

Phase 14 external media remains a separate source layer.

Historical court-corpus expansion must not silently ingest external media as court records.

## Continuous sync

After backfill, implement recurring incremental sync that detects:

- newly published record;
- newly public/reclassified record;
- corrected version;
- new language version;
- new transcript;
- metadata change.

Unchanged records must be skipped.

## Source disappearance

Do not silently delete locally held provenance if an official source disappears.

Record:

- previously observed state;
- current availability;
- capture provenance.

Do not speculate about why it disappeared.

## Reconciliation

Provide periodic reconciliation across:

```text
official inventory
vs
database
vs
object storage
vs
parse/index state
```

Detect:

- missing objects;
- orphan objects;
- orphan versions;
- stale metadata;
- unprocessed versions;
- impossible states.

## Storage / capacity

Track:

- object count;
- bytes;
- growth rate;
- dedup savings;
- backup size;
- restore time.

Plan capacity from measured growth.

## Performance scaling

Re-run representative tests at larger corpus sizes:

- search;
- reader;
- network;
- timeline;
- pagination;
- ingestion throughput;
- parse throughput;
- citation re-resolution.

## Reliability

At scale test:

- worker crash;
- restart;
- lease expiry;
- duplicate acquisition;
- DB reconnect;
- object-store transient error;
- parser failure;
- retry exhaustion;
- quarantine;
- interrupted batch.

## Operations / observability

Maintain metrics for:

- inventory;
- queue;
- fetch;
- verification;
- parse;
- index;
- quarantine;
- citations;
- processing rate;
- storage;
- failures.

Use actionable alerts only.

## Reproducibility manifests

Track metadata-only manifests/checkpoints in Git where appropriate.

Never commit bulk PDFs/media artifacts.

A checkpoint should identify:

- declared scope;
- capture/inventory date;
- record/version counts;
- languages;
- artifact hashes or stable manifest hash;
- quality-gate result.

## Sampling audit

At major milestones manually review a risk-based sample across:

- years;
- parties;
- document types;
- languages;
- public/redacted/reclassified;
- transcripts;
- annexes;
- corrected versions.

Do not sample only easy records.

## Coverage dashboard

Create an internal/admin report such as:

```text
Case: KSC-BC-2020-06

Officially discovered: X
Locally represented: Y
Verified artifacts: Z
Parsed: A
Indexed: B
Review required: C
Quarantined: D
Last discovery sync: ...
Historical strata covered: ...
```

## Completeness claim

A `complete` label requires:

1. documented source scope;
2. exhaustive inventory method;
3. repeatable discovery pass;
4. no unexplained gaps;
5. reconciliation pass;
6. quality sampling;
7. exact date of the claim.

Otherwise use wording like:

`Known public corpus indexed as of <date>`.

## Continuous-update cadence

Define a reasonable sync cadence after backfill.

Do not overload official services.

Fail closed when access-control behavior changes.

## Testing

Run:

- inventory;
- incremental sync;
- new-version detection;
- duplicate handling;
- language/version pairing;
- OCR if enabled;
- parser/reprocessing;
- stable-ID citation resolution;
- lineage safety;
- reconciliation;
- storage consistency;
- crash/retry/resume;
- large-batch performance;
- search/network/timeline regressions;
- AI eligibility;
- external/court separation;
- backup/restore;
- full regression suite.

## Historical expansion quality gate

At every declared scale milestone record actual:

```text
discovered
accepted
fetched
verified
parsed
indexed
review-required
failed
quarantined
duplicates
bytes
citations
resolved
ambiguous
unresolved
invalid
```

No illustrative numbers in completion reports.

## Acceptance criteria

Phase 17 is complete when the declared scope has reached its target and:

- inventory is reproducible;
- lawful acquisition is stable;
- accepted artifacts are integrity-verified;
- version/language identity is preserved;
- parser/OCR review works at scale;
- citation re-resolution preserves lineage;
- search/network/timeline remain stable;
- Phase 10–14 authoritative state is not silently mutated;
- continuous sync is implemented;
- reconciliation passes;
- coverage is reported honestly;
- backup/restore is proven at expanded scale;
- performance remains within production limits.

If full official coverage cannot be established, close only against an explicitly narrower declared scope and do not label it a complete corpus.

## Stop condition

Never trade source integrity, public-access rules or provenance for corpus size.

## Completion report

```text
PHASE 17 STATUS
DECLARED SCOPE
OFFICIAL INVENTORY
HISTORICAL COVERAGE
ACQUISITION
LANGUAGES / VERSIONS
TRANSCRIPTS
OCR
PARSING / REPROCESSING
CITATION RE-RESOLUTION
SEARCH
NETWORK / TIMELINE
AI / APPEAL / FINDINGS LINEAGE
CONTINUOUS SYNC
RECONCILIATION
STORAGE / BACKUP
PERFORMANCE
QUALITY GATES
ACTUAL CORPUS COUNTS
KNOWN GAPS
COMMITS
TAG
NEXT
MEMORY
```
