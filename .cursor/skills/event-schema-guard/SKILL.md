---
name: event-schema-guard
description: Validates event schema and enforces event-log discipline. Use when a new event is introduced, the event schema is modified, or shared schema/types change. Checks required envelope fields, naming convention (<entity>.<action>.<past_tense>), minimal payload, no PII unless required, schema.json canonical alignment with backend and frontend types, and no breaking change without a schema_version increment strategy. Returns EVENT_SCHEMA_OK or EVENT_SCHEMA_BLOCKERS with exact fix steps.
---

# Event Schema Guard

Validates new or changed domain events and enforces event-log discipline. Apply when events or shared schema/types change.

## Trigger

- New event type or payload shape added
- Event schema (envelope or payload) modified
- `shared/events/schema.json`, `shared/events/types.py`, or `shared/events/types.ts` changed

## Required envelope fields

Every event must include exactly these (canonical: `shared/events/schema.json`):

| Field | Type | Purpose |
|-------|------|---------|
| `event_id` | string (UUID) | Unique event id |
| `ts` | string (ISO8601) | Timestamp (UTC) |
| `actor` | string | Actor that caused the event |
| `entity_type` | string | e.g. `lead`, `call`, `queue_item` |
| `entity_id` | string | ID of the affected entity |
| `event_type` | string | Action identifier (see naming below) |
| `payload` | object | Minimal event-specific data |
| `source` | string | e.g. `backend`, `frontend` |
| `schema_version` | integer (>= 1) | Envelope/payload version |

## Checks

Run in order. On first failure, stop and output **EVENT_SCHEMA_BLOCKERS** with exact fix steps.

### 1. Required fields present

- All nine fields must be present; no extra top-level properties if schema has `additionalProperties: false`.
- **Fix:** Add missing fields to event construction and to `shared/events/schema.json` `required` array; ensure backend validation (e.g. Pydantic in `backend/app/domain/events/`) and `shared/events/types.py` / `shared/events/types.ts` include them.

### 2. Naming convention: \<entity\>.\<action\>.\<past_tense\>

- `event_type` must follow: entity (snake_case), action (snake_case), past tense.
- Examples: `lead.created`, `call.ended`, `lead.outcome.recorded`, `queue_item.created`.
- **Fix:** Rename `event_type` to match pattern; update event catalog in `docs/events.md`.

### 3. Payload minimal; no PII unless strictly required

- Payload only what projectors and audit need; no derived or redundant data.
- No PII (names, emails, phones, addresses) unless the event contract explicitly requires it; prefer IDs/references.
- **Fix:** Remove unnecessary payload fields; replace PII with opaque IDs or document why PII is required.

### 4. schema.json canonical; backend + frontend aligned

- `shared/events/schema.json` is canonical. Backend (e.g. `backend/app/domain/events/`) and frontend types must match it.
- **Fix:** Update `shared/events/schema.json` first, then `shared/events/types.py` and `shared/events/types.ts`; sync any backend Pydantic schemas and `docs/events.md`.

### 5. No breaking change without schema_version strategy

- Changing payload shape or semantics is a breaking change for consumers. Require a versioning strategy.
- **Fix:** Bump `schema_version` when payload or envelope contract changes; document the change and, if needed, add an upcaster or migration note. Do not overwrite historical events.

## Output: EVENT_SCHEMA_BLOCKERS

When any check fails, output the following and do **not** approve the change:

```markdown
## EVENT_SCHEMA_BLOCKERS

**Trigger:** [New event introduced | Event schema modified | Shared schema/types changed]

**Failed check:** [Check name]

**What's wrong:** [One sentence]

**Fix:**
1. [Exact step 1 - file path, field name, or code change]
2. [Exact step 2]
...

**Files to update:** [e.g. shared/events/schema.json, shared/events/types.py, shared/events/types.ts, backend/..., docs/events.md]
```

Fix steps must be **explicit** (exact field names, paths, and actions). No vague "ensure X" without how.

## Output: EVENT_SCHEMA_OK

When all checks pass:

```markdown
## EVENT_SCHEMA_OK

All checks satisfied. Required fields present; event_type follows \<entity\>.\<action\>.\<past_tense\>; payload minimal and PII-safe; schema.json and backend/frontend types aligned; breaking changes covered by schema_version strategy. Proceed.
```

## Quick checklist (for agent)

- [ ] All nine required fields present; schema.json and types aligned
- [ ] event_type matches \<entity\>.\<action\>.\<past_tense\>
- [ ] Payload minimal; no PII unless required
- [ ] schema.json canonical; types.py and types.ts in sync
- [ ] No breaking change without schema_version bump and strategy
