# Phase 21B Design Parity Audit

Date: 2026-09-25
Status: implementation checkpoint; final 21B acceptance deferred
Design source: `docs/design/Design.html`

## Comparison method

The actual Person Dossier, Witness Dossier, Incident Detail, Timeline, Appeal
Research, AI Research, Evidence Path, Document Reader, Finding Detail, Network,
Mobile and System artboards were rendered before implementation. Real routes
were then inspected at 1440px, 1024px and the Pixel 7 viewport. No prototype
identifier, count, quotation, relationship or status was copied into the app.

## Route audit

| Design reference | Current route | Changes made | Real-data differences / remaining gaps |
|---|---|---|---|
| Evidence Explorer directory language | `/people`, `/witnesses`, `/findings` | Dense continuous table, integrated search/filter/density/export controls, selection state, desktop inspector and mobile cards/overlay. Person and witness columns expose supported occurrence and relationship counts without treating them as importance. | The design has no separate directory artboards. Real list projections do not provide exact anchors; source navigation begins in the dossier. |
| `07_PersonDossier` | `/people/:slug` | Wider dossier composition, explicit record activity, aliases, bounded verified/review/search occurrence groups, typed relationships and direct exact-source actions. | Real public roles and aliases are shown as stored. Sparse findings/appearances remain absent; no inferred identity or role is added. |
| `08_WitnessDossier` | `/witnesses/:code` | Protected-code identity header, activity summary, appearance chronology, bounded verified mentions/search matches/relationships, exact transcript/source actions and responsive protection context. | Protected witnesses remain code-only. Only header-backed appearances are shown; unavailable hearings are stated rather than estimated. |
| `FindingDetail` | `/findings/:id` | Existing real Court finding → adjudicative record → evidence matrix → party positions → Court response hierarchy retained and aligned with the shared compact research system. | The held corpus has one verified finding. No illustrative evidence direction or AI issue is added. |
| `Network` | `/network` | Existing bounded graph, typed filters, progressive focus, node/edge inspector, textual alternative and exact provenance actions retained as the approved graph workspace. | The real graph is larger and dominated by citation edges; it remains paginated rather than rendered as one undifferentiated graph. |
| `12_Timeline` | `/timeline` | Real dates now use a bounded seven-lane overview with date-type styling, counts, zoom controls and selected-card inspector; mobile uses the chronological list alternative. | Real events have no SourceAnchors. Lane cards therefore expose stored docket dates without fabricating text anchors. |
| `11_IncidentDetail` | `/incidents`, `/incidents/:id` | Existing honest real empty/list state retained; no ordinary mention is promoted to an incident. | The real structured corpus currently does not support the rich illustrative incident matrix. |
| `13_AppealResearch` | `/appeal` | Potential-Issue framing, compact two-column source comparison, citation audit, missing-material grid and no-prediction boundaries. | One narrow review issue is supported. Missing filings and the absent Trial Judgment remain explicit. |
| External-source system pattern | `/media` | Existing three-region public-source workspace retained with scope controls, source list/comparison and limitations inspector. | `Design.html` has no dedicated external-source artboard. All three real items remain `EXTERNAL_ONLY`; they never masquerade as court evidence. |
| `15_AIResearch` | `/ai`, `/ai/:sessionId` | Citation-first question workspace retained; session history is now a bounded sidebar. Record blocks remain above the provenance boundary and AI blocks below it. | No fake answer is created. Empty/input state is shown until a real audited run is opened or created. |
| `DocumentReader` | `/documents/:id` | Phase 20 source-first three-panel Reader retained: exact original PDF, synchronized parsed text, contextual inspector, compact toolbar and Source/Text/Context mobile workflow. | Real held PDFs and persisted geometry determine every visible highlight; no illustrative summary or entity link is synthesized. |
| `20_EvidencePath` | `/network/path` | Deterministic hop canvas, hop inspector, provenance actions, composition panel and limitation copy retained; remaining demo-language leak removed. | Paths traverse citation-backed real edges only. Unsupported alternate paths are not invented. |

## Responsive result

- 1440px: directory and graph inspectors remain visible; dossiers use their
  wide research composition; timeline uses lanes.
- 1024px: controls wrap compactly and inspectors move below or withhold until
  selection as appropriate.
- Pixel 7: directories become labelled record cards, inspectors become
  overlays/sheets, timeline becomes a list, Network uses its detail sheet and
  Reader uses Source/Text/Context modes.
- The viewport matrix found no document-level horizontal overflow.

## Integrity checks

- `VERIFIED MENTION`, `SEARCH MATCH`, review states, citation states and
  `UNKNOWN` remain distinct.
- Protected-witness code-only behavior is unchanged.
- Phase 20 exact-version PDF, SourceAnchor, highlight and transcript-sync
  behavior is unchanged.
- External public sources remain structurally and visually separate from the
  court record.
- Counts remain occurrence/reference counts, never scores or rankings.

## Deferred acceptance work

This is the implementation checkpoint requested for the constrained session.
The full Phase 21B route-by-route interaction/axe flow gate and repository-wide
regression suite were deliberately deferred to the next step. Phase 21B and
Phase 21 remain in progress; 21C has not started.
