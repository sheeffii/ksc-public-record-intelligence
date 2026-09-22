# Operator capture plan — `2026-09-21-corpus-02`

Purpose: the next lawful Phase 13 scale step for `KSC-BC-2020-06`. The held
corpus is 22 records; the first gradual-scale gate needs at least 50. This
capture targets **40–50 additional public records** so that duplicates,
translations and already-held versions cannot leave the corpus below 50.

This plan was prepared without browser access. No record below is
pre-selected: every reference, title, date, URL and hash must be read from the
official site in the operator's own browser session. Nothing may be typed from
memory.

## Rules (unchanged from ADR-011 / `OPERATOR_CAPTURE.md`)

- Normal interactive browser only (Firefox or Chromium). No extension, script,
  `curl`/`wget`, fetch tool or automation of any kind.
- Only official public surfaces: `https://repository.scp-ks.org/` (Public
  Court Records) and `https://www.scp-ks.org/`.
- If Cloudflare shows a challenge, let the browser handle it as any visitor
  would. Never use anti-bot tools, cookie export, proxies or header spoofing.
- Open and download only records the site itself labels **Public** or
  **Public Redacted**. Skip anything Confidential, Strictly Confidential, Ex
  Parte, or without a public file. Confidential annexes of public filings are
  not captured; only the public parent is.
- Do not read across versions to reconstruct redactions. Record redaction
  status exactly as published.
- Do not touch `data/captures/2026-09-20-corpus-01/`.

## Existing corpus — do not re-select

Match on the repository `doc_id` (in the detail-page URL) or the published
filing id. A **new language or redaction/correction version** of one of these
filings is welcome as a counterpart, but it does not count as a new filing.

| rec | filing id         | held version                        | lang | type         | doc_id             |
| --- | ----------------- | ----------------------------------- | ---- | ------------ | ------------------ |
| r01 | `F00045`          | `KSC-BC-2020-06/F00045/A03`         | en   | Filing Annex | `0910c8e180227f65` |
| r02 | `F00045`          | `KSC-BC-2020-06/F00045/A03/sqi`     | sq   | Filing Annex | `0910c8e180228458` |
| r03 | `F00001`          | `KSC-BC-2020-06/F00001`             | en   | Filing       | `0910c8e180227ce6` |
| r04 | `F00004RED`       | `KSC-BC-2020-06/F00004/RED`         | en   | Filing       | `0910c8e180228910` |
| r05 | `F00004RED`       | `KSC-BC-2020-06/F00004/RED/sqi`     | sq   | Filing       | `0910c8e18022ad05` |
| r06 | `F03752`          | `KSC-BC-2020-06/F03752`             | en   | Filing       | `0910c8e1805bed0b` |
| r07 | `F03780`          | `KSC-BC-2020-06/F03780`             | en   | Filing       | `0910c8e18060eb4c` |
| r08 | `IA042-F00005RED` | `KSC-BC-2020-06/IA042/F00005/RED`   | en   | Filing       | `0910c8e1805a997d` |
| r09 | `IA042-F00002`    | `KSC-BC-2020-06/IA042/F00002`       | en   | Filing       | `0910c8e180570605` |
| r10 | `F03776`          | `KSC-BC-2020-06/F03776`             | en   | Filing       | `0910c8e1805f75e8` |
| r11 | `F03667CORRED`    | `KSC-BC-2020-06/F03667/COR/RED`     | en   | Filing       | `0910c8e1805a3f12` |
| r12 | `F03777`          | `KSC-BC-2020-06/F03777`             | en   | Filing       | `0910c8e180601fec` |
| r13 | `F03762RED`       | `KSC-BC-2020-06/F03762/RED`         | en   | Filing       | `0910c8e1805cb221` |
| r14 | `F03774`          | `KSC-BC-2020-06/F03774`             | en   | Filing       | `0910c8e1805f75e6` |
| r15 | `F03664RED2`      | `KSC-BC-2020-06/F03664/RED2`        | en   | Filing       | `0910c8e1805b71d6` |
| r16 | `F03668RED`       | `KSC-BC-2020-06/F03668/RED/A01/RED` | en   | Filing Annex | `0910c8e18057b079` |
| r17 | `F03668RED2`      | `KSC-BC-2020-06/F03668/RED2`        | en   | Filing       | `0910c8e180596a11` |
| r18 | `F03744RED`       | `KSC-BC-2020-06/F03744/RED`         | en   | Filing       | `0910c8e1805b0bcc` |
| r19 | `F00267RED`       | `KSC-BC-2020-06/F00267/RED`         | en   | Filing       | `0910c8e1805dc7e1` |
| r20 | `—`               | `KSC-BC-2020-06/T/2026-02-18`       | en   | Transcript   | `0910c8e180548bf2` |
| r21 | `—`               | `KSC-BC-2020-06/T/2026-02-18/sqi`   | sq   | Transcript   | `0910c8e1805552d0` |
| r22 | `—`               | `KSC-BC-2020-06/T/2026-02-16`       | en   | Transcript   | `0910c8e180547470` |

Three held transcripts have no filing id: hearings of 2026-02-16 (en),
2026-02-18 (en) and 2026-02-18 (sq). Other public transcript dates are new.

## Selection targets (≈ 45 records)

Only what the site actually shows as public. Adjust counts to availability;
do not pad with unclear items.

| Coverage                                           | Aim        | Notes                                                        |
| -------------------------------------------------- | ---------- | ------------------------------------------------------------ |
| Trial Panel / Pre-Trial Judge decisions and orders | 8–10       | spread across years; include at least 2 with a `RED` version |
| SPO filings (requests, responses, notices)         | 6–8        | different filing types                                       |
| Defence filings — Thaçi, Veseli, Selimi, Krasniqi  | 8 (2 each) | different filing types per accused                           |
| Court of Appeals decisions (IA-series)             | 4–5        | several distinct interlocutory appeals                       |
| Registrar submissions / notifications              | 2–3        |                                                              |
| Victims' Counsel filings                           | 2–3        |                                                              |
| President / Supreme Court / Constitutional level   | 1–2        | only if a public item exists for this case                   |
| Public transcripts (new hearing dates)             | 4–6        | mix of years; at least one `Public Redacted`                 |
| Albanian (`sqi`) versions                          | 5–6        | preferably of records selected above (same filing id)        |
| Version counterparts: `RED`/`RED2`/`COR`/`CORRED`  | 3–4 pairs  | same filing number, successive public generations            |
| Public annexes                                     | 2–3        | only where the annex itself is public                        |

The repository search form filters on `case_number`, `record_type_short`,
`filing_court_level`, `filing_type`, `filing_submitter`, `language_short`,
`filing_number` and date; use those filters rather than browsing at random.

## Per-record fields (all read from the detail page)

case number · official filing/document id (e.g. `F03668RED2`, `IA012-F00005`)
· title · date · filing/document type · filing party · court level · language ·
public status (`public` / `public_redacted` / `public_redacted_v2` /
`public_redacted_corrected`) · detail-page URL (address bar, verbatim) ·
official PDF URL (right-click → Copy Link, verbatim) · selection reason ·
`hearing_date` for transcripts. Where the PDF can be read in the browser:
SHA-256 and byte size of the unaltered download, HTTP status.

## Bundle layout (capture format v0 — what `import-capture` accepts)

```text
<capture-dir>/
  manifest.json          bundle info + records r01…rNN (see source_manifest.json of corpus-01 for the exact shape)
  pages/rNN.html         one normalised snapshot per record with the row labels:
                         Record ID · Case Number · Title · Document / Filing ID · Record Type ·
                         Filing Type · Filing Party · Court Level · Date · Language ·
                         Public / Redacted Status · SHA-256 · Bytes · Selection Reason
  files/sha256sums.txt   "<sha256>  <local_file>" per record
  CAPTURE_NOTES.md       method, boundaries observed, anything unusual
```

PDFs are downloaded separately with the site's file names; the importer
matches them by exact SHA-256 only. If the browser workspace cannot write the
PDF bytes, still complete `manifest.json`, `pages/` and `sha256sums.txt` — the
bytes are then supplied by the approved browser-assisted artifact step
(`files/fetch_files.sh` / `verify_files.sh` pattern of corpus-01).

## Before import — duplicate check (no network, no database)

```sh
.venv/bin/python scripts/compare_capture.py <capture-dir>/manifest.json \
    --json <capture-dir>/comparison.json
```

It classifies every record as `duplicate` (doc_id or SHA-256 already held),
`counterpart` (new version/language of a held filing), `new` or
`new_unnumbered` (transcripts), lists language/version pairs inside the capture,
and flags non-public statuses or internal duplicates. Remove or replace flagged
records before importing. Unique new records must number ≥ 28 so that
22 + new ≥ 50 with margin.

## Import, verify, ingest (ingestion is a separate, explicitly authorised step)

```sh
.venv/bin/ksc-ingest import-capture <capture-dir> data/captures/2026-09-21-corpus-02 \
    --pdf-dir ~/Downloads --bundle-id 2026-09-21-corpus-02 \
    --captured-by "<operator>" --browser "<browser/version/OS>"
.venv/bin/ksc-ingest bundle data/captures/2026-09-21-corpus-02 --dry-run
# only when authorised:
.venv/bin/ksc-ingest bundle data/captures/2026-09-21-corpus-02
.venv/bin/ksc-ingest gate   data/captures/2026-09-21-corpus-02 --json data/captures/2026-09-21-corpus-02/quality_gate_report.json
.venv/bin/ksc-ingest export-corpus data/captures/2026-09-21-corpus-02 --out docs/ingestion/manifests/phase13-corpus-02.json
.venv/bin/ksc-ingest parse && .venv/bin/ksc-ingest gate-phase13 --json docs/ingestion/phase13-quality-gate.json
```

## Capture report template

```text
CAPTURE ID                        2026-09-21-corpus-02
TOTAL SELECTED
UNIQUE NEW RECORDS                (compare_capture: new + new_unnumbered)
DUPLICATES AGAINST EXISTING CORPUS
LANGUAGE / VERSION PAIRS
DOCUMENT TYPE COVERAGE
PDF BYTES PRESENT
HASHES RECORDED
MISSING ARTIFACTS
PUBLIC-ACCESS LIMITATIONS
```

## Collector (added 2026-09-22)

`scripts/ksc_operator_browser_capture.mjs` performs this plan through the
operator's own visible Chrome (ADR-019). Sequence:

```sh
pnpm exec node scripts/ksc_operator_browser_capture.mjs --print-chrome-command
# start Chrome with the printed line, pass any Cloudflare check as a normal visitor, then:
pnpm exec node scripts/ksc_operator_browser_capture.mjs --probe --attach
pnpm exec node scripts/ksc_operator_browser_capture.mjs --attach --case KSC-BC-2020-06 \
    --target-new 40 --output ~/Downloads/ksc-bc-2020-06-phase13-corpus-02
```

The run ends with `scripts/check_capture_pdfs.py` (page-1 stamp check; flagged
records go to `quarantine/`) and `scripts/compare_capture.py`.

## Result — 2026-09-22 run

- Records: 40 (new 40, counterparts
  0, Albanian 6); duplicates skipped
  during discovery 13; PDFs missing
  0; navigations 10 listings /
  40 details / 40 PDFs; challenges while attached 0.
- Comparator: selected 40 · duplicates
  0 · counterparts
  0 · new 40 · unique new
  filing numbers 35 · hashes
  40 · problems 0.
- By record type: {"Filing": 34, "Transcript": 3, "Filing Annex": 3}; by language:
  {"eng": 34, "sqi": 6}; by party: {"Specialist Chambers": 11, "Specialist Counsel": 10, "Specialist Prosecutor": 7, "\u2014": 6, "Registrar": 3, "Victims Counsel": 3}.
- Stamp check: 40 checked, 0 flagged (8 court-reclassified-as-public records
  carry the court's own stamp).
- Known review items for import: `r31 F03734RED` (PDF header prints `F03734`)
  and `r37 PL003-F00004` (unknown id pattern) will be ambiguous at import.
- Coverage gaps: no RED2/COR/CORRED counterpart pair in this batch; 37 of 40
  records date from 2025–2026 (the stop condition was reached before the
  oldest-first strata ran).
- Bundle: `~/Downloads/ksc-bc-2020-06-phase13-corpus-02/` (not ingested; not
  imported into `data/captures/`).
