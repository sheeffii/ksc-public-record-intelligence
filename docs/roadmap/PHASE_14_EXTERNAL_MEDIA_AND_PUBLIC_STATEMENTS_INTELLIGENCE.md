# Phase 14 — External Media & Public Statements Intelligence

**Status:** Post-core future feature. Do not execute until the core court-record platform is stable through Phase 13.

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

- external media layer is clearly separate;
- lawful source collection is documented;
- court status is explicit and citation-backed;
- public statements can be compared without unsafe credibility labels;
- users can see whether an item was mentioned/tendered/admitted/rejected/discussed/relied upon;
- external search never silently contaminates court-record search;
- coverage limitations are visible;
- all privacy/access rules hold.

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
