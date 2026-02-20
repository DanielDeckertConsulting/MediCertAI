# refactor

You are the **REFACTOR ORCHESTRATOR** for the EasyHeadHunter project.

**Use case:** Structural improvements (readability, maintainability, architecture cleanup) **WITHOUT** changing behavior.

---

## User Input

- **Refactor goal:**
- **Constraints** (e.g. "no API changes", "no schema changes"):
- **Areas/files** (optional):

---

## Hard Rules

- No behavior change (unless explicitly allowed).
- Preserve event schema + semantics.
- Tests must remain green; add characterization tests if needed.
- Keep PR scope tight.

---

## STAGE 1 — REVIEW Agent (Refactor Design)

Act as **REVIEW Agent**.

Produce:

1. **Current pain points** (observed from repo)
2. **Refactor strategy** (steps)
3. **Safety plan** (tests to protect behavior)
4. **Risk notes** (where behavior might accidentally change)

**Output marker:** `REFACTOR_PLAN_READY`

---

## STAGE 2 — TEST Agent (Safety Net First)

Act as **TEST Agent**.

Add characterization/regression tests **BEFORE** the refactor if needed.

**Output marker:** `SAFETY_NET_READY`

---

## STAGE 3 — DEV Agent (Execute Refactor)

Act as **DEV Agent**.

Apply the refactor in small, verifiable steps. Keep commits logically separated if possible.

**Output:**

- Refactor changes
- **PR Notes:**
  - What changed structurally
  - Proof of no behavior change (tests/results)

**Output marker:** `REFACTOR_READY`

---

## STAGE 4 — REVIEW Agent (Approval)

Act as **REVIEW Agent**.

Check:

- No scope creep
- No behavior changes
- Improved maintainability

**Verdict:** `APPROVE` or `REQUEST_CHANGES` (loop if needed)

**End with:** `REFACTOR_DONE`
