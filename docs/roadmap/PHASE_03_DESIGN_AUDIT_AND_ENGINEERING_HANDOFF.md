# Phase 3 — Design Completion, Audit & Engineering Handoff

**Status:** Historically completed.

## Goal

Convert the design into an engineering-ready package, audit it for missing workflows/safety issues, and create durable written specifications so later coding agents do not depend on screenshots or conversation memory.

## Required handoff package

The design package should live under:

```text
docs/design/
```

Expected files:

- `Design.html`
- `HANDOFF.md`
- `PAGE_SPECS.md`
- `ROUTE_MAP.md`
- `COMPONENTS.md`
- `DESIGN_SYSTEM.md`
- `UX_FLOWS.md`
- `DESIGN_DECISIONS.md`

These files are read-only source-of-truth references during implementation unless a deliberate design revision is authorized.

## Audit objectives

Check whether the design fully resolves:

- search → result → source;
- person/witness dossier navigation;
- document/transcript citation flow;
- finding → evidence → source audit;
- network node/edge inspection;
- record-connection/evidence-path workflow;
- timeline date semantics;
- appeal-research workflow;
- AI research source panel;
- public/simple mode;
- mobile network/reader/finding states;
- EN/SQ affordance;
- demo-data indicators;
- neutrality disclaimers;
- protected-witness handling.

## Evidence Path requirement

The design audit introduced/confirmed a dedicated Evidence Path view.

Every hop must independently show:

- relationship type;
- source;
- citation;
- verification state;
- date where applicable.

Alternate paths may be ordered by neutral structural properties such as hop count, but not by implied guilt/importance.

## Citation-resolution architecture observation

A key engineering decision should be carried forward:

> Citation references should be resolved and persisted during ingestion rather than rediscovered expensively on every request.

Future flow:

```text
Raw document
  ↓
Citation extraction
  ↓
Normalization
  ↓
Resolution
  ↓
Persisted resolution index
  ↓
Fast runtime lookup
```

This becomes an ADR in Phase 4 and schema foundation in Phase 6.

## Known non-blocking design gaps

The original design audit allowed engineering to begin even if some items remained:

- some directory pages reuse a common Evidence Explorer/DataTable pattern rather than unique artboards;
- Albanian legal terminology requires later review against official usage;
- additional mobile variants may be needed;
- formal accessibility audit remains future work;
- graph/timeline screen-reader semantics need engineering care.

## Engineering handoff rules

Coding agents must:

- read the written design files before implementing a screen;
- use `Design.html` as visual reference;
- avoid ad-hoc redesign;
- document necessary deviations;
- keep source categories distinct;
- preserve demo-data labeling until real data exists.

## Deliverables

- complete design package;
- route map;
- component inventory;
- page specifications;
- UX flows;
- design decisions;
- engineering handoff guidance;
- explicit citation-resolution observation.

## Acceptance criteria

- design files are organized and readable;
- major workflows resolve end-to-end;
- safety/neutrality constraints are represented;
- engineering can begin without depending on conversation memory;
- missing non-blocking work is documented.

## Stop condition

Stop after handoff is ready. Engineering begins in Phase 4.

## Completion report

```text
PHASE 3 STATUS
HANDOFF FILES
WORKFLOWS
AUDIT FIXES
KNOWN DESIGN GAPS
ENGINEERING DECISIONS TO CARRY FORWARD
NEXT
```
