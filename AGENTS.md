# AGENTS.md

Instructions for any AI coding agent working in this repository.

1. Read `CLAUDE.md` first — it holds the permanent rules (mission, design source of
   truth, public-data rule, protected-witness rule, citation rule, neutrality rule).
2. Then `MEMORY.md` (where work stopped), `docs/PROJECT_STATE.md` (milestones) and
   `docs/DECISIONS.md` (ADRs).
3. `docs/design/` is the approved UX and is read-only. Never format or rewrite it.
4. Never scrape, download, parse or embed court material unless the current phase
   explicitly authorises it. Phase 4 authorises none of it.
5. Never fabricate identifiers, citations, quotes or figures. Unresolved stays
   `UNRESOLVED`. Protected witnesses stay as their W-code.
6. Never add a score, rank, weight or probability field about a person, anywhere.
7. Interface strings go in the string tables; colours come from tokens.
8. Run `make lint`, `make typecheck` and `make test` before declaring work done.
9. Update `MEMORY.md` at the end of the session; `docs/PROJECT_STATE.md` and
   `docs/DECISIONS.md` when they change.
10. Commits: Conventional Commits, short, no AI attribution trailers. Never push
    unless explicitly told to.
