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

`GET /metrics` on the API returns Prometheus text exposition (no client
library, no extra service): per-route request counters and a latency
histogram (`ksc_http_requests_total`, `ksc_http_request_duration_seconds`),
build info, and database-backed operational gauges read on each scrape —
`ksc_source_records`, `ksc_document_versions`, `ksc_versions_fetched`,
`ksc_versions_parse_review_required`, `ksc_verified_artifact_bytes`,
`ksc_citations{state}`, `ksc_acquisition_queue{state}`,
`ksc_acquisition_stuck_leases`, `ksc_quarantine{state}`,
`ksc_processing_runs{state}`, `ksc_ingestion_items_failed`,
`ksc_ai_runs`, `ksc_ai_runs_withheld`, `ksc_ai_runs_failed`,
`ksc_ai_cost_usd_total`. `ksc_metrics_db_scrape_ok` is 0 when PostgreSQL could
not be read; the scrape itself never fails. Labels carry route templates and
states only — never identifiers, query strings or text.

The same numbers are readable as JSON from the internal
`/api/v1/ingestion/status` endpoint and from `ksc-ingest status`.

Logs are structured JSON (`LOG_FORMAT=json`, one object per line) with an
access line per request carrying `request_id`, `method`, `route`, `status`
and `duration_ms`; the response echoes `X-Request-ID`. Log lines never carry
document text, witness identifiers beyond public codes, or secrets
(`docs/SECURITY.md`).

Alert rules live in `ops/alerts/ksc-api.rules.yml`: API down, 5xx rate above
2%, p95 latency above 500 ms, metrics scrape failing, stuck leases, growing
blocked/failed acquisitions, open quarantine or parser-review rows older than
a day, failed processing runs, new failed ingestion items, growing ambiguous
citations, unexpected storage growth, and failing AI runs.

Do not advance a corpus batch while error metrics regress. The Phase 13 scale
gate starts at 50 real public records; synthetic fixtures can verify mechanics
but can never satisfy that gate.
