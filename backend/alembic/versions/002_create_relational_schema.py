"""Create the governed source, ingestion, answer, and citation schema.

Revision ID: 002_create_relational_schema
Revises: 001_enable_pgvector
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op
from src.config import settings

revision = "002_create_relational_schema"
down_revision = "001_enable_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE source_type AS ENUM "
        "('webpage', 'linked_page', 'pdf', 'form', "
        "'catalog', 'schedule', 'policy', 'office_resource')"
    )
    op.execute("CREATE TYPE source_status AS ENUM ('active', 'blocked', 'archived')")
    op.execute("CREATE TYPE extraction_status AS ENUM ('pending', 'complete', 'failed')")
    op.execute(
        "CREATE TYPE source_activation_status AS ENUM "
        "('inactive', 'active', 'superseded', 'rejected')"
    )
    op.execute("CREATE TYPE campus AS ENUM ('hammond', 'westville')")
    op.execute(
        "CREATE TYPE ingestion_job_status AS ENUM "
        "('pending', 'fetching', 'extracting', 'embedding', 'validating', 'complete', 'failed')"
    )
    op.execute("CREATE TYPE response_state AS ENUM ('answer', 'clarification', 'refusal', 'error')")

    source_type = postgresql.ENUM(name="source_type", create_type=False)
    source_status = postgresql.ENUM(name="source_status", create_type=False)
    extraction_status = postgresql.ENUM(name="extraction_status", create_type=False)
    activation_status = postgresql.ENUM(name="source_activation_status", create_type=False)
    campus = postgresql.ENUM(name="campus", create_type=False)
    job_status = postgresql.ENUM(name="ingestion_job_status", create_type=False)
    response_state = postgresql.ENUM(name="response_state", create_type=False)

    op.create_table(
        "approved_sources",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("owner_office", sa.Text(), nullable=True),
        sa.Column("status", source_status, server_default=sa.text("'active'"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_approved_sources_title"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_url"),
    )

    op.create_table(
        "escalation_destinations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("office_name", sa.Text(), nullable=False),
        sa.Column("service_description", sa.Text(), nullable=False),
        sa.Column("contact_url", sa.Text(), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("campus", campus, nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("length(trim(office_name)) > 0", name="ck_escalations_office_name"),
        sa.CheckConstraint(
            "length(trim(service_description)) > 0", name="ck_escalations_service_description"
        ),
        sa.CheckConstraint("length(trim(contact_url)) > 0", name="ck_escalations_contact_url"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "source_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "extraction_status",
            extraction_status,
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "activation_status",
            activation_status,
            server_default=sa.text("'inactive'"),
            nullable=False,
        ),
        sa.Column(
            "embedding_model", sa.Text(), server_default=settings.embedding_model, nullable=False
        ),
        sa.Column(
            "embedding_dimension",
            sa.Integer(),
            server_default=str(settings.embedding_dimension),
            nullable=False,
        ),
        sa.Column("chunking_version", sa.String(length=64), nullable=False),
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "embedding_dimension > 0", name="ck_source_versions_embedding_dimension_positive"
        ),
        sa.CheckConstraint(
            f"embedding_dimension = {settings.embedding_dimension}",
            name="ck_source_versions_embedding_dimension_matches_config",
        ),
        sa.ForeignKeyConstraint(["source_id"], ["approved_sources.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id", "content_hash", name="uq_source_versions_source_content_hash"
        ),
    )
    op.create_index("ix_source_versions_source_id", "source_versions", ["source_id"], unique=False)
    op.create_index(
        "uq_source_versions_one_active_per_source",
        "source_versions",
        ["source_id"],
        unique=True,
        postgresql_where=sa.text("activation_status = 'active'"),
    )

    op.create_table(
        "source_chunks",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("source_version_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(settings.embedding_dimension), nullable=True),
        sa.Column(
            "search_document",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', content)", persisted=True),
            nullable=False,
        ),
        sa.Column("heading_path", sa.Text(), nullable=True),
        sa.Column("locator", sa.Text(), nullable=True),
        sa.Column("campus", campus, nullable=True),
        sa.Column("term", sa.String(length=64), nullable=True),
        sa.Column("program", sa.String(length=255), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.CheckConstraint("ordinal >= 0", name="ck_source_chunks_ordinal_nonnegative"),
        sa.CheckConstraint(
            "effective_from IS NULL OR effective_to IS NULL OR effective_to >= effective_from",
            name="ck_source_chunks_effective_date_range",
        ),
        sa.ForeignKeyConstraint(["source_id"], ["approved_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_version_id", "ordinal", name="uq_source_chunks_version_ordinal"
        ),
    )
    op.create_index("ix_source_chunks_source_id", "source_chunks", ["source_id"], unique=False)
    op.create_index(
        "ix_source_chunks_source_version_id", "source_chunks", ["source_version_id"], unique=False
    )

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("source_version_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("status", job_status, server_default=sa.text("'pending'"), nullable=False),
        sa.Column("dry_run", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("chunk_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("embedded_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("validation_report", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("chunk_count >= 0", name="ck_ingestion_jobs_chunk_count_nonnegative"),
        sa.CheckConstraint(
            "embedded_count >= 0", name="ck_ingestion_jobs_embedded_count_nonnegative"
        ),
        sa.ForeignKeyConstraint(["source_version_id"], ["source_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_jobs_source_version_id", "ingestion_jobs", ["source_version_id"], unique=False
    )

    op.create_table(
        "student_questions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("message_redacted", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "length(trim(message_redacted)) > 0", name="ck_student_questions_message"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "answers",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("question_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("response_state", response_state, nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("escalation_destination_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("latency_ms >= 0", name="ck_answers_latency_nonnegative"),
        sa.ForeignKeyConstraint(
            ["escalation_destination_id"], ["escalation_destinations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["question_id"], ["student_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id"),
    )

    op.create_table(
        "citations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("answer_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("source_chunk_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("display_title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("locator", sa.Text(), nullable=True),
        sa.Column("review_context", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["answer_id"], ["answers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_chunk_id"], ["source_chunks.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("answer_id", "source_chunk_id", name="uq_citations_answer_chunk"),
    )
    op.create_index("ix_citations_source_chunk_id", "citations", ["source_chunk_id"], unique=False)

    op.create_table(
        "source_escalations",
        sa.Column("source_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("escalation_destination_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["escalation_destination_id"], ["escalation_destinations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["source_id"], ["approved_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("source_id", "escalation_destination_id"),
    )


def downgrade() -> None:
    op.drop_table("source_escalations")
    op.drop_index("ix_citations_source_chunk_id", table_name="citations")
    op.drop_table("citations")
    op.drop_table("answers")
    op.drop_table("student_questions")
    op.drop_index("ix_ingestion_jobs_source_version_id", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    op.drop_index("ix_source_chunks_source_version_id", table_name="source_chunks")
    op.drop_index("ix_source_chunks_source_id", table_name="source_chunks")
    op.drop_table("source_chunks")
    op.drop_index("uq_source_versions_one_active_per_source", table_name="source_versions")
    op.drop_index("ix_source_versions_source_id", table_name="source_versions")
    op.drop_table("source_versions")
    op.drop_table("escalation_destinations")
    op.drop_table("approved_sources")
    for enum_name in (
        "response_state",
        "ingestion_job_status",
        "campus",
        "source_activation_status",
        "extraction_status",
        "source_status",
        "source_type",
    ):
        op.execute(f"DROP TYPE {enum_name}")
