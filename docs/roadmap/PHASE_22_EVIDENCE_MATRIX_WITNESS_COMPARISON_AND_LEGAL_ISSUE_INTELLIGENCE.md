# Phase 22 — Evidence Matrix, Witness Comparison & Legal Issue Intelligence

**Status:** IN PROGRESS
**Current checkpoint:** 22A COMPLETE — 22B NEXT, not authorized
**Started:** 2026-09-27
**Branch:** `feat/phase-22-evidence-matrix-legal-intelligence`
**Entry point:** synchronized `main` at Phase 21 closeout `f25cfe0`, annotated
tag `phase-21-complete`

## Goal

Turn the existing verified corpus, structured intelligence, provenance,
SourceAnchors and source-native Reader into a legal research workspace capable
of answering:

- What did the Court find?
- What source material did the Court explicitly rely upon?
- What did the SPO argue?
- What did each Defence team argue?
- What did Victims' Counsel argue, where applicable?
- What testimony relates to the issue?
- What evidence supports, qualifies or appears contrary to a proposition?
- Where are potentially inconsistent witness statements?
- What material may merit human legal review?
- Where exactly is every relevant passage in the original public source?

The workspace organises and traces public-source research. It does not decide
facts, credibility, guilt, legal error or likely outcome.

```text
RESEARCH QUESTION / POTENTIAL ISSUE FOR REVIEW
                         ↓
         COURT FINDING / PARTY POSITION / TESTIMONY
                         ↓
        EXPLICIT RELATIONSHIP + HUMAN CLASSIFICATION
                         ↓
               SOURCE ANCHOR / SOURCE SPAN
                         ↓
             ORIGINAL PUBLIC COURT SOURCE
```

## Starting baseline

- Phase 10 provides first-class Court findings, finding-evidence links, party
  arguments and Court-response links with exact provenance.
- Phase 12 provides neutral potential-issue research, statement comparison,
  missing-material and human-review structures.
- Phase 19 provides verified entity mentions, witness appearances, exhibit
  status history and typed source-backed relationships.
- Phase 20 provides version-bound SourceSpans, SourceAnchors and the
  source-native PDF/transcript Reader.
- Phase 21 provides the audited dense research UX over real repository data.

22A begins with a repository and data audit. Existing structures must be
extended or reconciled where they already carry the required semantics; do not
create a parallel evidence, finding, comparison or issue system merely for the
new UI. Repository, migration, test and live-data reality win over this
summary.

This phase works over the existing lawfully held public corpus. It does not
authorize scraping, downloading or acquiring additional court material.

## Non-negotiable semantic separation

The data model, API, exports, filters, badges, prose and visual hierarchy must
keep these categories distinct:

1. `COURT FINDING`
2. `WITNESS TESTIMONY`
3. `SPO ARGUMENT`
4. `DEFENCE ARGUMENT`
5. `VICTIMS' COUNSEL ARGUMENT`, where applicable
6. `DOCUMENT / EXHIBIT`
7. `HUMAN RESEARCH NOTE`
8. `AI ANALYSIS`
9. `EXTERNAL PUBLIC SOURCE`

Existing Court-response or Court-reasoning records remain distinct from party
arguments and must not be promoted to a Court finding unless an exact official
passage is human-classified as a finding. A Court's summary of a party position
is labelled as a Court summary and is not presented as the underlying filing.
An external public source is never presented as court-record evidence merely
because it discusses the same person, witness, event or proposition.

Category is not inferred from display location, colour, title or proximity.
It is persisted or deterministically derived from an authoritative typed
record and returned explicitly by the API. Unknown or unsupported
classification fails closed.

## Source authority

Preserve this authority hierarchy everywhere:

```text
ORIGINAL PUBLIC COURT SOURCE
>
PARSED SOURCE TEXT
>
VERIFIED STRUCTURED INTELLIGENCE
>
HUMAN RESEARCH CLASSIFICATION
>
AI ANALYSIS
```

- The exact original public source remains visually and legally primary.
- Parsed text is a derivative navigation aid and never silently corrects the
  source.
- Structured intelligence must retain verification state, relationship basis,
  extraction origin and exact source provenance.
- Human classification may organise or compare source material but does not
  change what the source says.
- AI output is never evidence, never a Court finding, never a party position,
  never testimony and never a human classification.
- A missing, ambiguous or unresolved source remains visibly missing,
  `AMBIGUOUS` or `UNRESOLVED`. No lower layer fills a gap in a higher layer.

## Safety and legal-research rules

Do not implement or add a field capable of storing:

- guilt or innocence scores;
- witness credibility or reliability scores;
- suspicion scores;
- appeal-success probabilities;
- legal-outcome predictions;
- automatic witness deanonymization;
- inferred exhibit status;
- inferred Court findings.

Use **Potential Issue for Review** as the neutral product term. Do not use
**Appeal Ground**, **Winning Issue**, **Fatal Error** or **Likely Reversal**
unless an official filing itself uses the wording and the interface clearly
attributes the exact quotation to that filing.

Additional permanent rules:

- Direction labels such as `supports`, `qualifies` or `appears contrary` are
  scoped only to an explicit proposition, never to a person or witness.
- `Appears contrary` is a research relationship, not a finding that a witness
  lied, that evidence is false or that a legal error occurred.
- A possible inconsistency is a prompt for human review, not a credibility
  conclusion. Context, translation, question wording, date and source type
  remain visible.
- Protected witnesses remain their public W-code. Never derive identity or
  sensitive attributes from co-occurrence, comparison or external material.
- Exhibit status comes only from an exact official status source. Mention,
  tender, admission, discussion and reliance remain separate states.
- The Court explicitly relied on material only when an exact Court passage or
  citation establishes that relationship. Related material is never upgraded
  to relied-upon material.
- No citation, quotation, paragraph, line, identifier, status or relationship
  may be fabricated or guessed.

## Phase structure

| Checkpoint | Scope | Status / stop rule |
|---|---|---|
| **22A** | Evidence Matrix + legal-issue/finding architecture | **COMPLETE (2026-09-27)**. |
| **22B** | Witness comparison + party-position mapping + research intelligence | **NEXT; not authorized.** Stop after 22A. |
| **22C** | Deep legal/source fidelity audit + closeout | Not started. Stop after 22B until explicitly authorized. |

Each checkpoint has separate implementation, verification and documentation.
Use focused tests while implementing. Run the full repository gates only at
the final verification point required by the checkpoint or phase closeout; do
not repeatedly rerun unchanged suites.

## 22A — Evidence Matrix + legal-issue/finding architecture

### A1. Inventory and semantic contract

- Inventory current findings, finding-evidence links, arguments,
  argument-response links, appeal issues, issue sources, research notes,
  citations, SourceAnchors and Reader deep links.
- Record which existing fields correctly represent the Phase 22 categories and
  where additive migration is required. Preserve stable identifiers and
  authoritative foreign keys.
- Define one closed semantic contract shared by database, API, UI, exports and
  tests. Include source category, relationship role, relationship basis,
  verification/review state, extraction origin and exact source anchor.
- Represent Defence positions with the specific Defence team or filing party
  where the official source identifies it. Do not collapse distinct Defence
  teams into one unattributed view.
- Add Victims' Counsel as a first-class party-position category where source
  material exists; honest absence is not an error.
- Preserve `direct_source`, `court_summary` and `source_missing` distinctions.

### A2. Finding and legal-issue architecture

- A Court finding requires an exact official Court passage, document version,
  source coordinates and human verification. Headings, search matches, party
  characterisations and AI summaries cannot create findings.
- Keep the Court's finding text separate from analyst-created titles,
  propositions, issue labels and notes.
- Model a **Potential Issue for Review** as a research container linked to
  findings, propositions, party positions, testimony, document/exhibit
  material, public authority, missing material and human notes without
  asserting legal error.
- Applicable legal standards or public authorities retain their own source
  category and exact passage. A source being relevant does not establish that
  the Court adopted it.
- Court treatment values describe only what an exact cited passage shows:
  addressed, accepted, rejected, distinguished, qualified, not located or
  unresolved. `Not located` never means the Court was silent as a legal fact.
- Missing source material is first-class and is never silently replaced by a
  Court summary, another language version, related filing or AI output.

### A3. Evidence Matrix

Build a matrix around one explicit finding, proposition or Potential Issue for
Review. Every row must expose:

- source category and source identity;
- party/team or witness code where applicable;
- verbatim passage or clearly labelled human synopsis;
- relationship role: Court relied upon, supports, qualifies, appears contrary,
  context, applicable standard, party position or Court response;
- relationship basis: explicit Court citation, exact source passage, human
  classification or other closed, auditable value;
- verification/review state and classifier identity/date where applicable;
- exact document version and SourceAnchor resolution level;
- one action to open the exact passage in the source-native Reader;
- visible missing, ambiguous, unresolved or unavailable state.

The matrix must never imply that visual alignment, row order or adjacency is a
legal relationship. Sorting and filters are research aids, not rankings. Colour
encodes source/category only, never strength, credibility or severity.

### A4. API and workspace behavior

- Provide bounded, paginated reads for findings, issues and matrix rows, with
  filters for category, party/team, witness, relationship role, verification,
  source availability and date.
- Keep source excerpts bounded while making the exact original-source passage
  one action away.
- Support direct, stable links to a finding, issue and selected matrix row.
- Preserve English/Shqip interface parity. Do not treat translations as the
  same source version or transfer anchors between versions.
- Add exports only if each exported row retains category, verification,
  relationship basis and exact provenance; otherwise defer export.
- Use existing design tokens, components and string tables. Any new workflow
  must fit the approved research UX without modifying `docs/design/`.

### A5. 22A verification and exit criteria

- [x] Existing Phase 10/12 structures are inventoried and reconciled; no
      duplicate semantic system is introduced.
- [x] Database constraints prevent category conflation and prevent unsupported
      relied-upon or Court-finding relationships.
- [x] A real-source finding/issue matrix separates Court, each party category,
      testimony, documents/exhibits, human notes, AI and external sources.
- [x] Every affirmative matrix relationship is human-verified and opens the
      correct version-bound original passage or exposes an honest fallback.
- [x] Missing/ambiguous/unresolved material is visible and never substituted.
- [x] Protected-witness and exhibit-status safeguards pass focused tests.
- [x] API bounds, UI responsive behavior, accessibility and EN/SQ string parity
      pass focused verification.
- [x] `make lint`, `make typecheck` and `make test` pass at checkpoint
      acceptance.
- [x] The implementation, real-data reconciliation and remaining limitations
      are recorded in this file, `MEMORY.md` and `docs/PROJECT_STATE.md`.

Stop after recording 22A. Do not begin 22B without explicit authorization.

## 22B — Witness comparison + party-position mapping + research intelligence

### B1. Witness comparison

- Compare two or more exact public passages only when each passage resolves to
  its own document version, SourceAnchor and public witness code or officially
  public identity.
- Preserve source type, testimony/statement date, hearing/session,
  examination context, question and answer boundaries, language/version,
  paragraph or transcript lines and any public-session gaps.
- Distinguish `possible inconsistency`, `qualification`, `timeline difference`,
  `consistent on the compared point` and `not comparable`. These are scoped to
  the passages and proposition being compared, never to overall credibility.
- Machine retrieval may surface candidate passages, but it cannot publish a
  comparison classification. Publication requires a human reviewer and exact
  source verification.
- Never bridge redactions, closed/private sessions or missing statements.
- Never compare a protected witness to external identity clues or use
  co-occurrence to narrow identity.

### B2. Party-position mapping

- Map the SPO, each identified Defence team and Victims' Counsel separately to
  the exact finding, proposition or Potential Issue for Review they address.
- Preserve filing chronology and distinguish original, corrected, redacted,
  translated and response/reply versions.
- Distinguish direct party text from a Court summary of the party's position.
- Show where the Court addressed a position only through exact Court passages;
  no response is inferred from chronology or topic similarity.
- Conflicting or evolving positions are compared passage-to-passage without
  declaring which is correct.

### B3. Research intelligence

- Support source-first discovery across verified findings, testimony, party
  positions, documents/exhibits, public authority and external public sources.
- Candidate retrieval remains visibly distinct from verified relationships.
  A lexical or semantic match is not evidence that a source supports or
  contradicts a proposition.
- Human research notes remain a separate layer with author, timestamp and
  citations. Notes cannot alter source text or authoritative classifications.
- AI-assisted analysis must use the existing audited citation-first run model,
  show its complete source set, retain prompt/model/run lineage and abstain when
  sources are insufficient.
- AI may suggest questions or candidate passages for human review. It may not
  verify a relationship, create a canonical finding, classify credibility,
  infer exhibit status or convert output into evidence.
- External public sources remain in their separate Phase 14 boundary unless an
  exact court-record source establishes tender, admission, discussion or
  reliance.

### B4. 22B verification and exit criteria

- [ ] Real witness comparisons preserve exact passages, context and separate
      human-review state without credibility inference.
- [ ] SPO, each Defence team and Victims' Counsel positions remain separately
      attributable and distinguish direct sources from Court summaries.
- [ ] Candidate matches cannot mutate or appear as verified relationships.
- [ ] Human notes and AI analysis are visibly and structurally separate from
      evidence; AI output cannot auto-verify or publish classifications.
- [ ] Reader links open the correct source version, page, paragraph/line and
      validated highlight or honest fallback.
- [ ] Protected-witness, translation/version, external-source and missing-data
      adversarial tests pass.
- [ ] Responsive, accessible, EN/SQ and bounded-query checks pass.
- [ ] `make lint`, `make typecheck` and `make test` pass at checkpoint
      acceptance.
- [ ] The implementation and real-data checkpoint are recorded before work
      stops.

Stop after recording 22B. Do not begin 22C without explicit authorization.

## 22C — Deep legal/source fidelity audit + closeout

### C1. Audit population

Audit real records from every Phase 22 category that exists in the held corpus,
plus explicit honest-absence cases. Include:

- Court finding and Court-reasoning passages;
- explicit Court-relied-upon and merely related material;
- SPO, each represented Defence team and Victims' Counsel where available;
- witness testimony and at least one human-reviewed comparison when the record
  safely supports it;
- document/exhibit material and its official status source;
- human note, AI analysis and external-source separation;
- missing, ambiguous, unresolved, page-only and unavailable paths;
- English/Shqip and corrected/redacted version boundaries where available;
- protected witness paths.

Do not fabricate a row to satisfy category coverage. Record `NOT PRESENT IN
HELD CORPUS` where no verified example exists.

### C2. Fidelity and integrity checks

- Verify each sampled quote byte/character-for-character against stored parsed
  text and visually against the original public PDF.
- Verify every sampled SourceAnchor belongs to the selected version and lands
  on the correct page, paragraph/transcript line and region or honest fallback.
- Verify Court reliance has an exact Court citation/passage and that related
  material is not upgraded.
- Verify every direction label is scoped to a proposition and backed by human
  classification; no direction is attached to a person.
- Verify party attribution, source scope, filing version and chronology.
- Verify witness comparisons retain enough context to avoid misleading
  excerpting and never imply credibility.
- Verify missing and unresolved sources stay unfilled across UI, API, export,
  search and AI retrieval.
- Verify no Phase 22 operation mutates authoritative source bytes, citations,
  exhibit status, witness protection state or earlier verified records.

### C3. Product and operational checks

- Run desktop, 1024px and Pixel 7 source-first workflows from research question
  to matrix/comparison to the exact Reader passage.
- Test keyboard operation, focus order, screen-reader labels, contrast and
  non-colour category cues.
- Measure bounded API/query performance against the current corpus and record
  the dataset and thresholds used.
- Test authorization boundaries for research-note and human-classification
  writes if such writes are implemented.
- Produce a reproducible Phase 22 quality report and machine-readable manifest
  with counts by category, verification state, relationship basis,
  SourceAnchor resolution and audit result.

### C4. Closeout criteria

- [ ] All 22A and 22B acceptance criteria are verified against repository and
      real-data reality.
- [ ] The deep legal/source fidelity audit passes with zero category
      conflations, fabricated relationships, wrong-version anchors or protected
      witness breaches.
- [ ] Every sampled affirmative relationship resolves to the exact original
      public source; every unsupported path fails closed.
- [ ] AI remains analysis only and cannot enter authoritative evidence or human
      classification state.
- [ ] Performance, accessibility, responsive and security checks pass or a
      concrete blocker is recorded without closing the phase.
- [ ] `make lint`, `make typecheck` and `make test` pass.
- [ ] The full phase file is re-read and every acceptance criterion is checked
      against repository reality.
- [ ] The Phase 22 quality report/manifest, completion record, master roadmap,
      `MEMORY.md` and `docs/PROJECT_STATE.md` are updated.
- [ ] A conventional closeout commit and annotated `phase-22-complete` tag are
      created only after every criterion passes.

Stop after Phase 22 closeout. Do not begin a later phase automatically.

## Out of scope

- Additional court-source acquisition or corpus completeness claims.
- Automatic legal conclusions, prediction, ranking or scoring.
- Automatic publication of AI- or machine-classified evidence relationships.
- Witness identity inference or protected-data enrichment.
- Reconstruction of redacted, private, closed-session, sealed or missing text.
- Treating external media as court evidence without an exact court-record
  bridge.
- Redesigning or rewriting the approved `docs/design/` package.

## Checkpoint completion records

### 22A

**COMPLETE — 2026-09-27**

- Migration `0017` extends the existing Phase 10/12 structures instead of
  creating parallel finding, evidence or issue systems. The closed finding
  relation vocabulary is `COURT_RELIES_ON`, `COURT_CITES`, `PARTY_CITES`,
  `SUPPORTS`, `QUALIFIES`, `CONTRARY` and `CONTEXT`.
- Court relations require source-derived Court attribution. Research direction
  labels require classification origin and review process; AI suggestions
  cannot be stored as verified evidence classifications.
- Potential Issues for Review now carry definition origin. Finding links,
  arguments and issue sources carry typed SourceAnchors; party/team attribution
  and direct-source/Court-summary distinctions remain explicit.
- Bounded finding and issue matrix APIs return backend-composed rows,
  provenance, review status, filters and pagination. The Finding workspace uses
  those rows, exact Reader links and honest witness/classification empty states.
- Phase 22A projects source-documented graph nodes/edges only from the verified
  benchmark. The real Court-reliance row resolves through Evidence Path in one
  cited `RELIES_ON` hop; no hop is invented.
- Real benchmark: 1 finding, 1 Court-reliance link, 2 party positions, 1 Court
  response, 0 Court-citation-only rows, 0 support/qualify/contrary rows, 0
  linked witness passages and 0 linked exhibits. All 5 matrix rows have
  SourceAnchors. Detailed counts and limitations are in
  `docs/ingestion/PHASE22A_EVIDENCE_MATRIX_REPORT.md`.
- Migration round-trip and schema comparison pass. Targeted semantic,
  provenance, SourceAnchor, matrix-query, Finding UI and Evidence Path checks
  pass. Final gates: `make lint`, `make typecheck` and `make test` PASS (357
  backend and 260 frontend tests).
- Phase 22 remains **IN PROGRESS**. Stop here; 22B is next but has not been
  authorized or started.

### 22B

`NOT STARTED`

### 22C

`NOT STARTED`

## Setup completion record

- Phase 21 precondition verified: annotated tag `phase-21-complete` resolves to
  `f25cfe0`; synchronized `main` and `origin/main` contain that commit.
- Branch `feat/phase-22-evidence-matrix-legal-intelligence` created from the
  synchronized Phase 21 closeout.
- At setup, Phase 22 was registered as **IN PROGRESS** with **22A NEXT**; the
  22A completion record above supersedes that checkpoint.
- Setup only: no schema, ingestion, API, UI or test functionality changed.
- Setup stopped before 22A pending the authorization that was later supplied.
