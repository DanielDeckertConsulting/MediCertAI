# Case Summary (Cross-Conversation) Flow

Draft support only. No diagnosis. No treatment recommendation. No automatic storage.

```mermaid
sequenceDiagram
    participant U as User
    participant SPA as Frontend
    participant API as Backend API
    participant GW as Azure OpenAI
    participant DB as PostgreSQL

    U->>SPA: Select folder, click "Fallzusammenfassung generieren"
    SPA->>API: POST /cases/summary { conversation_ids }
    API->>API: Validate tenant + auth
    API->>DB: Fetch messages for each chat (tenant-isolated)
    API->>GW: Chat completion (case summary prompt)
    Note over API,GW: Prompt: no diagnosis, no treatment recommendation
    GW-->>API: Structured JSON (case_summary, trends, treatment_evolution)
    API->>DB: INSERT audit_logs (action: cross_case_summary_generated, metadata only)
    API-->>SPA: 200 { case_summary, trends, treatment_evolution }
    SPA-->>U: Modal with summary + disclaimer
```

**Related flow:** Triggered from [Folder Management](folder-management-flow.md) — user selects folder, then clicks "Fallzusammenfassung generieren".

## Compliance

- **No automatic storage** of summary output unless user explicitly saves
- **No diagnosis** wording in prompt or output
- **No treatment recommendation** in prompt or output
- **Disclaimer** in UI: "KI-gestützte Zusammenfassung – keine diagnostische Entscheidung."
- **Audit** metadata only (conversation_ids, count); no content in logs
