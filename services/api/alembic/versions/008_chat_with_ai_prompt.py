"""Add CHAT_WITH_AI system prompt. General conversational default.

Revision ID: 008
Revises: 007
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CHAT_WITH_AI_PROMPT = """You are a helpful AI assistant. Support the user with their questions and tasks. Be professional, accurate, and concise. Respond in German (de-DE) unless the user asks in another language. Do not provide medical or psychological diagnoses or treatment advice."""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            INSERT INTO prompts (key, display_name, tenant_id)
            SELECT 'CHAT_WITH_AI', 'Chat with AI', NULL
            WHERE NOT EXISTS (SELECT 1 FROM prompts WHERE key = 'CHAT_WITH_AI' AND tenant_id IS NULL)
        """)
    )
    conn.execute(
        text("""
            INSERT INTO prompt_versions (prompt_id, version, body)
            SELECT p.id, 1, :body
            FROM prompts p
            WHERE p.key = 'CHAT_WITH_AI' AND p.tenant_id IS NULL
              AND NOT EXISTS (SELECT 1 FROM prompt_versions pv WHERE pv.prompt_id = p.id AND pv.version = 1)
        """),
        {"body": CHAT_WITH_AI_PROMPT},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            DELETE FROM prompt_versions
            WHERE prompt_id IN (SELECT id FROM prompts WHERE key = 'CHAT_WITH_AI' AND tenant_id IS NULL)
        """)
    )
    conn.execute(
        text("DELETE FROM prompts WHERE key = 'CHAT_WITH_AI' AND tenant_id IS NULL")
    )
