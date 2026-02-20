# Projection Rebuild Simulator — Reference

## Simulating in code (optional)

To simulate a rebuild in tests:

1. **Setup**: Create a minimal event store slice (or in-memory list of events).
2. **First run**: Apply all events to the projector; capture read-model state (e.g. query the projection table).
3. **Second run**: Reset read model (or use a fresh DB/session), apply the **same** events again.
4. **Assert**: Compare state after run 1 and run 2; they must be identical.

Example pattern (pseudocode):

```python
def test_lead_new_queue_projector_idempotent():
    events = [lead_created_event(lead_id="..."), lead_converted_event(lead_id="...")]
    # Run 1
    for e in events:
        projector.handle(e)
    state1 = get_lead_new_queue_snapshot()
    # Run 2 (e.g. clear table, same events)
    clear_lead_new_queue()
    for e in events:
        projector.handle(e)
    state2 = get_lead_new_queue_snapshot()
    assert state1 == state2
```

## Ordering tests

If the projector should be order-independent for certain events:

- Build two event lists: same events, different order.
- Apply each list; where order should not matter, assert same final read-model state.

## Rebuild strategy (docs)

When adding or changing a projection, document in code or docs:

- **Rebuild**: "Truncate read table X, then replay all events of type A, B for entity_type Y."
- **Idempotency**: "Upsert by (entity_id); safe to re-run same events."

This supports the projection-rebuild-simulator checks and operational replays.
