# Chat Export Flow (PDF / TXT)

**Date:** 2025-02-20

## Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as Backend API
    participant DB as Database

    U->>FE: Click Export → TXT or PDF
    FE->>API: GET /chats/{id}/export?format=txt|pdf
    API->>API: Resolve tenant_id, require_auth
    API->>DB: SELECT chats (RLS, owner check)
    alt Chat not found
        API-->>FE: 404
        FE-->>U: Error alert
    else Chat found
        API->>DB: SELECT chat_messages (ORDER BY created_at)
        API->>API: Check limits (max 2000 msgs, ~2MB)
        alt Limits exceeded
            API-->>FE: 413 Payload Too Large
            FE-->>U: Error alert
        else Within limits
            API->>DB: INSERT audit_logs (action=export_requested, metadata={format}, NO content)
            API->>API: Generate TXT or PDF
            API-->>FE: 200 + Content-Disposition attachment
            FE->>FE: blob → createObjectURL → download
            FE-->>U: File downloaded
        end
    end
```

## Compliance

- **Audit:** `export_requested` in `audit_logs` with `entity_type=chat`, `metadata.format=txt|pdf` only. No prompt/response content.
- **Generation:** In-request; no blob storage for MVP. File streamed directly.

## API

| Endpoint | Format | Response |
|----------|--------|----------|
| `GET /chats/{id}/export?format=txt` | Plain text | `text/plain; charset=utf-8` |
| `GET /chats/{id}/export?format=pdf` | PDF | `application/pdf` |
| `GET /chats/{id}/export.txt` | Legacy | Same as format=txt |
