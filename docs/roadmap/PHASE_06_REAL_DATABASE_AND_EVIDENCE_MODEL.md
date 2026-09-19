# Phase 6 — Real Database / Evidence Model

**Status:** Next core architecture phase.

## Goal

Build the normalized persistent evidence/domain model that will later receive real public KSC records.

This is a schema/API foundation phase. **Do not ingest real KSC documents yet.**

## Why this phase matters

The quality of Phases 7–13 depends on getting distinctions such as these right:

- `Document` vs `DocumentVersion`;
- `Person` vs `Witness`;
- `Claim` vs `Court Finding`;
- `Incident` vs `Event`;
- `Citation` vs source coordinate;
- `Citation` vs resolved target;
- source discovery vs normalized entity;
- relationship existence vs legal significance;
- public/redacted/unknown/private visibility.

A schema mistake made before 10 records is cheap. A schema mistake discovered after thousands of records is expensive.

## Non-negotiable architecture

```text
PRIMARY COURT SOURCE
        ↓
PERSISTED SOURCE RECORD
        ↓
STRUCTURED EVIDENCE
        ↓
PROVENANCE / CITATIONS
        ↓
RELATIONSHIPS
        ↓
SEARCH / NETWORK / ANALYSIS
        ↓
AI
```

## Required domain entities

Implement normalized models for at least:

- cases;
- source/discovery records;
- documents;
- document versions;
- pages;
- sections;
- chunks;
- hearings;
- transcripts;
- transcript segments;
- persons;
- witnesses;
- witness appearances;
- organizations;
- locations;
- exhibits;
- incidents;
- events;
- claims;
- claim mentions;
- findings;
- finding evidence links;
- arguments;
- argument responses;
- citations;
- identifier/alias resolution foundation;
- relationships;
- research notes;
- AI run/output/prompt audit tables;
- ingestion jobs;
- audit logs.

## Cases

Preserve existing `KSC-BC-2020-06` metadata.

Use internal UUID identity and separate external case number.

## Official source/discovery provenance

Future ingestion may discover records from more than one official KSC surface.

The schema should preserve **where a record was discovered** separately from **what normalized entity it represents**.

Suggested concept:

```text
source_records
```

Fields may include:

- `id`;
- `case_id`;
- `source_system`;
- `external_record_id`;
- `record_type`;
- `language`;
- `discovery_url`;
- `canonical_source_url`;
- `title`;
- `visibility`;
- `raw_metadata` JSONB;
- `discovered_at`;
- `last_seen_at`;
- optional resolved `document_id`, `document_version_id`, `hearing_id`, `transcript_id`.

Possible future source systems:

- `KSC_CASE_PAGE`;
- `KSC_PUBLIC_COURT_RECORDS`;
- `KSC_PUBLIC_HEARING`;
- `OTHER_OFFICIAL_KSC`.

Do not fetch these sources in Phase 6.

## Documents and versions

### Document

Represents the logical filing/material.

Support fields such as:

- official document ID;
- filing number;
- document type;
- title;
- language;
- filing party;
- filing/original/public dates;
- visibility;
- source URL;
- processing status.

### DocumentVersion

Represents a specific publicly available artifact/version.

Support:

- official version ID;
- version type;
- visibility;
- source URL;
- object storage key;
- SHA-256;
- MIME type;
- page count;
- text extraction method;
- supersedes/related version.

Never overwrite a public-redacted/corrected version with another version.

## Pages, sections, chunks

### Pages

Store real page number only when known.

Unique by version + page number.

### Sections

Hierarchical structure for headings, judgment sections, etc.

### Chunks

Preparation for later retrieval. Structural, not arbitrary fixed-size-only design.

Embedding may be nullable if useful for future schema compatibility, but do not generate embeddings now.

## Hearings / transcripts

Model:

```text
Hearing
  ↓
Transcript
  ↓
Transcript Segment
```

Transcript segments should support:

- page number nullable;
- line start/end nullable;
- speaker;
- witness reference nullable;
- examination type;
- text;
- deterministic sequence number.

Examination types:

- DIRECT;
- CROSS;
- REDIRECT;
- RECROSS;
- JUDGE_QUESTION;
- UNKNOWN.

Never invent lines.

## Person vs witness

A witness is not automatically a public person.

Witness should support:

- public code;
- optional person reference;
- identity status (`PUBLIC`, `PROTECTED_CODE`, `UNKNOWN`);
- optional public name only when lawful/public.

Protected witness must be representable with no person identity.

## Exhibits

Store official exhibit ID separately from internal UUID.

Prepare for links to public document artifacts where applicable.

## Incident vs event

### Incident

A structured incident relevant to case material. A stored incident does not automatically mean every allegation about it is established fact.

### Event

Broader timeline item used to distinguish:

- historical event date;
- document date;
- filing date;
- testimony date;
- decision date.

Support uncertain/date precision:

- EXACT;
- MONTH_ONLY;
- YEAR_ONLY;
- RANGE;
- APPROXIMATE;
- UNKNOWN.

## Claims

A `Claim` means:

> This proposition exists in the structured research system.

It does **not** mean the proposition is true.

Support creation source:

- `SOURCE_EXTRACTED`;
- `HUMAN`;
- `AI_EXTRACTED`.

AI-extracted never means verified.

## Claim mentions

Link claims to exact citations with stance:

- SUPPORTS;
- CONTRADICTS;
- QUALIFIES;
- NEUTRAL;
- UNCLEAR.

Contradiction does not imply dishonesty.

## Findings

A `Finding` represents a court finding, not an AI conclusion.

Support:

- judgment document;
- finding key;
- person/charge/legal element/incident where relevant;
- exact court finding text;
- paragraph coordinates;
- verification.

## Finding evidence links

Connect finding → citation with relationship such as:

- RELIES_ON;
- SUPPORTS;
- QUALIFIES;
- CONTEXT.

Track whether the Court explicitly cited the source.

## Arguments

Keep party arguments distinct from findings.

Party values may include:

- SPO;
- DEFENCE;
- VICTIMS_COUNSEL;
- COURT;
- OTHER.

Support response relationships with citations.

## First-class citations

Citation is one of the central models.

Support:

- raw citation;
- normalized citation;
- type;
- source document/version/page;
- page/paragraph coordinates;
- transcript/segment/page/line coordinates;
- exhibit;
- witness;
- source URL;
- resolution status;
- resolution confidence;
- resolver method;
- verification timestamp.

Resolution states:

- `RESOLVED`;
- `UNRESOLVED`;
- `AMBIGUOUS`;
- `INVALID`.

Ambiguous references must never be silently mapped.

## Citation resolution index foundation

Prepare persisted identifier/alias structures for future references such as:

```text
F01234
F01234/RED
F01234/COR
P00123
W01234
```

Do not implement the full resolver yet.

Future flow:

```text
Ingestion
→ citation extraction
→ normalization
→ resolution
→ persisted resolution index
→ fast runtime lookup
```

## Relationships / evidence graph

Every production relationship should eventually require provenance.

Support relationship types such as:

- MENTIONED_IN;
- CO_MENTION;
- TESTIFIED_ABOUT;
- TESTIFIED_AT;
- CITED_IN;
- RELIES_ON;
- SUPPORTS;
- CONTRADICTS;
- QUALIFIES;
- DISPUTES;
- RESPONDS_TO;
- ASSOCIATED_WITH;
- LOCATED_AT;
- OCCURRED_AT;
- MEMBER_OF;
- HELD_POSITION_IN;
- AUTHORED;
- FILED_BY;
- CHALLENGED_BY;
- CORROBORATED_BY;
- PART_OF_INCIDENT;
- PRECEDES;
- FOLLOWS.

A connection does not imply wrongdoing.

If polymorphic generic UUID references are used, document how referential integrity is enforced. Do not pretend a generic UUID is a true foreign key when it is not.

## Visibility

Support at least:

- PUBLIC;
- PUBLIC_REDACTED;
- UNKNOWN;
- PRIVATE_AUTHORIZED.

Current product mode is public-only.

Default public query behavior:

- PUBLIC → include;
- PUBLIC_REDACTED → include that public representation;
- UNKNOWN → exclude;
- PRIVATE_AUTHORIZED → exclude.

Fail closed.

## Verification

Support consistent states:

- UNREVIEWED;
- AI_FLAGGED;
- HUMAN_VERIFIED;
- HUMAN_REJECTED;
- NEEDS_MORE_EVIDENCE;
- UNRESOLVED.

Never auto-promote AI output to human verified.

## Research notes

Store human notes separately from court evidence and label as human provenance.

## AI audit schema

Create tables such as:

- `ai_runs`;
- `ai_outputs`;
- `prompt_versions`.

No model calls in Phase 6.

Future audit fields include provider/model/temperature/prompt hash/retrieved sources/tokens/cost/output.

## Ingestion jobs

Schema foundation only:

- source;
- case;
- job type/status;
- cursor/checkpoint;
- counts discovered/downloaded/processed/failed;
- timestamps;
- error summary.

## Migrations

Upgrade cleanly from Phase 4 migration history.

Preserve existing case/audit data.

Test upgrade → downgrade where practical → re-upgrade.

## Synthetic fixture

Use clearly synthetic IDs, e.g.:

- `F-DEMO-001`;
- `F-DEMO-001/RED`;
- `W-DEMO-001`;
- `P-DEMO-001`.

Prove traversals:

```text
Document → Version → Page → Citation
Witness → Transcript → Segment → Citation
Claim → Mention → Citation → Source
Finding → Evidence Link → Citation → Source
Relationship → Citation → Source
```

Do not invent substantive allegations about real people.

## API/domain layer

Expose typed read boundaries using service/repository + Pydantic contracts.

Possible routes:

- cases;
- documents;
- people;
- witnesses;
- exhibits;
- incidents;
- findings;
- citations;
- relationships;
- network.

Use pagination and safe public filtering.

Do not expose raw ORM objects directly.

## Frontend repository boundary

Keep `MockRepository` working.

Add an `ApiRepository` implementation alongside it.

Mock remains default during Phase 6.

Prove swapability without rewriting UI.

## Source-origin addition

The schema must be able to later preserve a chain such as:

```text
Official KSC case page
      ↓ discovered hearing
Public Court Records record
      ↓ official transcript/PDF
Document / Version
      ↓
Structured transcript/pages/citations
```

Discovery source, normalized entity, and stored file are distinct concepts.

## Out of scope

Do not:

- crawl KSC;
- download real PDFs;
- parse real transcripts;
- ingest real witnesses/exhibits;
- use external AI;
- generate embeddings;
- perform legal conclusions;
- perform appeal analysis;
- remediate broad UI visual parity (Phase 5B handles that).

## Testing

Add serious tests for:

- identifier scoping;
- document/version uniqueness;
- SHA duplicate handling;
- pages/line validation;
- protected witness without person;
- visibility fail-closed behavior;
- citation states;
- identifier lookup foundation;
- claims/mentions;
- findings/evidence links;
- provenance-backed relationships;
- API pagination/filtering/serialization;
- migration path;
- synthetic evidence traversal;
- ApiRepository mapping.

Maintain all existing Phase 4/5 tests.

## Acceptance criteria

Phase 6 is complete when:

- normalized schema exists;
- provenance, visibility, verification, versioning are first-class;
- citation model and resolution-index foundation exist;
- protected witness is safe;
- relationships require provenance;
- source-origin/discovery provenance is representable;
- API boundaries exist;
- frontend API repository boundary exists;
- migrations/tests/lint/typecheck/build pass;
- docs/memory/state/ADRs are updated;
- no real KSC records were ingested.

## Stop condition

Do not begin Phase 7.

## Completion report

```text
PHASE 6 STATUS
DATABASE MODEL
MIGRATIONS
API
FRONTEND INTEGRATION
PROVENANCE / CITATIONS
TESTS
SECURITY
DECISIONS
KNOWN LIMITATIONS
COMMITS
NEXT
MEMORY
```
