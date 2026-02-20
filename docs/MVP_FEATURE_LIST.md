# 🏥 ClinAI – Version 1 (MVP 0.1) – Complete Feature List

**Status:** Implemented features as of current codebase  
**Date:** 2026-02-20

---

# Boundaries

* Azure-only (Germany West Central)
* GDPR must-have
* No Kubernetes
* Healthcare-sensitive positioning
* Multi-tenant SaaS
* Mobile-first (390px baseline, 768px tablet, desktop)
* No EHR integration
* No content logging
* No model fine-tuning

---

# 1. Authentication & Access Control

## 1.1 Azure B2C Authentication (Partial / Placeholder)

* Login via Azure B2C (UI placeholder)
* Local dev auth bypass (`auth_bypass_local`)
* Secure token validation backend-ready (B2C wiring pending)
* HTTPS enforced
* Refresh/session flow planned

## 1.2 Role-Based Access Control (RBAC)

Roles:

* **HCP Admin**
* **HCP User**

Permissions:

* Chat usage
* Chat deletion
* Data export
* Finalization
* Audit visibility (Admin = tenant-wide; User = own only)

## 1.3 Multi-Tenant Isolation (RLS Enforced)

* Tenant derived from B2C claim or injected in dev
* Row-Level Security on:

  * chats
  * chat_messages
  * folders
  * audit_logs
  * usage_records
* No cross-tenant visibility
* Tenant enforcement middleware

---

# 2. Chat Interface (Core)

## 2.1 Chat UI

* ChatGPT-style interface
* Streaming responses (token streaming)
* Timestamped messages
* Scroll persistence
* Clear user/AI separation
* Mobile responsive layout
* WCAG AA accessibility baseline

### Smart Context Intelligence

**Continue Session – Smart Context Banner**

* Shows when opening existing chat:

  * "Letzte Aktivität vor X Tagen – Kontext wird fortgeführt."
  * Optional: session length
  * Optional: total tokens in session
* Metadata only, no content analysis

---

## 2.2 Chat Lifecycle Management

* Create chat
* Rename chat
* Delete chat (hard delete)
* Mark as favorite
* Folder organization
* Search over chat titles (no content search)

### Conversation Lock / Finalize

* Button: „Dokumentation abschließen"
* Sets `status = finalized`
* Read-only state
* Message sending blocked (409)
* Export still allowed
* Audit event: `chat.finalized`

---

## 2.3 Storage & Isolation

* Postgres storage
* Azure-only processing
* No prompt leaves Azure
* No prompt/response content logged

---

# 3. Structured Assist Modes

## 3.1 Assist Modes

1. Chat with AI
2. Session Summary
3. Structured Documentation
4. Therapy Plan Draft
5. Risk Analysis

## 3.2 System Prompt Governance

* Server-side prompt enforcement
* Prompt versioning
* Prompt injection mitigation
* Client cannot modify system prompts

## 3.3 Safe Prompt Mode (Strenger Sicherheitsmodus)

Toggle per conversation.

When active:

* Conservative phrasing
* No speculative language
* No absolute medical claims
* Shorter responses
* Strict modifier appended server-side

Indicator badge visible when active.

---

# 4. Privacy & Compliance Layer

## 4.1 Visible EU Processing Notice

Banner on Chat + Login:

> "All data is processed within the EU."

* Dismissible
* Links to /privacy
* Mobile responsive

## 4.2 Anonymization Toggle

* Detect likely names
* Replace with placeholders ([PATIENT], [THERAPIST])
* Pre-LLM anonymization
* Clear UI indicator

## 4.3 Consent Documentation Module

Settings checkbox:

> "Ich bestätige, dass ich keine identifizierenden Patientendaten ohne Einwilligung eingebe."

* Stored in user profile
* Audit event on update
* Optional reminder banner
* Non-blocking

## 4.4 No Model Training Guarantee

* No fine-tuning
* No training on customer data

---

# 5. Data Management

## 5.1 Chat Deletion

* Hard delete
* Tenant enforced

## 5.2 Export (PDF & TXT)

Per chat:

* TXT export
* PDF export (clean layout, timestamped)
* Minimal branding
* Allowed when finalized
* Audit event: `export_requested`

## 5.3 Folders

* Create / rename / delete folders
* Assign chats
* Filter by folder
* Deleting folder moves chats to Unfiled

---

# 6. Case-Level Intelligence

## 6.1 Cross-Conversation Case Summary

Button: "Fallzusammenfassung generieren"

* Select multiple chats
* POST `/cases/summary`
* Returns:

  * Case summary
  * Trends
  * Treatment evolution
* Not automatically stored
* Disclaimer:

  > "KI-gestützte Zusammenfassung – keine diagnostische Entscheidung."
* Audit event: `cross_case_summary_generated`

---

# 7. AI Response Rendering

* Markdown sanitization
* Block extraction
* Action detection
* AIResponseRenderer
* Timeline view

## AI Confidence Indicator

Under AI messages:

> "KI-Entwurf – fachliche Prüfung erforderlich."

Optional:

* Modellvertrauen (if available)

---

# 8. Voice-to-Text Dictation

* Microphone icon in chat input
* Browser Web Speech API (MVP)
* No audio stored
* Only text sent
* User can edit before sending
* Button hidden if unsupported

---

# 9. Admin & Monitoring

## 9.1 KPIs

* Token usage (input/output/total)
* Requests
* Chats created
* Assist mode distribution
* Model usage
* Active days & streak

Scope:

* Admin: tenant-wide
* User: own only

## 9.2 Searchable Audit Logs

Filter by:

* Date range
* Assist mode
* Action
* Model name

Logged:

* user_id
* tenant_id
* timestamp
* assist_mode
* token_usage
* model_name
* model_version

Not logged:

* Full prompts
* Full responses
* Patient names
* Raw transcripts

---

# 10. Security Architecture

* Azure Germany West Central
* HTTPS / TLS
* Azure Key Vault
* Encryption at rest
* Rate limiting
* Input validation
* Server-side prompt enforcement
* RLS tenant isolation

---

# 11. Data Architecture

Entities:

* Tenant
* User
* Folder
* Chat (active | finalized)
* ChatMessage
* AssistMode
* AuditLog
* usage_records
* AIResponse

Storage:

* Postgres
* Azure Blob (PDF temp optional)

---

# Explicitly NOT in V1

* EHR integration
* Multi-language
* Custom tenant branding
* Fine-tuning
* Multi-LLM routing
* Content full-text search
* Chat sharing
* External integrations
* Kubernetes
* Advanced clinical decision support

---

# Definition of Done – V1 (Complete)

* Multi-tenant isolation proven
* Streaming chat works
* 5 assist modes available
* Safe Prompt Mode works
* Anonymization works
* Consent module present
* EU notice visible
* Smart context banner active
* Chat finalize (lock) works
* Folders CRUD works
* Case summary generation works
* PDF/TXT export works
* Voice dictation works
* AI Confidence Indicator visible
* Admin KPIs + searchable logs functional
* No cross-tenant data leak possible
* No sensitive content logged
* Azure-only processing

---

# Strategic Positioning After V1

ClinAI is no longer:

> "A secure ChatGPT clone"

It is now:

> **A GDPR-compliant, clinically positioned AI documentation co-pilot with governance controls, medico-legal stabilization, and structured case intelligence.**
