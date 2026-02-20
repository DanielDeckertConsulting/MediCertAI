# Admin KPIs and Audit Logs Flow

**Date:** 2025-02-20

## Data flow

```mermaid
flowchart TB
    subgraph Client["Frontend Admin"]
        AdminPage[Admin Page]
        KPITab[KPIs Tab]
        LogsTab[Logs Tab]
    end

    subgraph API["Backend API /admin"]
        KPIEndpoints["/admin/kpis/*"]
        AuditEndpoint["/admin/audit-logs"]
    end

    subgraph DB["PostgreSQL"]
        UsageRecords[(usage_records)]
        AuditLogs[(audit_logs)]
        Chats[(chats)]
    end

    subgraph WritePath["Write Path (no content)"]
        ChatStream[Chat Streaming]
        ExportEndpoint[Export /chats/{id}/export]
        ChatStream --> UsageRecords
        ChatStream --> AuditLogs
        ExportEndpoint --> AuditLogs
    end

    AdminPage --> KPITab
    AdminPage --> LogsTab
    KPITab --> KPIEndpoints
    LogsTab --> AuditEndpoint
    KPIEndpoints --> UsageRecords
    KPIEndpoints --> Chats
    AuditEndpoint --> AuditLogs
```

## Admin read sequence

```mermaid
sequenceDiagram
    participant U as User
    participant Admin as Admin Page
    participant API as Backend /admin
    participant DB as PostgreSQL

    U->>Admin: Open /admin (KPIs or Logs tab)
    Admin->>API: GET /admin/kpis/summary?scope=me
    API->>API: Resolve tenant_id, check role if scope=tenant
    API->>DB: Query usage_records, chats (RLS)
    DB-->>API: Aggregated data
    API-->>Admin: KPISummary JSON
    Admin-->>U: Render cards, charts

    U->>Admin: Switch to Logs, apply filters
    Admin->>API: GET /admin/audit-logs?q=...&scope=me
    API->>DB: Query audit_logs (RLS, filters)
    DB-->>API: Paginated rows
    API-->>Admin: AuditLogsResponse
    Admin-->>U: Render table
```

## Role-based scope

- **scope=me**: HCP User sees only own KPIs and own logs (filtered by actor_id/user_id)
- **scope=tenant**: HCP Admin sees tenant-wide KPIs and tenant-wide logs; requires admin role
