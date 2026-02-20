# Manual Test Plan: Folder Management (Ordner Verwaltung & Chat-Zuordnung)

**Feature Branch:** `feature/folder-management`  
**Related Ticket:** [FOLDER_MANAGEMENT_TICKET.md](./FOLDER_MANAGEMENT_TICKET.md)

---

## Test Environment

- **Viewport:** Desktop (1280×720), Mobile 390px (Golden Path)
- **Auth:** Therapist role, tenant isolation enforced
- **Prerequisites:** Backend running, valid session, RLS enabled

---

## Test Cases

### Happy Path

| ID | Title | Preconditions | Steps | Expected Results | Related AC |
|----|-------|---------------|-------|------------------|------------|
| **TC-FOLDER-001** | Create folder (happy path) | Therapist logged in, at Chat page or Folders page | 1. Click "Ordner erstellen" or equivalent<br>2. Enter name "EMDR Fälle"<br>3. Submit | Folder appears in sidebar immediately; `folder.created` event emitted; folder persists after reload | AC-01 |
| **TC-FOLDER-002** | Assign chat to folder | Chat exists (Unfiled), folder exists | 1. Open chat<br>2. Open "Ordner auswählen" dropdown<br>3. Select folder "EMDR Fälle" | Chat moves to folder list; disappears from Unfiled; `chat.folder_changed` emitted; no page reload; optimistic update | AC-04 |
| **TC-FOLDER-003** | Filter chats by folder | Folders and chats exist | 1. Click folder "EMDR Fälle" in sidebar<br>2. Observe chat list | Only chats in that folder shown; "Unfiled" section always visible; filter persists while folder selected | AC-06 |
| **TC-FOLDER-004** | Rename folder | Folder exists | 1. Open folder context menu or inline edit<br>2. Change name from "EMDR Fälle" to "EMDR Fälle 2025"<br>3. Save | New name appears immediately; `folder.renamed` event emitted; no impact on assigned chats | AC-07 |
| **TC-FOLDER-005** | Delete folder — chats move to Unfiled | Folder exists with ≥1 assigned chat | 1. Delete folder (confirm if prompted)<br>2. Check chat list under Unfiled | All chats move to Unfiled; folder hard deleted; `folder.deleted` emitted; audit log entry (folder_id only, no name) | AC-08 |
| **TC-FOLDER-006** | Unfiled default for new chat | Therapist logged in | 1. Create new chat (+ Neuer Chat)<br>2. Do not assign folder | Chat has folder_id = null; appears under "Unfiled" | AC-05 |

---

### Validation

| ID | Title | Preconditions | Steps | Expected Results | Related AC |
|----|-------|---------------|-------|------------------|------------|
| **TC-FOLDER-007** | Folder name required (empty) | At create-folder form | 1. Leave name empty<br>2. Submit | Validation error shown; no folder created; no `folder.created` event | AC-02 |
| **TC-FOLDER-008** | Folder name whitespace only | At create-folder form | 1. Enter "   " (spaces/tabs)<br>2. Submit | Validation error shown; no folder created | AC-02 |
| **TC-FOLDER-009** | Duplicate folder name per tenant | Folder "EMDR Fälle" already exists for tenant | 1. Create folder with same name "EMDR Fälle"<br>2. Submit | 409 or 400 validation error; no folder created | AC-03 |

---

### API Contract

| ID | Title | Preconditions | Steps | Expected Results | Related AC |
|----|-------|---------------|-------|------------------|------------|
| **TC-FOLDER-010** | PATCH chat with folder_id | Chat + folder exist (same tenant) | 1. Send PATCH /chats/{id} with body `{ folder_id: "<folder_uuid>" }`<br>2. Verify response | Chat updated; 200 OK; `chat.folder_changed` emitted | AC-10 |
| **TC-FOLDER-011** | GET /chats?folder_id filter | Chats in various folders | 1. GET /chats?folder_id={uuid}<br>2. GET /chats (omit folder_id)<br>3. GET /chats?folder_id= (null/Unfiled per spec) | Only chats in that folder returned; filter works; Unfiled returned when folder_id=null | AC-11 |

---

### Cross-Tenant

| ID | Title | Preconditions | Steps | Expected Results | Related AC |
|----|-------|---------------|-------|------------------|------------|
| **TC-FOLDER-012** | Cross-tenant folder access (UI assign) | User A (tenant A) has folder; User B (tenant B) logged in | 1. User B tries to assign chat to tenant A's folder (e.g. via manipulated dropdown)<br>2. Submit | 403 or 404; RLS prevents access; no assignment; user sees error | AC-09 |
| **TC-FOLDER-013** | Cross-tenant folder access (API direct) | User A folder UUID known; User B (tenant B) has valid token | 1. User B: PATCH /chats/{id} with tenant A folder_id<br>2. User B: GET /folders (or access folder by ID) | 403 or 404; RLS blocks; no data leakage | AC-09 |

---

### Empty / Loading / Error States

| ID | Title | Preconditions | Steps | Expected Results | Related AC |
|----|-------|---------------|-------|------------------|------------|
| **TC-FOLDER-014** | Loading state | User opens sidebar / folder list | 1. Trigger folder list load (throttle network if needed)<br>2. Observe UI | Loading spinner or skeleton; no blank/white area | AC-12 |
| **TC-FOLDER-015** | Empty state (no folders) | New user, no folders created | 1. Open folder list / sidebar | "No folders yet" (or equivalent) message; option to create first folder; no blank area | AC-12 |
| **TC-FOLDER-016** | Error state with retry | API unreachable or 500 | 1. Simulate fetch failure for folders<br>2. Open sidebar | Error message shown; retry option present; no crash | AC-12 |

---

### Mobile (390px Golden Path)

| ID | Title | Preconditions | Steps | Expected Results | Related AC |
|----|-------|---------------|-------|------------------|------------|
| **TC-FOLDER-017** | Mobile folder drawer / list | Viewport 390px | 1. Open app at 390px<br>2. Open folder list/drawer | Folder list mobile-friendly; no horizontal scroll; drawer/sheet pattern if applicable | AC-13 |
| **TC-FOLDER-018** | Mobile touch targets | Viewport 390px | 1. Open folder list<br>2. Tap folder item, create button, assign dropdown | All primary actions ≥44×44px touch target; no overlap; tappable | AC-13 |
| **TC-FOLDER-019** | Mobile full flow | Viewport 390px | 1. Create folder<br>2. Assign chat to folder<br>3. Filter by folder | Full Golden Path works on mobile; no layout breaks | AC-13, AC-04, AC-06 |

---

### Edge Cases

| ID | Title | Preconditions | Steps | Expected Results | Related AC |
|----|-------|---------------|-------|------------------|------------|
| **TC-FOLDER-020** | Delete folder with multiple chats | Folder has 3+ chats | 1. Delete folder<br>2. Confirm | All chats move to Unfiled; `folder.deleted` with `chats_moved` count; audit log | AC-08 |
| **TC-FOLDER-021** | No folders exist — new user | New tenant, no folders | 1. Open Chat page<br>2. Create chat<br>3. Try to assign folder | Unfiled works; "Create folder" or empty dropdown; no crash | AC-05, AC-12 |
| **TC-FOLDER-022** | Unassign chat (move to Unfiled) | Chat in folder | 1. Select "Unfiled" or clear folder assignment | Chat moves to Unfiled; `chat.folder_changed` with new_folder_id: null | AC-04 |
| **TC-FOLDER-023** | Optimistic UI — network failure | Assign chat to folder | 1. Assign chat<br>2. Simulate network error on PATCH | Optimistic update reverts or error shown; state consistent; retry possible | AC-04 |
| **TC-FOLDER-024** | Folder count optional | Folders with chats | 1. View folder list with count feature (if implemented) | Count shown per folder; no errors if not implemented (non-blocking) | AC-14 |
| **TC-FOLDER-025** | Delete empty folder | Folder has 0 chats | 1. Delete folder | Folder removed; no errors; `folder.deleted` with chats_moved: 0 | AC-08 |

---

## Edge Case Matrix

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty folder name | Validation error, no create (AC-02) |
| Whitespace-only name | Validation error, no create (AC-02) |
| Duplicate name (same tenant) | 409/400, no create (AC-03) |
| Cross-tenant folder_id in PATCH | 403/404, no assignment (AC-09) |
| Delete folder with chats | Chats → Unfiled, hard delete, audit (AC-08) |
| Delete empty folder | Hard delete, no side-effect on chats |
| No folders at all | Empty state, Unfiled only (AC-12) |
| Network error on folder fetch | Error + retry (AC-12) |
| Network error on assign | Optimistic rollback or error + retry |
| GET /chats?folder_id=invalid_uuid | 400 or empty list (per API spec) |
| PATCH chat folder_id to non-existent folder | 404, no assignment |

---

## Flow List (Documentation Agent / Sequence Diagrams)

Structured steps for generating sequence diagrams. Format: **Actor → Action → System Response → Event**.

### Flow 1: Create Folder
1. **User** → Clicks "Ordner erstellen"
2. **User** → Enters name "EMDR Fälle", submits
3. **API** → POST /folders { name }
4. **DB** → Insert folder (tenant_id from auth)
5. **API** → Return 201 + folder
6. **Event** → folder.created { folder_id, name }
7. **UI** → Show folder in sidebar

### Flow 2: Assign Chat to Folder
1. **User** → Opens chat, selects folder from "Ordner auswählen"
2. **UI** → Optimistic update (chat appears in folder list)
3. **API** → PATCH /chats/{id} { folder_id }
4. **DB** → Update chats.folder_id (tenant check)
5. **API** → Return 200
6. **Event** → chat.folder_changed { old_folder_id, new_folder_id, chat_id }
7. **UI** → Confirm or rollback on error

### Flow 3: Filter Chats by Folder
1. **User** → Clicks folder in sidebar
2. **UI** → Set filter state
3. **API** → GET /chats?folder_id={uuid} (or client-side filter if preloaded)
4. **API** → Return filtered chats
5. **UI** → Show only chats in folder; Unfiled always visible

### Flow 4: Rename Folder
1. **User** → Triggers rename (inline edit or modal)
2. **User** → Enters new name, saves
3. **API** → PATCH /folders/{id} { name }
4. **DB** → Update folders.name (RLS)
5. **API** → Return 200
6. **Event** → folder.renamed { old_name, new_name, folder_id }
7. **UI** → Update folder label

### Flow 5: Delete Folder
1. **User** → Clicks delete on folder (with optional confirmation)
2. **API** → DELETE /folders/{id}
3. **DB** → Set chats.folder_id = null for that folder; DELETE folder
4. **API** → Return 204
5. **Event** → folder.deleted { folder_id, chats_moved } (no name)
6. **Audit** → Log folder_id only (no PII)
7. **UI** → Remove folder; show chats under Unfiled

### Flow 6: Cross-Tenant Denial
1. **User B (tenant B)** → Attempts PATCH /chats/{id} with folder_id from tenant A
2. **API** → Validate folder tenant
3. **API** → Return 403 or 404
4. **UI** → Show error; no assignment

---

## How to Test

1. **Desktop:** Use default viewport; run TC-FOLDER-001 through TC-FOLDER-016, TC-FOLDER-020–025.
2. **Mobile:** Resize to 390px or use DevTools device mode; run TC-FOLDER-017–019.
3. **Cross-tenant:** Use two tenants (e.g. test tenants A/B); run TC-FOLDER-012, TC-FOLDER-013.
4. **API:** Use curl/Postman for TC-FOLDER-010, TC-FOLDER-011, TC-FOLDER-013.
5. **Events:** Verify event emission via event store or logs (folder.created, folder.renamed, folder.deleted, chat.folder_changed).
6. **Audit:** After TC-FOLDER-005/020, verify audit log contains folder_id only (no folder name).

---

## Impact Summary

| Path | Impact |
|------|--------|
| Golden Path (Chat → Assign → Filter) | MEDIUM |
| New user (no folders) | LOW |
| Cross-tenant | HIGH (security) |
| Mobile 390px | MEDIUM |
