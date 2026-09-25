# Data model

Implemented by Alembic revisions `0001`–`0008`. The schema has 47 application
tables; the `vector` extension is enabled, but no vector column exists yet.
Models live in `apps/api/src/ksc_api/models/`; database enums use the lower-case
values shown below. Phase 12's bounded research vocabularies are CHECK-constrained
strings so their neutral states can be audited without adding global enum types.

```
PRIMARY COURT SOURCE → source_records → documents / document_versions
      → pages · sections · chunks · transcripts · segments
      → citations (resolution index) → claims · findings · arguments
      → graph_nodes / relationships → search · network · analysis → AI (audited)
```

## Vocabularies

| enum                       | values                                                                                                                                                                                                                                                                                                                                                                    |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `visibility`               | `public` · `public_redacted` · `not_public` · `unknown` · `private_authorized` — public mode returns only the first two; `not_public` states "exists in the docket, text not public" (ROUTE_MAP.md §8)                                                                                                                                                                    |
| `verification_state`       | `unreviewed` · `ai_flagged` · `human_verified` · `human_rejected` · `needs_more_evidence` · `unresolved` — the two human states require `verified_by` + `verified_at` (CHECK); rejected facts never surface                                                                                                                                                               |
| `resolution_state`         | `resolved` · `unresolved` · `ambiguous` · `invalid` — only `resolved` may carry a target; everything else displays the literal `UNRESOLVED`                                                                                                                                                                                                                               |
| `resolution_method`        | `exact_id` · `pattern` · `manual` · `none`                                                                                                                                                                                                                                                                                                                                |
| `citation_type`            | `document` · `document_version` · `page` · `paragraph` · `transcript` · `transcript_line` · `exhibit` · `witness` · `finding` · `decision` · `url` · `unknown`                                                                                                                                                                                                            |
| `source_system`            | `ksc_case_page` · `ksc_public_court_records` · `ksc_public_hearing` · `other_official_ksc`                                                                                                                                                                                                                                                                                |
| `document_version_type`    | `original` · `public_redacted` · `corrected` · `reclassified` · `translation` · `other`                                                                                                                                                                                                                                                                                   |
| `document_ingestion_state` | `discovered` · `downloaded` · `parsed` · `indexed` · `failed`                                                                                                                                                                                                                                                                                                             |
| `text_extraction_method`   | `none` · `native_text` · `ocr` · `manual`                                                                                                                                                                                                                                                                                                                                 |
| `examination_type`         | `direct` · `cross` · `redirect` · `recross` · `judge_question` · `unknown`                                                                                                                                                                                                                                                                                                |
| `witness_identity_status`  | `public` · `protected_code` · `unknown` — anything but `public` is protected                                                                                                                                                                                                                                                                                              |
| `party`                    | `spo` · `defence` · `victims_counsel` · `court` · `other`                                                                                                                                                                                                                                                                                                                 |
| `date_type`                | `event` · `document` · `filing` · `testimony` · `decision` — never merged (DESIGN_DECISIONS.md §7)                                                                                                                                                                                                                                                                        |
| `date_precision`           | `exact` · `month_only` · `year_only` · `range` · `approximate` · `unknown`                                                                                                                                                                                                                                                                                                |
| `claim_origin`             | `source_extracted` · `human` · `ai_extracted` — AI-extracted never means verified                                                                                                                                                                                                                                                                                         |
| `claim_stance`             | `supports` · `contradicts` · `qualifies` · `neutral` · `unclear` — scoped to the claim, never to a person                                                                                                                                                                                                                                                                 |
| `finding_link_type`        | `relies_on` · `supports` · `qualifies` · `context`                                                                                                                                                                                                                                                                                                                        |
| `argument_response_kind`   | `responds_to` · `disputes` · `concurs_with` · `rules_on`                                                                                                                                                                                                                                                                                                                  |
| `relationship_type`        | `mentioned_in` · `co_mention` · `testified_about` · `testified_at` · `cited_in` · `relies_on` · `supports` · `contradicts` · `qualifies` · `disputes` · `responds_to` · `associated_with` · `located_at` · `occurred_at` · `member_of` · `held_position_in` · `authored` · `filed_by` · `challenged_by` · `corroborated_by` · `part_of_incident` · `precedes` · `follows` |
| `entity_kind`              | `person` · `witness` · `organization` · `location` · `document` · `document_version` · `exhibit` · `incident` · `event` · `claim` · `finding` · `argument` · `hearing` · `transcript`                                                                                                                                                                                     |
| `identifier_kind`          | `filing` · `filing_version` · `exhibit` · `witness` · `transcript` · `finding` · `other`                                                                                                                                                                                                                                                                                  |
| `answer_block_kind`        | `court` · `evidence` · `testimony` · `spo` · `defence` · `ai`                                                                                                                                                                                                                                                                                                             |
| `ai_run_status`            | `pending` · `completed` · `failed`                                                                                                                                                                                                                                                                                                                                        |
| `ingestion_job_status`     | `pending` · `running` · `completed` · `failed` · `cancelled`                                                                                                                                                                                                                                                                                                              |

Common columns: every table has a `uuid` primary key (internal only; routes and
citations use the record's own identifier). Fact tables carry
`verification_state`, `verified_by`, `verified_at` (the `VerificationMixin`).
Most tables carry `created_at` / `updated_at`.

## Case and discovery provenance

| table            | purpose                                                                                                          | key columns / rules                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ---------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cases`          | top-level container; `KSC-BC-2020-06` seeded, `KSC-DEMO-0000` synthetic fixture                                  | `case_number` unique, `title`, `court`, `seat`, `official_source_url`, `description`                                                                                                                                                                                                                                                                                                                                                                                      |
| `source_records` | **where** a record was discovered, separate from **what** entity it became and from the stored file (roadmap §6) | `source_system`, `external_record_id` (unique per case + system), `record_type`, `language`, `discovery_url`, `canonical_source_url`, `title`, `visibility`, `raw_metadata` jsonb, `discovered_at`, `last_seen_at`; optional true FKs `document_id`, `document_version_id`, `hearing_id`, `transcript_id`. Phase 7 writes it from operator capture bundles; `raw_metadata.capture` records who / how / when, `raw_metadata.metadata_source` where the metadata came from. |

## Documents

| table                 | purpose                                                      | key columns / rules                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `documents`           | the logical filing / decision / judgment / transcript record | `official_ref` (unique per case; case / [sub-proceeding] / filing [/ annex], transcripts `…/T/<date>` — ADR-012), `filing_number` (indexed), `title`, `document_type`, `language`, `filing_party`, three independent dates, `visibility`, `ingestion_state`, `source_url`; Phase 8 generated `search_vector` with GIN index                                                                                                                                                                                                                                                                                                                                              |
| `document_versions`   | one publicly available artifact of a document                | `official_version_ref` (unique per document, e.g. `F01234/RED`), `version_type`, `version_label`, `visibility`, `public_date`, `source_url`, `storage_key`, `sha256` (**unique** when set — identical bytes are a duplicate, not a version), `mime_type`, `page_count`, `text_extraction_method`, `supersedes_version_id`; **Phase 7:** `artifact_status` (`not_fetched` \| `fetched` \| `failed`; CHECK: `fetched` ⇔ `sha256` and `storage_key` set — a metadata-only version carries the official URLs and nothing else), `byte_size`, `fetched_at`, `fetch_method` (`operator_browser_capture`, `http`). A public-redacted or corrected version is never overwritten. |
| `document_pages`      | page text as published                                       | exact zero-based `pdf_page_index` unique per version; nullable true `page_number` and `printed_page_label`; `text`, `running_head`, explicit `has_redactions` / extents — PDF and printed coordinates are never substituted                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `document_paragraphs` | numbered paragraphs                                          | unique `paragraph_number` per version, sequence, exact PDF index span, nullable printed-page span, text                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `document_sections`   | heading hierarchy                                            | `sequence` (unique per version), `level`, `heading`, `parent_section_id`, page and paragraph ranges                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `document_chunks`     | structural retrieval spans (no embedding)                    | `sequence`, `chunk_kind`, section, PDF / printed-page / paragraph ranges, `text`, `char_count`, generated `search_vector` + GIN                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |

## Hearings and transcripts

| table                 | purpose                        | key columns / rules                                                                                                                                                                                                                                          |
| --------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `hearings`            | a court session                | `hearing_date`, `session_sequence` (unique with date per case), `session_label`, `hearing_type`, `official_ref`, `source_url`, `visibility`                                                                                                                  |
| `transcripts`         | the transcript of a hearing    | `hearing_id`, `document_version_id` (unique when set — the official PDF), `official_ref`, `language`, `visibility`, `page_from` / `page_to` (running T. pages), `text_extraction_method`                                                                     |
| `transcript_segments` | Q/A blocks with T. coordinates | `sequence`, `pdf_page_index`, true transcript `page_number`, explicit line range, speaker/role only when printed, witness FK nullable, examination type, text, `closed_session` (empty text required), generated FTS vector + GIN. Lines are never invented. |
| `witness_appearances` | witness × hearing              | unique pair; `transcript_id`, `testimony_date`, page range                                                                                                                                                                                                   |

## Actors

| table            | purpose                                          | key columns / rules                                                                                                                                                                                                                                                                                                                                                                                                               |
| ---------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `persons`        | named persons in the public record               | `slug` (unique per case), `display_name`, `public_role`, `description`. **No score / rank / weight / probability column exists anywhere** (unit-tested over every table).                                                                                                                                                                                                                                                         |
| `person_aliases` | name variants                                    | `alias` unique per person, `language`                                                                                                                                                                                                                                                                                                                                                                                             |
| `witnesses`      | W-codes; a witness is not automatically a person | `code` (unique per case), `identity_status`, `person_id` nullable, `public_name` nullable, `called_by`, `protective_measures` jsonb. **CHECK**: `identity_status = 'protected_code'` ⇒ `person_id IS NULL AND public_name IS NULL`; `public_name` only when `identity_status = 'public'`. The API serialises a `public` block only for an explicitly public witness with a stored name; the block is absent, not null, otherwise. |
| `organizations`  | units and bodies                                 | `slug`, `name`, `kind`, `name_variants` jsonb                                                                                                                                                                                                                                                                                                                                                                                     |
| `locations`      | places with recorded spellings                   | `slug`, `name`, `name_variants` jsonb (Qirez / Çirez / Cirez / Ćirez are never merged away), `kind`                                                                                                                                                                                                                                                                                                                               |

## Evidence

| table                    | purpose                                                              | key columns / rules                                                                                                                                                                                                                      |
| ------------------------ | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exhibits`               | P-/D-numbered items                                                  | `official_exhibit_id` (unique per case), `title`, `description`, `tendered_by`, `through_witness_id`, `admitted_date`, `document_date`, `document_version_id` (public artifact), `visibility`                                            |
| `incidents`              | alleged events in case material — "as charged", not a determination  | `slug`, `title`, `summary`, `location_id`, `date_from` / `date_to` (`date_to ≥ date_from`), `date_precision`, `charges_pleaded` jsonb                                                                                                    |
| `events`                 | typed timeline items                                                 | `title`, `date_type` (five types, never merged), `date_from` / `date_to`, `date_precision` (a known precision needs a date), optional `incident_id`, `document_id`, `hearing_id`, `citation_id`, `source_record_id`, `extraction_origin` |
| `claims`                 | a proposition that exists in the research system — not a truth claim | `claim_key` (unique per case), `text`, `origin`, `created_by`, `source_citation_id`, verification                                                                                                                                        |
| `claim_mentions`         | claim → exact citation with stance                                   | unique (claim, citation); `stance`, `quote_text` (verbatim or nothing), `note`, verification                                                                                                                                             |
| `findings`               | court findings in the Court's words                                  | `finding_key` (unique per case), exact adjudicative document + version, `text`, `para_from` ≥ 1 / `para_to`, optional public entity/legal fields, own resolved coordinate, extraction origin, verification                               |
| `finding_evidence_links` | finding → citation                                                   | unique (finding, citation, link type); direction, explicit-Court-citation vs related basis (must agree with `court_cited`), source category, note, extraction origin, verification                                                       |
| `arguments`              | party (or Court) positions, distinct from findings                   | exact document + version and paragraph range; direct source vs Court summary vs missing source scope; underlying source ref where known; finding link, extraction origin, verification                                                   |
| `argument_responses`     | argument ↔ argument                                                  | unique (argument, response, kind); citation, note, extraction origin, verification; no self-response                                                                                                                                     |

## Citations — the resolution index (ADR-005)

`citations` separates three things:

- **source coordinate** — where the citing text appears: `source_document_version_id`,
  `source_page`, `source_pdf_page_index`, `source_para`, exact character start/end,
  `source_transcript_segment_id`, `source_url`;
- **the reference itself** — `raw_text`, `normalized_text`, `citation_type`;
- **resolved target** — real foreign keys `target_document_id`,
  `target_document_version_id`, `target_transcript_id`,
  `target_transcript_segment_id`, `target_exhibit_id`, `target_witness_id`,
  `target_finding_id`, with `target_page`, `target_para_from/to`,
  `target_line_from/to`, `target_pdf_page_index`.

Resolution columns: `resolution_state`, `resolution_method`,
`resolution_confidence` (0–1; about the string match, never about a person or
evidential weight), `resolved_at`, `display` (pre-formatted, e.g.
`F01234 · ¶45–46`), audit detail and ambiguous candidate identifiers, plus verification.

CHECKs: `resolved` ⇔ at least one target set and `resolved_at` present; anything
not resolved has **no** target and `display = 'UNRESOLVED'`; ranges are ordered;
pages ≥ 1. Ambiguous references are therefore never silently mapped.

`record_identifiers` is the lookup the resolver uses: `identifier`,
`normalized_identifier` (upper-cased, whitespace-collapsed), `identifier_kind`,
`entity_kind`, `is_primary`, and exactly one of `document_id`,
`document_version_id`, `exhibit_id`, `witness_id`, `transcript_id`, `finding_id`
(CHECK). Unique on (case, normalized identifier, entity kind); a lookup that
returns several rows is `ambiguous`. `GET /api/v1/citations/resolve?ref=` exposes
it. Phase 8 rebuilds this index and resolves citations once during ingestion;
requests read the persisted result and never guess.

## Graph

`graph_nodes` is a registry row per entity that can take part in the network:
`entity_kind`, `label`, and exactly one non-NULL foreign key among
`person_id`, `witness_id`, `organization_id`, `location_id`, `document_id`,
`exhibit_id`, `incident_id`, `event_id`, `claim_id`, `finding_id`,
`argument_id`, `hearing_id` (CHECK `num_nonnulls(...) = 1`, and the kind must
match the populated key). Each key is `ON DELETE CASCADE` and unique, so a node
cannot outlive its entity and an entity has at most one node. This is how
polymorphic references keep true referential integrity (ADR-010).

`relationships`: `from_node_id`, `to_node_id`, `relationship_type`,
`citation_id NOT NULL` (`ON DELETE RESTRICT` — a citation in use cannot be
deleted), `source_category`, `extraction_origin` (`source_documented`,
`deterministic_citation`, or `analytical`), optional relationship date and its
precision, `note`, verification. Unique on (from, to, type, citation); no self
loops. Public queries include an edge only when its citation is resolved, it is
not human-rejected, and both endpoints are public. Evidence-path traversal also
excludes analytical edges; every returned hop therefore has its own citation.

## Research notes and AI audit

| table                  | purpose                                             | key columns / rules                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ---------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `research_notes`       | notes, apart from evidence                          | optional `finding_id` and `appeal_issue_id`, `author`, `title`, `body`, `provenance` (`human` or `ai_assisted`); AI-assisted rows require `origin_ai_run_id`; `research_note_citations` stores the source set                                                                                                                                                                                                                                                       |
| `prompt_versions`      | every prompt text ever used                         | `name` + `version` unique, `template`, `template_sha256`                                                                                                                                                                                                                                                                                                                                                                                                            |
| `ai_runs`              | every AI invocation                                 | provider/model/parameters, prompt and system-prompt hash, question/input hash, structured output, validation errors, whole-answer withholding, token/cost fields, timestamps and status                                                                                                                                                                                                                                                                             |
| `ai_retrieval_sources` | immutable run source snapshots                      | passage-only rank/value, retrieval method, category/visibility, identifiers/URL, exact excerpt + SHA-256, page/paragraph/line coordinates, copied verification reviewer metadata, and exactly one source anchor; ranking never applies to a person                                                                                                                                                                                                                  |
| `ai_outputs`           | validated answer blocks in API order                | `sequence` unique per run, labelled kind/content type/text, AI-flagged verification; `ai_output_sources` links only the persisted retrieval whitelist and `ai_output_citations` retains resolved citations                                                                                                                                                                                                                                                          |
| `ingestion_jobs`       | one ingestion run (capture bundle, live probe)      | `source_system`, `job_type`, `status`, `cursor` (e.g. `bundle_id`) / `checkpoint` (last item) jsonb, four non-negative counts, timestamps, `error_summary`                                                                                                                                                                                                                                                                                                          |
| `ingestion_job_items`  | one record touched by a job, with a terminal status | `item_key` (unique per job; `<source_system>:<external id>`), `sequence`, `status` (`pending` · `downloaded` · `metadata_only` · `skipped_duplicate` · `not_public` · `failed_download` · `blocked_by_access_control` · `invalid_metadata` · `unsupported_artifact` · `ambiguous_mapping`), `reason`, `detail` jsonb (identifiers, URLs, hashes, per-version outcomes — never text), optional FKs to `source_records`, `documents`, `document_versions`, timestamps |
| `audit_log`            | append-only system / reviewer actions               | `occurred_at`, `actor`, `action`, `entity_type`, `entity_id`, `detail` jsonb — never document text or protected identity                                                                                                                                                                                                                                                                                                                                            |

## Appeal research and red team

| table                     | purpose                                                  | key columns / rules                                                                                                                                                                                                                                                                           |
| ------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `appeal_issues`           | neutral potential issues for human review                | unique case + `issue_key`; category and legal/factual/sentencing/procedural context; required canonical `finding_id`; Court treatment; neutral red-team result; notes, extraction origin and verification. No score, rank, probability, credibility or outcome field.                         |
| `appeal_issue_sources`    | exact source-backed roles in an issue research structure | required `citation_id`, ordered role (`court_reasoning`, legal standard, evidence relied, party positions, Court response, supporting, contrary or qualifying), source category, exact excerpt, optional canonical argument/evidence-link anchor, and verification.                           |
| `appeal_missing_material` | explicit absent or unresolved research dependencies      | unique issue + reference; kind, reason and state (`source_unavailable`, `court_treatment_not_located`, `unresolved`). Missing material is not an affirmative relationship and `not located` is not “ignored.”                                                                                 |
| `statement_comparisons`   | comparison of two exact public passages                  | unique case + key; two distinct citation FKs, separate excerpts/speakers, comparison type, neutral classification (`possible_contradiction`, `qualification`, `timeline_difference`, `consistent`, `not_comparable`), explanation and verification. It cannot store a credibility conclusion. |
| `red_team_reviews`        | one neutral result over an issue                         | result (`supported_for_review`, `qualified`, `countered`, `insufficient_record`); human or AI-assisted origin. An AI-assisted row requires an audited `ai_run_id`; verification remains separate and cannot auto-promote.                                                                     |
| `red_team_findings`       | ordered multi-perspective review observations            | perspective (`defence_analyst`, `spo_red_team`, `neutral_reviewer`), neutral category, text, optional citation and verification. An affirmative observation requires a citation; only an explicit missing citation, legal/human question, or source limitation may be uncited.                |

The real Phase 12 projection keeps the canonical Phase 10 finding and evidence
links unchanged. It adds one `NEEDS_MORE_EVIDENCE` issue, five human-verified
source links, one human-verified two-citation comparison, one human red-team
review, four red-team findings, and four explicit missing-material rows.

## External media and public statements

These tables are outside the court-record hierarchy. Public availability is
provenance, not proof, and never implies admission or reliance.

| table                         | purpose                               | key columns / rules                                                                                                                                                                                                                                                                                                                     |
| ----------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `external_sources`            | public publisher/platform provenance  | case + canonical URL unique; platform, source type, publisher/account, language, public visibility, permitted access method, terms and coverage notes; public-only CHECK and verification.                                                                                                                                              |
| `media_items`                 | one captured public URL               | original/canonical URL, title/publisher, distinct publication and capture timestamps, language, exact captured-text SHA-256, transcript origin, original/repost/clip/embed state, archive metadata and public-only access state.                                                                                                        |
| `media_statements`            | exact source fragment                 | ordered item anchor, optional confidently public person link, speaker label, exact text/hash, character or timecode coordinates, transcript origin and verification. Protected witness identity is never inferred.                                                                                                                      |
| `court_media_links`           | the sole external-to-court bridge     | explicit status (`external_only`, `mentioned`, `tendered`, `admitted`, `rejected`, `discussed`, `relied_upon`, `unknown`); every status beyond external/unknown requires a court citation and human verification. Runtime also requires that citation to resolve. Optional document/exhibit/finding anchors never replace the citation. |
| `media_statement_comparisons` | neutral comparison over exact sources | external statement A plus exactly one external statement or court citation B; only Possible Contradiction, Qualification, Timeline Difference, Consistent or Not Comparable; explanation, extraction origin and verification, never credibility.                                                                                        |

## Invariants tested

Phase 20A (`0015`, ADR-027) adds source-native geometry and anchors:

- `document_pages` stores version-specific dimensions, rotation, geometry
  extraction method/state and extractor plus processing-run lineage.
- `page_text_geometry` is a derived word-level layer keyed by exact version and
  PDF page. Its character ranges explicitly name `page_geometry_text` as their
  basis. Rectangles are positive, in-bounds top-left PDF points; native and OCR
  extraction methods remain distinct.
- `source_spans` stores exact text/coordinate provenance plus one explicit
  precision state. `source_regions` exists only for validated geometry.
- `source_anchors` binds entity occurrences, citations, relationship evidence
  and findings to reusable spans. It contains no untyped score or guessed
  rectangle.
- Related versions cannot share geometry through the schema: every geometry
  row and span carries the exact `document_version_id`.

Phase 20B (`0016`, ADR-028) adds `transcript_segment` to the anchor object
types (one anchor per segment, line-box regions only when validated) and
`transcript_page_contexts`: one row per transcript page whose official running
header states a witness code or officially printed name, a session state
(`open`/`private`/`closed`) and an optional examination heading, with exact
`document_pages.text` offsets and rule lineage.

Phase 17C adds `entity_occurrences`: exactly one person, witness, organization
or exhibit target plus the held document version, optional transcript segment,
original occurrence text and exact page/line/character coordinates. The row
also carries deterministic extraction origin and review-required state. Exhibit
`status` is explicit and defaults to `unknown`; filenames never establish it.

Phase 19A (`0013`, ADR-024) adds mention lineage to `entity_occurrences`:
`rule_id`/`rule_version`, `projection_run_id` → `processing_runs`,
`mention_state` (`verified` · `review_required` · `rejected`, kept consistent
with `review_required` by CHECK), `char_anchor` (the text the character range
indexes: segment text, speaker label or page text), `paragraph_number` and
`language`. The idempotency key is (version, anchor, segment, PDF page, char
range, entity, rule) with `NULLS NOT DISTINCT`.

Phase 19B (`0014`, ADR-025):

- `citations.resolution_rule`: the machine-readable rule behind every terminal
  state (for example `identifier.zero_padded`, `transcript.hearing_date`,
  `ambiguous.subcase_bare_filing`, `unresolved.target_not_held`).
- `person_aliases.alias_kind` (`speaker_label` · `full_name`). A `full_name`
  alias requires source version, PDF page, character range and rule (CHECK).
- `witness_appearances`: the subject is exactly one of `witness_id` (code) and
  `person_id` (publicly named). There is one row per transcript version, and the
  header signal's exact page span is stored with session page counts, verbatim
  examination headers and rule/run lineage. Unique key: (witness, person,
  hearing, transcript), `NULLS NOT DISTINCT`.
- `exhibit_status_events`: new table. It holds the history of explicit
  court-record statements (`number_assigned` · `admitted` · `rejected` ·
  `marked_for_identification` · `withdrawn`), with verbatim identifier, optional
  bound exhibit, classification, statement date, exact segment span, speaker and
  rule. `exhibits.status_event_id` points to the event establishing a
  non-`unknown` status.
- `relationships`: exactly one evidence anchor, `citation_id`,
  `entity_occurrence_id` or `witness_appearance_id` (CHECK). `evidence_count` is
  ≥ 1 and is a count, never a weight. New origin: `deterministic_occurrence`.

- The table set includes the foundation through Phase 13 plus the five Phase 14
  external-source tables; `alembic check` reports no drift between
  models and the migrated schema.
- No person field contains score / rank / rating / weight / priority /
  probability / likelihood. The only rank/value fields added in Phase 11 order
  retrieved passages and cannot reference a person.
- The migration chain preserves existing records; the current
  `0009 → 0010 → 0009 → 0010` round trip is clean and `alembic check` reports
  no model/schema drift.
- Protected witness without identity; page and line validation; SHA-256
  duplicates; resolved/unresolved target consistency; mandatory relationship
  provenance; node registry exactly-one-target; reviewer-required verification.
- The synthetic fixture (`ksc-demo-fixture`, case `KSC-DEMO-0000`) proves
  Document → Version → Page → Citation, Witness → Transcript → Segment →
  Citation, Claim → Mention → Citation → Source, Finding → Evidence Link →
  Citation → Source and Relationship → Citation → Source. Nothing in it is a real
  record.
- Phase 12 tests cover exact two-source comparisons, issue-source whitelisting,
  human-review requirements, missing material, `not_located` versus “ignored,”
  and fail-closed AI success/credibility claims. The real quality gate confirms
  all seven distinct citations navigate and authoritative finding/evidence state
  is unchanged.

## Not yet

- Embedding column on `document_chunks`; the Phase 11 measured baseline uses
  structured records plus PostgreSQL FTS. The public Trial Judgment is not held.
