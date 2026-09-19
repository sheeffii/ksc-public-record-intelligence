# KSC Public Record Intelligence

Citation-first research platform over the **public** court record of
**KSC-BC-2020-06** (Kosovo Specialist Chambers). Neutral, evidence-driven, and built
so that every statement resolves to a page, paragraph or line of the record — or is
withheld.

> Status: **Phase 4 — engineering foundation.** No court documents have been
> ingested. No AI is wired. Every approved route renders the application shell.

## Principles

```
PRIMARY COURT SOURCES → DATABASE → STRUCTURED EVIDENCE → PROVENANCE / CITATIONS
→ SEARCH / NETWORK / ANALYSIS → AI
```

- The record is authoritative; AI is analysis only.
- A connection never implies wrongdoing. No score of any person exists in the data model.
- Protected witnesses are shown only as their public code (e.g. `W01234`).
- A citation that does not resolve is not rendered.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

| Service               | URL                                                                 |
| --------------------- | ------------------------------------------------------------------- |
| Web (Next.js)         | http://localhost:3000                                               |
| API (FastAPI)         | http://localhost:8000 · `/health` · `/ready` · `/version` · `/docs` |
| MinIO console         | http://localhost:9001                                               |
| PostgreSQL (pgvector) | localhost:5432                                                      |
| Redis                 | localhost:6379                                                      |

Host-side development: `make setup && make infra && make dev`. All commands:
`make help`. Details in `docs/DEVELOPMENT.md`.

## Repository

```
apps/web          Next.js frontend (TypeScript strict, Tailwind 4, next-intl EN/SQ)
apps/api          FastAPI backend (SQLAlchemy 2, Alembic, PostgreSQL + pgvector)
workers/          ingestion / analysis placeholders (nothing runs yet)
packages/shared   TypeScript contract types from the design handoff
packages/prompts  reserved
tests/            backend unit + integration, Playwright e2e, fixtures, evaluation
docs/design/      approved UX — read-only source of truth for the frontend
docs/             ARCHITECTURE · DATA_MODEL · DECISIONS · SECURITY · AI_METHODS · INGESTION · DEVELOPMENT · PROJECT_STATE
```

## Working in this repo

Read `CLAUDE.md` (permanent rules), then `MEMORY.md` (where work stopped).
