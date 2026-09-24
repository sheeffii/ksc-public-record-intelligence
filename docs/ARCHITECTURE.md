# Architecture

KSC Public Record Intelligence is a citation-first research platform over the public
record of **KSC-BC-2020-06**. This document describes the system through Phase 12.

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
workers/analysis    placeholder — later embedding or extended analysis jobs
packages/shared     TypeScript contract types (Citation, VerificationState, Witness, …)
packages/prompts    immutable, versioned AI prompt templates
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
  the synchronous mock directly except real-data Search, Document Reader,
  Network, Timeline, Finding Matrix, AI Research, Appeal Research, Argument Lab,
  and Statement Comparison routes, which server-load through `getRepository()`
  and consume API data.

## API (`apps/api`)

- `create_app()` in `ksc_api/main.py`; routers under `ksc_api/routers/`.
- System endpoints: `GET /health` (liveness), `GET /ready` (PostgreSQL, pgvector,
  Redis, MinIO; 503 when any is down), `GET /version`.
- **Read API** (`ksc_api/routers/records.py`, prefix `/api/v1`): `case`,
  `documents` (+ `document-versions/{ref}/pages|paragraphs|chunks`), `people`, `witnesses`,
  `exhibits`, `incidents`, `findings`, `claims`, `arguments`, `events`,
  `transcripts/{ref}`, `citations/{id}`, `citations/resolve?ref=`, `network`,
  `relationships`, `search`. Lists paginate with `limit` (≤ 200) / `offset` and
  return `{items, total, limit, offset}`.
- **AI research API** (`ksc_api/routers/ai.py`): create/list/read audited runs and
  save a valid output as an explicitly AI-assisted research note. It cannot
  mutate sources, findings, citation resolution, relationships, or verification.
- **Appeal research API** (`ksc_api/routers/appeal.py`): list/read potential
  issues, read a source-backed Argument Lab, review an issue, save a
  source-whitelisted human note, and list exact statement comparisons. Issues,
  source roles, Court treatment, red-team perspectives, missing material and
  human verification are first-class; no endpoint scores or predicts an appeal.
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
  case the API serves (the case is never a route segment). The deterministic AI
  provider requires no key; compatible external providers are opt-in.
- Sync SQLAlchemy 2.0 with psycopg 3; sessions are FastAPI dependencies. Enum
  columns persist member _values_ (`db_enum`), matching the PostgreSQL types.
- Alembic migrations in `apps/api/alembic/`: `0001`–`0008`, through Phase 12's
  appeal issues, exact issue-source links, missing material, statement
  comparisons, red-team reviews/findings, and issue-linked research notes.
  Enum types are created and dropped
  explicitly; `alembic check` is part of the integration suite.
- `ksc-seed` inserts public metadata for KSC-BC-2020-06 (idempotent);
  `ksc-demo-fixture` loads the synthetic `KSC-DEMO-0000` evidence graph used by
  tests. The container entrypoint runs migrations then seed before serving.

## Database

PostgreSQL 16 with the **pgvector** extension enabled from the first migration so
later phases can add embedding columns without a privileged step. Phase 6 holds
the normalized evidence model — 47 tables described in `docs/DATA_MODEL.md` —
with provenance, visibility, verification and versioning as first-class columns,
the `citations` resolution index, the `record_identifiers` lookup, and a
`graph_nodes` registry that gives polymorphic graph references real foreign keys
(ADR-010). Search will use PostgreSQL full-text + pgvector before any separate
search engine is considered (ADR-002).

## Object storage

MinIO (S3-compatible) holds original document bytes under `MINIO_BUCKET_DOCUMENTS`.
Every stored object will carry a SHA-256 and the official public URL it came from.
The controlled corpus holds 22 hash-addressed official public PDFs; no bulk corpus.

## Redis

Reserved for job queues (ingestion / analysis workers), short-lived caches and
rate limiting. Only connectivity is verified in Phase 4.

## Workers

- **ingestion** (`workers/ingestion`, package `ksc_ingestion`, CLI
  `ksc-ingest`) — Phase 7: operator capture bundle → discovery provenance
  (`source_records`) → normalization → public-only gate → SHA-256 → MinIO →
  `documents` / `document_versions` (+ hearings / transcripts) → job items and
  audit log; then held-object native parsing, structural chunks, transcript lines,
  deterministic citation resolution and lexical indexing. Official hosts only;
  a bot-mitigation challenge is a recorded failure, never bypassed (ADR-011).
  Deterministic, network-free projections build the real finding matrix, evidence
  graph/timeline, and hand-reviewed Phase 12 appeal benchmark; separate quality
  gates audit each projection.
- **analysis** remains a worker placeholder. Phase 11 retrieval, provider
  orchestration and deterministic validation run in the API service layer;
  future embeddings or long-running analysis may move behind this worker without
  changing the audit contract.

## Derived layers

### Citation resolution index (ADR-005)

Resolution is computed **at ingest**, not at request time:

```
DOCUMENT INGESTION → CITATION EXTRACTION → CITATION RESOLUTION
       → PERSISTED RESOLUTION INDEX → FAST RUNTIME LOOKUP
```

Each extracted raw citation (`F01234`, `F01234/RED`, `P00123`, `W01234`, transcript
page/line, judgment paragraph, other decisions) is stored with its resolved target,
a deterministic-match confidence, and a verification state. Unresolvable citations persist as
`UNRESOLVED` and block rendering of dependent content. The runtime never guesses.

### Search

Phase 8/11 use PostgreSQL generated `tsvector` columns and GIN indexes over public
metadata, structural chunks and transcript segments, plus exact normalized
identifier lookup. Results retain version and PDF/printed page/paragraph/line
coordinates. Phase 11 combines that lexical retrieval with verified structured
findings/arguments. pgvector remains installed but no embedding is created.

### Evidence graph

Nodes are registry rows over record entities; **every edge carries a
`citation_id`** (`NOT NULL`, `RESTRICT`). Phase 9 projects resolved inter-document
citations from the controlled corpus as deterministic `CITED_IN` edges with an
explicit source category, extraction origin and optional typed date. Edges whose
citation is unresolved or rejected are never returned. `GET /api/v1/network/path`
runs a bounded breadth-first search over public source-backed edges only; each
returned hop includes its own citation and ordering is by hop count only.
`GET /api/v1/network?focus_ref=` returns one entity's neighbourhood; the
reference is resolved by exact identifier match only, never by label similarity.

The same database-only projection creates timeline events from persisted
document and hearing dates. Date type and precision remain separate, and each
projected event points to its official `source_record`. At the measured Phase 9
scale (13 nodes, 22 edges), the existing SVG renderer remains performant and
retains its textual alternative; WebGL is deferred until real scale requires it.

### AI layer (docs/AI_METHODS.md)

Phase 11 persists exact ranked source snapshots before provider generation and
then validates source IDs, category, exact quotations, answer order and the
non-factual AI boundary independently of the provider. A validation error or
insufficient source withholds the whole answer. The record/AI boundary is
structural in the payload (`AnswerBlock.kind`) and visual in the UI. No guilt,
suspicion, credibility or success scores exist anywhere in the pipeline or schema.

### Appeal research layer (ADR-017)

Phase 12 keeps a potential issue distinct from the underlying canonical finding.
Every affirmative issue-source relationship has an exact citation and a human
verification state; absent sources are separate missing-material rows. Court
treatment records only what can be located (`addressed`, `accepted`, `rejected`,
`distinguished`, `qualified`, `not_located`, or `unresolved`) and `not_located`
never means ignored.

Statement comparisons require two distinct exact citations and use only the
roadmap's neutral classifications. Red-team reviews retain Defence analyst, SPO
red-team and neutral-reviewer findings without choosing a winner. AI-assisted
reviews, if later created through the Phase 11 boundary, must reference an
audited `ai_run`; the real controlled-corpus benchmark is human-reviewed and
returns `insufficient_record` rather than filling missing material.

### External public-source layer (ADR-021)

Phase 14 is a sibling research layer, not an extension of the court evidence
hierarchy. `external_sources`, `media_items` and `media_statements` retain
lawfully public URL metadata, publication/capture timestamps, hashes and exact
short excerpts. `court_media_links` is the only bridge into the court record.
`MENTIONED`, `TENDERED`, `ADMITTED`, `REJECTED`, `DISCUSSED` and `RELIED_UPON`
require a human-verified exact court citation; invalid links are withheld from
the API even if malformed data is introduced outside the application.

External search, timeline and network projections have their own `/api/v1/media`
namespace. Combined search renders court and external results in separate panels.
An `EXTERNAL_ONLY` item creates no court-network edge. The Phase 11 retrieval
schema does not admit an external source category, so external material cannot
silently enter a court-record answer. Future AI use needs an explicit external
answer category and a separately reviewed prompt/validator contract.

### Structured intelligence (Phase 19, ADR-024/025)

```text
ENTITY (person · witness code · organization · exhibit)
  ← ALIAS (speaker label | source-backed full name, with exact span)
  ← IDENTITY RESOLUTION (identity.py: VERIFIED · REVIEW_REQUIRED · AMBIGUOUS · SEARCH_ONLY)
  ← ENTITY OCCURRENCE (entity_occurrences: rule, run, anchor, char range)
  → EVIDENCE-BACKED EDGE (relationships: exactly one citation | occurrence | appearance)
SEARCH MATCH — lexical only, never stored, labelled SEARCH_MATCH
```

The worker pipeline runs in a fixed order: `reresolve`, then `build-evidence`
(citation edges), then `build-intelligence`. `build-intelligence` itself runs
caption aliases, then transcript-header appearances, then exhibit status events,
then verified mentions, then typed edges. `report-phase19b` is the read-only
reconciliation gate.

The read side gives every evidence kind the same `ProvenanceRead` shape. The
endpoints are:

- `/network/edges`, a bounded, cursor-paginated edge service with type, entity,
  evidence, document and date filters;
- `/witnesses/{code}/appearances`;
- `/people/{slug}/appearances`;
- `/exhibits/{id}/status-events`.

## Cross-cutting rules enforced in code

| Rule                                         | Where                                                                               |
| -------------------------------------------- | ----------------------------------------------------------------------------------- |
| No score/rank/weight field of any person     | `tests/unit/test_models.py` scans every column name; `@ksc/shared` types carry none |
| Unresolved citation ⇒ not rendered           | `CitationChip` returns `null`; tested                                               |
| Interface strings from the string table only | `src/i18n/messages/*`; key-parity test                                              |
| Official identifiers never translated        | `UNRESOLVED` literal test; identifiers rendered via `identifier` utility            |
| Document date ≠ filing date                  | separate nullable columns; tested                                                   |
| Light surface only for reader/public         | route registry test                                                                 |
