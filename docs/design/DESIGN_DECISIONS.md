# DESIGN_DECISIONS.md
### KSC Public Record Intelligence — decisions, rationale, and what was rejected

This document records *why* the design is the way it is, so that future changes are made with the reasoning in view rather than against it.

---

## 1. Why colour encodes source, not severity

**Decision.** Every colour in the semantic palette answers "where did this come from?" — court, witness, prosecution, defence, document, software. No colour answers "how bad is this?"

**Rejected.** The obvious dashboard convention — red for high-severity, green for clear, amber for caution — applied to people, findings or evidence.

**Why.** A severity palette applied to a criminal case does the thing the product exists not to do. If an accused person's node were red and a witness's node green, the interface would be asserting something the record does not say, on every screen, permanently, without a citation. Once severity colour exists anywhere, every new feature inherits the temptation to use it.

**Consequence engineering must preserve.** Red (`#F87171`) appears in exactly two roles: the `Contradicts` direction label and the Incident node shape. Both are neutral record classifications. Red is never bound to a person, and `--incident` and `--unresolved` are kept as separate tokens even though the hex currently matches, so neither can drift into the other's meaning.

---

## 2. Why there is no score of any kind

**Decision.** No guilt score, suspicion score, importance score, centrality score, culpability score, relevance-to-the-case score, appeal-strength score or success probability exists anywhere in the product.

**Rejected.** Network centrality as a visual weight; "most important witnesses"; sorting findings by significance; an appeal-ground strength rating.

**Why.** Each of these is a quantitative assertion about a person or about the merits, produced by software, that no court made. They would be read as authoritative precisely because they are numeric. The problem is not that a score would be inaccurate — it is that a score would be a conclusion, and this product does not draw conclusions.

**Consequence.** There is **no field in the data model** for such a value. This is deliberate defence in depth: a future feature cannot accidentally render a score that does not exist. Counts that do exist are reference counts, and the component that renders them (`ReferenceCountStrip`) carries its own disclaimer so the disclaimer cannot be dropped by a page author.

**What replaced ranking.** Judgment order. Findings, issues and evidence are listed in the order the court addressed them. It is the one ordering the record itself supplies.

---

## 3. Why "Potential Issues for Review" replaced "appeal risk"

**Decision.** Every appeal-adjacent surface uses *Potential Issues for Review*. The words *risk*, *strength*, *likelihood*, *chance* and *probability* do not appear.

**Why.** "Appeal risk" implies the software has modelled an outcome. It has not, and it should not — an outcome model would be a prediction about a live proceeding, produced without access to closed-session material, presented to people who may act on it. Naming the feature after the thing it actually does (surfacing places in the Judgment where the record holds material worth examining) also constrains what it can grow into.

**Reinforcement on screen.** Artboard 13's right rail carries an explicit *"What this screen will not do"* card listing the four prohibitions — estimate probability, rank by strength, recommend grounds, state that the Panel erred — against the one thing it does: show where the record holds material bearing on a stated point, with citations.

---

## 4. Why the record/AI boundary uses four signals, not one

**Decision.** Record material and generated analysis are separated by container, border style, colour, and a labelled divider — simultaneously.

**Rejected.** A single "AI" badge, or an italic typeface, or a colour tint alone.

**Why.** Any single signal fails for someone. A badge is missed by a user scanning quickly. Colour fails for colour-blind users and in print. Italics fail at small sizes. A divider alone fails if the user enters mid-page from an anchor link. Four independent signals mean that losing any one still leaves three.

This is the highest-stakes design decision in the product. A user who mistakes a generated paragraph for a court finding, and repeats it, has been actively misled by the interface.

**Consequence.** The boundary is never dropped for vertical space, including at 390px. `RecordBlock` and `AiAnalysisBlock` never nest and never share a container.

---

## 5. Why the AI answer retrieves sources before it writes

**Decision.** On Artboard 15, the eighteen sources are retrieved and listed in the right rail **before** any answer text renders.

**Why.** It makes the provenance ordering visible as a sequence, not just a claim: the user watches the system gather the record, then compose over it. It also makes the failure mode legible — if retrieval returns little, the user sees that before reading a confident-sounding paragraph.

**Paired hard rule.** An answer containing a citation that does not resolve is not rendered at all. The gap is reported instead. A partially-verifiable answer is more dangerous than no answer, because the resolvable citations lend credibility to the unresolvable one.

---

## 6. Why protected witnesses have no identity markup at all

**Decision.** The protected variant of `WitnessHeader` does not contain a name field, an image slot, or any biographical attribute. Not hidden — absent from the markup.

**Rejected.** A single component with fields conditionally hidden by a `isProtected` flag.

**Why.** Conditionally hidden fields leak. They appear in DOM inspection, in exports, in print styles, in screen-reader output, in a future refactor where someone inverts a boolean. Two separate variants cannot leak what they do not contain.

**Fail-closed rule.** If protection state cannot be resolved, the surface renders the protected treatment. The failure mode of an error is over-protection, never under-protection.

**Also enforced.** Search does not resolve a name to a witness code. The `ProtectionNotice` component states this to the user explicitly, because a researcher who knows the system will not do it is less likely to attempt it elsewhere.

---

## 7. Why the timeline has two eras and five date types

**Decision.** The timeline splits at 44% into *Events 1998–1999* and *Proceedings 2020–2026*, with independent scales. Five date types — event, document, filing, testimony, decision — each carry their own glyph and are never merged.

**Rejected.** A single linear axis from 1996 to 2026.

**Why.** On one linear scale, the eighteen months of events that the case is *about* compress to roughly five percent of the width and become unusable, while two decades of procedural history dominate. The dashed era divider is more honest than a continuous line that is effectively lying about proportion.

The five date types matter because conflating them produces false chronology. A document written on 28 April 1999, filed on 9 February 2024, spoken to on 14 March 2024, and cited in a decision on 16 May 2025 has four different dates, and a researcher who reads the filing date as the event date has misunderstood the record. One card can sit on several dates; it is drawn on the lane for its own type and the others are listed in the detail rail.

**Stated on screen.** *"Placing two cards near each other on the timeline shows only that they carry nearby dates. Sequence in time is not causation."*

---

## 8. Why direction labels are scoped to a claim, not a person

**Decision.** `Supports` / `Contradicts` / `Qualifies` / `Neutral` are always measured against the specific claim in the same row, and every surface showing them carries a note saying so.

**Why.** Without scoping, "12 supporting, 3 contrary" reads as a tally about a person — as though the record were a scoreboard. Scoped to a stated claim, the same numbers are a map of where to read next. The difference is entirely in the framing, which is why the framing is a required part of the component rather than page copy.

**Also.** The counts are shown for supporting *and* contrary *and* qualifying *and* neutral, always together. Showing only supporting material would be advocacy.

---

## 9. Why light mode means "the record itself"

**Decision.** Only two screen families are light: the Document Reader and Public/Simple mode. Everything else is dark.

**Why.** The split is semantic, not aesthetic. Dark means "you are working over the record" — network, analysis, comparison, argument. Light means "you are reading the record" — the document page, or the public-facing explanation of it. A user learns the distinction in about thirty seconds and then has a persistent, wordless cue about what kind of surface they are on.

**Consequence.** Libre Baskerville follows the same logic. Serif in this product means "these are the words from the record". It appears in judgment paragraphs, transcript Q&A, exhibit quotations and prior statements — and nowhere else. Generated analysis is never set in serif.

---

## 10. Why the network edge inspector is headed with a question

**Decision.** The edge inspector is headed **"Why does this connection exist?"** rather than "Connection details".

**Why.** It frames every edge as something requiring justification, and the panel then supplies it: the source, the exact citation, the verification state. A user who clicks three edges learns that edges are claims backed by documents, not facts the system knows.

**Paired rule.** An edge with no resolvable citation is not drawn. There is no "inferred" or "probable" edge type, and adding one would undermine the whole graph.

---

## 11. Why Statement Comparison has a "Not Comparable" label

**Decision.** Five labels, one of which records that a source does not address the topic.

**Why.** Without it, silence gets classified as difference. If a prior statement simply never mentions a checkpoint, a four-label system forces a reviewer to choose between "consistent" and "possible contradiction", and either is wrong. `Not Comparable` lets the interface say *"Prior statement silent on topic"* — which is the accurate answer and the one a careful researcher needs.

**Companion rule.** This screen never uses *lying*, *dishonest*, *false* or *unreliable* in the system's own voice. Those words appear only inside a quotation from a court finding, in quotation marks, with a citation and a `Court Finding` badge. Artboard 09's right rail demonstrates the pattern: the Chamber's credibility finding is shown, quoted, attributed, with the note *"This is the Chamber's assessment, not the system's."*

---

## 12. Why the Argument Lab flags absence of citation, not quality of argument

**Decision.** The editor underlines substantive sentences with no supporting citation. It never evaluates whether the argument is sound.

**Why.** "Is this sentence sourced?" is a question software can answer correctly. "Is this argument good?" is not, and a tool that answered it would be making legal judgments for its users. The distinction is stated on screen so that users understand what the red underline does and does not mean.

**Same logic in the Neutral Reviewer.** Its eight categories report gaps between the draft and the record — unsupported, missing citation, ignored evidence, unanswered counterargument. Its `Legal Question` category explicitly declines: *"This system does not answer it. Consult qualified counsel."*

---

## 13. Why the three-stage workflow cannot be collapsed

**Decision.** Defence Analyst → SPO Red Team → Neutral Reviewer, always in that order, always visible as three separate stages with their own findings.

**Why.** A single "review my argument" button would blend advocacy and critique into one output, and the user would not be able to tell which was which. Three stages with three visible outputs means the user sees that the strongest version of their argument and the strongest attack on it were both constructed from the same record, and that the neutral pass came last.

**Also.** Each stage is independently re-runnable, and "Compare stages" diffs them — so a user can see what changed when the record changed.

---

## 14. Why Public mode never replaces the record

**Decision.** Every plain-language passage is shown together with the official text it describes, on the same screen, at the same time. The "What this finding does not mean" and "There was also evidence pointing the other way" blocks are required parts of the explained-finding pattern.

**Rejected.** A simplified-only view with a "see original" link.

**Why.** A link is a second step most readers will not take, and a simplified paragraph read alone becomes the reader's memory of what the court said. Placing the original beneath it makes the simplification auditable by the person reading it.

**Failure direction.** If plain-language text fails to load, the original court text renders. Never the reverse.

---

## 15. Why the demo-data flag is on every screen

**Decision.** A `Demo data` badge appears on every screen that displays a figure, plus an explicit notice above the homepage statistics.

**Why.** The numbers in this prototype are plausible — 3,241 documents, 186,420 transcript pages, 147 witnesses. Plausible fake numbers about a real criminal case, in a professional-looking interface, screenshotted and shared, become misinformation. The flag makes the screenshot self-labelling.

**Production rule.** The flag is removed from a screen only when every figure on that screen is a live database read.

---

## 16. Why Albanian layout was designed for, not adapted to

**Decision.** Nav items have no fixed width. Badges use `min-width` and wrap rather than truncate. Table column minimums are set from the longest translation. Card titles allow two lines at every breakpoint.

**Why.** Albanian interface strings run 30–60% longer than English — the measured nav comparison on Artboard 18 shows 498px growing to 706px, +42%. Retrofitting truncation later would mean *Çështje potenciale për shqyrtim* rendering as *Çështje potencia…*, which is worse than useless for a legal term.

**Never translated.** Official identifiers — `KSC-BC-2020-06`, `W01234`, `P00441`, `¶1,204`, `T. 4,226` — render identically in both languages. They are addresses into the record, not words.

**Open item.** The Albanian strings in Artboard 18 are design placeholders. Legal terminology must be reviewed against the Chambers' own published Albanian texts before release; the court publishes in Albanian and its wording governs, not ours.

---

## 17. Why gaps are rendered rather than filled

**Decision.** Closed-session ranges, redactions, unresolved citations and untranslated documents are shown explicitly, with their extent, wherever they bear on what the user is reading.

**Rejected.** Omitting them silently; inferring redacted content; machine-translating court documents in place.

**Why.** A researcher who does not know that 41 transcript pages are closed-session may believe they have seen the whole of a witness's evidence. The gap is part of the record's shape and withholding it is a distortion. Artboard 15's right rail carries a dedicated *"Not Available to This Answer"* card for exactly this reason.

---

## 17b. Why Evidence Path is its own screen, not a network overlay

**Decision.** *Find Record Connection* resolves to a dedicated screen (artboard 20) with a horizontal path canvas and a per-hop inspector list, rather than a highlighted route drawn inside the network graph.

**Rejected.** Highlighting the path in place on the Network Explorer, with the existing edge inspector doing the work.

**Why.** A highlighted route inside a graph reads as one object — *a connection between two people* — and the graph's visual language encourages taking it whole. That is precisely the inference this product must not invite. Decomposing the path into a numbered list, where each row is a separate citation with its own verification state and its own document, makes a path arithmetic rather than rhetoric: four documents each mention the thing next to them, and the user can check all four.

The dedicated screen also has room for the two pieces of copy the feature needs and the graph has nowhere to put — the header constraint (*"These records reference one another. That is all a path shows"*) and the *What a path cannot tell you* card.

**Ordering.** Alternate paths are listed by hop count and nothing else, introduced by *"A shorter path is not a stronger one."* There is no path scoring function, and adding one would reintroduce exactly the ranked-inference problem §2 exists to prevent.

**Audit note.** This screen did not exist until the final handoff audit. Flow F was specified in the flow documentation and referenced by the Network toolbar, but the screen itself had never been drawn — meaning the most inference-prone feature in the product carried no drawn constraints. Closing that gap is the clearest return the audit produced.

---

## 18. Open questions for engineering

1. **Citation resolution at scale.** The rule that an unresolvable citation blocks rendering is correct but expensive. Resolution needs to be pre-computed at ingest, with a resolution index, not checked at request time.
2. **Protected-witness index isolation.** The guarantee that search cannot resolve a name to a W-code should be enforced at the index level — protected witness records in a separate index with no name field — not only in the query layer.
3. **Albanian legal terminology.** Needs review against the Chambers' published Albanian texts before any public release.
4. **Closed-session boundary detection.** Transcript segmentation must identify closed-session ranges reliably, since the chronology rail lists them and the AI layer must exclude them.
5. **Direction labelling provenance.** Whether direction labels are human-assigned, machine-suggested, or both, needs deciding — the verification column implies a workflow that is not yet specified.
6. **Density persistence scope.** Per-table, per-user. Confirm this survives across sessions and devices.
7. **Export citation integrity.** An export must carry its citation set, not just its rendered rows, so it can be re-resolved against the live record later.
8. **Path computation cost.** Paths are never cached by URL, because the record can change underneath them. Confirm that recomputation at depth 3 over the full citation graph is fast enough to feel interactive, and decide the timeout behaviour if it is not.
9. **Plain-language authoring workflow.** Public-mode text is authored and reviewed, keyed to a finding id, not generated at request time. Who writes it, who approves it, and what happens to the public page when the underlying finding is amended on appeal.

---

## 19. What must not change without revisiting this document

- Colour encodes source, never severity
- No score, rank or rating of any person exists in the data model
- The record/AI boundary uses four simultaneous signals
- Protected witness surfaces fail closed and carry no identity markup
- An unresolvable citation blocks rendering rather than degrading it
- Network edges without a citation are not drawn
- Date types are never merged
- Direction labels are scoped to a claim, never to a person
- Plain-language text never appears without the record text it describes
- Gaps are stated, never filled
- Evidence paths decompose into individually cited hops, ordered by hop count and nothing else
