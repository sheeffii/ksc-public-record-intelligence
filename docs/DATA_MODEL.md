# Data model

## Phase 4 — implemented

Three tables, created by Alembic revision `0001`. The `vector` extension is enabled
in the same migration; no vector column exists yet.

### `cases`

| column                  | type               | notes                                                            |
| ----------------------- | ------------------ | ---------------------------------------------------------------- |
| id                      | uuid pk            | internal only                                                    |
| case_number             | varchar(64) unique | official, e.g. `KSC-BC-2020-06`; what routes and citations use   |
| title                   | text               | official case name                                               |
| court                   | varchar(255)       | Kosovo Specialist Chambers                                       |
| seat                    | varchar(255)       | nullable                                                         |
| official_source_url     | varchar(512)       | root of the court's public site; specific URLs are never guessed |
| description             | text               | nullable                                                         |
| created_at / updated_at | timestamptz        |                                                                  |

Seeded row: `KSC-BC-2020-06` only. No other case content.

### `documents`

| column                  | type            | notes                                                                                           |
| ----------------------- | --------------- | ----------------------------------------------------------------------------------------------- |
| id                      | uuid pk         | internal only                                                                                   |
| case_id                 | uuid fk → cases | restrict delete                                                                                 |
| official_ref            | varchar(128)    | e.g. `KSC-BC-2020-06/F01234/RED`; unique per case                                               |
| filing_number           | varchar(32)     | e.g. `F01234`; indexed for citation resolution                                                  |
| title                   | text            |                                                                                                 |
| document_type           | varchar(64)     | filing / decision / judgment / transcript / exhibit … (constrained later)                       |
| language                | varchar(16)     | document language — independent of interface language                                           |
| document_date           | date            | **never merged with** `filing_date`                                                             |
| filing_date             | date            | **never inferred from** `document_date`                                                         |
| public_state            | enum            | `public` · `public_redacted` · `not_held` — "exists but not public" is distinguishable from 404 |
| ingestion_state         | enum            | `discovered` · `downloaded` · `parsed` · `indexed` · `failed`                                   |
| source_url              | varchar(1024)   | the official public URL the bytes came from                                                     |
| storage_key             | varchar(512)    | MinIO object key                                                                                |
| sha256                  | varchar(64)     | integrity of stored bytes                                                                       |
| page_count              | int             |                                                                                                 |
| created_at / updated_at | timestamptz     |                                                                                                 |

No rows exist. Phase 4 ingests nothing.

### `audit_log`

| column                  | type         | notes                                                          |
| ----------------------- | ------------ | -------------------------------------------------------------- |
| id                      | uuid pk      |                                                                |
| occurred_at             | timestamptz  | indexed                                                        |
| actor                   | varchar(128) | `system:seed`, worker name, reviewer id                        |
| action                  | varchar(64)  | indexed, e.g. `case.seeded`                                    |
| entity_type / entity_id | varchar      |                                                                |
| detail                  | jsonb        | must never contain document text or protected-witness identity |

### Invariants tested

- Exactly these three tables exist (`tests/unit/test_models.py`).
- No column name contains score / rank / rating / weight / priority / probability /
  likelihood (DESIGN_DECISIONS.md §2, enforced for every future table too).
- `document_date` and `filing_date` are separate, independently nullable columns.

## Planned entities (not implemented)

Order roughly follows the ingestion pipeline. All identifiers are the record's own.

| entity                | purpose                                              | key provenance fields                                                                     |
| --------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `document_versions`   | RED / CONF-lifted / corrected versions of one filing | version label, supersedes, official_ref                                                   |
| `document_pages`      | page-level text, running head, redaction extents     | page number, redactions[] with extent                                                     |
| `transcripts`         | hearing sessions                                     | session date, public/closed ranges                                                        |
| `transcript_segments` | Q/A blocks with T. page and line ranges              | t_from, t_to, line_from, line_to, kind (direct/cross/redirect/panel/closed), content_held |
| `witnesses`           | W-code, protection state, protective measures        | `public` sub-record **absent** (not null) when protected                                  |
| `exhibits`            | P-/D- numbered items                                 | tendering party, through-witness, admitted date, document date, document_id               |
| `people`              | named persons in the public record                   | aliases, public roles; **no score field**                                                 |
| `organizations`       | units and bodies                                     | variants                                                                                  |
| `locations`           | places with recorded name variants                   | variants[] (Qirez / Çirez / Cirez / Ćirez)                                                |
| `incidents`           | alleged events                                       | event date range, location, charges pleaded ("as charged — not a determination")          |
| `claims`              | stated claims direction labels are measured against  | text, source citation                                                                     |
| `findings`            | court findings in judgment order                     | para_from, para_to, mode of liability, counts, verification                               |
| `citations`           | **the resolution index**                             | see below                                                                                 |
| `relationships`       | graph edges                                          | from, to, type, `citation_id` NOT NULL                                                    |
| `arguments`           | SPO / defence positions                              | party, text, citations                                                                    |
| `research_notes`      | user notes storing the source set, not rendered text | citation set                                                                              |
| `ai_runs`             | every AI invocation                                  | model, prompt version, retrieval set, output blocks, unresolved count                     |
| `verifications`       | reviewer state per fact                              | state, reviewed_by, reviewed_at                                                           |

### `citations` — the resolution index (ADR-005)

```
citations
  id                  uuid
  raw_text            text        "F01234/RED, para. 45", "T. 4,226, lines 8–19"
  source_document_id  uuid        where the citation appears
  source_locator      jsonb       page / ¶ / line where it appears
  target_kind         enum        document | document_version | transcript_segment | exhibit | witness | finding | decision
  target_id           uuid?       resolved target, NULL when unresolved
  target_locator      jsonb?      page / paraFrom–paraTo / lineFrom–lineTo
  resolution_state    enum        resolved | unresolved | ambiguous
  resolution_method   enum        exact_id | pattern | manual | …
  confidence          numeric     0–1, deterministic methods = 1.0
  verification_state  enum        verified | ai-flagged | unresolved | needs-evidence | unreviewed
  display             text        canonical string ("Judgment · ¶8421–8427")
  resolved_at         timestamptz
```

Rules:

- Resolution happens at ingest. The API reads `resolution_state`; it never re-resolves per request.
- `UNRESOLVED` is persisted as such. Nothing substitutes a plausible target.
- Anything that depends on a citation (chip, edge, path hop, AI answer) checks the
  index and withholds itself when the citation is not `resolved`.
- `display` is pre-formatted so the client never reconstructs a citation string.

### Provenance requirements for every future table

1. Every fact row carries at least one `citation_id` (or is itself a primary record).
2. Protected witnesses: the schema for the public variant is a separate table or
   sub-record that does not exist for protected codes — not nullable columns.
3. Dates are typed: `event`, `document`, `filing`, `testimony`, `decision`. A record
   with several dates stores several typed dates; none is merged.
4. Verification is a first-class column with reviewer identity, never a boolean.
5. Nothing stores a score, rank, weight, centrality or probability of any person.
