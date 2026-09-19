# Interface strings

- `messages/en.json` — English, the reference table.
- `messages/sq.json` — Shqip. **Provisional.** Legal terminology must be checked
  against the Kosovo Specialist Chambers' own published Albanian texts before any
  public release (HANDOFF.md §12, DESIGN_DECISIONS.md §16). The court's wording governs.

Rules:

- No English literal in a component. Every user-visible string comes from these tables,
  including badge labels, governance footnotes and disclaimers (HANDOFF.md §10.5, §10.8).
- Official identifiers (`KSC-BC-2020-06`, `W01234`, `P00441`, `F01234`, `¶1,204`,
  `T. 4,226`) are never translated. They are addresses into the record, not words.
- Albanian strings run 30–60 % longer. Layout must grow, never truncate.
- Keys are stable; add, do not rename, so translations do not silently fall back.
