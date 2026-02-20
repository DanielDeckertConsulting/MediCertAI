# ClinAI MVP — Security Baseline

**Version:** 0.1  
**Date:** 2025-02-19

---

## 1. Key Vault Usage

| Secret | Purpose | Access |
|--------|---------|--------|
| PostgreSQL connection string | DB access | Backend (Managed Identity) |
| Azure OpenAI API key | LLM calls | Backend (Managed Identity) |
| B2C client secret | Token validation | Backend (Managed Identity) |
| Optional: signing keys | If custom JWT | Backend |

- All secrets in Key Vault; none in app config or environment variables
- App Service uses Managed Identity to read Key Vault
- No secrets in code, containers, or logs

---

## 2. Secret Rotation Strategy

| Secret | Rotation | MVP Approach |
|--------|----------|--------------|
| PostgreSQL | On compromise | Manual; document procedure |
| OpenAI key | On compromise | Manual; can use separate key per env |
| B2C secret | On compromise | Manual; rotate in B2C portal |

**MVP:** Document rotation steps. No automated rotation. Phase 2: consider Azure automatic rotation for KV secrets where supported.

---

## 3. Rate Limiting

| Endpoint Type | Limit | Scope |
|---------------|-------|-------|
| Auth (B2C) | B2C built-in | Per user |
| API (general) | 100 req/min per user | Per JWT sub |
| LLM proxy | 20 req/min per user | Per JWT sub |
| Login attempts | B2C | B2C handles |

**Implementation:** In-process middleware (e.g. slowapi) or API Management (Phase 2).

---

## 4. CORS

- Allow only frontend origin (e.g. `https://app.clinai.example`)
- No `*` in production
- Credentials: `true` for cookie/session if used; JWT typically in header

---

## 5. HTTPS Enforcement

- App Service: HTTPS only; redirect HTTP → HTTPS
- HSTS header in production
- TLS 1.2 minimum

---

## 6. Session Timeout

- JWT expiry: 1 hour (configurable in B2C)
- Refresh token: per B2C policy
- No server-side session store in MVP (stateless JWT)
- Idle timeout: Frontend can clear token after N minutes; B2C handles token lifetime

---

## 7. Role Enforcement

| Role | Permissions |
|------|-------------|
| therapist | CRUD own conversations, folders; use LLM; view own usage |
| admin | All therapist + manage users, tenant settings, view tenant usage |

- Middleware checks `role` from token or DB
- 403 if action not permitted
- RLS enforces tenant; role enforces action type

---

## 8. Audit Table Schema

```sql
CREATE TABLE audit_log (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    UUID NOT NULL,
  actor_id     TEXT NOT NULL,       -- opaque user id
  action       TEXT NOT NULL,       -- e.g. conversation_created, user_deleted
  entity_type  TEXT NOT NULL,       -- conversation, folder, user
  entity_id    UUID,
  ip_address   INET,               -- optional; consider GDPR
  user_agent   TEXT,               -- optional; truncated
  metadata     JSONB,               -- no PII
  ts           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_tenant_ts ON audit_log (tenant_id, ts);
-- RLS: tenant_id = current tenant
```

**Actions to audit:**

- `user_login`
- `conversation_created`, `conversation_deleted`
- `folder_created`, `folder_deleted`
- `export_requested`
- `tenant_settings_changed`
- `user_invited`, `user_removed`

---

## 9. Input Validation

- All inputs validated via Pydantic
- Max length on text fields (e.g. message length)
- No raw SQL; parameterized queries only
- File upload (Phase 2): type/size limits, virus scan consideration

---

## 10. Dependency Security

- `pip audit` / `npm audit` in CI
- Dependabot or similar for updates
- Pin versions in requirements.txt / package-lock.json

---

## 11. Security Checklist (MVP)

| Item | Status |
|------|--------|
| HTTPS only | ✅ |
| Secrets in Key Vault | ✅ |
| JWT validation | ✅ |
| RLS on tenant tables | ✅ |
| Rate limiting | ✅ (in-process) |
| CORS restricted | ✅ |
| No PII in logs | ✅ |
| Audit log for sensitive actions | ✅ |
| Input validation | ✅ |
| Role enforcement | ✅ |
