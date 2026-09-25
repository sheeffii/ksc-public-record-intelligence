# Phase 21 — Design Parity & Research UX

**Status:** IN PROGRESS
**Current checkpoint:** 21A COMPLETE — stop before 21B
**Started:** 2026-09-25
**Branch:** `feat/phase-21-design-parity-research-ux`

## Objective

Bring the real KSC Public Record Intelligence application into close visual,
information-architecture and interaction parity with the approved
`docs/design/Design.html`, while preserving Phase 19 real data, Phase 20
source-native navigation and every evidence-integrity safeguard.

```text
APPROVED DESIGN.HTML + REAL PHASE 19 DATA + PHASE 20 SOURCE-NATIVE READER
```

`Design.html` is the primary visual reference. Illustrative values in the
design are never production data.

## Permanent constraints

- Use live database/API values. Never copy prototype names, identifiers,
  figures, citations, quotations, statuses or relationships into production.
- Preserve entity identity, protected-witness handling, citation resolution,
  exhibit status semantics, provenance requirements and version-bound
  SourceAnchor precision.
- A search match remains distinct from a verified mention.
- Unsupported design concepts receive an honest empty or unavailable state.
- Interface strings live in both string tables and colours come from tokens.
- `docs/design/` remains read-only except for the Phase 21 audit deliverable
  explicitly required by this phase.
- Do not start a later checkpoint without explicit authorization.

## 21A — Complete (2026-09-25)

### Scope

1. Audit the running application against the actual Home, Global Search,
   command-search overlay, Evidence Explorer, Document Reader, mobile and
   design-system artboards.
2. Align the shared visual system and shell: typography, density, surface
   hierarchy, spacing, navigation, case context and reusable controls.
3. Rebuild the homepage as the approved research entry point using real corpus
   counts and real recent records.
4. Recompose Search into the approved query → categories → grouped results →
   interpretation → exact-source workflow.
5. Refine command search for identifier- and name-first navigation using only
   real supported results and actions.
6. Recompose Documents and Exhibits around the dense Evidence Explorer table,
   selection and inspector pattern. Exhibits retain their real status history
   and `UNKNOWN` state.
7. Route source actions through Phase 20 exact, version-safe Reader links.
8. Implement intentional 1440px, 1024px and Pixel 7 behavior.
9. Record the comparison in
   `docs/design/PHASE21A_DESIGN_PARITY_AUDIT.md`.

### Verification

- Focused unit/component coverage for homepage, navigation, search, command
  search, documents, exhibits, responsive states and exact-source actions.
- Side-by-side captures of Home, Search and Documents/Exhibits at 1440px,
  1024px and Pixel 7 against the relevant design artboards.
- Real flow checks: Search → result → exact source; Document → Reader → correct
  PDF; Exhibit → dossier/inspector → status/source; Witness → appearance →
  transcript → PDF.
- Accessibility checks for changed routes.
- Before checkpoint acceptance: `make lint`, `make typecheck`, `make test`.

### Exit criteria

- [x] Shared shell and reusable research controls closely match the approved
      design composition and density.
- [x] Homepage uses the approved hierarchy with real corpus state.
- [x] Search and command search provide rich, honest real-result navigation.
- [x] Documents and Exhibits use the dense explorer plus inspector pattern.
- [x] Phase 20 exact-source behavior is preserved.
- [x] Desktop, laptop/tablet and Pixel 7 comparisons are captured and audited.
- [x] Focused real-data and accessibility flows pass.
- [x] Remaining differences and data limitations are documented.

### 21A completion record

- Implementation: `253085c` (`feat(web): align phase 21a research entry surfaces`).
- Audit and focused browser coverage: `0a3092c`
  (`test(web): add phase 21a parity audit`).
- Design comparison: `docs/design/PHASE21A_DESIGN_PARITY_AUDIT.md`.
- Responsive capture matrix: Home, Search, Documents and Evidence at 1440px,
  1024px and Pixel 7; no document-level horizontal overflow.
- Real browser flows: 9 passed, 1 intentionally skipped duplicate capture;
  Phase 19 witness/exhibit regressions: 4 passed.
- Accessibility: changed research-entry routes passed automated checks on
  desktop and Pixel 7.
- Repository gates: `make lint`, `make typecheck`, `make test` pass (353 backend
  and 260 frontend tests).
- Phase 21 remains **IN PROGRESS**. No tag was created and 21B was not started.

## 21B — Not started

People / Witnesses; Findings; Network / Timeline; Appeal / AI / External
Sources; Reader and remaining workflow parity.

## 21C — Not started

Full route-by-route desktop, laptop and mobile parity audit, regression gate
and Phase 21 closeout.

## Closeout rule

Phase 21 is not complete at the end of 21A. Do not tag, merge to `main` or
begin 21B without explicit authorization.
