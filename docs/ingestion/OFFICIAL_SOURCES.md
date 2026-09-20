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

## VERIFIED FROM CAPTURE (bundle `2026-09-20-corpus-01`, 22 records)

Everything in this section was demonstrated by the captured detail-page fields,
the official URLs the operator copied, and the 22 official PDFs themselves.

**Hosts and URL forms**

```text
https://repository.scp-ks.org/details.php?doc_id=<16 hex>&doc_type=<stl_filing|stl_filing_annex|stl_transcript>&lang=<eng|sqi>
https://repository.scp-ks.org/LW/Published/Filing/<16 hex>/<title as published>.pdf
https://repository.scp-ks.org/LW/Published/Transcript/KSC-BC-2020-06/<title as published>.pdf
```

`doc_id` is a stable 16-hex key per record _and language_ (r04 eng and r05 sqi
have different `doc_id`s but share the filing id). The PDF path segment
(`0b1ec6e9…`) differs from the detail `doc_id` (`0910c8e1…`). Filing PDFs of
the same filing in two languages can share the path folder (r04/r05) or not
(r01/r02). Titles are percent-encoded verbatim in the PDF URL.

**Record categories seen**: `Filing`, `Filing Annex`, `Transcript`
(`doc_type` mirrors these). Filing types seen: Indictment, Decision, Submission,
Brief, Notice/Notification, Request, Transcript, Filing Annex.

**Metadata fields published on a detail page** (as captured): Case Number,
Title, Document / Filing ID, Record Type, Filing Type, Filing Party, Court
Level, Date, Language, public / redacted status. **Nullable as published**:
Document / Filing ID and Court Level (transcripts), Filing Party (annexes and
transcripts), Date (annexes). Nothing else fills them.

**Filing-party labels seen**: Specialist Prosecutor · Specialist Counsel
(defence) · Specialist Chambers · President · Registrar · Victims Counsel.
**Court levels seen**: Basic Court Chamber · Court of Appeal Chamber.
**Languages seen**: `eng`, `sqi`.

**Version naming (published id → reference printed in the PDF header)**

| published id                       | header reference                                                                         | meaning                                          |
| ---------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `F00004RED`                        | `KSC-BC-2020-06/F00004/RED`                                                              | public redacted                                  |
| `F00004RED` (lang `sqi`)           | `KSC-BC-2020-06/F00004/RED/sqi`                                                          | Albanian version — the court's own `/sqi` suffix |
| `F03664RED2`                       | `KSC-BC-2020-06/F03664/RED2`                                                             | further public redacted generation               |
| `F03667CORRED`                     | `KSC-BC-2020-06/F03667/COR/RED`                                                          | corrected, then public redacted                  |
| `IA042-F00005RED`                  | `KSC-BC-2020-06/IA042/F00005/RED`                                                        | interlocutory-appeal sub-proceeding              |
| `F00045` (annex, lang `eng`/`sqi`) | `…/F00045/A03`, `…/F00045/A03/sqi`                                                       | annex number from the title                      |
| `F03668RED` (annex)                | `…/F03668/RED/A01/RED`                                                                   | annex to the RED brief, itself redacted          |
| — (transcript)                     | none printed; page header shows case, date and a running page number (e.g. `Page 29148`) | no filing number exists                          |

**Page-1 markers**: filings print `Classification: <text>` and, when
reclassified, the court's stamp `PUBLIC … Reclassified as Public pursuant to
instructions contained in CRSPDnnn …` (r03, r09, r14; r01/r02 carry the same
stamp on the annex cover). Redacted versions print "Date original" and "Date
public redacted version" (r16). Transcript text layers carry line numbers 1–25
and the running transcript page.

**Capture format**: the operator's session saved _normalised snapshots_ (one
small HTML table per record, `pages/rNN.html`) plus `manifest.json` and
`files/sha256sums.txt`, not the raw PCR DOM; the PDFs were downloaded
separately and matched by SHA-256 (`ksc_ingestion.capture_import`). All 22
artifact URLs returned HTTP 200 in the browser at capture time; all 22
downloaded files matched their capture-time hashes and sizes exactly.

**Access behaviour**: the same Cloudflare challenge described above blocked
every automated request on 2026-09-20, while the operator's interactive browser
session was served normally. The browser-assisted path is therefore the working
fallback (ADR-011) and the only path used.

## NOT YET VERIFIED

- the raw DOM of a PCR detail or listing page (no raw page was saved; the
  `DetailPageParser` interface for raw pages stays unimplemented);
- whether the public UI is backed by a JSON endpoint;
- the search-form filters the operator reports (`record_type_short`,
  `filing_court_level`, `filing_type`, `filing_submitter`, `language_short`,
  `filing_number`, dates, sort, page) — plausible, recorded from
  `CAPTURE_NOTES.md`, not exercised by this pipeline;
- Serbian (`srb`) variants; `lang=alb` vs `sqi` spelling in URLs (only `sqi`
  seen);
- how the repository links versions / translations to each other on its own
  pages (references here were confirmed from the PDFs, not from page links);
- the case page on `www.scp-ks.org` (not captured);
- rate-limit expectations and the text of `robots.txt` (unreadable to clients);
- absence of a trial judgment and of public unredacted originals — operator
  observations only ("not found in this controlled capture or observed
  query").

## Rules restated

Public-only. Never bypass authentication, access controls or robots rules;
never guess confidential URLs; never reconstruct redactions; never infer a
protected witness's identity. Search engines and third-party copies may help a
human find an official page; they are never provenance.
