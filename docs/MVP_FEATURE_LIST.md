# ClinAI – Version 1 (MVP 0.1) Feature List

**Status:** Final V1 scope  
**Date:** 2025-02-19

---

## Boundaries

- Azure-only
- GDPR must-have
- No Kubernetes
- Healthcare-sensitive
- Multi-tenant SaaS
- Desktop-first
- No EHR integration

---

# 1. Authentication & Access Control

## 1.1 Azure B2C Authentication

- Login via Azure B2C
- Secure token validation on backend
- Session timeout (configurable)
- Refresh token flow
- HTTPS enforced

## 1.2 Role-Based Access Control (RBAC)

**Roles:** HCP Admin, HCP User

**Permissions:**
- Chat usage
- Data export
- Chat deletion
- Audit visibility (Admin only)

## 1.3 Multi-Tenant Isolation

- Tenant ID derived from B2C claim
- Row-Level Security (Postgres)
- No cross-tenant data visibility
- Tenant enforcement middleware

---

# 2. Chat Interface (Core)

## 2.1 Chat UI

- ChatGPT-style interface
- Streaming responses (token streaming)
- Timestamped messages
- Scroll persistence
- Message-level display separation (user vs AI)

## 2.2 Chat Management

- Create new chat
- Rename chat
- Delete single chat
- Bulk delete chats
- Mark chat as favorite
- Folder structure for chats
- Search over chat titles (NOT content)

## 2.3 Storage & Isolation

- Chat history stored in Postgres
- Tenant-separated
- No prompt leaves Azure tenant
- No sensitive content written to logs

---

# 3. Specialized Assist Modes (Therapy Presets)

## 3.1 Assistenzmodus Dropdown

1. Session Summary
2. Structured Documentation (Guideline-based)
3. Therapy Plan Draft
4. Risk Analysis (Suicidality Signal Detection)
5. Case Reflection (Supervision Support)

## 3.2 System Prompt Enforcement

- Server-side system prompts
- Prompt versioning
- System prompts NOT editable by client
- Prompt injection mitigation layer (basic)

---

# 4. Privacy & Anonymization Mode

## 4.1 Visible EU Processing Notice

UI notice: *"All data is processed within the EU."*

## 4.2 Anonymization Toggle

When enabled:
- Detect likely names
- Replace with placeholders (e.g. [PATIENT], [THERAPIST])
- Pre-LLM anonymization layer
- Clear UI indicator when active

## 4.3 No Model Training Guarantee

- Explicit policy: no fine-tuning
- No customer data used for model training

---

# 5. Data Management

## 5.1 Chat Deletion

- Delete individual chat
- Bulk delete chats
- Hard delete (no soft delete in MVP unless required for audit)

## 5.2 Export

Export per chat as **PDF** and **TXT**.
- PDF: clean layout, timestamped messages, minimal branding

---

# 6. Audit & Logging (Compliance-Light)

## 6.1 Audit Log Fields

- user_id, tenant_id, timestamp
- assist_mode, token_usage (prompt + completion)
- model_name, model_version

## 6.2 Explicitly NOT Logged

- Full prompt content
- Full response content
- Patient names
- Raw transcripts

## 6.3 Admin View

HCP Admin: usage metrics, token consumption, assist mode usage distribution

---

# 7. UI Requirements

- **Design:** Clean, calm, medical, minimal. No flashy animations.
- **Responsive:** Desktop first, tablet responsive
- **Accessibility:** WCAG AA

---

# 8. Security (Mandatory V1)

- Azure Germany West Central only; HTTPS; TLS; Key Vault
- Server-side system prompts; rate limiting; input validation; RLS
- Encryption at rest and in transit

---

# 9. Data Architecture (V1)

**Entities:** Tenant, User, Chat, ChatMessage, AssistMode, AuditLog, LLMUsageRecord
**Storage:** Postgres (structured), Azure Blob (optional for PDF temp)

---

# 10. MVP Metrics Tracking

- DAU per tenant, chats per week, avg session length
- Assist mode usage frequency, token usage per user, tenant churn rate
- No advanced analytics in V1

---

# Explicitly NOT in V1

- EHR integration, voice input, multi-language
- Custom branding per tenant, fine-tuning, multi-LLM routing
- Content full-text search, chat sharing, external integrations
- Mobile-first design

---

# Definition of Done – V1

- Multi-tenant isolation proven
- Chat streaming works
- Assist modes selectable
- Anonymization toggle works
- Audit logging functional
- PDF export works
- Azure-only data flow verified
- GDPR data deletion possible
- Admin usage view available
- No cross-tenant data leak possible
