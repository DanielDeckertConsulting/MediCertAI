"""Server-side prompt registry. Resolves assist_mode_key to system prompt."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.prompt_injection import security_header

ASSIST_KEYS = [
    "CHAT_WITH_AI",
    "SESSION_SUMMARY",
    "STRUCTURED_DOC",
    "THERAPY_PLAN",
    "RISK_ANALYSIS",
    "CASE_REFLECTION",
]


async def get_system_prompt(session: AsyncSession, assist_mode_key: str) -> str | None:
    """
    Resolve active system prompt for assist mode. Global prompts (tenant_id NULL) only for MVP.
    Returns None if key not found.
    """
    if assist_mode_key not in ASSIST_KEYS:
        return None

    result = await session.execute(
        text("""
            SELECT pv.body
            FROM prompts p
            JOIN prompt_versions pv ON pv.prompt_id = p.id
            WHERE p.key = :key AND p.tenant_id IS NULL
            ORDER BY pv.version DESC
            LIMIT 1
        """),
        {"key": assist_mode_key},
    )
    row = result.fetchone()
    if not row or not row[0]:
        return None
    return security_header() + row[0]
