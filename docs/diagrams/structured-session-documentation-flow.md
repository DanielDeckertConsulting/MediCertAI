# Structured Session Documentation Flow (EPIC 14)

**Date:** 2026-02-20

## Overview

- **1.1** Structured Session Templates: Chat / Structured view toggle; form with 7 optional fields; versioned documents.
- **1.2** Intervention Library: Evidence-informed, non-prescriptive suggestions; global + tenant entries.
- **1.3** Convert: Server-side LLM transforms conversation → structured JSON → validate → store.

---

## UI state flow (Chat page)

```mermaid
stateDiagram-v2
    [*] --> ChatView: Open chat
    ChatView --> StructuredView: Toggle "Struktur"
    StructuredView --> ChatView: Toggle "Chat"
    ChatView --> StructuredView: "In Struktur umwandeln" (after convert)
    note right of ChatView: Messages, input, assist mode
    note right of StructuredView: 7-field form, version, Save
    note right of ChatView: Interventionsideen panel (toggle)
```

---

## Sequence: Convert to Structured Documentation

```mermaid
sequenceDiagram
    participant U as User
    participant SPA as Frontend
    participant API as Backend
    participant DB as PostgreSQL
    participant LLM as Azure OpenAI

    U->>SPA: Click "In Struktur umwandeln"
    SPA->>API: POST /chats/{id}/structured-document/convert
    API->>API: Resolve tenant_id, user_id
    API->>DB: Fetch chat messages (RLS)
    DB-->>API: Messages
    API->>API: Build prompt (server-side only)
    API->>LLM: Chat completion (no diagnosis)
    LLM-->>API: JSON
    API->>API: Validate schema
    alt Invalid JSON
        API->>API: Emit structured_document.validation_failed
        API-->>SPA: 422
    else Valid
        API->>DB: INSERT/UPDATE structured_session_documents
        API->>DB: Append structured_document.generated
        API-->>SPA: document + usage
        SPA->>SPA: Switch to Structured view, refetch doc
    end
```

---

## Sequence: Manual create/update (Structured view)

```mermaid
sequenceDiagram
    participant U as User
    participant SPA as Frontend
    participant API as Backend
    participant DB as PostgreSQL

    U->>SPA: Toggle to Struktur, edit fields, click Speichern
    SPA->>API: PUT /chats/{id}/structured-document { content }
    API->>API: Validate tenant, chat ownership, not finalized
    API->>DB: Upsert structured_session_documents (version++)
    API->>DB: Append structured_document.updated / .versioned
    API-->>SPA: 200 { document }
    SPA->>SPA: Refetch doc, update form
```

---

## Sequence: Intervention panel

```mermaid
sequenceDiagram
    participant U as User
    participant SPA as Frontend
    participant API as Backend
    participant DB as PostgreSQL

    U->>SPA: Click "Interventionsideen"
    SPA->>API: GET /interventions
    API->>DB: SELECT (tenant_id IS NULL OR tenant_id = current)
    DB-->>API: Rows
    API-->>SPA: 200 [ { id, category, title, description, evidence_level } ]
    SPA-->>U: Drawer with disclaimer + list
```

---

## Data model

```mermaid
erDiagram
    tenants ||--o{ structured_session_documents : "tenant_id"
    chats ||--o{ structured_session_documents : "conversation_id"
    tenants ||--o{ intervention_library : "tenant_id nullable"

    structured_session_documents {
        uuid id PK
        uuid tenant_id FK
        uuid conversation_id FK
        int version
        jsonb content
        timestamptz created_at
        timestamptz updated_at
    }

    intervention_library {
        uuid id PK
        text category
        text title
        text description
        text evidence_level
        text[] references
        uuid tenant_id FK "NULL = global"
    }
```

- **RLS:** `structured_session_documents`: tenant_id = current. `intervention_library`: tenant_id IS NULL OR tenant_id = current.

---

## Events

| Event | When |
|-------|------|
| `structured_document.created` | First manual or generated doc for conversation |
| `structured_document.updated` | Content saved (same version row updated) |
| `structured_document.versioned` | New version saved |
| `structured_document.generated` | Convert flow succeeded |
| `structured_document.validation_failed` | LLM returned invalid JSON |
| `intervention_viewed` | User viewed intervention entry (no PII) |

---

## Related

- **Export:** PDF can include a "Strukturierte Dokumentation" section when a structured doc exists for the chat. See [export-chat-flow.md](export-chat-flow.md).
