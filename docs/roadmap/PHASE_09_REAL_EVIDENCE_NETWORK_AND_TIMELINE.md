# Phase 9 — Real Evidence Network & Timeline

**Status:** Pending.

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

- real graph data replaces demo graph for the controlled corpus;
- every edge can answer “why does this connection exist?”;
- Evidence Path uses only auditable hops;
- timeline is based on real structured dates;
- graph performance is acceptable;
- neutrality/safety wording remains intact;
- tests pass.

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
