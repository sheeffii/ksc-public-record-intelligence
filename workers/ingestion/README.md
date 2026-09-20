# workers/ingestion — `ksc_ingestion`

Controlled, public-only ingestion of official KSC records (roadmap Phase 7).

```text
sources.py    official host allowlist; URL classification / canonicalization
fetch.py      identified HTTP client: robots, pacing, challenge → fail closed
discovery.py  DiscoveredRecord / DiscoveredArtifact contract; visibility gate
normalize.py  official refs, version types, dates, parties (never guesses)
capture.py    operator capture bundle: manifest schema, validation, discovery
snapshot.py   parser for the normalised detail-page snapshots of the v0 capture
capture_import.py  v0 capture + downloaded PDFs → project bundle (SHA-256 match,
              references confirmed against the PDF header, ADR-012)
quality_gate.py    per-record verification against DB + MinIO (re-hashes objects)
corpus_manifest.py tracked metadata manifest of a verified corpus (docs/ingestion/manifests/)
artifacts.py  SHA-256, MIME sniff, PDF validation (page count, case number)
storage.py    object store (MinIO / in-memory), hash-addressed keys
pipeline.py   Ingestor: SourceRecord → Document → DocumentVersion → job items
probe.py      one live request; a challenge becomes a recorded failure
cli.py        ksc-ingest import-capture | bundle | gate | export-corpus | probe | status
```

Commands (host side, `make infra` running):

```bash
.venv/bin/ksc-ingest import-capture <source> data/captures/<bundle-id> --pdf-dir ~/Downloads \
    --bundle-id <bundle-id> --captured-by "<operator>"
.venv/bin/ksc-ingest bundle data/captures/<bundle-id> --dry-run   # report only
.venv/bin/ksc-ingest bundle data/captures/<bundle-id>             # ingest / resume
.venv/bin/ksc-ingest probe "https://repository.scp-ks.org/..." --record
.venv/bin/ksc-ingest gate data/captures/<bundle-id> --json <report.json>
.venv/bin/ksc-ingest status
```

Rules: official hosts only; a bot-mitigation challenge is an access control and
is reported, never bypassed (ADR-011); nothing non-public is fetched or stored;
UNKNOWN visibility fails closed; identical bytes are a duplicate, not a version;
a version holding different bytes is never overwritten. See
`docs/INGESTION.md`, `docs/ingestion/OFFICIAL_SOURCES.md`,
`docs/ingestion/OPERATOR_CAPTURE.md`.
