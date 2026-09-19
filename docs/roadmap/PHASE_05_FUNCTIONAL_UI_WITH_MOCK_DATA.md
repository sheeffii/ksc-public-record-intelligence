# Phase 5 — Functional Approved UI with Mock Data

**Status:** Functionally completed. A later design audit found significant visual-parity debt; see Phase 5B.

## Goal

Implement all approved product routes and research workflows as a working frontend using typed, centralized **demo/mock data only**.

The purpose is to prove interaction architecture, domain contracts, citation/provenance presentation, responsive behavior, and screen-to-screen navigation before real KSC data enters the application.

## Why mock data is intentional

At this stage real KSC material has not yet been:

- discovered through a controlled pipeline;
- versioned;
- hashed;
- parsed;
- citation-resolved;
- mapped into a real evidence schema.

Using mock data lets engineering validate the UI contract without conflating UI bugs with parser/schema/provenance bugs.

Mock data must be obviously demo data and should not invent sensational allegations against real people.

## Mock repository architecture

Do not hard-code demo objects inside every page.

Use typed repository/domain interfaces so the frontend can later switch:

```text
MockRepository
      ↓
      UI
```

into:

```text
ApiRepository
      ↓
     API
      ↓
 PostgreSQL
```

without rewriting every screen.

## Provenance primitives

Implement and use consistently:

- `RecordBlock`;
- `AiAnalysisBlock`;
- `SourceBadge`;
- `VerificationBadge`;
- `CitationChip`;
- `ProvenanceBoundary`.

Record evidence and AI analysis must be visually distinct.

## Required screens / routes

Implement purpose-built screens for the approved route map, including:

- Overview/Home;
- Global Search;
- command search overlay;
- People directory;
- Person Dossier;
- Witnesses directory;
- Witness Dossier;
- Statement Comparison;
- Documents/Evidence Explorer;
- Document Reader;
- Transcript Viewer;
- Exhibits;
- Incident Detail;
- Timeline;
- Network Explorer;
- node/edge inspector;
- Find Record Connection;
- Evidence Path;
- Judgment Reader;
- Findings directory;
- Finding Detail;
- Appeal Research;
- Argument Lab;
- Red Team;
- AI Research;
- Public/Simple Mode;
- representative mobile states.

## Search

Support mock grouped results by:

- person;
- witness;
- document;
- transcript;
- exhibit;
- incident/location;
- finding.

Support `CMD/CTRL+K` quick search.

## Protected witnesses

Demonstrate both:

- public witness identity;
- protected witness code-only state.

Never invent identity.

## Statement comparison

Allowed demo labels:

- Possible Contradiction;
- Qualification;
- Timeline Difference;
- Consistent;
- Not Comparable.

No liar/dishonest label and no credibility percentage.

## Document / transcript reading

Document Reader should demonstrate:

- light reading surface;
- metadata/versions/structure;
- highlighted passage;
- context rail;
- citations;
- finding links.

Transcript Viewer should demonstrate:

- page/line structure;
- speakers;
- witness code;
- examination type;
- line selection/citation actions.

## Network / Evidence Path

Use mock graph data with source-backed relationships.

Network features may include:

- search;
- pan/zoom;
- isolate;
- expand/collapse;
- node inspector;
- edge inspector;
- textual accessibility alternative.

Evidence Path must show independently cited hops and the neutrality disclaimer.

## Finding Detail

Represent the approved chain:

```text
Court Finding
→ Judgment location
→ Evidence relied upon
→ Source summaries
→ Supporting / contrary / qualifying material
→ Defence argument
→ SPO argument
→ Court response
→ Potential Issue for Review
→ Red Team
→ Source Audit
```

## Appeal / AI research

Use mock analysis only.

Never show:

- probability of appeal success;
- guilt score;
- suspicion score;
- witness credibility score.

## EN/SQ

All Phase 5 UI should use centralized translation infrastructure.

Albanian legal terminology may remain provisional until checked against official usage.

## Testing

Maintain prior tests and add:

- provenance boundaries;
- protected-witness safety;
- unresolved citation fail-closed behavior;
- route navigation;
- mock repository validation;
- EN/SQ parity;
- network/evidence-path disclaimer;
- absence of prohibited scores;
- major Playwright workflows.

## Known result from design audit

The implementation is functionally complete but visually simplified on many screens. This is not a schema/data failure. It is handled in **Phase 5B**.

## Acceptance criteria

Functional Phase 5 is complete when:

- all approved routes have purpose-built screens;
- mock data is centralized/typed;
- EN/SQ works;
- provenance is consistent;
- protected witness handling is safe;
- Network/Evidence Path work with mock data;
- Finding/Appeal/AI workflows exist;
- mobile representative states work;
- tests/lint/typecheck/build pass.

Visual parity is **not** considered complete until Phase 5B.

## Stop condition

Do not connect real KSC sources or AI providers.

## Completion report

```text
PHASE 5 STATUS
SCREENS IMPLEMENTED
FUNCTIONAL WORKFLOWS
WORKING
TESTS
ACCESSIBILITY
KNOWN DIFFERENCES
COMMITS
NEXT
MEMORY
```
