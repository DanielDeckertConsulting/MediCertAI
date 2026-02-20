---
name: golden-path-grind
description: Runs an autonomous fix-until-green loop to stabilize the Golden Path. Re-runs tests and checks until all pass or max iterations. Use after implementing a feature (#ship_feature), after refactor (#refactor), when CI is red locally, or before final review/acceptance.
---

# Golden Path Grind

Stabilizes the Golden Path by repeatedly running checks, applying minimal fixes on failure, and re-running until green or the iteration limit is reached.

## When to Use

- After implementing a feature (`#ship_feature*`)
- After refactor (`#refactor`)
- When CI is red locally
- Before final review / acceptance

## Entry Point (Preferred)

Use a single entrypoint to avoid drift:

```bash
./scripts/test.sh
```

**Fallback** if `./scripts/test.sh` is not available:

- Backend: `cd backend && python -m pytest -q`
- Frontend: `cd frontend && npm run lint && npm run build` (or `npm test` if defined)
- E2E (optional): `cd frontend && npx playwright test`

## Loop Rules

1. Run checks (prefer `./scripts/test.sh`).
2. If failing:
   - Identify minimal root cause.
   - Apply smallest possible fix.
   - Do not expand scope.
3. Re-run checks.
4. Continue until:
   - All checks pass **and** `.cursor/scratchpad.md` contains `DONE`, or
   - Max iterations reached (default 5).

## Stop Conditions

| Result | Condition |
|--------|-----------|
| **PASS** | All checks green and scratchpad contains `DONE` |
| **STOP** | Max iterations reached (default 5) |
| **STOP** | Non-recoverable (missing deps, env, etc.) |

## Hard Rules

- **No scope creep:** Fix only what is required for green state.
- **Do not disable tests** or skip them to get green.
- **Do not weaken assertions** just to make tests pass.
- **Preserve** Event-Log-first invariants and idempotent projections.
- **Never** print or store secrets; never introduce PII into logs, tests, or docs.

## Output Contract

At the end of each iteration, **append** to `.cursor/scratchpad.md`:

- Iteration number
- Commands executed
- Summary of failures
- Fixes applied
- Remaining issues (if any)

Write `DONE` in the scratchpad **only when**:

- All checks pass
- No new regressions

## Hook Integration

If `.cursor/hooks.json` configures a stop hook with `golden_grind.ts`, the agent can be driven in a loop: the hook reads the scratchpad and, until `DONE` or max iterations, injects a followup message to continue. The skill defines the behavior; the hook enforces the loop.

## Scratchpad Location

- **Path:** `.cursor/scratchpad.md`
- Updated by the agent each iteration; the hook uses it to decide whether to continue or stop.
