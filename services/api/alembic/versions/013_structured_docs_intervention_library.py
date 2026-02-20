"""Add structured_session_documents and intervention_library for EPIC 14.

Revision ID: 013
Revises: 012
Create Date: 2026-02-20

Structured Session Documentation (1.1) and Intervention Suggestion Library (1.2).
RLS enforced per MULTI_TENANCY_DESIGN.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "structured_session_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_structured_session_documents_tenant_id",
        "structured_session_documents",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_structured_session_documents_conversation_id",
        "structured_session_documents",
        ["conversation_id"],
        unique=False,
    )

    op.create_table(
        "intervention_library",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_level", sa.Text(), nullable=True),
        sa.Column("references", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intervention_library_tenant_id", "intervention_library", ["tenant_id"], unique=False)
    op.create_index("ix_intervention_library_category", "intervention_library", ["category"], unique=False)

    op.execute("ALTER TABLE structured_session_documents ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_structured_docs ON structured_session_documents
        USING (tenant_id::text = current_setting('app.tenant_id', true))
    """)

    op.execute("ALTER TABLE intervention_library ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_intervention_library ON intervention_library
        USING (tenant_id IS NULL OR tenant_id::text = COALESCE(current_setting('app.tenant_id', true), ''))
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_intervention_library ON intervention_library")
    op.execute("ALTER TABLE intervention_library DISABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_structured_docs ON structured_session_documents")
    op.execute("ALTER TABLE structured_session_documents DISABLE ROW LEVEL SECURITY")
    op.drop_table("intervention_library")
    op.drop_table("structured_session_documents")
