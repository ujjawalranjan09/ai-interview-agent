"""Add performance indexes for Phase 10

Revision ID: 005
Revises: 004
Create Date: 2026-06-20

"""
from typing import Sequence, Union

from alembic import op


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_interviews_status_created", "interviews", ["status", "created_at"])
    op.create_index("ix_interviews_candidate_id", "interviews", ["candidate_id"])
    op.create_index("ix_questions_bank_id", "questions", ["bank_id"])
    op.create_index("ix_reports_interview_id", "reports", ["interview_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_interview_id")
    op.drop_index("ix_questions_bank_id")
    op.drop_index("ix_interviews_candidate_id")
    op.drop_index("ix_interviews_status_created")
