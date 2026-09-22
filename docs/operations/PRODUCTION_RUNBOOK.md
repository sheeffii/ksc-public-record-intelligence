# Production operations runbook

## Environments and access

Development, test, staging and production never share a database, bucket,
Redis namespace, API token, DNS name or compose project. Only staging and
production use `compose.production.yml`. Keep the real environment file at
`/etc/ksc-pri/<environment>.env` with mode `0600`; never copy it into Git.
Production must contain real data only. The demo fixture command is forbidden.

The public can use GET/HEAD research routes. Researcher tokens can create AI
runs and notes; verifier tokens additionally change review state and inspect
ingestion status; administrator tokens inherit both and are reserved for
operations. Rotate a role token by briefly configuring old,new, deploy, update
clients, then remove old. API tokens and provider secrets stay server-side.

## Deploy

1. Confirm CI, dependency/container scans, approved immutable Git SHA and a
   current verified backup. Review migrations and recovery guidance.
2. Set `IMAGE_TAG=<git-sha>` in the environment file and pull images.
3. Run `docker compose --env-file <file> -f compose.production.yml --profile operations run --rm migrate`.
4. Run `docker compose --env-file <file> -f compose.production.yml up -d --wait`.
5. Verify HTTPS redirect, certificate, `/health`, `/ready`, `/version`, home,
   search, reader, network and timeline. Confirm version SHA and alerts.

No server file or container is edited manually. Staging receives the same SHA
and smoke checks before the protected production environment is approved.

## Rollback and migration safety

Set `IMAGE_TAG` to the last known-good SHA and run `up -d --wait`, then repeat
smoke checks. Do not downgrade a schema blindly. For an incompatible migration,
stop writes, provision a clean database/bucket, restore the pre-deploy backup,
point the environment file to restored state, and deploy the prior SHA. Record
times, operator, backup manifest hash and resulting `/version` response.

## Backup, restore and disaster recovery

Target: RPO 24 hours, RTO 4 hours. Run `scripts/backup_restore.py backup` daily
to encrypted storage in a different failure domain; retain 7 daily, 5 weekly
and 12 monthly sets. Provider-side object versioning/lifecycle retains verified
artifacts; bucket policy denies public writes and grants the app only list/get/
put. Retain the Git SHA, environment-variable names (not values), DNS/TLS notes
and alert configuration with each backup. Write `BACKUP_METRICS_FILE` to the
Prometheus textfile directory.

Monthly, in a new isolated environment: restore into an empty DB and bucket
with `scripts/backup_restore.py restore <set> --confirm`; apply migrations;
run the held-object hash quality gate; start services; test readiness and the
representative routes. Record actual start/end time, object count, hashes,
failures and RPO/RTO result. A backup is not accepted until this drill passes.
Set `RESTORE_DATABASE_URL` to the isolated recovery owner; never grant DDL or
drop privileges to the normal application account.

## Routine operations

- Ingestion/capture import: use the existing operator bundle and CLI; never
  automate around source access controls. Run the worker image only through the
  protected `operations` profile, mount the reviewed bundle read-only, and
  verify the corpus gate afterward. There is no public ingestion endpoint.
- Quarantine: verifier inspects the original public source and stored hash;
  release/reject explicitly and retain audit history.
- Parser/re-resolution: back up first, run the bounded parser/resolver CLI,
  review changed counts and unresolved/ambiguous citations, then rerun gates.
- Health/metrics: `/health` is liveness, `/ready` checks DB/Redis/storage, and
  internal `/metrics` feeds the existing Phase 13 metrics and alert rules.
- Database: enable managed-service TLS, `pg_stat_statements`, connection/CPU
  graphs and slow-query logging at 500 ms; alert on saturation and investigate
  query plans without logging bind values or document text.
- Incident: preserve logs/request IDs, revoke affected tokens, disable external
  AI if relevant, isolate writes, verify artifact hashes, restore if integrity
  is uncertain, and publish only confirmed availability facts.

Logs contain route templates, status, latency and request IDs—not query strings,
document text, protected identifiers or research notes. No analytics, cookies
or third-party error tracker are enabled. Reassess payload filtering before
adding telemetry. Supported beta clients are current and previous Chrome,
Firefox, Safari and Edge, plus responsive mobile Safari/Chrome.
