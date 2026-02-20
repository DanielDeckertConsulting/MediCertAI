# ClinAI — Row-Level Security (RLS)

**Database:** PostgreSQL  
**Strategy:** Single DB, shared schema, RLS on tenant-scoped tables

## Session Variables

| Variable | Set By | Purpose |
|----------|--------|---------|
| `app.tenant_id` | Middleware | Tenant isolation for RLS |
| `app.user_id` | Middleware | Audit / optional checks |

Application sets via `SET LOCAL app.tenant_id = '<uuid>'` at request start.

## Tables with RLS

| Table | Policy |
|-------|--------|
| users | `tenant_id::text = current_setting('app.tenant_id', true)` |
| prompts | `tenant_id IS NULL OR tenant_id::text = current_setting(...)` (global + tenant) |
| audit_logs | `tenant_id::text = current_setting('app.tenant_id', true)` |
| usage_records | `tenant_id::text = current_setting('app.tenant_id', true)` |
| folders | `tenant_id::text = current_setting('app.tenant_id', true)` |
| chats | `tenant_id::text = current_setting('app.tenant_id', true)` |
| chat_messages | tenant + chat ownership join |
| llm_audit_logs | `tenant_id::text = current_setting('app.tenant_id', true)` |
| domain_events | `tenant_id::text = current_setting('app.tenant_id', true)` |
| ai_responses | `tenant_id::text = current_setting('app.tenant_id', true)` |
| structured_session_documents | `tenant_id::text = current_setting('app.tenant_id', true)` |
| intervention_library | `tenant_id IS NULL OR tenant_id::text = current_setting(...)` (global + tenant) |

## Bypass

- Migrations and system jobs use superuser / `BYPASSRLS`
- Application role never bypasses RLS
