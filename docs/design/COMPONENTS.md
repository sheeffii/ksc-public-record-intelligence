# COMPONENTS.md
### KSC Public Record Intelligence — component library

Components are grouped by layer. Each entry gives its props, its states, and — where it carries a product rule — the constraint engineering must not drop.

---

## COMPONENT INVENTORY

| Layer | Components | Count |
|---|---|---|
| Chrome | GlobalNav, LightNav, CaseStripe, Breadcrumb, TabBar, DemoDataFlag, LanguageToggle, ModeToggle, GovernanceFooter | 9 |
| Provenance | SourceBadge, VerificationBadge, CitationChip, CitationPreview, ProvenanceBoundary, AiAnalysisBlock, RecordBlock, ProtectionNotice | 8 |
| Data display | DataTable, DensityToggle, StatCell, ReferenceCountStrip, MetadataTable, DirectionBadge, DirectionSummaryBar, EvidenceMatrix, SourceAuditTable | 9 |
| Record content | DocumentPage, TestimonyCard, SourceQuoteCard, QuotedReasoning, PlainLanguageBlock, LegalTermTooltip | 6 |
| Entity | PersonHeader, WitnessHeader (2 states), HexAvatar, ProtectedAvatar, IncidentHeader, EntityChip, QuickActionBar | 7 |
| Graph | NetworkCanvas, NodeShape (8), EdgeLine, EdgeInspector, NodeInspector, NetworkPreview, LegendPanel, Minimap | 8 |
| Time | DualEraAxis, LaneRow, TimelineEvent, DateTypeLegend, TypedDateTimeline, AttachedDatesTable | 6 |
| Search | SearchField, CommandPalette, PaletteRow, FilterRail, FilterChip, ResultRow, GroupHeader, MatchHighlight, QueryInterpretation | 9 |
| Analysis | IssueCard, ComparisonColumn, DifferenceSpan, LabelPicker, ArgumentEditor, StageStepper, NeutralReviewRow, CitationHealthPanel, PotentialIssueBlock, RedTeamPair | 10 |
| Chain | ChainSpine, ChainStepMarker, EvidenceRow, DirectionCountCard, ScopeNote | 5 |
| Path | EntityPicker, PathCanvas, PathNode, PathEdge, HopMarker, HopInspectorRow, PathCompositionTable, AlternatePathList, CannotTellYouCard | 9 |
| States | SkeletonBlock, EmptyState, ErrorState, GapNotice, ProgressBar | 5 |
| **Total** | | **91** |

---

## 1. CHROME

### GlobalNav
`52px` fixed. Logo (4-square mark + `KSC·PRI`) · nav links · right cluster (search affordance with `⌘K`, LanguageToggle, avatar).

Props: `activeSection`, `showSearch`, `user`.
States: default · active link (`--surface-raised` pill) · AI link (always `--ai` coloured, never active-pilled).

**Constraint.** Nav links have no fixed width and 11px horizontal padding, so Albanian labels grow rather than truncate. Below 1280px in SQ, trailing items collapse into an overflow menu — never ellipsis.

### LightNav
`56px`. The light-mode equivalent used on 04 and 16. Carries ModeToggle on 16.

### CaseStripe / Breadcrumb
`30–32px` band below the nav. Carries case identifier, breadcrumb trail, and the DemoDataFlag pinned right.

### TabBar
`38–40px`. Active tab: 600 weight, 2px bottom border in the screen's accent (`--court` on 07, `--witness` on 08, `--incident` on 11, `--verified` on 05).

Props: `tabs[]`, `active`, `accent`.
**Constraint.** Tabs scroll horizontally rather than wrap or truncate. Tab labels are URL-addressable.

### DemoDataFlag
`badge` variant. Amber, `#201A08` / `#6B5320` / `#FBB035`. Text: *Demo data — not live records* (long form) or *Demo data* (compact).

**Constraint.** Present on every screen that displays a figure. Removed in production only when every figure on that screen is a live database read.

### LanguageToggle
Fixed `62px` `EN / SQ` control. Expands to LanguageMenu with English / Shqip, each with a sub-line, plus the note that switching changes the interface only.

**Constraint.** Never reflows the nav. Document language is a separate control (DocumentLanguagePanel) and the two are never merged.

### ModeToggle
Simple / Research segmented control. Swaps rendering of the same entity routes.

### GovernanceFooter
`24–26px` band. 10px `--text-faint` text. Carries the screen's required neutrality note.

**Constraint.** Not decorative. Each screen's required text is listed in `PAGE_SPECS.md` and is part of the screen's definition of done.

---

## 2. PROVENANCE — the load-bearing layer

### SourceBadge
Uppercase 9–9.5px / 600, `0.05–0.06em` tracking, 3px radius, dot or glyph + label.

Props: `type` (`court` · `witness` · `spo` · `defence` · `exhibit` · `ai` · `incident` · `location` · `organisation`), `size`, `variant`.

Ten canonical variants are specified in Artboard 01 and must not be extended without a matching entry in the palette and the glossary.

**Constraint.** `min-width`, never fixed width. Wraps to a second line rather than truncating, because Albanian labels run up to 60% longer.

### VerificationBadge
Five states, each with a distinct glyph so they are separable without colour:

| State | Colour | Glyph |
|---|---|---|
| Human Verified | `--verified` | tick in circle |
| AI Flagged — needs review | `--ai` | cross in circle |
| Unresolved Citation | `--unresolved` | `!` in circle |
| Needs More Evidence | `--doc` | `!` in circle, amber |
| Unreviewed | `--text-secondary` | dashed circle |

### CitationChip
The most-used component in the product. `--surface-raised` ground, `--border`, 5px radius, source-coloured 600-weight text, optional type glyph, trailing arrow when navigable.

Props: `sourceType`, `reference`, `navigable`, `size` (`sm` 10px / `md` 10.5px), `inline`.

Four canonical forms:
```
Judgment · ¶8421–8427
Transcript · 14 Mar 2024 · p. 12,453 · lines 8–19
Exhibit P00123 · p. 4
KSC-BC-2020-06/F01234/RED · ¶45
```

**Constraint.** A chip always resolves to a specific page, paragraph or line range. A chip that cannot resolve is not rendered — the surrounding content is withheld or marked with GapNotice instead.

Inline variant uses `vertical-align: middle` and sits inside flowing prose without breaking the line box.

### CitationPreview
Popover shown on chip activation **before** navigation. Contains the surrounding passage, the full citation, and an "Open document" action. The underlying answer or argument stays visible behind it.

**Added during the Flow E audit.** Chips previously navigated directly, which lost the user's place in a cited answer.

### ProvenanceBoundary
A labelled dashed rule: `repeating-linear-gradient` in `--ai` at 36% alpha, with centred uppercase text *"▼ Below this line: generated analysis, not the record"*.

**Constraint.** Required on any surface where record material and generated analysis both appear. Never omitted for vertical space, including at 390px.

### RecordBlock / AiAnalysisBlock
A matched pair, deliberately divergent:

| | RecordBlock | AiAnalysisBlock |
|---|---|---|
| Border | 1px solid, source-coloured | **1.5px dashed** `#5C2D4A` |
| Ground | `--surface` | `#150C1C` / `#1A1024` |
| Header band | Source colour on its tinted bg | `--ai` on `#25102A` |
| Header text | Source name + provenance note | `AI Analysis` + *"Written by software · no part of this is a court record"* |
| Body type | Libre Baskerville for quotations | DM Sans only |

**Constraint.** These two never nest and never share a container. Four independent signals separate them — container, border style, colour, label — and removing any one is a regression.

### ProtectionNotice
Cyan-bordered card shown on every protected witness surface. States that the system holds only the pseudonym, derives nothing, and that search will not resolve a name to a code.

**Constraint.** Renders before witness content, not after. If protection state cannot be resolved, the surface fails closed to the protected treatment.

---

## 3. DATA DISPLAY

### DataTable
Header row `28–30px` on `--bg-deep` with 9px uppercase labels. Rows `32px` compact / `44px` comfortable, separated by `--border-faint`. Selected row: `--surface-high` with a 3px source-coloured left border.

Props: `columns[]`, `rows[]`, `density`, `sortBy`, `selectedId`, `onSelect`.

**Constraint.** Column minimum widths are set from the **longest translation**, not the English string. Numeric columns are right-aligned and `tabular-nums`. Identifier columns are source-coloured and 600 weight.

### DensityToggle
Compact / Comfortable. Persisted per table, not globally.

### StatCell / ReferenceCountStrip
Large tabular figure (17–24px / 700, `-0.02em`) over a 10–11px muted label.

**Constraint.** ReferenceCountStrip is always preceded by the label *Record References* and the sentence *"how many times this appears in the record. Not a measure of significance, involvement or responsibility."* The disclaimer is part of the component, not the page.

### DirectionBadge
`↑ Supports` · `↓ Contradicts` · `~ Qualifies` · `— Neutral`.

**Constraint.** Always rendered with ScopeNote in view, stating that direction is measured against the claim in the same row, not against any person.

### EvidenceMatrix
Source · Claim · Direction · Court cited? · Verification. Rows with `Contradicts` get a subtle warm row tint (`#160F10`) to aid scanning — this is a readability affordance, not a severity signal, and applies to the row's *direction label*, never to a person.

### SourceAuditTable
Citations resolved · Human verified · Unresolved citations · Redacted in public text. Four rows, tabular, colour-coded by health.

---

## 4. RECORD CONTENT

### DocumentPage
Light-mode page: `600px` column, `52px 60px` padding, `0 2px 12px rgba(0,0,0,.1)` shadow, running head and page number, Libre Baskerville at 12.5px / 1.75.

Sub-parts: ParagraphAnchor (addressable `¶` numbers), CitedBanner (amber, *"Cited in Finding Fxxxxx"*), FootnoteBlock, RedactionBlock.

**Constraint.** Redactions render as visible blocks with their extent, never as removed text.

### TestimonyCard
Q/A in Libre Baskerville with `Q.` / `A.` markers in 10px DM Sans 700 muted. Header carries the transcript range and any "Cited in" badge. Footer carries citation chips and verification state.

### SourceQuoteCard
Verbatim excerpt with a 3px source-coloured left border, a source identity line, and a citation chip. Used in Finding Detail step 03.

**Constraint.** Verbatim only. Paraphrase is never rendered in this component.

### PlainLanguageBlock + LegalTermTooltip
Public-mode pair. Legal terms carry a dotted `--l-accent` underline; the tooltip gives a plain definition, the governing article, and "Learn more".

**Constraint.** A PlainLanguageBlock is never rendered without the OriginalTextBlock it describes, on the same screen, at the same time.

---

## 5. ENTITY

### PersonHeader
Hexagon avatar · name at 25/700 · role badges · public-role line · alias chips · QuickActionBar (View Network · View Timeline · Find Record Connection · Ask AI).

### WitnessHeader — two states
**Protected:** ProtectedAvatar (dashed circle, neutral figure glyph), W-code at 23/700 in `--witness`, `Protected Witness` badge, the withholding sentence, protective-measure chips.
**Public:** solid circle with initials, name at 23/700, `Public Witness` badge, W-code secondary, stated occupation and calling party.

**Constraint.** The protected variant never renders a name field, an image slot, or any biographical attribute — the markup for them does not exist in that variant.

### IncidentHeader
Triangle glyph · incident name with date · `Incident` badge · ID · event date range · location · charge chips.

**Constraint.** Charge chips carry *"as charged in the Indictment — not a determination."*

---

## 6. GRAPH

### NodeShape — eight types
Hexagon (Accused) · solid circle (Public witness) · **dashed circle (Protected witness)** · pill (Court finding) · rectangle (Document/exhibit) · triangle (Incident) · diamond (Location) · clasped rectangle (Organisation).

**Constraint.** Shape carries type independently of colour. Selected nodes get an outer ring, never a fill change that could read as emphasis or severity.

### EdgeLine / EdgeInspector
Edges are coloured by the source type that created them, with arrow markers for directional references.

EdgeInspector is headed **"Why does this connection exist?"** and shows the source, the exact citation, the verification state and the date.

**Constraint.** Every edge resolves to a citation. An edge with no citation is not drawn. The legend footer and a canvas watermark both carry *"Connections represent relationships or references found in the public court record. A connection does not by itself imply wrongdoing, agreement, responsibility or guilt."*

### NetworkPreview
Static 270×172 mini-graph used in dossier rails, with the neutrality line beneath at 8px.

---

## 7. TIME

### DualEraAxis
Splits at 44% into *Events 1998–1999* and *Proceedings 2020–2026*, divided by a 2px dashed rule. Independent scales per era.

**Constraint.** The two eras are never rendered on one linear scale. Zoom rescales them independently.

### TimelineEvent
Typed glyph + label pill. Five date types, each with its own glyph:

| Type | Glyph |
|---|---|
| Event date | red diamond (rotated square) |
| Document date | amber square |
| Filing date | amber square, outlined |
| Testimony date | cyan circle |
| Decision date | indigo square |

**Constraint.** A card is drawn on the lane for its own date type. Other dates attached to the same record are listed in AttachedDatesTable in the detail rail — never merged into one date.

### TypedDateTimeline
Vertical variant used in dossier rails. Each entry states its date type explicitly (`· Filing date`, `· Decision date`).

---

## 8. SEARCH

### CommandPalette
`660px`, 13px radius, heavy shadow plus a 1px accent ring, over a `rgba(6,10,18,.72)` scrim on a blurred page.

Sections: scoped-pattern hint · Best Match · category groups · Actions · keyboard footer.
Keys: `↑↓` navigate · `↵` open · `⌘↵` open in network · `tab` filter · `esc` close.

### QueryInterpretation
Shows how the query was parsed, what it matched as, and which recorded variants are being searched (e.g. Qirez / Çirez / Cirez / Ćirez).

**Constraint.** Always visible on the results page, including on zero results — it is how a user diagnoses an empty search.

### ResultRow
Entity glyph · title · type badge · metadata · context excerpt with MatchHighlight · citation chip · typed date.

**Constraint.** Every row opens an underlying source, never a generated summary standing in for one. The results footer carries *"Result ordering reflects textual relevance and record density only. It carries no assessment of any person or of the weight of any evidence."*

### FilterRail
Category counts · date range (labelled as applying to the **event** date) · source type · verification · text availability.

---

## 9. ANALYSIS

### IssueCard
Expanded form carries six labelled sections: Court Reasoning at Issue · Trial Defence Position · SPO Position · Evidence Relied Upon · Potential Contrary/Qualifying Evidence · Missing Material. Plus category badge, human review state, judgment paragraphs and finding reference.

**Constraint.** No probability, likelihood, strength or ranking field exists on this component. Sort is judgment order only.

### ComparisonColumn + DifferenceSpan
Three-column comparison. Difference spans are marked with an amber underline and tint (`#2A2208` / `#FBB035`) — a neutral "look here" marker, not a severity signal.

### LabelPicker
Five labels: Consistent · Possible Contradiction · Qualification · Timeline Difference · Not Comparable.

**Constraint.** `Not Comparable` is a first-class state so that silence in one source is never rendered as a difference.

### ArgumentEditor
Inline citation chips in flowing prose; uncited substantive sentences get a dashed red underline and an `Unsupported assertion` / `No citation` badge.

**Constraint.** The editor flags *absence of citation*. It never evaluates whether the argument is correct, and no such affordance may be added.

### StageStepper + NeutralReviewRow
Three stages: Defence Analyst → SPO Red Team → Neutral Reviewer.

NeutralReviewRow categories: Unsupported · Missing Citation · Ignored Evidence · Unanswered · Factual Dispute · Legal Question · Well Supported · Human Required. Each row carries citation chips.

**Constraint.** `Legal Question` rows explicitly decline to answer and say so: *"This system does not answer it. Consult qualified counsel."*

### PotentialIssueBlock
Dashed AI container used in the Finding Detail right rail. Carries the `AI Analysis` badge, per-issue category badges, `Needs human review` state, and the footer *"No success score, probability, or outcome estimate is produced."*

**Naming.** This component replaced the Phase 1 "appeal risk indicator". The words *risk*, *likelihood*, *strength* and *chance* must not appear in it or any successor.

---

## 10. CHAIN

### ChainSpine + ChainStepMarker
A 1px vertical rule with 22px numbered circular markers, each tinted to its section's source type. Used on Finding Detail to make the evidence chain one continuous object rather than a stack of cards.

### EvidenceRow
Type badge (fixed 96px) · reference (fixed 60px, source-coloured, tabular) · description (flex, single-line ellipsis) · extent · open arrow.

### DirectionCountCard
Supporting / Contrary / Qualifying / Neutral count cards, each border-tinted to its direction colour.

**Constraint.** Always accompanied by ScopeNote.

---

## 11. PATH — artboard 20

### EntityPicker
`From` and `To` slots, each showing the entity's node glyph, label and a clear control, separated by a bidirectional arrow. Max-hops segmented control (1/2/3) and a primary *Find path* action.

Props: `from`, `to`, `maxHops`, `onFind`.
**Constraint.** Either slot can be empty; the action is disabled until both are filled. Arriving from a dossier pre-fills `from` only.

### PathCanvas / PathNode / PathEdge / HopMarker
Horizontal chain: endpoint nodes at each end, intermediate nodes between, edges coloured by the source type that created them, and a numbered `HopMarker` circle centred on each edge.

Nodes reuse the eight `NodeShape` types; the destination node carries an outer selection ring. Each node has a label and a type sublabel beneath it.

**Constraint.** The protected-witness dashed circle is used unchanged here. The canvas footnote states that shape carries type independently of colour and that a dashed circle holds no identity.

### HopInspectorRow
One row per hop: numbered marker · `fromNode` → relation → `toNode` · source badge · verification badge · optional verbatim excerpt in Libre Baskerville · citation chip · date line with date type named.

Props: `hop`, `expanded`, `onOpenSource`.
States: collapsed · expanded (first hop expanded by default) · unverified (verification note shown in amber).

**Constraint.** Every hop renders its own citation chip. A hop whose source fails to load keeps the chip visible so the user can open it manually — the path is not discarded.

### PathCompositionTable
Hops · citations backing them · human verified · intermediate node types.

### AlternatePathList
Other paths found, each with hop count, the refs it goes via, and a one-line summary.

**Constraint.** Ordered by **hop count only**, and the list is introduced with *"Ordered by hop count only. A shorter path is not a stronger one."*

### CannotTellYouCard
Three ✕ statements and one ✓ statement, fixed copy:

> ✕ That the two entities are connected in any real-world sense
> ✕ That either knew of, or is answerable for, the other
> ✕ That a shorter path is more significant than a longer one
> ✓ That these documents each mention the item next to them, at the pages cited

**Constraint.** Required on the Evidence Path screen. Not optional, not collapsible.

---

## 12. STATES

### SkeletonBlock
Matches the final layout's rails, card outlines and row heights so nothing reflows on arrival.

### EmptyState
Three lines: what is absent · **why it may be absent** · one action.

**Constraint.** The middle line is required and must be specific. *"The public version of this document is redacted at these pages"* and *"No records match these filters"* are different empty states and are never collapsed.

### GapNotice
Dashed-border card naming material the system does not hold — closed session ranges, redactions, untranslated documents, unresolved citations.

**Constraint.** Gaps are stated, never filled. The system does not supply text it does not hold, does not machine-translate court documents in place, and does not infer redacted content.

### ErrorState
Names the failing scope and offers an action. Partial data renders with the gap marked rather than failing the whole view. Never "Something went wrong."

---

## COMPONENT RULES SUMMARY

Nine rules that survive every screen, every breakpoint and both languages:

1. A citation chip always resolves to a page, paragraph or line range — or it is not rendered.
2. Record material and generated analysis are separated by four independent signals.
3. Protected witness surfaces fail closed and carry no identity-bearing markup.
4. No component has a field for a score, rank, rating or weight of any person.
5. Direction labels are scoped to a stated claim and always shown with their scope note.
6. Network edges without a citation are not drawn.
7. Date types are never merged.
8. Badges and labels size to content and wrap; nothing truncates in Albanian.
9. Gaps in the record are rendered explicitly and never filled.
10. Evidence paths decompose — every hop carries its own citation, and paths are ordered by hop count and nothing else.
