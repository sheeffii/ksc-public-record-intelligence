# Phase 9 — Real Evidence Network & Timeline

**Status:** Complete.

**Completed:** 2026-09-21.

**Completion commit:** `548a151` (final verified code/test baseline; the
subsequent roadmap closeout commit records completion metadata).

**Completion tag:** `phase-9-complete`.

## Goal

Replace mock graph/timeline content with real, provenance-backed relationships and dates from the structured public record.

## Preconditions

Do not begin until:

- Phase 8 exact citations work;
- real document/transcript entities are queryable;
- relationships can carry provenance;
- date semantics are preserved.

## Relationship creation policy

A graph edge must be based on a source-backed relationship or clearly marked analytical extraction.

Production UI should prefer human/source-verified edges.

Each edge should support:

- subject;
- relationship type;
- object;
- source category;
- exact citation;
- verification state;
- extraction origin;
- date if relevant.

## Relationship types

Use the normalized vocabulary defined in the schema, e.g.:

- MENTIONED_IN;
- TESTIFIED_ABOUT;
- TESTIFIED_AT;
- CITED_IN;
- RELIES_ON;
- SUPPORTS;
- CONTRADICTS;
- QUALIFIES;
- RESPONDS_TO;
- LOCATED_AT;
- OCCURRED_AT;
- FILED_BY;
- CORROBORATED_BY;
- PRECEDES/FOLLOWS.

Do not create a broad “connected to” edge when a more precise sourced relation exists.

## Co-mention caution

`CO_MENTION` is structurally weak.

It should never be presented as evidence of association or wrongdoing.

Consider hiding it by default or labeling it clearly.

## Network Explorer

Switch the mock graph to real API data.

Required behavior:

- search node;
- filters;
- node inspector;
- edge inspector;
- source citation;
- expand/collapse;
- isolate;
- reset;
- textual alternative;
- evidence-path launch.

## Graph engine

Reassess the Phase 5 lightweight SVG implementation using actual graph size.

If real graph scale/performance requires it, migrate to Sigma.js + Graphology or equivalent WebGL stack.

Make the engine decision based on measured scale, not aesthetics alone.

## Evidence Path

Run pathfinding only over eligible source-backed edges.

Every hop must be independently cited.

Paths may be ordered by neutral criteria such as hop count, but never by guilt/importance.

Preserve warning:

> These records reference one another. That is all a path shows.

## Timeline

Populate real layered timeline categories:

- historical events/incidents;
- document dates;
- filing dates;
- hearing/testimony dates;
- decisions/orders;
- judgment milestones;
- later appeal milestones when present.

Do not collapse dates into one generic timestamp.

## Date uncertainty

Respect date precision:

- exact;
- approximate;
- range;
- month/year only;
- unknown.

UI must represent uncertainty rather than invent exact dates.

## Source controls

Allow filtering by:

- source type;
- verification state;
- date range;
- entity type;
- relationship type;
- public/redacted version if useful.

## Tests

Test:

- every graph edge has provenance;
- hidden/private/unknown visibility does not leak;
- evidence-path hops carry citations;
- path algorithm does not invent unsupported edges;
- timeline date types remain distinct;
- uncertain dates render correctly;
- large synthetic graph performance if needed;
- textual accessibility alternative.

## Acceptance criteria

- [x] real graph data replaces demo graph for the controlled corpus;
- [x] every edge can answer “why does this connection exist?”;
- [x] Evidence Path uses only auditable hops;
- [x] timeline is based on real structured dates;
- [x] graph performance is acceptable;
- [x] neutrality/safety wording remains intact;
- [x] tests pass.

## Stop condition

Do not yet build full Judgment/Evidence Matrix or AI analysis.

## Completion report

```text
PHASE 9 STATUS
REAL GRAPH
RELATIONSHIP PROVENANCE
EVIDENCE PATH
TIMELINE
GRAPH PERFORMANCE
ACCESSIBILITY
TESTS
KNOWN LIMITATIONS
COMMITS
NEXT
MEMORY
```

## Completion Record

- Closeout audit: **PASS**, 2026-09-21. Every requirement and acceptance
  criterion above was re-read and checked against migration `0005`, committed
  implementation, automated tests, the live real-case database/API, and the
  pinned controlled-corpus quality report.
- Real graph: 23 resolved citations inspected; one self-citation omitted; 13
  public document nodes and 22 deterministic `CITED_IN` edges created. Every
  edge has a resolved citation, exact persisted source occurrence, source
  category, verification state and extraction origin; zero analytical,
  unsupported, self, or citation-less edges were created.
- Evidence Path: bounded deterministic breadth-first search uses only public,
  resolved, non-rejected, non-analytical edges. Every returned hop carries its
  own target citation and exact citing-source coordinates. The required
  neutrality warning remains verbatim.
- Timeline: 19 source-record-backed events from persisted metadata — 11 document
  dates, 6 decisions/orders, and 2 testimony dates. All controlled-corpus dates
  are explicitly exact; UI tests verify approximate/range presentation without
  inventing dates. Categories absent from the corpus remain absent.
- UI/API: Network Explorer, Evidence Path and Timeline server-load the API in
  real mode. Search, source, verification, from/to date, entity and relationship
  controls, inspectors, expand/collapse, isolate, reset, exact-source links and
  textual alternative are present. Demo content is suppressed in real mode.
- Scale: measured at 13 nodes / 22 edges. The accessible SVG engine is retained;
  no synthetic large-graph test or WebGL dependency is warranted at this scale.
- Tests/gates: `make lint`, `make typecheck`, `make test`, `make build`, and
  `make e2e` passed: 238 backend, 191 frontend, and 96 Playwright checks passed
  (2 desktop-only mobile checks skipped by design). Migration round-trip/model
  drift and a real API smoke test passed at migration head `0005`.
- Scope: no additional court material was fetched, the corpus was not expanded,
  and no Phase 10 matrix or AI analysis was implemented.
- Evidence: `docs/ingestion/PHASE9_QUALITY_GATE.md` and
  `docs/ingestion/manifests/phase9-controlled-corpus-quality.json`.
