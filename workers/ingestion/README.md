# workers/ingestion

Placeholder. No ingestion code exists in Phase 4.

Planned pipeline (docs/INGESTION.md):

```
discover → download (official public URLs only) → verify hash → store (MinIO)
→ parse → segment → extract citations → resolve citations → persist resolution index
```

Nothing in this package may bypass access controls, guess URLs, or reconstruct
redactions. Controlled, per-document ingestion precedes any corpus-wide run
(ADR-003).
