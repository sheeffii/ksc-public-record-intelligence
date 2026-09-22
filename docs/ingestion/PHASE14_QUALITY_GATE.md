# Phase 14 real-data quality gate

Date: 2026-09-22

Result: **PASS**

## Controlled public set

The tracked manual-URL manifest contains three genuinely public English pages
from two publishers: two BIRN reports and one Human Rights Watch institutional
release. Each page was publicly readable, and the manifest preserves its
canonical/original URL, publisher, publication and capture timestamps, access
method, short exact excerpt, SHA-256, transcript origin and verification state.

Only short reviewed excerpts are retained; no site was crawled and no full
article was mirrored. One KSC page that returned an automated-access refusal
during verification was not included.

## Court boundary

All three items are `EXTERNAL_ONLY`. No exact citation in the held
KSC-BC-2020-06 corpus was established for these specific media items, so no
`MENTIONED`, `TENDERED`, `ADMITTED`, `REJECTED`, `DISCUSSED` or `RELIED_UPON`
relationship was invented. Consequently the external/court bridge network has
zero edges. The full taxonomy remains queryable and database-enforced for future
verified links.

## Statement comparison

Three exact statement fragments are hash-verified. One human-reviewed
comparison is `NOT COMPARABLE`: its two excerpts concern different speakers,
subjects and dates. It makes no truth or credibility finding.

## Machine result

`docs/ingestion/phase14-quality-gate.json` records:

- 2 real public sources;
- 3 real public items;
- 3 exact statements;
- 3 explicit external-only status rows;
- 0 citation-backed court links and 0 invalid court links;
- 1 neutral statement comparison;
- 0 duplicate URLs;
- 0 manifest/database item mismatches;
- 0 verification violations;
- 0 access violations;
- 0 external retrieval sources in the Phase 11 court-record AI audit;
- coverage limitations documented;
- overall PASS.

## Coverage limitations

This is a small controlled capability proof, not a comprehensive media archive.
It does not cover private, restricted, paywalled or deleted material and does
not attempt complete Facebook, TikTok or X coverage. The quality result says
nothing about the truth, importance, influence or evidential weight of any item.
