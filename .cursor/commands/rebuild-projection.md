# rebuild-projection

Dieser Command ist verfügbar im Chat mit `#rebuild_projection` bzw. `/rebuild-projection`.

---

You are the **PROJECTION REBUILD DESIGNER** for the EasyHeadHunter project.

## Mission

Design and implement a **safe projection rebuild tool** that replays events from the event store into projection (read-model) tables, with DRY_RUN support, idempotency, and a clear safety contract.

---

## User Input

- **Projection name(s)** to rebuild (e.g. `candidate_summary`, `lead_summary`) or `all`
- **Mode:** `DRY_RUN` (no DB writes to projection tables) or `APPLY` (write to projection tables)
- **From** (optional): `--from-ts <ISO timestamp>` or `--from-event-id <UUID>` to start replay from a point (default: from oldest event)

---

## Hard Rules

1. Rebuild must be **idempotent** and **restartable** (re-running produces same result; interrupt + restart is safe).
2. Must support **DRY_RUN** (no writes to projection tables) and **APPLY**.
3. Must have a **kill switch / cancellation** mechanism (e.g. SIGINT/SIGTERM, or `--max-events` cap).
4. Must **log progress** (events processed, batches, errors) and a **summary** at the end.
5. Must **NOT** mutate the **event_store** (read-only access to event_store).

---

## Deliverables

1. **Spec** – how the tool works (overview, flow, guarantees).
2. **CLI design** – command + arguments.
3. **Safety guarantees** – transactions, batching, checkpoints (optional Phase 2).
4. **Implementation plan** – files to add/change, order of work.
5. **Minimal tests** – what to test (unit + one integration-style test).

---

## Implementation constraints (suggested)

- Implement as **Python CLI script** under `backend/scripts/` (e.g. `rebuild_projection.py`) or `backend/app/domain/projections/` (e.g. `rebuild_cli.py`). Prefer **`backend/scripts/rebuild_projection.py`** so domain stays free of CLI wiring.
- Use **DB transaction boundaries per batch** (one transaction per batch of events; on failure, only that batch is rolled back).
- **Checkpoint table** is optional Phase 2; for MVP use **“start over”** semantics (truncate/clear projection tables for selected projectors, then replay from event_store from beginning or from `--from-ts`/`--from-event-id`).

---

# Output structure

Produce the following sections and **end with: READY_FOR_IMPLEMENTATION**.

---

## 1. Overview

**Purpose:** Rebuild one or more read-models (projections) by replaying events from `event_store` into the corresponding projection tables. Used after schema changes, bugs in projectors, or to re-sync after data fixes.

**Flow (high level):**

1. Parse CLI: projection name(s) or `all`, mode (`DRY_RUN` | `APPLY`), optional `--from-ts` / `--from-event-id`.
2. Resolve projectors by name (from registry; support `all` = all registered projectors).
3. **APPLY only:** Optionally clear target projection tables for selected projectors (MVP: “start over” for those projections).
4. Stream events from `event_store` in **chronological order** (oldest first), in batches (e.g. 100–500 per batch).
5. For each batch: in DRY_RUN, only log what would be applied; in APPLY, open transaction → run each event through selected projectors → commit (or rollback on error and abort/retry according to policy).
6. Support cancellation (SIGINT/SIGTERM or `--max-events`) and log progress + final summary.

**Idempotency:** Projectors must implement idempotent `handle(event)` (e.g. upsert by `event_id` or entity key). Re-running the rebuild yields the same projection state. Restarting after interrupt = start over from beginning or from same `--from-*` (MVP: no checkpoint persistence).

---

## 2. CLI Examples

```bash
# Dry run: which events would be replayed, no writes
python -m scripts.rebuild_projection --projection candidate_summary --mode DRY_RUN

# Rebuild single projection (APPLY)
python -m scripts.rebuild_projection --projection candidate_summary --mode APPLY

# Rebuild all projections from a given time
python -m scripts.rebuild_projection --projection all --mode APPLY --from-ts "2025-02-01T00:00:00Z"

# Rebuild from a specific event (e.g. after that event_id)
python -m scripts.rebuild_projection --projection lead_summary --mode APPLY --from-event-id "550e8400-e29b-41d4-a716-446655440000"

# Cap events (kill switch / testing)
python -m scripts.rebuild_projection --projection all --mode APPLY --max-events 1000
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `--projection` | Yes | Projection name (e.g. `candidate_summary`) or `all` |
| `--mode` | Yes | `DRY_RUN` \| `APPLY` |
| `--from-ts` | No | ISO8601 timestamp; replay events with `ts >= from-ts` (chronological order) |
| `--from-event-id` | No | UUID; replay events after this `event_id` (by `ts` then `event_id`) |
| `--batch-size` | No | Events per batch (default e.g. 200) |
| `--max-events` | No | Stop after N events (0 = no limit); useful as kill switch or for tests |

**Exit codes:** `0` = success, `1` = usage/configuration error, `2` = replay error (e.g. projector exception in APPLY).

---

## 3. Architecture

- **Event store:** Read-only. New method (or adapter) to stream events **oldest first** with optional `since_ts` / `after_event_id` and **limit/offset** (or keyset) for batching. Implement e.g. `list_events_chronological(since_ts=None, after_event_id=None, limit=200, offset=0)` on a new read-only interface or directly on `PostgresEventStore` (or a dedicated `EventStoreReader` used only by rebuild).
- **Projector registry:** Already has `get_projectors()`. Each projector must expose a **name** (e.g. `ProjectorBase.name` or `__name__`) so the CLI can filter by `--projection X` or `all`.
- **Rebuild orchestrator:** One function/class that:
  - Takes (projection names, mode, from_ts, from_event_id, batch_size, max_events).
  - Iterates batches from event store (chronological).
  - In APPLY: per batch, starts DB transaction, runs each event through selected projectors, commits; on exception, rollback and exit (or log and exit).
  - In DRY_RUN: same loop but does not call projector `handle()`, only counts and logs.
  - Handles SIGINT/SIGTERM (set a flag, stop after current batch, log summary).
- **No checkpoint in MVP:** Each run starts from “beginning” or from `--from-ts`/`--from-event-id`. Optional Phase 2: checkpoint table (e.g. `rebuild_checkpoints`: projection_name, last_event_id, last_ts, updated_at) to resume after last batch.

---

## 4. Pseudocode

```text
function rebuild(projection_names, mode, from_ts, from_event_id, batch_size, max_events):
  projectors = resolve_projectors(projection_names)  # from registry by name or "all"
  if APPLY:
    for p in projectors:
      clear_projection_table(p)  # MVP: truncate or delete by projection
  total, errors = 0, 0
  since_ts, after_id = from_ts, from_event_id
  while True:
    batch = event_store.list_events_chronological(since_ts=since_ts, after_event_id=after_id, limit=batch_size)
    if not batch: break
    if max_events and total + len(batch) > max_events:
      batch = batch[: max_events - total]
    if mode == DRY_RUN:
      log("DRY_RUN would apply", len(batch), "events")
      total += len(batch)
    else:
      with session.begin():  # one transaction per batch
        for ev in batch:
          try:
            for p in projectors: p.handle(ev)
            total += 1
          except Exception as e:
            errors += 1
            log_error(ev, e)
            raise  # rollback batch and exit, or collect and continue (configurable)
    # advance cursor for next batch
    last = batch[-1]
    since_ts, after_id = last.ts, last.event_id
    if max_events and total >= max_events: break
    if cancellation_requested(): break
  log_summary(total, errors)
  return 0 if errors == 0 else 2
```

**Clear projection (MVP):** For each selected projector, either:
- call a method `clear()` on the projector (if it exists), or
- run a known truncate/delete for that projector’s table (e.g. from a small registry mapping projection name → table name or clear SQL). Prefer `projector.clear()` if you add it to the base interface (optional, only for projectors that support it).

---

## 5. Files to add/change

| Action | Path | Description |
|--------|------|-------------|
| Add | `backend/scripts/rebuild_projection.py` | CLI entrypoint: argparse, resolve projectors, call rebuild engine. |
| Add | `backend/app/domain/projections/rebuild_engine.py` | Rebuild logic: stream events in batches, DRY_RUN/APPLY, transaction per batch, progress + summary. |
| Change | `backend/app/domain/events/event_store.py` (or new reader) | Add `list_events_chronological(since_ts=None, after_event_id=None, limit=..., offset=0)` for oldest-first pagination. |
| Change | `backend/app/domain/projections/projector_base.py` | Add `name: str` (abstract or property) so each projector has a stable name for CLI. |
| Change | `backend/app/domain/projections/projector_registry.py` | Optional: `get_projector_by_name(name: str)`, `get_all_projector_names()`. |
| Optional | Projectors (e.g. `*_projection.py`) | Implement `name` and optionally `clear()` for APPLY “start over”. |
| Add | `backend/tests/domain/projections/test_rebuild_engine.py` | Unit tests: dry run no writes, apply calls handle, batch boundaries, max_events, from_ts/from_event_id. |
| Add | `backend/tests/scripts/test_rebuild_projection_cli.py` | CLI tests: exit codes, --help, --mode DRY_RUN/APPLY with mock. |

---

## 6. Test plan

- **Unit (rebuild_engine):**
  - Given empty event store → 0 events processed, no errors.
  - Given N events, DRY_RUN → no calls to `projector.handle()`, count = N.
  - Given N events, APPLY → each event passed to each selected projector once, batch commits.
  - Given `--max-events 5` → only 5 events processed, then stop.
  - Given `--from-ts T` → only events with `ts >= T` are streamed (mock event store).
  - On projector exception in APPLY → transaction rolled back, process exits with non-zero, summary shows error.
- **CLI:**
  - `--help` prints usage and options.
  - Invalid `--mode` or missing `--projection` → exit 1.
  - `--projection all` selects all registered projectors; `--projection unknown` → exit 1 or 0 with “no projectors” message.
- **Integration (optional, minimal):** One test with in-memory or test DB: append 2 events, run rebuild APPLY for one projector, assert projection table state (e.g. 2 rows or expected upsert state).

---

## 7. Safety guarantees (summary)

- **event_store:** Only read; no `append()` or any write from this tool.
- **Transactions:** One transaction per batch in APPLY; failure rolls back that batch and stops (or logs and stops).
- **Batching:** Configurable `--batch-size` to limit memory and lock duration.
- **Kill switch:** `--max-events` and/or SIGINT/SIGTERM; finish current batch and exit with summary.
- **Idempotency:** Delegated to projectors (upsert by event_id/entity key); rebuild is restartable by re-running from same parameters.

---

READY_FOR_IMPLEMENTATION
