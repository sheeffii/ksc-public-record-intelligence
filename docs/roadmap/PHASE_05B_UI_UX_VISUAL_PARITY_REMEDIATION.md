# Phase 5B — UI/UX Visual Parity Remediation

**Status:** Complete.

**Completed:** 2026-09-20.

**Completion commit:** `eaeb4ce`.

**Completion tag:** `phase-5b-complete`.

**Historical sequence requirement:** Execute after Phase 6 and before Phase 7;
this ordering was satisfied.

## Goal

Bring the functioning Phase 5 frontend much closer to the approved Claude Design artifact **page-by-page**, without changing the evidence architecture or introducing real KSC data.

Phase 5 proved that routes and workflows work. Phase 5B proves that the implementation actually reflects the intended product design.

## Why this phase was added

A detailed audit of `docs/design/Design.html` found that the previous implementation matched the design system and safety architecture, but several pages were substantially simplified.

Tests were primarily functional and did not establish screenshot-level design parity.

## Design source of truth

Read all of:

```text
docs/design/DESIGN_SYSTEM.md
docs/design/PAGE_SPECS.md
docs/design/COMPONENTS.md
docs/design/UX_FLOWS.md
docs/design/DESIGN_DECISIONS.md
docs/design/ROUTE_MAP.md
docs/design/HANDOFF.md
docs/design/Design.html
```

Do not alter design files merely to make implementation appear correct.

## Known gaps to remediate

### Home

Current concept is correct but less dense than the approved design.

Remediate:

- hierarchy;
- research status/summary areas;
- navigation cards;
- spacing/density;
- demo-data presentation;
- responsive composition.

### Network

Current three-column concept is present, but graph/tools are simplified.

Remediate:

- toolbar/control density;
- filters;
- inspector composition;
- graph viewport;
- mobile inspector behavior;
- source/relationship detail;
- visual emphasis on provenance.

Do not prematurely rewrite graph engine solely for parity. Engine choice can remain deferred until real-data scale is known.

### Document Reader

Remediate:

- designed toolbar;
- document navigation depth;
- metadata/TOC/versions rail;
- context rail;
- citation interaction;
- responsive header crowding;
- mobile collapsible research context.

### Finding Detail

The logical chain exists, but composition/density differ.

Remediate:

- section rhythm;
- evidence grouping;
- argument/court-response presentation;
- source audit;
- tabs/mobile stacking;
- exact hierarchy from design.

### Search

Major remediation required:

- denser grouped results;
- category controls;
- query tools;
- filters that actually affect results;
- result metadata/citations;
- command-overlay parity.

### Person Dossier

Rebuild missing dossier structure from design:

- summary/header;
- tabs;
- actions;
- record counts/status;
- findings/testimony/documents/incidents/network sections;
- relevant side panels.

### Witness Dossier

Preserve protected-witness safety while adding:

- designed header;
- testimony/cross/prior statement sections;
- exhibits/findings/timeline/network/research composition;
- public/protected variants.

### Statement Comparison

Add missing:

- comparison rail;
- context;
- source metadata;
- human-review workflow;
- verification state;
- navigation among comparison items.

### Evidence Explorer / directory routes

Current implementation is too sparse.

Add:

- dense table workspace;
- preview/details area where designed;
- functioning filter/sort/density controls;
- export control behavior if in scope;
- search;
- proper pagination/demo data volume.

### Incident Detail

Restore designed:

- header/context;
- controls;
- evidence matrix;
- timeline/source context;
- navigation.

### Timeline

Current list must become the designed layered interactive timeline.

Represent distinct layers/types:

- historical events;
- documents;
- filings;
- testimony;
- decisions;
- judgment/appeal milestones.

Dates must remain semantically distinct.

### Appeal Research

Add missing:

- issue coverage;
- category navigation;
- review panels;
- source links;
- human-review status;
- party/court positions.

No predictive scores.

### Argument Lab / Red Team

Expand from basic stages into designed workflow:

- argument editor;
- research support;
- contrary evidence;
- citation checks;
- party/court response lookups;
- Defence Analyst;
- SPO Red Team;
- Neutral Reviewer;
- unsupported-assertion/missing-citation panels.

### AI Research

Retain strong provenance separation but add designed:

- source rail;
- retrieved-documents workflow;
- citation status;
- open-all-sources;
- save note/create argument;
- richer research layout.

### Public Mode

Build dedicated public composition rather than a thin variant of research mode.

Include:

- dedicated public navigation/mode switch;
- plain-language explanation;
- topic routes with differentiated content;
- preserved source links/citations.

### Evidence Path

Add:

- path controls;
- alternate-path context;
- stronger per-hop source detail;
- verification/date presentation;
- “What a path cannot tell you.”

## Mobile remediation

At minimum fix:

- Network inspector covering too much of graph;
- Document Reader header/breadcrumb/demo controls;
- Finding Detail tab overflow and stacking;
- dense table patterns;
- AI research side panels;
- witness dossier navigation.

## Interaction remediation

Make visually present controls functional where feasible:

- directory filters;
- sorting;
- density;
- search filters;
- export/demo export if specified;
- tabs;
- panel toggles;
- path controls.

## Visual verification workflow

For each authoritative screen:

```text
Read design spec
   ↓
Open Design.html reference
   ↓
Render current app state
   ↓
Capture screenshot
   ↓
Compare hierarchy/layout/spacing/components
   ↓
Fix
   ↓
Re-test
```

Use Playwright screenshot/visual-regression tooling if practical.

Do not rely only on route/DOM tests.

## Accessibility

Visual parity must not regress:

- keyboard navigation;
- focus indicators;
- semantic headings;
- table semantics;
- accessible dialogs/drawers;
- non-color-only status;
- reduced motion;
- graph textual alternative.

## Out of scope

- real KSC ingestion;
- schema redesign;
- AI provider calls;
- actual legal analysis;
- bulk corpus loading.

## Acceptance criteria

Phase 5B is complete only when:

- each authoritative screen has been compared directly against design;
- major known gaps are remediated;
- mobile states are materially closer to design;
- search/directory controls actually work;
- timeline is no longer a basic list;
- public mode has a dedicated composition;
- screenshots/visual checks exist for representative screens;
- all prior functional tests remain green;
- lint/typecheck/build pass;
- design docs remain unchanged.

## Stop condition

Stop before Phase 7. Do not start real ingestion.

## Completion report

```text
PHASE 5B STATUS
SCREENS REMEDIATED
DESIGN MATCH
MOBILE
INTERACTIONS
VISUAL TESTS
FUNCTIONAL TESTS
KNOWN DIFFERENCES
COMMITS
NEXT
MEMORY
```
