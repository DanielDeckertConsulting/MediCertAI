# MentalCarePilot MVP — Technical Risks

**Version:** 0.1  
**Date:** 2025-02-19

---

## 1. Healthcare Regulatory Risk

| Risk | Impact | Likelihood | Mitigation | Owner | By |
|------|--------|------------|------------|-------|-----|
| Classification as medical device | High | Medium | Position as documentation assistance; no diagnoses; legal review | Legal | Pre-launch |
| Psychotherapy-specific regulation (e.g. German guidelines) | Medium | Medium | Legal counsel; ensure no therapeutic recommendations from AI | Legal | Pre-launch |
| BfArM / MDR applicability | High | Low | Document use case; avoid medical device claims | Legal | Pre-launch |
| Professional liability for therapists | Medium | Medium | Clear ToS; AI as tool, not substitute; therapist responsibility | Legal | Pre-launch |

---

## 2. LLM Hallucination Liability

| Risk | Impact | Likelihood | Mitigation | Owner | By |
|------|--------|------------|------------|-------|-----|
| AI suggests incorrect treatment | High | Medium | System prompt: no treatment advice; therapist must verify | Dev | V1 |
| Fictional patient data in output | High | Low | Anonymization reduces input; output review by therapist | Dev | V1 |
| Inappropriate content | Medium | Low | Content filters; system prompt constraints | Dev | V1 |
| Misleading documentation | Medium | Medium | Assistenzmodus as draft only; human review required | Product | V1 |

---

## 3. Token Cost Risk

| Risk | Impact | Likelihood | Mitigation | Owner | By |
|------|--------|------------|------------|-------|-----|
| Runaway usage per tenant | High | Medium | Usage tracking; per-tenant quotas; alerts | Dev | V1 |
| Model upgrade cost spike | Medium | Low | Pin model version; cost monitoring | DevOps | V1 |
| Abuse (e.g. automated scraping) | High | Low | Rate limiting; auth required; anomaly detection | Dev | V1 |

---

## 4. Tenant Misconfiguration

| Risk | Impact | Likelihood | Mitigation | Owner | By |
|------|--------|------------|------------|-------|-----|
| Wrong tenant_id in B2C | High | Low | Validation; test flows; fallback to user→tenant lookup | Dev | V1 |
| RLS policy bug | High | Low | Tests for cross-tenant isolation; code review | Dev | V1 |
| Shared credentials across tenants | High | Low | No tenant-specific secrets; tenant_id from token only | Dev | V1 |

---

## 5. Data Deletion Complexity

| Risk | Impact | Likelihood | Mitigation | Owner | By |
|------|--------|------------|------------|-------|-----|
| Orphaned data after deletion | Medium | Medium | Cascade rules; purge job; audit | Dev | V1 |
| Blob references not deleted | Medium | Low | Delete blobs when conversation deleted | Dev | V1 |
| Audit log retention vs GDPR | Medium | Low | Define retention; anonymize where possible; legal input | Legal | Pre-launch |
| Backup restore brings back deleted data | Medium | Low | Document backup policy; deletion = purge from backups in Phase 2 | DevOps | Phase 2 |

---

## 6. Azure Dependency Risk

| Risk | Impact | Likelihood | Mitigation | Owner | By |
|------|--------|------------|------------|-------|-----|
| Azure OpenAI outage | High | Low | Graceful degradation; show message; retry later | Dev | V1 |
| B2C outage | High | Low | Auth unavailable; document SLA | DevOps | V1 |
| Region outage | High | Very low | Single region for MVP; multi-region later | — | Phase 2 |
| Key Vault rate limits | Medium | Low | Caching of secrets; backoff | Dev | V1 |

---

## 7. Security / Privacy Risks

| Risk | Impact | Likelihood | Mitigation | Owner | By |
|------|--------|------------|------------|-------|-----|
| Prompt leakage in logs | High | Medium | Strict policy: never log prompts; code review | Dev | V1 |
| Cross-tenant data leak | High | Low | RLS + middleware; tests | Dev | V1 |
| XSS / injection | Medium | Low | Input validation; output escaping; CSP | Dev | V1 |
| Stolen token | Medium | Low | Short-lived JWT; refresh; HTTPS | Dev | V1 |

---

## 8. Risk Summary

| Category | Highest Risk | Priority | Action |
|----------|--------------|----------|--------|
| Regulatory | Medical device classification | P0 | Legal review before launch |
| LLM | Incorrect/inappropriate output | P0 | Strong system prompts; human-in-loop in V1 |
| Cost | Runaway usage | P1 | Usage tracking + quotas in V1 |
| Tenant | Misconfiguration | P1 | Validation + tests in V1 |
| Deletion | Orphaned data | P1 | Cascade + audit in V1 |
| Azure | OpenAI outage | P2 | Graceful degradation in V1 |
| Security | Prompt in logs | P1 | Policy + code review from day 1 |

---

## 9. Mitigation Action List

| # | Mitigation | Owner | Dependency |
|---|------------|-------|------------|
| 1 | Legal review (medical device, ToS) | Legal | OQ-13 |
| 2 | System prompt: no treatment advice | Dev | — |
| 3 | Usage table + per-tenant quotas | Dev | — |
| 4 | RLS + tenant middleware + isolation tests | Dev | — |
| 5 | Deletion cascade + blob purge | Dev | — |
| 6 | Never log prompts; review all log calls | Dev | — |
| 7 | Graceful degradation when OpenAI fails | Dev | — |
