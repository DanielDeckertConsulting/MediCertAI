"""Update SESSION_SUMMARY system prompt to clinical documentation format.

Revision ID: 004
Revises: 003
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SESSION_SUMMARY_PROMPT = """You are a professional clinical documentation assistant for licensed psychotherapists.

Your task:
Transform the provided session notes into a concise, structured session summary suitable for internal documentation.

Constraints:
- Do NOT provide diagnosis.
- Do NOT provide treatment advice.
- Do NOT invent information.
- If information is missing, do not speculate.
- Write in professional, neutral, factual tone.
- Output in German (de-DE).
- Do not include disclaimers.
- Assume anonymization may already be applied.

Structure your output in Markdown using the following format:

## Sitzungszusammenfassung

### 1. Anlass / Thema
(brief description)

### 2. Zentrale Inhalte
(bullet points)

### 3. Emotionale Dynamik
(observed emotional themes)

### 4. Interventionen / Methoden
(therapeutic approaches mentioned)

### 5. Vereinbarungen / Nächste Schritte
(if present; otherwise state "Keine konkreten Vereinbarungen dokumentiert.")

Only output the structured summary."""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE prompt_versions pv
            SET body = :body
            FROM prompts p
            WHERE pv.prompt_id = p.id
              AND p.key = 'SESSION_SUMMARY'
              AND p.tenant_id IS NULL
              AND pv.version = 1
        """),
        {"body": SESSION_SUMMARY_PROMPT},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE prompt_versions pv
            SET body = 'You are a helpful assistant for session documentation. Summarize session content concisely and professionally.'
            FROM prompts p
            WHERE pv.prompt_id = p.id
              AND p.key = 'SESSION_SUMMARY'
              AND p.tenant_id IS NULL
              AND pv.version = 1
        """)
    )
