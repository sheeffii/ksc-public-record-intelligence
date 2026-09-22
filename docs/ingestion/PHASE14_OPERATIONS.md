# Phase 14 external-source operations

Phase 14 starts with reviewed, manually submitted public URLs. It does not
crawl a publisher, use a private API, bypass a login/challenge/paywall, or
promise comprehensive platform coverage.

## Controlled import

The tracked manifest is
`docs/ingestion/manifests/phase14-external-media.json`. Each item must provide:

- a public HTTPS original and canonical URL with no embedded credentials;
- publisher/platform/source type and permitted access method;
- publication time when known and a later capture time;
- a short captured excerpt and its SHA-256;
- exact statement spans within that excerpt;
- terms and coverage notes;
- an explicit court status.

Run from the host with the normal local service settings:

```text
DATABASE_URL=postgresql+psycopg://ksc:ksc_dev_password@localhost:5432/ksc \
  .venv/bin/ksc-ingest import-media \
  docs/ingestion/manifests/phase14-external-media.json
```

The importer is deterministic for the controlled Phase 14 set. It rejects
local/private URLs, non-HTTPS URLs, credentials, duplicate canonical URLs,
non-public access states, invalid timestamps, changed hashes and statements
that are not exact spans of the captured text.

## Court status review

Do not change `EXTERNAL_ONLY` or `UNKNOWN` based on a name, phrase or topic
match. A reviewer may assign `MENTIONED`, `TENDERED`, `ADMITTED`, `REJECTED`,
`DISCUSSED` or `RELIED_UPON` only after locating the exact court passage and
persisting its resolved citation. The database requires that link to be human
verified; the API withholds it if the citation does not resolve.

## Quality gate

```text
DATABASE_URL=postgresql+psycopg://ksc:ksc_dev_password@localhost:5432/ksc \
  .venv/bin/ksc-ingest gate-phase14 \
  --json docs/ingestion/phase14-quality-gate.json
```

The gate requires at least two genuine publishers/sources, three public items,
three exact hashed statements, one neutral comparison, no duplicate URLs, no
access violations, no invalid court link, no external source in the Phase 11
retrieval table, and explicit coverage limitations.

## Current exclusions

- private profiles, deleted content and unauthorized archives;
- login-gated, paywalled, CAPTCHA or Cloudflare-blocked pages;
- automated Facebook, TikTok or X collection;
- full-article mirroring;
- automatic identity matching, authenticity findings or court-status promotion.
