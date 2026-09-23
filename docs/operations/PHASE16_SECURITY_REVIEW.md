# Phase 16 security review checkpoint

Implementation controls: production config fails closed; TLS and HSTS terminate
at Caddy; CORS is exact-origin; bodies are capped; security headers and opaque
errors are applied; public reads are separate from role-protected writes;
privileged requests are Redis-throttled; production demo mode is blocked;
external AI endpoints are HTTPS/allowlisted and budgeted; official/external
capture remains bounded by manifests rather than user-supplied fetch URLs;
containers are read-only/capability-free; DB migration and runtime identities
are separate; storage is private and integrity-addressed; lockfiles, dependency
updates and CI scans are present.

Review scope for the final gate: API input/error behavior, every mutation,
ingestion and external capture, presigned/object access, database grants, AI
payload policy, export formulas/content types, and file/path normalization.
Run the automated dependency/container checks and a focused manual abuse pass.
Critical/high findings block beta. Record accepted lower-risk findings with
owner, rationale and review date. This checkpoint is not the final security
sign-off; live infrastructure policy and penetration checks remain pending.

## Manual application review — 2026-09-23

**Status: PASS for the locally reviewable application boundary.** Critical: 0;
high: 0; medium: 0; accepted low: 2. This does not claim a live infrastructure
or provider penetration test.

- Privileged surfaces: ingestion status and review mutations require verifier;
  AI runs/notes and research-note mutations require researcher; the role ladder,
  constant-time bearer comparison, Redis throttling and fail-closed behavior
  were reviewed. Public reads remain separate from mutations.
- Input/transport: a disallowed-origin preflight returned 400, TRACE returned
  405, an encoded traversal attempt returned an opaque 404, and an oversized
  request returned 413. CORS is exact-origin in production; request/log handling
  records neither query strings nor bodies.
- Ingestion/files/storage: URLs are HTTPS-only on the explicit KSC host list;
  redirects are manual and refused off-list; robots/access controls fail closed;
  capture paths are resolved inside the bundle root. There is no public upload
  or object-write API, no presigned-object endpoint, and objects are addressed
  by verified hashes in a private bucket.
- Secrets/AI/exports: production configuration rejects development credentials,
  wildcard/non-HTTPS origins and unallowlisted AI endpoints. Provider redirects
  are refused, secrets remain server-side, output/concurrency/daily budgets are
  bounded, and source text is marked untrusted. CSV fields are quoted and quote-
  escaped; exports contain controlled public-record directory fields only.
- Headers/errors: Caddy strips `Server`, applies the production security headers,
  caps request bodies and redirects HTTP to HTTPS. API errors observed in the
  abuse pass were opaque and did not expose stack, SQL, path or secret data.

Accepted low-risk findings:

1. `S16-L01` — a direct internal API 413 response is returned before the API
   middleware adds its headers. The API is backend-network-only and Caddy adds
   the externally visible headers and body limit. Owner: operations. Recheck in
   the first authorized staging smoke test; review by 2026-10-07.
2. `S16-L02` — CSV quoting does not additionally prefix spreadsheet formula
   characters. Current exports contain controlled Court-directory data and no
   external/user-authored rows. Owner: web. Revisit before export scope accepts
   external or user-authored values; review by 2026-10-31.

Live managed-database/object-store grants and external edge policy remain part
of the authorized-environment verification, not this local application sign-off.
