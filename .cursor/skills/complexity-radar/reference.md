# Complexity Radar – Reference

Detailed definitions and how to measure each signal. Main instructions: [SKILL.md](SKILL.md).

## Event count

- **What:** Number of distinct `event_type` values (e.g. `lead.created`, `call.ended`).
- **How:**
  - Count constants in `backend/app/domain/events/event_types.py` that are full event types (pattern `ENTITY_ACTION` or `DOMAIN.action`), excluding `ENTITY_*` only, `SOURCE_*`, `SCHEMA_VERSION`, and suffixes like `EVENT_CREATED`.
  - Or count documented event types in `docs/events.md` (one per `### event_type` or table row).
- **Entity types** are not event types; only count strings used as `event_type` in the store.

## Projection count

- **What:** Number of read-model projectors (one per aggregate or view).
- **How:** Count files matching `backend/app/domain/projections/*_projector.py` and exclude `projector_base.py` and `projector_registry.py`.
- Each file that implements a projector (handles events and updates a read model) counts as one.

## Cross-layer changes

- **Layers:** API (`backend/app/api/`), domain (`backend/app/domain/`), services (`backend/app/services/`), projections (inside `domain/projections/`), frontend (`frontend/src/`).
- **Same feature:** Changes in the same PR/branch that implement one user-facing capability or one event flow (e.g. “mandate intake” touching routes, event types, mandate projector, and React components).
- **Count:** How many of these layers are touched for that single feature? 1–2 = LOW, 3 = MEDIUM, 4+ = HIGH.

## Branch size

- **Small:** Few files, few new event types/projectors, single concern.
- **Medium:** ~10–25 changed files, or 1–2 new event families / projectors.
- **Large:** Many files (e.g. 25+), multiple new event families, new projectors, new screens, or broad refactors.

Use `git diff --stat main` (or your base branch) and consider both file count and kind of change (config vs domain vs UI).

## New entity introduction

- **What:** New aggregate or new event family (new `entity_type` or a coherent set of new event types for one concept).
- **How:** New constants in `event_types.py` for entity types or event types that did not exist before; new projector file; new read-model table or documented view.
- One new entity = one new aggregate/view (e.g. “mandate” with mandate.created, mandate.stage_changed counts as one entity).

## Threshold tuning

Adjust the ranges in SKILL.md to match your process:

- **Event count:** Raise LOW ceiling (e.g. ≤20) if you expect many small events; lower (e.g. ≤12) for stricter control.
- **Projection count:** Align with “> 5 projections” in your DEV-split rule (MEDIUM at 6–8, HIGH > 8).
- **Branch size:** Use your team’s “small PR” vs “large PR” norms for file-count bands.
