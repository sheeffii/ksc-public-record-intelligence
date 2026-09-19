"""Read repositories. Every query is scoped to one case and filtered to the
public record (docs/SECURITY.md: fail closed)."""

from ksc_api.repositories.records import RecordRepository, get_repository

__all__ = ["RecordRepository", "get_repository"]
