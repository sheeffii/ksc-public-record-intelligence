# CLAUDE.md — permanent project instructions

Long-term rules for working in this repository. Temporary progress lives in
`MEMORY.md`; milestones in `docs/PROJECT_STATE.md`; decisions in `docs/DECISIONS.md`.

# Project Mission

KSC Public Record Intelligence is a professional, citation-first research platform
over the **public** court record of **KSC-BC-2020-06** (Kosovo Specialist Chambers).
It will let researchers explore documents, transcripts, witnesses, exhibits, people,
incidents, locations, court findings, evidence relationships, timelines,
prosecution and defence arguments, potential appellate issues, and source-backed AI
research — with every statement traceable to a page, paragraph or line.

The system is neutral and evidence-driven. A network connection never implies guilt
or wrongdoing. Protected witnesses remain protected. AI never becomes the source of
truth.

# Design Source of Truth

The approved design lives under `docs/design/` and is **read-only** for
engineering. Before modifying any user-facing UX, review the relevant
specification, in this priority:

1. `docs/design/DESIGN_SYSTEM.md`
2. `docs/design/PAGE_SPECS.md`
3. `docs/design/COMPONENTS.md`
4. `docs/design/UX_FLOWS.md`
5. `docs/design/DESIGN_DECISIONS.md`
6. `docs/design/ROUTE_MAP.md`
7. `docs/design/HANDOFF.md`
8. `docs/design/Design.html`

Do not redesign components ad hoc. If an engineering constraint forces a
deviation, record it in `docs/DECISIONS.md` first. Never run a formatter over
`docs/design/` (it is in `.prettierignore`; keep it there).

# Evidence Source of Truth

```
PRIMARY COURT SOURCES → DATABASE → STRUCTURED EVIDENCE → PROVENANCE / CITATIONS
→ SEARCH / NETWORK / ANALYSIS → AI
```

Primary sources, the database, provenance and citations are authoritative. AI
output is analysis only. Do not build around "AI memory"; AI memory is not
evidence.

# Public Data Rules

The application uses only lawfully public records. Never:

- bypass authentication;
- bypass access restrictions;
- guess confidential URLs;
- reconstruct redactions;
- infer protected witness identities;
- deanonymize protected people.

# Protected Witness Rule

If a witness is publicly identified only as `W01234`, continue to display only
`W01234` — unless an official public court source identifies them. No name, image,
location, occupation, age or inferred attribute is stored or displayed. Protection
state comes from the backend and fails closed to the protected treatment.

# Citation Rule

Never fabricate document IDs, witness codes, exhibit IDs, pages, paragraphs,
transcript lines or quotes. A citation that cannot be resolved remains
`UNRESOLVED`, and content that depends on it is withheld, not degraded. Citation
resolution happens at ingestion and is persisted (ADR-005); the runtime looks it up.

# Neutrality Rule

Always distinguish:

`COURT FINDING` · `WITNESS TESTIMONY` · `SPO ARGUMENT` · `DEFENCE ARGUMENT` ·
`DOCUMENT / EXHIBIT` · `AI ANALYSIS`

Never generate guilt scores, suspicion scores, credibility scores or appeal success
probabilities — and never add a field that could hold one. Use **Potential Issue
for Review** rather than predictive language. Colour encodes source, never
severity. Direction labels are scoped to a stated claim, never a person.

# Language Rule

English and Shqip. All interface strings come from
`apps/web/src/i18n/messages/{en,sq}.json`; no literals in components. Official
identifiers (`KSC-BC-2020-06`, `F01234`, `W01234`, `P00123`, `¶1,204`, `T. 4,226`)
are never translated. Albanian legal terminology is provisional until checked
against official KSC Albanian publications. Layouts grow for Albanian; nothing
truncates.

# Development Rules

- Run tests after meaningful changes (`make test`; `make lint`; `make typecheck`).
- Do not claim work is complete unless it runs.
- Update documentation when architecture changes (`docs/ARCHITECTURE.md`,
  `docs/DATA_MODEL.md`, `docs/DECISIONS.md`).
- Tokens only — no hardcoded colours in components.
- Do not add infrastructure that is not needed yet (no OpenSearch, no AI provider).
- Do not ingest, download or scrape court material outside an explicitly
  authorised ingestion phase.

# Source-of-Truth Priority

If documentation conflicts: 1 repository code · 2 database schema / migrations ·
3 automated tests · 4 current Git state · 5 `docs/DECISIONS.md` ·
6 `docs/PROJECT_STATE.md` · 7 `MEMORY.md` · 8 conversation history.
Repository reality beats stale memory. If `MEMORY.md` is wrong, fix `MEMORY.md`.

# Session Startup Procedure

At the beginning of EVERY new session:

1. Read `CLAUDE.md`.
2. Read `MEMORY.md`.
3. Read `docs/PROJECT_STATE.md`.
4. Read relevant recent entries from `docs/DECISIONS.md`.
5. Run `git status`.
6. Run `git log --oneline -10`.
7. Inspect the current branch.
8. Verify `MEMORY.md` matches repository reality.
9. Continue from `MEMORY.md → Next Actions`.

Do NOT ask the user "What were we working on?" if the repository already contains
the answer.

# Session End Procedure

After every meaningful work session:

- update `MEMORY.md`;
- update `docs/PROJECT_STATE.md` when milestone progress changes;
- update `docs/DECISIONS.md` when architecture decisions are made.
