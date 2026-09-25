# KSC Public Record Intelligence — Master Roadmap

> Milestone plan and execution contract for coding agents.
>
> This roadmap defines **what each phase is supposed to accomplish**. It is not a replacement for repository reality. If this roadmap conflicts with code, migrations, tests, Git, `docs/DECISIONS.md`, `docs/PROJECT_STATE.md`, or `MEMORY.md`, repository reality wins.

## Project mission

Build a professional, neutral, citation-first research platform for the **lawfully public** record of KSC case `KSC-BC-2020-06`, with architecture that can later support additional cases.

The platform should make it possible to move from a high-level question to the exact public source that supports the answer:

```text
Question / Finding / Person / Witness / Incident
                    ↓
            Structured evidence
                    ↓
              Exact citation
                    ↓
       Official public court source
```

The system is not intended to decide guilt, predict appellate outcomes, rank credibility, or infer protected identities. It is intended to make the public record easier to inspect, compare, verify, and research.

## Permanent principles

1. **Primary public sources are authoritative.**
2. **Database + provenance + citations are authoritative over AI output.**
3. **AI is an analytical layer, never evidence.**
4. **Protected witnesses remain protected.** Never infer or reconstruct hidden identity.
5. **No fabricated citations, pages, transcript lines, quotes, exhibit IDs, or document IDs.**
6. **Unresolvable citations remain `UNRESOLVED`.**
7. **A network connection does not imply wrongdoing, responsibility, agreement, endorsement, or guilt.**
8. **Court finding, witness testimony, SPO argument, Defence argument, document/exhibit, human note, and AI analysis remain visibly distinct.**
9. **No guilt scores, suspicion scores, credibility scores, or appeal-success probabilities.**
10. **Use public-only ingestion unless a future separately authorized private-data architecture is created.**

## Source-of-truth order

When anything conflicts, use this order:

1. repository code;
2. database schema and migrations;
3. automated tests;
4. current Git state;
5. `docs/DECISIONS.md`;
6. `docs/PROJECT_STATE.md`;
7. `MEMORY.md`;
8. these roadmap files;
9. conversation history.

## Roadmap structure

The original core roadmap contains **13 numbered phases**. Eight additional milestones are included without changing the core numbering:

- **Phase 5B** — UI/UX Visual Parity Remediation. This was added after a detailed design audit found that Phase 5 was functionally complete but visually simplified on several screens.
- **Phase 14** — External Media & Public Statements Intelligence. This is a **post-core feature** and must happen only after the core court-record platform is stable.
- **Phase 15** — Real Data UI Completion & Demo Removal.
- **Phase 16** — Production Readiness, Security & Lawyer Beta.
- **Phase 17** — Historical Corpus Expansion, Coverage & Continuous Sync.
- **Phase 18** — Research Experience & Visual Excellence. No separate phase file exists; its acceptance contract was the 16-criterion closeout brief recorded in `docs/PROJECT_STATE.md`.
- **Phase 19** — Corpus Depth & Verified Entity Intelligence (`PHASE_19_CORPUS_DEPTH_AND_VERIFIED_ENTITY_INTELLIGENCE.md`).
- **Phase 20** — Source-Native Intelligent PDF & Transcript Reader (`PHASE_20_SOURCE_NATIVE_INTELLIGENT_PDF_AND_TRANSCRIPT_READER.md`).

### Current sequence

| Phase | Name | Current status |
|---|---|---|
| 1 | Product Definition & Evidence/Safety Architecture | Completed historically |
| 2 | UX/UI Design System & Flagship Workflows | Completed historically |
| 3 | Design Completion, Audit & Engineering Handoff | Completed historically |
| 4 | Engineering Foundation | Completed |
| 5 | Functional Approved UI with Mock Data | Completed functionally; visual remediation completed in Phase 5B |
| 5B | UI/UX Visual Parity Remediation | Completed (2026-09-20) |
| 6 | Real Database / Evidence Model | Completed (2026-09-20) |
| 7 | KSC Public Record Discovery + Controlled 10–20 Document Ingestion | Completed (2026-09-20) |
| 8 | Parsing, Exact Citations, Resolution & Search | **COMPLETE (2026-09-20)** |
| 9 | Real Evidence Network & Timeline | **COMPLETE (2026-09-21)** |
| 10 | Judgment, Findings & Evidence Matrix | **COMPLETE (2026-09-21)** |
| 11 | Citation-First AI / RAG | **COMPLETE (2026-09-21)** |
| 12 | Appeal Research, Red Team & Statement Comparison | **COMPLETE (2026-09-21)** |
| 13 | Gradual Full Public Corpus Ingestion & Production Hardening | **COMPLETE (2026-09-22)** |
| 14 | External Media & Public Statements Intelligence | **COMPLETE (2026-09-22)** — controlled real-public-source gate PASS |
| 15 | Real Data UI Completion & Demo Removal | **COMPLETE (2026-09-22)** |
| 16 | Production Readiness, Security & Lawyer Beta | **IN PROGRESS** — local gates pass; external deployment/alerting gates intentionally deferred |
| 17 | Historical Corpus Expansion, Coverage & Continuous Sync | **COMPLETE (2026-09-24)** — known-public-corpus scope; no exhaustive-corpus claim |
| 18 | Research Experience & Visual Excellence | **COMPLETE (2026-09-24)** — tag `phase-18-complete` |
| 19 | Corpus Depth & Verified Entity Intelligence | **COMPLETE (2026-09-25)** — tag `phase-19-complete` |
| 20 | Source-Native Intelligent PDF & Transcript Reader | **IN PROGRESS (2026-09-25)** — 20A complete; stop before 20B |

## Recommended execution order from now

```text
Phase 6
  ↓
Phase 5B
  ↓
Phase 7
  ↓
Phase 8
  ↓
Phase 9
  ↓
Phase 10
  ↓
Phase 11
  ↓
Phase 12
  ↓
Phase 13
  ↓
Phase 14
  ↓
Phase 15
  ├─ Phase 16 (IN PROGRESS; external deployment/alerting deferred)
  └─ Phase 17 (COMPLETE 2026-09-24)
       ↓
     Phase 18 (COMPLETE 2026-09-24)
       ↓
     Phase 19 (COMPLETE 2026-09-25)
       ↓
     Phase 20 (IN PROGRESS; 20A complete, 20B not started)
```

Phase 5B happens after Phase 6 because the UI can be visually remediated without interfering with schema design, but it should happen before real-data ingestion so the first genuine KSC data enters a UI we are satisfied with.

Current checkpoint: Phase 17 is complete against the explicitly declared known
public `KSC-BC-2020-06` EN/SQ corpus indexed as of 2026-09-24. This is not a
complete/exhaustive KSC corpus claim. All 134 accepted versions are verified,
parsed and indexed; structured projections and citations retain fail-closed
provenance rules. Phase 16 remains **IN PROGRESS** with only external
deployment/alerting blockers intentionally deferred. Phase 18 is **COMPLETE
(2026-09-24)**. Phase 19 is **COMPLETE (2026-09-25)**, tag `phase-19-complete`:
verified mentions, header-backed appearances, exhibit status history, typed
evidence edges and fail-closed citations over the known public corpus. Phase 20
is **IN PROGRESS (2026-09-25)** with 20A complete; 20B (transcript-native Reader,
deterministic PDF synchronization and research overlays) has not started. Stop
pending explicit authorization.

## How to use these files with Claude Code, Codex, or another coding agent

Do **not** paste giant milestone prompts every time. Instead use the relevant phase file as the execution contract.

### Standard phase-start prompt

```text
Continue the KSC Public Record Intelligence project.

Follow AGENTS.md / CLAUDE.md session startup instructions.
Read MEMORY.md, docs/PROJECT_STATE.md, and recent docs/DECISIONS.md first.
Verify git status, current branch, recent commits, and existing tests.

Then read this milestone file completely:

docs/roadmap/<PHASE_FILE>.md

Execute that phase according to the file.
Do not skip acceptance criteria.
Do not begin the next phase automatically.
Keep MEMORY.md and PROJECT_STATE.md current.
Stop and report using the completion-report format defined in the phase file.
```

### Standard resume prompt inside the same phase

```text
Resume the current milestone.

Read CLAUDE.md / AGENTS.md, MEMORY.md, PROJECT_STATE.md, recent DECISIONS.md,
and the active docs/roadmap phase file.

Inspect repository reality before trusting memory.
Continue from MEMORY.md -> Next Actions.
Do not repeat completed work.
Do not begin the next phase.
```

## Git / checkpoint strategy

Each major phase should ideally have:

- a dedicated feature branch;
- coherent commits;
- all tests passing;
- clean working tree;
- a milestone tag such as `phase-6-complete`;
- `MEMORY.md` updated after the final commit/tag;
- `PROJECT_STATE.md` updated;
- ADRs added only for meaningful architecture decisions.

Do not push or merge unless explicitly authorized by the user or repository workflow already requires it.

## Design source of truth

The approved design package is under:

```text
docs/design/
```

Important files include:

- `DESIGN_SYSTEM.md`
- `PAGE_SPECS.md`
- `COMPONENTS.md`
- `UX_FLOWS.md`
- `DESIGN_DECISIONS.md`
- `ROUTE_MAP.md`
- `HANDOFF.md`
- `Design.html`

`Design.html` is a visual reference. It should not be embedded as the production application.

## Real KSC source strategy

The real-data pipeline will use official public KSC sources, especially:

1. the official case page for `KSC-BC-2020-06`, useful for public-hearing discovery, procedural context, transcript/video links, and selected case materials;
2. the official Public Court Records repository, useful for filings, decisions, judgments, transcripts, public/redacted versions, metadata, and downloadable public artifacts.

The system must preserve **discovery provenance** separately from the normalized entity and separately from the stored file/object.

Search engines may help humans discover public pages, but they are not authoritative provenance.

## Public-only rule

Do not bypass login, authentication, access control, robots restrictions, private APIs, sealed records, confidential/ex parte content, or redactions.

If the only public version is redacted, store and analyze the public redacted version as such. Do not reconstruct hidden text or protected identity.

## Post-core media rule

Phase 14 may later add publicly accessible media, interviews, videos, social posts, and press material. These remain **external context** unless the official court record shows that the material was tendered, admitted, discussed, or relied upon.

The application must distinguish at least:

```text
EXTERNAL PUBLIC SOURCE
MENTIONED IN COURT RECORD
TENDERED
ADMITTED
REJECTED
DISCUSSED
RELIED UPON
UNKNOWN
```

Never treat online popularity or repetition as proof.
