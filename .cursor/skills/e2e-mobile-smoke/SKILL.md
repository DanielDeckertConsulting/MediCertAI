---
name: e2e-mobile-smoke
description: Runs mobile E2E smoke tests on iPhone-like viewport for the Golden Path. Use only when flow-relevant UI changes are detected (pages, routes, Golden Path screens, navigation, forms on critical flows). Returns MOBILE_E2E_OK or MOBILE_E2E_FAIL with failing test IDs.
---

# E2E Mobile Smoke

Runs Playwright smoke tests on the Mobile Safari project to validate the Golden Path on an iPhone-like viewport.

## When to run

**Trigger only when flow-relevant UI changes are detected:**

- Pages or routes used in the Golden Path (Lead → Call → Outcome → Callback → Report)
- Navigation, layout, or key action components on critical flows
- Forms or inputs on Golden Path screens
- Changes to queues, call logic UI, outcome codes UI, or report screens

**Do not run for:**

- Backend-only changes
- Pure styling or non-interactive tweaks
- Documentation or test file changes

## Command

```bash
cd frontend && npx playwright test --project="Mobile Safari" --grep @smoke
```

If the frontend lives in `apps/web`, use:

```bash
cd apps/web && npx playwright test --project="Mobile Safari" --grep @smoke
```

## Prerequisites

- Playwright must be installed in the frontend app
- `playwright.config.*` must define a project named `"Mobile Safari"` (typically iPhone-like viewport)
- Smoke tests must be tagged with `@smoke` (e.g. `test('...', { tag: '@smoke' })`)

## Output format

Report exactly one of:

| Result | Output |
|--------|--------|
| All pass | `MOBILE_E2E_OK` |
| Some fail | `MOBILE_E2E_FAIL` and list failing test IDs (one per line) |

**Example (failure):**

```
MOBILE_E2E_FAIL

- specs/leads.spec.ts:15:1 › Lead list loads on mobile
- specs/call.spec.ts:22:1 › Outcome selection visible
```

**Example (success):**

```
MOBILE_E2E_OK
```

## Interpretation

- `MOBILE_E2E_OK`: Golden Path mobile smoke passes; no further action.
- `MOBILE_E2E_FAIL`: Investigate failing tests. Prefer minimal fixes (selectors, viewport assumptions, timing). Do not disable or skip tests to achieve OK.
