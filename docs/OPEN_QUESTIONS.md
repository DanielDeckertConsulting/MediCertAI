# ClinAI MVP — Open Questions

**Version:** 0.1  
**Date:** 2025-02-19

---

## 1. Product & Scope

| ID | Question | Owner | Impact | Status | Draft / Resolution |
|----|----------|-------|--------|--------|--------------------|
| OQ-1 | Exact MVP feature list (conversation CRUD, folders, presets, Assistenzmodus, anonymization — all confirmed?) | Product | Scope clarity | **Resolved** | Full V1 feature list confirmed → see [MVP_FEATURE_LIST.md](MVP_FEATURE_LIST.md) |
| OQ-2 | Export format (PDF, DOCX, plain text)? | Product | Implementation | **Resolved** | PDF + TXT in MVP |
| OQ-3 | Billing/subscription model for MVP (manual invoicing vs. integration)? | Product | Scope | **Resolved** | Stripe integration |
| OQ-4 | German-only UI confirmed for MVP? | Product | i18n scope | **Resolved** | German only (de-DE); no i18n in MVP |

---

## 2. Identity & Tenancy

| ID | Question | Owner | Impact | Status | Draft / Resolution |
|----|----------|-------|--------|--------|--------------------|
| OQ-5 | B2C custom claim for `tenant_id`: extension attribute vs. app-specific claim? | Tech | Token design | **Resolved** | Extension attribute |
| OQ-6 | User-to-tenant mapping: B2C only or also in app DB? | Tech | Fallback logic | **Resolved** | App DB (lookup `users.tenant_id` by B2C `sub`) |
| OQ-7 | MVZ: one tenant per practice or per legal entity? | Product | Data model | **Resolved** | One tenant per legal entity |
| OQ-8 | Invite flow: email invite + B2C sign-up, or pre-provisioned users? | Product | Onboarding | **Resolved** | Email invite + B2C sign-up |

---

## 3. LLM & Prompts

| ID | Question | Owner | Impact | Status | Draft / Resolution |
|----|----------|-------|--------|--------|--------------------|
| OQ-9 | Default model: gpt-4o-mini vs. gpt-4o (cost vs. quality)? | Product/Tech | Cost, quality | **Resolved** | gpt-4o (quality over cost) |
| OQ-10 | Preset prompts: global vs. per-tenant? | Product | Data model | **Resolved** | Global presets + tenant-specific prompt configuration per tenant |
| OQ-11 | Assistenzmodus: one global prompt or tenant-customizable? | Product | Config | **Resolved** | One global base prompt; tenants can add tenant-specific prompt on top |
| OQ-12 | Anonymization patterns: which PII types in scope for MVP? | Legal/Product | Compliance | **Resolved** | See [ANONYMIZATION_SPEC.md](ANONYMIZATION_SPEC.md): names, email, phone, IDs, DoB, addresses; regex + optional NER |

---

## 4. Compliance & Legal

| ID | Question | Owner | Impact | Status | Draft / Resolution |
|----|----------|-------|--------|--------|--------------------|
| OQ-13 | Legal review for medical device / psychotherapy applicability? | Legal | Go-to-market | **Resolved** | No medical device — positioning avoids becoming one |
| OQ-14 | DPA with Microsoft (Azure, B2C, OpenAI) — already covered? | Legal | Compliance | **Resolved** | Yes, covered |
| OQ-15 | Data retention: default 2 years for conversations — confirmed? | Legal | Retention policy | **Resolved** | Confirmed: 2 years |
| OQ-16 | Audit log retention: 7 years — any jurisdiction-specific requirements? | Legal | Retention | **Resolved** | 10 years |
| OQ-17 | DPIA required before launch? | Legal | GDPR | **Resolved** | Yes, required before launch |

---

## 5. Infrastructure & Ops

| ID | Question | Owner | Impact | Status | Draft / Resolution |
|----|----------|-------|--------|--------|--------------------|
| OQ-18 | CI/CD: GitHub Actions, Azure DevOps, or other? | DevOps | Pipeline | **Resolved** | GitHub Actions |
| OQ-19 | Staging environment: mirror of prod or minimal? | DevOps | Cost, testing | **Resolved** | Minimal |
| OQ-20 | Backup: 7-day default for Postgres — sufficient? | DevOps | RTO/RPO | **Resolved** | Yes, sufficient |
| OQ-21 | Custom domain and TLS: managed how? | DevOps | Deployment | **Resolved** | Cloudflare |

---

## 6. UX & Design

| ID | Question | Owner | Impact | Status | Draft / Resolution |
|----|----------|-------|--------|--------|--------------------|
| OQ-22 | Design system: from scratch or existing (e.g. medical UI kit)? | Design | Consistency | **Resolved** | From scratch; theme changeable (easy to swap theme) |
| OQ-23 | Accessibility: WCAG 2.1 AA target for MVP? | Design | Effort | **Resolved** | Yes, WCAG 2.1 AA ready |
| OQ-24 | Mobile: responsive web only, or native app later? | Product | Scope | **Resolved** | Responsive web now; native app later |

---

## 7. Resolution Status

| Status | Meaning |
|--------|---------|
| Open | Not yet decided; blocks or critical path |
| Draft | Preliminary answer; needs confirmation |
| Resolved | Decision made; document in ADR or design doc |

---

## 8. Triage Summary

| Status | Count |
|-------|-------|
| Open | 0 |
| Draft | 0 |
| Resolved | 24 |

All open questions resolved.
