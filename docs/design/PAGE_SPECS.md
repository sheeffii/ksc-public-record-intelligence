# PAGE_SPECS.md
### KSC Public Record Intelligence — per-screen specification

21 artboards. Every screen is specified as: **Purpose · Route · Layout · Components · Data requirements · Interactions · Desktop behavior · Mobile behavior · Loading · Empty · Error.**

Routes and query params: `ROUTE_MAP.md`. Components: `COMPONENTS.md`. Rationale: `DESIGN_DECISIONS.md`.

---

## PAGE INVENTORY

| # | Artboard | Size | Mode | Route | Status |
|---|---|---|---|---|---|
| 01 | Design System | 1440×920 | Dark | — | Reference |
| 02 | Homepage | 1440×960 | Dark | `/` | Authoritative |
| 03 | Network Explorer | 1440×900 | Dark | `/network` | Authoritative |
| 04 | Document Reader | 1440×900 | **Light** | `/documents/:id` | Authoritative |
| 05 | Finding Detail | 1440×1100 | Dark | `/findings/:id` | Authoritative |
| 06 | Global Search | 1440×1040 | Dark | `/search` | Authoritative |
| 06b | ⌘K Overlay | 1440×900 | Dark | modal | Authoritative |
| 07 | Person Dossier | 1440×1040 | Dark | `/people/:slug` | Authoritative |
| 08 | Witness Dossier | 1440×1080 | Dark | `/witnesses/:code` | Authoritative |
| 09 | Statement Comparison | 1440×980 | Dark | `/witnesses/:code/compare` | Authoritative |
| 10 | Evidence Explorer | 1440×1000 | Dark | `/exhibits` | Authoritative |
| 11 | Incident Detail | 1440×1020 | Dark | `/incidents/:id` | Authoritative |
| 12 | Research Timeline | 1440×940 | Dark | `/timeline` | Authoritative |
| 13 | Appeal Research | 1440×1020 | Dark | `/appeal` | Authoritative |
| 14 | Argument Lab + Red Team | 1440×1060 | Dark | `/appeal/argument/:id` | Authoritative |
| 15 | AI Research | 1440×1060 | Dark | `/ai` | Authoritative |
| 16 | Public / Simple Mode | 1440×980 | **Light** | `/public` | Authoritative |
| 17 | Mobile — 390px | 1760×980 | Both | — | Authoritative (4 frames) |
| 18 | Language — EN / Shqip | 1440×900 | Dark | — | Reference |
| 19 | Flow Audit A–F | 1760×1100 | Dark | — | Reference |
| 20 | Evidence Path | 1440×980 | Dark | `/network/path` | Authoritative |

---

## GLOBAL STATES

Apply to every screen unless overridden.

**Loading.** Skeleton blocks matching the final layout — rails, card outlines, row heights drawn immediately so nothing reflows on arrival. Never a full-page spinner. Counts render as a dimmed `—` until resolved, **never as `0`**, because `0` is a meaningful value in this product.

**Empty.** Three lines: what is absent · **why it may be absent** · one action. The middle line is required and must be specific. *"The public version of this document is redacted at these pages"* and *"No records match these filters"* are different states and are never collapsed.

**Error.** Names the failing scope, offers an action. Partial data renders with the gap marked rather than failing the whole view. Never "Something went wrong."

**The gap rule.** Closed sessions, redactions, unresolved citations and untranslated documents are rendered explicitly with their extent. Nothing is inferred, reconstructed, machine-translated or silently dropped.

**Chrome.** Every screen carries GlobalNav (52px) with the EN/SQ toggle, and every screen showing a figure carries the DemoDataFlag.

---

## 01 · DESIGN SYSTEM — reference

**Purpose** Token, type, badge, chip, nav, verification and node-shape reference.
**Route** — · **Layout** Header + three columns.
**Components** All. **Data** None — static.
**Interactions / Desktop / Mobile / Loading / Empty / Error** N/A.

---

## 02 · HOMEPAGE

**Purpose** Orient a first-time visitor, offer search, expose the eight sections, show ingestion health.
**Route** `/`
**Layout** Nav 52 · case stripe 32 with DemoDataFlag · hero (title, subtitle, large search, quick-search pills) · mock-data notice strip · 7-stat row · 8-card explore grid · 3-panel row.
**Components** GlobalNav · CaseStripe · DemoDataFlag · SearchField(large) · QuickSearchPill · StatCell · ExploreCard · RecordListItem · ProgressBar · LanguageToggle.

**Data requirements**
```
caseMeta      { id, court, lastIndexedAt, recordCount }
counts        { documents, transcriptPages, witnesses, exhibits,
                findings, incidents, citationsResolved }   ← live COUNT()
recentAdded   [{ id, type, title, addedAt }]               limit 5
recentFindings[{ id, ref, title, verifiedState }]          limit 5
ingestion     [{ source, state, processed, total }]
```

**Interactions** Search submits to `/search`; ⌘K opens 06b; explore cards route to their sections; stat cells link to the filtered directory behind them.
**Desktop** Stats in a single 7-column row; explore grid 4×2.
**Mobile** Stats 2×4 grid; explore cards single column; hero search full-bleed; bottom tab bar replaces nav (see 17 frame 1).
**Loading** Stats as dimmed `—`; explore cards render immediately (static); recent panels skeleton 3 rows each.
**Empty** Before first ingestion: stats show `—`, ingestion panel names pending sources, no explore card is disabled.
**Error** A failed stat shows `—` with a tooltip naming the failure; the rest of the page is unaffected.

---

## 03 · NETWORK EXPLORER

**Purpose** Explore source-backed relationships between record entities.
**Route** `/network?focus=&depth=&layers=&sel=&seledge=`
**Layout** Nav · toolbar (search, Find Connection, Layout, Depth 1/2/3, Filters, Save View, Export, Fullscreen, EN/SQ) · legend rail 220 · SVG canvas · inspector 280.
**Components** NetworkCanvas · NodeShape(8) · EdgeLine · EdgeTooltip · LegendPanel · DateRangeSlider · VerificationFilter · NodeInspector · EdgeInspector · Minimap · ZoomControls · NeutralityDisclaimer(×2).

**Data requirements**
```
nodes  [{ id, type, label, protected:bool, shape, counts:{docs,findings,incidents} }]
edges  [{ id, from, to, sourceType, citation:{docId,page,para,lines},
          verifiedState, date, dateType }]
```
Every edge **must** carry a resolvable `citation`. An edge without one is not returned by the API and not drawn.

**Interactions** Click node → inspector; click edge → EdgeInspector headed *"Why does this connection exist?"* with the citation; double-click → re-centre; drag pan; scroll zoom; Find Connection → `/network/path`.
**Desktop** Three regions side by side; graph gets the remaining width.
**Mobile** Canvas full-bleed; floating search and filter buttons; inspector becomes a three-detent bottom sheet (peek/half/full) — see 17 frame 3.
**Loading** Focus node renders first, then expands by depth with a chip reading *"resolving depth 2 of 3"*.
**Empty** Node with no edges at current depth: node alone plus *"No connections in the record at depth 1. Try depth 2."*
**Error** Last successful view retained with a banner; zoom and pan stay live.

---

## 04 · DOCUMENT READER — light

**Purpose** Read an original court document at the exact cited page.
**Route** `/documents/:id?page=&highlight=&panel=`
**Layout** LightNav · breadcrumb with type badges · sidebar 240 (metadata, in-doc search, ToC, pager) · document column · research panel 300 (6 tabs).
**Components** LightNav · DocumentBreadcrumb · DocumentMetaTable · TableOfContents · PdfToolbar · DocumentPage · ParagraphAnchor · CitedBanner · FootnoteBlock · RedactionBlock · ResearchPanelTabs · AiAnalysisBlock · CourtFindingCard · WitnessAvatar · ExhibitChip.

**Data requirements**
```
document  { id, title, type, docDate, filingDate, pages, language,
            translationOf?, version, publicState }
page      { number, blocks:[{ para, text, footnotes[] }],
            redactions:[{ from, to, extent }] }
context   { aiSummary?, mentions[], people[], exhibits[], findings[], citations[] }
```

**Interactions** ToC jumps; paragraph anchors addressable and copyable; CitedBanner routes to `/findings/:id`; panel tabs switch without losing scroll; *Copy citation* yields the official citation string.
**Desktop** Three columns; document column fixed 600px, centred.
**Mobile** Sidebar → drawer; research panel → three accordions pinned above a bottom pager; serif body at 11.5px / 1.85 — see 17 frame 2.
**Loading** Page frame and metadata first; text streams; ToC and panel resolve after.
**Empty** A redacted page renders the frame plus *"This page is redacted in the public version"* and the extent — never a blank page.
**Error** Adjacent pages stay navigable; the failed page names itself.

---

## 05 · FINDING DETAIL

**Purpose** One court finding as a traceable evidence chain, finding text through to source audit. The most important screen in the product.
**Route** `/findings/:id?tab=chain|quotes|arguments|annotations`
**Layout** Nav · breadcrumb + DemoDataFlag · rail 236 (numbered index 01–09, related findings) · chain with numbered vertical spine · analysis panel 316 · governance footer 26.
**Chain** 01 Court Finding · 02 Evidence Relied Upon · 03 What Those Sources Say · 04 Other Record Material · 05 Trial Arguments · 06 Court Response · 07 Potential Issues for Review · 08 Red Team · 09 Source Audit.
**Components** ChainSpine · ChainStepMarker · CourtFindingBlock · EvidenceRow · SourceQuoteCard · DirectionCountCard · ScopeNote · VerificationBadge · PotentialIssueBlock · RedTeamPair · SourceAuditTable · GovernanceFooter.

**Data requirements**
```
finding    { id, ref, title, text, paraFrom, paraTo, modeOfLiability,
             counts[], verifiedState, verifiedBy, verifiedAt }
reliedUpon [{ sourceType, ref, label, citation, extent }]        all 18
quotes     [{ sourceType, ref, verbatim, citation, speakerRole? }]
direction  { supporting:int, contrary:int, qualifying:int, neutral:int }
arguments  { spo:[{ text, citation }], defence:[{ text, citation }] }
issues     [{ category, text, reviewState }]                     no score field
audit      { citationsTotal, citationsResolved, humanVerified, redacted }
related    [{ id, ref, title }]
```

**Interactions** Rail scroll-spies the chain; evidence rows open their source; quote chips open the reader at the line range; direction counts open the filtered evidence matrix (`/incidents/:id?tab=evidence&direction=`); *Send to Argument Lab* → 14.
**Desktop** Three regions; chain in the centre at full height.
**Mobile** Spine stacks vertically; section pills at top scroll-spy; right panel content folds into the stack — see 17 frame 4.
**Loading** Finding text → evidence rows → quotes → analysis panel. The chain never renders out of order.
**Empty** No contrary material shows `0` with *"No material in the record tends against this finding as stated"* — stated positively, never left blank.
**Error** Failed section shows its header plus *"This section could not be loaded"*; chain above and below stays intact.

---

## 06 · GLOBAL SEARCH

**Purpose** One query across eight record categories, every result resolving to a source.
**Route** `/search?q=&cat=&from=&to=&src=&verif=&avail=&sort=`
**Layout** Nav · search bar with syntax affordances · result summary · filter rail 238 · grouped results · query panel 262.
**Groups** People · Witnesses · Documents · Transcripts · Exhibits · Incidents · Findings · Locations.
**Components** SearchField · SyntaxHint · FilterRail · GroupHeader · ResultRow · MatchHighlight · CitationChip · QueryInterpretation · SyntaxReference · RelatedEntities · RankingDisclaimer.

**Data requirements**
```
query       { raw, parsedAs, matchedEntityType?, variants[] }
groups      [{ key, total, results:[{ id, type, title, badges[],
                metadata, excerpt, matchRanges[], citation, date, dateType }] }]
facetCounts { perCategory, perSourceType, perVerification, perAvailability }
timingMs    int
```

**Interactions** Group tabs filter in place; filters additive and URL-reflected; every row opens an underlying source; saved searches persist per user.
**Desktop** Three regions; results centre.
**Mobile** Filter rail → drawer; query panel → collapsible under the summary; result rows reflow to two lines with the citation chip on its own line.
**Loading** Group headers with counts first; rows stream per group; summary shows elapsed time.
**Empty** *"No records match."* plus the three filters narrowing most (each individually removable) **plus** the QueryInterpretation panel, so the user can see how their query was read.
**Error** A failed category shows its header plus *"This category could not be searched"*; other categories return normally.

**Syntax** `W#####` · `F#####` · `P#####` · `D#####` · `¶####` · `"exact phrase"` · free text. Place names match across recorded variants and the variant set is shown to the user.

---

## 06b · ⌘K OVERLAY

**Purpose** Keyboard-first navigation from anywhere.
**Route** Modal over any route; `⌘K` / `Ctrl+K`.
**Layout** Scrim over blurred page · 660px palette at y=96 · input · scoped-pattern hint · Best Match · category groups · Actions · keyboard footer with DemoDataFlag.
**Components** CommandPalette · ScopedPatternHint · PaletteRow · KbdChip · PaletteFooter.

**Data requirements**
```
suggestions { bestMatch?, groups:[{ key, rows:[{ id, type, label, sublabel }] }],
              actions:[{ id, label, shortcut?, destination }] }
detectedPattern  enum | null
```

**Interactions** `↑↓` navigate · `↵` open · `⌘↵` open in network · `tab` filter by category · `esc` close. A detected identifier promotes a Best Match row opening the dossier directly.
**Desktop** 660px centred, 96px from top.
**Mobile** Full-width with 16px margins, full-height, virtual keyboard aware.
**Loading** Rows appear per group as each resolves; the input never blocks.
**Empty** *"No match for that."* plus the recognised-pattern reference.
**Error** Failed group omitted with one line naming it; palette stays usable.

---

## 07 · PERSON DOSSIER

**Purpose** Everything the record contains about one named person, with no assessment of them.
**Route** `/people/:slug?tab=`
**Layout** Nav · breadcrumb + DemoDataFlag · person header (hex avatar, name, role badges, public-role line, aliases, 4 quick actions) · *Record References* label + disclaimer · 7-stat row · 10 tabs · content + rail 300.
**Components** PersonHeader · HexAvatar · QuickActionBar · ReferenceCountStrip · ReferenceCountDisclaimer · TabBar · CitedSummaryProse · FindingsTable · TypedDateTimeline · NetworkPreview · ReferenceBreakdown · KeyReferenceCard · NoScoreFooter.

**Data requirements**
```
person    { id, slug, displayName, aliases[], caseRole, publicRoles:[{title,from,to}],
            defenceTeamRef? }
refCounts { documentMentions, transcriptMentions, exhibitRefs, findings,
            witnessesWhoReferred, incidents, citationsResolved }
summary   [{ sentence, citations:[{sourceType, ref, page/para}] }]   every sentence cited
findings  [{ id, ref, title, paraFrom, paraTo, verifiedState, outcome }]  judgment order
dates     [{ date, dateType, label, citation }]
refsByType{ judgment, spo, defence, transcripts, exhibits }
network   { nodes[], edges[] }   depth 1 preview
```
**No score field of any kind exists on this model.** See `DESIGN_DECISIONS.md` §2.

**Interactions** Quick actions → Network, Timeline, `/network/path?from=`, AI Research; findings table sorts by judgment order **only** (no relevance or severity sort is offered); network preview expands to 03 focused here.
**Desktop** Header full-width; content + rail below the tabs.
**Mobile** Stat strip 2-up scroll; tabs a scrolling strip; rail content appended below main content.
**Loading** Header and name first, counts as dimmed `—`, then tables.
**Empty** Low-reference person shows the real low counts plus *"This person appears rarely in the public record"* — never hidden or padded.
**Error** Failed tab errors inside its own panel; header and other tabs remain.

---

## 08 · WITNESS DOSSIER

**Purpose** A witness's evidence, in protected and public states.
**Route** `/witnesses/:code?tab=`
**Layout** Nav · breadcrumb + DemoDataFlag · **two header states side by side** (A Protected — rendered; B Public — reference) · 7-stat strip + Compare / Ask AI · 10 tabs · chronology rail 228 · testimony reader · rail 286.
**Components** WitnessHeaderProtected · WitnessHeaderPublic · ProtectedAvatar · ProtectionNotice · ChronologyRail · ClosedSessionRow · TestimonyCard · TranscriptCitation · ExhibitShownChip · ComparisonFlag · FindingsCitingList · PriorStatementCard · ComparisonStatusPanel.

**Data requirements**
```
witness    { code, protected:bool, protectiveMeasures[],
             public?: { displayName, statedOccupation, expertField?, calledBy } }
```
When `protected` is true the `public` object **must be absent from the payload**, not null-filled. The protected variant has no name field to populate.
```
stats      { sessions, transcriptPages, exhibitsShown, findingsCiting,
             incidents, priorStatements, closedSessionPages }
chronology [{ segmentId, kind: direct|cross|redirect|panel|closed,
              sessionDate, tFrom, tTo, examiner, contentHeld:bool }]
testimony  [{ segmentId, blocks:[{ role:Q|A, text }], citation,
              exhibitsShown[], citedInFindings[], verifiedState, flagged? }]
priorStmts [{ ref, date, pages, disclosureRef, publicState }]
comparison { total, consistent, possibleContradiction, qualification,
             timelineDifference, notComparable }
```

**Interactions** Chronology selects a segment; testimony cards link to transcript line range and to the exhibit shown; flagged cards → 09.
**Desktop** Rail + reader + rail.
**Mobile** Chronology → dropdown; rail content appended; testimony cards full-width.
**Loading** Header and ProtectionNotice first — **never render a witness surface before protection state is known**.
**Empty** No prior statements: *"No prior public statement has been disclosed for this witness"* — silence is stated, never treated as a difference.
**Error** Failed segments marked in the chronology rail; others stay readable. **If protection state cannot be resolved, the screen fails closed to the protected treatment.**

---

## 09 · STATEMENT COMPARISON

**Purpose** Align what the record contains across three settings so a human can judge it.
**Route** `/witnesses/:code/compare?segment=&label=`
**Layout** Nav · header (witness identity + neutrality line) · topic rail 246 · three columns · AI analysis band · review bar · rail 264.
**Columns** A Prior public statement · B Trial testimony · C Cross-examination.
**Labels** Possible Contradiction · Qualification · Timeline Difference · Consistent · Not Comparable.
**Components** ComparisonHeader · TopicRail · ComparisonColumn · DifferenceSpan · CitationBlock · AiAnalysisBand · LabelPicker · ReviewStatusBar · LabelLegend · LanguageRulesCard · CourtCredibilityFindingCard.

**Data requirements**
```
segments  [{ id, topic, label, reviewState, sourceCount }]
segment   { id, topic,
            columns:[{ role:A|B|C, sourceType, title, date, elapsedNote,
                       excerpt, diffSpans:[{from,to}], citation, sessionState }],
            aiAnalysis:{ text, generatedAt },
            courtFinding?:{ verbatim, citation }   ← quoted, attributed, never paraphrased
          }
```

**Interactions** Topic rail selects; `‹ ›` step segments; reviewer sets the label and marks reviewed; every citation opens its source.
**Desktop** Three equal columns.
**Mobile** Single column with an A/B/C segmented control; the AI band and review bar stack below.
**Loading** All three column headers render together; excerpts stream. Never show two of three as though the third does not exist.
**Empty** *Not Comparable* is a first-class state: the column renders with *"Prior statement silent on this topic."*
**Error** A failed source leaves its citation visible with the excerpt replaced, so the reviewer can still open the original.

**Language rule.** *lying · dishonest · false · unreliable* never appear in the system's voice. Where the Chamber made a credibility finding it is quoted, in serif, with a `Court Finding` badge, a paragraph citation, and *"This is the Chamber's assessment, not the system's."*

---

## 10 · EVIDENCE EXPLORER

**Purpose** High-density exploration of the exhibit set.
**Route** `/exhibits?q=&type=&party=&cited=&verif=&density=&sort=&sel=`
**Layout** Nav · toolbar (counts, search, filters, active chips, DemoDataFlag, density toggle, Export) · table · detail panel 376.
**Columns** Exhibit ID · Description · Date · Type · Witnesses · Incidents · Used By · Judgment References · Verification.
**Components** DataTable · TableHeaderSortable · DensityToggle · FilterChip · ExhibitIdCell · TypeBadge · PartyBadge · VerificationBadge · DetailPanel · PagePreview · MetadataTable · LinkedRecordRow · CitationChipGroup · ColumnMeaningFooter.

**Data requirements**
```
rows    [{ id, description, docDate, docDateUncertain:bool, type, party,
           witnessCount, incidentCount, judgmentRefCount, verifiedState }]
detail  { id, description, docDate, admittedDate, party, throughWitness,
          originalLanguage, translationAvailable, pages, redactedPages,
          provenance, preview:{ pageNumber, text, redactions[] },
          linked:{ witnesses[], incidents[], findings[], people[] },
          judgmentCitations:[{ para }] }
page    { total, cursor }
```

**Interactions** Column sort; row selection opens the panel without losing scroll; density persists per table; Export respects active filters **and carries the citation set**; panel *Open full document* → 04 at the cited page.
**Desktop** Table + panel side by side; 12 rows visible at compact density.
**Mobile** Table → stacked cards (ID, description, date, type, verification); detail → full-screen sheet.
**Loading** Header row and column widths immediately; rows stream in pages of 50.
**Empty** *"No exhibits match these filters"* plus the two filters narrowing most, each removable.
**Error** Failed page of rows shows an inline retry row; loaded rows stay interactive.

**Required footer** *"Column values are record attributes. 'Judgment' counts paragraphs citing the exhibit — it is not a weight or an importance score."*

---

## 11 · INCIDENT DETAIL

**Purpose** Everything the record contains about one alleged event, with the evidence matrix as the centrepiece.
**Route** `/incidents/:id?tab=&direction=`
**Layout** Nav · incident header (triangle glyph, name, event date range, location, charge chips, DemoDataFlag, actions) · 9 tabs · evidence matrix · positions rail 340.
**Matrix columns** Source · Claim in the record · Direction · Court cited? · Verification.
**Components** IncidentHeader · ChargePleadedChip · EvidenceMatrix · MatrixRow · DirectionBadge · DirectionScopeNote · CourtCitedCell · CourtFindingCard · PartyPositionCard · WitnessChipCloud · DirectionSummaryBar.

**Data requirements**
```
incident  { id, name, eventDateFrom, eventDateTo, location:{ name, variants[],
            municipality, region }, chargesPleaded:[{ count, label }] }
matrix    [{ sourceType, ref, citation, claim, direction, courtCited:bool,
             courtCitedPara?, verifiedState, note? }]
summary   { supports, contradicts, qualifies, neutral }
findings  [{ id, ref, verbatim, citation }]
positions { spo:{ text, citations[] }, defence:{ text, citations[] } }
witnesses [{ code, protected:bool, displayName? }]
```

**Interactions** Direction and Court-cited filters; sort by direction; rows open their source; tabs URL-addressable. `?direction=` is the entry point from Finding Detail step 04.
**Desktop** Matrix + positions rail.
**Mobile** Positions → tabs; matrix rows become stacked cards with Direction and Verification as a header row.
**Loading** Header and charges first, then matrix header, then rows grouped by direction.
**Empty** No contrary evidence shows `0` with the summary bar still present, so absence is visible rather than implied.
**Error** Failed row shows its source and citation with the claim replaced.

**Required notes** Charge chips: *"as charged in the Indictment — not a determination."* Matrix: *"Direction is measured against the claim in the same row, not against any person."* Footer: *"Listing a person or a charge here records that the material exists — it is not an allegation by this system."*

---

## 12 · RESEARCH TIMELINE

**Purpose** Place record material in time while keeping five date types distinct.
**Route** `/timeline?layers=&from=&to=&person=&witness=&incident=&doc=&card=`
**Layout** Nav · toolbar with active filter chips · date-type legend strip · dual-era axis · 7 lanes · card detail rail 314.
**Lanes** Historical Events · Documents · Hearings · Witness Testimony · Court Decisions · Judgment · Appeal Proceedings.
**Date types** Event (red diamond) · Document (amber square) · Filing (amber outlined square) · Testimony (cyan circle) · Decision (indigo square).
**Components** TimelineToolbar · DateTypeLegend · DualEraAxis · LaneRow · LaneLabel · TimelineEvent · EraDivider · CardDetailPanel · AttachedDatesTable · LinkedFromList · SequenceDisclaimer.

**Data requirements**
```
eras   [{ key, from, to, widthFraction }]     two eras, independent scales
lanes  [{ key, label, visible }]
cards  [{ id, lane, primaryDate, primaryDateType, label, sublabel,
           attachedDates:[{ date, dateType, label }],
           citations[], linked:{ witness?, incident?, document?, finding? } }]
```

**Interactions** Zoom ± rescales each era independently; lane labels toggle layers; filter chips additive; a card opens the rail showing every attached date and which lane it was drawn on.
**Desktop** Horizontal lanes with the dual-era axis.
**Mobile** Vertical list grouped by era, date-type glyphs retained, lane shown as a label on each card.
**Loading** Axis and lanes first, then events per lane.
**Empty** A lane with no events renders the lane plus *"No records in this layer for the selected filters"* — it never collapses, because a missing lane would misrepresent the record.
**Error** Failed lane marked in its label; other lanes render.

**Required notes** *"A document's date and the date it was filed are never merged. Both are indexed separately."* · *"Placing two cards near each other shows only that they carry nearby dates. Sequence in time is not causation."*

---

## 13 · APPEAL RESEARCH

**Purpose** Index points in the Judgment where the record holds material worth examining. Identifies questions; answers none.
**Route** `/appeal?category=&state=&issue=`
**Layout** Nav · header with neutral framing · category rail 236 · issue cards (one expanded) · legal disclaimer strip · rail 276.
**Categories** Evidence Assessment · Error of Law · Error of Fact · Reasoning · Mode of Liability · Procedural Fairness · Sentencing · Other.
**Card sections** Court Reasoning at Issue · Trial Defence Position · SPO Position · Evidence Relied Upon · Potential Contrary/Qualifying Evidence · Missing Material.
**Components** AppealHeader · CategoryRail · ReviewStateSummary · IssueCard · IssueSection · QuotedReasoning · PositionSection · EvidenceChipGroup · ContraryEvidenceList · MissingMaterialBlock · ReviewActionBar · JudgmentCoverageTable · WillNotDoCard · AppealStatusCard · LegalDisclaimerStrip.

**Data requirements**
```
issues  [{ id, category, title, description, paraFrom, paraTo, findingRef,
           courtReasoning:{ verbatim, citation },
           defencePosition:{ text, citations[] },
           spoPosition:{ text, citations[] },
           reliedUpon:[{ sourceType, ref }],
           contrary:[{ direction, sourceType, ref, label }],
           missingMaterial:[{ kind, extent, reason }],
           reviewState: kept|dismissed|awaiting, reviewNote?, closedAt? }]
coverage { paragraphsIndexed, findingsExtracted, citationsResolved, unresolved }
appeal   { status, noticeRef, noticeDate, orders[] }
```
**Prohibited fields, permanently:** `probability`, `likelihood`, `successScore`, `strength`, `rank`, `priority`. Sort is judgment order only.

**Interactions** Category filters; cards expand in place; *Send to Argument Lab* → 14; reviewers mark reviewed or dismiss with a note.
**Desktop** Rail + cards + rail.
**Mobile** Category rail → dropdown; card sections stack single-column; the *What this screen will not do* card stays, it is not an optional extra.
**Loading** Category counts first, then cards in judgment order.
**Empty** *"No issues surfaced in this category"* plus a line explaining this reflects the pattern-matching pass, not a judgment that none exist.
**Error** Failed card renders its judgment paragraph reference so the reviewer can go to the Judgment directly.

---

## 14 · ARGUMENT LAB + RED TEAM

**Purpose** Draft an argument, then test it against the record from three perspectives.
**Route** `/appeal/argument/:id?stage=`
**Layout** Nav · header with draft status · top region 388 (editor + actions 292) · three-stage region (stepper + three columns).
**Actions** Research Support · Find Contrary Evidence · Check Citations · Find Defence Position · Find SPO Response · Find Court Response · Red Team This Argument · Generate Neutral Review.
**Stages** 1 Defence Analyst → 2 SPO Red Team → 3 Neutral Reviewer.
**Neutral categories** Unsupported · Missing Citation · Ignored Evidence · Unanswered · Factual Dispute · Legal Question · Well Supported · Human Required.
**Components** ArgumentEditor · InlineCitationChip · UnsupportedSpan · CitationHealthPanel · ResearchActionList · StageStepper · StageSummaryCard · NeutralReviewRow · SuggestedCitationChip · StageActionBar.

**Data requirements**
```
draft   { id, title, blocks:[{ text, citations:[{sourceType,ref,citation}],
          unsupportedSpans:[{from,to,kind}] }], wordCount, savedAt, seededFrom? }
health  { citations, resolving, quotationVerified, unsupportedSentences }
stages  [{ stage:1|2|3, state, findings:[...] }]
stage3  [{ category, text, citations[], suggestedCitation? }]
```

**Interactions** Editor flags uncited sentences as you type; actions return annotations **without modifying the draft**; stages independently re-runnable; *Compare stages* diffs findings; suggested citations applied individually.
**Desktop** Editor + actions above; three stage columns below.
**Mobile** Actions collapse under the editor; stage columns become a tabbed set.
**Loading** Editor live immediately; per-stage progress in the stepper.
**Empty** No citations yet: health panel all zeros plus *"No citations yet — every substantive sentence should resolve to a source."*
**Error** Failed stage marked in the stepper; other stages' results retained.

**Required notes** *"The editor flags sentences with no supporting citation as you write. It does not evaluate whether the argument is correct."* · *"The neutral reviewer reports gaps between the draft and the record. It does not say whether the argument should be made, nor predict how any court would receive it."*

---

## 15 · AI RESEARCH

**Purpose** Answer a research question from the indexed record, structured by source type, with the record/AI boundary structurally unmistakable.
**Route** `/ai` · `/ai/:sessionId?q=&cite=`
**Layout** Nav · session rail 214 · answer column · sources rail 292.
**Answer order** Court Finding → Record Evidence → Witness Testimony → SPO + Defence Position → **boundary divider** → AI Analysis.
**Components** SessionRail · QuestionHeader · ScopeChip · RecordBlock · BoundaryDivider · AiAnalysisBlock · InlineCitationChip · CitationPreview · SourcesUsedList · CitationStatusTable · VerificationStatusCard · NotAvailableCard · AnswerActionBar.

**Data requirements**
```
session  { id, question, scope, createdAt }
retrieval{ sources:[{ sourceType, ref, citation, verifiedState }], count }
answer   { blocks:[{ kind: court|evidence|testimony|spo|defence|ai,
                     text, citations[] }] }
status   { citationsProduced, citationsResolved, quotationsMatched,
           unresolved, humanVerified, unreviewed }
gaps     [{ kind: closed-session|redaction|untranslated, ref, extent, reason }]
```
`kind: ai` blocks render in AiAnalysisBlock and **must** sit after the boundary divider. The API returns block order; the client does not reorder.

**Interactions** Every chip opens CitationPreview **first** (answer stays on screen), then the document; *View as Evidence Graph* hands the source set to 03; *Create Argument* seeds 14.
**Desktop** Three regions; answer centre.
**Mobile** Session rail → drawer; sources rail → accordion below the answer. **Record blocks and the AI block keep their distinct treatments at every width — the boundary is never dropped for space.**
**Loading** Sources retrieved and listed **before any answer text renders**.
**Empty** If the record holds nothing: no answer is composed; the screen states which categories were searched and that nothing matched.
**Error** **An answer containing a citation that does not resolve is not rendered at all.** The gap is reported instead. A hard product rule, not a degradation path.

---

## 16 · PUBLIC / SIMPLE MODE — light

**Purpose** Let a non-specialist understand the case without simplifying the evidence.
**Route** `/public` · `/public/:topic`
**Layout** LightNav with Simple/Research toggle and EN/Shqip · hero + *Before you begin* · six entry cards · worked example (finding explained, inline term tooltip, original text beneath) · *What this finding does not mean* · *Where this finding came from* · footer.
**Components** LightNav · ModeToggle · LanguageToggle · BeforeYouBeginCard · EntryCard · PlainLanguageBlock · LegalTermTooltip · OriginalTextBlock · DoesNotMeanList · WhereItCameFromList · OtherSideCallout · PublicFooter.

**Data requirements**
```
entryCards [{ key, title, blurb, count, route }]
explained  { findingId, plainTitle, plainText,
             terms:[{ term, definition, statuteRef, learnMoreRoute }],
             originalText, citation,
             doesNotMean:[string],
             provenance:{ witnesses, documents, priorFindings },
             otherSide:{ blurb, route } }
```
`plainText` is authored/reviewed content keyed to `findingId`, **not** generated at request time.

**Interactions** Dotted-underline terms open a tooltip with definition, governing article and *Learn more*; the mode toggle swaps rendering of the same entity routes; every card routes to the full section.
**Desktop** Six cards in one row; worked example two-column.
**Mobile** Cards single column; worked example stacks; tooltips become bottom sheets.
**Loading** Static content immediately; counts as dimmed `—`.
**Empty** Entry cards always render; a section with no data says so on its own page rather than hiding the card.
**Error** Plain-language failures fall back to the original court text — **never the reverse**.

**Hard constraint** Plain-language text never replaces the record. Every simplified passage is shown together with the official text. *What this finding does not mean* and *There was also evidence pointing the other way* are required parts of the pattern.

---

## 17 · MOBILE — 390px

**Purpose** Prove the IA and the provenance rules survive at phone width.
**Frames** Home & Search · Document Reader (light) · Network + bottom sheet · Finding Detail stacked.

**Rules**
- Top nav → five-item bottom tab bar (Home · Search · Network · Docs · AI). Case identifier and DemoDataFlag stay pinned under the header.
- Document Reader: serif body 11.5px / 1.85; three desktop context panels become accordions pinned above the pager.
- Network: canvas full-bleed; floating search and filter; inspector is a three-detent bottom sheet.
- Finding Detail: numbered spine stacks vertically; section pills scroll-spy.
- Touch targets ≥44px. Type floor 10px labels, 11px body.

**Preserved at 390px** Source colours · badge semantics · citation chips · the dashed AI container · the protected-witness treatment · the network neutrality disclaimer.
**Loading / Empty / Error** As desktop; sheets show their own inline states rather than replacing the canvas.

---

## 18 · LANGUAGE — EN / Shqip — reference

**Purpose** Specify the language system and prove the layout survives Albanian string lengths.
**Contents** Collapsed and open selector · document-language panel · never-translated identifier set · nav at both lengths (498px EN → 706px SQ, +42%) · the same Finding card in both languages · layout rules · EN→SQ glossary.
**Data** `uiStrings` keyed by locale; `document.originalLanguage` / `translationOf` per document.
**Layout rules** Nav items 11px padding, no fixed width. Badges `min-width`, wrap not truncate. Card titles two lines at every breakpoint. Table minimums from the **longest** translation. No label centred in a fixed pill. Below 1280px in SQ the nav overflows rather than truncating.
**Never translated** `KSC-BC-2020-06` · `W01234` · `P00441` · `F02219` · `F00482` · `¶1,204` · `T. 4,226`.
**Open item** Albanian strings are design placeholders; legal terminology must be reviewed against the Chambers' published Albanian texts before release.

---

## 19 · FLOW AUDIT A–F — reference

**Purpose** Verify every required workflow resolves and record the fixes produced.
**Audit rule** Every hop reachable from a control visible on the preceding screen without scrolling past the fold, and the final hop lands on a page of an actual public record.
**Result** All six resolve. Two fixes applied — see `UX_FLOWS.md`.

---

## 20 · EVIDENCE PATH

**Purpose** Show how two entities are connected in the record, decomposed so every hop is separately checkable.
**Route** `/network/path?from=&to=&maxhops=&alt=&hop=`
**Layout** Nav · entity picker (From / To / max hops / Find path / DemoDataFlag) · constraint banner · path canvas 238 · hop inspector list · rail 322 · footer 26.
**Components** EntityPicker · PathCanvas · PathNode · PathEdge · HopMarker · HopInspectorRow · PathCompositionTable · AlternatePathList · CannotTellYouCard · NeutralityDisclaimer.

**Data requirements**
```
path      { hops:[{ index, fromNode, toNode, relationLabel, sourceType,
                    citation:{docId,page,para,lines}, verbatim?,
                    verifiedState, docDate, dateType, admittedDate?, party? }],
            nodes:[{ id, type, label, sublabel, protected:bool }] }
alternates[{ index, hopCount, viaRefs[], summary }]
composition{ hops, citationsBacking, humanVerified, intermediateTypes }
```
Every hop **must** carry a resolvable citation. A path containing an unresolvable hop is not returned.

**Interactions** Picker swaps either entity; max-hops 1/2/3; *Find path* recomputes (paths are never cached by URL); clicking a hop expands its inspector row; any hop opens the document behind it; alternates are selectable; *Open in Network* hands the node set to 03.
**Desktop** Canvas above, hop list below, rail right.
**Mobile** Canvas becomes a vertical chain; hops stack as cards; alternates and the constraint card move below.
**Loading** Picker live immediately; canvas shows the two endpoints with a *searching* state between them; hops populate in order.
**Empty** *"No source-backed path within 3 hops"* plus a control to raise the limit and a note that no path may exist in the public record.
**Error** A hop whose source fails keeps its citation visible so the user can open it manually; the path is not discarded.

**Required copy** Banner: *"These records reference one another. That is all a path shows."* Footer: *"No path is scored, weighted or ranked by anything other than hop count."* Plus the *What a path cannot tell you* card.

---

## SCREENS NOT YET DESIGNED

Five directory routes referenced by designed screens. None needs new components or new semantics.

| Route | Build from |
|---|---|
| `/people` | Evidence Explorer table (10), person columns |
| `/witnesses` | Table (10) + protected treatment from 08 |
| `/documents` | Table (10), document columns |
| `/incidents` | Table (10) or cards using header pattern from 11 |
| `/findings` | The findings table from 07, promoted to full page |
