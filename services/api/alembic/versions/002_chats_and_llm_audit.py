"""Add chats, chat_messages, llm_audit_logs for Phase 1.1 Chat Vertical Slice.

Revision ID: 002
Revises: 001
Create Date: 2025-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Message role enum for chat_messages
    role_enum = postgresql.ENUM("user", "assistant", "system", name="chat_message_role")
    role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False, server_default="New chat"),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chats_tenant_id", "chats", ["tenant_id"], unique=False)
    op.create_index("ix_chats_owner_user_id", "chats", ["owner_user_id"], unique=False)
    op.create_index("ix_chats_updated_at", "chats", ["updated_at"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", postgresql.ENUM("user", "assistant", "system", name="chat_message_role", create_type=False), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_tenant_id", "chat_messages", ["tenant_id"], unique=False)
    op.create_index("ix_chat_messages_chat_id", "chat_messages", ["chat_id"], unique=False)
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"], unique=False)

    op.create_table(
        "llm_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("assist_mode_key", sa.String(100), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("token_usage_prompt", sa.Integer(), nullable=True),
        sa.Column("token_usage_completion", sa.Integer(), nullable=True),
        sa.Column("correlation_id", sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_audit_logs_tenant_id", "llm_audit_logs", ["tenant_id"], unique=False)
    op.create_index("idx_llm_audit_tenant_ts", "llm_audit_logs", ["tenant_id", "timestamp"], unique=False)

    # RLS on chats
    op.execute("ALTER TABLE chats ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_chats ON chats
        USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)

    # RLS on chat_messages (tenant + chat ownership via join)
    op.execute("ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_chat_messages ON chat_messages
        USING (
            tenant_id::text = current_setting('app.tenant_id', true)
            AND EXISTS (
                SELECT 1 FROM chats c
                WHERE c.id = chat_messages.chat_id
                AND c.tenant_id::text = current_setting('app.tenant_id', true)
            )
        )
    """)

    # RLS on llm_audit_logs
    op.execute("ALTER TABLE llm_audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_llm_audit ON llm_audit_logs
        USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_llm_audit ON llm_audit_logs")
    op.execute("ALTER TABLE llm_audit_logs DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_chat_messages ON chat_messages")
    op.execute("ALTER TABLE chat_messages DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_chats ON chats")
    op.execute("ALTER TABLE chats DISABLE ROW LEVEL SECURITY")

    op.drop_table("llm_audit_logs")
    op.drop_table("chat_messages")
    op.drop_table("chats")

    role_enum = postgresql.ENUM("user", "assistant", "system", name="chat_message_role")
    role_enum.drop(op.get_bind(), checkfirst=True)
