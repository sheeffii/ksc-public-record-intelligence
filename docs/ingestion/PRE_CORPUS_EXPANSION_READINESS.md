# Pre-corpus-expansion readiness audit

Date: 2026-09-28. Branch: `chore/pre-corpus-expansion-audit` (from `main`
`9dbb0c6`). Nothing was acquired, downloaded or imported for this audit.

This audit asks one question: **if the corpus becomes 20–30× larger, what
breaks?** It is for whoever plans and runs the first large ingestion batches.

## Scale

| Table                |        Now (live DB) | Expected after Legal Tools + gap fill |
| -------------------- | -------------------: | ------------------------------------: |
| Source records       |                  204 |                          ~3,700–4,000 |
| Documents / versions |            181 / 206 |                        ~3,700 / 4,000 |
| Pages                |                9,450 |       ~150,000 (mirror lists 149,500) |
| Page word geometry   | 2.55 M rows (628 MB) |                   ~40 M rows (~10 GB) |
| Citations            |               20,047 |                                ~400 k |
| Entity occurrences   |               26,693 |                                ~500 k |
| Relationships        |               12,132 |                            ~250–300 k |
| SourceAnchors        |               74,312 |                                ~1.5 M |
| Exhibits / events    |            903 / 206 |                    several k / ~3.7 k |

## Pass — already safe

- **API list endpoints.** Every collection endpoint pages (`limit` ≤ 200 plus
  `offset`), mention lists page per entity, and `/network/edges` is
  cursor-paginated at ≤ 200. The unfocused `/network` is capped at 2,000 and is
  not used by the web app. No N+1 queries: a list page issues 4–8 queries.
- **Search API.** It is bounded at 10 hits per category, so it can never pull
  all matches, and it runs on GIN full-text indexes over documents, chunks and
  transcript segments. A common word currently takes about 30 ms.
- **Reader.** It is page-local: pages and chunks are fetched per page,
  `page-context` is limited to ≤ 200, local search to ≤ 100 and transcript
  segments to ≤ 200. There is no whole-document geometry or parsed-text
  download. **PASS; left alone.**
- **Document and version identity.** It is keyed by
  `(case, official_ref)` and `(document, official_version_ref)` plus a unique
  SHA-256, never by filing number alone. Annexes, the IA/PL series,
  RED/RED2/COR/CORRED, CONF→reclassified and the `/sqi` language form all
  derive from the published id, confirmed against the PDF header. A bare filing
  number shared with annexes resolves only when unambiguous (ADR-029). Other
  bytes arriving for a held version are `ambiguous_mapping` and are never
  overwritten.
- **Bundle import.** It is idempotent: stable external id, SHA-256 and scoped
  uniqueness. Every item commits alone, failures are rows, and quarantine keeps
  conflicts out of trusted processing.
- **Parse and geometry.** Both are incremental: versions already processed by
  the current parser or extractor version are skipped or reused.
- **Phase 19 data-quality rules.** Exhibit sub-number identity, other-case
  citation protection, witness-code safety, review-required surnames,
  `UNKNOWN` exhibit status and fail-closed citations all live in the one
  resolver and mention pipeline. Bulk batches go through the same path;
  nothing bypasses it. SourceAnchor ids are deterministic
  (`uuid5(object, role)`), so links survive every rebuild.
- **Legal Tools compatibility.** No second data model is needed. Mirror
  records become ordinary capture-v0 bundles and then the same document and
  version rows. The only differences are provenance fields (`fetch_method`,
  mirror PURL) and the record key. The exceptions are listed under "Before the
  first large batch".
- **No hardcoded corpus counts, languages or categories** in the web app. The
  two literal years are only fallbacks for empty or mock data.

## Fixed during this audit

1. **Reference counts on every directory page (blocker).**
   `RecordRepository._counts` OR-joined the whole public-edge set against the
   page. For one 50-document page it discarded about 1.9 M join rows (140 ms
   now). Its cost grows with total edges × page size plus page edges × all
   nodes, which would take minutes per page at 25×. It now selects only the
   edges touching the page's own nodes (BitmapOr over the from/to indexes) and
   counts each direction with equality joins. Counts were checked
   **identical for all 1,358 documents, people, witnesses, exhibits and
   organizations**. The query now takes 18–45 ms and scales with the page's own
   edges.
2. **One bad PDF aborted `parse` (blocker).** An exception in any version
   stopped the remaining versions, the identifier rebuild and citation
   resolution. Because versions run in reference order, a single bad PDF
   blocked every later version on every re-run. Each version now runs in
   isolation: its transaction rolls back, the failure is written to the
   processing run (`failed_count`, `failed_versions`) and to the audit log
   (`document_version.parse_failed`), and the batch continues. The CLI prints
   `FAILED` rows.
3. **One bad PDF aborted `project-source-geometry` (blocker).** This had the
   same flaw: a pdfminer error in a worker process, or an object-store read,
   failed the run and skipped SourceAnchor projection. The same isolation now
   applies (`document_version.geometry_failed`).
4. **SourceAnchor projection was not case-scoped.** It deleted every span in
   the database and re-projected every case's occurrences, citations,
   relationships and findings. The live DB holds two cases. All five queries
   are now scoped to the projected case.

## Before the first large batch

- **Legal Tools harvester: Serbian transcripts mislabelled as English.** The
  mirror tags some Serbian transcripts as English (`Zasedanje u prvostepenom
postupku – 18 May / 19 July 2023`). Transcripts have no page-1
  classification line, and the stamp check accepts the Serbian open-session
  heading. If such a file arrives before the real English one, it would be
  stored as the English version. Fix on `feat/legal-tools-ingestion`: reject a
  transcript whose title or page-1 heading is Serbian.
- **Same-date transcripts.** The transcript key is
  `case/T/<hearing date>[/<lang>]`. The mirror has 7 date/language keys with
  2–4 distinct official PDFs each: per-accused Initial and Further Appearances,
  and a superseded transcript with its revised re-issue. The pipeline fails
  closed (the second PDF is quarantined), but the first one silently takes the
  bare key. Decide the identity rule in an ADR before importing transcripts,
  for example a session discriminator taken from the official file name, or
  quarantine every colliding group. Until then, have the harvester quarantine
  any transcript whose date/language key collides within the inventory or with
  a held record. Re-keying after import would mean migrating official
  references and links.

## Watch after 500 documents

- **Citation extraction and resolution after each `parse`.** It re-extracts
  and resolves citations for all parsed versions in one transaction (45–95 s
  now; roughly 20–40 min per batch at 5 k). Re-resolving everything is correct,
  because new documents resolve older citations. Re-extracting unchanged
  versions is waste. Record its run time on every batch.
- **SourceAnchor projection.** It rebuilds the whole case's spans, regions and
  anchors in one transaction after every geometry run, loading all occurrences
  and citations. It is correct and ids are stable, but its memory and duration
  grow linearly. Record its duration and peak RSS at 100 and 500 documents.
- **Geometry extraction time.** It is incremental, but history shows runs from
  404 s to 20,951 s for about 200 versions. Measure seconds per new version on
  the first batch before planning the rest.

## Should fix before ~1,000 new documents

- **Directory screens load entire collections.** The web repository walks
  every API page for Documents, People, Witnesses, Exhibits, Incidents,
  Findings and Organizations, and the directory screen filters, sorts, pages
  and counts facets in the browser. `/exhibits` (903 rows) already takes 0.75 s
  and 627 KB, and `/documents` 0.55 s. Both grow linearly, reaching several
  seconds and several MB per view at 4 k documents or 10 k exhibits. Home and
  `/public` load five collections the same way. The fix is server-driven:
  URL-state page, sort, filter and facet counts from the API. The layout does
  not change. No data or migration is involved, so it can be done after the
  first batches.
- **Timeline** fetches every event (`page("/events")`) and places every card on
  the canvas. `/events` has no date or type filter. Events track documents
  about 1:1, so expect ~3.7 k. The fix is a server date window plus type
  filter, with the UI rendering the window.
- **Search** shows at most 10 hits per category, with no totals and no
  pagination, and filters those hits in the browser. It is safe, but it cannot
  show 20,000 results. The fix is per-category `limit`/`offset` plus a total
  count, with the filters sent to the API (which already supports them).

## Safe to defer

- Page-geometry storage (~10 GB at full scale) is disk, not a design problem.
  Its separate `(version, page)` index duplicates the prefix of its unique
  index (303 MB of index now), so it can be dropped later.
- There are no btree indexes on `documents.document_type` / `language` /
  `filing_date`, or on events and relationships by date. At ≤ 5 k documents a
  sequential scan is trivial, so add these only with a query plan that shows a
  need.
- `get_transcript`, witness appearances, finding sections and exhibit status
  events return unbounded lists per record. They are bounded by one transcript
  or entity, not by the corpus.
- Media and appeal workspaces load all rows. They are curated or external sets
  that don't grow with the court corpus.

## Recommended progression

`100` → inspect → `300–500` → inspect → `~1,000` → inspect → the rest.

At each inspection, record:

- parse, geometry, re-resolution and anchor-projection durations;
- any `failed_versions`, the quarantine count and the gates;
- `/documents` and `/exhibits` response time and page size.

Fix the "before ~1,000" UI items before that step.
