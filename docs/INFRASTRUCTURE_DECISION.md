# ClinAI MVP — Infrastructure Decision

**Version:** 0.1  
**Date:** 2025-02-19  
**Region:** Azure Germany West Central

---

## 1. Service Recommendations

| Layer | Service | Configuration |
|-------|---------|----------------|
| **Backend** | Azure App Service (Linux) | B1 or S1; Python 3.11 runtime |
| **Frontend** | Static Web App or App Service static | CDN, custom domain |
| **Database** | Azure Database for PostgreSQL (Flexible) | Burstable B1ms; single server |
| **Blob** | Azure Blob Storage | GPv2, LRS, private container |
| **Auth** | Azure B2C | User flows for sign-in/sign-up |
| **LLM** | Azure OpenAI Service | gpt-4o-mini or gpt-4o; Germany West Central |
| **Secrets** | Azure Key Vault | Standard tier |
| **Observability** | Application Insights | Same region |

---

## 2. Deployment Model — MVP

### Option A: App Service (Recommended)

| Pro | Con |
|-----|-----|
| Simple deployment | Less isolation than containers |
| Built-in scaling (scale out) | |
| Easy Key Vault integration | |
| No container registry needed | |
| Good for monolith | |

### Option B: Container Apps

| Pro | Con |
|-----|-----|
| Container-based | Slightly more setup |
| More portability | Overkill for single backend MVP |
| Auto-scale to zero possible | |

### Option C: Azure Functions (Backend)

| Pro | Con |
|-----|-----|
| Serverless, pay-per-use | Cold starts for streaming |
| | Less natural for stateful flows |
| | More complex for long-lived connections |

**Decision:** App Service for backend. Container Apps and Functions add complexity without clear MVP benefit. Revisit when scaling or isolation requirements grow.

---

## 3. Database: Azure PostgreSQL

- **Tier:** Flexible Server, Burstable B1ms (MVP)
- **Region:** Germany West Central
- **Extensions:** `uuid-ossp`, `pgcrypto` (if needed for encryption at app layer)
- **Backup:** 7-day retention (default)
- **RLS:** Enabled on tenant-scoped tables (see MULTI_TENANCY_DESIGN.md)

**Alternative rejected:** Cosmos DB — overkill for relational domain; Postgres sufficient and cheaper.

---

## 4. Blob Storage

- **Account:** GPv2, LRS
- **Container:** Private; SAS or Managed Identity for backend access
- **Use cases (MVP):** Export files, optional future document uploads

---

## 5. Azure B2C

- **User flows:** Sign-up, Sign-in, Profile edit
- **Custom claims:** `tenant_id`, `role` (therapist, admin)
- **Token:** ID token + optional access token for API
- **Redirect:** SPA redirect URI for OAuth2 code flow + PKCE

---

## 6. Azure OpenAI

- **Deployment:** Chat completions model (e.g. gpt-4o-mini for cost, gpt-4o for quality)
- **Region:** Germany West Central (data residency)
- **Endpoint:** Via Key Vault secret or Managed Identity
- **No external calls:** All LLM traffic stays within Azure tenant

---

## 7. Key Vault

- **Secrets:** PostgreSQL connection string, OpenAI API key, B2C client secret
- **Access:** App Service Managed Identity; no keys in config
- **Rotation:** Manual for MVP; document procedure

---

## 8. Application Insights

- **Workspace:** Same region
- **Types:** Requests, traces, custom metrics (token usage)
- **Logging:** Structured JSON; no PII
- **Alerts:** 5xx rate, latency p95, OpenAI errors

---

## 9. Background Jobs (Optional MVP)

| Need | Solution |
|------|----------|
| GDPR deletion workflow | In-request or Azure Function on Queue message |
| Token usage aggregation | Nightly Function or in-request accumulation |
| Export generation | Sync in-request (MVP) or Queue + Function |

**Recommendation:** Start without dedicated queue. Add Azure Queue Storage + Function when async deletion or heavy exports are required.

---

## 10. Summary

| Component | Choice | Why |
|-----------|--------|-----|
| Compute | App Service | Simple, sufficient for MVP |
| DB | Azure PostgreSQL Flexible | Relational, RLS, cost-effective |
| Blob | Azure Blob | Standard for files |
| Auth | Azure B2C | Managed identity, B2C support |
| LLM | Azure OpenAI | In-region, no external egress |
| Secrets | Key Vault | Best practice, no secrets in code |
| Monitoring | App Insights | Native Azure integration |
