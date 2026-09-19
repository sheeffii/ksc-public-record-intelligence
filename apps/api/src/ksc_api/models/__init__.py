"""Phase 6 evidence model.

Import order matters only for readability; SQLAlchemy resolves string
relationship targets once every module is imported. Everything is registered
on `Base.metadata` by importing this package (Alembic relies on that).
"""

from ksc_api.models.actor import Location, Organization, Person, PersonAlias, Witness
from ksc_api.models.ai import AiOutput, AiOutputCitation, AiRun, PromptVersion
from ksc_api.models.audit_log import AuditLog
from ksc_api.models.case import Case
from ksc_api.models.citation import (
    UNRESOLVED_DISPLAY,
    Citation,
    RecordIdentifier,
    normalize_identifier,
)
from ksc_api.models.document import (
    Document,
    DocumentChunk,
    DocumentIngestionState,
    DocumentPage,
    DocumentSection,
    DocumentVersion,
)
from ksc_api.models.enums import (
    PUBLIC_VISIBILITIES,
    AiRunStatus,
    AnswerBlockKind,
    ArgumentResponseKind,
    CitationType,
    ClaimOrigin,
    ClaimStance,
    DatePrecision,
    DateType,
    DocumentVersionType,
    EntityKind,
    ExaminationType,
    FindingLinkType,
    IdentifierKind,
    IngestionJobStatus,
    Party,
    RelationshipType,
    ResolutionMethod,
    ResolutionState,
    SourceSystem,
    TextExtractionMethod,
    VerificationState,
    Visibility,
    WitnessIdentityStatus,
)
from ksc_api.models.evidence import (
    Argument,
    ArgumentResponse,
    Claim,
    ClaimMention,
    Event,
    Exhibit,
    Finding,
    FindingEvidenceLink,
    Incident,
)
from ksc_api.models.graph import NODE_FK_COLUMNS, GraphNode, Relationship
from ksc_api.models.hearing import Hearing, Transcript, TranscriptSegment, WitnessAppearance
from ksc_api.models.ingestion import IngestionJob
from ksc_api.models.research import ResearchNote, ResearchNoteCitation
from ksc_api.models.source_record import SourceRecord

__all__ = [
    "NODE_FK_COLUMNS",
    "PUBLIC_VISIBILITIES",
    "UNRESOLVED_DISPLAY",
    "AiOutput",
    "AiOutputCitation",
    "AiRun",
    "AiRunStatus",
    "AnswerBlockKind",
    "Argument",
    "ArgumentResponse",
    "ArgumentResponseKind",
    "AuditLog",
    "Case",
    "Citation",
    "CitationType",
    "Claim",
    "ClaimMention",
    "ClaimOrigin",
    "ClaimStance",
    "DatePrecision",
    "DateType",
    "Document",
    "DocumentChunk",
    "DocumentIngestionState",
    "DocumentPage",
    "DocumentSection",
    "DocumentVersion",
    "DocumentVersionType",
    "EntityKind",
    "Event",
    "ExaminationType",
    "Exhibit",
    "Finding",
    "FindingEvidenceLink",
    "FindingLinkType",
    "GraphNode",
    "Hearing",
    "IdentifierKind",
    "Incident",
    "IngestionJob",
    "IngestionJobStatus",
    "Location",
    "Organization",
    "Party",
    "Person",
    "PersonAlias",
    "PromptVersion",
    "RecordIdentifier",
    "Relationship",
    "RelationshipType",
    "ResearchNote",
    "ResearchNoteCitation",
    "ResolutionMethod",
    "ResolutionState",
    "SourceRecord",
    "SourceSystem",
    "TextExtractionMethod",
    "Transcript",
    "TranscriptSegment",
    "VerificationState",
    "Visibility",
    "Witness",
    "WitnessAppearance",
    "WitnessIdentityStatus",
    "normalize_identifier",
]
