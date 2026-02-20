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

## Folder & Chat events

| Event type | Description | Payload |
|------------|-------------|---------|
| `folder.created` | Folder created | folder_id, name |
| `folder.renamed` | Folder renamed (no PII in payload) | folder_id |
| `folder.deleted` | Folder deleted; chats moved to Unfiled | folder_id, chats_moved |
| `chat.folder_changed` | Chat assigned to different folder | chat_id, old_folder_id, new_folder_id |
| `chat.finalized` | Chat locked/finalized for medico-legal documentation | chat_id |

**Chat metadata (2026-02-20):** `chats.metadata` JSONB stores conversation-level settings (e.g. `safe_mode: boolean`). No domain event emitted; persisted via PATCH /chats. See [seq-safe-mode.mmd](../diagrams/flows/seq-safe-mode.mmd).

**Flow:** See [folder-management-flow.md](diagrams/folder-management-flow.md). See [chat-finalize-flow.md](diagrams/chat-finalize-flow.md) for Conversation Lock/Finalize.

---

## AI Response events (EPIC 13)

| Event type | Description | Payload |
|------------|-------------|---------|
| `ai_response.created` | AI markdown processed and stored | raw_markdown, structured_blocks, model, confidence, version |
| `ai_response.action_executed` | User executed AI-recommended action | command, label, confidence |
| `ai_response.sanitization_failed` | Markdown sanitization rejected unsafe content | reason |
| `ai_response.regenerated` | AI response regenerated; new version | previous_version, new_version |

**Flow:** See [ai-response-rendering-flow.mmd](diagrams/ai-response-rendering-flow.mmd).

---

## Storage

Events are stored in `domain_events` (append-only, tenant-isolated).  
AI responses are materialized in `ai_responses` (read model).

---

## Audit (Admin Logs, 2025-02-20)

### audit_logs (extended)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| tenant_id | UUID | FK → tenants |
| actor_id | TEXT | Opaque user/actor id |
| action | TEXT | e.g. `folder.deleted`, `chat_message_sent` |
| entity_type | TEXT | Nullable (extended 2025-02-20) |
| entity_id | UUID | Nullable |
| metadata | JSONB | No PII, no prompt/response content |
| ts | TIMESTAMPTZ | Default now() |
| assist_mode | TEXT | Nullable, for LLM actions |
| model_name | TEXT | Nullable |
| model_version | TEXT | Nullable |
| input_tokens | INT | Nullable, default 0 |
| output_tokens | INT | Nullable, default 0 |

**Actions:** `folder.deleted` (entity_type=folder), `chat_message_sent` (entity_type=chat_message; used for per-chat token aggregation in GET /chats/{id} → [chat-context-banner-flow.md](diagrams/chat-context-banner-flow.md)), `export_requested` (entity_type=chat, metadata: `{ format: "txt"|"pdf" }` only; no content), `cross_case_summary_generated` (entity_type=case_summary, metadata: conversation_count, conversation_ids; no summary content). Flow: [export-chat-flow.md](diagrams/export-chat-flow.md), [case-summary-flow.md](diagrams/case-summary-flow.md).

### usage_records

KPI aggregation. No PII, no prompt/response content.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, default uuid_generate_v4() |
| tenant_id | UUID | FK → tenants, NOT NULL |
| user_id | TEXT | Opaque actor id, NOT NULL |
| ts | TIMESTAMPTZ | Default now() |
| assist_mode | TEXT | Nullable |
| model_name | TEXT | NOT NULL, default 'gpt-4' |
| model_version | TEXT | Nullable |
| input_tokens | INT | NOT NULL, default 0 |
| output_tokens | INT | NOT NULL, default 0 |
| status | TEXT | Nullable (success/error) |
| latency_ms | INT | Nullable |

**Indexes:** (tenant_id, ts), (tenant_id, user_id, ts).
