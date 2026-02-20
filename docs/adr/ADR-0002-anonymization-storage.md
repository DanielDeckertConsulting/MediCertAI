# ADR-0002: Anonymization Storage — Original vs Masked in DB

## Context

Phase 1.1 introduces an anonymization toggle. When enabled, user messages are masked (e.g. emails → [EMAIL]) before sending to Azure OpenAI. The question: do we store the **original** user message or the **masked** variant in `chat_messages`?

## Decision

**Store the original content** as typed by the user. Anonymization is applied only in the request pipeline before the LLM call; the masked variant is **not** persisted.

## Rationale

- **Therapist workflow:** Clinicians may need the original wording for documentation and clinical context.
- **Data minimization:** We avoid duplicating content (original + masked) in the DB.
- **Transparency:** Users see what they wrote; masking is an export/LLM-bound protection, not a storage transformation.
- **GDPR:** Retention and deletion policies apply to the stored original. LLM providers receive only masked text, reducing exposure.

## Consequences

- UI should warn when anonymization is OFF: "Avoid entering patient-identifying information."
- If stricter compliance is required later (e.g. never store PII), we can add an option to store masked-only and document it as a tenant setting.
- Audit logs remain metadata-only (no prompt/response content).
