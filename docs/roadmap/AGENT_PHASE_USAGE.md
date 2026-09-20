# Agent Phase Usage — Short Prompts

This file exists so the user does not need to paste long phase instructions into Claude Code or Codex.

## Starting a new phase

Replace `<PHASE_FILE>` with the correct roadmap file.

```text
Continue the KSC Public Record Intelligence project.

Before changing code:
- follow AGENTS.md / CLAUDE.md startup instructions;
- read MEMORY.md;
- read docs/PROJECT_STATE.md;
- read recent docs/DECISIONS.md;
- inspect git status, branch, recent commits and relevant tests.

Then read this file completely:

docs/roadmap/<PHASE_FILE>

Execute that milestone exactly as specified.
Repository reality wins if documentation is stale.
Keep MEMORY.md and PROJECT_STATE.md current.
Add ADRs only for meaningful architecture decisions.
Do not begin the next phase automatically.
At completion, use the report format in the phase file and stop.
```

## Resuming a phase after model/context limit

```text
Resume the current KSC Public Record Intelligence milestone.

Read AGENTS.md / CLAUDE.md, MEMORY.md, PROJECT_STATE.md, recent DECISIONS.md,
and the active docs/roadmap phase file.

Inspect git status and recent commits before trusting memory.
Run focused tests relevant to the last checkpoint.
Continue from MEMORY.md -> Next Actions.
Do not restart completed work.
Do not begin the next phase.
```

## Handoff from Claude to Codex or vice versa

```text
You are taking over an existing repository from another coding agent.

Do not re-scaffold, redesign, or restart completed work.

Read AGENTS.md / CLAUDE.md, MEMORY.md, PROJECT_STATE.md, recent DECISIONS.md,
and the active roadmap phase file.

Inspect:
- git status
- current branch
- git log --oneline -10
- milestone tags
- relevant test commands

Verify repository reality against MEMORY.md.
If memory is stale, update memory rather than changing correct code.
Continue only from the first unfinished Next Action.
Do not begin the next phase automatically.
```

## Closing a phase

```text
Do not start the next milestone.

Re-read the complete active phase roadmap and perform a final closeout audit.
Check every acceptance criterion against the actual implementation, migrations,
tests, and any required real-data quality gate. Related code existing is not
enough evidence. Fix missing phase requirements without starting the next phase.

Only after every mandatory criterion passes:
- mark the phase COMPLETE and add its completion date and completion commit;
- mark acceptance-criteria checkboxes complete where appropriate;
- append a concise Completion Record with actual data, migration and test counts;
- update 00_MASTER_ROADMAP.md so the completed phase and next pending phase are clear;
- update MEMORY.md and PROJECT_STATE.md;
- update DECISIONS.md only if architecture changed;
- verify the working tree and required lint, typecheck, tests, migrations,
  real-data gates, E2E and production build as applicable;
- create or update the clean milestone tag if repository workflow uses one.

Preserve the original roadmap requirements. Do not rewrite them into a status
summary and do not remove them. Create a clean milestone commit/tag if
authorized by repository workflow.
Then print only the completion-report sections required by the active roadmap file.
Stop.
```

## Roadmap files

```text
PHASE_01_PRODUCT_DEFINITION_AND_EVIDENCE_ARCHITECTURE.md
PHASE_02_UX_UI_DESIGN_AND_FLAGSHIP_WORKFLOWS.md
PHASE_03_DESIGN_AUDIT_AND_ENGINEERING_HANDOFF.md
PHASE_04_ENGINEERING_FOUNDATION.md
PHASE_05_FUNCTIONAL_UI_WITH_MOCK_DATA.md
PHASE_05B_UI_UX_VISUAL_PARITY_REMEDIATION.md
PHASE_06_REAL_DATABASE_AND_EVIDENCE_MODEL.md
PHASE_07_KSC_DISCOVERY_AND_CONTROLLED_INGESTION.md
PHASE_08_PARSING_EXACT_CITATIONS_RESOLUTION_AND_SEARCH.md
PHASE_09_REAL_EVIDENCE_NETWORK_AND_TIMELINE.md
PHASE_10_JUDGMENT_FINDINGS_AND_EVIDENCE_MATRIX.md
PHASE_11_CITATION_FIRST_AI_RAG.md
PHASE_12_APPEAL_RESEARCH_RED_TEAM_AND_STATEMENT_COMPARISON.md
PHASE_13_FULL_PUBLIC_CORPUS_INGESTION_AND_HARDENING.md
PHASE_14_EXTERNAL_MEDIA_AND_PUBLIC_STATEMENTS_INTELLIGENCE.md
```
