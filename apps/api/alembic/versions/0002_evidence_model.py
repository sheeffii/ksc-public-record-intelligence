"""evidence model: normalized Phase 6 schema

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-20

Adds the normalized evidence model (source records, document versions / pages /
sections / chunks, hearings / transcripts / segments, persons / witnesses /
organizations / locations, exhibits, incidents / events, claims / mentions,
findings / evidence links, arguments / responses, citations + record
identifiers, graph nodes / relationships, research notes, AI audit tables,
ingestion jobs) on top of the Phase 4 foundation.

`documents` is migrated in place: `public_state` becomes `visibility`
(public → public, public_redacted → public_redacted, not_held → not_public),
`filing_party` and `public_date` are added, and the artifact columns
(`storage_key`, `sha256`, `page_count`) move to `document_versions`.
Existing `cases` and `audit_log` rows are untouched.

Every PostgreSQL enum type is created explicitly (checkfirst) at the top of
`upgrade()` and dropped at the end of `downgrade()`.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# --- enum types ------------------------------------------------------------
AI_RUN_STATUS = postgresql.ENUM(
    "pending", "completed", "failed", name="ai_run_status", create_type=False
)
ANSWER_BLOCK_KIND = postgresql.ENUM(
    "court",
    "evidence",
    "testimony",
    "spo",
    "defence",
    "ai",
    name="answer_block_kind",
    create_type=False,
)
ARGUMENT_RESPONSE_KIND = postgresql.ENUM(
    "responds_to",
    "disputes",
    "concurs_with",
    "rules_on",
    name="argument_response_kind",
    create_type=False,
)
CITATION_TYPE = postgresql.ENUM(
    "document",
    "document_version",
    "page",
    "paragraph",
    "transcript",
    "transcript_line",
    "exhibit",
    "witness",
    "finding",
    "decision",
    "url",
    "unknown",
    name="citation_type",
    create_type=False,
)
CLAIM_ORIGIN = postgresql.ENUM(
    "source_extracted", "human", "ai_extracted", name="claim_origin", create_type=False
)
CLAIM_STANCE = postgresql.ENUM(
    "supports",
    "contradicts",
    "qualifies",
    "neutral",
    "unclear",
    name="claim_stance",
    create_type=False,
)
DATE_PRECISION = postgresql.ENUM(
    "exact",
    "month_only",
    "year_only",
    "range",
    "approximate",
    "unknown",
    name="date_precision",
    create_type=False,
)
DATE_TYPE = postgresql.ENUM(
    "event", "document", "filing", "testimony", "decision", name="date_type", create_type=False
)
DOCUMENT_VERSION_TYPE = postgresql.ENUM(
    "original",
    "public_redacted",
    "corrected",
    "reclassified",
    "translation",
    "other",
    name="document_version_type",
    create_type=False,
)
ENTITY_KIND = postgresql.ENUM(
    "person",
    "witness",
    "organization",
    "location",
    "document",
    "document_version",
    "exhibit",
    "incident",
    "event",
    "claim",
    "finding",
    "argument",
    "hearing",
    "transcript",
    name="entity_kind",
    create_type=False,
)
EXAMINATION_TYPE = postgresql.ENUM(
    "direct",
    "cross",
    "redirect",
    "recross",
    "judge_question",
    "unknown",
    name="examination_type",
    create_type=False,
)
FINDING_LINK_TYPE = postgresql.ENUM(
    "relies_on", "supports", "qualifies", "context", name="finding_link_type", create_type=False
)
IDENTIFIER_KIND = postgresql.ENUM(
    "filing",
    "filing_version",
    "exhibit",
    "witness",
    "transcript",
    "finding",
    "other",
    name="identifier_kind",
    create_type=False,
)
INGESTION_JOB_STATUS = postgresql.ENUM(
    "pending",
    "running",
    "completed",
    "failed",
    "cancelled",
    name="ingestion_job_status",
    create_type=False,
)
PARTY = postgresql.ENUM(
    "spo", "defence", "victims_counsel", "court", "other", name="party", create_type=False
)
RELATIONSHIP_TYPE = postgresql.ENUM(
    "mentioned_in",
    "co_mention",
    "testified_about",
    "testified_at",
    "cited_in",
    "relies_on",
    "supports",
    "contradicts",
    "qualifies",
    "disputes",
    "responds_to",
    "associated_with",
    "located_at",
    "occurred_at",
    "member_of",
    "held_position_in",
    "authored",
    "filed_by",
    "challenged_by",
    "corroborated_by",
    "part_of_incident",
    "precedes",
    "follows",
    name="relationship_type",
    create_type=False,
)
RESOLUTION_METHOD = postgresql.ENUM(
    "exact_id", "pattern", "manual", "none", name="resolution_method", create_type=False
)
RESOLUTION_STATE = postgresql.ENUM(
    "resolved", "unresolved", "ambiguous", "invalid", name="resolution_state", create_type=False
)
SOURCE_SYSTEM = postgresql.ENUM(
    "ksc_case_page",
    "ksc_public_court_records",
    "ksc_public_hearing",
    "other_official_ksc",
    name="source_system",
    create_type=False,
)
TEXT_EXTRACTION_METHOD = postgresql.ENUM(
    "none", "native_text", "ocr", "manual", name="text_extraction_method", create_type=False
)
VERIFICATION_STATE = postgresql.ENUM(
    "unreviewed",
    "ai_flagged",
    "human_verified",
    "human_rejected",
    "needs_more_evidence",
    "unresolved",
    name="verification_state",
    create_type=False,
)
VISIBILITY = postgresql.ENUM(
    "public",
    "public_redacted",
    "not_public",
    "unknown",
    "private_authorized",
    name="visibility",
    create_type=False,
)
WITNESS_IDENTITY_STATUS = postgresql.ENUM(
    "public", "protected_code", "unknown", name="witness_identity_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    AI_RUN_STATUS.create(bind, checkfirst=True)
    ANSWER_BLOCK_KIND.create(bind, checkfirst=True)
    ARGUMENT_RESPONSE_KIND.create(bind, checkfirst=True)
    CITATION_TYPE.create(bind, checkfirst=True)
    CLAIM_ORIGIN.create(bind, checkfirst=True)
    CLAIM_STANCE.create(bind, checkfirst=True)
    DATE_PRECISION.create(bind, checkfirst=True)
    DATE_TYPE.create(bind, checkfirst=True)
    DOCUMENT_VERSION_TYPE.create(bind, checkfirst=True)
    ENTITY_KIND.create(bind, checkfirst=True)
    EXAMINATION_TYPE.create(bind, checkfirst=True)
    FINDING_LINK_TYPE.create(bind, checkfirst=True)
    IDENTIFIER_KIND.create(bind, checkfirst=True)
    INGESTION_JOB_STATUS.create(bind, checkfirst=True)
    PARTY.create(bind, checkfirst=True)
    RELATIONSHIP_TYPE.create(bind, checkfirst=True)
    RESOLUTION_METHOD.create(bind, checkfirst=True)
    RESOLUTION_STATE.create(bind, checkfirst=True)
    SOURCE_SYSTEM.create(bind, checkfirst=True)
    TEXT_EXTRACTION_METHOD.create(bind, checkfirst=True)
    VERIFICATION_STATE.create(bind, checkfirst=True)
    VISIBILITY.create(bind, checkfirst=True)
    WITNESS_IDENTITY_STATUS.create(bind, checkfirst=True)

    op.create_table(
        "prompt_versions",
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("template_sha256", sa.String(length=64), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompt_versions")),
        sa.UniqueConstraint("name", "version", name="uq_prompt_versions_name_version"),
    )
    op.create_table(
        "ai_runs",
        sa.Column("case_id", sa.UUID(), nullable=True),
        sa.Column("prompt_version_id", sa.UUID(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("temperature", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending", "completed", "failed", name="ai_run_status", create_type=False
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("requested_by", sa.String(length=128), nullable=True),
        sa.Column("input_sha256", sa.String(length=64), nullable=True),
        sa.Column("retrieved_citation_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "input_tokens IS NULL OR input_tokens >= 0",
            name=op.f("ck_ai_runs_input_tokens_non_negative"),
        ),
        sa.CheckConstraint(
            "output_tokens IS NULL OR output_tokens >= 0",
            name=op.f("ck_ai_runs_output_tokens_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_ai_runs_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["prompt_version_id"],
            ["prompt_versions.id"],
            name=op.f("fk_ai_runs_prompt_version_id_prompt_versions"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_runs")),
    )
    op.create_index(op.f("ix_ai_runs_case_id"), "ai_runs", ["case_id"], unique=False)
    op.create_table(
        "hearings",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("hearing_date", sa.Date(), nullable=False),
        sa.Column("session_sequence", sa.Integer(), nullable=False),
        sa.Column("session_label", sa.String(length=64), nullable=True),
        sa.Column("hearing_type", sa.String(length=64), nullable=True),
        sa.Column("official_ref", sa.String(length=128), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "visibility",
            postgresql.ENUM(
                "public",
                "public_redacted",
                "not_public",
                "unknown",
                "private_authorized",
                name="visibility",
                create_type=False,
            ),
            server_default="public",
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "session_sequence >= 1", name=op.f("ck_hearings_session_sequence_positive")
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_hearings_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hearings")),
        sa.UniqueConstraint(
            "case_id", "hearing_date", "session_sequence", name="uq_hearings_case_date_session"
        ),
    )
    op.create_index(op.f("ix_hearings_case_id"), "hearings", ["case_id"], unique=False)
    op.create_table(
        "ingestion_jobs",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column(
            "source_system",
            postgresql.ENUM(
                "ksc_case_page",
                "ksc_public_court_records",
                "ksc_public_hearing",
                "other_official_ksc",
                name="source_system",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "running",
                "completed",
                "failed",
                "cancelled",
                name="ingestion_job_status",
                create_type=False,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("cursor", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("checkpoint", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("discovered_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("downloaded_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "discovered_count >= 0 AND downloaded_count >= 0 AND processed_count >= 0 AND failed_count >= 0",
            name=op.f("ck_ingestion_jobs_counts_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_ingestion_jobs_case_id_cases"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_jobs")),
    )
    op.create_index(op.f("ix_ingestion_jobs_case_id"), "ingestion_jobs", ["case_id"], unique=False)
    op.create_table(
        "locations",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "name_variants",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_locations_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_locations")),
        sa.UniqueConstraint("case_id", "slug", name="uq_locations_case_slug"),
    )
    op.create_index(op.f("ix_locations_case_id"), "locations", ["case_id"], unique=False)
    op.create_table(
        "organizations",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=True),
        sa.Column(
            "name_variants",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_organizations_case_id_cases"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("case_id", "slug", name="uq_organizations_case_slug"),
    )
    op.create_index(op.f("ix_organizations_case_id"), "organizations", ["case_id"], unique=False)
    op.create_table(
        "persons",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("public_role", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_persons_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_persons")),
        sa.UniqueConstraint("case_id", "slug", name="uq_persons_case_slug"),
    )
    op.create_index(op.f("ix_persons_case_id"), "persons", ["case_id"], unique=False)
    op.create_table(
        "research_notes",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("author", sa.String(length=128), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("provenance", sa.String(length=16), server_default="human", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "provenance = 'human'", name=op.f("ck_research_notes_provenance_is_human")
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_research_notes_case_id_cases"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_notes")),
    )
    op.create_index(op.f("ix_research_notes_case_id"), "research_notes", ["case_id"], unique=False)
    op.create_table(
        "ai_outputs",
        sa.Column("ai_run_id", sa.UUID(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "kind",
            postgresql.ENUM(
                "court",
                "evidence",
                "testimony",
                "spo",
                "defence",
                "ai",
                name="answer_block_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("unresolved_citation_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "verification_state",
            postgresql.ENUM(
                "unreviewed",
                "ai_flagged",
                "human_verified",
                "human_rejected",
                "needs_more_evidence",
                "unresolved",
                name="verification_state",
                create_type=False,
            ),
            server_default="unreviewed",
            nullable=False,
        ),
        sa.Column("verified_by", sa.String(length=128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name=op.f("ck_ai_outputs_human_verification_has_reviewer"),
        ),
        sa.CheckConstraint(
            "unresolved_citation_count >= 0",
            name=op.f("ck_ai_outputs_unresolved_count_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["ai_run_id"],
            ["ai_runs.id"],
            name=op.f("fk_ai_outputs_ai_run_id_ai_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_outputs")),
        sa.UniqueConstraint("ai_run_id", "sequence", name="uq_ai_outputs_run_sequence"),
    )
    op.create_index(op.f("ix_ai_outputs_ai_run_id"), "ai_outputs", ["ai_run_id"], unique=False)
    op.create_table(
        "document_versions",
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("official_version_ref", sa.String(length=128), nullable=False),
        sa.Column(
            "version_type",
            postgresql.ENUM(
                "original",
                "public_redacted",
                "corrected",
                "reclassified",
                "translation",
                "other",
                name="document_version_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("version_label", sa.String(length=64), nullable=True),
        sa.Column(
            "visibility",
            postgresql.ENUM(
                "public",
                "public_redacted",
                "not_public",
                "unknown",
                "private_authorized",
                name="visibility",
                create_type=False,
            ),
            server_default="public",
            nullable=False,
        ),
        sa.Column("public_date", sa.Date(), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column(
            "text_extraction_method",
            postgresql.ENUM(
                "none",
                "native_text",
                "ocr",
                "manual",
                name="text_extraction_method",
                create_type=False,
            ),
            server_default="none",
            nullable=False,
        ),
        sa.Column("supersedes_version_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "page_count IS NULL OR page_count >= 0",
            name=op.f("ck_document_versions_page_count_non_negative"),
        ),
        sa.CheckConstraint(
            "supersedes_version_id IS NULL OR supersedes_version_id <> id",
            name=op.f("ck_document_versions_no_self_supersede"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_document_versions_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_version_id"],
            ["document_versions.id"],
            name=op.f("fk_document_versions_supersedes_version_id_document_versions"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_versions")),
        sa.UniqueConstraint(
            "document_id", "official_version_ref", name="uq_document_versions_document_ref"
        ),
    )
    op.create_index(
        op.f("ix_document_versions_document_id"), "document_versions", ["document_id"], unique=False
    )
    op.create_index(
        "uq_document_versions_sha256",
        "document_versions",
        ["sha256"],
        unique=True,
        postgresql_where="sha256 IS NOT NULL",
    )
    op.create_table(
        "incidents",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("location_id", sa.UUID(), nullable=True),
        sa.Column("date_from", sa.Date(), nullable=True),
        sa.Column("date_to", sa.Date(), nullable=True),
        sa.Column(
            "date_precision",
            postgresql.ENUM(
                "exact",
                "month_only",
                "year_only",
                "range",
                "approximate",
                "unknown",
                name="date_precision",
                create_type=False,
            ),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("charges_pleaded", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "date_to IS NULL OR date_from IS NULL OR date_to >= date_from",
            name=op.f("ck_incidents_date_range"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_incidents_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            name=op.f("fk_incidents_location_id_locations"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incidents")),
        sa.UniqueConstraint("case_id", "slug", name="uq_incidents_case_slug"),
    )
    op.create_index(op.f("ix_incidents_case_id"), "incidents", ["case_id"], unique=False)
    op.create_table(
        "person_aliases",
        sa.Column("person_id", sa.UUID(), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_person_aliases_person_id_persons"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_person_aliases")),
        sa.UniqueConstraint("person_id", "alias", name="uq_person_aliases_person_alias"),
    )
    op.create_index(
        op.f("ix_person_aliases_person_id"), "person_aliases", ["person_id"], unique=False
    )
    op.create_table(
        "witnesses",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column(
            "identity_status",
            postgresql.ENUM(
                "public",
                "protected_code",
                "unknown",
                name="witness_identity_status",
                create_type=False,
            ),
            server_default="protected_code",
            nullable=False,
        ),
        sa.Column("person_id", sa.UUID(), nullable=True),
        sa.Column("public_name", sa.String(length=255), nullable=True),
        sa.Column(
            "called_by",
            postgresql.ENUM(
                "spo",
                "defence",
                "victims_counsel",
                "court",
                "other",
                name="party",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "protective_measures",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "identity_status <> 'protected_code' OR (person_id IS NULL AND public_name IS NULL)",
            name=op.f("ck_witnesses_protected_code_has_no_identity"),
        ),
        sa.CheckConstraint(
            "identity_status = 'public' OR public_name IS NULL",
            name=op.f("ck_witnesses_public_name_requires_public"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_witnesses_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_witnesses_person_id_persons"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_witnesses")),
        sa.UniqueConstraint("case_id", "code", name="uq_witnesses_case_code"),
    )
    op.create_index(op.f("ix_witnesses_case_id"), "witnesses", ["case_id"], unique=False)
    op.create_index(op.f("ix_witnesses_person_id"), "witnesses", ["person_id"], unique=False)
    op.create_table(
        "document_pages",
        sa.Column("document_version_id", sa.UUID(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("running_head", sa.String(length=512), nullable=True),
        sa.Column("has_redactions", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("redaction_extents", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint("page_number >= 1", name=op.f("ck_document_pages_page_number_positive")),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_document_pages_document_version_id_document_versions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_pages")),
        sa.UniqueConstraint(
            "document_version_id", "page_number", name="uq_document_pages_version_page"
        ),
    )
    op.create_table(
        "document_sections",
        sa.Column("document_version_id", sa.UUID(), nullable=False),
        sa.Column("parent_section_id", sa.UUID(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("heading", sa.Text(), nullable=False),
        sa.Column("page_from", sa.Integer(), nullable=True),
        sa.Column("page_to", sa.Integer(), nullable=True),
        sa.Column("para_from", sa.Integer(), nullable=True),
        sa.Column("para_to", sa.Integer(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint("level >= 0", name=op.f("ck_document_sections_level_non_negative")),
        sa.CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from",
            name=op.f("ck_document_sections_page_range"),
        ),
        sa.CheckConstraint(
            "para_to IS NULL OR para_from IS NULL OR para_to >= para_from",
            name=op.f("ck_document_sections_para_range"),
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_document_sections_document_version_id_document_versions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_section_id"],
            ["document_sections.id"],
            name=op.f("fk_document_sections_parent_section_id_document_sections"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_sections")),
        sa.UniqueConstraint(
            "document_version_id", "sequence", name="uq_document_sections_version_sequence"
        ),
    )
    op.create_table(
        "exhibits",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("official_exhibit_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "tendered_by",
            postgresql.ENUM(
                "spo",
                "defence",
                "victims_counsel",
                "court",
                "other",
                name="party",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("through_witness_id", sa.UUID(), nullable=True),
        sa.Column("admitted_date", sa.Date(), nullable=True),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("document_version_id", sa.UUID(), nullable=True),
        sa.Column(
            "visibility",
            postgresql.ENUM(
                "public",
                "public_redacted",
                "not_public",
                "unknown",
                "private_authorized",
                name="visibility",
                create_type=False,
            ),
            server_default="public",
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_exhibits_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_exhibits_document_version_id_document_versions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["through_witness_id"],
            ["witnesses.id"],
            name=op.f("fk_exhibits_through_witness_id_witnesses"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exhibits")),
        sa.UniqueConstraint("case_id", "official_exhibit_id", name="uq_exhibits_case_official_id"),
    )
    op.create_index(op.f("ix_exhibits_case_id"), "exhibits", ["case_id"], unique=False)
    op.create_table(
        "findings",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("finding_key", sa.String(length=64), nullable=False),
        sa.Column("judgment_document_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("para_from", sa.Integer(), nullable=False),
        sa.Column("para_to", sa.Integer(), nullable=True),
        sa.Column("person_id", sa.UUID(), nullable=True),
        sa.Column("incident_id", sa.UUID(), nullable=True),
        sa.Column("charge_ref", sa.String(length=128), nullable=True),
        sa.Column("legal_element", sa.String(length=255), nullable=True),
        sa.Column("mode_of_liability", sa.String(length=128), nullable=True),
        sa.Column("citation_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "verification_state",
            postgresql.ENUM(
                "unreviewed",
                "ai_flagged",
                "human_verified",
                "human_rejected",
                "needs_more_evidence",
                "unresolved",
                name="verification_state",
                create_type=False,
            ),
            server_default="unreviewed",
            nullable=False,
        ),
        sa.Column("verified_by", sa.String(length=128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name=op.f("ck_findings_human_verification_has_reviewer"),
        ),
        sa.CheckConstraint("para_from >= 1", name=op.f("ck_findings_para_from_positive")),
        sa.CheckConstraint(
            "para_to IS NULL OR para_to >= para_from", name=op.f("ck_findings_para_range")
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_findings_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name=op.f("fk_findings_incident_id_incidents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["judgment_document_id"],
            ["documents.id"],
            name=op.f("fk_findings_judgment_document_id_documents"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_findings_person_id_persons"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_findings")),
        sa.UniqueConstraint("case_id", "finding_key", name="uq_findings_case_key"),
    )
    op.create_index(op.f("ix_findings_case_id"), "findings", ["case_id"], unique=False)
    op.create_index(op.f("ix_findings_incident_id"), "findings", ["incident_id"], unique=False)
    op.create_index(
        op.f("ix_findings_judgment_document_id"), "findings", ["judgment_document_id"], unique=False
    )
    op.create_index(op.f("ix_findings_person_id"), "findings", ["person_id"], unique=False)
    op.create_table(
        "transcripts",
        sa.Column("hearing_id", sa.UUID(), nullable=False),
        sa.Column("document_version_id", sa.UUID(), nullable=True),
        sa.Column("official_ref", sa.String(length=128), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column(
            "visibility",
            postgresql.ENUM(
                "public",
                "public_redacted",
                "not_public",
                "unknown",
                "private_authorized",
                name="visibility",
                create_type=False,
            ),
            server_default="public",
            nullable=False,
        ),
        sa.Column("page_from", sa.Integer(), nullable=True),
        sa.Column("page_to", sa.Integer(), nullable=True),
        sa.Column(
            "text_extraction_method",
            postgresql.ENUM(
                "none",
                "native_text",
                "ocr",
                "manual",
                name="text_extraction_method",
                create_type=False,
            ),
            server_default="none",
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from",
            name=op.f("ck_transcripts_page_range"),
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_transcripts_document_version_id_document_versions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["hearing_id"],
            ["hearings.id"],
            name=op.f("fk_transcripts_hearing_id_hearings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transcripts")),
    )
    op.create_index(op.f("ix_transcripts_hearing_id"), "transcripts", ["hearing_id"], unique=False)
    op.create_index(
        op.f("ix_transcripts_official_ref"), "transcripts", ["official_ref"], unique=False
    )
    op.create_index(
        "uq_transcripts_document_version",
        "transcripts",
        ["document_version_id"],
        unique=True,
        postgresql_where="document_version_id IS NOT NULL",
    )
    op.create_table(
        "document_chunks",
        sa.Column("document_version_id", sa.UUID(), nullable=False),
        sa.Column("section_id", sa.UUID(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("page_from", sa.Integer(), nullable=True),
        sa.Column("page_to", sa.Integer(), nullable=True),
        sa.Column("para_from", sa.Integer(), nullable=True),
        sa.Column("para_to", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from",
            name=op.f("ck_document_chunks_page_range"),
        ),
        sa.CheckConstraint(
            "para_to IS NULL OR para_from IS NULL OR para_to >= para_from",
            name=op.f("ck_document_chunks_para_range"),
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_document_chunks_document_version_id_document_versions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["document_sections.id"],
            name=op.f("fk_document_chunks_section_id_document_sections"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
        sa.UniqueConstraint(
            "document_version_id", "sequence", name="uq_document_chunks_version_sequence"
        ),
    )
    op.create_table(
        "record_identifiers",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("identifier", sa.String(length=128), nullable=False),
        sa.Column("normalized_identifier", sa.String(length=128), nullable=False),
        sa.Column(
            "identifier_kind",
            postgresql.ENUM(
                "filing",
                "filing_version",
                "exhibit",
                "witness",
                "transcript",
                "finding",
                "other",
                name="identifier_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "entity_kind",
            postgresql.ENUM(
                "person",
                "witness",
                "organization",
                "location",
                "document",
                "document_version",
                "exhibit",
                "incident",
                "event",
                "claim",
                "finding",
                "argument",
                "hearing",
                "transcript",
                name="entity_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=True),
        sa.Column("document_version_id", sa.UUID(), nullable=True),
        sa.Column("exhibit_id", sa.UUID(), nullable=True),
        sa.Column("witness_id", sa.UUID(), nullable=True),
        sa.Column("transcript_id", sa.UUID(), nullable=True),
        sa.Column("finding_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "num_nonnulls(document_id, document_version_id, exhibit_id, witness_id, transcript_id, finding_id) = 1",
            name=op.f("ck_record_identifiers_exactly_one_target"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_record_identifiers_case_id_cases"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_record_identifiers_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_record_identifiers_document_version_id_document_versions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["exhibit_id"],
            ["exhibits.id"],
            name=op.f("fk_record_identifiers_exhibit_id_exhibits"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            name=op.f("fk_record_identifiers_finding_id_findings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["transcript_id"],
            ["transcripts.id"],
            name=op.f("fk_record_identifiers_transcript_id_transcripts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["witness_id"],
            ["witnesses.id"],
            name=op.f("fk_record_identifiers_witness_id_witnesses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_record_identifiers")),
        sa.UniqueConstraint(
            "case_id", "normalized_identifier", "entity_kind", name="uq_record_identifiers_lookup"
        ),
    )
    op.create_index(
        op.f("ix_record_identifiers_case_id"), "record_identifiers", ["case_id"], unique=False
    )
    op.create_index(
        op.f("ix_record_identifiers_normalized_identifier"),
        "record_identifiers",
        ["normalized_identifier"],
        unique=False,
    )
    op.create_table(
        "source_records",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column(
            "source_system",
            postgresql.ENUM(
                "ksc_case_page",
                "ksc_public_court_records",
                "ksc_public_hearing",
                "other_official_ksc",
                name="source_system",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("external_record_id", sa.String(length=256), nullable=False),
        sa.Column("record_type", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("discovery_url", sa.String(length=1024), nullable=False),
        sa.Column("canonical_source_url", sa.String(length=1024), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column(
            "visibility",
            postgresql.ENUM(
                "public",
                "public_redacted",
                "not_public",
                "unknown",
                "private_authorized",
                name="visibility",
                create_type=False,
            ),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("raw_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=True),
        sa.Column("document_version_id", sa.UUID(), nullable=True),
        sa.Column("hearing_id", sa.UUID(), nullable=True),
        sa.Column("transcript_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_source_records_case_id_cases"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_source_records_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_source_records_document_version_id_document_versions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["hearing_id"],
            ["hearings.id"],
            name=op.f("fk_source_records_hearing_id_hearings"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["transcript_id"],
            ["transcripts.id"],
            name=op.f("fk_source_records_transcript_id_transcripts"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_records")),
        sa.UniqueConstraint(
            "case_id", "source_system", "external_record_id", name="uq_source_records_external"
        ),
    )
    op.create_index(op.f("ix_source_records_case_id"), "source_records", ["case_id"], unique=False)
    op.create_index(
        op.f("ix_source_records_document_id"), "source_records", ["document_id"], unique=False
    )
    op.create_table(
        "transcript_segments",
        sa.Column("transcript_id", sa.UUID(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("line_from", sa.Integer(), nullable=True),
        sa.Column("line_to", sa.Integer(), nullable=True),
        sa.Column("speaker", sa.String(length=255), nullable=True),
        sa.Column("speaker_role", sa.String(length=64), nullable=True),
        sa.Column("witness_id", sa.UUID(), nullable=True),
        sa.Column(
            "examination_type",
            postgresql.ENUM(
                "direct",
                "cross",
                "redirect",
                "recross",
                "judge_question",
                "unknown",
                name="examination_type",
                create_type=False,
            ),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("closed_session", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "NOT closed_session OR text = ''",
            name=op.f("ck_transcript_segments_closed_session_has_no_text"),
        ),
        sa.CheckConstraint(
            "line_from IS NULL OR line_from >= 1",
            name=op.f("ck_transcript_segments_line_from_positive"),
        ),
        sa.CheckConstraint(
            "line_to IS NULL OR line_from IS NOT NULL",
            name=op.f("ck_transcript_segments_line_to_needs_line_from"),
        ),
        sa.CheckConstraint(
            "line_to IS NULL OR line_from IS NULL OR line_to >= line_from",
            name=op.f("ck_transcript_segments_line_range"),
        ),
        sa.CheckConstraint(
            "page_number IS NULL OR page_number >= 1",
            name=op.f("ck_transcript_segments_page_number_positive"),
        ),
        sa.CheckConstraint(
            "sequence >= 0", name=op.f("ck_transcript_segments_sequence_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["transcript_id"],
            ["transcripts.id"],
            name=op.f("fk_transcript_segments_transcript_id_transcripts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["witness_id"],
            ["witnesses.id"],
            name=op.f("fk_transcript_segments_witness_id_witnesses"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transcript_segments")),
        sa.UniqueConstraint("transcript_id", "sequence", name="uq_transcript_segments_sequence"),
    )
    op.create_index(
        op.f("ix_transcript_segments_witness_id"),
        "transcript_segments",
        ["witness_id"],
        unique=False,
    )
    op.create_table(
        "witness_appearances",
        sa.Column("witness_id", sa.UUID(), nullable=False),
        sa.Column("hearing_id", sa.UUID(), nullable=False),
        sa.Column("transcript_id", sa.UUID(), nullable=True),
        sa.Column("testimony_date", sa.Date(), nullable=True),
        sa.Column("page_from", sa.Integer(), nullable=True),
        sa.Column("page_to", sa.Integer(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.CheckConstraint(
            "page_to IS NULL OR page_from IS NULL OR page_to >= page_from",
            name=op.f("ck_witness_appearances_page_range"),
        ),
        sa.ForeignKeyConstraint(
            ["hearing_id"],
            ["hearings.id"],
            name=op.f("fk_witness_appearances_hearing_id_hearings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["transcript_id"],
            ["transcripts.id"],
            name=op.f("fk_witness_appearances_transcript_id_transcripts"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["witness_id"],
            ["witnesses.id"],
            name=op.f("fk_witness_appearances_witness_id_witnesses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_witness_appearances")),
        sa.UniqueConstraint(
            "witness_id", "hearing_id", name="uq_witness_appearances_witness_hearing"
        ),
    )
    op.create_index(
        op.f("ix_witness_appearances_hearing_id"),
        "witness_appearances",
        ["hearing_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_witness_appearances_witness_id"),
        "witness_appearances",
        ["witness_id"],
        unique=False,
    )
    op.create_table(
        "citations",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.String(length=512), nullable=True),
        sa.Column(
            "citation_type",
            postgresql.ENUM(
                "document",
                "document_version",
                "page",
                "paragraph",
                "transcript",
                "transcript_line",
                "exhibit",
                "witness",
                "finding",
                "decision",
                "url",
                "unknown",
                name="citation_type",
                create_type=False,
            ),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("source_document_version_id", sa.UUID(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_para", sa.Integer(), nullable=True),
        sa.Column("source_transcript_segment_id", sa.UUID(), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("target_document_id", sa.UUID(), nullable=True),
        sa.Column("target_document_version_id", sa.UUID(), nullable=True),
        sa.Column("target_page", sa.Integer(), nullable=True),
        sa.Column("target_para_from", sa.Integer(), nullable=True),
        sa.Column("target_para_to", sa.Integer(), nullable=True),
        sa.Column("target_transcript_id", sa.UUID(), nullable=True),
        sa.Column("target_transcript_segment_id", sa.UUID(), nullable=True),
        sa.Column("target_line_from", sa.Integer(), nullable=True),
        sa.Column("target_line_to", sa.Integer(), nullable=True),
        sa.Column("target_exhibit_id", sa.UUID(), nullable=True),
        sa.Column("target_witness_id", sa.UUID(), nullable=True),
        sa.Column("target_finding_id", sa.UUID(), nullable=True),
        sa.Column(
            "resolution_state",
            postgresql.ENUM(
                "resolved",
                "unresolved",
                "ambiguous",
                "invalid",
                name="resolution_state",
                create_type=False,
            ),
            server_default="unresolved",
            nullable=False,
        ),
        sa.Column(
            "resolution_method",
            postgresql.ENUM(
                "exact_id", "pattern", "manual", "none", name="resolution_method", create_type=False
            ),
            server_default="none",
            nullable=False,
        ),
        sa.Column("resolution_confidence", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("display", sa.String(length=255), server_default="UNRESOLVED", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "verification_state",
            postgresql.ENUM(
                "unreviewed",
                "ai_flagged",
                "human_verified",
                "human_rejected",
                "needs_more_evidence",
                "unresolved",
                name="verification_state",
                create_type=False,
            ),
            server_default="unreviewed",
            nullable=False,
        ),
        sa.Column("verified_by", sa.String(length=128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(resolution_state = 'resolved' AND num_nonnulls(target_document_id, target_document_version_id, target_transcript_id, target_transcript_segment_id, target_exhibit_id, target_witness_id, target_finding_id) >= 1) OR (resolution_state <> 'resolved' AND num_nonnulls(target_document_id, target_document_version_id, target_transcript_id, target_transcript_segment_id, target_exhibit_id, target_witness_id, target_finding_id) = 0)",
            name=op.f("ck_citations_targets_match_resolution_state"),
        ),
        sa.CheckConstraint(
            "resolution_state <> 'resolved' OR resolved_at IS NOT NULL",
            name=op.f("ck_citations_resolved_has_timestamp"),
        ),
        sa.CheckConstraint(
            "resolution_state = 'resolved' OR display = 'UNRESOLVED'",
            name=op.f("ck_citations_unresolved_display_literal"),
        ),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name=op.f("ck_citations_human_verification_has_reviewer"),
        ),
        sa.CheckConstraint(
            "resolution_confidence IS NULL OR (resolution_confidence >= 0 AND resolution_confidence <= 1)",
            name=op.f("ck_citations_confidence_unit_interval"),
        ),
        sa.CheckConstraint(
            "target_line_to IS NULL OR target_line_from IS NULL OR target_line_to >= target_line_from",
            name=op.f("ck_citations_line_range"),
        ),
        sa.CheckConstraint(
            "target_page IS NULL OR target_page >= 1",
            name=op.f("ck_citations_target_page_positive"),
        ),
        sa.CheckConstraint(
            "target_para_to IS NULL OR target_para_from IS NULL OR target_para_to >= target_para_from",
            name=op.f("ck_citations_para_range"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_citations_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_citations_source_document_version_id_document_versions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_transcript_segment_id"],
            ["transcript_segments.id"],
            name=op.f("fk_citations_source_transcript_segment_id_transcript_segments"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_document_id"],
            ["documents.id"],
            name=op.f("fk_citations_target_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_document_version_id"],
            ["document_versions.id"],
            name=op.f("fk_citations_target_document_version_id_document_versions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_exhibit_id"],
            ["exhibits.id"],
            name=op.f("fk_citations_target_exhibit_id_exhibits"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_finding_id"],
            ["findings.id"],
            name=op.f("fk_citations_target_finding_id_findings"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_transcript_id"],
            ["transcripts.id"],
            name=op.f("fk_citations_target_transcript_id_transcripts"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_transcript_segment_id"],
            ["transcript_segments.id"],
            name=op.f("fk_citations_target_transcript_segment_id_transcript_segments"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_witness_id"],
            ["witnesses.id"],
            name=op.f("fk_citations_target_witness_id_witnesses"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_citations")),
    )
    op.create_index(
        "ix_citations_case_resolution", "citations", ["case_id", "resolution_state"], unique=False
    )
    op.create_index(
        op.f("ix_citations_normalized_text"), "citations", ["normalized_text"], unique=False
    )
    op.create_index(
        op.f("ix_citations_source_document_version_id"),
        "citations",
        ["source_document_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_citations_target_document_id"), "citations", ["target_document_id"], unique=False
    )
    op.create_index(
        op.f("ix_citations_target_document_version_id"),
        "citations",
        ["target_document_version_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_citations_target_exhibit_id"), "citations", ["target_exhibit_id"], unique=False
    )
    op.create_index(
        op.f("ix_citations_target_finding_id"), "citations", ["target_finding_id"], unique=False
    )
    op.create_index(
        op.f("ix_citations_target_transcript_id"),
        "citations",
        ["target_transcript_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_citations_target_witness_id"), "citations", ["target_witness_id"], unique=False
    )
    # findings.citation_id <-> citations.target_finding_id is circular; the
    # findings side is added once both tables exist.
    op.create_foreign_key(
        op.f("fk_findings_citation_id_citations"),
        "findings",
        "citations",
        ["citation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "ai_output_citations",
        sa.Column("ai_output_id", sa.UUID(), nullable=False),
        sa.Column("citation_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ai_output_id"],
            ["ai_outputs.id"],
            name=op.f("fk_ai_output_citations_ai_output_id_ai_outputs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            name=op.f("fk_ai_output_citations_citation_id_citations"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("ai_output_id", "citation_id", name=op.f("pk_ai_output_citations")),
    )
    op.create_table(
        "arguments",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("argument_key", sa.String(length=64), nullable=False),
        sa.Column(
            "party",
            postgresql.ENUM(
                "spo",
                "defence",
                "victims_counsel",
                "court",
                "other",
                name="party",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("document_id", sa.UUID(), nullable=True),
        sa.Column("para_from", sa.Integer(), nullable=True),
        sa.Column("para_to", sa.Integer(), nullable=True),
        sa.Column("citation_id", sa.UUID(), nullable=True),
        sa.Column("finding_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "verification_state",
            postgresql.ENUM(
                "unreviewed",
                "ai_flagged",
                "human_verified",
                "human_rejected",
                "needs_more_evidence",
                "unresolved",
                name="verification_state",
                create_type=False,
            ),
            server_default="unreviewed",
            nullable=False,
        ),
        sa.Column("verified_by", sa.String(length=128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name=op.f("ck_arguments_human_verification_has_reviewer"),
        ),
        sa.CheckConstraint(
            "para_to IS NULL OR para_from IS NULL OR para_to >= para_from",
            name=op.f("ck_arguments_para_range"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_arguments_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            name=op.f("fk_arguments_citation_id_citations"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_arguments_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            name=op.f("fk_arguments_finding_id_findings"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_arguments")),
        sa.UniqueConstraint("case_id", "argument_key", name="uq_arguments_case_key"),
    )
    op.create_index(op.f("ix_arguments_case_id"), "arguments", ["case_id"], unique=False)
    op.create_index(op.f("ix_arguments_document_id"), "arguments", ["document_id"], unique=False)
    op.create_index(op.f("ix_arguments_finding_id"), "arguments", ["finding_id"], unique=False)
    op.create_table(
        "claims",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("claim_key", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "origin",
            postgresql.ENUM(
                "source_extracted", "human", "ai_extracted", name="claim_origin", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("source_citation_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "verification_state",
            postgresql.ENUM(
                "unreviewed",
                "ai_flagged",
                "human_verified",
                "human_rejected",
                "needs_more_evidence",
                "unresolved",
                name="verification_state",
                create_type=False,
            ),
            server_default="unreviewed",
            nullable=False,
        ),
        sa.Column("verified_by", sa.String(length=128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name=op.f("ck_claims_human_verification_has_reviewer"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_claims_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["source_citation_id"],
            ["citations.id"],
            name=op.f("fk_claims_source_citation_id_citations"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claims")),
        sa.UniqueConstraint("case_id", "claim_key", name="uq_claims_case_key"),
    )
    op.create_index(op.f("ix_claims_case_id"), "claims", ["case_id"], unique=False)
    op.create_table(
        "events",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "date_type",
            postgresql.ENUM(
                "event",
                "document",
                "filing",
                "testimony",
                "decision",
                name="date_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("date_from", sa.Date(), nullable=True),
        sa.Column("date_to", sa.Date(), nullable=True),
        sa.Column(
            "date_precision",
            postgresql.ENUM(
                "exact",
                "month_only",
                "year_only",
                "range",
                "approximate",
                "unknown",
                name="date_precision",
                create_type=False,
            ),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("incident_id", sa.UUID(), nullable=True),
        sa.Column("document_id", sa.UUID(), nullable=True),
        sa.Column("hearing_id", sa.UUID(), nullable=True),
        sa.Column("citation_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "date_precision = 'unknown' OR date_from IS NOT NULL",
            name=op.f("ck_events_known_precision_has_date"),
        ),
        sa.CheckConstraint(
            "date_to IS NULL OR date_from IS NULL OR date_to >= date_from",
            name=op.f("ck_events_date_range"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_events_case_id_cases"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            name=op.f("fk_events_citation_id_citations"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_events_document_id_documents"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["hearing_id"],
            ["hearings.id"],
            name=op.f("fk_events_hearing_id_hearings"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name=op.f("fk_events_incident_id_incidents"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
    )
    op.create_index(op.f("ix_events_case_id"), "events", ["case_id"], unique=False)
    op.create_index(op.f("ix_events_incident_id"), "events", ["incident_id"], unique=False)
    op.create_table(
        "finding_evidence_links",
        sa.Column("finding_id", sa.UUID(), nullable=False),
        sa.Column("citation_id", sa.UUID(), nullable=False),
        sa.Column(
            "link_type",
            postgresql.ENUM(
                "relies_on",
                "supports",
                "qualifies",
                "context",
                name="finding_link_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("court_cited", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("court_cited_para", sa.Integer(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "verification_state",
            postgresql.ENUM(
                "unreviewed",
                "ai_flagged",
                "human_verified",
                "human_rejected",
                "needs_more_evidence",
                "unresolved",
                name="verification_state",
                create_type=False,
            ),
            server_default="unreviewed",
            nullable=False,
        ),
        sa.Column("verified_by", sa.String(length=128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name=op.f("ck_finding_evidence_links_human_verification_has_reviewer"),
        ),
        sa.CheckConstraint(
            "court_cited OR court_cited_para IS NULL",
            name=op.f("ck_finding_evidence_links_cited_para_needs_court_cited"),
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            name=op.f("fk_finding_evidence_links_citation_id_citations"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            name=op.f("fk_finding_evidence_links_finding_id_findings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_finding_evidence_links")),
        sa.UniqueConstraint(
            "finding_id", "citation_id", "link_type", name="uq_finding_evidence_links_triplet"
        ),
    )
    op.create_index(
        op.f("ix_finding_evidence_links_citation_id"),
        "finding_evidence_links",
        ["citation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_finding_evidence_links_finding_id"),
        "finding_evidence_links",
        ["finding_id"],
        unique=False,
    )
    op.create_table(
        "research_note_citations",
        sa.Column("note_id", sa.UUID(), nullable=False),
        sa.Column("citation_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            name=op.f("fk_research_note_citations_citation_id_citations"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["note_id"],
            ["research_notes.id"],
            name=op.f("fk_research_note_citations_note_id_research_notes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("note_id", "citation_id", name=op.f("pk_research_note_citations")),
    )
    op.create_table(
        "argument_responses",
        sa.Column("argument_id", sa.UUID(), nullable=False),
        sa.Column("response_argument_id", sa.UUID(), nullable=False),
        sa.Column(
            "response_kind",
            postgresql.ENUM(
                "responds_to",
                "disputes",
                "concurs_with",
                "rules_on",
                name="argument_response_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("citation_id", sa.UUID(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "argument_id <> response_argument_id",
            name=op.f("ck_argument_responses_no_self_response"),
        ),
        sa.ForeignKeyConstraint(
            ["argument_id"],
            ["arguments.id"],
            name=op.f("fk_argument_responses_argument_id_arguments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            name=op.f("fk_argument_responses_citation_id_citations"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["response_argument_id"],
            ["arguments.id"],
            name=op.f("fk_argument_responses_response_argument_id_arguments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_argument_responses")),
        sa.UniqueConstraint(
            "argument_id", "response_argument_id", "response_kind", name="uq_argument_responses"
        ),
    )
    op.create_index(
        op.f("ix_argument_responses_argument_id"),
        "argument_responses",
        ["argument_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_argument_responses_response_argument_id"),
        "argument_responses",
        ["response_argument_id"],
        unique=False,
    )
    op.create_table(
        "claim_mentions",
        sa.Column("claim_id", sa.UUID(), nullable=False),
        sa.Column("citation_id", sa.UUID(), nullable=False),
        sa.Column(
            "stance",
            postgresql.ENUM(
                "supports",
                "contradicts",
                "qualifies",
                "neutral",
                "unclear",
                name="claim_stance",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("quote_text", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "verification_state",
            postgresql.ENUM(
                "unreviewed",
                "ai_flagged",
                "human_verified",
                "human_rejected",
                "needs_more_evidence",
                "unresolved",
                name="verification_state",
                create_type=False,
            ),
            server_default="unreviewed",
            nullable=False,
        ),
        sa.Column("verified_by", sa.String(length=128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name=op.f("ck_claim_mentions_human_verification_has_reviewer"),
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            name=op.f("fk_claim_mentions_citation_id_citations"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["claims.id"],
            name=op.f("fk_claim_mentions_claim_id_claims"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claim_mentions")),
        sa.UniqueConstraint("claim_id", "citation_id", name="uq_claim_mentions_claim_citation"),
    )
    op.create_index(
        op.f("ix_claim_mentions_citation_id"), "claim_mentions", ["citation_id"], unique=False
    )
    op.create_index(
        op.f("ix_claim_mentions_claim_id"), "claim_mentions", ["claim_id"], unique=False
    )
    op.create_table(
        "graph_nodes",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column(
            "entity_kind",
            postgresql.ENUM(
                "person",
                "witness",
                "organization",
                "location",
                "document",
                "document_version",
                "exhibit",
                "incident",
                "event",
                "claim",
                "finding",
                "argument",
                "hearing",
                "transcript",
                name="entity_kind",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("person_id", sa.UUID(), nullable=True),
        sa.Column("witness_id", sa.UUID(), nullable=True),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("location_id", sa.UUID(), nullable=True),
        sa.Column("document_id", sa.UUID(), nullable=True),
        sa.Column("exhibit_id", sa.UUID(), nullable=True),
        sa.Column("incident_id", sa.UUID(), nullable=True),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column("claim_id", sa.UUID(), nullable=True),
        sa.Column("finding_id", sa.UUID(), nullable=True),
        sa.Column("argument_id", sa.UUID(), nullable=True),
        sa.Column("hearing_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(entity_kind = 'person' AND person_id IS NOT NULL) OR (entity_kind = 'witness' AND witness_id IS NOT NULL) OR (entity_kind = 'organization' AND organization_id IS NOT NULL) OR (entity_kind = 'location' AND location_id IS NOT NULL) OR (entity_kind = 'document' AND document_id IS NOT NULL) OR (entity_kind = 'exhibit' AND exhibit_id IS NOT NULL) OR (entity_kind = 'incident' AND incident_id IS NOT NULL) OR (entity_kind = 'event' AND event_id IS NOT NULL) OR (entity_kind = 'claim' AND claim_id IS NOT NULL) OR (entity_kind = 'finding' AND finding_id IS NOT NULL) OR (entity_kind = 'argument' AND argument_id IS NOT NULL) OR (entity_kind = 'hearing' AND hearing_id IS NOT NULL)",
            name=op.f("ck_graph_nodes_kind_matches_entity"),
        ),
        sa.CheckConstraint(
            "num_nonnulls(person_id, witness_id, organization_id, location_id, document_id, exhibit_id, incident_id, event_id, claim_id, finding_id, argument_id, hearing_id) = 1",
            name=op.f("ck_graph_nodes_exactly_one_entity"),
        ),
        sa.ForeignKeyConstraint(
            ["argument_id"],
            ["arguments.id"],
            name=op.f("fk_graph_nodes_argument_id_arguments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_graph_nodes_case_id_cases"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["claims.id"],
            name=op.f("fk_graph_nodes_claim_id_claims"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_graph_nodes_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_graph_nodes_event_id_events"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["exhibit_id"],
            ["exhibits.id"],
            name=op.f("fk_graph_nodes_exhibit_id_exhibits"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            name=op.f("fk_graph_nodes_finding_id_findings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hearing_id"],
            ["hearings.id"],
            name=op.f("fk_graph_nodes_hearing_id_hearings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name=op.f("fk_graph_nodes_incident_id_incidents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            name=op.f("fk_graph_nodes_location_id_locations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_graph_nodes_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_graph_nodes_person_id_persons"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["witness_id"],
            ["witnesses.id"],
            name=op.f("fk_graph_nodes_witness_id_witnesses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_graph_nodes")),
    )
    op.create_index(op.f("ix_graph_nodes_case_id"), "graph_nodes", ["case_id"], unique=False)
    op.create_index(
        "uq_graph_nodes_argument_id",
        "graph_nodes",
        ["argument_id"],
        unique=True,
        postgresql_where="argument_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_claim_id",
        "graph_nodes",
        ["claim_id"],
        unique=True,
        postgresql_where="claim_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_document_id",
        "graph_nodes",
        ["document_id"],
        unique=True,
        postgresql_where="document_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_event_id",
        "graph_nodes",
        ["event_id"],
        unique=True,
        postgresql_where="event_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_exhibit_id",
        "graph_nodes",
        ["exhibit_id"],
        unique=True,
        postgresql_where="exhibit_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_finding_id",
        "graph_nodes",
        ["finding_id"],
        unique=True,
        postgresql_where="finding_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_hearing_id",
        "graph_nodes",
        ["hearing_id"],
        unique=True,
        postgresql_where="hearing_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_incident_id",
        "graph_nodes",
        ["incident_id"],
        unique=True,
        postgresql_where="incident_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_location_id",
        "graph_nodes",
        ["location_id"],
        unique=True,
        postgresql_where="location_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_organization_id",
        "graph_nodes",
        ["organization_id"],
        unique=True,
        postgresql_where="organization_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_person_id",
        "graph_nodes",
        ["person_id"],
        unique=True,
        postgresql_where="person_id IS NOT NULL",
    )
    op.create_index(
        "uq_graph_nodes_witness_id",
        "graph_nodes",
        ["witness_id"],
        unique=True,
        postgresql_where="witness_id IS NOT NULL",
    )
    op.create_table(
        "relationships",
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("from_node_id", sa.UUID(), nullable=False),
        sa.Column("to_node_id", sa.UUID(), nullable=False),
        sa.Column(
            "relationship_type",
            postgresql.ENUM(
                "mentioned_in",
                "co_mention",
                "testified_about",
                "testified_at",
                "cited_in",
                "relies_on",
                "supports",
                "contradicts",
                "qualifies",
                "disputes",
                "responds_to",
                "associated_with",
                "located_at",
                "occurred_at",
                "member_of",
                "held_position_in",
                "authored",
                "filed_by",
                "challenged_by",
                "corroborated_by",
                "part_of_incident",
                "precedes",
                "follows",
                name="relationship_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("citation_id", sa.UUID(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "verification_state",
            postgresql.ENUM(
                "unreviewed",
                "ai_flagged",
                "human_verified",
                "human_rejected",
                "needs_more_evidence",
                "unresolved",
                name="verification_state",
                create_type=False,
            ),
            server_default="unreviewed",
            nullable=False,
        ),
        sa.Column("verified_by", sa.String(length=128), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "verification_state NOT IN ('human_verified', 'human_rejected') OR (verified_by IS NOT NULL AND verified_at IS NOT NULL)",
            name=op.f("ck_relationships_human_verification_has_reviewer"),
        ),
        sa.CheckConstraint(
            "from_node_id <> to_node_id", name=op.f("ck_relationships_no_self_loop")
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name=op.f("fk_relationships_case_id_cases"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["citation_id"],
            ["citations.id"],
            name=op.f("fk_relationships_citation_id_citations"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["from_node_id"],
            ["graph_nodes.id"],
            name=op.f("fk_relationships_from_node_id_graph_nodes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["to_node_id"],
            ["graph_nodes.id"],
            name=op.f("fk_relationships_to_node_id_graph_nodes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_relationships")),
        sa.UniqueConstraint(
            "from_node_id",
            "to_node_id",
            "relationship_type",
            "citation_id",
            name="uq_relationships_edge_citation",
        ),
    )
    op.create_index(op.f("ix_relationships_case_id"), "relationships", ["case_id"], unique=False)
    op.create_index(
        op.f("ix_relationships_citation_id"), "relationships", ["citation_id"], unique=False
    )
    op.create_index(
        op.f("ix_relationships_from_node_id"), "relationships", ["from_node_id"], unique=False
    )
    op.create_index(
        op.f("ix_relationships_to_node_id"), "relationships", ["to_node_id"], unique=False
    )
    # --- documents: public_state -> visibility, artifact columns -> versions ---
    op.add_column(
        "documents",
        sa.Column("filing_party", PARTY, nullable=True),
    )
    op.add_column("documents", sa.Column("public_date", sa.Date(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("visibility", VISIBILITY, server_default="public", nullable=False),
    )
    op.execute(
        """
        UPDATE documents SET visibility = CASE public_state
            WHEN 'public' THEN 'public'::visibility
            WHEN 'public_redacted' THEN 'public_redacted'::visibility
            ELSE 'not_public'::visibility
        END
        """
    )
    op.drop_column("documents", "public_state")
    op.execute("DROP TYPE IF EXISTS document_public_state")
    # No document row exists before Phase 7; these columns now live on
    # document_versions. Dropping them is lossless for every real deployment.
    op.drop_column("documents", "page_count")
    op.drop_column("documents", "storage_key")
    op.drop_column("documents", "sha256")


def downgrade() -> None:
    # --- documents: visibility -> public_state ------------------------------
    document_public_state = postgresql.ENUM(
        "public", "public_redacted", "not_held", name="document_public_state", create_type=False
    )
    document_public_state.create(op.get_bind(), checkfirst=True)
    op.add_column("documents", sa.Column("sha256", sa.String(length=64), nullable=True))
    op.add_column("documents", sa.Column("storage_key", sa.String(length=512), nullable=True))
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("public_state", document_public_state, nullable=True))
    op.execute(
        """
        UPDATE documents SET public_state = CASE visibility
            WHEN 'public' THEN 'public'::document_public_state
            WHEN 'public_redacted' THEN 'public_redacted'::document_public_state
            ELSE 'not_held'::document_public_state
        END
        """
    )
    op.alter_column("documents", "public_state", nullable=False)
    op.drop_column("documents", "visibility")
    op.drop_column("documents", "public_date")
    op.drop_column("documents", "filing_party")
    op.drop_index(op.f("ix_relationships_to_node_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_from_node_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_citation_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_case_id"), table_name="relationships")
    op.drop_table("relationships")
    op.drop_index(
        "uq_graph_nodes_witness_id",
        table_name="graph_nodes",
        postgresql_where="witness_id IS NOT NULL",
    )
    op.drop_index(
        "uq_graph_nodes_person_id",
        table_name="graph_nodes",
        postgresql_where="person_id IS NOT NULL",
    )
    op.drop_index(
        "uq_graph_nodes_organization_id",
        table_name="graph_nodes",
        postgresql_where="organization_id IS NOT NULL",
    )
    op.drop_index(
        "uq_graph_nodes_location_id",
        table_name="graph_nodes",
        postgresql_where="location_id IS NOT NULL",
    )
    op.drop_index(
        "uq_graph_nodes_incident_id",
        table_name="graph_nodes",
        postgresql_where="incident_id IS NOT NULL",
    )
    op.drop_index(
        "uq_graph_nodes_hearing_id",
        table_name="graph_nodes",
        postgresql_where="hearing_id IS NOT NULL",
    )
    op.drop_index(
        "uq_graph_nodes_finding_id",
        table_name="graph_nodes",
        postgresql_where="finding_id IS NOT NULL",
    )
    op.drop_index(
        "uq_graph_nodes_exhibit_id",
        table_name="graph_nodes",
        postgresql_where="exhibit_id IS NOT NULL",
    )
    op.drop_index(
        "uq_graph_nodes_event_id", table_name="graph_nodes", postgresql_where="event_id IS NOT NULL"
    )
    op.drop_index(
        "uq_graph_nodes_document_id",
        table_name="graph_nodes",
        postgresql_where="document_id IS NOT NULL",
    )
    op.drop_index(
        "uq_graph_nodes_claim_id", table_name="graph_nodes", postgresql_where="claim_id IS NOT NULL"
    )
    op.drop_index(
        "uq_graph_nodes_argument_id",
        table_name="graph_nodes",
        postgresql_where="argument_id IS NOT NULL",
    )
    op.drop_index(op.f("ix_graph_nodes_case_id"), table_name="graph_nodes")
    op.drop_table("graph_nodes")
    op.drop_index(op.f("ix_claim_mentions_claim_id"), table_name="claim_mentions")
    op.drop_index(op.f("ix_claim_mentions_citation_id"), table_name="claim_mentions")
    op.drop_table("claim_mentions")
    op.drop_index(
        op.f("ix_argument_responses_response_argument_id"), table_name="argument_responses"
    )
    op.drop_index(op.f("ix_argument_responses_argument_id"), table_name="argument_responses")
    op.drop_table("argument_responses")
    op.drop_table("research_note_citations")
    op.drop_index(op.f("ix_finding_evidence_links_finding_id"), table_name="finding_evidence_links")
    op.drop_index(
        op.f("ix_finding_evidence_links_citation_id"), table_name="finding_evidence_links"
    )
    op.drop_table("finding_evidence_links")
    op.drop_index(op.f("ix_events_incident_id"), table_name="events")
    op.drop_index(op.f("ix_events_case_id"), table_name="events")
    op.drop_table("events")
    op.drop_index(op.f("ix_claims_case_id"), table_name="claims")
    op.drop_table("claims")
    op.drop_index(op.f("ix_arguments_finding_id"), table_name="arguments")
    op.drop_index(op.f("ix_arguments_document_id"), table_name="arguments")
    op.drop_index(op.f("ix_arguments_case_id"), table_name="arguments")
    op.drop_table("arguments")
    op.drop_table("ai_output_citations")
    op.drop_constraint(op.f("fk_findings_citation_id_citations"), "findings", type_="foreignkey")
    op.drop_index(op.f("ix_citations_target_witness_id"), table_name="citations")
    op.drop_index(op.f("ix_citations_target_transcript_id"), table_name="citations")
    op.drop_index(op.f("ix_citations_target_finding_id"), table_name="citations")
    op.drop_index(op.f("ix_citations_target_exhibit_id"), table_name="citations")
    op.drop_index(op.f("ix_citations_target_document_version_id"), table_name="citations")
    op.drop_index(op.f("ix_citations_target_document_id"), table_name="citations")
    op.drop_index(op.f("ix_citations_source_document_version_id"), table_name="citations")
    op.drop_index(op.f("ix_citations_normalized_text"), table_name="citations")
    op.drop_index("ix_citations_case_resolution", table_name="citations")
    op.drop_table("citations")
    op.drop_index(op.f("ix_witness_appearances_witness_id"), table_name="witness_appearances")
    op.drop_index(op.f("ix_witness_appearances_hearing_id"), table_name="witness_appearances")
    op.drop_table("witness_appearances")
    op.drop_index(op.f("ix_transcript_segments_witness_id"), table_name="transcript_segments")
    op.drop_table("transcript_segments")
    op.drop_index(op.f("ix_source_records_document_id"), table_name="source_records")
    op.drop_index(op.f("ix_source_records_case_id"), table_name="source_records")
    op.drop_table("source_records")
    op.drop_index(
        op.f("ix_record_identifiers_normalized_identifier"), table_name="record_identifiers"
    )
    op.drop_index(op.f("ix_record_identifiers_case_id"), table_name="record_identifiers")
    op.drop_table("record_identifiers")
    op.drop_table("document_chunks")
    op.drop_index(
        "uq_transcripts_document_version",
        table_name="transcripts",
        postgresql_where="document_version_id IS NOT NULL",
    )
    op.drop_index(op.f("ix_transcripts_official_ref"), table_name="transcripts")
    op.drop_index(op.f("ix_transcripts_hearing_id"), table_name="transcripts")
    op.drop_table("transcripts")
    op.drop_index(op.f("ix_findings_person_id"), table_name="findings")
    op.drop_index(op.f("ix_findings_judgment_document_id"), table_name="findings")
    op.drop_index(op.f("ix_findings_incident_id"), table_name="findings")
    op.drop_index(op.f("ix_findings_case_id"), table_name="findings")
    op.drop_table("findings")
    op.drop_index(op.f("ix_exhibits_case_id"), table_name="exhibits")
    op.drop_table("exhibits")
    op.drop_table("document_sections")
    op.drop_table("document_pages")
    op.drop_index(op.f("ix_witnesses_person_id"), table_name="witnesses")
    op.drop_index(op.f("ix_witnesses_case_id"), table_name="witnesses")
    op.drop_table("witnesses")
    op.drop_index(op.f("ix_person_aliases_person_id"), table_name="person_aliases")
    op.drop_table("person_aliases")
    op.drop_index(op.f("ix_incidents_case_id"), table_name="incidents")
    op.drop_table("incidents")
    op.drop_index(
        "uq_document_versions_sha256",
        table_name="document_versions",
        postgresql_where="sha256 IS NOT NULL",
    )
    op.drop_index(op.f("ix_document_versions_document_id"), table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_index(op.f("ix_ai_outputs_ai_run_id"), table_name="ai_outputs")
    op.drop_table("ai_outputs")
    op.drop_index(op.f("ix_research_notes_case_id"), table_name="research_notes")
    op.drop_table("research_notes")
    op.drop_index(op.f("ix_persons_case_id"), table_name="persons")
    op.drop_table("persons")
    op.drop_index(op.f("ix_organizations_case_id"), table_name="organizations")
    op.drop_table("organizations")
    op.drop_index(op.f("ix_locations_case_id"), table_name="locations")
    op.drop_table("locations")
    op.drop_index(op.f("ix_ingestion_jobs_case_id"), table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    op.drop_index(op.f("ix_hearings_case_id"), table_name="hearings")
    op.drop_table("hearings")
    op.drop_index(op.f("ix_ai_runs_case_id"), table_name="ai_runs")
    op.drop_table("ai_runs")
    op.drop_table("prompt_versions")

    op.execute("DROP TYPE IF EXISTS ai_run_status")
    op.execute("DROP TYPE IF EXISTS answer_block_kind")
    op.execute("DROP TYPE IF EXISTS argument_response_kind")
    op.execute("DROP TYPE IF EXISTS citation_type")
    op.execute("DROP TYPE IF EXISTS claim_origin")
    op.execute("DROP TYPE IF EXISTS claim_stance")
    op.execute("DROP TYPE IF EXISTS date_precision")
    op.execute("DROP TYPE IF EXISTS date_type")
    op.execute("DROP TYPE IF EXISTS document_version_type")
    op.execute("DROP TYPE IF EXISTS entity_kind")
    op.execute("DROP TYPE IF EXISTS examination_type")
    op.execute("DROP TYPE IF EXISTS finding_link_type")
    op.execute("DROP TYPE IF EXISTS identifier_kind")
    op.execute("DROP TYPE IF EXISTS ingestion_job_status")
    op.execute("DROP TYPE IF EXISTS party")
    op.execute("DROP TYPE IF EXISTS relationship_type")
    op.execute("DROP TYPE IF EXISTS resolution_method")
    op.execute("DROP TYPE IF EXISTS resolution_state")
    op.execute("DROP TYPE IF EXISTS source_system")
    op.execute("DROP TYPE IF EXISTS text_extraction_method")
    op.execute("DROP TYPE IF EXISTS verification_state")
    op.execute("DROP TYPE IF EXISTS visibility")
    op.execute("DROP TYPE IF EXISTS witness_identity_status")
