# ClinAI — GDPR Baseline (Placeholder)

**Status:** Documented; implementation in feature phases

## Retention

| Data | Retention |
|------|-----------|
| Conversations | 2 years (configurable per tenant) |
| Audit log | 10 years |
| Token usage | 12 months |

## Deletion

- User requests deletion → cascade: messages, conversation, blob exports
- Hard delete in MVP; soft delete + purge job in Phase 2
- Audit log: retain per legal requirement; no PII in payload

## Logging

- Never log: prompts, responses, patient names, raw transcripts
- Log only: tenant_id, user_id (opaque), action, entity_id, token_count, latency

## Key Vault

- Production: all secrets from Azure Key Vault
- Local: .env (gitignored); .env.example documents variables
