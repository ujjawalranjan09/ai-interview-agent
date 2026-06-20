"""Add Phase 8 tables: consent, availability, proctoring, plagiarism, branding

Revision ID: 003
Revises: 002
Create Date: 2026-06-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Consent / GDPR ---
    op.create_table(
        "consents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("consent_type", sa.String(64), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consents_user_id", "consents", ["user_id"])

    op.create_table(
        "data_retention_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("auto_delete", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "data_export_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_export_requests_user_id", "data_export_requests", ["user_id"])

    # --- Availability / Scheduling ---
    op.create_table(
        "availability_slots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_availability_slots_user_id", "availability_slots", ["user_id"])

    op.create_table(
        "scheduled_interviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("interviewer_id", sa.Uuid(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("status", sa.String(32), nullable=False, server_default="scheduled"),
        sa.Column("meet_link", sa.String(512), nullable=True),
        sa.Column("reminder_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reschedule_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["interviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scheduled_interviews_interview_id", "scheduled_interviews", ["interview_id"])

    # --- Proctoring ---
    op.create_table(
        "proctoring_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("flags_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proctoring_sessions_interview_id", "proctoring_sessions", ["interview_id"])

    op.create_table(
        "proctoring_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="info"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["session_id"], ["proctoring_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proctoring_events_session_id", "proctoring_events", ["session_id"])

    # --- Plagiarism ---
    op.create_table(
        "plagiarism_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("matched_with", sa.Uuid(), nullable=True),
        sa.Column("matched_source", sa.String(64), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["submission_id"], ["coding_submissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_with"], ["coding_submissions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plagiarism_checks_submission_id", "plagiarism_checks", ["submission_id"])

    op.create_table(
        "plagiarism_matches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("check_id", sa.Uuid(), nullable=False),
        sa.Column("matched_submission_id", sa.Uuid(), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("matched_lines", sa.JSON(), nullable=True),
        sa.Column("algorithm", sa.String(64), nullable=False, server_default="moss"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["check_id"], ["plagiarism_checks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_submission_id"], ["coding_submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plagiarism_matches_check_id", "plagiarism_matches", ["check_id"])

    # --- Branding ---
    op.create_table(
        "organization_branding",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("logo_url", sa.String(512), nullable=True),
        sa.Column("favicon_url", sa.String(512), nullable=True),
        sa.Column("primary_color", sa.String(7), nullable=True),
        sa.Column("secondary_color", sa.String(7), nullable=True),
        sa.Column("accent_color", sa.String(7), nullable=True),
        sa.Column("font_family", sa.String(128), nullable=True),
        sa.Column("custom_css", sa.Text(), nullable=True),
        sa.Column("custom_domain", sa.String(256), nullable=True),
        sa.Column("email_template", sa.Text(), nullable=True),
        sa.Column("portal_heading", sa.String(256), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("theme_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
        sa.UniqueConstraint("custom_domain"),
    )
    op.create_index("ix_organization_branding_organization_id", "organization_branding", ["organization_id"])


def downgrade() -> None:
    op.drop_table("organization_branding")
    op.drop_table("plagiarism_matches")
    op.drop_table("plagiarism_checks")
    op.drop_table("proctoring_events")
    op.drop_table("proctoring_sessions")
    op.drop_table("scheduled_interviews")
    op.drop_table("availability_slots")
    op.drop_table("data_export_requests")
    op.drop_table("data_retention_policies")
    op.drop_table("consents")
