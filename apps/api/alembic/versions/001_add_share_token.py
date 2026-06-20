"""Add share_token to interviews

Revision ID: 001
Revises: 
Create Date: 2026-06-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interviews",
        sa.Column("share_token", sa.String(64), nullable=True, unique=True),
    )
    op.create_index("ix_interviews_share_token", "interviews", ["share_token"])


def downgrade() -> None:
    op.drop_index("ix_interviews_share_token", table_name="interviews")
    op.drop_column("interviews", "share_token")
