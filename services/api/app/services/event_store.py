"""Event store: append-only domain events. Tenant-isolated."""
import json
from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def append_event(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    event_id: UUID | None = None,
    actor: str,
    entity_type: str,
    entity_id: str,
    event_type: str,
    payload: dict,
    source: str = "praxis-pilot-api",
    schema_version: str = "1",
    confidence: float | None = None,
    model: str | None = None,
) -> UUID:
    """Append immutable domain event. Returns event_id."""
    eid = event_id or uuid4()
    now = datetime.now(timezone.utc)
    await session.execute(
        text("""
            INSERT INTO domain_events
            (tenant_id, event_id, timestamp, actor, entity_type, entity_id, event_type, payload, source, schema_version, confidence, model)
            VALUES (:tenant_id, :event_id, :timestamp, :actor, :entity_type, :entity_id, :event_type, CAST(:payload AS jsonb), :source, :schema_version, :confidence, :model)
        """),
        {
            "tenant_id": str(tenant_id),
            "event_id": str(eid),
            "timestamp": now,
            "actor": actor,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "event_type": event_type,
            "payload": json.dumps(payload),
            "source": source,
            "schema_version": schema_version,
            "confidence": confidence,
            "model": model,
        },
    )
    return eid
