# Official KSC public sources — discovery findings (Phase 7)

Status as of 2026-09-20. This documents _observed_ behaviour of the official
public surfaces for `KSC-BC-2020-06`, what is confirmed, what is only known
from search-engine indexes (never treated as provenance) and what could not
be inspected. It is the reference for `ksc_ingestion.sources` and for ADR-011.

## Surfaces

| Surface                    | Host                                                                       | Role                                                              |
| -------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Case page                  | `www.scp-ks.org` (`/en/cases/...`)                                         | procedural context, hearings, links to transcripts / video        |
| Public Court Records (PCR) | `repository.scp-ks.org`                                                    | filings, decisions, judgments, transcripts; metadata; public PDFs |
| PCR user guide             | `www.scp-ks.org/en/user-information-guide-public-court-records-repository` | how the PCR is meant to be used                                   |

`SourceSystem`: `ksc_case_page` · `ksc_public_court_records` ·
`ksc_public_hearing` · `other_official_ksc`. Nothing else is a source.

## Access behaviour (confirmed by direct request, 2026-09-20)

Requests with an identifying `User-Agent` (`ksc-public-record-intelligence/0.1
(+research tool …; contact: …)`) to

- `https://www.scp-ks.org/robots.txt`
- `https://repository.scp-ks.org/robots.txt`
- a PCR detail page (`details.php?doc_id=…`)
- a PCR PDF path (`/LW/Published/Transcript/KSC-BC-2020-06/….pdf`)

all answered **HTTP 403** with `cf-mitigated: challenge`, `server: cloudflare`
and a "Just a moment…" JavaScript challenge page. The agent's fetch tool was
refused the same way. `robots.txt` itself is therefore unreadable to a
non-browser client.

Consequences:

- the Cloudflare managed challenge is an **access control**; the project rules
  forbid defeating it (no browser-engine automation to solve challenges, no
  header/cookie spoofing, no proxy services). `HttpFetcher` detects a challenge
  and raises `AccessControlBlockedError`; it never retries;
- because `robots.txt` cannot be read, the fetcher treats both hosts as closed
  (fail closed), so **no automated fetch of any official page or file is made**;
- the pipeline ingests **operator capture bundles** instead — pages and PDFs a
  human saved in an ordinary browser session (docs/ingestion/OPERATOR_CAPTURE.md);
- a live `ksc-ingest probe <url> --record` persists the block as an
  `ingestion_job_items` row with status `blocked_by_access_control`, so the
  situation is visible in the data.

If the court ever admits identified research clients, `HttpFetcher` is the
path; nothing else changes.

## URL shapes (from search-engine index of official pages; canonical host confirmed)

These forms were observed in indexed official URLs and are what
`ksc_ingestion.sources.classify` recognises. They are **not** constructed by the
pipeline; a URL enters only when observed on an official page or copied by the
operator from the browser.

```text
https://repository.scp-ks.org/?icc_filters[case_number]=KSC-BC-2020-06
      &icc_filters[language_short]=_all&icc_filters[record_type_short]=_all
      &icc_filters[sort_order]=_sort_date_newest/1000&page=N              listing
https://repository.scp-ks.org/details.php?doc_id=<16 hex>&doc_type=stl_filing&lang=eng   detail
https://repository.scp-ks.org/LW/Published/Filing/<16 hex>/<title>.pdf                  filing PDF
https://repository.scp-ks.org/LW/Published/Transcript/KSC-BC-2020-06/<hearing>.pdf      transcript PDF
https://www.scp-ks.org/en/cases/...                                                     case page
```

Observed facts: the listing is filterable by case number, language
(`language_short`, `_all`) and record type (`record_type_short`, `_all`), is
sortable (`_sort_date_newest`) and paginated (`page=…`; a page 211 exists for
this case, so the public docket is in the thousands of records). Detail pages
key records by `doc_id` (16 hex characters) with `doc_type=stl_filing` and a
`lang` parameter (`eng` observed; `alb`/`srb` expected but **unverified**).
Indexed titles show the KSC conventions: "Public Redacted Version of …",
filing numbers `KSC-BC-2020-06-F00005`, sub-proceedings such as `IA002-F00001`,
and version suffixes `-RED`. Transcript PDFs are titled by hearing date and
session ("Trial Hearing - 25 November 2024 - Public Redacted").

## Not yet inspected (needs saved official pages)

- the exact metadata fields and labels on a detail page (document number,
  filing date, filing party, classification, related versions, translations);
- whether the listing is server-rendered or backed by a JSON endpoint the public
  UI calls (only endpoints the public UI itself uses may ever be considered);
- how versions (original / public redacted / corrected) and translations are
  linked between records;
- how the case page lists hearings and links transcripts / video;
- rate-limit expectations and the text of `robots.txt`.

These are answered by the first operator capture bundle. The PCR detail-page
parser (`DetailPageParser` in `ksc_ingestion.capture`) is implemented against
those saved pages, not against guesses; until then a saved page without
manifest metadata is a visible `invalid_metadata` item.

## Rules restated

Public-only. Never bypass authentication, access controls or robots rules;
never guess confidential URLs; never reconstruct redactions; never infer a
protected witness's identity. Search engines and third-party copies may help a
human find an official page; they are never provenance.
