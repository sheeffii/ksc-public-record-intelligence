# AGENTS.md

Instructions for any AI coding agent working in this repository.

1. Read `CLAUDE.md` first — it holds the permanent rules (mission, design source of
   truth, public-data rule, protected-witness rule, citation rule, neutrality rule).
2. Then `MEMORY.md` (where work stopped), `docs/PROJECT_STATE.md` (milestones) and
   `docs/DECISIONS.md` (ADRs).
3. The execution plan lives in `docs/roadmap/`. Read
   `docs/roadmap/00_MASTER_ROADMAP.md`, then the complete phase file for the
   active milestone named in `MEMORY.md` / `docs/PROJECT_STATE.md`. Inspect
   `git status`, branch, recent commits and tags, and continue from the current
   checkpoint. Do not restart completed phases. Do not begin a later phase
   without explicit authorisation. Repository code, migrations, tests and Git
   state win over stale roadmap text; do not reformat `docs/roadmap/`.
4. `docs/design/` is the approved UX and is read-only. Never format or rewrite it.
5. Never scrape, download, parse or embed court material unless the active
   roadmap phase explicitly authorises it. Nothing before Phase 7 does.
6. Never fabricate identifiers, citations, quotes or figures. Unresolved stays
   `UNRESOLVED`. Protected witnesses stay as their W-code.
7. Never add a score, rank, weight or probability field about a person, anywhere.
8. Interface strings go in the string tables; colours come from tokens.
9. Run `make lint`, `make typecheck` and `make test` before declaring work done.
10. Before completing any roadmap phase, re-read its full phase file, verify
    every acceptance criterion against repository reality, run every required
    quality gate, then update that phase's status/date/commit/tag and Completion
    Record, `docs/roadmap/00_MASTER_ROADMAP.md`, `MEMORY.md`, and
    `docs/PROJECT_STATE.md`. Preserve the original requirements and stop before
    the next phase.
11. Update `MEMORY.md` at the end of the session; `docs/PROJECT_STATE.md` and
    `docs/DECISIONS.md` when they change.
12. Commits: Conventional Commits, short, no AI attribution trailers. Never push
    unless explicitly told to.
