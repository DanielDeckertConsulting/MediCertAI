"""Add folders table, FK on chats.folder_id, RLS, index.

Revision ID: 009
Revises: 008
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_folders_tenant_name"),
    )
    op.create_index("ix_folders_tenant_id", "folders", ["tenant_id"], unique=False)

    # Add FK from chats.folder_id to folders (ON DELETE SET NULL)
    op.create_foreign_key(
        "fk_chats_folder_id_folders",
        "chats",
        "folders",
        ["folder_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Index for folder filtering
    op.create_index("ix_chats_tenant_folder", "chats", ["tenant_id", "folder_id"], unique=False)

    # RLS on folders
    op.execute("ALTER TABLE folders ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_folders ON folders
        USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_folders ON folders")
    op.execute("ALTER TABLE folders DISABLE ROW LEVEL SECURITY")

    op.drop_index("ix_chats_tenant_folder", table_name="chats")
    op.drop_constraint("fk_chats_folder_id_folders", "chats", type_="foreignkey")
    op.drop_table("folders")
