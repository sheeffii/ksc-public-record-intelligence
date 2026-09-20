# Operator capture protocol (Phase 7)

Why this exists: on 2026-09-20 every official KSC public surface —
`www.scp-ks.org`, `repository.scp-ks.org` detail pages **and** direct PDF paths —
answered automated clients (identified `curl`, the agent's fetch tool) with a
Cloudflare managed JavaScript challenge (`HTTP 403`, `cf-mitigated: challenge`).
Solving, spoofing or proxying around that challenge would defeat an access
control, which `docs/SECURITY.md`, the master roadmap and
`docs/roadmap/PHASE_07_*.md` forbid. The lawful path is the one the public uses:
a human in an ordinary browser. See ADR-011.

The pipeline therefore ingests **capture bundles**: files a human operator saved
from the official site in a normal browser session, plus a manifest recording
the official URL of every file. The pipeline never contacts the court site for
these files; it verifies, hashes, stores and persists provenance.

## What the operator does

Use your normal browser (Firefox or Chromium on Ubuntu). Do **not** use any
extension, script or "anti-bot" tool; just browse. Save everything into one
bundle directory (kept out of Git by `.gitignore`):

```text
data/captures/<bundle-id>/
  manifest.json
  pages/      saved official HTML pages ("Web Page, HTML only")
  files/      PDFs downloaded from official links
```

`<bundle-id>` is any slug, e.g. `2026-09-20-corpus-01`.

### 1. Listing pages (discovery provenance)

Open the Public Court Records repository (PCR) and filter on case
`KSC-BC-2020-06`, all languages, all record types, newest first. Save:

- page 1 of the results as `pages/listing-all-p1.html`;
- the same filter with record type **Transcript** (if that filter exists) as
  `pages/listing-transcripts-p1.html`;
- the case page on `www.scp-ks.org` for `KSC-BC-2020-06` (the page that lists
  hearings / transcripts / case materials) as `pages/case-page.html`;
- the PCR "User Information Guide" page as `pages/user-guide.html`.

For each saved page copy the **exact URL from the address bar** into the
manifest.

### 2. Records (10–20)

For each selected record:

1. open its detail page (`details.php?doc_id=…`) and save it as
   `pages/<doc_id>.html`, where `<doc_id>` is the value in the URL;
2. download the public PDF(s) linked from that page into `files/`
   (keep the file name the site gives, or a short one — the manifest carries
   the truth); right-click the link → _Copy Link_ to get the official artifact
   URL;
3. add the record to the manifest with the detail-page URL, artifact URL(s)
   and a one-line reason for selecting it.

If a detail page offers both an original and a public-redacted or corrected
version, capture **both** as separate artifacts of the same record. If a page
says the material is confidential and offers no public file, do not capture it.

Target coverage (only what is actually public):

| Type                                                                | Want   |
| ------------------------------------------------------------------- | ------ |
| Trial judgment / judgment summary (if published)                    | 1      |
| Trial transcripts (different dates; at least one "Public Redacted") | 2–3    |
| SPO filings                                                         | 2      |
| Defence filings (≥ 2 different accused)                             | 2–3    |
| Trial Panel / Pre-Trial Judge decisions or orders                   | 2      |
| Court of Appeals decision                                           | 1      |
| Registry / Victims' Counsel filing                                  | 1      |
| A public-redacted or corrected version paired with its counterpart  | 1 pair |
| Albanian-language variant of any record above                       | 1      |

### 3. Manifest

`manifest.json` (all URLs verbatim from the browser; times ISO-8601 with offset):

```json
{
  "bundle_id": "2026-09-20-corpus-01",
  "case_number": "KSC-BC-2020-06",
  "captured_by": "operator name",
  "captured_at": "2026-09-20T12:00:00+02:00",
  "capture_method": "manual browser session on the official public site",
  "browser": "Firefox 143 / Ubuntu",
  "listing_pages": [
    {
      "url": "https://repository.scp-ks.org/?icc_filters[case_number]=KSC-BC-2020-06&…",
      "file": "pages/listing-all-p1.html"
    }
  ],
  "records": [
    {
      "detail_page_url": "https://repository.scp-ks.org/details.php?doc_id=091ec6e98038f36c&doc_type=stl_filing&lang=eng",
      "detail_page_file": "pages/091ec6e98038f36c.html",
      "artifacts": [
        {
          "url": "https://repository.scp-ks.org/LW/Published/Filing/…/….pdf",
          "file": "files/F00005-RED.pdf"
        }
      ],
      "selection_reason": "SPO request; public redacted version; early procedural record"
    }
  ]
}
```

Optional per-item `captured_at` overrides the bundle value. Each artifact may
carry `official_version_ref` (e.g. `KSC-BC-2020-06/F00005/RED`), `version_type`,
`version_label`, `language` and `classification` exactly as the page shows
them; when a record has one file and no reference, the file is the record itself.

### Metadata: page first, manifest second

The pipeline reads a record's metadata from the **saved detail page** when a
parser for that page exists (`metadata_source = official_page`). The parser is
written against the first real saved pages — never against guesses — so the
first bundle is also what makes the parser possible. A record may additionally
carry a `metadata` block typed from the page:

```json
"metadata": {
  "metadata_source": "operator_manifest",
  "record_type": "filing",
  "official_ref": "KSC-BC-2020-06/F00005",
  "title": "Public Redacted Version of ‘Request for arrest warrants …’",
  "case_number": "KSC-BC-2020-06",
  "language": "eng",
  "filing_party_label": "Specialist Prosecutor",
  "filing_date": "28 May 2020",
  "classification": "Public",
  "hearing": { "date": "2024-11-25", "session_sequence": 1, "hearing_type": "trial" }
}
```

`classification` must be the page's own wording ("Public", "Public Redacted",
"Confidential"): visibility is derived from it and anything unclear fails
closed (nothing is stored). `hearing` is for transcripts only. Manifest
metadata is flagged as operator-typed and double-checked at the quality gate;
where a parser is available its values win. A saved page with neither a parser
nor a `metadata` block is a visible `invalid_metadata` item, not an error.

## What the pipeline does with a bundle

```text
validate manifest (official hosts only, files present, no path escapes)
  → parse saved listing / detail pages (discovery + metadata snapshot)
  → public visibility check (fail closed)
  → SHA-256, MIME / PDF check
  → MinIO object  documents/<case>/<official_ref>/<sha256>.pdf
  → SourceRecord + Document + DocumentVersion (+ Hearing / Transcript)
  → IngestionJob counts, checkpoint, AuditLog
```

Re-running on the same bundle is a no-op (stable external id + SHA-256 +
scoped uniqueness); an interrupted run resumes. Failures are persisted as job
items, never dropped. An artifact listed with a URL but no file is recorded as
a metadata-only version (`artifact_status = not_fetched`).

```bash
.venv/bin/ksc-ingest bundle data/captures/<bundle-id> --dry-run   # check first
.venv/bin/ksc-ingest bundle data/captures/<bundle-id>
.venv/bin/ksc-ingest status
```

## Quality gate (after ingestion)

For each record, compare `GET /api/v1/ingestion/status` → `held` (or
`ksc-ingest status`) with the saved detail page: correct case, title, official
reference, version, filing date / party / type, public visibility, source URL;
open the stored PDF from MinIO and confirm it is the same document; confirm the
SHA-256 is stored and a second `ksc-ingest bundle` run changes nothing.

## Capture format v0 and `import-capture` (what actually happened on 2026-09-20)

The first real capture did not follow the layout above exactly: the browser
session produced `manifest.json` + `pages/rNN.html` (normalised snapshots of
each detail page's published fields, not raw DOM) + `files/sha256sums.txt`, and
the PDFs were downloaded separately with their repository file names. The
importer bridges that:

```bash
.venv/bin/ksc-ingest import-capture ~/Downloads/<capture>/ksc_capture data/captures/<bundle-id> \
    --pdf-dir ~/Downloads --bundle-id <bundle-id> --captured-by "<operator>" [--browser "<text>"]
```

It validates the source manifest against every snapshot, matches each PDF by
**exact SHA-256 only** (names are never used), derives the document / version
references from the published filing id and confirms them against the reference
the PDF prints in its own header, copies the PDFs as `files/rNN.pdf`
(re-hashed), keeps the snapshots, notes and source manifest, and writes the
project `manifest.json` with `metadata_source = capture_snapshot`. It refuses
to write anything if a PDF is missing, mismatched or shared between records.
Then:

```bash
.venv/bin/ksc-ingest bundle data/captures/<bundle-id> --dry-run
.venv/bin/ksc-ingest bundle data/captures/<bundle-id>
.venv/bin/ksc-ingest gate   data/captures/<bundle-id> --json data/captures/<bundle-id>/quality_gate_report.json
```

Results for the first bundle: `docs/ingestion/CONTROLLED_CORPUS.md`.
