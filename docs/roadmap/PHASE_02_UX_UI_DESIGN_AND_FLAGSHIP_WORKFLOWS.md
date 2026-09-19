# Phase 2 — UX/UI Design System & Flagship Workflows

**Status:** Historically completed through Claude Design.

## Goal

Turn the evidence/safety architecture into a coherent professional research interface before engineering begins.

The design must demonstrate how users will inspect sources, move between entities, distinguish source material from analysis, and understand dense legal information without losing provenance.

## Design philosophy

The application is a research workspace, not a marketing dashboard and not a generic chatbot.

The design should feel:

- serious;
- evidence-first;
- dense but readable;
- appropriate for legal research;
- neutral;
- auditable;
- usable in both English and Albanian;
- responsive without sacrificing desktop research density.

## Design system requirements

Define:

- dark research surfaces;
- light reading/public surfaces;
- typography hierarchy;
- spacing scale;
- border/radius rules;
- source-category badges;
- verification badges;
- citation chips;
- AI-specific visual treatment;
- warning/disclaimer patterns;
- tables/filters;
- side rails;
- mobile drawers/bottom sheets;
- loading, empty, and error states.

Record material and AI analysis must never be visually indistinguishable.

## Primary navigation model

Design around routes/workspaces such as:

- Overview;
- People;
- Witnesses;
- Documents;
- Exhibits;
- Incidents;
- Timeline;
- Network;
- Judgment;
- Findings;
- Appeal;
- AI Research;
- Search;
- Public/Simple Mode.

Support EN/SQ switching.

## Flagship screen designs

### Home / Overview

Include:

- case context;
- global search;
- navigation to major research modes;
- data-status/demo indicators;
- recent or representative activity;
- clear distinction between demo statistics and future real counts.

### Global Search / Command Search

Support grouped result types:

- people;
- witness codes;
- documents;
- transcripts;
- exhibits;
- incidents;
- findings;
- locations.

Design both full-page search and `CMD/CTRL+K` quick search.

### Network Explorer

Three-column research layout where appropriate:

- graph/search/filter controls;
- graph canvas;
- node/edge inspector.

Every edge should expose “Why does this connection exist?” with source citation.

### Evidence Path

Design a numbered hop chain where every hop is independently cited.

Permanent warning:

> These records reference one another. That is all a path shows.

Include “What a path cannot tell you.”

### Document Reader

Three-column desktop experience:

- left: metadata, versions, structure, page navigation;
- center: reading surface;
- right: research context, mentions, findings, citations, AI analysis.

Citation interaction should open exact source context.

### Transcript Viewer

Support:

- transcript page;
- line numbers;
- speaker;
- witness code/public identity where lawful;
- examination phase;
- line selection/citation creation.

### Person Dossier

Design record-backed tabs/actions such as:

- overview;
- documents;
- testimony;
- exhibits;
- incidents;
- timeline;
- findings;
- arguments;
- network;
- review/research.

No guilt/suspicion scoring.

### Witness Dossier

Support both public and protected witness states.

Protected state must remain code-first and identity-safe.

### Statement Comparison

Compare:

- prior statement;
- trial testimony;
- cross-examination;
- other comparable source-backed statements.

Allowed analytical labels:

- Possible Contradiction;
- Qualification;
- Timeline Difference;
- Consistent;
- Not Comparable.

### Timeline

Visually distinguish:

- historical event date;
- document date;
- filing date;
- testimony date;
- decision date;
- judgment/appeal milestones.

### Judgment / Findings

The Finding Detail design should represent the core research chain:

```text
COURT FINDING
    ↓
EXACT JUDGMENT LOCATION
    ↓
EVIDENCE RELIED UPON
    ↓
WHAT EACH SOURCE SAYS
    ↓
OTHER RELEVANT MATERIAL
    ↓
SUPPORTING / CONTRARY / QUALIFYING
    ↓
DEFENCE POSITION
    ↓
SPO POSITION
    ↓
COURT RESPONSE
    ↓
POTENTIAL ISSUE FOR REVIEW
    ↓
RED TEAM
    ↓
SOURCE AUDIT
```

### Appeal Research

Design research categories without prediction:

- error of law;
- error of fact;
- sentencing;
- evidence assessment;
- procedural fairness;
- reasoning;
- mode of liability;
- other.

### Argument Lab / Red Team

Three analytical roles:

1. Defence Analyst;
2. SPO Red Team;
3. Neutral Reviewer.

Every material statement should be citation-aware.

### AI Research

A research workspace, not a generic chat interface.

Show:

- question;
- structured response;
- source categories;
- sources used;
- retrieved documents;
- citation status;
- verification status;
- actions to open sources or continue research.

### Public / Simple Mode

Allow ordinary users to answer:

- What did the Court decide?
- Who testified?
- What evidence was used?
- What happened when?
- How are public records connected?
- Where is the source?

Use plain explanations without weakening citations.

## Mobile requirements

At minimum design mobile states for:

- home/search;
- document reader;
- network;
- finding detail;
- witness;
- AI research.

Network mobile should preserve a useful graph viewport with a bottom-sheet/compact inspector.

## Out of scope

- production code;
- real data;
- scraping;
- final database schema;
- AI calls.

## Deliverables

Design package under `docs/design/`, ultimately including visual artifact and written handoff specs.

## Acceptance criteria

- core workflows are represented;
- evidence/AI distinction is visually explicit;
- protected witness state is designed;
- citations are first-class UI elements;
- network neutrality is clear;
- desktop and mobile patterns exist;
- EN/SQ is accounted for;
- major legal-research workflows are designable without inventing unsafe semantics.

## Stop condition

Do not start engineering until the design can be handed off as written specifications plus visual reference.

## Completion report

```text
PHASE 2 STATUS
DESIGN SYSTEM
SCREENS
WORKFLOWS
MOBILE
PROVENANCE DESIGN
SAFETY DESIGN
GAPS
NEXT
```
