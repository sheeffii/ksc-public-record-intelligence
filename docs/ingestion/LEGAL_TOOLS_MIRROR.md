# Legal Tools mirror acquisition (ADR-030)

The Legal Tools Database (https://www.legal-tools.org, run by CILRAP) mirrors
the public KSC record. It provides each document's official repository URL and
serves its PDFs without a challenge. CILRAP gave written permission for this
project to download them. The script below turns the mirror into ordinary
capture-v0 bundles, so everything after download is the same path as a
browser capture.

This runbook is for whoever runs an acquisition batch. It assumes the repo's
`.venv` is set up and that you can reach `legal-tools.org`.

## What it does and does not do

- It contacts only the mirror: its search API and the object store its PDFs
  live in. It never requests the official site.
- It skips Serbian records (out of scope), records we already hold (by official
  URL or SHA-256), mirror duplicates, and anything without an official
  repository URL.
- It also rejects strong Serbian transcript markers even when the mirror labels
  the record English, and excludes same-date/language transcript collisions or
  superseded transcripts rather than assigning a date-only identity (ADR-032).
- It decides public status from the PDF's own page-1 stamp, as for browser
  captures. It quarantines a record whose page-1 wording contradicts the
  mirror's language tag.
- It never adopts the mirror's party or court categories. It keeps the Legal
  Tools PURL (`metadata.extra.mirror.purl`) for attribution, as Legal Tools'
  terms ask.

## 1. Plan (no PDFs)

Pass the permission citation, not the email itself:

```bash
.venv/bin/python scripts/ksc_legal_tools_harvest.py --inventory-only \
  --permission "CILRAP written permission to <owner>, <date of email>"
```

This writes `~/Downloads/ksc-bc-2020-06-legal-tools/inventory.json` and
`plan.json`. `plan.json` lists what would be taken and why each other record is
skipped. Paging the API takes about 8 minutes, at the robots.txt
`crawl-delay: 10`. Add `--reuse-inventory` to skip the paging on later runs.

## 2. Download

```bash
.venv/bin/python scripts/ksc_legal_tools_harvest.py --reuse-inventory \
  --permission "CILRAP written permission to <owner>, <date of email>" \
  [--pilot-size 100] [--limit 200] [--bundle-prefix 2026-09-27-ltd]
```

- PDFs are cached in `_pdfs/<slug>.pdf`. An interrupted run resumes without
  downloading anything twice.
- `--pilot-size 100` selects a deterministic, stratified filing pilot with
  EN/SQ pairs preferred and writes its category/language distribution to
  `plan.json`; it is mutually exclusive with the unstratified `--limit`.
- The script writes `<prefix>-01`, `<prefix>-02`, … bundles of at most 99
  records each, runs `check_capture_pdfs.py` on each one, and moves flagged
  records to `quarantine/`.
- `summary.json` records what was bundled and what was not taken.
- If a challenge or a robots refusal appears, the run stops with exit code 2.
  It is never retried with other headers.

## 3. Import and ingest each bundle

The same commands as for a browser capture:

```bash
B=2026-09-27-ltd-01
SRC=~/Downloads/ksc-bc-2020-06-legal-tools/$B
.venv/bin/ksc-ingest import-capture $SRC data/captures/$B \
    --pdf-dir $SRC/files --bundle-id $B --captured-by "<operator>"
.venv/bin/ksc-ingest bundle data/captures/$B --dry-run
.venv/bin/ksc-ingest bundle data/captures/$B
.venv/bin/ksc-ingest gate data/captures/$B
.venv/bin/ksc-ingest export-corpus data/captures/$B \
    --out docs/ingestion/manifests/$B.json
```

Then run the usual downstream steps: `parse` → `reresolve` →
`build-evidence` → `build-intelligence`.

## 4. Fill the gaps from the official site

The mirror lags by a few days and lacks some records. Finish with a
browser-collector run that excludes everything already held:

```bash
pnpm exec node scripts/ksc_operator_browser_capture.mjs --attach \
  --exclude docs/ingestion/manifests/phase7-controlled-corpus.json \
  --also-exclude docs/ingestion/manifests/<every other bundle>.json … \
  --bundle-id <id> --target-new 100 --output ~/Downloads/<id>
```

The collector skips a record before downloading its PDF when its official PDF
URL is already held. It still dedupes by SHA-256 afterwards.
