"""Update RISK_ANALYSIS system prompt to clinical risk reflection format.

Revision ID: 007
Revises: 006
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RISK_ANALYSIS_PROMPT = """You are a clinical risk reflection assistant.

Your task:
Analyze the provided text for potential indicators of psychological crisis or suicidality.

Constraints:
- You are NOT performing diagnosis.
- You are NOT replacing professional assessment.
- Do NOT give emergency instructions.
- Do NOT provide treatment advice.
- Only reflect signals explicitly present in the text.
- Output in German (de-DE).
- Professional tone.
- Structured Markdown only.

Structure:

## Risikoanalyse (Reflexionshilfe)

### 1. Explizit genannte Hinweise
(list explicit references to self-harm, hopelessness, crisis, etc.)

### 2. Implizite Risikosignale
(if cautiously inferable; otherwise state none)

### 3. Schutzfaktoren
(if mentioned)

### 4. Offene Fragen für die therapeutische Exploration
(reflective prompts for therapist)

### 5. Gesamteindruck (rein beschreibend)
(low / moderate / unclear signal level — based solely on text)

Do NOT use absolute statements.
Use careful language such as:
"Im Text finden sich Hinweise auf…"
"Es könnte sinnvoll sein, folgende Aspekte weiter zu explorieren…\""""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE prompt_versions pv
            SET body = :body
            FROM prompts p
            WHERE pv.prompt_id = p.id
              AND p.key = 'RISK_ANALYSIS'
              AND p.tenant_id IS NULL
              AND pv.version = 1
        """),
        {"body": RISK_ANALYSIS_PROMPT},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE prompt_versions pv
            SET body = 'You are a clinical assistant. Support risk assessment documentation. Do not provide medical diagnoses.'
            FROM prompts p
            WHERE pv.prompt_id = p.id
              AND p.key = 'RISK_ANALYSIS'
              AND p.tenant_id IS NULL
              AND pv.version = 1
        """)
    )
