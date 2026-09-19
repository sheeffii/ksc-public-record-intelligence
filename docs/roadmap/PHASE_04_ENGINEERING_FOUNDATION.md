# Phase 4 — Engineering Foundation

**Status:** Completed and checkpointed.

## Goal

Create a production-quality monorepo and persistent project-memory system without implementing real ingestion, real evidence analysis, or AI.

Phase 4 should provide a stable platform on which all later milestones can build.

## Core technology direction

### Frontend

- Next.js;
- React;
- TypeScript strict;
- Tailwind;
- reusable design/provenance primitives;
- EN/SQ infrastructure;
- light/dark/surface theming.

### Backend

- Python 3.12+;
- FastAPI;
- Pydantic v2;
- SQLAlchemy;
- Alembic.

### Infrastructure

- PostgreSQL 16+;
- pgvector;
- Redis;
- MinIO/S3-compatible storage;
- Docker Compose.

### Quality

- pytest;
- Ruff;
- mypy;
- ESLint/Prettier;
- frontend unit tests;
- Playwright infrastructure;
- CI.

## Repository structure

Expected general shape:

```text
apps/
  web/
  api/
workers/
  ingestion/
  analysis/
packages/
  shared/
  prompts/
infrastructure/
scripts/
tests/
docs/
  design/
data/
CLAUDE.md
AGENTS.md
MEMORY.md
README.md
docker-compose.yml
.env.example
Makefile
```

## Persistent memory architecture

### `CLAUDE.md`

Permanent project rules:

- mission;
- design source of truth;
- evidence rules;
- protected-witness rules;
- citation rules;
- development conventions;
- session startup/end procedures.

### `AGENTS.md`

Agent-neutral permanent instructions for coding tools that use this convention.

### `MEMORY.md`

Live checkpoint answering: “Where exactly did we stop?”

Should include:

- current branch/commit/milestone;
- current task;
- what works;
- frontend/backend/infra state;
- test state;
- problems;
- recent decisions;
- next actions;
- blockers;
- useful commands.

### `docs/PROJECT_STATE.md`

Longer-term milestone/feature/technical-debt tracker.

### `docs/DECISIONS.md`

ADR-style architectural decisions.

## Required ADRs / principles

Include at least:

- citation-first architecture;
- PostgreSQL + pgvector before a separate search engine;
- controlled ingestion before bulk ingestion;
- design package as frontend source of truth;
- citation-resolution index at ingestion time.

## Frontend foundation

Implement:

- app shell;
- navigation;
- responsive shell;
- theme infrastructure;
- EN/SQ infrastructure;
- design tokens;
- source badge;
- verification badge;
- citation chip;
- panels/tables/filters;
- loading/empty/error states;
- placeholder route coverage.

Do not implement all full product screens yet.

## Backend foundation

Implement:

- `/health`;
- `/ready`;
- `/version`;
- PostgreSQL/pgvector connection;
- Redis connection;
- MinIO configuration;
- Alembic;
- minimal `Case`, `Document`, `AuditLog` models;
- seed only basic case metadata for `KSC-BC-2020-06`.

## Docker

Services:

- web;
- api;
- postgres;
- redis;
- minio.

Target developer experience:

```bash
cp .env.example .env
docker compose up --build
```

## Prohibited work

Do not implement:

- KSC crawling;
- PDF download/parsing;
- OCR;
- embeddings;
- RAG;
- real AI providers;
- evidence extraction;
- contradiction analysis;
- appeal analysis;
- full schema.

## Testing

Verify:

- API health/readiness;
- DB connectivity;
- pgvector availability;
- frontend shell/navigation;
- EN/SQ;
- theme switching;
- route rendering;
- provenance primitive behavior;
- lint/typecheck;
- Docker health.

## Acceptance criteria

- monorepo works;
- design package untouched;
- frontend/backend start;
- Postgres/pgvector/Redis/MinIO work;
- migrations work;
- CI exists;
- tests pass;
- memory/decision docs exist;
- citation-resolution architecture is documented.

## Stop condition

Stop before implementing the full UI or real data.

## Completion report

```text
PHASE 4 STATUS
WORKING
TESTS
ISSUES
COMMITS
NEXT
MEMORY
```
