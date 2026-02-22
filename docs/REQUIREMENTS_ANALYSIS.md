# MentalCarePilot MVP 0.1 — Requirements Analysis

**Version:** 0.1  
**Date:** 2025-02-19  
**Status:** Phase 0 — Architecture Only

---

## 1. Context Summary

| Attribute | Value |
|-----------|-------|
| Project | MentalCarePilot |
| Target Users | Psychotherapists (Einzelpraxis + MVZ) |
| Region | Azure Germany West Central |
| Compliance | GDPR (must-have in V1) |
| Tenant Model | Multi-tenant SaaS |
| LLM | Azure OpenAI |
| Auth | Azure B2C |
| DB | Azure Database for PostgreSQL |
| Blob | Azure Blob Storage |
| Secrets | Azure Key Vault |
| Encryption | At Rest + In Transit |

---

## 2. Core User Journeys

### 2.1 Primary Journeys (MVP)

| ID | Journey | Actor | Description |
|----|---------|-------|-------------|
| J1 | Authenticate & access workspace | Therapist | Login via Azure B2C, land on tenant workspace |
| J2 | Create / manage folders | Therapist | Organize conversations by patient/case/folder |
| J3 | Start chat with AI | Therapist | Start new conversation, optionally link to folder |
| J4 | Chat with streaming responses | Therapist | Type message, receive AI response via streaming |
| J5 | Use preset prompts | Therapist | Apply server-side versioned prompt templates (e.g. Dokumentationshilfe) |
| J6 | Toggle Assistenzmodus | Therapist | Enable/disable assistant mode with injected system prompt |
| J7 | Toggle anonymization | Therapist | Anonymize input before sending to LLM (PII masking) |
| J8 | View / search conversation history | Therapist | List and search past conversations within tenant |
| J9 | Export / download | Therapist | Export conversation or notes (MVP: basic export) |
| J10 | Delete conversation / data | Therapist | GDPR: request deletion of conversation and associated data |

### 2.2 Secondary Journeys (MVP)

| ID | Journey | Actor | Description |
|----|---------|-------|-------------|
| J11 | Configure tenant | Admin | Tenant-level settings (e.g. default Assistenzmodus) |
| J12 | Manage users | Admin | Invite users to practice (MVP: basic) |

---

## 3. Domain Entities

| Entity | Description | Attributes (Key) |
|--------|-------------|------------------|
| **Tenant** | Practice / MVZ organization | tenant_id, name, settings |
| **User** | Therapist or admin | user_id, tenant_id, email, role |
| **Folder** | Container for conversations | folder_id, tenant_id, name, parent_id |
| **Conversation** | Chat session | conversation_id, tenant_id, folder_id, created_at |
| **Message** | Single chat message | message_id, conversation_id, role, content_hash, ts |
| **Preset Prompt** | Server-side prompt template | prompt_id, version, tenant_id (optional), body |
| **Audit Log** | Security/access events | event_id, tenant_id, actor, action, ts |
| **Usage** | Token/request usage per tenant | tenant_id, period, tokens, requests |

---

## 4. System Boundaries

| Boundary | Scope | External Systems |
|----------|-------|------------------|
| **Identity** | Azure B2C | OIDC/OAuth2 flows |
| **LLM** | Azure OpenAI | Chat completions, streaming |
| **Storage** | Azure Blob | Document/export blobs |
| **Secrets** | Azure Key Vault | Connection strings, API keys |
| **Observability** | Application Insights | Logs, traces, metrics |

---

## 5. Compliance Constraints

### 5.1 GDPR (Must-Have in V1)

- **Lawfulness:** Consent or legitimate interest documented
- **Purpose limitation:** Data used only for stated purpose
- **Data minimization:** Only necessary data collected
- **Storage limitation:** Retention defined and enforced
- **Integrity & confidentiality:** Encryption, access control
- **Accountability:** Audit trail, DPA, deletion workflow

### 5.2 Healthcare Sensitivity

- Psychotherapist context implies potential patient-related content
- No direct patient system; therapist uses AI for documentation assistance
- Anonymization mode must be available
- No prompt/input data in application logs

---

## 6. Security Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| S1 | All traffic over HTTPS | Must |
| S2 | Auth via Azure B2C; no custom auth in V1 | Must |
| S3 | Tenant isolation: zero cross-tenant data access | Must |
| S4 | Row-Level Security (RLS) on all tenant-scoped tables | Must |
| S5 | Secrets in Key Vault; no secrets in code/config | Must |
| S6 | Rate limiting on API and LLM calls | Should |
| S7 | Session timeout configurable | Should |
| S8 | Audit logging for sensitive actions | Must |

---

## 7. Non-Functional Requirements

### 7.1 Scalability

- Support ~50–200 tenants (MVP)
- ~10–50 concurrent users peak
- LLM streaming: first token &lt; 3s p95

### 7.2 Availability

- Target: 99.5% uptime (MVP)
- Graceful degradation if OpenAI unavailable
- Health checks for API, DB, LLM connectivity

### 7.3 Auditability

- Audit table for: login, conversation create/delete, export, tenant config changes
- No PII in audit messages; reference by entity_id only
- Retain audit logs per retention policy

### 7.4 Observability

- Structured JSON logging (no PII)
- Correlation IDs across requests
- App Insights: traces, metrics, alerts
- Token usage per tenant for cost control

### 7.5 Data Isolation

- Logical isolation per tenant (single DB + RLS)
- No cross-tenant queries
- Tenant ID derived from B2C token and enforced in middleware

### 7.6 Performance (Streaming LLM)

- Server-Sent Events (SSE) or similar for streaming
- Backend proxies to Azure OpenAI; no client-to-OpenAI direct calls
- Connection timeout / keep-alive appropriate for streaming

---

## 8. Out of Scope (MVP)

- Kubernetes, microservices
- Patient-facing portal
- Billing / subscription management (manual for MVP)
- Offline mode
- Multi-language UI (German only for MVP)
- Advanced prompt injection defense beyond basic mitigation

---

## 9. Traceability Matrix

| Requirement Area | Source | Delivered By |
|------------------|--------|--------------|
| Multi-tenancy | Context | MULTI_TENANCY_DESIGN.md |
| GDPR | Context | LLM_SECURITY_AND_GDPR.md |
| Azure services | Context | ARCHITECTURE.md, INFRASTRUCTURE_DECISION |
| No K8s | Constraint | MVP_SIMPLICITY_JUSTIFICATION.md |
| Streaming LLM | NFR | FRONTEND_ARCHITECTURE.md, TECHSTACK.md |
| Assistenzmodus / Presets | Inferred MVP | FRONTEND_ARCHITECTURE.md |
| Anonymization | Inferred MVP | LLM_SECURITY_AND_GDPR.md |
