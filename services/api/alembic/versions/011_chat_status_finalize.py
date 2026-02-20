"""Add chats.status for Conversation Lock/Finalize mode.

Revision ID: 011
Revises: 010
Create Date: 2025-02-20

Adds status column (active|finalized) to support medico-legal documentation freeze.
Export (PDF/TXT) remains allowed when finalized.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chats",
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
    )
    op.create_index(
        "idx_chats_status",
        "chats",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_chats_status", table_name="chats")
    op.drop_column("chats", "status")
