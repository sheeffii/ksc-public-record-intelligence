# ADR-022 — Single-host container beta with managed state

Status: accepted for Phase 16 beta implementation.

The beta uses Caddy as the only public TLS endpoint, with separate web and API
containers and an internal Redis service. PostgreSQL and S3-compatible object
storage are managed stateful services reached over TLS. A one-shot migration
container uses a distinct DDL credential; the API uses a non-owner DML account.

This is the smallest recoverable architecture for the expected beta scale.
Kubernetes is intentionally deferred. Staging and production use separate DNS,
compose project names, databases, buckets, credentials and environment files.
Images are addressed by Git SHA and run read-only without Linux capabilities.

The tradeoff is a single application host. State survives host replacement,
and the documented restore/deploy process is the recovery path. Horizontal web
or API replicas may be added behind Caddy without changing state ownership.
