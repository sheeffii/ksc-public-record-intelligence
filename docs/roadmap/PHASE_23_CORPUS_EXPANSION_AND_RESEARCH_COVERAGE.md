# Phase 23 — Corpus Expansion & Research Coverage

Status: **IN PROGRESS**  
Current pass: **23C — reconciliation and closeout (open issues remain)**  
Started: 2026-09-29  
Checkpoint: `docs/ingestion/PHASE23_CLOSEOUT_REPORT.md` (2026-10-02)

## Goal

Expand the real public `KSC-BC-2020-06` corpus toward thousands of records by
using the permitted Legal Tools Database mirror as an acquisition source while
keeping the official KSC identity, official URL and document bytes as the
authoritative court record. Import counts never override provenance, identity,
public-status, language, protected-witness or citation-integrity rules.

## Permanent boundaries

- ADR-030's written-permission gate must pass before any mirror PDF download.
- Legal Tools is a byte mirror, not the court source or a parallel data model.
- Only lawfully public English and Albanian records are in scope. Serbian,
  confidential, uncertain and identity-conflicting material is skipped or
  quarantined.
- Official reference, official artifact URL, PDF header and SHA-256 determine
  canonical identity. Metadata disagreement is never guessed through.
- Every accepted record uses the existing capture, validation, import, parse,
  resolution, evidence, intelligence, SourceAnchor and search pipeline.
- A failed candidate must not abort the remainder of a batch.
- Phase 16 remains separate and is not closed by this work.

## 23A — Readiness and approximately 100-document pilot

1. Integrate the existing Legal Tools harvester with current `main`.
2. Verify permission and provenance fields: mirror PURL,
   `fetch_method = legal_tools_mirror`, acquisition time, official KSC URL and
   official version identity.
3. Reject or quarantine Serbian transcripts mislabeled as English; preserve
   EN/SQ as separate versions; resolve same-date transcript identity without a
   date-only collision; verify RED/RED2/COR/annex handling; skip held URLs and
   SHA-256 duplicates; keep unproven generic origins review-required.
4. Produce a non-random pilot plan of approximately 100 genuinely new records
   with strong deterministic identity. Report the planned language and filing
   category distribution before downloading.
5. Download only the pilot with the configured pacing. Stop immediately on an
   access-control challenge or block pattern.
6. Validate every PDF against its KSC case/reference, first-page/header,
   public status, language and logical document/version identity. Classify every
   candidate as accepted, duplicate, quarantined or failed with a reason.
7. Import accepted records through the canonical pipeline and run the existing
   reconciliation order: parse; re-resolve; structured projection; re-resolve;
   evidence; intelligence; legal matrix where applicable; geometry/transcript
   synchronization; SourceAnchors and search.
8. Record exact before/after corpus, intelligence, relationship, citation and
   SourceAnchor counts. Inspect newly imported filing, search, dossier,
   evidence, Reader, EN/SQ and party-attribution flows.
9. Record new source/data patterns without generalizing from one anomaly.

### 23A acceptance

- Permission and source-authority gates pass.
- Acquisition and canonical import are deterministic and idempotent.
- No canonical-model redesign or Legal-Tools-specific UI is required.
- Integrity/data-quality gates and focused real-data workflows pass.
- The pilot report is saved at
  `docs/ingestion/PHASE23A_CORPUS_PILOT_REPORT.md`.
- The Phase 23 branch is committed and pushed.

After this acceptance checkpoint, **STOP**. Do not begin 23B without explicit
authorization. Phase 23 remains in progress.

## 23B — Staged expansion

Requires explicit authorization after reviewing 23A.

Progression: approximately 300–500 new records → inspect → approximately 1,000
→ inspect → remaining safe historical corpus. Record parse, geometry,
re-resolution and SourceAnchor timing plus quarantine/failure counts at each
gate. Complete server-driven directory/search/timeline scaling work before it
is required by measured load.

## 23C — Reconciliation and closeout

Requires explicit authorization after 23B. Run final reconciliation,
coverage/scale and source-fidelity audits, rebuild research intelligence,
verify all acceptance criteria against repository and database reality, update
the milestone records, run the required final gates, and only then close and
tag Phase 23.

## 23A verification scope

Use ingestion/data-quality gates, focused Legal Tools and reconciliation tests,
a small set of real-data UI/Reader flows, and relevant static checks. Do not run
broad full suites during the pilot checkpoint.

