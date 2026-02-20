"""Case summary across multiple conversations. Draft support only, no diagnosis, no treatment recommendation."""
import json
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.azure_openai import chat_completion
from app.services.prompt_injection import security_header

# Compliance: internal prompt, no diagnosis wording, no treatment recommendation
CASE_SUMMARY_SYSTEM_PROMPT = """Du bist ein Assistent zur Dokumentations-Unterstützung in der psychotherapeutischen Praxis.

AUFGABE: Erstelle eine strukturierte Fallzusammenfassung über mehrere Gespräche hinweg.

WICHTIGE REGELN:
- Keine Diagnose. Keine ICD/DSM-Klassifikation. Keine Behandlungsempfehlung.
- Nur deskriptive Zusammenfassung, Trends und dokumentierter Verlauf.
- Formuliere vorsichtig: "laut Protokoll", "dokumentiert", "berichtet".
- Keine absoluten Aussagen oder Spekulationen.

Antworte ausschließlich als gültiges JSON mit exakt diesen Feldern (deutsch):
{
  "case_summary": "Kurze Gesamtübersicht der ausgewählten Gespräche (2-4 Sätze).",
  "trends": ["Liste nicht-diagnostischer Beobachtungen, z.B. Themenverläufe, wiederkehrende Motive."],
  "treatment_evolution": "Überblick über den dokumentierten Verlauf (keine Empfehlung)."
}
"""

# Max conversations and content to avoid token overflow
MAX_CONVERSATIONS = 20
MAX_CHARS_PER_CONVERSATION = 8000


async def fetch_messages_for_chats(
    session: AsyncSession,
    chat_ids: list[UUID],
    tenant_id: UUID,
    owner_user_id: UUID,
) -> list[tuple[str, str, list[tuple[str, str, str]]]]:
    """
    Fetch chat title and messages for each chat. Returns [(chat_id, title, [(role, content, created_at)])].
    Only chats owned by user in tenant.
    """
    result: list[tuple[str, str, list[tuple[str, str, str]]]] = []
    for cid in chat_ids:
        chat_row = await session.execute(
            text("""
                SELECT id, title FROM chats
                WHERE id = :cid AND tenant_id = :tid AND owner_user_id = :oid
            """),
            {"cid": str(cid), "tid": str(tenant_id), "oid": str(owner_user_id)},
        )
        row = chat_row.fetchone()
        if not row:
            continue
        chat_id, title = str(row[0]), row[1] or "Unbenannt"

        msgs = await session.execute(
            text("""
                SELECT role, content, created_at
                FROM chat_messages
                WHERE chat_id = :cid AND role != 'system'
                ORDER BY created_at ASC
            """),
            {"cid": str(cid)},
        )
        msg_list = [
            (m[0], m[1] or "", m[2].isoformat() if m[2] else "")
            for m in msgs.fetchall()
        ]
        result.append((chat_id, title, msg_list))
    return result


def _build_user_message(chats_data: list[tuple[str, str, list[tuple[str, str, str]]]]) -> str:
    """Build user message from chat data. Truncate per-conversation if needed."""
    parts = []
    for chat_id, title, messages in chats_data:
        block = [f"## Chat: {title} (ID: {chat_id})\n"]
        total = 0
        for role, content, created_at in messages:
            seg = f"[{created_at}] {role}: {content}\n"
            if total + len(seg) > MAX_CHARS_PER_CONVERSATION:
                seg = seg[: MAX_CHARS_PER_CONVERSATION - total - 20] + "\n[... gekürzt]\n"
                block.append(seg)
                break
            block.append(seg)
            total += len(seg)
        parts.append("".join(block))
    return "\n\n---\n\n".join(parts)


def _parse_summary_response(raw: str) -> dict:
    """Parse LLM JSON response. Fallback to safe structure on parse error."""
    raw = raw.strip()
    # Extract JSON if wrapped in markdown
    if "```" in raw:
        start = raw.find("```")
        if start >= 0:
            raw = raw[start:]
            if raw.startswith("```json"):
                raw = raw[7:]
            elif raw.startswith("```"):
                raw = raw[3:]
            end = raw.find("```")
            if end >= 0:
                raw = raw[:end]
    try:
        out = json.loads(raw)
        if not isinstance(out, dict):
            return {"case_summary": str(out), "trends": [], "treatment_evolution": ""}
        return {
            "case_summary": out.get("case_summary", ""),
            "trends": out.get("trends", []) if isinstance(out.get("trends"), list) else [],
            "treatment_evolution": out.get("treatment_evolution", ""),
        }
    except json.JSONDecodeError:
        return {
            "case_summary": raw[:2000] if raw else "Zusammenfassung konnte nicht strukturiert werden.",
            "trends": [],
            "treatment_evolution": "",
        }


async def generate_case_summary(
    session: AsyncSession,
    chat_ids: list[UUID],
    tenant_id: UUID,
    owner_user_id: UUID,
) -> tuple[dict, dict]:
    """
    Generate case summary for given chats. Returns (structured_summary, usage).
    All chats must belong to same tenant and user.
    """
    if len(chat_ids) > MAX_CONVERSATIONS:
        raise ValueError(f"Max {MAX_CONVERSATIONS} conversations allowed")

    chats_data = await fetch_messages_for_chats(session, chat_ids, tenant_id, owner_user_id)
    if not chats_data:
        raise ValueError("No accessible conversations found")

    user_msg = _build_user_message(chats_data)
    system = security_header() + CASE_SUMMARY_SYSTEM_PROMPT

    content, usage = await chat_completion(
        system_prompt=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    summary = _parse_summary_response(content)
    return (summary, usage)
