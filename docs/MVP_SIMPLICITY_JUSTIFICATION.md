# ClinAI MVP — Infrastructure Simplicity Justification

**Version:** 0.1  
**Date:** 2025-02-19

---

## 1. What We Avoid (and Why)

| Avoid | Reason |
|-------|--------|
| **Kubernetes** | Operational complexity; no scale or isolation requirement in MVP. App Service is simpler to deploy and maintain. |
| **Microservices sprawl** | Single backend is sufficient; no bounded context needs separate deployment. |
| **Event-driven overengineering** | No cross-system async workflows in MVP. CRUD + LLM proxy are request-scoped. |
| **Service mesh** | Single backend; no inter-service traffic. |
| **Multiple databases** | One Postgres + RLS covers multi-tenant needs. |
| **Elasticsearch / separate search** | Postgres full-text or simple filters enough for MVP. |

---

## 2. What We Use (MVP)

| Component | Count | Purpose |
|-----------|-------|---------|
| Backend | 1 | API, auth, LLM proxy, business logic |
| Frontend | 1 | SPA (chat, folders, settings) |
| Database | 1 | PostgreSQL, all tenant data |
| Queue | 0 (or 1 if needed) | Deletion/export can be in-request |
| Blob | 1 | Exports, optional attachments |
| Auth | B2C (managed) | No custom auth service |
| LLM | Azure OpenAI | No self-hosted model |

---

## 3. Why This Is Enough for MVP

### 3.1 Scale

- Target: ~50–200 tenants, ~10–50 concurrent users
- Single App Service instance can handle this
- Postgres Flexible Burstable is sufficient
- No need for read replicas or sharding

### 3.2 Feature Set

- CRUD: Tenants, users, folders, conversations, messages
- LLM: Streaming chat via proxy
- Auth: B2C handles identity
- No heavy batch jobs, no real-time multi-user collaboration
- Export: Small; sync in-request acceptable

### 3.3 Team & Time

- Single backend, single frontend = less coordination
- One deploy pipeline
- Easier local dev (docker-compose or minimal services)
- Faster iteration

---

## 4. What Will Break at Scale

| Threshold | Symptom | Evolution |
|-----------|---------|-----------|
| **~500+ concurrent users** | App Service CPU/memory | Scale out (more instances); add CDN for frontend |
| **~1000+ tenants** | Postgres connection pool | Read replica, connection pooling (PgBouncer) |
| **Heavy async jobs** | Blocking in request | Add Azure Queue + Functions |
| **Regulatory isolation** | Tenant data separation | Schema-per-tenant or DB-per-tenant |
| **LLM rate limits** | 429 from OpenAI | Queue + backoff; or multiple deployments |
| **Geo distribution** | Latency for distant users | Multi-region deployment (Phase 2+) |

---

## 5. When to Evolve Architecture

| Trigger | Action |
|---------|--------|
| Async deletion/export needed | Add Azure Queue + Function |
| Token limits / cost alerts | Usage aggregation job (Function) |
| Compliance requires isolation | Evaluate schema-per-tenant |
| 2–3x current load | Scale out App Service; add read replica |
| New bounded context (e.g. Billing) | Consider separate service only if clear boundary |
| Multi-region | Separate deployments per region |

---

## 6. Decision Summary

- **MVP:** 1 backend, 1 frontend, 1 DB, 0–1 queue
- **Rationale:** Minimal complexity, fast delivery, Azure-native
- **Evolution path:** Add queue, scale out, read replicas as needed — no Big Bang rewrite
