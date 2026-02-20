"""Structured session documentation: CRUD and LLM-based conversion. No diagnosis, documentation only."""
import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.azure_openai import chat_completion
from app.services.event_store import append_event
from app.services.prompt_injection import security_header

# Schema for structured session document content (EPIC 14)
STRUCTURED_FIELDS = [
    "session_context",
    "presenting_symptoms",
    "resources",
    "interventions",
    "homework",
    "risk_assessment",
    "progress_evaluation",
]

STRUCTURED_DOC_TRANSFORMATION_SYSTEM = """Du bist ein Assistent zur strukturierten psychotherapeutischen Dokumentation.

AUFGABE: Extrahiere aus dem folgenden Gesprächsverlauf eine strukturierte Dokumentation. Erfinde keine Informationen. Wenn ein Feld im Gespräch nicht vorkommt, setze einen leeren String "".

WICHTIGE REGELN:
- Keine Diagnose. Keine ICD/DSM-Codes. Keine Behandlungsempfehlung.
- Nur dokumentieren, was im Gespräch erwähnt oder ableitbar ist.
- Keine Spekulation.

Antworte ausschließlich mit gültigem JSON, genau diese Felder (alle Strings):
{
  "session_context": "",
  "presenting_symptoms": "",
  "resources": "",
  "interventions": "",
  "homework": "",
  "risk_assessment": "",
  "progress_evaluation": ""
}
"""

MAX_MESSAGES_CHARS = 12000


def _empty_content() -> dict:
    return {f: "" for f in STRUCTURED_FIELDS}


def validate_structured_content(data: dict) -> dict:
    """Normalize and validate; return only allowed fields, empty string for missing."""
    out = _empty_content()
    if not isinstance(data, dict):
        return out
    for key in STRUCTURED_FIELDS:
        val = data.get(key)
        out[key] = str(val).strip() if val is not None else ""
    return out


def _build_conversation_text(messages: list[tuple[str, str, str]]) -> str:
    """Build single text from messages for LLM. Truncate if needed."""
    parts = []
    total = 0
    for role, content, created_at in messages:
        seg = f"[{created_at}] {role}: {content}\n"
        if total + len(seg) > MAX_MESSAGES_CHARS:
            seg = seg[: MAX_MESSAGES_CHARS - total - 20] + "\n[... gekürzt]\n"
            parts.append(seg)
            break
        parts.append(seg)
        total += len(seg)
    return "".join(parts)


def _parse_llm_json(raw: str) -> dict | None:
    """Parse LLM JSON response. Return None on failure."""
    raw = raw.strip()
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
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


async def get_by_conversation(
    session: AsyncSession,
    conversation_id: UUID,
    tenant_id: UUID,
    owner_user_id: UUID,
) -> dict | None:
    """Get latest structured document for conversation. Verify chat ownership via RLS/join."""
    r = await session.execute(
        text("""
            SELECT ssd.id, ssd.conversation_id, ssd.version, ssd.content, ssd.created_at, ssd.updated_at
            FROM structured_session_documents ssd
            JOIN chats c ON c.id = ssd.conversation_id AND c.tenant_id = ssd.tenant_id
            WHERE ssd.conversation_id = :cid AND ssd.tenant_id = :tid AND c.owner_user_id = :oid
            ORDER BY ssd.version DESC
            LIMIT 1
        """),
        {"cid": str(conversation_id), "tid": str(tenant_id), "oid": str(owner_user_id)},
    )
    row = r.fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "conversation_id": str(row[1]),
        "version": row[2],
        "content": row[3] or _empty_content(),
        "created_at": row[4].isoformat() if row[4] else "",
        "updated_at": row[5].isoformat() if row[5] else "",
    }


async def create_or_update(
    session: AsyncSession,
    conversation_id: UUID,
    tenant_id: UUID,
    owner_user_id: UUID,
    actor: str,
    content: dict,
    *,
    is_manual_create: bool = True,
) -> dict:
    """Create new or update latest structured document. Increment version on update. Emit events."""
    content = validate_structured_content(content)

    # Ensure chat exists and user owns it
    chat = await session.execute(
        text("""
            SELECT id FROM chats
            WHERE id = :cid AND tenant_id = :tid AND owner_user_id = :oid
        """),
        {"cid": str(conversation_id), "tid": str(tenant_id), "oid": str(owner_user_id)},
    )
    if not chat.fetchone():
        raise ValueError("Chat not found or access denied")

    # Check existing doc
    existing = await session.execute(
        text("""
            SELECT id, version FROM structured_session_documents
            WHERE conversation_id = :cid AND tenant_id = :tid
            ORDER BY version DESC LIMIT 1
        """),
        {"cid": str(conversation_id), "tid": str(tenant_id)},
    )
    row = existing.fetchone()
    if row:
        doc_id, version = row[0], row[1]
        new_version = version + 1
        await session.execute(
            text("""
                UPDATE structured_session_documents
                SET content = CAST(:content AS jsonb), version = :version, updated_at = now()
                WHERE id = :id
            """),
            {"content": json.dumps(content), "version": new_version, "id": str(doc_id)},
        )
        await append_event(
            session,
            tenant_id,
            actor=actor,
            entity_type="structured_document",
            entity_id=str(doc_id),
            event_type="structured_document.updated",
            payload={
                "document_id": str(doc_id),
                "conversation_id": str(conversation_id),
                "version": new_version,
            },
        )
        await append_event(
            session,
            tenant_id,
            actor=actor,
            entity_type="structured_document",
            entity_id=str(doc_id),
            event_type="structured_document.versioned",
            payload={
                "document_id": str(doc_id),
                "conversation_id": str(conversation_id),
                "version": new_version,
            },
        )
        r = await session.execute(
            text("SELECT id, conversation_id, version, content, created_at, updated_at FROM structured_session_documents WHERE id = :id"),
            {"id": str(doc_id)},
        )
        row = r.fetchone()
        return {
            "id": str(row[0]),
            "conversation_id": str(row[1]),
            "version": row[2],
            "content": row[3] or _empty_content(),
            "created_at": row[4].isoformat() if row[4] else "",
            "updated_at": row[5].isoformat() if row[5] else "",
        }
    else:
        doc_id = uuid4()
        await session.execute(
            text("""
                INSERT INTO structured_session_documents (id, tenant_id, conversation_id, version, content)
                VALUES (:id, :tenant_id, :conversation_id, 1, CAST(:content AS jsonb))
            """),
            {
                "id": str(doc_id),
                "tenant_id": str(tenant_id),
                "conversation_id": str(conversation_id),
                "content": json.dumps(content),
            },
        )
        await append_event(
            session,
            tenant_id,
            actor=actor,
            entity_type="structured_document",
            entity_id=str(doc_id),
            event_type="structured_document.created",
            payload={
                "document_id": str(doc_id),
                "conversation_id": str(conversation_id),
                "version": 1,
            },
        )
        r = await session.execute(
            text("SELECT id, conversation_id, version, content, created_at, updated_at FROM structured_session_documents WHERE id = :id"),
            {"id": str(doc_id)},
        )
        row = r.fetchone()
        return {
            "id": str(row[0]),
            "conversation_id": str(row[1]),
            "version": row[2],
            "content": row[3] or _empty_content(),
            "created_at": row[4].isoformat() if row[4] else "",
            "updated_at": row[5].isoformat() if row[5] else "",
        }


async def generate_from_conversation(
    session: AsyncSession,
    conversation_id: UUID,
    tenant_id: UUID,
    owner_user_id: UUID,
    actor: str,
) -> tuple[dict, dict]:
    """
    Fetch messages, call LLM, validate, store. Returns (document_out, usage).
    Emits structured_document.generated or structured_document.validation_failed.
    """
    msgs_result = await session.execute(
        text("""
            SELECT role, content, created_at
            FROM chat_messages cm
            JOIN chats c ON c.id = cm.chat_id AND c.tenant_id = cm.tenant_id
            WHERE cm.chat_id = :cid AND c.tenant_id = :tid AND c.owner_user_id = :oid
            AND cm.role != 'system'
            ORDER BY cm.created_at ASC, cm.id ASC
        """),
        {"cid": str(conversation_id), "tid": str(tenant_id), "oid": str(owner_user_id)},
    )
    messages = [(m[0], m[1] or "", m[2].isoformat() if m[2] else "") for m in msgs_result.fetchall()]
    if not messages:
        raise ValueError("No messages in conversation")

    user_content = _build_conversation_text(messages)
    system = security_header() + STRUCTURED_DOC_TRANSFORMATION_SYSTEM
    content, usage = await chat_completion(
        system_prompt=system,
        messages=[{"role": "user", "content": user_content}],
    )
    parsed = _parse_llm_json(content)
    if not parsed:
        await append_event(
            session,
            tenant_id,
            actor=actor,
            entity_type="structured_document",
            entity_id=str(conversation_id),
            event_type="structured_document.validation_failed",
            payload={"conversation_id": str(conversation_id), "reason": "invalid_json"},
        )
        raise ValueError("LLM output was not valid JSON")

    validated = validate_structured_content(parsed)
    doc = await create_or_update(
        session,
        conversation_id,
        tenant_id,
        owner_user_id,
        actor,
        validated,
        is_manual_create=False,
    )
    await append_event(
        session,
        tenant_id,
        actor=actor,
        entity_type="structured_document",
        entity_id=doc["id"],
        event_type="structured_document.generated",
        payload={
            "document_id": doc["id"],
            "conversation_id": str(conversation_id),
            "version": doc["version"],
        },
    )
    return (doc, usage)
