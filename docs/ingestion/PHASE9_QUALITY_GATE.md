# Phase 9 controlled-corpus quality gate

Date: 2026-09-20  
Result: **PASS**

Phase 9 projects only the already-held 22-record Phase 7 corpus parsed and
resolved in Phase 8. `ksc-ingest build-evidence` performs no network request.
It creates one `CITED_IN` relationship for each resolved citation whose source
and target are different public documents, and typed timeline events only from
persisted document or hearing dates.

## Result

- input manifest SHA-256:
  `df27eca54a5f1d127064b22b7669702475bc32d558deb162ea11a5a1c9087b99`;
- 23 resolved citations inspected; one true self-citation omitted;
- 13 document nodes and 22 independently cited edges;
- zero missing citations, self-edges, inferred edges, or analytical edges;
- 19 source-backed timeline items: 11 document, 6 decision, 2 testimony;
- all 19 events have an official `source_record`; all controlled dates are
  explicitly exact (no precision was inferred);
- graph scale is 13 nodes / 22 edges, so the existing accessible SVG renderer
  remains appropriate; a WebGL migration would add complexity without a
  measured performance need.

The machine-readable result is
`docs/ingestion/manifests/phase9-controlled-corpus-quality.json`.

## Safety interpretation

An edge says only that the citing public record contains the exact citation
stored on that edge. It does not state agreement, responsibility, wrongdoing,
importance, or guilt. Evidence paths use only public, resolved, non-rejected,
non-analytical edges; hop count is the only ordering criterion. Unresolved and
ambiguous Phase 8 citations create no edge and remain unchanged.
