# Project state

Long-term implementation tracker. `MEMORY.md` is the live checkpoint; this file
tracks milestones, features, debt and status across sessions.

Last updated: 2026-09-24 (Phase 18 Pass A checkpoint)

## Milestones

| Phase  | Scope                                                                                                     | Status                                                                                                   |
| ------ | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 1–3    | Product definition, design system, 21-artboard UX package, flow audit                                     | ✅ Delivered (docs/design)                                                                               |
| **4**  | **Engineering foundation** — monorepo, shell, tokens, i18n, theme infra, API, DB, Docker, tests, CI, docs | ✅ **Complete (2026-09-19)**                                                                             |
| **5**  | **Implement approved UI with mock data (all 21 screens + 5 directories, DemoDataFlag everywhere)**        | ✅ **Functionally complete (2026-09-19)** — visual parity: remediation pending (Phase 5B)                |
| **6**  | **Real database / evidence model and API-backed repository contracts**                                    | ✅ **Complete (2026-09-20)**                                                                             |
| **5B** | **UI/UX visual parity remediation against `docs/design/Design.html`**                                     | ✅ **Complete (2026-09-20)**                                                                             |
| **7**  | **KSC public record discovery + controlled document ingestion (first real KSC data)**                     | ✅ **Complete (2026-09-20)** — 22 real public records, quality gate 22/22, idempotent (ADR-011, ADR-012) |
| **8**  | **Parsing, exact citations, resolution index, search**                                                    | ✅ **Complete (2026-09-20)** — controlled-corpus quality gate PASS (ADR-013)                             |
| **9**  | **Real evidence network and timeline**                                                                    | ✅ **Complete (2026-09-21)** — controlled-corpus quality gate PASS (ADR-014)                             |
| **10** | **Judgment, findings and evidence matrix**                                                                | ✅ **Complete (2026-09-21)** — real Court-decision quality gate PASS (ADR-015)                           |
| **11** | **Citation-first AI / RAG**                                                                               | ✅ **Complete (2026-09-21)** — real-corpus AI quality gate PASS (ADR-016)                                |
| **12** | **Appeal research, red team and statement comparison**                                                    | ✅ **Complete (2026-09-21)** — real-corpus appeal quality gate PASS (ADR-017)                            |
| **13** | **Gradual full public corpus ingestion and production hardening**                                         | ✅ **Complete (2026-09-22)** — real-scale gate PASS 61/50 (ADR-018, ADR-019, ADR-020)                    |
| **14** | **External media and public statements intelligence**                                                     | ✅ **Complete (2026-09-22)** — controlled real-public-source gate PASS (ADR-021)                         |
| **15** | **Real data UI completion and demo removal**                                                              | ✅ **Complete (2026-09-22)** — route-level real-data gate PASS                                           |
| **16** | **Production readiness, security and lawyer beta**                                                        | **IN PROGRESS** — local gates pass; external deployment/alerting gates intentionally deferred            |
| **17** | **Historical corpus expansion, coverage and continuous sync**                                             | ✅ **COMPLETE (2026-09-24)** — known-public-corpus scope; no exhaustive-corpus claim                     |
| **18** | **Research experience and visual excellence**                                                             | **IN PROGRESS** — Pass A implemented and verified; Phase 18 not complete                                 |

## Roadmap

The persistent execution plan is `docs/roadmap/` (installed 2026-09-19):
`00_MASTER_ROADMAP.md` is the high-level plan and each `PHASE_*.md` is the
execution specification for one milestone. Phases 6, 5B, and 7–14 are complete.
The table above is the status record; the roadmap files hold scope and acceptance
criteria. Phase 13 is complete: the second lawful operator-assisted capture
raised the corpus to 62 source records / 61 held versions and the real-scale
gate passes at 61/50. Phase 14 is complete: 3 controlled public pages from 2
publishers pass the external-source gate while remaining structurally separate
and `EXTERNAL_ONLY`. Phase 15 is complete: production routes default to real
APIs or honest empty states, demo fallbacks are removed from normal routes, and
the desktop/mobile route-level gate passes. Phase 16A implements the production,
security and operations surfaces. Phase 16B verified the local implementation;
the blocker-resolution pass closed performance and manual security/accessibility.
An authorized deployment target, live alert/IAM verification and production
smoke remain pending. The external beta protocol is documented as an external
dependency, not an active completion blocker. Phase 16 remains **IN PROGRESS**;
its remaining blockers are external deployment/alerting only and it will resume
when public deployment is desired. Phase 17 is complete against its explicitly
declared known-public-corpus scope. Phase 18 Pass A aligns the research surfaces
to that real-data baseline; Phase 18 remains in progress.
Repository code, migrations, tests and Git state win over stale roadmap text.

## Completed features (Phase 4)

Frontend (`apps/web`)

- Next.js 16 / React 19 / TS strict / Tailwind 4; standalone Docker build.
- Design tokens transcribed from DESIGN_SYSTEM.md (dark + light sets, source palette,
  direction colours, AI surfaces, radii, elevation, chrome heights, breakpoints).
- Two font families via next/font (DM Sans, Libre Baskerville).
- Application shell: GlobalNav (52px, overflow menu <1280px, AI link styling),
  CaseStripe with untranslated case id + DemoDataFlag, GovernanceFooter, five-item
  MobileTabBar (<860px), skip link, SurfaceTheme (light for reader/public).
- Theme infrastructure: next-themes provider (dark default) + tested ThemeToggle
  (not mounted — ADR-006).
- i18n: next-intl without routing, cookie locale, EN/SQ tables (166 keys, parity-tested),
  LanguageToggle with server action.
- Provenance primitives: SourceBadge (9 types), VerificationBadge (5 states, glyphs),
  CitationChip (null when unresolved, deep-links to reader), ProvenanceBoundary.
- Primitives: Button, Panel, DataTable + DensityToggle, FilterChip/ActiveFilters/
  FilterRail/FilterOption, SkeletonBlock, PendingCount, EmptyState, ErrorState,
  GapNotice, Modal, Drawer (Radix).
- 23 route pages per ROUTE_MAP.md rendering PlaceholderScreen inside the shell;
  homepage foundation (hero, search → /search, pending-dash stats, explore grid);
  not-found page; /api/health.
- Route registry with tab sets and light/dark modes; citation formatter for the
  four canonical forms.

Backend (`apps/api`)

- FastAPI app factory; `/health`, `/ready` (db, pgvector, redis, minio → 503 on
  failure), `/version`; CORS from env.
- pydantic-settings config; no AI key required.
- SQLAlchemy 2 (sync, psycopg 3); models Case, Document, AuditLog.
- Alembic `0001`: `CREATE EXTENSION vector`, three tables, two enums.
- Idempotent seed of KSC-BC-2020-06 public metadata + audit entry; container
  entrypoint runs migrate + seed.

Infrastructure

- docker-compose: postgres (pgvector/pg16), redis, minio (quay.io) + bucket init,
  api, web — all with healthchecks; `.env.example`; Makefile (dev/up/down/test/
  lint/migrate/reset-db/logs/format/typecheck/seed/e2e/ci).
- GitHub Actions CI: frontend format/lint/typecheck/test/build; backend ruff/mypy/
  pytest with postgres+redis services and MinIO container.

Shared / docs

- `@ksc/shared` contract types (Citation, VerificationState, Witness, Direction,
  ReferenceCounts, AnswerBlock, Gap, DateType, Locale).
- CLAUDE.md, AGENTS.md, MEMORY.md, README.md, docs/ARCHITECTURE.md, DATA_MODEL.md,
  DECISIONS.md (ADR-001…007), SECURITY.md, AI_METHODS.md, INGESTION.md,
  DEVELOPMENT.md.

## Unfinished / deferred (by design)

- Screens reading through `getRepository()` and persistent interaction state
  (Phase 5B / Phase 7).
- Ingestion, parsing and the citation resolver that fills `citations` and
  `record_identifiers` (Phase 7 / Phase 8).
- Production-scale graph rendering and real AI retrieval remain later phases.
- Albanian legal terminology needs specialist review against official KSC texts.

## Completed features (Phase 5)

- Branch `feat/phase-5-approved-ui` created from the verified Phase 4 checkpoint.
- Added the matched `RecordBlock` / `AiAnalysisBlock` provenance pair,
  `CitationPreview`, `ProtectionNotice`, `DirectionBadge` + `ScopeNote`, and
  `ReferenceCountStrip`.
- Added a typed `MockRepository` boundary and centralized generic demo records under
  `apps/web/src/mock/`; no real court material or provider call is involved.
- Replaced every generic route placeholder with the approved mock-data experience:
  overview, search and command palette, directories, dossiers, comparison, readers,
  evidence, network/path, timeline, incident/finding chain, appeal, argument/red
  team, AI research and public/simple mode.
- Implemented desktop and representative mobile states, including collapsible
  reader context and a network bottom-sheet inspector.
- Added keyboard-accessible controls, semantic tables/headings, non-color badge
  labels, reduced-motion handling and a textual graph alternative.
- Added six major E2E workflows across desktop and mobile and regression tests for
  provenance, protected-witness safety, repository validity and prohibited scoring.
- Documentation discrepancy retained without redesign: `HANDOFF.md` says 83
  components while `COMPONENTS.md` inventories 91; its “Nine rules” summary lists ten.

## Completed features (Phase 6)

- Branch `feat/phase-6-evidence-model` from `main` (`3e9f8f8`); tag
  `phase-6-complete`.
- Alembic `0002`: 34 new tables on top of the Phase 4 three; `documents`
  migrated in place (`public_state` → `visibility`, artifact columns →
  `document_versions`); 23 explicit enum types; upgrade with data, `alembic
check` and `head → base → head` are integration-tested.
- Models under `apps/api/src/ksc_api/models/` with schema-level rules:
  protected witness without identity, page/line validation, unique SHA-256,
  resolved-only targets, mandatory relationship provenance, node registry with
  real FKs, reviewer-required human verification, human-only research notes.
- Read API `/api/v1` (24 routes) with Pydantic contracts, case scoping,
  pagination, public-only filtering and structural witness protection.
- Synthetic fixture `KSC-DEMO-0000` (`ksc-demo-fixture`) covering the five
  required traversals plus rejected / unresolved negative rows.
- Frontend `apps/web/src/data/`: `ResearchRepository`, mock adapter (default),
  `ApiRepository` with fail-closed mappers, `getRepository()` selection,
  swap-ability contract test.
- Docs: `DATA_MODEL.md` rewritten, `ARCHITECTURE.md`, `DEVELOPMENT.md`,
  `INGESTION.md`, ADR-009, ADR-010.
- Not done by design: screens still read the sync mock; no path engine; no AI
  run; no embedding column; no real record.

## Completed features (Phase 5B)

- Branch `feat/phase-5b-visual-parity` from `main` (`bdf7293`); tag
  `phase-5b-complete`.
- Every authoritative screen recomposed to PAGE_SPECS regions, rails and
  controls (see MEMORY.md → What Works); five directory routes share one dense
  table workspace with functioning filter / sort / density / pagination /
  export over generated demo volume.
- Shared 5B building blocks in `screens/phase5/Workspace.tsx`; `phase5b`
  string namespace (333 keys, EN/SQ parity); date-type glyph utilities on the
  source palette tokens.
- Mobile: three-detent network sheet, reader sidebar / panel toggles,
  comparison A/B/C control, stage tabs, timeline vertical list, appeal category
  dropdown, term tooltips as bottom sheets.
- Tests: 12 composition / interaction tests, 16-screen visual screenshot spec
  across desktop and Pixel 7, two mobile layout assertions. All prior tests
  green; design docs untouched.
- Not done by design: screens still consume the sync mock; no pixel baselines.

## Completed features (Phase 7)

- Discovery: both official hosts serve a Cloudflare managed challenge to
  automated clients (`HTTP 403`, `cf-mitigated: challenge`), including
  `robots.txt`. Treated as an access control — never bypassed (ADR-011).
  Findings, confirmed URL shapes and open questions:
  `docs/ingestion/OFFICIAL_SOURCES.md`.
- Decision: records enter through **operator capture bundles** (a human saving
  official pages and PDFs in a normal browser; `docs/ingestion/OPERATOR_CAPTURE.md`).
- Delivered: `workers/ingestion` (`ksc_ingestion`) — host allowlist / URL
  classification, identified fetcher with challenge detection that fails
  closed, capture manifest schema + validation, discovery contract,
  normalization (version types, visibility fail-closed, dates, parties),
  SHA-256 + PDF validation, hash-addressed MinIO storage, resumable /
  idempotent pipeline writing `source_records` · `documents` ·
  `document_versions` · `hearings` / `transcripts` · `ingestion_jobs` ·
  `ingestion_job_items` · `audit_log`; CLI `ksc-ingest bundle|probe|status`.
- Schema: migration `0003` — `document_versions.artifact_status`
  (`not_fetched|fetched|failed`, CHECK-tied to hash + object), `byte_size`,
  `fetched_at`, `fetch_method`; new `ingestion_job_items`.
- API: `artifact_status` / `fetched_at` on version reads;
  `GET /api/v1/ingestion/status` (internal data-status view). Web API types
  mirrored.
- Tests: 109 unit (sources, fetch, normalize, artifacts, capture, probe) +
  12 integration (full synthetic bundle, idempotent re-run, crash → resume,
  metadata-only fill, never-overwrite, duplicate bytes, fail-closed
  visibility, wrong case, other-case refusal, dry run, recorded blocked probe,
  status endpoint) over the synthetic `KSC-DEMO-0000` bundle
  (`tests/support/synthetic.py`). No real record is described by any fixture.
- Real capture (2026-09-20): operator browser session → 22-record capture
  (normalised detail-page snapshots, manifest, capture-time SHA-256 / sizes)
  plus 22 separately downloaded PDFs. `ksc-ingest import-capture` matched all
  22 by exact SHA-256, confirmed references against the PDF headers (ADR-012)
  and wrote bundle `2026-09-20-corpus-01` (git-ignored).
- Ingested: 22 source records · 19 documents · 22 versions (all fetched) ·
  2 hearings · 3 transcripts · 22 MinIO objects (24,429,094 bytes). Coverage:
  indictment annex EN/SQ, SPO (incl. 716-page final trial brief COR/RED),
  Defence for all four accused, Pre-Trial Judge / Trial Panel / President
  decisions, Court of Appeals (IA042), Registrar, Victims' Counsel, transcripts
  EN/SQ, RED2 generations, three court-stamped reclassifications. No trial
  judgment and no public unredacted original were found in this capture
  (operator observation, not independently verified).
- `ksc-ingest gate`: 22/22 PASS (32–35 checks per record incl. MinIO object
  re-hash). Idempotent re-run: all record tables and objects byte-identical.
- Tracked metadata manifest `docs/ingestion/manifests/phase7-controlled-corpus.json`
  (`ksc-ingest export-corpus`, schema-validated by a unit test); no PDFs or
  captured pages in Git.
- New modules: `snapshot.py`, `capture_import.py`, `quality_gate.py`,
  `corpus_manifest.py`; tests
  +17 (15 unit, 2 integration). Docs: `CONTROLLED_CORPUS.md`,
  `OFFICIAL_SOURCES.md` (verified vs not yet verified), ADR-012.
- No admin UI (API + CLI status view); raw PCR DOM parser interface remains
  unfilled because no raw official PCR page is held.

## Completed features (Phase 8)

- Final closeout audit completed 2026-09-20: all nine Phase 8 acceptance
  criteria verified against implementation commit `9fc67c5`, final verified
  code/test baseline `02ab3c8`, migration `0004`, automated tests, live
  service/database probes, and the pinned controlled-corpus quality gate. The
  Phase 8 roadmap was marked COMPLETE before Phase 9 began.

- Migration `0004` adds parser provenance, exact PDF/source coordinate layers,
  numbered paragraphs, citation audit fields, and generated PostgreSQL FTS
  vectors with GIN indexes.
- The held-object parser processed all 22 controlled versions using native text:
  1,979 pages, 1,233 numbered paragraphs, 1,592 structural chunks, and 607
  transcript segments. No OCR was needed and no version requires review.
- Deterministic extraction persists exact raw references and source character
  spans. The resolver uses `record_identifiers` and held coordinates only;
  resolved, ambiguous, unresolved, and invalid are terminal persisted states.
- PostgreSQL search supports exact identifiers, phrases, keywords, document/date/
  party/language/source filters, transcript text, and exact reader target paths.
- The server-rendered Search and Document Reader routes now use the configured
  repository (`mock` or `api`); real mode does not render demo content panels.
- Real-corpus evaluation: `docs/ingestion/PHASE8_QUALITY_GATE.md` and the tracked
  `phase8-controlled-corpus-quality.json` report. No new documents were fetched.

## Completed features (Phase 9)

- Final closeout audit completed 2026-09-21 against implementation commits
  `431f1dd` and `ac59afa`, verified code/test baseline `548a151`, migration
  `0005`, all automated gates, live real-case API/database probes and the pinned
  controlled-corpus quality report.
- `ksc-ingest build-evidence` deterministically projects already-persisted Phase
  8 data only. The controlled graph has 13 document nodes and 22 exact-citation
  `CITED_IN` edges; one self-citation is omitted and zero analytical,
  unsupported, self, or citation-less edges were created.
- Relationship contracts carry source category, extraction origin, optional
  typed date, exact resolved target citation and exact citing-source coordinates.
  Evidence paths use bounded neutral BFS over eligible public source-backed
  edges; every hop is independently cited.
- The real timeline contains 19 source-record-backed events: 11 document dates,
  6 decisions/orders and 2 hearing/testimony dates. Date types and precision
  remain distinct; absent categories remain absent.
- Network, Evidence Path and Timeline use the API repository in real mode and
  suppress demo content. Network supports node search; source, verification,
  true from/to date, entity and relationship filters; inspectors;
  expand/collapse; isolate; reset; exact-source links; and a textual alternative.
- The required neutrality warning is unchanged. No person relationship,
  co-mention, guilt, responsibility, agreement, importance, or evidential weight
  is inferred.
- The measured graph is 13 nodes / 22 edges, so the accessible SVG renderer is
  retained. `docs/ingestion/PHASE9_QUALITY_GATE.md` records the PASS result.
- Final gates: 238 backend tests, 191 frontend tests, production build, lint,
  typecheck, migration round-trip/drift checks, real API smoke and Playwright
  (96 passed, 2 skipped) all pass.

## Completed features (Phase 10)

- Final closeout audit completed 2026-09-21 against implementation commit
  `c8eaa1e`, migration `0006`, automated gates, live real-case database/API/UI
  probes and the pinned controlled-corpus quality report.
- The 22-record corpus has no Trial Judgment. The real benchmark is explicitly
  Court decision `KSC-BC-2020-06/F03752`; no brief was substituted and no new
  material was ingested.
- One human-verified finding preserves exact paragraphs 12–16. One exact
  resolved Court-cited evidence link targets held version `F03667/COR/RED` with
  source coordinates and verification provenance.
- One Defence and one SPO position are stored separately as exact Court
  summaries; missing underlying filings F03743/F03746 remain explicit. One exact
  Court response is linked independently to both positions.
- The queryable matrix API and real Finding Detail provide structural navigation,
  exact-source opening, evidence categories and a source audit. No unsupported
  evidence link, AI-generated canonical finding, legal conclusion or score exists.
- Final gates: 238 backend tests, 194 frontend tests, production build, lint,
  typecheck, migration round-trip/drift checks, real-corpus gate, standard
  Playwright (96 passed / 4 skipped), and real-data Phase 10 Playwright (2 passed).

## Completed features (Phase 11)

- Final closeout audit completed 2026-09-21 against implementation commit
  `58ed7a8`, migration `0007`, automated gates, the rebuilt live stack, real
  API/UI probes and the pinned real-corpus AI quality report (ADR-016).
- Provider-neutral `AiProvider` protocol: deterministic extractive provider is
  the verified default; OpenAI-/Anthropic-compatible HTTP adapters are opt-in
  configuration. Prompts are immutable versioned files under
  `packages/prompts/`; the hash is persisted with every run.
- Every run persists a ranked, public-only retrieval snapshot with exact
  anchors, version hashes and verification state before generation; claims are
  linked to persisted sources; structured output, validation errors and tokens
  are audited. Repeated questions yield identical ranked snapshots and blocks.
- Deterministic validation rejects sources outside the whitelist, unmatched
  quotes, paraphrases, category conflation, evaluative language and free-form
  AI analysis; any failure withholds the whole answer. Missing Trial Judgment /
  filings abstain before generation.
- Real `/ai` and `/ai/{id}` show retrieved sources first, distinct record
  blocks, a provenance boundary, the AI block, citation status, run audit and
  exact-source links with no demo flag; saved output is an `ai_assisted`
  research note with run origin, never evidence.
- Final gates: 250 backend tests, 197 frontend tests, production build, lint,
  typecheck, migration round-trip/drift checks, real-corpus AI gate, standard
  Playwright (96 passed / 8 skipped), real-data Phase 11 Playwright (4 passed)
  and Phase 10 Playwright (2 passed).

## Completed features (Phase 12)

- Final closeout audit completed 2026-09-21 against implementation commit
  `7a9779b`, migration `0008`, automated gates, the rebuilt live stack, real
  API/UI probes and the pinned controlled-corpus appeal quality report
  (ADR-017).
- First-class neutral issue, exact issue-source, missing-material, statement
  comparison, red-team review/finding and issue-linked research-note models;
  Court treatment and human verification are explicit and no prohibited
  scoring/prediction field exists.
- One real `NEEDS_MORE_EVIDENCE` issue over F03752 paragraphs 12–16 has 5 exact
  human-verified source roles, 4 explicit missing sources, 3 red-team
  perspectives and an `insufficient_record` result. It asserts no legal error.
- One exact comparison links F03752 paragraph 12 and F03667/COR/RED page 160.
  It is `not_comparable` because the pre-correction brief is absent and makes no
  credibility inference.
- Real `/appeal`, `/appeal/argument/{id}` and statement-comparison routes show
  source-backed data, exact navigation, Court treatment, missing material,
  citation audit and all three red-team perspectives with no demo flag.
- Phase 11 remains the only AI retrieval/provider/validation path. AI-assisted
  reviews require an audited run; the real Phase 12 benchmark is human-reviewed
  and does not fill corpus gaps.
- Final gates: 255 backend tests, 199 frontend tests, production build, lint,
  typecheck, migration round-trip/drift checks, real-corpus appeal gate,
  standard Playwright (96 passed / 14 skipped) and real-data Phase 10–12
  Playwright (12 passed across desktop/mobile).

## Phase 13 result

- Migration `0009` adds immutable source-metadata snapshots, one acquisition
  queue row per public artifact version, explicit quarantine, and auditable
  processing runs. Existing SHA-addressed artifacts and version rows remain the
  evidence authority.
- Metadata-only official inventories are separate from local artifact state.
  Missing public versions can be leased in bounded batches with expiring locks,
  capped backoff and crash recovery. Cloudflare/access-control failures are
  terminal and appear in operator browser-capture plans; there is no bypass.
  An identified-HTTP adapter consumes bounded queue batches when robots and the
  official host permit it; future official API/export adapters share its
  contract.
- Parser output supports forced deterministic reconstruction; citation indexes
  and resolutions can be rebuilt separately. Serious hash/PDF/case/mapping
  conflicts stay quarantined; open-quarantine versions are excluded from parse
  and citation resolution, and the gate fails if one already holds parsed
  output.
- Ingestion status now exposes verified bytes, metadata-history count,
  duplicates, parser-review count, acquisition depth by state, open quarantine
  and processing runs. The Phase 13 machine gate verifies every object/hash,
  public-only and quarantine isolation, actual counts, and measured search,
  exact-lookup and network-query latency.
- API containers already run non-root. Phase 13 adds secure response headers,
  a declared-body request limit, weekly dependency updates for `apps/api`,
  `workers/ingestion`, pnpm and Actions, and guarded checksum-verified
  PostgreSQL/MinIO backup/restore tooling.
- A local operator-assisted browser collector (ADR-019) produced the second
  lawful capture `2026-09-21-corpus-02`: 40 public records selected, 39 accepted,
  1 refused and quarantined for review. The operator's own Chrome performed every
  official request and completed the Cloudflare check by hand; no access control
  was bypassed and two live-probe items remain `blocked_by_access_control`.
- Observability is complete (ADR-020): `/metrics` Prometheus exposition with
  request counters, latency histogram and corpus/queue/quarantine/parser/
  citation/AI gauges; structured JSON logs with request ids; alert rules in
  `ops/alerts/ksc-api.rules.yml`.
- Final real state: 62 source records · 56 documents · 61 versions (fetched,
  parsed) · 61 objects · 36,443,971 bytes · 2,832 pages · 2,019 paragraphs ·
  1,363 transcript segments · 15,730 citations (188 resolved · 3 ambiguous ·
  15,420 unresolved · 119 invalid) · 1 open quarantine · 1 parser review ·
  0 missing/hash-mismatched objects · 0 fetched non-public versions. A restore
  into an isolated database and bucket verified 61/61 objects at migration
  `0009`. The Phase 13 gate reports `completion_ready: true` at 61/50 accepted
  records; the Phase 10–12 gates pass against the combined pinned manifest.

## Phase 14 result

- Migration `0010` adds 5 tables in a separate external provenance domain:
  public source/publisher, media item, exact statement, verified court bridge
  and neutral comparison. It does not reuse a court document, evidence or AI
  category for internet material.
- The complete court-status taxonomy is enforced. `MENTIONED`, `TENDERED`,
  `ADMITTED`, `REJECTED`, `DISCUSSED` and `RELIED_UPON` require an exact
  citation and human verification; runtime reads also require resolution and a
  same-case citation. `EXTERNAL_ONLY` and `UNKNOWN` never imply evidence.
- A strict manual-URL manifest workflow stores only explicitly public HTTPS
  pages, short exact excerpts and metadata. It rejects credentials, local/non-
  global IPs, restricted access, timestamp inversions, hash changes, duplicates
  and unsafe status promotion. Collection and current exclusions are documented.
- The controlled set has 3 genuinely public pages from 2 publishers, 3 exact
  hash-verified statements and 1 human-reviewed `NOT COMPARABLE` comparison.
  All 3 items remain `EXTERNAL_ONLY`; no court link was invented and the court-
  bridge network has zero edges.
- Read-only API list/detail, comparison, external timeline and court-bridge
  network projections are case-scoped and fail closed. `/media` adds separate
  Court Record Only, External Public Sources and Both panels, status filtering,
  explicit source/status badges, original-source links and visible limitations.
- Phase 11 court-record RAG does not admit an external source category; a
  validation regression proves external material cannot become Court evidence.
  External-only material creates no appeal issue, red-team conclusion or hidden
  identity link.
- Final gate: 2 sources · 3 items · 3 statements · 3 external-only links · 1
  comparison · 0 invalid/citation-backed links · 0 duplicates · 0 manifest
  mismatches · 0 verification/access violations · 0 external court-RAG sources.
  Final verification: 283 backend, 204 frontend and 4 Phase 14 desktop/mobile
  Playwright tests pass; lint, typecheck, build, migration round-trip, drift,
  live readiness and API probes pass.

## Completed features (Phase 15)

- `docs/quality/REAL_DATA_ROUTE_AUDIT.md` classifies every normal production
  route. None is `MIXED` or `DEMO`; the unset/default source is the API, and
  categories without reviewed rows render honest empty states.
- Documents and Reader use real parsed Court data with exact coordinate and
  official-source navigation. Search keeps Court, External and Both modes
  separate. Findings retain the canonical detail text and concise list
  hierarchy. Network renders 48 readable nodes and 178 provenance-backed edges.
- The current structured / verified projections contain 0 Person, Witness,
  Exhibit and Claim records. This does not establish that the underlying public
  court record contains none. Production does not substitute demo or inferred
  records.
- Protected witnesses remain code-only, prior provenance and verification rules
  remain intact, and Court and External source domains remain separate.
- The approved homepage, Findings and Network hierarchy was checked after
  remediation. The homepage three-panel row and live ingestion summary were
  restored without a material design regression.
- Final recorded gates pass: lint/format, 283 backend tests, 236 frontend tests,
  strict typecheck, production build, 28/28 targeted frontend checks, and 38/38
  Phase 15 desktop/mobile Playwright checks.
- Implementation commits: `5470511` and `0c2c40d`; checkpoint: `e06455e`;
  completion date: 2026-09-22; annotated tag: `phase-15-complete`.

## Phase 16A implementation checkpoint

- Implementation commits: `fc217fc` (API/config authorization and AI controls)
  and `e9b7520` (deployment, recovery, CI/CD and review tooling).
- Added the single-host beta architecture (Caddy TLS edge, isolated web/API/
  Redis, one-shot migrations and operator worker, managed PostgreSQL/object
  storage), environment templates, immutable-image deployment workflow and
  production fail-fast validation. Production cannot select the demo case or
  mock frontend repository.
- Privileged AI/note/review/ingestion-status actions use least-privilege
  researcher/verifier/administrator bearer roles with Redis rate/concurrency
  controls. External AI requires explicit enablement, HTTPS allowlisting,
  server-only secrets, timeouts/retries, output and daily-run budgets.
- Added verified DB/object backup and guarded restore tooling, recovery metrics,
  Phase 13 alert extensions, k6/axe tooling, dependency/container scans,
  deployment/rollback/incident runbooks, ADR-022, performance/accessibility
  targets, a focused security checkpoint and an evidence-only Phase 16 gate.
- Added global EN/SQ independent-tool, public-source, external-source, network,
  AI, citation, legal-advice and telemetry disclosures.
- The lawyer/researcher beta protocol is prepared. No external participation is
  claimed; recruitment and observed feedback are an external dependency.
- This is implementation only. No staging/production deploy, restore drill,
  alert exercise, load run, manual accessibility/security review, production
  smoke, external beta, final Phase 16 gate, completion tag or Phase 17 work has
  occurred.

## Phase 16B verification checkpoint

- Production fail-fast validation, role-protected privileged routes, AI-disabled
  operation, redirect-safe external AI, request limits and reproducible compose/
  runtime images were verified. No authorized external target was deployed.
- The isolated database/object restore drill passed: migration `0010`, 57 public
  tables, 61 documents, 66 versions, 66 fetched versions and 61 objects matched;
  the restored state hash was `3be5769ccd20256441a3c06662a8c34d`. Non-empty
  restore was refused and all drill resources were removed.
- Dependency audits found no known high/critical issue; rebuilt API, web and
  worker runtime images each scanned with 0 high/critical findings. Readiness,
  metrics, request IDs, structured logs and all 17 Prometheus rules passed local
  checks; live alert routing and managed-service permissions remain pending.
- Automated accessibility passed 18/18 axe routes and 38/38 real-data desktop/
  mobile workflows. Manual keyboard, contrast and 200% zoom review remains.
- The single representative load gate completed 1,323 requests with 0.00% errors,
  p50 755.43 ms and p95 2.85 s; it failed the p95 <1 s target. At 10 VUs the web,
  API and PostgreSQL used about 64%, 119% and 39% CPU respectively.
- The evidence-only Phase 16 gate is **PENDING**: authorization, restore and
  supply-chain evidence pass; load fails; live deployment/alerts/security,
  manual accessibility and production smoke are pending. The prepared beta
  protocol has no real participant completion and remains an external dependency.
  Phase 16 is not complete and Phase 17 has not started.

## Phase 16 blocker-resolution checkpoint

- Targeted profiling isolated repeated read fan-out on home, finding detail and
  appeal. A 30-second server cache was added only to those read-only projections;
  the k6 gate now enforces the unchanged p95 <1 s target globally and per route.
- The final nine-route run passed: 5,940 requests, 0.00% errors, p50 75.18 ms,
  p95 467.66 ms; every route passed its own threshold (worst p95 732.08 ms).
- The focused manual application-security review passed with 0 critical, 0 high
  and 0 medium findings. Two accepted low risks are recorded in the security
  report; live managed-service grants/edge policy still require a real target.
- The manual keyboard, focus, command-dialog, contrast, 200%-equivalent reflow,
  desktop and representative-mobile review passed after fixing command-palette
  focus trapping and restoration. Existing axe/workflow evidence remains valid.
- No authorized staging/production target, alert receiver/provider credentials
  or managed-service credentials are configured. Deployment/HTTPS smoke, live
  alert delivery and managed DB/object-store IAM verification were not claimed.
- Phase 16 remains in progress. Its remaining external deployment/alerting gates
  are intentionally deferred until public deployment is desired; the unclaimed
  external beta is already documented as an external dependency. Phase 17 was
  explicitly authorized to proceed in parallel.

## Phase 17 Pass A checkpoint

- Declared scope: officially discovered public `KSC-BC-2020-06` records in EN/SQ;
  the report says “known public corpus indexed as of 2026-09-24” and makes no
  complete-corpus claim.
- A reproducible metadata-only report inventories all 62 official source rows
  and their detail/PDF URLs, version markers, acquisition, parse and index state.
  The held corpus is 56 documents / 61 fetched, parsed and indexed PDF versions,
  2,832 pages, 2,019 numbered paragraphs, 1,363 transcript segments and 15,730
  citations. One conflicting official record remains unmapped/unfetched for review.
- The structured audit records 0 People, Witness, Organization and Exhibit rows
  without treating zero as absence from the case. All 3 hearings, 1,363 transcript
  fragments, 54 events and 178 relationships pass their applicable source/version/
  coordinate provenance checks.
- The current inventory contains no genuinely new unheld record. A 75-record
  metadata-first operator discovery batch is recommended for the missing 2021–2024
  and document-type/language strata; acquisition remains fail-closed until that
  official inventory exists. No bulk download or access-control bypass occurred.
- Phase 17 remains in progress. Pass A does not close the phase or start Phase 18.

## Phase 17 Pass B checkpoint

- Official discovery produced 75 genuinely new candidates; 73 were accepted and
  2 Albanian transcripts were quarantined because page one had no open-session
  heading. The accepted EN 57 / SQ 16 batch spans 2021–2025, contains 50 filings
  and 23 transcripts, and adds 42,867,559 verified bytes.
- Excluding five historical/manual benchmark artifacts, the official corpus is
  now 135 source records, 116 documents and 134 fetched/parsed/indexed PDFs:
  79,311,530 bytes, 5,725 pages, 3,133 numbered paragraphs and 8,547 transcript
  segments. The bundle quality gate passed 73/73 with no acquisition failure.
- Deterministic structured rows moved from 3 to 16 hearings, 1,363 to 8,547
  statements, 54 to 127 events and 178 to 291 citation-backed relationships.
  People, witnesses, organizations and exhibits remain 0 because no approved
  reviewed projection exists; no identity or exhibit status was inferred.
- Citation states moved from resolved/ambiguous/unresolved/invalid
  188/3/15,420/119 to 306/3/16,831/141 after re-resolution. Migration `0011`
  widens official hearing session labels to 255 characters without truncation.
- Evidence: `docs/ingestion/PHASE17_PASS_B_COVERAGE.md`, the metadata-only
  `phase17-corpus-03.json` manifest and `phase17-pass-b-coverage.json` report.
  Phase 17 remains in progress; no further batch or later phase has started.

## Phase 17 Pass C checkpoint

- Root cause of zero People/Witness/Organization/Exhibit rows was the absence
  of a reviewed projector and occurrence-provenance layer. APIs/UI already
  supported three categories; organizations lacked a read endpoint, and the
  resolver could extract but not target witness/exhibit identifiers.
- Migration `0012` adds exact entity occurrences and explicit exhibit status.
  Existing-corpus projection now contains 48 people, 201 protected code-only
  witnesses, 6 organizations and 981 exhibits backed by 15,024 occurrences.
  Four occurrences on one surname-only person are review-required; there are
  zero provenance, protected-identity or exhibit-status violations.
- Hearings/statements/events remain 16/8,547/127. Exact citation-backed
  relationships are now 10,380. The single safe re-resolution changed citation
  states from 306/3/16,831/141 to 10,395/3/6,742/141
  (resolved/ambiguous/unresolved/invalid).
- Real API checks returned all four structured directories, organizations,
  search results, timeline and network data. Web pagination now follows the
  API total instead of truncating large directories at 200.
- `docs/ingestion/phase17c-structured-quality-gate.json` is PASS. No record was
  acquired; at this checkpoint Phase 17 remained in progress and Phase 18 had
  not started.

## Phase 17 completion audit

- Completed 2026-09-24 against the declared known officially discovered public
  `KSC-BC-2020-06` EN/SQ scope; no complete/exhaustive corpus claim is made.
- All 11 mandatory closeout checks pass from recorded evidence: lawful/public
  acquisition, artifact/version/language/quarantine integrity, 134/134 parsing
  and indexing, exact provenance, protected-witness safety, fail-closed exhibit
  status and citations, real app delivery, resumable/incremental ingestion, and
  reconciliation.
- Final counts: 135 source records, 116 documents, 134 PDFs, 79,311,530 bytes,
  5,725 pages, 3,133 paragraphs and 8,547 transcript segments; 48 people, 201
  protected code-only witnesses, 6 organizations, 981 exhibits, 16 hearings,
  8,547 statements, 127 events and 10,380 relationships.
- Of 15,024 exact occurrences, 15,020 are provenance-verified. The four
  surname-only `Smith` occurrences remain review-required and unmerged. There
  are zero provenance, protected-identity and invalid-exhibit-status violations.
- Citation states are 10,395 resolved, 3 ambiguous, 6,742 unresolved and 141
  invalid. Ambiguous and unresolved references remain targetless/fail-closed.
- Recorded quality evidence: backend 303 passed, frontend 239 passed, lint and
  strict typecheck passed, migration round-trip passed, and Alembic drift check
  passed. Phase 18 is NEXT / PENDING and has not started.

## Phase 18 Pass A checkpoint

- Implementation commit: `5733533` (`feat(web): refine real-data research
experience`).
- Audited Homepage, Search, Documents/Reader, People, Witnesses, Exhibits,
  Findings, Network and Timeline against the approved design and real Phase 17
  baseline. Actionable remaining gaps are recorded in
  `docs/PHASE18_PASS_A_UX_AUDIT.md`.
- Homepage now presents meaningful corpus measures: 116 documents, 5,725 parsed
  pages, 8,547 transcript segments, 48 people, 201 witness codes, 981 exhibits
  and 10,395 resolved citations, plus explicit research paths and date-ordered
  recent documents.
- People and witness directories preserve separate document, transcript and
  relationship counts. Detail views expose source-backed activity paths;
  protected witnesses remain code-only. No hearing count is inferred because
  the current witness API does not expose one.
- Exhibits display their explicit status; `UNKNOWN` is a neutral uncertainty
  notice and never implies admitted, rejected or tendered. Finding summaries are
  clamped in list rows, and search results distinguish what/where/source.
- Network exploration now renders a bounded selected-node neighbourhood rather
  than attempting all 10,380 relationships, uses readable labels, live counts
  and exact provenance, and no longer overlaps subset nodes using whole-graph
  coordinates. Timeline uses a readable chronological real-event list.
- Dense tables become stacked cards below 860px. Live visual checks passed at
  1440px, 1024px and Pixel 7 widths for the high-priority routes. The local
  Docker API/web images were rebuilt from migration `0012` and are healthy.
- Focused Phase 18/frontend/data/i18n tests pass (36/36); the complete frontend
  suite also passed earlier in this pass (239/239). Next production build passed.
  Phase 18 is not complete and Phase 18B has not started.

## Technical debt / notes

- `next/font/google` fetches fonts at build time; builds need network access.
- Playwright e2e passes locally (Chromium only; mobile project uses Pixel 7) but is not in CI.
- Albanian strings are provisional pending review against official KSC texts.
- `eslint` pinned to 9.x: `eslint-config-next@16.3.5` → `eslint-plugin-react@7`
  is incompatible with ESLint 10.
- MinIO images pulled from `quay.io/minio/*` (Docker Hub pull was denied).
- Web/API healthchecks use `127.0.0.1` (busybox `wget` resolves `localhost` to ::1).
- Container image sizes: api 364 MB, web 296 MB (not yet optimised).

## Known parser / data issues

- The controlled corpus produced no naturally ambiguous citation. The state is
  exercised with an overlapping-transcript fixture and always remains targetless.
- Native-text parsing is deliberately conservative. Unrecognized structures stay
  as page chunks; speaker, line, paragraph, and printed-page coordinates are never
  inferred. OCR is not implemented because none of the 22 inputs requires it.
- Citation extraction is intentionally broad and preserves 14,105 syntactically
  valid references as unresolved; corpus expansion, not fuzzy matching, may resolve
  them in Phase 13.

## Test / evaluation status

| Suite                          | Count        | Last result                                              |
| ------------------------------ | ------------ | -------------------------------------------------------- |
| Backend (pytest)               | 303          | pass                                                     |
| Frontend (vitest)              | 239          | pass                                                     |
| E2E (playwright)               | Phase 16     | 38/38 workflows; 18/18 axe routes pass desktop/mobile    |
| Targeted frontend verification | Phase 15     | 28/28 pass                                               |
| Evaluation                     | 3 real items | Phase 14 controlled real-public-source quality gate PASS |

Lint/typecheck: ruff, ruff format, mypy --strict, eslint, tsc, prettier — all pass.

## Deployment state

Local stack verified 2026-09-22 with all five services healthy, live database
at migration `0010`, and the real `/media` API/UI active. Git:
Phase 6 tag `phase-6-complete` = `bdf7293`. Phase 5B is on `feat/phase-5b-visual-parity`, tag
`phase-5b-complete`, not pushed. Phase 5B and Phase 7 were
fast-forwarded into `main` on 2026-09-20: `main` = `origin/main` = `96e402a`,
tags `phase-5b-complete` and `phase-7-complete` pushed. No remote deployment
or production workflow. Phase 10 is complete on
`feat/phase-10-judgment-findings-matrix`, local tag `phase-10-complete`. Phase
11 is complete on `feat/phase-11-citation-first-ai-rag`; local tag
`phase-11-complete` marks its final documentation checkpoint. On 2026-09-21 `main` was fast-forwarded to
`277686b` (Phase 11 closeout) and pushed with tag `phase-11-complete`;
Phase 12 was completed, fast-forwarded to `main`, pushed, and tagged
`phase-12-complete`. Phase 13 was fast-forwarded to `main` and pushed at
`d00e7bf`; its feature branch and annotated `phase-13-complete` tag were also
pushed. Phase 14 was fast-forwarded to `main` and pushed through roadmap commit
`efc4ee3`; its feature branch and annotated `phase-14-complete` tag at
`5717d24` were pushed. Phase 15 was fast-forwarded to `main` and pushed at
`01cb693`; its feature branch and annotated `phase-15-complete` tag were also
pushed. Phase 16 branch `feat/phase-16-production-readiness-security-beta`
starts from `01cb693` and currently ends at local blocker-resolution commit
`eb01a87`; it has not been deployed or pushed. Phase 17 branch
`feat/phase-17-corpus-expansion-structured-data` starts from `eb01a87`, retaining
the useful Phase 16 fixes. Phase 17 implementation runs through `0e382b3` on
that branch. Phase 17 was closed on 2026-09-24 without merging to `main`;
annotated tag `phase-17-complete` marks the closeout commit.

## Verification limitations

`docs/design/DESIGN_SYSTEM.md`, `ROUTE_MAP.md`, `PAGE_SPECS.md` were re-transcribed
from a verbatim read after an accidental formatter pass; structurally verified
(line counts, sections, fences, spec fields) but not byte-verified because no
original copy exists locally. See MEMORY.md → Current Problems.

## Ingestion state

Real case `KSC-BC-2020-06` (bundle `2026-09-20-corpus-01`): source records 22 ·
documents 19 · versions 22 (fetched 22 · parsed 22 · not_fetched 0 · failed 0) ·
hearings 2 · transcripts 3 · MinIO objects 22 · indexed documents 19 · pages
1,979 · paragraphs 1,233 · chunks 1,592 · transcript segments 607 · citations
14,212 (30 resolved · 0 ambiguous · 14,105 unresolved · 77 invalid) · failed 0.
Bytes came from the operator's browser downloads matched by SHA-256; the
pipeline itself fetched nothing from the court site (ADR-011).

Phase 13 final: 62 immutable source snapshots · 61 verified objects ·
36,443,971 bytes · 0 missing/hash-mismatched objects · 0 fetched non-public
versions · 1 open quarantine (nothing stored for it) · 6 processing runs ·
local measured search/exact/network queries all below 1.2 ms. Forced reparse,
re-resolution and the corpus-02 ingestion left every authoritative Phase 9–12
row unchanged; the Phase 9 deterministic projection was rebuilt to 48 nodes /
178 edges / 54 events. Bundle manifests: `manifests/phase13-corpus-02.json`
and the combined `manifests/phase13-controlled-corpus.json`.

Phase 17 Pass B official-case scope: 135 immutable source records · 116 logical
documents · 134 verified/parsed/indexed PDFs · 79,311,530 bytes · 5,725 pages ·
3,133 numbered paragraphs · 8,547 transcript segments · 17,281 citations
(306 resolved · 3 ambiguous · 16,831 unresolved · 141 invalid). Batch 03 added
73 accepted records; 2 remain quarantined and unpersisted.

Phase 9 projection: graph nodes 13 · citation-backed edges 22 · source-backed
timeline events 19 (document 11 · decision 6 · testimony 2). No additional
record was ingested.

Phase 10 projection: findings 1 · exact paragraph mappings 1 · explicit
Court-cited evidence links 1 · party positions 2 (Defence 1 · SPO 1) · Court
response links 2 · human-verified relationships 6. All five distinct linked
citations resolve; missing underlying filings F03743/F03746 and the absent Trial
Judgment remain explicit. No additional record was ingested.

Phase 11 audit: the deterministic gate creates four audited `ai_runs` per
invocation; closeout smoke checks added further audited runs and one
`ai_assisted` research note. Findings, evidence links, arguments, documents,
versions, citations and verification states are unchanged. No additional
record was ingested and no embedding exists.

Phase 12 projection: appeal issues 1 · issue-source links 5 · missing-material
rows 4 · statement comparisons 1 · red-team reviews 1 · red-team findings 4 ·
distinct exact citations 7/7 resolved and navigable · human-verified Phase 12
relationships 10 · incomplete-record abstentions 1. The canonical finding and
finding-evidence fingerprint is unchanged. No additional record was ingested.

Phase 14 external layer: 2 verified public publishers/sources · 3 public media
items · 3 exact statements · 3 `EXTERNAL_ONLY` status rows · 1 neutral
comparison · 0 citation-backed/invalid court links · 0 court-bridge edges · 0
duplicates, manifest mismatches, verification violations or access violations.
The external items do not enter the Phase 11 court-record retrieval table.
