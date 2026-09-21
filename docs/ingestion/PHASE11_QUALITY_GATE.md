# Phase 11 controlled-corpus AI quality gate

Date: 2026-09-21  
Result: **PASS, with explicit corpus and model-layer limitations**

The gate uses only the existing 22-record controlled public corpus and performs
no discovery, download, or corpus expansion. It runs the offline deterministic
extractive provider through the same persisted retrieval, answer, and citation
validation path used by the API:

```bash
ksc-ingest gate-ai \
  --evaluation tests/evaluation/phase11_questions.json \
  --json docs/ingestion/manifests/phase11-controlled-corpus-quality.json
```

## Measured result

- 4 evaluated real-record questions;
- 1 supported question against Court decision `F03752`;
- 8 public/public-redacted, held-version source snapshots;
- 6 rendered answer blocks and 13 validated claim-to-source links;
- Court finding, SPO position, Defence position, Court response, and
  document/exhibit categories remained separate;
- 100% citation correctness, source-category correctness, quote accuracy, and
  exact-source navigation for the supported case;
- 3/3 correct whole-answer abstentions for the missing Trial Judgment, F03743,
  and F03746;
- 0 unsupported claims rendered;
- source records unchanged and human verification state unchanged.

The gate validates every used version reference and stored SHA-256 against
`phase7-controlled-corpus.json`, re-hashes every persisted retrieval excerpt,
and checks every answer link against the run's persisted whitelist. Each gate
invocation intentionally creates four audited `ai_runs`; the authoritative
source and evidence tables remain unchanged.

## Adversarial coverage

Automated tests reject a fabricated source ID, a quote not found in its source,
an unreviewed paraphrase, category conflation, prohibited evaluative language,
arbitrary factual AI analysis, and instructions embedded inside source text.
Any failure withholds the complete answer. Insufficient-evidence tests verify
that no answer block is rendered or saveable.

## Limitations

- The controlled corpus has no public Trial Judgment and does not hold the
  underlying F03743 or F03746 filings. The gate tests abstention for all three;
  it does not silently fill them.
- The supported benchmark is the narrow Phase 10 Court-decision finding at
  F03752 paragraphs 12–16, not a full merits or appellate analysis.
- The deterministic provider is the verified completion baseline. External
  compatible adapters are configuration paths with deterministic test doubles;
  no paid provider or model-quality claim is made.
- No embedding is used because structured retrieval plus PostgreSQL FTS meets
  the controlled evaluation. Semantic recall outside this corpus is not claimed.

The machine-readable report is
`docs/ingestion/manifests/phase11-controlled-corpus-quality.json`.
