# Phase 22 — AI Relevance Gate Closeout

Date: 2026-09-27

Result: **PASS**

## Root cause

The Phase 11 retriever used OR across query tokens, assigned structured rows a
large base rank, and passed the first eight results directly to generation.
There was no question-to-passage eligibility step. A one-token lexical match
could therefore become an exact, source-backed quotation even when it did not
address the question.

## Deterministic fail-closed gate

The service now determines a research intent, removes generic intent language
from topical matching, and applies eligibility before persisting sources or
calling a provider. It enforces:

- minimum topical overlap, with a stricter threshold for lexical FTS results;
- exact filing, exhibit or public witness-code matching for entity-specific
  questions;
- Defence, SPO and witness category constraints for category-specific requests;
- at least two eligible passages for comparison requests;
- a verified structured `COURT_RELIES_ON` relationship for Court-reliance
  questions; ordinary Court citations cannot satisfy that request.

When the gate fails, no partial source set or answer is published. The run uses
the existing withheld/insufficient-evidence state with
`INSUFFICIENT_RELEVANCE` and the message that the retrieved public sources do
not provide sufficiently relevant evidence to answer reliably.

## Existing-run replay

The 64 stored completed-run questions were replayed through the gate without
creating replacement runs.

| Measure                                       | Before | After |
| --------------------------------------------- | -----: | ----: |
| Answered / relevance-eligible                 |     25 |    28 |
| Withheld / insufficient                       |     39 |    36 |
| Previously answered, now withheld             |      — |     0 |
| Previously answered, still directly supported |      — |    25 |
| Unsupported answered runs                     |      — |     0 |

The three additional eligible instances were historical validation/provider
failures for the same well-supported amendments question; the relevance gate
does not retroactively rewrite their stored audit state. All 25 previously
answered instances remain eligible because four directly relevant structured
sources survive while four low-relevance lexical sources are excluded.

## Manual real-corpus sample

- Panel/amendments summary: **answered** from F03752 ¶¶12–16, Defence summary
  ¶6, Court response ¶¶14–16 and SPO summary ¶7. Each source has a typed
  SourceAnchor and exact-version Reader path.
- Defence/amendments position: **answered** only from the Defence-attributed
  F03752 ¶6 source.
- Detention centres plus lunar-treaty remedies: **withheld** after 8 candidates
  produced 0 eligible sources.
- W02144 testimony about the amendments: **withheld** because no exact
  W02144-attributed testimony passage addressed that topic.
- Material relied upon by the Court for the amendments: **withheld** because
  Phase 22C correctly found only `COURT_CITES`, not `COURT_RELIES_ON`.

## Focused verification

- Ruff on changed Python files: PASS.
- Mypy on the AI retrieval and validation services: PASS.
- Focused AI relevance, validation and integration tests: 17 passed.
- Real 64-run replay: 28 eligible, 36 withheld, 0 unsupported answers.
- Five persisted deterministic manual samples: 2 answered, 3 correctly
  withheld, 0 validation errors on answered runs.

No broad backend, frontend, browser or accessibility suite was rerun, as the
operator explicitly limited this closeout to the sole AI relevance blocker.
No UI, corpus acquisition or witness-comparison functionality changed.
