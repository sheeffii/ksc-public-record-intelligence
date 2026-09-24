# Phase 17A corpus coverage

Snapshot date: 2026-09-24  
Case: `KSC-BC-2020-06`

## Declared scope

This pass covers official public records already discovered for
`KSC-BC-2020-06`, in English and Albanian, and reports held artifacts and
structured projections separately. It is a **known public corpus indexed as of
2026-09-24**, not a complete-corpus claim.

The reproducible metadata-only inventory and machine-readable audit are in
`docs/ingestion/manifests/phase17-pass-a-coverage.json`. Regenerate them from
the database with:

```text
ksc-ingest report-phase17a --generated-at 2026-09-24 \
  --out docs/ingestion/manifests/phase17-pass-a-coverage.json
```

## Current corpus

| Measure | Actual count |
| --- | ---: |
| Officially discovered source records | 62 |
| Logical documents | 56 |
| Artifact versions | 61 |
| Fetched PDFs | 61 |
| Parsed versions | 61 |
| Indexed versions | 61 |
| Pages | 2,832 |
| Numbered paragraphs | 2,019 |
| Transcript segments | 1,363 |
| Citations | 15,730 |
| Resolved / ambiguous / unresolved / invalid citations | 188 / 3 / 15,420 / 119 |

The 62nd source record is a real official metadata record that remains
unmapped and unfetched because its published identifier conflicts with the PDF
header. It remains review-required; it is not forced into a document/version.

Language distribution is EN 53 and SQ 9 at source-record level. Logical
document dates cover 2020 (2), 2025 (5), 2026 (44), with 5 unspecified. There
are no held dated logical documents from 2021–2024.

Document-type distribution at source-record level is: decision 16, request 12,
submission 6, transcript 6, filing annex 4, response 4, brief 3,
notice/notification 3, reply 3, indictment 2, order 2, other 1.

## Structured-data audit

| Projection | Model | Real rows | Source-backed | Pipeline | API / UI | Missing foundation |
| --- | --- | ---: | ---: | --- | --- | --- |
| People | `persons` | 0 | 0 | none | API + people UI | reviewed exact-source projection; ambiguous names must remain unresolved |
| Public witness codes | `witnesses` | 0 | 0 | none | API + witness UI | reviewed code-only projection; never infer a protected identity |
| Organizations | `organizations` | 0 | 0 | none | none | projection and read surface |
| Exhibits | `exhibits` | 0 | 0 | none | API + exhibits UI | official exhibit-identity/status projection; a filing annex is not an exhibit |
| Hearings | `hearings`, `transcripts` | 3 | 3 | capture normalization | transcript/event APIs; reader/timeline | direct hearing-list API |
| Statements | `transcript_segments` | 1,363 | 1,363 | transcript parser | transcript API; reader | no semantic classification; exact fragments remain available |
| Events | `events` | 54 | 54 | deterministic projection | events API; timeline | none for current projection |
| Relationships | `relationships` | 178 | 178 | resolved-citation projection | network/path/relationship APIs; network UI | none for current projection |

The zero entity counts do not mean that the underlying case contains no people,
witnesses, organizations, or exhibits. They mean that no reviewed structured
projection has yet been persisted. Phase 17A adds the reproducible inventory,
structured audit, and fail-closed batch gate; it does not create unsupported
entities or relationships.

## Next data batch

The current inventory contains zero genuinely new unheld records, so it does
not safely support an acquisition batch yet. The next action is a lawful,
operator-assisted official discovery pass capped at 75 new records. Its priority
order is:

1. 2021–2022 pre-trial decisions, orders, and party filings.
2. 2023–2025 public trial transcripts, with EN/SQ counterparts where published.
3. Balanced SPO, all Defence teams, Registrar, and Victims' Counsel material.
4. Appeals material and corrected/reclassified public versions.
5. Public annexes and exhibits only where the official record establishes their
   identity and status.

Official public search results confirm that missing strata exist, including the
[3 April 2023 opening-statement transcript](https://repository.scp-ks.org/LW/Published/Transcript/KSC-BC-2020-06/Opening%20Statements%20-%203%20April%202023.pdf),
[filing F01771 concerning public material used with W04746](https://repository.scp-ks.org/LW/Published/Filing/0b1ec6e98118a059/Prosecution%20request%20for%20admission%20of%20items%20used%20during%20the%20examination%20of%20W04746%20with%20public%20Annex%201.pdf),
and [Registrar filing F02082/RED from 2024](https://repository.scp-ks.org/LW/Published/Filing/0b1ec6e98125708f/Public%20redacted%20version%20of%20%E2%80%98Registry%20Notification%20in%20Relation%20to%20Court-Ordered%20Protective%20Measures%20and%20Request%20for%20Guidance%20Pursuant%20to%20Decision%20F01977%20with%20confidential%20Annexes%201-10%E2%80%99.pdf).
These are discovery leads, not accepted inventory rows; exact detail-page
metadata must first enter through the existing operator inventory workflow.

No Cloudflare, CAPTCHA, authentication, or access restriction was bypassed, and
no bulk corpus download was attempted in this pass.
