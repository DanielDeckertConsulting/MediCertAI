"""AI Response Rendering Service. Parses, sanitizes, stores AI markdown."""
from uuid import UUID, uuid4
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.markdown_sanitizer import sanitize_markdown
from app.services.block_extractor import extract_blocks
from app.services.event_store import append_event


class AIRenderingService:
    """Processes AI markdown into structured blocks; emits events."""

    def __init__(self, session: AsyncSession, tenant_id: UUID, user_id: str):
        self.session = session
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def process_markdown(
        self,
        raw_markdown: str,
        entity_type: str,
        entity_id: str,
        model: str = "gpt-4",
        confidence: float = 1.0,
    ) -> dict:
        """
        Sanitize, extract blocks, store event + ai_response.
        Returns { id, structured_blocks, confidence, needs_review, version }.
        On sanitization failure: emits AI_RENDER_SANITIZATION_FAILED, raises.
        """
        sanitized_result = sanitize_markdown(raw_markdown)
        if sanitized_result.failed:
            await append_event(
                self.session,
                self.tenant_id,
                actor="system",
                entity_type=entity_type,
                entity_id=entity_id,
                event_type="ai_response.sanitization_failed",
                payload={"reason": sanitized_result.reason or "Sanitization failed"},
                source="ai-rendering-service",
            )
            raise ValueError(sanitized_result.reason or "Sanitization failed")

        blocks = extract_blocks(sanitized_result.sanitized)

        # Get next version for this entity
        version_result = await self.session.execute(
            text("""
                SELECT COALESCE(MAX(version), 0) + 1
                FROM ai_responses
                WHERE tenant_id = :tenant_id AND entity_id = :entity_id
            """),
            {"tenant_id": str(self.tenant_id), "entity_id": entity_id},
        )
        version = version_result.scalar() or 1

        response_id = uuid4()
        blocks_json = json.dumps(blocks)

        await self.session.execute(
            text("""
                INSERT INTO ai_responses
                (id, tenant_id, entity_type, entity_id, raw_markdown, structured_blocks, model, confidence, version)
                VALUES (:id, :tenant_id, :entity_type, :entity_id, :raw_markdown, CAST(:structured_blocks AS jsonb), :model, :confidence, :version)
            """),
            {
                "id": str(response_id),
                "tenant_id": str(self.tenant_id),
                "entity_type": entity_type,
                "entity_id": entity_id,
                "raw_markdown": sanitized_result.sanitized,
                "structured_blocks": blocks_json,
                "model": model,
                "confidence": confidence,
                "version": version,
            },
        )

        await append_event(
            self.session,
            self.tenant_id,
            actor="ai_model",
            entity_type=entity_type,
            entity_id=entity_id,
            event_type="ai_response.created",
            payload={
                "raw_markdown": sanitized_result.sanitized,
                "structured_blocks": blocks,
                "model": model,
                "confidence": confidence,
                "version": version,
                "response_id": str(response_id),
            },
            source="ai-rendering-service",
            confidence=confidence,
            model=model,
        )

        needs_review = confidence < settings.ai_confidence_threshold
        return {
            "id": str(response_id),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "structured_blocks": blocks,
            "model": model,
            "confidence": confidence,
            "version": version,
            "needs_review": needs_review,
        }
