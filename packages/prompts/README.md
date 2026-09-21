# packages/prompts

Versioned prompt templates used by the Phase 11 analysis layer.

The immutable `citation-first-answer-v1.txt` and
`citation-first-answer-v2.txt` files are hashed and stored with every run
through a `prompt_versions` row. Version 2 adds the fail-closed, non-factual
AI-analysis boundary. Retrieved source text remains untrusted data and every
structured claim must use the source whitelist. No guilt, suspicion,
credibility, judicial-quality or success scores are permitted; unresolved
citations are never replaced; protected witnesses stay as their W-code.
