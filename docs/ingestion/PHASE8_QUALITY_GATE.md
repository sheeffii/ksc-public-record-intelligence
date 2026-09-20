# Phase 8 controlled-corpus quality gate

Status: **PASS**, 2026-09-20.

The gate uses only the 22 public versions in capture bundle
`2026-09-20-corpus-01`. Its input is pinned by
`phase7-controlled-corpus.json` (SHA-256
`df27eca54a5f1d127064b22b7669702475bc32d558deb162ea11a5a1c9087b99`). No
additional KSC material was fetched or ingested.

The machine-readable result is
`manifests/phase8-controlled-corpus-quality.json`. The checks compare the
manifest's exact version set and page counts to PostgreSQL, inspect parser
provenance and coordinate constraints, exercise the read/search API, and run
the Phase 8 unit and integration suites.

## Result

- 22/22 versions parsed with `ksc-native-pdf/2`, native text, and no
  review-required flag.
- 1,979 PDF pages match the manifest exactly; 1,233 numbered paragraphs and
  1,592 structural chunks are persisted.
- Three real transcripts produced 607 segments. Every segment has a held-PDF
  index, a printed transcript page, and an explicit line range inside 1–25.
- Manual coordinate samples were checked at transcript pages 29,148 line 6,
  29,009 line 8, and Albanian page 1 line 6. The stored speaker and text begin
  at those printed coordinates; none was inferred.
- Filing `KSC-BC-2020-06/F03780` paragraph 1 maps to PDF index 1 and printed
  page 2. The final brief's dot-leader table of contents is not misclassified
  as numbered paragraphs.
- 14,205 citations are persisted: 23 resolved, 14,105 unresolved, and 77
  invalid. All 14,182 non-resolved citations display exactly `UNRESOLVED` and
  have no target foreign key. Every extracted citation has an exact source PDF
  index and character span.
- The real corpus passes exact-ID, phrase, keyword, document-filter,
  transcript-filter, and exact-source-navigation checks. The known phrase
  `"causal link between the public statements"` opens transcript page 29,009,
  line 8.
- Plausible fake identifiers, wrong cases, missing suffixes, and impossible
  page/line coordinates fail. A controlled overlapping-page fixture remains
  explicitly `AMBIGUOUS` with no selected target.

## Reproduction

Apply migration `0004`, retain the Phase 7 controlled bundle and MinIO objects,
then run `ksc-ingest parse`. Validate the manifest hash and execute
`make lint`, `make typecheck`, `make test`, and `make build`. The SQLAlchemy
queries used for the recorded totals are case-scoped joins over
`document_versions`, `document_pages`, `document_paragraphs`,
`document_chunks`, `transcripts`, `transcript_segments`, and `citations`.

The gate deliberately records counts and short coordinate probes rather than
copying source text into Git. Original public PDFs remain in ignored object
storage with the Phase 7 hashes and official-source provenance.
