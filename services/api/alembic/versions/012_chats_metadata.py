"""Add chats.metadata for conversation-level settings (e.g. safe_mode).

Revision ID: 012
Revises: 011
Create Date: 2025-02-20

Additive, backwards compatible. No PII in metadata.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chats",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chats", "metadata")
