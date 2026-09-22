# Phase 15 — Real Data UI Completion & Demo Removal

**Status:** Pending. Execute only after Phase 14 is complete or formally deferred.

## Goal

Convert every normal production-facing route from Phase 5 mock/demo data to real, provenance-backed API data.

```text
REAL DATABASE
    ↓
REAL API
    ↓
REAL UI
    ↓
EXACT SOURCE
```

After this phase, production routes must never silently display synthetic records.

## Core rule

```text
PRODUCTION ROUTE
→ REAL DATA OR HONEST EMPTY STATE

DEMO DATA
→ DEV / TEST / STORY / EXPLICIT DEMO ONLY
```

Never use demo data as a fallback when a real API returns no records.

## Route audit

Audit every route and classify it as:

- `REAL`;
- `MIXED`;
- `DEMO`;
- `EMPTY / NOT IMPLEMENTED`.

At minimum audit:

- Documents;
- Document Reader;
- People / Person Detail;
- Witnesses / Witness Detail;
- Evidence / Exhibits;
- Incidents / Incident Detail;
- Findings / Finding Detail;
- Network / Evidence Path;
- Timeline;
- Search;
- AI Research;
- Appeal Research;
- Argument Lab / Red Team;
- Statement Comparison;
- External Sources / Media Detail / Public Statements;
- mobile and public/simple-mode routes.

Create a tracked report such as:

`docs/quality/REAL_DATA_ROUTE_AUDIT.md`

## Remove production demo fallbacks

Production mode must not show synthetic identifiers/content such as:

- `demo-person-*`;
- `Demo record *`;
- `F-DEMO-*`;
- sample document IDs/content;
- sample findings;
- sample linked records.

Do not merely hide the `DEMO DATA` badge. Remove the demo source from normal execution.

## Environment/data mode

Use the repository's existing data-mode mechanism or add a clear one, for example:

```text
APP_DATA_MODE=real
APP_DATA_MODE=demo
```

Production/default must be `real`.

Demo fixtures may remain for tests, visual QA, stories, or explicit demo routes.

## Documents

Use real `Document` / `DocumentVersion` data:

- official reference;
- title;
- type;
- party;
- chamber/court level;
- language;
- public state;
- version;
- date;
- page count;
- parsing state;
- verification state;
- official URLs;
- artifact status;
- exact-source navigation.

## Real Document Reader

Replace sample reader text with parsed real source content.

Preserve exact coordinate layers:

- PDF index;
- printed/source page;
- paragraph;
- transcript page;
- transcript line;
- citation target.

Do not invent paragraph or line numbers.

Provide:

- page navigation;
- deep links;
- provenance;
- citation chips;
- official-source link;
- version state;
- parsed-content state;
- AI analysis clearly separated from source text.

If parsing is unavailable/review-required, show an honest state.

## People / entities

People screens must use real source-backed entity records only.

Show where available:

- name;
- public role;
- aliases;
- document/transcript mentions;
- relationships;
- verification state;
- source audit.

Do not create a person only from an unverified name heuristic.

## Witnesses / privacy

- Preserve protected witness codes.
- Do not infer private identities.
- Do not link a witness code to a real name unless the official public record does so.
- Do not use facial or voice recognition.

## Evidence / exhibits / incidents

Use real source-backed records only.

Distinguish:

- court document;
- exhibit;
- testimony;
- external item;
- court finding;
- party argument;
- human research note.

Corpus presence does not imply admission or Court reliance.

Do not infer incidents from keyword proximity alone.

## Findings

Use the real Phase 10 finding model.

Every real finding must be labelled `COURT FINDING` and navigate to exact source coordinates.

Never promote AI summaries, party arguments or external statements to findings.

## Network / Timeline

Use the real Phase 9 APIs only.

Every edge/event must preserve provenance and verification state.

Network connection does not imply guilt, wrongdoing, agreement or responsibility.

External events must remain distinguishable from court-record events.

## Search

Production search must use real indexes and keep source types separated:

- Court Record;
- External Public Source;
- Both — clearly separated.

Never silently merge external material into court-record results.

## Entity extraction / linking

If People/Witness screens require more real entities, implement the repository-approved source-backed extraction/linking pipeline.

Requirements:

- source occurrence;
- deterministic normalization;
- human review for ambiguity;
- no protected-identity inference;
- idempotent reprocessing;
- provenance.

## Exports

CSV/export must use real filtered records and preserve useful provenance/citation fields.

No demo IDs in production exports.

## Empty states

Correct empty states are preferred to synthetic content, for example:

- `No verified people have been linked to this record yet.`
- `No public court treatment has been located.`
- `This document has not yet been parsed.`

## Visual parity and mobile

Preserve the approved design system while switching data sources.

Verify desktop and mobile, especially:

- network inspector;
- reader;
- finding tabs;
- tables/filters;
- evidence path;
- AI citations;
- external-source badges.

## API

Complete any missing production APIs required by real routes.

Reuse existing domain models/repositories; do not create duplicate stacks.

Use pagination and avoid loading the full corpus into the browser.

## Real-data coverage report

For each production route track:

- API endpoint;
- real record count;
- remaining demo dependency;
- provenance support;
- desktop test;
- mobile test;
- status.

## Testing

Test at minimum:

- production mode contains no demo fixtures;
- route audit;
- real Documents + Reader;
- People/Witness real-data or honest empty states;
- Evidence/Exhibit separation;
- Findings exact-source navigation;
- Network real edges;
- Timeline real events;
- Search real results;
- AI/Appeal/External routes stay real;
- exports contain real IDs;
- mobile;
- empty states;
- previous Phase 8–14 regressions.

Run repository-standard backend/frontend/Playwright/lint/format/type/build gates.

## Real-data quality gate

Create a Phase 15 route-level gate with:

```text
route
data mode
API endpoint
real record count
demo dependency
source/provenance support
desktop test
mobile test
status
```

Completion requires zero unapproved demo dependencies on normal production routes.

## Acceptance criteria

Phase 15 is complete when:

- every normal production route is audited;
- all production routes use real APIs or honest empty states;
- demo/mock data is removed from normal production execution;
- Reader displays real parsed court material;
- People/Witness behavior is source-backed and privacy-safe;
- Findings/Network/Timeline/Search use real data;
- External/Court source boundaries remain intact;
- route-level real-data gate passes;
- desktop/mobile real-data Playwright passes;
- no prior provenance/verification rule is weakened.

## Stop condition

Do not begin production-readiness deployment until normal app usage is real-data complete.

## Completion report

```text
PHASE 15 STATUS
ROUTE AUDIT
DEMO REMOVAL
DOCUMENTS / READER
PEOPLE / WITNESSES
EVIDENCE / INCIDENTS
FINDINGS
NETWORK / TIMELINE
SEARCH
EXTERNAL SOURCES
API
REAL-DATA QUALITY GATE
DESKTOP / MOBILE
TESTS
KNOWN LIMITATIONS
COMMITS
TAG
NEXT
MEMORY
```
