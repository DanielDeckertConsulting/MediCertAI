---
name: gdpr-scan
description: Scans codebase for accidental PII leakage in logs, tests, docs, and error messages. Returns GDPR_OK or GDPR_BLOCKERS with exact locations. Use when backend or frontend code is touched, when healthcare mode is enabled, or when the user asks for a PII or GDPR scan.
---

# GDPR / PII Scan

Prevents accidental PII leakage into logs, tests, docs, and diagrams. Run the checks below and report **GDPR_OK** or **GDPR_BLOCKERS** with exact file paths and line references.

## When to run

- Backend or frontend code was added or modified
- Healthcare mode is enabled
- User requests a PII check or GDPR scan

## Checks

### 1. Logs

Scan for logging of:

- Real names (person names, not placeholders)
- Email addresses (except placeholders like `example@example.com`)
- Phone numbers (except placeholders like `+49-000-0000`)
- Physical addresses
- Patient notes, medical details, or other sensitive content

**Action:** Search `backend/` and `frontend/` for `log`, `logger`, `print`, `console.log`, `console.error`, etc. Inspect logged values. Redact or use opaque IDs; never log raw PII.

### 2. Tests and fixtures

- Test data and fixtures must use **placeholders only**: e.g. `user_123`, `example@example.com`, `+49-000-0000`, fake names.
- No production-like or real-person data in fixtures, snapshots, or test descriptions.

**Action:** Search `*test*`, `*spec*`, `*fixture*`, `*mock*` under `backend/` and `frontend/`. Flag any real-looking identifiers.

### 3. Docs and diagrams

- No real names, emails, phone numbers, or addresses in markdown, ADRs, or diagrams.
- Use placeholders in examples (e.g. `user_123`, `example@example.com`).

**Action:** Scan `docs/`, `*.md`, `*.mmd`. Check diagram labels and example snippets.

### 4. Error messages

- Error messages must **not echo** user input that could be PII (e.g. email, name, query string).
- Prefer generic messages or structured error codes; avoid embedding sensitive input in exception text or API error bodies.

**Action:** Search for `raise`, `HTTPException`, `error(`, `throw new Error`. Ensure messages do not include unsanitized request/input data.

## Output format

After running all checks, report exactly one of:

**GDPR_OK**

- No PII leakage found in the scanned scope.

**GDPR_BLOCKERS**

- List each finding with:
  - **Location:** `path/to/file.ext:LINE` (or line range)
  - **Category:** Logs | Tests/fixtures | Docs/diagrams | Error messages
  - **Issue:** One-line description (e.g. "Real email in log statement")
  - **Fix:** Concrete fix (e.g. "Use placeholder or redact; do not log email")

Example:

```markdown
## GDPR_BLOCKERS

| Location | Category | Issue | Fix |
|----------|----------|--------|-----|
| backend/app/api/routes_user.py:42 | Logs | Logs `user.email` on error | Log only `user_id` or redact; never log email |
| backend/tests/fixtures/users.json:3 | Tests/fixtures | Real-looking email in fixture | Replace with `example@example.com` |
```

## Scope

- **Backend/frontend touched:** Scan only files under `backend/` and `frontend/` (and docs if they reference the change).
- **Healthcare mode:** Scan full repo (backend, frontend, docs, diagrams) and apply all checks strictly.
