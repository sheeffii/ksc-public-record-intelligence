# Architecture

KSC Public Record Intelligence is a citation-first research platform over the public
record of **KSC-BC-2020-06**. This document describes the system as it exists after
Phase 4 (engineering foundation) and the layers planned above it.

## The authoritative hierarchy

```
PRIMARY COURT SOURCES        official public documents, transcripts, exhibits
        ↓
DATABASE                     PostgreSQL — the system of record for what we hold
        ↓
STRUCTURED EVIDENCE          documents, pages, segments, witnesses, exhibits, findings…
        ↓
PROVENANCE / CITATIONS       every structured fact points back to page / ¶ / line
        ↓
SEARCH / NETWORK / ANALYSIS  derived views, computed from the layers above
        ↓
AI                           analysis only — never a source of truth
```

**Database + primary sources + provenance + citations are authoritative.** AI
operates above these systems, reads from them, and produces analysis that is
always labelled as such and always cites downward. The product is not built
around "AI memory"; AI memory is not evidence.

## Monorepo layout

```
apps/web            Next.js 16 · React 19 · TypeScript strict · Tailwind 4 · next-intl · next-themes
apps/api            FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic · psycopg 3
workers/ingestion   ksc_ingestion — controlled public-only ingestion (Phase 7)
workers/analysis    placeholder — embeddings / retrieval / AI analysis (later)
packages/shared     TypeScript contract types (Citation, VerificationState, Witness, …)
packages/prompts    reserved for versioned prompt templates (empty)
infrastructure/     Docker assets beyond compose (empty in Phase 4)
scripts/            operational scripts
tests/              backend unit + integration, Playwright e2e, fixtures, evaluation
docs/               this documentation; docs/design is the approved UX (read-only)
```

## Frontend (`apps/web`)

- **App Router**, one page per approved route in `docs/design/ROUTE_MAP.md`. The
  registry lives in `src/lib/routes.ts` and a test asserts every route has a page.
- **Tokens** in `src/styles/globals.css`, transcribed from `DESIGN_SYSTEM.md`.
  Components use Tailwind utilities bound to tokens; no component hardcodes a hex.
- **Theme**: dark is the default and semantic ("working over the record"). Light is
  applied per surface by `<SurfaceTheme mode="light">` for the Document Reader and
  Public mode. `next-themes` provides the user-preference infrastructure (ADR-006).
- **i18n**: `next-intl` without routing; the locale is a cookie, never a URL
  prefix. Tables in `src/i18n/messages/{en,sq}.json`; Albanian is provisional.
- **Shell**: `AppShell` = GlobalNav (52px) · CaseStripe (32px) · content ·
  GovernanceFooter (26px) · MobileTabBar (<860px).
- **Provenance primitives**: `SourceBadge`, `VerificationBadge`, `CitationChip`
  (returns `null` when `resolved === false`), `ProvenanceBoundary`.
- **Primitives**: `DataTable` + `DensityToggle`, `Panel`, filters, `SkeletonBlock`,
  `EmptyState` (three required lines), `ErrorState` (names its scope), `GapNotice`,
  `Modal`, `Drawer` (Radix Dialog).
- **Repository boundary** (`src/data/`, ADR-008 → ADR-009): screens consume
  screen-facing types through `ResearchRepository`, an asynchronous contract with
  two adapters — `createMockRepositoryAdapter()` (the bundled Phase 5 mock, the
  default) and `createApiRepository()` (the read API). `getRepository()` chooses
  from `NEXT_PUBLIC_DATA_SOURCE=mock|api`; the base URL is `API_INTERNAL_URL` on
  the server and `NEXT_PUBLIC_API_URL` in the browser. `src/data/api/mappers.ts`
  is the only place that knows the wire shapes: it turns unresolved citations
  into `resolved: false`, drops human-rejected facts, keeps protected witnesses
  code-only, and never builds a citation display string. Screens still import
  the synchronous mock directly; moving them onto `getRepository()` is Phase 5B
  work, not a contract change.

## API (`apps/api`)

- `create_app()` in `ksc_api/main.py`; routers under `ksc_api/routers/`.
- System endpoints: `GET /health` (liveness), `GET /ready` (PostgreSQL, pgvector,
  Redis, MinIO; 503 when any is down), `GET /version`.
- **Read API** (`ksc_api/routers/records.py`, prefix `/api/v1`): `case`,
  `documents` (+ `document-versions/{ref}/pages|chunks`), `people`, `witnesses`,
  `exhibits`, `incidents`, `findings`, `claims`, `arguments`, `events`,
  `transcripts/{ref}`, `citations/{id}`, `citations/resolve?ref=`, `network`,
  `relationships`, `search`. Lists paginate with `limit` (≤ 200) / `offset` and
  return `{items, total, limit, offset}`. There is no write endpoint.
- **Layering**: router → `RecordRepository` (`ksc_api/repositories/records.py`,
  one instance per request, scoped to the configured case) → `mappers.py` →
  Pydantic read models in `ksc_api/schemas/`. Raw ORM objects never leave the
  repository. `filters.py` holds the fail-closed rules every query applies:
  visibility `public` / `public_redacted` only, human-rejected facts withheld,
  anything depending on an unresolved citation withheld, both ends of an edge
  public. A document that exists but is not public is _stated_
  (`visibility: not_public`, no versions) instead of a 404. The `WitnessRead`
  serializer omits `public` structurally for anything not explicitly public.
- Settings via `pydantic-settings` (`ksc_api/config.py`); `CASE_ID` selects the
  case the API serves (the case is never a route segment). No AI key is required.
- Sync SQLAlchemy 2.0 with psycopg 3; sessions are FastAPI dependencies. Enum
  columns persist member _values_ (`db_enum`), matching the PostgreSQL types.
- Alembic migrations in `apps/api/alembic/`: `0001` (foundation) and `0002` (the
  evidence model, `docs/DATA_MODEL.md`). Enum types are created and dropped
  explicitly; `alembic check` is part of the integration suite.
- `ksc-seed` inserts public metadata for KSC-BC-2020-06 (idempotent);
  `ksc-demo-fixture` loads the synthetic `KSC-DEMO-0000` evidence graph used by
  tests. The container entrypoint runs migrations then seed before serving.

## Database

PostgreSQL 16 with the **pgvector** extension enabled from the first migration so
later phases can add embedding columns without a privileged step. Phase 6 holds
the normalized evidence model — 37 tables described in `docs/DATA_MODEL.md` —
with provenance, visibility, verification and versioning as first-class columns,
the `citations` resolution index, the `record_identifiers` lookup, and a
`graph_nodes` registry that gives polymorphic graph references real foreign keys
(ADR-010). Search will use PostgreSQL full-text + pgvector before any separate
search engine is considered (ADR-002).

## Object storage

MinIO (S3-compatible) holds original document bytes under `MINIO_BUCKET_DOCUMENTS`.
Every stored object will carry a SHA-256 and the official public URL it came from.
Nothing is stored yet.

## Redis

Reserved for job queues (ingestion / analysis workers), short-lived caches and
rate limiting. Only connectivity is verified in Phase 4.

## Workers

- **ingestion** (`workers/ingestion`, package `ksc_ingestion`, CLI
  `ksc-ingest`) — Phase 7: operator capture bundle → discovery provenance
  (`source_records`) → normalization → public-only gate → SHA-256 → MinIO →
  `documents` / `document_versions` (+ hearings / transcripts) → job items and
  audit log. Official hosts only; a bot-mitigation challenge is a recorded
  failure, never bypassed (ADR-011). Parsing, citation extraction and
  resolution are Phase 8. See docs/INGESTION.md.
- **analysis** (placeholder) — embeddings, retrieval, AI analysis, relationship extraction,
  potential-issue surfacing. All output is `AI ANALYSIS`, cited, and withheld when
  any citation is `UNRESOLVED`.

## Future layers

### Ingestion beyond Phase 7 (docs/INGESTION.md)

Parsing, segmentation, citation extraction and the wider corpus remain later
phases. Controlled, per-document, auditable (ADR-003).

### Citation resolution index (ADR-005)

Resolution is computed **at ingest**, not at request time:

```
DOCUMENT INGESTION → CITATION EXTRACTION → CITATION RESOLUTION
       → PERSISTED RESOLUTION INDEX → FAST RUNTIME LOOKUP
```

Each extracted raw citation (`F01234`, `F01234/RED`, `P00123`, `W01234`, transcript
page/line, judgment paragraph, other decisions) is stored with its resolved target,
a confidence, and a verification state. Unresolvable citations persist as
`UNRESOLVED` and block rendering of dependent content. The runtime never guesses.

### Search

PostgreSQL full-text search over segments and metadata, with pgvector for semantic
retrieval. Protected-witness records live in an index with no name field so a name
can never resolve to a W-code (DESIGN_DECISIONS.md §18.2).

### Evidence graph

Implemented as schema and read API in Phase 6: nodes are registry rows over
record entities; **every edge carries a `citation_id`** (`NOT NULL`,
`RESTRICT`). Edges whose citation is unresolved exist in the table but are never
returned; rejected edges likewise. Paths over the real graph (`getPath`) are
Phase 9 and are computed per request, ordered by hop count only.

### AI layer (docs/AI_METHODS.md)

Retrieval before composition; block order returned by the API; the record/AI
boundary is structural in the payload (`AnswerBlock.kind`). No guilt, suspicion,
credibility or success scores exist anywhere in the pipeline or the schema.

## Cross-cutting rules enforced in code

| Rule                                         | Where                                                                               |
| -------------------------------------------- | ----------------------------------------------------------------------------------- |
| No score/rank/weight field of any person     | `tests/unit/test_models.py` scans every column name; `@ksc/shared` types carry none |
| Unresolved citation ⇒ not rendered           | `CitationChip` returns `null`; tested                                               |
| Interface strings from the string table only | `src/i18n/messages/*`; key-parity test                                              |
| Official identifiers never translated        | `UNRESOLVED` literal test; identifiers rendered via `identifier` utility            |
| Document date ≠ filing date                  | separate nullable columns; tested                                                   |
| Light surface only for reader/public         | route registry test                                                                 |
