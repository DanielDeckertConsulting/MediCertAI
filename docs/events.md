# Domain Events (Event-Log-First)

**Version:** 1  
**Canonical schema:** `shared/events/schema.json`

---

## Event envelope (required fields)

Every domain event MUST include:

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | UUID | Unique event identifier |
| `timestamp` | ISO 8601 | Event time |
| `actor` | string | Initiator (user_id, system, ai_model) |
| `entity_type` | string | Affected entity type |
| `entity_id` | string | Affected entity ID |
| `event_type` | string | Event type (see catalog) |
| `payload` | object | Event payload |
| `source` | string | Origin service/context |
| `schema_version` | string | Schema version |

Optional: `confidence`, `model` (for AI events).

---

## AI Response events (EPIC 13)

| Event type | Description | Payload |
|------------|-------------|---------|
| `ai_response.created` | AI markdown processed and stored | raw_markdown, structured_blocks, model, confidence, version |
| `ai_response.action_executed` | User executed AI-recommended action | command, label, confidence |
| `ai_response.sanitization_failed` | Markdown sanitization rejected unsafe content | reason |
| `ai_response.regenerated` | AI response regenerated; new version | previous_version, new_version |

---

## Storage

Events are stored in `domain_events` (append-only, tenant-isolated).  
AI responses are materialized in `ai_responses` (read model).
