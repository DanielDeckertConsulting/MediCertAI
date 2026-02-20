# Ticket: Ordner Verwaltung & Chat-Zuordnung

**Branch:** `feature/folder-management`
**PR Title:** feat: Folder CRUD, chat assignment, filter by folder

---

## Feature Rephrase

As a therapist, I want to create folders, assign chats to folders, and filter chats by folder so that I can organize my conversations by patient or case.

---

## Success Metrics (max 3)

1. Therapists can create, rename, delete folders and assign chats without errors
2. Cross-tenant folder access returns 403/404
3. Audit log records folder deletes; no PII in logs

---

## Scope (Phase 1)

- Create folders (name required, unique per tenant)
- Assign chat to exactly one folder (or Unfiled = folder_id null)
- Filter chats by folder in sidebar
- Rename / delete folder (chats → Unfiled on delete)
- RLS on folders; tenant isolation enforced
- Optimistic UI for chat assignment
- Mobile-first sidebar + folder drawer

---

## Out of Scope (Phase 2+)

- Nested folders
- Multi-label tagging (chat in multiple folders)
- Folder sharing across tenants/users
- Color coding
- Folder drag-and-drop reorder

---

## Assumptions

- Single DB + RLS; no new Azure components
- Auth middleware sets `app.tenant_id` (existing)
- `chats.folder_id` already exists (nullable); need `folders` table + FK
- API uses "chats" (not "conversations") for consistency with codebase

---

## Domain Events

| Event | Entity | Payload (example) |
|-------|--------|-------------------|
| folder.created | folder | `{"name": "EMDR Fälle", "folder_id": "uuid"}` |
| folder.renamed | folder | `{"old_name": "...", "new_name": "...", "folder_id": "uuid"}` |
| folder.deleted | folder | `{"folder_id": "uuid", "chats_moved": 3}` (no PII; no folder name) |
| chat.folder_changed | chat | `{"old_folder_id": "uuid" \| null, "new_folder_id": "uuid" \| null, "chat_id": "uuid"}` |

---

## Minimal API Contract

**Folders:**
```
GET    /folders                    → list folders (tenant-scoped)
POST   /folders                    → create folder (body: { name })
PATCH  /folders/{id}               → rename (body: { name })
DELETE /folders/{id}                → delete; chats → Unfiled
```

**Chats:**
```
GET    /chats?folder_id=...        → filter by folder (null = Unfiled)
PATCH  /chats/{id}                 → add folder_id | null to PatchChatBody
```

Validation: folder_id must belong to same tenant; 403 if cross-tenant.

---

## Compliance Hotspots

| Hotspot | Handling |
|---------|----------|
| Folder names may contain PII | No folder name in audit logs; log folder_id only |
| Cross-tenant | RLS + API validation |
| Chat assignment | Same-tenant folder check |

---

## Acceptance Criteria (Given/When/Then)

**Golden Path impact:** MEDIUM — extends existing chat flow with folder assignment + filter.

### AC-01: Create folder (happy path)
**Given** a therapist is logged in **When** they create a folder with a non-empty name **Then** the folder appears in the sidebar immediately and a `folder.created` event is emitted.

### AC-02: Folder name required
**Given** a therapist is on the create-folder form **When** they submit without a name (or empty/whitespace) **Then** validation error is shown and no folder is created.

### AC-03: Folder unique per tenant
**Given** a folder named "EMDR Fälle" already exists for the tenant **When** the therapist creates another folder with the same name **Then** a 409 (or 400) validation error is returned and no folder is created.

### AC-04: Assign chat to folder
**Given** a chat exists and a folder exists **When** the user selects the folder from the "Ordner auswählen" dropdown **Then** the chat is assigned, appears in that folder's list, disappears from Unfiled, and `chat.folder_changed` is emitted. Update is optimistic (no page reload).

### AC-05: Unfiled default
**Given** a new chat is created **When** no folder is selected **Then** the chat has folder_id = null and appears under "Unfiled".

### AC-06: Filter chats by folder
**Given** folders and chats exist **When** the user clicks a folder in the sidebar **Then** only chats in that folder are shown. "Unfiled" is always visible.

### AC-07: Rename folder
**Given** a folder exists **When** the user renames it **Then** the new name appears immediately and `folder.renamed` is emitted.

### AC-08: Delete folder — chats move to Unfiled
**Given** a folder with chats exists **When** the user deletes the folder **Then** all chats move to Unfiled, folder is hard deleted, `folder.deleted` and audit log entry (folder_id only, no name) are created.

### AC-09: Cross-tenant folder access
**Given** user A (tenant A) has a folder **When** user B (tenant B) tries to assign a chat to that folder (or access it via API) **Then** 403 or 404 is returned; RLS prevents access.

### AC-10: PATCH chat with folder_id
**Given** a chat and folder exist (same tenant) **When** client sends PATCH /chats/{id} with folder_id **Then** chat is updated and `chat.folder_changed` is emitted.

### AC-11: GET /chats?folder_id filter
**Given** chats exist in various folders **When** client calls GET /chats?folder_id={uuid} **Then** only chats in that folder are returned. folder_id=null or omitted returns all (or Unfiled per spec).

### AC-12: Empty/loading/error states
**Given** user opens sidebar or folder list **When** folders are loading, empty, or fetch fails **Then** loading spinner, "No folders yet" message, or error message with retry option are shown (no blank/white area).

### AC-13: Mobile folder drawer
**Given** user is on 390px viewport **When** they open folders **Then** folder list/drawer is mobile-friendly (no horizontal scroll, 44px touch targets).

### AC-14: Folder count optional
**Given** folders exist **When** optionally displayed **Then** folder shows count of chats inside (non-blocking for MVP).

### Annahmen
- Auth middleware sets tenant_id; RLS enforced.
- One folder per chat (no multi-label).
- Event store is append-only; no projection rebuild required for MVP (direct DB reads).

### Out-of-Scope
- Nested folders, multi-label, folder sharing, color coding, drag-and-drop reorder.

---

## Manual Test Plan

See **[FOLDER_MANAGEMENT_MANUAL_TESTS.md](./FOLDER_MANAGEMENT_MANUAL_TESTS.md)** for:

- **TC-FOLDER-001** to **TC-FOLDER-025**: Preconditions, steps, expected results, Related AC
- **Edge case matrix**: Validation, cross-tenant, delete, network errors
- **Flow list**: User → API → Event sequences for Documentation Agent (sequence diagrams)
