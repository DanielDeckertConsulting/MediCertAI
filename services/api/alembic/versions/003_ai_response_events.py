"""Add domain_events and ai_responses for EPIC 13 AI Response Rendering Engine.

Revision ID: 003
Revises: 002
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "domain_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("schema_version", sa.String(20), nullable=False, server_default="1"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_domain_events_tenant_id", "domain_events", ["tenant_id"], unique=False)
    op.create_index("ix_domain_events_entity", "domain_events", ["entity_type", "entity_id"], unique=False)
    op.create_index("ix_domain_events_timestamp", "domain_events", ["timestamp"], unique=False)
    op.create_index("ix_domain_events_event_id", "domain_events", ["event_id"], unique=True)

    op.create_table(
        "ai_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("raw_markdown", sa.Text(), nullable=False),
        sa.Column("structured_blocks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_responses_entity_id", "ai_responses", ["entity_id"], unique=False)
    op.create_index("ix_ai_responses_created_at", "ai_responses", ["created_at"], unique=False)
    op.create_index("idx_ai_responses_entity_version", "ai_responses", ["entity_id", "version"], unique=False)

    op.execute("ALTER TABLE domain_events ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_domain_events ON domain_events
        USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)
    op.execute("ALTER TABLE ai_responses ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_ai_responses ON ai_responses
        USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_ai_responses ON ai_responses")
    op.execute("ALTER TABLE ai_responses DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_domain_events ON domain_events")
    op.execute("ALTER TABLE domain_events DISABLE ROW LEVEL SECURITY")
    op.drop_table("ai_responses")
    op.drop_table("domain_events")
