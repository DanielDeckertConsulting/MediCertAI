# Export (PDF/TXT) – Manual Test Plan

**Feature:** MVP 5.2 Export – PDF and TXT per conversation  
**Date:** 2025-02-20

---

## Prerequisites

- Backend running (e.g. `uv run uvicorn app.main:app --reload` in `services/api`)
- Frontend running (e.g. `npm run dev` in `apps/web`)
- At least one chat with messages (user + assistant)

---

## Test Cases

### TC-EXPORT-001: Export PDF (Happy Path)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open a chat with messages | Chat detail loads |
| 2 | Click Export (⬇) in sidebar or in chat input area | Dropdown opens with "Export als TXT" and "Export als PDF" |
| 3 | Click "Export als PDF" | PDF downloads; filename like `mentalcarepilot-chat-<title>-<YYYY-MM-DD>.pdf` |
| 4 | Open PDF in viewer | Header: "MentalCarePilot Export", title, export date; body: messages with timestamp and role labels (Therapeut:in / KI) |
| 5 | Check UTF-8 | German umlauts (ä, ö, ü, ß) render correctly |

---

### TC-EXPORT-002: Export TXT (Happy Path)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open a chat | - |
| 2 | Click Export → "Export als TXT" | TXT file downloads |
| 3 | Open TXT | `# <title>` header; each message: `[YYYY-MM-DD HH:MM] ROLE:\n<content>` |

---

### TC-EXPORT-003: Long Messages Wrap

| Step | Action | Expected |
|------|--------|----------|
| 1 | Create chat with a long message (multi-line) | - |
| 2 | Export as PDF | PDF shows full message, wrapped; no horizontal overflow |

---

### TC-EXPORT-004: Mobile Layout

| Step | Action | Expected |
|------|--------|----------|
| 1 | Resize to 390px (iPhone baseline) | No horizontal scroll |
| 2 | Tap Export | Dropdown opens; options have ≥44px touch targets |
| 3 | Export PDF | Download works; layout unchanged |

---

### TC-EXPORT-005: Export Failure

| Step | Action | Expected |
|------|--------|----------|
| 1 | Stop backend | - |
| 2 | Click Export → PDF | Alert with error message; no crash |
| 3 | Restart backend, export again | Export works |

---

### TC-EXPORT-006: Limits (413)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Use chat with >2000 messages (or >2MB content) if feasible | Export returns 413 with user-friendly message |
| 2 | Frontend | Error alert shown |

---

### TC-EXPORT-007: Unauthorized / Not Found

| Step | Action | Expected |
|------|--------|----------|
| 1 | Call `GET /chats/<invalid-uuid>/export?format=pdf` with valid auth | 404 |
| 2 | Verify Admin Logs | `export_requested` appears only when export succeeds (metadata only, no content) |

---

## Audit Verification

After a successful export:

- Admin → Logs tab
- Filter by action: `export_requested`
- Row shows: tenant_id, actor_id, entity_type=chat, entity_id, metadata=`{"format":"pdf"}` or `{"format":"txt"}`
- **No** prompt or response content in any log field

---

## How to Test (Commands)

```bash
# Backend
cd services/api && uv run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd apps/web && npm run dev

# Unit tests
cd services/api && uv run pytest tests/test_chats.py -v -k export
```
