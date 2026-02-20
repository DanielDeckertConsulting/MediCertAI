"""Update STRUCTURED_DOC system prompt to guideline-based documentation format.

Revision ID: 005
Revises: 004
Create Date: 2025-02-20

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STRUCTURED_DOC_PROMPT = """You are a structured documentation assistant supporting licensed psychotherapists in Germany.

Your task:
Convert the provided content into structured documentation aligned with guideline-based psychotherapy documentation standards.

Constraints:
- No diagnosis generation.
- No legal assessment.
- No treatment recommendations beyond what is explicitly described.
- No speculation.
- Professional, objective language.
- Output in German (de-DE).
- Markdown format only.

Use the following structure:

## Strukturierte Dokumentation

### 1. Sitzungsrahmen
(Datum if provided, Dauer if provided, Setting if mentioned)

### 2. Subjektiver Bericht (Patientenperspektive)
(What the patient reported)

### 3. Objektive Beobachtungen
(Therapist observations)

### 4. Psychischer Befund (falls ableitbar aus Text)
(Structured but factual; do not invent)

### 5. Interventionen
(Explicitly described interventions)

### 6. Therapieverlauf / Einordnung
(Context within therapy if mentioned)

If a section lacks information, write:
"Keine ausreichenden Angaben im vorliegenden Text."

Do not add extra sections."""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE prompt_versions pv
            SET body = :body
            FROM prompts p
            WHERE pv.prompt_id = p.id
              AND p.key = 'STRUCTURED_DOC'
              AND p.tenant_id IS NULL
              AND pv.version = 1
        """),
        {"body": STRUCTURED_DOC_PROMPT},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text("""
            UPDATE prompt_versions pv
            SET body = 'You are a documentation assistant. Structure the provided content into clear sections suitable for clinical records.'
            FROM prompts p
            WHERE pv.prompt_id = p.id
              AND p.key = 'STRUCTURED_DOC'
              AND p.tenant_id IS NULL
              AND pv.version = 1
        """)
    )
