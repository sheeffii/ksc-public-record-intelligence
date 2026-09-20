"""Controlled vocabularies shared by the Phase 6 evidence model.

Every enum here becomes a named PostgreSQL type (see migration 0002). Values are
lower-case strings so they read naturally in SQL and JSON. None of them encodes
guilt, credibility, suspicion or any assessment of a person.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SaEnum


def db_enum(enum_cls: type[enum.StrEnum], name: str) -> SaEnum:
    """SQLAlchemy Enum column type that stores the member *values* (lower-case
    strings) rather than the member names, matching the PostgreSQL types
    created by the migrations."""

    return SaEnum(
        enum_cls,
        name=name,
        values_callable=lambda cls: [member.value for member in cls],
        validate_strings=True,
    )


class Visibility(enum.StrEnum):
    """Access class of a record. Public-only product mode fails closed: only
    PUBLIC and PUBLIC_REDACTED are returned by default queries.

    NOT_PUBLIC records that an identifier appears in the public docket but the
    material itself is not public — the system states this instead of a 404
    (ROUTE_MAP.md §8). Nothing is ever fetched or reconstructed for it.
    """

    PUBLIC = "public"
    PUBLIC_REDACTED = "public_redacted"
    NOT_PUBLIC = "not_public"
    UNKNOWN = "unknown"
    PRIVATE_AUTHORIZED = "private_authorized"


PUBLIC_VISIBILITIES: frozenset[Visibility] = frozenset(
    {Visibility.PUBLIC, Visibility.PUBLIC_REDACTED}
)


class VerificationState(enum.StrEnum):
    UNREVIEWED = "unreviewed"
    AI_FLAGGED = "ai_flagged"
    HUMAN_VERIFIED = "human_verified"
    HUMAN_REJECTED = "human_rejected"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    UNRESOLVED = "unresolved"


class SourceSystem(enum.StrEnum):
    """Official KSC surfaces a record may be discovered on. Nothing is fetched
    in Phase 6; the vocabulary exists so discovery provenance is representable."""

    KSC_CASE_PAGE = "ksc_case_page"
    KSC_PUBLIC_COURT_RECORDS = "ksc_public_court_records"
    KSC_PUBLIC_HEARING = "ksc_public_hearing"
    OTHER_OFFICIAL_KSC = "other_official_ksc"


class DocumentVersionType(enum.StrEnum):
    ORIGINAL = "original"
    PUBLIC_REDACTED = "public_redacted"
    CORRECTED = "corrected"
    RECLASSIFIED = "reclassified"
    TRANSLATION = "translation"
    OTHER = "other"


class TextExtractionMethod(enum.StrEnum):
    NONE = "none"
    NATIVE_TEXT = "native_text"
    OCR = "ocr"
    MANUAL = "manual"


class ExaminationType(enum.StrEnum):
    DIRECT = "direct"
    CROSS = "cross"
    REDIRECT = "redirect"
    RECROSS = "recross"
    JUDGE_QUESTION = "judge_question"
    UNKNOWN = "unknown"


class WitnessIdentityStatus(enum.StrEnum):
    PUBLIC = "public"
    PROTECTED_CODE = "protected_code"
    UNKNOWN = "unknown"


class Party(enum.StrEnum):
    SPO = "spo"
    DEFENCE = "defence"
    VICTIMS_COUNSEL = "victims_counsel"
    COURT = "court"
    OTHER = "other"


class DatePrecision(enum.StrEnum):
    EXACT = "exact"
    MONTH_ONLY = "month_only"
    YEAR_ONLY = "year_only"
    RANGE = "range"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class DateType(enum.StrEnum):
    """Five date types. Never merged (DESIGN_DECISIONS.md §7)."""

    EVENT = "event"
    DOCUMENT = "document"
    FILING = "filing"
    TESTIMONY = "testimony"
    DECISION = "decision"


class ClaimOrigin(enum.StrEnum):
    SOURCE_EXTRACTED = "source_extracted"
    HUMAN = "human"
    AI_EXTRACTED = "ai_extracted"


class ClaimStance(enum.StrEnum):
    """Direction of a mention relative to the stated claim it is measured
    against — never relative to a person. Contradiction does not imply
    dishonesty."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    QUALIFIES = "qualifies"
    NEUTRAL = "neutral"
    UNCLEAR = "unclear"


class FindingLinkType(enum.StrEnum):
    RELIES_ON = "relies_on"
    SUPPORTS = "supports"
    QUALIFIES = "qualifies"
    CONTEXT = "context"


class ArgumentResponseKind(enum.StrEnum):
    RESPONDS_TO = "responds_to"
    DISPUTES = "disputes"
    CONCURS_WITH = "concurs_with"
    RULES_ON = "rules_on"


class CitationType(enum.StrEnum):
    DOCUMENT = "document"
    DOCUMENT_VERSION = "document_version"
    PAGE = "page"
    PARAGRAPH = "paragraph"
    TRANSCRIPT = "transcript"
    TRANSCRIPT_LINE = "transcript_line"
    EXHIBIT = "exhibit"
    WITNESS = "witness"
    FINDING = "finding"
    DECISION = "decision"
    URL = "url"
    UNKNOWN = "unknown"


class ResolutionState(enum.StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"


class ResolutionMethod(enum.StrEnum):
    EXACT_ID = "exact_id"
    PATTERN = "pattern"
    MANUAL = "manual"
    NONE = "none"


class IdentifierKind(enum.StrEnum):
    FILING = "filing"
    FILING_VERSION = "filing_version"
    EXHIBIT = "exhibit"
    WITNESS = "witness"
    TRANSCRIPT = "transcript"
    FINDING = "finding"
    OTHER = "other"


class EntityKind(enum.StrEnum):
    """Kinds of entity that can be a graph node or an identifier target."""

    PERSON = "person"
    WITNESS = "witness"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DOCUMENT = "document"
    DOCUMENT_VERSION = "document_version"
    EXHIBIT = "exhibit"
    INCIDENT = "incident"
    EVENT = "event"
    CLAIM = "claim"
    FINDING = "finding"
    ARGUMENT = "argument"
    HEARING = "hearing"
    TRANSCRIPT = "transcript"


class RelationshipType(enum.StrEnum):
    """Graph edge vocabulary. A connection never implies wrongdoing,
    responsibility, agreement, endorsement or guilt."""

    MENTIONED_IN = "mentioned_in"
    CO_MENTION = "co_mention"
    TESTIFIED_ABOUT = "testified_about"
    TESTIFIED_AT = "testified_at"
    CITED_IN = "cited_in"
    RELIES_ON = "relies_on"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    QUALIFIES = "qualifies"
    DISPUTES = "disputes"
    RESPONDS_TO = "responds_to"
    ASSOCIATED_WITH = "associated_with"
    LOCATED_AT = "located_at"
    OCCURRED_AT = "occurred_at"
    MEMBER_OF = "member_of"
    HELD_POSITION_IN = "held_position_in"
    AUTHORED = "authored"
    FILED_BY = "filed_by"
    CHALLENGED_BY = "challenged_by"
    CORROBORATED_BY = "corroborated_by"
    PART_OF_INCIDENT = "part_of_incident"
    PRECEDES = "precedes"
    FOLLOWS = "follows"


class AnswerBlockKind(enum.StrEnum):
    COURT = "court"
    EVIDENCE = "evidence"
    TESTIMONY = "testimony"
    SPO = "spo"
    DEFENCE = "defence"
    AI = "ai"


class AiRunStatus(enum.StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionJobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ArtifactStatus(enum.StrEnum):
    """Whether the bytes of a document version are held. A version may exist
    as metadata only — official detail URL + official artifact URL — without
    the PDF having been fetched (Phase 7): NOT_FETCHED. FETCHED requires a
    SHA-256 and a storage key (schema CHECK). FAILED records that a fetch was
    attempted and did not yield a stored artifact; the reason lives on the
    ingestion job item."""

    NOT_FETCHED = "not_fetched"
    FETCHED = "fetched"
    FAILED = "failed"


class IngestionItemStatus(enum.StrEnum):
    """Outcome of one record within an ingestion job. Failures are persisted
    here, never dropped (roadmap Phase 7 — failure handling)."""

    PENDING = "pending"
    DOWNLOADED = "downloaded"
    METADATA_ONLY = "metadata_only"
    SKIPPED_DUPLICATE = "skipped_duplicate"
    NOT_PUBLIC = "not_public"
    FAILED_DOWNLOAD = "failed_download"
    BLOCKED_BY_ACCESS_CONTROL = "blocked_by_access_control"
    INVALID_METADATA = "invalid_metadata"
    UNSUPPORTED_ARTIFACT = "unsupported_artifact"
    AMBIGUOUS_MAPPING = "ambiguous_mapping"


INGESTION_FAILURE_STATUSES: frozenset[IngestionItemStatus] = frozenset(
    {
        IngestionItemStatus.FAILED_DOWNLOAD,
        IngestionItemStatus.BLOCKED_BY_ACCESS_CONTROL,
        IngestionItemStatus.INVALID_METADATA,
        IngestionItemStatus.UNSUPPORTED_ARTIFACT,
        IngestionItemStatus.AMBIGUOUS_MAPPING,
    }
)
