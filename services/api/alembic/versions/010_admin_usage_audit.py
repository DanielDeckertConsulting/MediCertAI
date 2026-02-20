"""Add usage_records, extend audit_logs, indexes for Admin KPIs and audit logs.

Revision ID: 010
Revises: 009
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create usage_records for KPI aggregation
    op.create_table(
        "usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("assist_mode", sa.Text(), nullable=True),
        sa.Column("model_name", sa.Text(), nullable=False, server_default="gpt-4"),
        sa.Column("model_version", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_usage_records_tenant_ts", "usage_records", ["tenant_id", "ts"], unique=False)
    op.create_index("idx_usage_records_tenant_user_ts", "usage_records", ["tenant_id", "user_id", "ts"], unique=False)

    # RLS on usage_records
    op.execute("ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_usage_records ON usage_records
        USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)

    # 2. Extend audit_logs with LLM fields (nullable for existing rows)
    op.add_column("audit_logs", sa.Column("assist_mode", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("model_name", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("model_version", sa.Text(), nullable=True))
    op.add_column("audit_logs", sa.Column("input_tokens", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("audit_logs", sa.Column("output_tokens", sa.Integer(), nullable=True, server_default="0"))
    op.alter_column(
        "audit_logs",
        "entity_type",
        existing_type=sa.String(50),
        nullable=True,
    )

    # 3. Indexes for audit_logs queries
    op.create_index("idx_audit_logs_tenant_actor_ts", "audit_logs", ["tenant_id", "actor_id", "ts"], unique=False)

    # 4. Index for chats-created KPI
    op.create_index("idx_chats_tenant_created_at", "chats", ["tenant_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_chats_tenant_created_at", table_name="chats")
    op.drop_index("idx_audit_logs_tenant_actor_ts", table_name="audit_logs")
    op.alter_column(
        "audit_logs",
        "entity_type",
        existing_type=sa.String(50),
        nullable=False,
    )
    op.drop_column("audit_logs", "output_tokens")
    op.drop_column("audit_logs", "input_tokens")
    op.drop_column("audit_logs", "model_version")
    op.drop_column("audit_logs", "model_name")
    op.drop_column("audit_logs", "assist_mode")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_usage_records ON usage_records")
    op.execute("ALTER TABLE usage_records DISABLE ROW LEVEL SECURITY")
    op.drop_index("idx_usage_records_tenant_user_ts", table_name="usage_records")
    op.drop_index("idx_usage_records_tenant_ts", table_name="usage_records")
    op.drop_table("usage_records")
