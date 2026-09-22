# Phase 14 — External Media & Public Statements Intelligence

**Status:** COMPLETE (2026-09-22) — controlled real-public-source quality gate PASS (ADR-021).

## Goal

Add a clearly separated research layer for **lawfully public external media and public statements**—such as news reports, public interviews, press conferences, public social posts, public videos, podcasts, and public speeches—while preserving a strict distinction between:

```text
EXTERNAL CONTEXT
```

and

```text
COURT RECORD / COURT EVIDENCE
```

This phase must never allow an online statement to become “court evidence” merely because it exists on the internet.

## Why this feature comes last

The court-record platform must first be trustworthy on its own.

Only after exact court citations, evidence status, findings, appeal research, and corpus ingestion are mature should external context be added. Otherwise external material risks confusing the source hierarchy.

## Core question for every external item

For every public article/video/post/interview, the system should be able to distinguish:

```text
Was this merely public commentary?
Was it mentioned in the court record?
Was it tendered by a party?
Was it admitted as evidence?
Was it rejected?
Was it discussed by the Court?
Was it actually relied upon by the Court?
Is the status unknown?
```

These are materially different states.

## Court status taxonomy

Support explicit status such as:

- `EXTERNAL_ONLY`;
- `MENTIONED`;
- `TENDERED`;
- `ADMITTED`;
- `REJECTED`;
- `DISCUSSED`;
- `RELIED_UPON`;
- `UNKNOWN`.

A status should be source-backed by court citation where applicable.

## External source types

Potentially support public material from:

- news portals;
- television/radio sites;
- YouTube;
- public Facebook pages/posts;
- public TikTok posts where lawfully accessible;
- X/public social posts;
- podcasts;
- public press conferences;
- public speeches;
- public institutional releases;
- public archives.

Do not assume every platform permits automated collection.

## Access / legal rules

Never:

- bypass login;
- scrape private profiles;
- defeat anti-bot/access controls;
- use stolen/private datasets;
- circumvent platform restrictions;
- reconstruct deleted/private content from unauthorized sources.

Prefer:

- official APIs where available and permitted;
- public webpages;
- manually submitted URLs;
- lawful archives;
- user-provided public source links.

Document provider/platform terms and collection method.

## Data model

Potential models:

### `external_sources`

- platform/domain;
- source type;
- publisher/account;
- canonical URL;
- visibility/access method;
- language;
- trust/provenance metadata that does **not** imply truth.

### `media_items`

- source/platform;
- URL/canonical URL;
- title;
- publisher;
- public speaker/person reference if confidently public;
- published timestamp;
- captured timestamp;
- language;
- content hash where lawful/practical;
- transcript/text where permitted;
- source metadata;
- archive metadata.

### `media_statements`

Source-backed statement fragments with exact timecode/text position where available.

### `court_media_links`

Connect media item to:

- court document;
- exhibit;
- citation;
- finding;

with court status (`MENTIONED`, `TENDERED`, etc.) and exact court citation.

## Provenance

For external items preserve:

- original URL;
- platform;
- publisher/account;
- publication timestamp if known;
- capture timestamp;
- content hash if available;
- transcript origin;
- whether content is original, repost, clip, or article embedding;
- court link/status separately.

## Verification challenges

External media may be:

- edited;
- clipped;
- reposted;
- deleted;
- misdated;
- mislabeled;
- duplicated;
- missing context.

Do not treat an external item as authentic solely because it is popular or repeated by many portals.

Use verification state and preserve uncertainty.

## Public statements comparison

Where lawful/public and useful, compare:

```text
External public statement
        ↓
Prior court/public statement
        ↓
Trial testimony
        ↓
Cross-examination
        ↓
Court finding / treatment
```

Allowed analytical labels remain:

- Possible Contradiction;
- Qualification;
- Timeline Difference;
- Consistent;
- Not Comparable.

Never automatically call someone a liar.

## Court-evidence bridge

A powerful workflow should answer:

> Show external/public media items that are actually present in the official court record.

Then distinguish:

```text
External item
   ↓
Court filing citation
   ↓
Exhibit (if any)
   ↓
Admissibility decision (if any)
   ↓
Judgment/finding reliance (if any)
```

## “Was this used as evidence?” view

For a media item display:

- external source details;
- court status;
- filing/exhibit identifiers;
- admission/rejection status;
- exact court decision citation;
- judgment/findings that reference it;
- verification state.

If unknown, say `UNKNOWN`; do not infer.

## Media / influence research

The platform may organize public statements by public figures, journalists, commentators, institutions, or other identifiable public speakers, but it must not infer political motives or use influence/popularity as evidence.

Useful neutral research questions:

- What did this public source say and when?
- Was the statement later cited in the court record?
- Was it admitted or rejected?
- Was it relied upon by a finding?
- Does a later public/testimony statement materially differ?
- Was that difference before the Trial Panel?
- How did the Court address it, if at all?

## Search

Support separate modes:

- `Court Record Only`;
- `External Public Sources`;
- `Both — clearly separated`.

Never silently mix result types.

## UI badges

Examples:

```text
EXTERNAL PUBLIC SOURCE
MEDIA REPORT
PUBLIC STATEMENT
MENTIONED IN COURT RECORD
TENDERED
ADMITTED COURT EXHIBIT
REJECTED
COURT-DISCUSSED
COURT-RELIED MATERIAL
STATUS UNKNOWN
```

## AI usage

AI may:

- transcribe/segment where lawful;
- summarize external items;
- compare statements;
- find court references;
- suggest possible links for human review.

AI may not:

- decide authenticity without evidence;
- decide truth from repetition;
- promote an external item to court evidence;
- infer hidden identities;
- generate unsupported accusations.

## Platform connectors / ingestion strategy

Implement each platform independently, with explicit permission/terms review.

Start with the easiest legally/publicly accessible sources, perhaps:

1. manually submitted public URLs;
2. news/public institutional webpages;
3. YouTube/public video metadata;
4. platform APIs where available/authorized;
5. other social platforms only after access rules are understood.

Do not promise “all of Facebook/TikTok.” Coverage should be reported honestly.

## Testing

Test:

- external/court source separation;
- court-status transitions require evidence/citation;
- private/login-gated sources are not ingested;
- duplicate/repost detection;
- publication/capture timestamp distinction;
- statement comparison provenance;
- external search filters;
- UI does not label external-only content as court evidence;
- AI cannot auto-promote status.

## Acceptance criteria

Phase 14 is complete when:

- [x] external media layer is clearly separate;
- [x] lawful source collection is documented;
- [x] court status is explicit and citation-backed;
- [x] public statements can be compared without unsafe credibility labels;
- [x] users can see whether an item was mentioned/tendered/admitted/rejected/discussed/relied upon;
- [x] external search never silently contaminates court-record search;
- [x] coverage limitations are visible;
- [x] all privacy/access rules hold.

## Stop condition

Do not expand to private/unauthorized data. Future extensions require a new explicit milestone and legal/privacy review.

## Completion report

```text
PHASE 14 STATUS
EXTERNAL SOURCES
COLLECTION METHODS
MEDIA DATA MODEL
COURT STATUS LINKS
STATEMENT COMPARISON
SEARCH / UI
ACCESS / PRIVACY
AI USE
COVERAGE LIMITATIONS
TESTS
COMMITS
NEXT
MEMORY
```

## Completion Record

- Closeout audit: **PASS**, 2026-09-22. The complete phase specification and
  every acceptance criterion were checked against implementation commit
  `9ff9a2b`, migration `0010`, the migrated real database, API/UI, rebuilt
  healthy Docker stack, automated tests, desktop/mobile Playwright and the
  tracked real-data quality report.
- External sources: a controlled manifest holds 3 genuinely public pages from
  2 publishers (2 BIRN reports and 1 Human Rights Watch institutional release).
  It retains canonical/original URL, publisher, distinct publication/capture
  timestamps, access method, short exact excerpt, SHA-256, transcript origin,
  review state, terms note and coverage limitation. No site was crawled and no
  full article was mirrored.
- Collection/access: the manual-URL importer accepts only explicit public HTTPS
  sources and rejects credentials, local/non-global IPs, private/restricted
  state, invalid timestamps, changed hashes, duplicate canonical URLs and
  non-exact statements. Login, CAPTCHA, Cloudflare, private profiles, paywalls
  and platform restrictions are never bypassed.
- Model/provenance: `external_sources`, `media_items`, `media_statements`,
  `court_media_links` and `media_statement_comparisons` remain outside the
  court-record hierarchy. Stronger court statuses require an exact citation and
  human verification in PostgreSQL; reads additionally require a resolved,
  same-case citation.
- Court status: all 3 real items are `EXTERNAL_ONLY`. No exact court citation
  establishing one of these media-item relationships was found, so no
  `MENTIONED`, `TENDERED`, `ADMITTED`, `REJECTED`, `DISCUSSED` or
  `RELIED_UPON` relationship was invented. The full taxonomy is enforced and
  visible; the external-to-court network has zero edges.
- Comparison/search/UI: 3 exact hash-verified statements and 1 human-reviewed
  `NOT COMPARABLE` comparison are exposed without a credibility inference.
  `/media` offers Court Record Only, External Public Sources and Both — clearly
  separated modes, status filters, explicit badges, original-source links and
  visible coverage limitations in English and Albanian.
- AI/appeal boundary: the Phase 11 court-record retrieval whitelist is
  unchanged and rejects external material as Court evidence. The Phase 12
  neutral comparison vocabulary is reused, while external anchors remain in
  their own provenance domain; no appeal issue or red-team conclusion is
  created from external-only material.
- Real-data gate: 2 sources · 3 items · 3 exact statements · 3 external-only
  status rows · 1 comparison · 0 citation-backed or invalid court links · 0
  duplicate URLs · 0 manifest/database mismatches · 0 verification or access
  violations · 0 external sources in court-record AI retrieval · PASS.
- Tests/gates: 283 backend and 204 frontend tests pass; lint, formatting, mypy,
  TypeScript, production build, `0009 → 0010 → 0009 → 0010`, `alembic check`,
  live API/readiness checks and 4 Phase 14 Playwright tests across desktop and
  mobile pass.
- Evidence: `docs/ingestion/PHASE14_QUALITY_GATE.md`,
  `docs/ingestion/phase14-quality-gate.json` and
  `docs/ingestion/manifests/phase14-external-media.json`.
- Scope stop: coverage is deliberately small and non-comprehensive. No private,
  deleted, restricted, paywalled or login-gated source and no comprehensive
  Facebook, TikTok or X coverage was added. No later phase is defined or begun.
