---
name: projection-rebuild-simulator
description: Simulates replaying events to rebuild projections. Loads event sequence, re-runs projection logic, compares read-model snapshot, and detects non-idempotent updates, missing event handlers, and ordering sensitivity. Use when projection logic changes, when validating rebuild safety before full replays, or when adding or changing projection handlers. Returns PROJECTION_OK or PROJECTION_RISK with concrete fix steps.
---

# Projection Rebuild Simulator

Validates that projections can be safely rebuilt from the event log by simulating a replay and checking idempotency, ordering assumptions, and deterministic behavior.

## When to use

- Projection logic or handlers are added or changed
- Validating rebuild safety before a full event-log replay
- Adding or changing projection handlers
- Reviewing code that writes from events to read-model tables

## Simulation steps

1. **Identify scope**: Which projector(s) and read-model(s) are affected.
2. **Event sequence**: Consider a representative slice of events (e.g. all events for one `entity_id`, or events in different orders).
3. **Re-run mentally or via tests**: Apply the same events once; then "replay" (re-apply same events) and compare resulting read-model state.
4. **Check ordering**: If event order is relevant, document it; if not, verify reordering does not change outcome where it shouldn't.

## Checks

### 1. Idempotency

- [ ] Re-running the projector on the **same** event(s) produces the **same** read-model state.
- [ ] Writes are keyed (e.g. by `entity_id` or composite key) and use **upsert** (INSERT … ON CONFLICT UPDATE / MERGE), not append-only INSERT that would duplicate rows on re-run.
- [ ] No counters or aggregates that **increment** on each apply (e.g. `SET count = count + 1`); use **replace** semantics (e.g. recompute from events) or deduplicate by `event_id`.

**Risk:** Replay or duplicate delivery changes data (double counts, duplicate rows).

### 2. Event ordering assumptions

- [ ] Any assumption about event order is **explicit** (e.g. "handles only latest event per entity" or "requires Created before Updated").
- [ ] Out-of-order or duplicate delivery does not corrupt the read model (e.g. late event still yields correct final state after re-run).

**Risk:** Replay with different order or duplicates yields wrong state.

### 3. Deterministic behavior

- [ ] Same events in same order always produce the same read-model update.
- [ ] No reliance on system time, random numbers, or external calls for the **written** state (or explicitly documented and replay-safe).

**Risk:** Rebuild produces inconsistent results across runs.

### 4. Idempotency tests

- [ ] Tests exist that re-apply the same event(s) and assert the read model is unchanged (or reaches the same final state).
- [ ] Optionally: test with events in different orders where order should not matter.

**Risk:** Regressions break rebuild safety without detection.

## Output format

Always end with one of:

```markdown
## Projection Rebuild Simulator

**Result:** PROJECTION_OK | PROJECTION_RISK

### Summary
[One to three sentences: what was checked, main finding.]

### Idempotency
✅ Same output on re-run | ❌ [what breaks]

### Ordering
✅ Explicit / order-independent | ⚠️ / ❌ [assumptions or risks]

### Determinism
✅ | ❌ [non-deterministic source]

### Tests
✅ Idempotency covered | ❌ No idempotency tests

### Fix steps (only if PROJECTION_RISK)
1. [Concrete step: file, change, example]
2. ...
```

## Fix steps (PROJECTION_RISK)

Be specific: file (or component), current behavior, desired behavior, and if helpful a short code sketch.

| Problem | Fix direction |
|--------|----------------|
| Non-idempotent write | Use upsert by entity/key; or deduplicate by `event_id` before applying. |
| Order-dependent bug | Document required order; or make handler robust to any order (e.g. take latest by timestamp). |
| Non-deterministic state | Derive all written fields from event payload and timestamp; remove `now()`/random/external from write path. |
| No idempotency tests | Add test: apply same event(s) twice, assert read-model snapshot unchanged (or same final state). |

## Relation to other skills

- For a full **idempotency and side-effect** checklist (direct DB writes, upsert, no side-effects in handlers), use the **projection-idempotency-check** skill.
- This skill focuses on **simulating** a rebuild (re-run, compare) and returning **PROJECTION_OK** vs **PROJECTION_RISK** with fix steps.
