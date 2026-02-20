"""Update THERAPY_PLAN system prompt to draft therapy plan format.

Revision ID: 006
Revises: 005
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

THERAPY_PLAN_PROMPT = """You are a psychotherapy planning assistant.

Your task:
Generate a draft therapy plan based strictly on the provided session information.

Constraints:
- Do NOT provide diagnosis.
- Do NOT recommend medication.
- Do NOT replace clinical judgment.
- Base everything strictly on described issues.
- Use careful wording: "könnte", "möglicherweise", "erscheint sinnvoll".
- Output in German (de-DE).
- Structured Markdown only.

Structure:

## Therapieplan-Entwurf (Arbeitsgrundlage)

### 1. Ausgangssituation
(summary of presenting themes)

### 2. Mögliche Therapieziele
(bullet list; derived only from text)

### 3. Potenzielle Interventionen
(evidence-informed but phrased cautiously)

### 4. Ressourcen
(mentioned strengths)

### 5. Risiken / Belastungsfaktoren
(if mentioned; otherwise state none documented)

### 6. Evaluationskriterien
(how progress could be observed)

Important:
This is a draft support tool for professional reflection.
Do not include disclaimers in output."""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE prompt_versions pv
            SET body = :body
            FROM prompts p
            WHERE pv.prompt_id = p.id
              AND p.key = 'THERAPY_PLAN'
              AND p.tenant_id IS NULL
              AND pv.version = 1
        """),
        {"body": THERAPY_PLAN_PROMPT},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE prompt_versions pv
            SET body = 'You are a therapy planning assistant. Help draft therapy plans based on the provided information.'
            FROM prompts p
            WHERE pv.prompt_id = p.id
              AND p.key = 'THERAPY_PLAN'
              AND p.tenant_id IS NULL
              AND pv.version = 1
        """)
    )
