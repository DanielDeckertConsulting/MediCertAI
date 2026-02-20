# Conversation Lock / Finalize Flow

**Date:** 2025-02-20

Conversation Lock/Finalize mode freezes a chat for medico-legal documentation. No further modifications allowed; export (PDF/TXT) remains available.

## Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as Backend API
    participant DB as Database
    participant ES as Event Store

    Note over U,ES: Finalize Chat
    U->>FE: Click Lock / Finalize
    FE->>API: POST /chats/{id}/finalize
    API->>API: require_auth, resolve tenant
    API->>DB: SELECT status (RLS)
    alt Chat not found
        API-->>FE: 404
    else Already finalized
        API-->>FE: 409 Conflict
    else status = active
        API->>DB: UPDATE chats SET status = 'finalized'
        API->>ES: chat.finalized { chat_id }
        API->>FE: 200 { status: "finalized" }
        FE->>U: UI shows locked state

    Note over U,ES: Blocked Operations (status = finalized)
    U->>FE: Try patch / send message / delete
    FE->>API: PATCH or POST or DELETE
    API->>DB: SELECT status
    API-->>FE: 409 "Chat is finalized; no modifications allowed"
    FE->>U: Error message

    Note over U,ES: Export Still Allowed
    U->>FE: Export TXT/PDF
    FE->>API: GET /chats/{id}/export?format=txt|pdf
    API->>DB: SELECT chats, chat_messages (no status check)
    API->>FE: 200 + attachment
    FE->>U: File downloaded
```

## State Rules

| Chat status | PATCH / Send / Delete | Export |
|-------------|-----------------------|--------|
| active      | Allowed               | Allowed |
| finalized   | 409 Conflict          | Allowed |

## API

| Endpoint | Description |
|----------|-------------|
| `POST /chats/{id}/finalize` | Finalize chat. Returns 409 if already finalized. Emits `chat.finalized`. |

## Compliance

- **Event:** `chat.finalized` in domain_events (immutable, tenant-isolated).
- **Audit:** No separate audit_logs entry; event store suffices for rebuild.
- **GDPR:** Deletion of finalized chats blocked (409). Export for data subject access remains available.
