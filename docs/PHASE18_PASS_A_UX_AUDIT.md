# Phase 18 Pass A — research experience audit

Date: 2026-09-24

Scope: production routes over the Phase 17 real-data baseline. This audit does
not authorize ingestion, deployment, backend redesign, or new inferred data.

| Route               | Classification | Actionable gap after Pass A                                                                                                                                                                                                      |
| ------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Homepage            | GOOD           | None for this pass. Corpus scale, research paths, recent documents, findings, and ingestion health are separated.                                                                                                                |
| Search              | GOOD           | None for this pass. Result rows identify what matched, where, the deterministic match basis, and the source coordinate where available.                                                                                          |
| Documents           | NEEDS POLISH   | The current summary API does not expose page counts or parsed-content availability per directory row. Add those only if a future existing API contract supplies them.                                                            |
| Document Reader     | NEEDS POLISH   | The document response does not include related people, witnesses, exhibits, or findings. The context rail now reports that absence instead of fabricating links; a future read-model endpoint is required for populated context. |
| People              | GOOD           | Directory exposes public role, document occurrences, transcript occurrences, and relationship counts without UUID-first labels.                                                                                                  |
| Person Detail       | NEEDS POLISH   | Available counts link into exact search/network exploration, but events, findings, and occurrence rows are not supplied directly by the person detail response.                                                                  |
| Witnesses           | NEEDS POLISH   | The directory exposes testimony/document occurrences and relationship counts. Distinct hearing counts are not available from the current API and are not inferred.                                                               |
| Witness Detail      | NEEDS POLISH   | Code-only protection and source-navigation paths are clear. A structured testimony/hearing occurrence payload is still absent.                                                                                                   |
| Exhibits / Evidence | GOOD           | Searchable compact directory, explicit neutral `UNKNOWN` status, document occurrence count, and responsive card layout are present.                                                                                              |
| Findings            | GOOD           | List rows keep the finding text to a concise clamped summary and retain source/verification metadata.                                                                                                                            |
| Finding Detail      | GOOD           | Court text, evidence, party positions, Court response, gaps, exact sources, and audit remain structurally separate.                                                                                                              |
| Network             | NEEDS POLISH   | Progressive selected-node neighbourhoods prevent rendering all 10,380 relationships. Server-side neighbourhood pagination/clustering would be required before materially larger graphs.                                          |
| Timeline            | GOOD           | Real events render as a filterable chronological research list with distinct date types, record links, precision, and official-source action where available.                                                                    |

Resolved broken presentations in this pass:

- exhibit status was present in real data but absent from the directory;
- person and witness counts were collapsed into a single opaque total;
- the network inspector displayed fixed demo counts in real-data mode;
- the dense network used whole-graph coordinates for a bounded subset, causing
  initial nodes to overlap;
- dense tables only overflowed horizontally at mobile widths;
- real reader context tabs could appear blank without explaining the API gap.
