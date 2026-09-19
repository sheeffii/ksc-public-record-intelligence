# HANDOFF.md
### KSC Public Record Intelligence — engineering handoff

**Read this file first.** It tells you what is authoritative, what is mock, what must come from the backend, and what must never be hardcoded.

Design is complete. Do not begin implementation until you have read §1, §9 and §10 — they contain constraints that are cheap to build in now and expensive to retrofit.

| Document | What it is for |
|---|---|
| **HANDOFF.md** | This file — the brief, the data contracts, the checklist |
| `DESIGN_SYSTEM.md` | Tokens, typography, spacing, colour semantics |
| `PAGE_SPECS.md` | Per-screen spec — 11 fields per screen, all 21 artboards |
| `COMPONENTS.md` | 83-component library with props, states and constraints |
| `ROUTE_MAP.md` | Routes, query params, deep-link guarantees |
| `UX_FLOWS.md` | Six audited end-to-end flows |
| `DESIGN_DECISIONS.md` | Why the design is this way, and what was rejected |

---

## 1. The three rules that outrank everything else

If a ticket ever conflicts with one of these, the ticket is wrong. Escalate rather than implement.

**1. The interface never implies guilt.** No score, rank, rating, weight or ordering of any person exists anywhere in the product — not in the UI, and **not in the data model**. Colour encodes *where information came from*, never how bad it is. A network connection means only that a source-backed reference exists.

**2. Record and AI are never confusable.** Court record material and generated analysis are separated by four simultaneous signals — separate container, different border style (solid vs dashed), a colour used for nothing else, and a labelled divider. Losing any one is a regression, including at 390px.

**3. A citation that does not resolve is not rendered.** Not degraded, not shown greyed, not shown with a warning — withheld, with the gap reported instead. This applies to chips, to network edges, to evidence paths and to whole AI answers.

---

## 2. Which artboards are authoritative

The Design canvas holds 21 artboards. **18 are authoritative** — build to them pixel-for-pixel on layout, spacing, type and colour.

| Authoritative — build to these | | |
|---|---|---|
| 02 Homepage | 09 Statement Comparison | 15 AI Research |
| 03 Network Explorer | 10 Evidence Explorer | 16 Public / Simple Mode |
| 04 Document Reader | 11 Incident Detail | 17 Mobile (4 frames) |
| 05 Finding Detail | 12 Research Timeline | 20 Evidence Path |
| 06 Global Search | 13 Appeal Research | |
| 06b ⌘K Overlay | 14 Argument Lab + Red Team | |
| 07 Person Dossier | | |
| 08 Witness Dossier | | |

**Three are reference, not build targets:**

- **01 Design System** — the token and component reference. Build the tokens from `DESIGN_SYSTEM.md`, not by eyedropping the artboard.
- **18 Language** — specifies the language system and proves Albanian layout. Not a route.
- **19 Flow Audit** — records that the six flows resolve. Not a route.

**Five routes are not designed** and must be built from existing patterns: `/people`, `/witnesses`, `/documents`, `/incidents`, `/findings`. All five are directory/index screens. Use the Evidence Explorer table (10) with different columns. None requires a new component or new semantics. Get these reviewed by design before shipping, but do not block on new artboards.

---

## 3. Reusable components

83 components in `COMPONENTS.md`. These twelve carry product rules and should be built first, as shared primitives, before any screen:

| Component | Why it is foundational |
|---|---|
| `CitationChip` | Used on every screen. Resolves to a page/paragraph/line, or does not render. |
| `CitationPreview` | Popover shown before navigation. Required by Flow E. |
| `SourceBadge` | Ten canonical variants. The provenance vocabulary. |
| `VerificationBadge` | Five states, glyph-differentiated. |
| `RecordBlock` / `AiAnalysisBlock` | The matched pair that makes the boundary structural. |
| `ProvenanceBoundary` | The labelled dashed divider. |
| `ProtectionNotice` | Required on every protected-witness surface. |
| `WitnessHeaderProtected` | Separate variant — no identity markup exists in it. |
| `DirectionBadge` + `ScopeNote` | Never ship one without the other. |
| `ReferenceCountStrip` | Carries its own disclaimer; the disclaimer is not page copy. |
| `DataTable` + `DensityToggle` | Five undesigned directories depend on this. |
| `GapNotice` | The component that makes absence visible. |

Build these as a package with their own tests before screen work starts. Several encode rules that are trivial to enforce in one component and nearly impossible to enforce screen-by-screen.

---

## 4. Route structure

Full detail in `ROUTE_MAP.md`. The contract in brief:

- Every meaningful view state is addressable. Tabs are `?tab=`, filters are query params, selection is `?sel=`.
- Route identifiers are the record's own — `W01234`, `P00441`, `F00482` — never internal IDs. Researchers cite URLs.
- The case prefix is omitted; everything is scoped to KSC-BC-2020-06. A second case later becomes `/case/:caseId/…` with everything nesting unchanged.
- Mode (Simple/Research) and language (EN/SQ) are user settings, **not** route prefixes.

**Deep links that must survive a cold load:** `/documents/:id?page=894&highlight=8422` · `/network?focus=X&depth=2&sel=Y` · `/exhibits?...&sel=P00441` · `/witnesses/:code/compare?segment=7` · `/findings/:id`.

**Paths are never cached by URL.** `/network/path?from=A&to=B` recomputes every time, because the record can change underneath it.

---

## 5. Desktop and mobile behavior

**Desktop is the primary target at 1440px.** The standard body is three regions: left rail 214–246 · centre flex with `min-width: 0` · right rail 262–376. The centre column always carries `min-width: 0` so long identifiers cannot force horizontal scroll.

**Breakpoints**

| Width | Behaviour |
|---|---|
| ≥1440 | Full three-region layout as drawn |
| 1280–1439 | Right rail → collapsible sheet; centre keeps its width |
| 1100–1279 | Left rail → drawer or dropdown; tables begin collapsing secondary columns |
| 860–1099 | Single column; rails become sheets; tables become stacked cards |
| ≤390 | Mobile patterns per artboard 17 |

**Mobile rules** (artboard 17 is authoritative for the four frames drawn; the patterns generalise):

- Top nav → five-item bottom tab bar. Case identifier and demo flag pin under the header.
- Side panels → bottom sheets. The network inspector has three detents: peek, half, full.
- Multi-column comparisons → single column with a segmented control.
- Horizontal timelines → vertical lists grouped by era, glyphs retained.
- Touch targets ≥44px. Type floor 10px labels, 11px body.
- **The provenance boundary, protected-witness treatment and network disclaimer are never dropped for space.**

---

## 6. Interaction rules

**Tabs** are route state and URL-addressable. An unknown `?tab=` value falls back to the default without an error.

**Filters** are additive, serialise to the URL, and are individually removable from the active-chip row. Empty states name the filters most responsible for narrowing.

**Sorting** — findings, issues and evidence sort by **judgment order** by default. No relevance, severity or significance sort is offered anywhere, on any screen. Tables (10) sort by column; that is a record attribute, not an assessment.

**Selection** opens a panel without losing scroll position in the list behind it.

**Density** is per-table and persists per user.

**Keyboard** — `⌘K` / `Ctrl+K` opens the palette from anywhere. In the palette: `↑↓` navigate, `↵` open, `⌘↵` open in network, `tab` filter by category, `esc` close. Focus is a 3px accent ring; never `outline: none` without a replacement.

**Actions that never mutate** — every Argument Lab research action returns annotations without modifying the draft. Red-team stages never rewrite the user's text.

---

## 7. Citation behavior

The single most important interaction in the product.

**A citation chip always resolves to a specific page, paragraph or line range.** If it cannot, the chip is not rendered and the surrounding content is either withheld or marked with `GapNotice`.

**Canonical forms**
```
Judgment · ¶8421–8427
Transcript · 14 Mar 2024 · p. 12,453 · lines 8–19
Exhibit P00123 · p. 4
KSC-BC-2020-06/F01234/RED · ¶45
```

**Click behaviour is two-stage.** A chip opens `CitationPreview` — a popover with the surrounding passage — with the originating answer or argument still visible behind it. *Open document* then navigates. This was added during the Flow E audit; a single-stage jump loses the user's place.

**Copy behaviour.** *Copy citation* yields the official citation string, not a URL. Researchers paste these into filings.

**Resolution must be pre-computed at ingest.** The rule that an unresolvable citation blocks rendering is correct but expensive to check at request time. Build a resolution index during ingestion.

**Exports carry the citation set**, not just rendered rows, so an export can be re-resolved against the live record later.

---

## 8. Network behavior

**Every edge resolves to a citation.** An edge without one is not returned by the API and not drawn. There is no "inferred", "probable" or "likely" edge type, and adding one would undermine the entire graph.

**The edge inspector is headed with a question** — *"Why does this connection exist?"* — and answers it with the source, exact citation, verification state and date. This framing is not decoration; it teaches users what an edge is.

**Node shape carries type independently of colour** (hexagon accused, dashed circle protected witness, triangle incident, and so on), so the graph is legible without colour vision.

**Selection uses an outer ring**, never a fill change that could read as emphasis or severity.

**The neutrality disclaimer appears twice** — legend footer and canvas watermark: *"Connections represent relationships or references found in the public court record. A connection does not by itself imply wrongdoing, agreement, responsibility or guilt."*

**Paths are ranked by hop count only.** Never by strength, directness or significance. A shorter path is not a stronger one, and the Evidence Path screen says so explicitly.

---

## 9. Data requirements for major components

Per-screen payloads are in `PAGE_SPECS.md`. These are the shared shapes.

### Citation — the universal type
```ts
Citation = {
  sourceType: 'court'|'witness'|'spo'|'defence'|'exhibit'
  ref: string            // "P00441", "F02219", "Judgment"
  docId: string          // resolves to /documents/:id
  page?: number
  paraFrom?: number
  paraTo?: number
  lineFrom?: number
  lineTo?: number
  resolved: boolean      // false ⇒ do not render the chip
  display: string        // pre-formatted canonical string
}
```

### Verification
```ts
VerificationState = 'verified' | 'ai-flagged' | 'unresolved'
                  | 'needs-evidence' | 'unreviewed'
VerificationMeta = { state, reviewedBy?: string[], reviewedAt?: ISO8601 }
```

### Witness — protection is structural
```ts
Witness = {
  code: string                 // "W01234"
  protected: boolean
  protectiveMeasures: string[]
  public?: {                   // MUST be absent when protected === true
    displayName: string
    statedOccupation?: string
    expertField?: string
    calledBy: 'spo'|'defence'
  }
}
```
When `protected` is true the `public` object is **omitted from the payload**, not null-filled. Enforce at the serialiser.

### Direction — always scoped to a claim
```ts
EvidenceDirection = {
  claimId: string              // the claim this is measured against
  direction: 'supports'|'contradicts'|'qualifies'|'neutral'
  sourceType, ref, citation: Citation
  courtCited: boolean
  courtCitedPara?: number
  verification: VerificationMeta
}
```
`direction` is meaningless without `claimId`. Never expose one without the other.

### Reference counts — counts only
```ts
ReferenceCounts = {
  documentMentions, transcriptMentions, exhibitRefs,
  findings, witnessesWhoReferred, incidents, citationsResolved: number
}
```
No score, weight, rank, centrality or priority field. Ever.

### AI answer block
```ts
AnswerBlock = {
  kind: 'court'|'evidence'|'testimony'|'spo'|'defence'|'ai'
  text: string
  citations: Citation[]
}
```
`kind: 'ai'` renders in `AiAnalysisBlock` after the boundary divider. **The API returns block order; the client does not reorder.** If any citation in any block has `resolved: false`, the whole answer is withheld.

### Gap
```ts
Gap = {
  kind: 'closed-session'|'redaction'|'untranslated'|'unresolved-citation'
  ref: string
  extent: string               // "T. 4,511–4,552", "2 pages"
  reason: string
}
```
Gaps are returned alongside content, never instead of it, and are always rendered.

---

## 10. Mock content, backend content, and what must never be hardcoded

### Mock-only — every figure and every case detail in the prototype

All numbers in the artboards are invented. Every name, witness code, exhibit reference, filing number, paragraph number, quotation and date is illustrative. They are plausible, which is exactly why they are dangerous — a screenshot of a plausible fake number about a real criminal case is misinformation.

```
3,241 documents · 186,420 transcript pages · 147 witnesses · 2,814 exhibits
512 findings · 89 incidents · 18,403 citations resolved · 24,847 records indexed
W01234 · W02891 · W03112 · W01287 · W01291 · Dr. A. Rexhepi
P00123 · P00441 · P00623 · P00887 · P01102 · P01377 · P01990 · P02041 · P00298
D01204 · D00914 · D01455 · D-0092 · D-0093
F00026 · F02204 · F02219 · F02890 · F02931
F00480 · F00482 · F00483 · F00484 · F00491 · F00495 · F00511 · F00518
I-0042 · ¶891 · ¶904 · ¶1,204–1,209 · ¶8421–8427 · T. 4,226 · T. 6,744
All quoted "judgment" and "transcript" text
```

**Every screen displaying a figure carries the `DemoDataFlag`.** It is removed from a screen only when every figure on that screen is a live database read. Do not remove it globally in one commit.

### Must come from the backend

| Data | Notes |
|---|---|
| All counts | Live `COUNT()` at request time. Never cached into the bundle. |
| Documents, pages, paragraph text | Including redaction extents |
| Transcripts, segment boundaries | Including closed-session ranges |
| Exhibits and provenance | Document date, admitted date, tendering party, through-witness |
| Findings and judgment paragraphs | With the citation graph |
| Witness records and protection state | Protection state is authoritative from the backend |
| Citation resolution index | Pre-computed at ingest |
| Network nodes and edges | Edges only where a citation resolves |
| Evidence paths | Computed per request, never cached by URL |
| Verification state and reviewer identity | |
| Direction labels and their claim scope | |
| AI retrieval sets and answers | Sources retrieved before composition |
| Plain-language text for Public mode | Authored and reviewed, keyed to `findingId` — **not generated at request time** |
| Interface strings for both locales | |
| Ingestion status | |

### Must never be hardcoded

1. **Any count, total or statistic.** If it appears as a number on screen, it comes from a query.
2. **Any case content** — names, codes, references, paragraph numbers, quotations, dates.
3. **Protection state.** Never a client-side list, never an environment constant. Resolve from the backend and fail closed.
4. **Citation resolution.** Never assume a reference resolves; check the `resolved` flag.
5. **Interface strings.** No English literals in components. Both locales come from the string table, including badge labels and governance footnotes.
6. **Legal terminology in Albanian.** Must come from the reviewed string table, checked against the Chambers' published Albanian texts.
7. **Colour values in components.** Tokens only. A component that hardcodes `#818CF8` will not survive a palette change and may silently break the provenance semantics.
8. **The boundary, the disclaimers and the scope notes.** These are component-owned, from the string table — never page-level copy a developer can forget to include.
9. **Date type.** Never infer that a document's date is its filing date, or vice versa. Both are stored; both are rendered as what they are.
10. **Any ordering that implies importance.** Sort keys come from the record (judgment order, hop count, date) or from an explicit user column choice.

---

## 11. Suggested build order

1. **Tokens + the twelve foundational components** (§3), with tests for the rules they encode.
2. **Citation resolution index** at ingest, and the `Citation` type end-to-end. Everything depends on this.
3. **Document Reader (04)** — the terminal state of five of eight flows. If this is wrong, nothing else matters.
4. **Global Search (06) + ⌘K (06b)** — the entry point to everything.
5. **Finding Detail (05)** — the most complex screen and the one that exercises every provenance rule.
6. **Dossiers (07, 08)** — including the protected-witness fail-closed path.
7. **Evidence Explorer (10)**, which unlocks the five undesigned directories.
8. **Network (03) + Evidence Path (20)**.
9. **Incident (11), Timeline (12), Statement Comparison (09)**.
10. **Appeal (13), Argument Lab (14), AI Research (15)**.
11. **Public mode (16)** and the second locale.
12. Mobile throughout, not at the end.

---

## 12. READY FOR ENGINEERING

| Area | Status | Notes |
|---|---|---|
| **Design system** | ✅ PASS | Tokens, type scale, spacing, radii, elevation, colour semantics fully specified. Artboard 01 is the reference; build from `DESIGN_SYSTEM.md`. |
| **Homepage** | ✅ PASS | Artboard 02. Demo-data flag and mock-data notice applied. |
| **Search** | ✅ PASS | Artboards 06 + 06b. Syntax, facets, query interpretation and empty-state diagnosis all specified. |
| **People** | ⚠️ NEEDS ATTENTION | Person Dossier (07) is complete. The `/people` **directory is not designed** — build from the Evidence Explorer table pattern and have design review before shipping. |
| **Witnesses** | ⚠️ NEEDS ATTENTION | Witness Dossier (08) complete with both protection states. The `/witnesses` **directory is not designed**; it additionally needs the protected treatment applied to a table row, which has not been drawn. |
| **Documents** | ⚠️ NEEDS ATTENTION | Document Reader (04) is complete and is the terminal state of most flows. The `/documents` **directory is not designed**. |
| **Network** | ✅ PASS | Artboard 03. Edge-citation rule, neutrality disclaimer in two places, shape-independent-of-colour all specified. |
| **Timeline** | ✅ PASS | Artboard 12. Dual-era axis and five distinct date types specified. |
| **Judgment** | ✅ PASS | Covered by Document Reader (04) in judgment context plus Finding Detail (05). Paragraph anchors are addressable. |
| **Findings** | ⚠️ NEEDS ATTENTION | Finding Detail (05) is complete and authoritative. The `/findings` **matrix/index is not designed** — promote the findings table from artboard 07. |
| **Evidence Path** | ✅ PASS | Artboard 20, built during this audit. Per-hop inspection, alternates by hop count only, and the *What a path cannot tell you* card. |
| **Appeal Research** | ✅ PASS | Artboard 13. Predictive language eliminated; prohibited fields named in the data contract. |
| **Argument Lab** | ✅ PASS | Artboard 14. Editor flags absence of citation only, never argument quality. |
| **Red Team** | ✅ PASS | Three stages on artboard 14, non-collapsible, each independently re-runnable. |
| **AI Research** | ✅ PASS | Artboard 15. Retrieval-before-composition, four-signal boundary, withhold-on-unresolved. |
| **English / Albanian** | ⚠️ NEEDS ATTENTION | The **system** is complete and proven (artboard 18): selector, layout rules, measured nav growth, never-translated identifier set, independent document language. But **the Albanian strings are design placeholders**. Legal terminology must be reviewed against the Chambers' own published Albanian texts before any public release — their wording governs. This is a content blocker, not a design gap. |
| **Mobile** | ⚠️ NEEDS ATTENTION | Four representative frames are designed (artboard 17) and the collapse patterns are specified for every screen in `PAGE_SPECS.md`. But **17 of 21 screens have no drawn mobile frame**. The patterns generalise; the risk is on the dense screens — Evidence Explorer (10), Incident matrix (11), Statement Comparison (09) and Argument Lab (14). Draw those four before building them. |
| **Accessibility** | ⚠️ NEEDS ATTENTION | The **floor** is specified: 4.5:1 body contrast, colour never the sole carrier, shape-independent node types, four-signal provenance, 3px focus ring, ≥44px mobile targets. **Not yet done:** a full contrast audit of every token pair, a keyboard map beyond the palette, screen-reader semantics for the network canvas and the timeline, and a reduced-motion policy. Commission these before the first external release. |
| **Source provenance** | ✅ PASS | Six source types distinguished by colour, badge, container and copy on every screen. The record/AI boundary uses four simultaneous signals. `SourceBadge` and the block pair are specified as shared primitives. |
| **Citation UX** | ✅ PASS | Canonical forms, resolve-or-withhold rule, two-stage preview-then-navigate, copy-citation, export-carries-citations. One note: `CitationPreview` is **specified but not drawn** — it was added during the Flow E audit. Build it from the spec in `COMPONENTS.md`; it is a standard popover. |

**Summary — 13 PASS, 7 NEEDS ATTENTION.**

None of the seven blocks the start of engineering. Four are undesigned directory/index screens that reuse an existing table pattern. One is a content dependency (Albanian legal review). Two are quality passes that should be commissioned now and land before external release (four more mobile frames, a full accessibility audit).

---

## 13. Workflow verification — all eight resolve

| # | Workflow | Result |
|---|---|---|
| 1 | Search → Entity/Document → Original Source | ✅ 06 → 07/04 → 04. Every result row opens an underlying source, never a summary. |
| 2 | Person → Network → Connection → Evidence → Original Source | ✅ 07 → 03 → EdgeInspector → 10 → 04. Six hops, all controls above the fold. |
| 3 | Witness → Testimony → Cross → Statement Comparison → Source | ✅ 08 → 08 → 08 → 09 → 04. Three entry points to 09 after the audit fix. |
| 4 | Judgment → Finding → Evidence Relied Upon → Original Sources | ✅ 04 → 05 step 01 → step 02 → 04. Contrary material is on the path, not behind a tab. |
| 5 | Finding → Supporting / Contrary / Qualifying Evidence | ✅ 05 step 04 direction counts → `/incidents/:id?tab=evidence&direction=` → the full matrix on 11. All four directions shown together, always. |
| 6 | Finding → Potential Issue for Review → Red Team → Source Audit | ✅ 05 step 07 → 13 → 14 stages 1–3 → 05 step 09. |
| 7 | AI Research → Answer → Citations → Original Court Source | ✅ 15 → structured answer → CitationPreview → 04. Answer withheld if any citation is unresolvable. |
| 8 | Entity A → Find Record Connection → Evidence Path → Entity B | ✅ 07 → picker → 20 → per-hop inspection → 04/10. **Artboard 20 was built during this audit; it did not previously exist.** |

---

## 14. Changes made during this audit

Two inconsistencies and one gap were found and fixed. Nothing else was redesigned.

1. **Missing screen.** Flow 8's Evidence Path had no artboard — it was referenced by the Network toolbar and the flow audit board but never designed. **Artboard 20 built.**
2. **Inconsistent chrome.** The EN/SQ language toggle was present on all 12 Phase 2 screens but absent from three Phase 1 screens. **Added to Homepage (02), Network Explorer (03) and Document Reader (04)** in their respective modes.
3. **Missing demo flag.** The ⌘K overlay (06b) displays counts but carried no demo-data flag. **Added to the palette footer.**

Verified clean, no action needed: all 21 artboards parse and carry a valid `$preview` matching their canvas frame · no stray markup · no instance of predictive appeal language anywhere (the four matches for "probability/likelihood" are all disclaimers explicitly ruling them out) · demo flags present on every screen displaying a figure · neutrality disclaimers present on Network, Incident and Mobile network frame · six source types visually distinguished throughout.
