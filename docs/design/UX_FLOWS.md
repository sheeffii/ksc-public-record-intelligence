# UX_FLOWS.md
### KSC Public Record Intelligence — end-to-end workflows

Six flows, audited on Artboard 19. Each hop names the artboard it lands on and the specific control that carries the user forward.

**Audit rule.** A flow passes only if every hop is reachable from a control visible on the preceding screen without scrolling past the fold, and the final hop lands on a page of an actual public record rather than a summary of one.

**Result.** All six resolve. Two fixes were made during the audit and are reflected in the artboards.

---

## WORKFLOW MAP

The eight workflows named for the handoff audit map onto the six lettered flows as follows.

| # | Workflow | Flow | Screens |
|---|---|---|---|
| 1 | Search → Entity/Document → Original Source | **A** (steps 1–2, 6) | 06 → 07/04 → 04 |
| 2 | Person → Network → Connection → Evidence → Original Source | **A** (full) | 07 → 03 → 10 → 04 |
| 3 | Witness → Testimony → Cross → Statement Comparison → Source | **B** | 08 → 09 → 04 |
| 4 | Judgment → Finding → Evidence Relied Upon → Original Sources | **C** (steps 1–4) | 04 → 05 → 04 |
| 5 | Finding → Supporting / Contrary / Qualifying Evidence | **C** (step 5) | 05 step 04 → 11 evidence matrix |
| 6 | Finding → Potential Issue for Review → Red Team → Source Audit | **C**→**D** | 05 → 13 → 14 → 05 step 09 |
| 7 | AI Research → Answer → Citations → Original Court Source | **E** | 15 → 04 |
| 8 | Entity A → Find Record Connection → Evidence Path → Entity B | **F** | 07 → 20 → 04/10 |

Workflows 1 and 2 are the short and long traversals of the same path, which is why they share Flow A. Workflow 5 is the branch off Flow C step 5 into the evidence matrix; the detail is under Flow C below.

---

## FLOW A — Search to original source

*Search → Person → Network → Connection → Evidence → Original Source*

The core "how do I know this" path. Six hops.

| # | Screen | What the user sees | Control that advances |
|---|---|---|---|
| 1 | **06** Global Search | Query `Hashim Thaçi`. Results grouped into eight categories, People first. QueryInterpretation shows how the term was parsed. | Result row → *View person dossier* |
| 2 | **07** Person Dossier | Header quick actions; NetworkPreview tile in the right rail with the neutrality line beneath it. | *View Network* quick action, or *Expand* on the preview |
| 3 | **03** Network Explorer | Person node centred at depth 2. Edges coloured by the source type that created them. Legend and watermark both carry the neutrality disclaimer. | Click an edge |
| 4 | **03** Edge Inspector | Panel headed *"Why does this connection exist?"* — names the source, the exact citation, verification state and date. | *Open Source* |
| 5 | **10** Exhibit Detail Panel | Provenance, metadata, page preview with redactions visible, linked records, judgment citations. | *Open full document* |
| 6 | **04** Document Reader | Opens at the exact cited page with the passage highlighted. | — terminates on the record ✓ |

**What this flow proves.** A user who starts from a name reaches a page of an original document in six steps, and at step 4 is told in plain language *why* the system drew a line between two things — before being shown the line's consequences.

---

## FLOW B — Witness to statement comparison

*Witness → Testimony → Cross Examination → Statement Comparison → Original Source*

Five hops. Reachable from three entry points so it is never a dead end.

| # | Screen | What the user sees | Control that advances |
|---|---|---|---|
| 1 | **08** Witness Dossier | Protected header state. Chronology rail lists every segment including closed-session ranges (listed, content not held). | Testimony tab |
| 2 | **08** Direct Examination | Q&A blocks in Libre Baskerville, each with its transcript citation and verification state. | Chronology rail → *Cross Examination* |
| 3 | **08** Cross Examination | Purple-bordered block, flagged *Needs human review*, showing a passage where a prior statement was put to the witness. | *Open statement comparison* |
| 4 | **09** Statement Comparison | Three columns — prior statement, trial testimony, cross-examination — with difference spans marked and each column carrying its own Citation block. | Citation A / B / C chip |
| 5 | **04** Document Reader | Transcript page or disclosed statement, at the cited line range. | — terminates on the record ✓ |

**Fix applied during the audit.** Statement Comparison was reachable only from the witness tab. Two further entry points were added: a *Compare* action in the dossier stat strip, and a link on every flagged testimony card.

**What this flow proves.** A researcher can move from "this testimony looks different from the earlier statement" to both original documents without the system ever characterising the witness. The comparison labels describe text; the only credibility assessment on screen is the Chamber's own, quoted and attributed.

---

## FLOW C — Judgment to potential issue

*Judgment → Finding → Evidence Relied Upon → Source → Other Relevant Evidence → Potential Issue for Review*

Runs down the numbered spine of the Finding Detail screen.

| # | Screen | What the user sees | Control that advances |
|---|---|---|---|
| 1 | **04** Document Reader | Reading ¶8422. An amber banner marks the paragraph as cited in a finding. | *Cited in Finding F00482* banner |
| 2 | **05** Step 01 — Court Finding | Green-bordered verbatim block with mode of liability and counts. | Scroll / jump to step 02 |
| 3 | **05** Step 02 — Evidence Relied Upon | 5 of 18 shown; each row carries type, reference, description and extent. | Row arrow → *Open source* |
| 4 | **05** Step 03 — What Sources Say | Verbatim excerpts in serif, never paraphrase, each with its citation chip. | Chip opens the reader; return to step 04 |
| 5 | **05** Step 04 — Other Record Material | Supporting 12 · Contrary 3 · Qualifying 3 · Neutral 27, with the scope note stating direction is measured against this finding as written. | Right rail → step 07 |
| 6 | **05** Step 07 — Potential Issues for Review | Dashed AI container. Names the issue, states *Needs human review*, and states that no score, probability or outcome estimate is produced. | Hands off to **13** Appeal Research ✓ |

**What this flow proves.** The user who arrives from a single judgment paragraph sees, in order: what the court concluded, what it relied on, what those sources actually say, what else the record holds including material pointing the other way, and only then the machine-surfaced question. The contrary material is on the path, not hidden behind a tab.

---

## FLOW D — Finding through adversarial review

*Finding → Defence Argument → SPO Response → Court Response → Red Team → Source Audit*

Both parties, then the court, then the red team, then the audit — in that order, never collapsed.

| # | Screen | What the user sees | Control that advances |
|---|---|---|---|
| 1 | **05** Finding Detail | Right rail step 08 shows both parties' positions side by side, each with its filing citation. | *Send to Argument Lab* |
| 2 | **14** Stage 1 — Defence Analyst | Editor pre-loaded with the Defence position and its citations. Stage card lists support located, strongest point, weakest point. | *Find SPO Response* |
| 3 | **14** Stage 2 — SPO Red Team | Counter-material, strongest rebuttal, and an explicit concession where the Defence point holds. | *Find Court Response* |
| 4 | **11 / 13** Court Response | What the Panel actually said on the point, quoted with its paragraph. | *Generate Neutral Review* |
| 5 | **14** Stage 3 — Neutral Reviewer | Eight labelled categories — Unsupported, Missing Citation, Ignored Evidence, Unanswered, Factual Dispute, Legal Question, Well Supported, Human Required — every one carrying citation chips. | *Save as research note* |
| 6 | **05** Step 09 — Source Audit | Citations resolved, human verified, unresolved, redacted counts. | — terminates on provenance ✓ |

**What this flow proves.** An argument cannot be built in this product without meeting the other side's material and the court's own reasoning. The neutral reviewer reports gaps between the draft and the record; it does not say whether the argument should be made, and the `Legal Question` category explicitly declines to answer questions of law.

---

## FLOW E — AI answer to original document

*Ask AI → cited answer → citation preview → original document*

Four hops. The shortest flow, deliberately — an AI claim is never more than two clicks from its page.

| # | Screen | What the user sees | Control that advances |
|---|---|---|---|
| 1 | **15** AI Research | Question entered. **18 sources are retrieved and listed before any answer text renders**, so the user sees what the answer will be built from. | Structured answer renders |
| 2 | **15** Cited Answer | Record blocks — Court Finding, Record Evidence, Witness Testimony, SPO Position, Defence Position — above a dashed labelled boundary. AI Analysis below it, in a dashed container with its own header disclaimer. | Hover / click a citation chip |
| 3 | **15** Citation Preview | Popover with the surrounding passage, so context is seen before navigating. The answer stays on screen behind it. | *Open document* |
| 4 | **04** Document Reader | Exact page and paragraph, in the document's own layout. | — terminates on the record ✓ |

**Fix applied during the audit.** Citation chips jumped straight to the document, losing the thread of the answer. A preview popover now sits between, with the answer still visible behind it.

**Hard guarantee on this flow.** An answer containing a citation that does not resolve is **not rendered at all**. The gap is reported instead. This is a product rule, not a degradation path.

**What this flow proves.** The record/AI boundary survives the full round trip. At step 2 the user can see at a glance which paragraphs are quoted from the court and which were written by software; at step 4 they are reading the court's own words in the court's own layout.

---

## FLOW F — Find record connection between two entities

*Entity A → Find Record Connection → Evidence Path → inspect every hop*

Every hop in the returned path is separately inspectable. A path is never shown as a single assertion.

| # | Screen | What the user sees | Control that advances |
|---|---|---|---|
| 1 | **07** Person Dossier | *Find Record Connection* quick action, present in the header of every entity page. | Click the action → `/network/path?from=:id` |
| 2 | **20** Entity Picker | From is pre-filled; second entity chosen by search; max hops set (1–3). | *Find path* |
| 3 | **20** Path Canvas | Shortest source-backed path drawn as a numbered chain. Alternates listed in the right rail, ordered by hop count only. | Click hop 1 |
| 4 | **20** Hop Inspector | Per hop: relation, source type, exact citation, verification state, document date and date type. First hop expanded by default. | hop 2 … hop n |
| 5 | **04 / 10** Source of Each Hop | Any hop opens the document that created that link. | — terminates on the record ✓ |

**Constraint carried on the path header.** *"These records reference one another. That is all a path shows."* No path is labelled strong, direct, significant or suspicious, and paths are not ranked by anything other than hop count. The right rail carries a *What a path cannot tell you* card stating the three things a path does not establish and the one thing it does.

**What this flow proves.** The most inference-prone feature in the product — "connect these two people" — is built so that the connection decomposes. Each hop is a citation a human can check, and the header tells the user what a path does and does not mean before they read it.

**Gap closed during the final audit.** Steps 2–4 previously had no artboard. The flow was specified and referenced by the Network toolbar, but the screen itself had never been designed — meaning the most inference-prone feature in the product had no drawn constraints. **Artboard 20 was built to close this**, and it is where the neutrality copy, the hop-count-only ordering and the per-hop citation requirement now live.

---

## INVARIANT ACROSS ALL SIX FLOWS

At no point in A–F does the interface present a conclusion about a person.

Every terminal state is one of three things: a document, a citation, or an explicit statement that the record is silent.

---

## SECONDARY FLOWS

Not audited on Artboard 19, but specified by the screens:

**Filter and export.** Any table or search view → adjust filters (reflected in the URL) → Export respects active filters → the export carries its citation set, not just its rows.

**Research note capture.** Any analysis surface → *Save Research Note* → the note stores the source set, not a rendered summary, so it can be re-resolved later against the live record.

**Language switch.** Any screen → LanguageToggle → the interface changes; document language does not. A document filed in Albanian stays in Albanian, with the official English translation offered alongside where the court filed one.

**Simple ↔ Research.** Public mode → ModeToggle → the same entity routes render in the full research interface, at the same record position.

**Protected witness encounter.** Any surface referencing a witness → protection state resolves → if protected, the code-only treatment renders and the ProtectionNotice appears. If protection state cannot be resolved, the surface fails closed to the protected treatment.
