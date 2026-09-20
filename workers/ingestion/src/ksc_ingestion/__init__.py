"""Ingestion worker — controlled, public-only ingestion of official KSC records.

Phase 7 scope: discovery provenance, capture-bundle ingestion, hashing,
object storage, Document / DocumentVersion / SourceRecord persistence, job
state. No parsing beyond validation; no citation resolution (Phase 8).

Rules that bind every module here (docs/SECURITY.md, docs/roadmap/PHASE_07_*):
- official KSC hosts only (`ksc_ingestion.sources.OFFICIAL_HOSTS`);
- never bypass an access control — a challenge is a visible failure;
- never guess URLs, never reconstruct redactions, never store text about a
  protected witness beyond the public code;
- controlled before bulk (ADR-003).
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
