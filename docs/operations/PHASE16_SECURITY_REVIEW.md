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
