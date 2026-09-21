# Phase 13 corpus operations

## Boundaries

The inventory and acquisition queue contain official public metadata only.
`unknown`, confidential, sealed and ex-parte records fail closed. Automated
access uses the identified, robots-aware, rate-limited HTTP adapter. A
Cloudflare or equivalent challenge is terminal `blocked` state: never rotate
headers, cookies, proxies or browser automation to evade it.

Use `ksc-ingest inventory INVENTORY.json` for a metadata-only inventory exported
from an official surface. It records discovery separately from local artifact
state and enqueues only explicitly public, missing versions. Use
`ksc-ingest browser-plan --out capture-plan.json` to hand those official URLs to
an operator using a normal authorized browser session, then the existing
`import-capture`, `bundle` and `gate` commands to validate and ingest the bytes.

When identified HTTP is admitted, an operator may run one bounded batch with
`ksc-ingest acquire-http --owner WORKER --batch-size 10`. The pluggable adapter
uses the same official-host allowlist, robots check, per-host pacing and
Cloudflare fail-closed behavior. A future verified official API/export adapter
implements the same acquisition contract without changing queue or storage
logic.

Workers claim bounded batches with PostgreSQL row locks and expiring leases.
Transient failures use capped exponential backoff. Access-control blocks do not
retry. Crashed leases become claimable after expiry. Artifact bytes remain
immutable SHA-addressed objects; source metadata changes create immutable
snapshots, and new official version references create new version rows.

Serious mapping, case, hash and PDF failures enter `artifact_quarantine`.
While a quarantine row is `open`, the version is excluded from parsing and
citation resolution, so it never gains the parsed output that search,
projection and AI retrieval read. A version quarantined after it was already
parsed keeps its derived rows until a reviewer releases or rejects the row; the
Phase 13 gate reports it as `quarantined_parsed_versions` and fails integrity.
`ksc-ingest parse --force` deterministically rebuilds parse output from held
bytes; `ksc-ingest reresolve` rebuilds the identifier index and citation
results. Both write processing-run history.

## Backup and restore

Set the normal `DATABASE_URL` and MinIO environment variables. Create an empty
target and run:

```sh
.venv/bin/python scripts/backup_restore.py backup /explicit/backup/path
```

The manifest contains SHA-256 checksums for the PostgreSQL custom dump and every
object, plus configuration key names but no secret values. Restore only into a
verified target database and bucket:

```sh
.venv/bin/python scripts/backup_restore.py restore /explicit/backup/path --confirm
```

Restore is destructive to the target database (`pg_restore --clean`) and
therefore refuses to run without `--confirm`. A release gate must restore into
an isolated database and bucket, compare migration head, row counts, object
counts and hashes, then remove those isolated test targets.

## Monitoring and alerts

The internal `/api/v1/ingestion/status` endpoint and `ksc-ingest status` expose
verified bytes, duplicate/failure counts, parser-review count, acquisition queue
depth by state, open quarantine count, source snapshot count, processing runs,
citations by resolution state and recent job checkpoints. Alert on stuck leases,
growing blocked/failed/quarantine queues, parser review, storage growth, job
failure, unresolved/ambiguous citation regressions and API readiness/latency.

Do not advance a corpus batch while error metrics regress. The Phase 13 scale
gate starts at 50 real public records; synthetic fixtures can verify mechanics
but can never satisfy that gate.
