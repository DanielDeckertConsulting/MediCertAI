---
name: responsive-audit
description: Enforces mobile-first usability for user-facing screens. Checks 390px viewport, touch targets, list/table mobile strategy, form usability, and loading/empty/error states. Returns RESPONSIVE_OK or RESPONSIVE_BLOCKERS with exact screen/component list. Use when frontend pages, routes, components, or UI flows are changed.
---

# Responsive Audit

Ensures mobile-first usability for all user-facing screens. Run the checks below and report **RESPONSIVE_OK** or **RESPONSIVE_BLOCKERS** with the exact screen/component list.

## When to run

- Frontend pages, routes, or components are added or modified
- UI flows or layouts change
- New user-facing screens are introduced
- User requests a responsive or mobile-first review

## Checks (all must pass)

### 1. 390px viewport

- No horizontal scrolling
- No clipped content (overflow hidden without intentional design)
- Layout uses relative units, fluid widths, or responsive breakpoints
- Images and media scale or fit within 390px width

**Action:** Inspect affected screens at 390px (iPhone 12/13/14 baseline). Search for fixed widths (px), `overflow-x: auto` on body, and content that breaks at narrow viewports.

### 2. Touch targets (44×44px minimum)

- Primary actions (buttons, links, interactive controls) meet minimum 44×44px
- Adequate spacing between touch targets to avoid mis-taps

**Action:** Check button, link, icon-button, and other primary-action components. Verify `min-height`, `min-width`, or `padding` yields at least 44×44px tap area.

### 3. Lists and tables – mobile strategy

- Tables have a mobile strategy: cards, stacked rows, or justified horizontal scroll
- Lists render correctly at 390px (no orphan columns, readable text)

**Action:** Identify table and list components. Verify responsive patterns (CSS Grid breakpoints, card layout on small screens, or documented horizontal-scroll UX).

### 4. Forms – mobile usability

- Labels visible and associated with inputs
- Adequate spacing for thumb interaction
- Error messages readable and not cut off
- Keyboard-friendly (focus order, spacing for virtual keyboard)

**Action:** Review form components. Check label/input association, error message placement, and input sizing.

### 5. Loading / empty / error states

- States are readable on 390px
- No truncated text or overlapping content
- Message and actions are accessible

**Action:** Inspect loading, empty, and error state UI in affected screens. Confirm no horizontal overflow or clipping.

## Output format

After running all checks, report exactly one of:

**RESPONSIVE_OK**

- All checks passed for the modified scope.
- Optionally list screens/components verified.

**RESPONSIVE_BLOCKERS**

- List each finding with:
  - **Screen/Component:** Path or identifier (e.g. `frontend/src/pages/LeadList.tsx`, `QueueTable`)
  - **Check:** Which check failed (1–5)
  - **Issue:** One-line description
  - **Fix:** Concrete remediation (e.g. "Add `min-height: 44px` to primary button", "Switch to card layout at 390px")

Example:

```markdown
## RESPONSIVE_BLOCKERS

| Screen/Component | Check | Issue | Fix |
|-----------------|-------|-------|-----|
| frontend/src/pages/Queue.tsx | 1 | Horizontal scroll at 390px due to fixed table columns | Add card layout below 768px breakpoint |
| frontend/src/components/SubmitButton.tsx | 2 | Touch target 32×32px | Set min-height/min-width 44px or padding to achieve 44×44 |
| frontend/src/pages/ReportForm.tsx | 4 | Error text clipped on narrow viewport | Use word-break or wrap; ensure error area has min-width |
```

## Scope

- **Frontend touched:** Audit only files under `frontend/` that were added or modified (pages, routes, components, shared UI).
- **Full audit:** If requested, run across all user-facing screens.
