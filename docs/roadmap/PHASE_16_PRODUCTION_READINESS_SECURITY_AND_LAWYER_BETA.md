# Phase 16 — Production Readiness, Security & Lawyer Beta

**Status:** Pending. Execute only after Phase 15 is complete.

## Goal

Turn the real-data application into a safe, observable, recoverable and usable beta deployment.

This phase is about proving:

```text
DEPLOYABLE
RECOVERABLE
SECURE
OBSERVABLE
MAINTAINABLE
USABLE BY REAL RESEARCHERS
```

Do not add major new legal-intelligence features unless required to close a production-readiness gap.

## Deployment architecture

Choose the simplest architecture that satisfies the current scale.

Avoid premature Kubernetes.

A reasonable initial shape may be:

```text
TLS / reverse proxy
        ↓
Web
API
Workers
        ↓
PostgreSQL
Redis
Object storage
```

Record the final decision in an ADR.

## Environments

Support clearly separated:

- development;
- test;
- staging;
- production.

No production credential may be committed to Git.

No demo fixture should enter production data accidentally.

## Configuration

Document every required environment variable.

Maintain `.env.example` without secrets.

Validate mandatory production configuration at startup and fail clearly when missing.

## Domain / TLS

Support:

- HTTPS;
- canonical domain;
- HTTP→HTTPS redirect;
- secure cookies where authentication exists;
- HSTS when appropriate.

## Authentication / authorization

Separate public read access from privileged mutation.

Protect actions such as:

- ingestion;
- verification;
- canonical relationship editing;
- quarantine review;
- research-note mutation;
- AI-provider/admin configuration.

Use least privilege.

If roles are needed, keep them minimal, e.g.:

- public reader;
- researcher;
- verifier;
- administrator.

## API security

Review and test:

- CORS;
- security headers;
- request-size limits;
- rate limiting where useful;
- input validation;
- path traversal;
- SSRF;
- unsafe redirects;
- upload/content-type handling;
- error leakage;
- unsafe methods.

External-source ingestion must not become an SSRF primitive.

## Object storage security

Production object storage must:

- preserve immutable verified artifacts;
- use least-privilege credentials;
- reject arbitrary public writes;
- have backup/lifecycle policy;
- support integrity verification;
- expose only material intended for public access.

## Database security

Use:

- non-superuser application account;
- separate migration/admin privilege where practical;
- TLS where appropriate;
- backups;
- retention;
- restore testing;
- slow-query visibility.

## Backups / restore

Define policy for:

- PostgreSQL;
- object storage;
- critical configuration metadata.

Document:

- frequency;
- retention;
- encryption;
- recovery procedure;
- appropriate RPO/RTO targets.

A backup is not accepted until a restore has been tested.

## Disaster recovery drill

Exercise:

```text
new environment
↓
restore DB
↓
restore/reconnect object storage
↓
migrate
↓
verify hashes
↓
start services
↓
run smoke/quality checks
```

Record actual steps and timing.

## Observability

Reuse the Phase 13 observability foundation.

Production visibility should include:

- health/readiness;
- metrics;
- structured logs;
- request IDs;
- queue depth;
- ingestion failures;
- quarantine;
- parser review;
- citation states;
- processing runs;
- AI run states;
- DB/object-store health;
- latency/error rates.

Do not create a parallel monitoring stack unnecessarily.

## Alerts

Create actionable alerts for:

- API unavailable;
- DB unavailable;
- object storage unavailable;
- stuck queue;
- repeated ingestion failure;
- quarantine spike;
- backup failure;
- restore verification failure;
- disk/storage capacity;
- high 5xx rate.

Avoid noisy vanity alerts.

## Error tracking / telemetry

If third-party error tracking is used, review payloads.

Do not send court-document text, protected identifiers or sensitive research notes by default.

Document analytics/cookie/telemetry behavior.

## Privacy / public disclosures

Document clearly:

- sources are public;
- confidential/ex parte/private material is excluded;
- external-source coverage limits;
- AI limits;
- telemetry;
- user-note retention if applicable.

The UI must not imply that this is an official KSC product.

## Public disclaimers

Show appropriate neutral disclaimers:

- independent research tool;
- network connections do not imply wrongdoing;
- AI analysis is not court record;
- external public sources are distinct from court evidence;
- users should verify important citations against original sources;
- not legal advice.

## Source availability

Keep official-source links.

If an official source later disappears/changes:

- preserve provenance;
- report availability honestly;
- do not describe a cached copy as the current official page.

## AI provider security / cost

For external model providers:

- secrets only server-side;
- explicit model/provider config;
- timeouts/retries;
- fail-closed behavior;
- request/token limits;
- budget/concurrency controls;
- clear policy for what source text may be sent externally.

The app must remain useful with AI disabled.

## Performance

Define beta targets for:

- home;
- search;
- reader;
- network;
- timeline;
- finding detail;
- AI research;
- appeal research.

Measure on realistic corpus data.

## Load test

Run a modest beta-scale test including representative:

- search;
- documents;
- reader;
- network;
- timeline.

Record:

- p50;
- p95;
- error rate;
- DB/resource behavior.

## Accessibility

Audit important workflows for:

- keyboard;
- semantic headings;
- labels;
- focus;
- contrast;
- responsive/mobile behavior.

Use both automated and manual checks.

## Browser/device support

Document supported modern browsers and mobile behavior.

## Security review

Perform a focused review of:

- API;
- ingestion;
- external-source capture;
- object storage;
- auth/admin;
- AI endpoints;
- export;
- file/path handling.

Resolve critical/high findings before beta.

Document accepted lower-risk items.

## Dependency / supply chain

Maintain:

- lockfiles;
- dependency updates;
- vulnerability scans;
- Dependabot/Renovate or equivalent;
- container scanning if applicable.

Do not auto-merge security updates without tests.

## CI/CD

Make deployment reproducible.

At minimum:

```text
lint
typecheck
test
build
migration safety
deploy
readiness
smoke test
```

Avoid undocumented manual server mutation.

## Migration safety

Production migrations must be reviewed, backed up where appropriate, and have rollback/recovery guidance.

Do not run destructive schema changes casually.

## Operational runbooks

Document:

- deploy;
- rollback;
- ingestion;
- capture import;
- quarantine review;
- parser reprocess;
- citation re-resolution;
- backup;
- restore;
- metrics;
- health;
- incident response.

## Lawyer / researcher beta

Run a small structured beta with legal/research users where available.

The platform should support human agency: organize and cite records, not make legal decisions for the user.

Evaluate:

- source trust;
- citation usability;
- document navigation;
- findings/evidence workflow;
- statement comparison;
- appeal research;
- AI usefulness;
- confusing labels;
- missing workflows;
- performance.

Do not collect unnecessary personal data.

## Neutral beta tasks

Examples:

- locate a filing by exact reference;
- trace a citation;
- inspect an evidence path;
- compare two source-backed statements;
- review Court treatment;
- verify an AI answer;
- distinguish external material from court record.

## Feedback classification

Classify:

- bug;
- data/provenance issue;
- UX;
- missing feature;
- performance;
- legal-language clarity;
- security/privacy;
- AI quality.

Prioritize integrity/provenance defects over convenience features.

## Production quality gate

Create a Phase 16 gate covering:

- deploy reproducibility;
- HTTPS;
- secrets;
- authorization;
- backup/restore;
- observability/alerts;
- security review;
- dependency scan;
- load test;
- accessibility;
- production smoke tests;
- beta feedback disposition.

## Acceptance criteria

Phase 16 is complete when:

- staging/production deployment is reproducible;
- production uses real data only;
- HTTPS/security configuration is active;
- privileged write/admin operations are protected;
- backup and restore are proven;
- observability and actionable alerts are active;
- critical/high security findings are resolved;
- representative load test passes the defined beta targets;
- agreed accessibility/mobile baseline passes;
- deploy/rollback/runbooks exist;
- public source/AI/network disclaimers are visible;
- lawyer/researcher beta is completed, or documented as the only remaining external dependency;
- no unresolved integrity/provenance blocker exists.

## Stop condition

Do not call the platform production-ready if recovery, security or source integrity is unproven.

## Completion report

```text
PHASE 16 STATUS
DEPLOYMENT ARCHITECTURE
ENVIRONMENTS
AUTH / AUTHORIZATION
SECURITY
BACKUPS / RESTORE
OBSERVABILITY / ALERTS
AI PROVIDER SECURITY / COST
PERFORMANCE / LOAD TEST
ACCESSIBILITY
CI/CD
RUNBOOKS
LAWYER / RESEARCHER BETA
QUALITY GATE
TESTS
KNOWN LIMITATIONS
COMMITS
TAG
NEXT
MEMORY
```
