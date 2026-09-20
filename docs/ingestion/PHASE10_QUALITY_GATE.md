# Phase 10 controlled-corpus quality gate

Date: 2026-09-21  
Result: **PASS, with an explicit corpus limitation**

Phase 10 reads only the already-held 22-record controlled corpus. The
`ksc-ingest build-findings` and `gate-findings` commands perform no network
request. The gate rejects unsupported “Court relied on” labels, non-exact
paragraph mappings, unresolved explicit links, and unreviewed relationships.

## Real benchmark

The controlled corpus does **not** contain the public Trial Judgment. It does
contain the public Court decision `KSC-BC-2020-06/F03752`. The benchmark is
therefore deliberately narrow:

- one human-verified procedural Court finding copied exactly from paragraphs
  12–16 of `F03752`;
- one explicitly Court-cited source link, from the exact phrase and character
  span in paragraph 12 to `F03667/COR/RED`;
- one Defence and one SPO position, each preserved as the Court's exact
  summary rather than silently presented as the unavailable underlying filing;
- one exact Court-response passage linked separately to both party positions;
- zero contrary links, zero AI-generated findings, and zero unsupported
  relied-upon labels.

All six stored relationships (one evidence link, three arguments, and two
responses) are human verified. All five distinct matrix citations resolve.
The finding text exactly equals the persisted paragraph 12–16 sequence.

## Missing official material

- the public Trial Judgment for `KSC-BC-2020-06`;
- the underlying public Joint Defence filing `F03743`;
- the underlying SPO response `F03746`.

The API and UI report the two party positions as `court_summary`, and the
per-finding source audit reports both underlying sources as missing. No trial
brief is represented as a judgment. The decision benchmark proves the data
model, exact-source navigation, party separation, Court-response linkage, and
audit behavior against real material; it does not claim that a full merits
matrix exists before the Trial Judgment is publicly available and ingested.

The machine-readable result is
`docs/ingestion/manifests/phase10-controlled-corpus-quality.json`.

## Safety interpretation

An explicit link means only that the cited source is expressly identified in
the Court passage recorded for this finding. A related link, if later added,
must remain separately labelled. Network paths and shared subject matter never
create finding-evidence links. Missing categories use the neutral statement:
“No additional corroborating source has been identified in the indexed public
record.” No guilt, credibility, judicial-quality, appeal-success, evidential
weight, rank, or probability score is produced.
