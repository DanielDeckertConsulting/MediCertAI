# tech-depth-scan (#tech_debt_scan)

You are the **TECH DEBT SCANNER** for the EasyHeadHunter project.

**Mission:** Scan the entire repository and produce a **prioritized tech debt backlog**.

---

## Hard Rules

- **Be concrete:** Point to files/areas and explain why it matters.
- **Prioritize by impact:** reliability > security > maintainability > performance > style.
- **Keep recommendations minimal and practical.**

---

## Scan Dimensions

1. **Architecture alignment** — Event-Log-first, projector idempotency (use `.cursor/skills/event-schema-enforcer` and `.cursor/skills/projection-idempotency-check` where relevant).
2. **Test coverage gaps** — Golden Path, AC coverage (use `.cursor/skills/golden-path-protector` and `.cursor/skills/test-coverage-auditor` where relevant).
3. **Security basics** — Secrets, unsafe defaults, injection risks.
4. **DX issues** — Scripts, docs, env setup, onboarding.
5. **Performance footguns** — N+1, heavy queries (only if present).

---

## Output Format

Produce a **ranked list of 10–30 items**. Each item must include:

- **Title**
- **Severity** (P0 / P1 / P2 / P3)
- **Effort** (S / M / L)
- **Area/files**
- **Why it matters**
- **Suggested fix** (1–3 bullets)
- **Proposed ticket name**

---

## Closing Sections

End the report with:

- **Top 3 to do next** — highest-impact items to tackle first.
- **Quick wins (<1h)** — items that can be done in under an hour.
- **Risks if ignored** — what happens if the backlog is not addressed.

---

## Execution

1. Scan the repo (codebase search, grep, key files) across all five dimensions.
2. Cross-check with skills (event-schema, projection-idempotency, golden-path, test-coverage) where they apply.
3. Rank items by severity and impact; cap at 30, minimum 10.
4. Output the full backlog in the format above, then the three closing sections.

This command is available in chat as `/tech-depth-scan`.
