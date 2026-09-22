# Security

## Secret management

- No secret is committed. `.env.example` holds placeholders only; `.env` is
  git-ignored. Docker Compose reads `.env`.
- Development defaults in code (`ksc_api/config.py`) are dev-only and overridden by
  the environment; production deployments must set every credential explicitly.
- AI provider keys are **not required** in Phase 4 and nothing reads them. When an
  AI layer exists, keys live only in the analysis worker's environment, never in the
  web app, never in the browser bundle (`NEXT_PUBLIC_*` must never carry a key).
- `GIT_SHA` is the only build-time value baked into images.

## Public-only ingestion rule

The application uses only lawfully public court records. Ingestion — when it
exists — must never:

- bypass authentication or access restrictions;
- guess confidential URLs or enumerate identifiers to discover non-public material;
- fetch from anything but the court's official public site (or an officially
  designated public mirror), recorded per document in `documents.source_url`;
- ignore robots rules or rate limits.

A document whose identifier is known but whose text is not public is stored with
`public_state = not_held` and shown to users as "not in the public set", never
fetched by other means.

## Protected witness rule

- A witness publicly identified only by a code (e.g. `W01234`) is displayed only as
  that code, labelled _Protected Witness_, with a dashed neutral avatar.
- The system never stores, infers, reconstructs or displays a name, image,
  location, occupation, age or other attribute for a protected witness, and never
  attempts to link a code to a name from any source.
- Protection state is authoritative from the backend. If it cannot be resolved the
  surface **fails closed** to the protected treatment.
- The public variant of a witness record is structurally absent for protected codes
  (a separate sub-record, not nullable fields), and search indexes for protected
  witnesses contain no name field.
- Redactions are rendered as visible blocks with their extent. Redacted content is
  never reconstructed, inferred or machine-translated in place.

## External public sources

Phase 14 accepts reviewed manifests of manually submitted public HTTPS URLs.
The importer rejects credentials in URLs, local/private hostnames and anything
not explicitly marked public. Login-gated, CAPTCHA/Cloudflare-protected,
paywalled, private-profile, deleted and platform-restricted material is not
collected or reconstructed. The controlled sample stores short exact excerpts,
hashes and provenance rather than mirroring full articles.

External material is isolated from court evidence. A status beyond
`EXTERNAL_ONLY` or `UNKNOWN` requires a human-verified court link with an exact
persisted citation; the read service additionally requires that citation to be
resolved. External-only items create no court graph edge and are not eligible
for the Phase 11 court-record retrieval whitelist.

## Future private-data separation

Phase 4 holds public data only. If private material (e.g. a client's own working
notes, or non-public disclosure a lawful user is entitled to hold) is ever added:

- it lives in a separate schema and bucket with its own access control;
- it never enters the shared search index or the AI retrieval set for other users;
- research notes store citation sets, not copied text.

## Input and file safety

- Identifiers from URLs (`W01234`, `F00482`, slugs) are treated as opaque strings,
  validated against the record before use, and never interpolated into SQL or
  shell. SQLAlchemy parameters only.
- Uploaded or fetched files (later phases) are written to MinIO with a content
  hash, scanned for type, and parsed in a worker with no network access.
- CORS is restricted to `CORS_ORIGINS`.
- API requests declaring a body larger than 10 MiB are refused before routing;
  ingestion artifacts enter through the offline worker and its PDF/hash checks.
- API responses set nosniff, frame-denial, restrictive referrer, permissions and
  CSP headers. Containers run as an unprivileged user.

## Dependency monitoring

Dependabot scans Python, pnpm and GitHub Actions dependencies weekly. CI remains
the merge gate for lint, type checks, tests and the production build; dependency
updates must pass the same gate.

## Logging restrictions

- Logs carry structured metadata (identifiers, counts, timings, error class), not
  document text, not transcript content, not anything that could identify a
  protected witness beyond the public code.
- The `audit_log.detail` JSON follows the same rule.
- Readiness failures log the exception class, not connection strings.

## Access control direction

- Phase 4 has no authentication; the deployment is local.
- Planned: authenticated users with roles (reader · reviewer · admin). Reviewer
  actions (verification, comparison labels, potential-issue review) write to the
  audit log with actor identity. Public mode remains readable without an account.
- Nothing in the data model — now or later — carries a score, rank or weight of any
  person; access control cannot make such a field appear because it does not exist.
