# Manual Test Plan: Mobile-First UI for MentalCarePilot

**Feature:** Mobile-first UI for MentalCarePilot (Chat, Folders, Assistenzmodus, Admin)  
**Target breakpoints:** 390px (phone), 768px (tablet), desktop  
**Test case ID format:** TC-MOBILE-NNN

---

## Acceptance Criteria Mapping

| AC ID | Description |
|-------|-------------|
| AC-01 | On 390px width, core workflows usable: navigate to Chat/Folders/Assist/Admin, open chat detail, primary actions (create chat, send message) |
| AC-02 | Chat list mobile-friendly (cards or stacked list) |
| AC-03 | Chat detail mobile-friendly: messages readable, input accessible (sticky bar allowed) |
| AC-04 | No horizontal scrolling on mobile/tablet |
| AC-05 | Touch targets 44x44px for primary actions |
| AC-06 | Loading/empty/error states readable on mobile |
| AC-07 | Desktop layout preserved |

---

## 1. Manual Test Cases

### TC-MOBILE-001 — Happy Path: Core Workflows at 390px (Phone)

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-001 |
| **Preconditions** | User is logged in. DevTools responsive mode or real device at 390px width. Backend running. |
| **Steps** | 1. Resize viewport to 390px (or use device emulation). 2. From app shell, tap "Chat". 3. Tap "Ordner". 4. Tap "Assistenzmodus". 5. Tap "Admin". 6. Return to Chat. 7. Tap "Neuer Chat" (or "+ Neuer Chat"). 8. Verify new chat opens. 9. Enter text in message input. 10. Tap "Senden". |
| **Expected results** | All nav items (Chat, Ordner, Assistenzmodus, Admin, Ping) accessible. Navigation works without horizontal scroll. New chat creates and opens. Message sends successfully. No layout overflow. |
| **Related AC** | AC-01, AC-04 |

---

### TC-MOBILE-002 — Chat List Mobile Layout (Cards/Stacked)

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-002 |
| **Preconditions** | User logged in. 390px viewport. At least 3 chats in list. |
| **Steps** | 1. Navigate to Chat page. 2. Inspect chat list. 3. Verify each chat is displayed as a card or stacked row. 4. Scroll the list vertically. 5. Tap a chat to open detail. |
| **Expected results** | Chat list shows cards or vertically stacked entries (not a cramped table). Each entry is tappable. Scrolling is vertical only. Tapping opens chat detail. No horizontal scroll. |
| **Related AC** | AC-02, AC-04 |

---

### TC-MOBILE-003 — Chat Detail Mobile: Messages and Input

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-003 |
| **Preconditions** | User logged in. 390px viewport. Chat with messages selected. |
| **Steps** | 1. Open a chat with at least 2 messages. 2. Scroll through messages. 3. Verify message text is readable (no tiny font, no truncation unless intended). 4. Locate message input. 5. Verify input is accessible without scrolling past it (or sticky at bottom). 6. Focus input and type. 7. Tap Senden. |
| **Expected results** | Messages readable. Input visible and accessible (sticky bar allowed). No horizontal scroll in message area. Send action works. |
| **Related AC** | AC-03 |

---

### TC-MOBILE-004 — No Horizontal Scrolling on Mobile (390px)

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-004 |
| **Preconditions** | 390px viewport. User on Chat, Folders, Assistenzmodus, Admin, Ping pages. |
| **Steps** | 1. Visit Chat page. Swipe/scroll horizontally. 2. Visit Folders page. Swipe horizontally. 3. Visit Assistenzmodus. Swipe horizontally. 4. Visit Admin. Swipe horizontally. 5. Visit Ping. Swipe horizontally. 6. With chat selected, scroll messages. 7. Open sidebar/drawer (if implemented) and check for horizontal scroll. |
| **Expected results** | No horizontal overflow or scroll. Content fits within viewport width. `overflow-x: hidden` or equivalent prevents horizontal scroll. |
| **Related AC** | AC-04 |

---

### TC-MOBILE-005 — Touch Targets 44x44px for Primary Actions

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-005 |
| **Preconditions** | 390px viewport. DevTools "Show rulers" or measuring tool available. |
| **Steps** | 1. Measure "Neuer Chat" / "+ Neuer Chat" button. 2. Measure "Senden" button. 3. Measure nav links (Chat, Ordner, Assistenzmodus, Admin, Ping). 4. Measure chat list item tap area. 5. Measure Assistenzmodus selector and Anonymisieren checkbox (primary interaction). 6. Measure edit/delete/favorite/export icons on chat items. |
| **Expected results** | Primary actions (create chat, send, nav items, chat selection) have min 44x44px touch target. Secondary actions (edit, delete, favorite, export) ideally 44x44px or clearly tappable. No overlapping targets. |
| **Related AC** | AC-05 |

---

### TC-MOBILE-006 — Loading State Readable on Mobile

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-006 |
| **Preconditions** | 390px viewport. Network throttling (Slow 3G) or backend delayed. |
| **Steps** | 1. Navigate to Chat. 2. Observe loading state for chat list. 3. Open a chat. 4. Observe loading state for messages. 5. Send message. 6. Observe streaming/loading state. |
| **Expected results** | Loading states (spinner, skeleton) visible and readable. No blank white area for >1s. Loader fits viewport. Text legible. |
| **Related AC** | AC-06 |

---

### TC-MOBILE-007 — Empty State Readable on Mobile

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-007 |
| **Preconditions** | 390px viewport. Fresh user or cleared chats. |
| **Steps** | 1. Navigate to Chat with no chats. 2. Observe empty list state. 3. Open a new chat with no messages. 4. Observe empty message area. |
| **Expected results** | "Keine Chats. Erstellen Sie einen neuen." (or equivalent) visible and legible. "Wählen Sie einen Chat oder erstellen Sie einen neuen." / "Schreiben Sie eine Nachricht, um zu beginnen." clear. CTA (e.g. "Neuer Chat") visible and tappable. |
| **Related AC** | AC-06 |

---

### TC-MOBILE-008 — Error State Readable on Mobile

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-008 |
| **Preconditions** | 390px viewport. Backend stopped or network offline. |
| **Steps** | 1. Load Chat page with backend unreachable. 2. Observe error banner. 3. Verify message legibility. 4. Trigger send with backend down (if applicable). 5. Check for alert/toast. |
| **Expected results** | Error message (e.g. "API nicht erreichbar...") visible, readable, no horizontal overflow. No stack trace. User-readable text. Retry possible if implemented. |
| **Related AC** | AC-06 |

---

### TC-MOBILE-009 — Desktop Layout Preserved

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-009 |
| **Preconditions** | Desktop viewport (e.g. 1280px or larger). |
| **Steps** | 1. Load app at 1280px width. 2. Verify sidebar nav visible. 3. Verify Chat page shows left chat list sidebar + main area. 4. Verify all pages (Folders, Assistenzmodus, Admin, Ping) render correctly. 5. Verify no mobile-only layout (e.g. hamburger replacing sidebar) unless breakpoint spec says so. |
| **Expected results** | Sidebar + main content layout as before. Chat list sidebar (w-64) visible. Two-column Chat layout. No regression. |
| **Related AC** | AC-07 |

---

### TC-MOBILE-010 — 768px Tablet Viewport

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-010 |
| **Preconditions** | 768px viewport. |
| **Steps** | 1. Resize to 768px. 2. Navigate all main sections (Chat, Folders, Assistenzmodus, Admin). 3. Open chat, send message. 4. Check for horizontal scroll. 5. Verify nav and primary actions usable. |
| **Expected results** | Layout suitable for tablet. No horizontal scroll. Core workflows usable. Either: sidebar collapsed to icons/hamburger, or layout adapts gracefully. Touch targets adequate. |
| **Related AC** | AC-01, AC-04 |

---

### TC-MOBILE-011 — Edge Case: Empty Chat List on Mobile

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-011 |
| **Preconditions** | 390px viewport. User has zero chats. |
| **Steps** | 1. Navigate to Chat. 2. Observe empty list. 3. Tap "Neuer Chat" (or equivalent). 4. Verify new chat created and opened. |
| **Expected results** | Empty state message visible. CTA works. No layout overflow. New chat opens in detail view. |
| **Related AC** | AC-02, AC-06 |

---

### TC-MOBILE-012 — Edge Case: Long Message Text

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-012 |
| **Preconditions** | 390px viewport. Chat with very long message (e.g. 500+ chars, no line breaks). |
| **Steps** | 1. Open chat with long message. 2. Inspect message bubble. 3. Check for horizontal overflow. 4. Verify text wraps. |
| **Expected results** | Message wraps within viewport. No horizontal scroll. Text readable. `whitespace-pre-wrap` or similar applied. |
| **Related AC** | AC-03, AC-04 |

---

### TC-MOBILE-013 — Edge Case: Sidebar/Nav Toggle (if hamburger on mobile)

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-013 |
| **Preconditions** | 390px viewport. App uses collapsible sidebar or bottom nav on mobile. |
| **Steps** | 1. Verify nav accessible (hamburger or bottom nav). 2. Open nav. 3. Navigate to each section. 4. Close nav. 5. Verify content area uses full width when nav closed. |
| **Expected results** | Nav toggle works. All sections reachable. No layout shift issues. Content area maximizes when nav hidden. |
| **Related AC** | AC-01 |

---

### TC-MOBILE-014 — Search/Create Actions on Mobile

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-014 |
| **Preconditions** | 390px viewport. Several chats in list. |
| **Steps** | 1. Locate "Chats durchsuchen..." search input. 2. Tap and type search term. 3. Verify filtered results. 4. Tap "+ Neuer Chat". 5. Verify new chat created. |
| **Expected results** | Search input usable (min 44px height). Filter works. Create chat works. No overlap with other controls. |
| **Related AC** | AC-01, AC-05 |

---

### TC-MOBILE-015 — Assistenzmodus and Anonymize Controls on Mobile

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-015 |
| **Preconditions** | 390px viewport. Chat selected. |
| **Steps** | 1. Locate Assistenzmodus dropdown. 2. Change selection. 3. Locate Anonymisieren checkbox. 4. Toggle. 5. Verify controls don’t overflow or clip. |
| **Expected results** | Dropdown and checkbox tappable (44x44px). Controls readable. No horizontal overflow. Warning text ("Vermeiden Sie personenbezogene Angaben...") visible when anonymization off. |
| **Related AC** | AC-05, AC-06 |

---

### TC-MOBILE-016 — Golden Path on 390px End-to-End

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-016 |
| **Preconditions** | 390px viewport. User logged in. Backend running. |
| **Steps** | 1. Open Chat. 2. Create new chat. 3. Select Assistenzmodus. 4. Type message. 5. Send. 6. Wait for response. 7. Navigate to Folders. 8. Navigate to Assistenzmodus. 9. Navigate to Admin. |
| **Expected results** | Full flow completable on phone viewport. No blocking issues. Navigation, create, send, read—all work. |
| **Related AC** | AC-01, AC-02, AC-03 |

---

### TC-MOBILE-017 — Ping Page Loading/Error on Mobile

| Field | Content |
|-------|---------|
| **Test case ID** | TC-MOBILE-017 |
| **Preconditions** | 390px viewport. |
| **Steps** | 1. Navigate to Ping. 2. Observe loading ("Laden..."). 3. With backend up: verify JSON display. 4. With backend down: verify error message. |
| **Expected results** | Loading and error states readable. No horizontal scroll. JSON or error fits viewport. |
| **Related AC** | AC-06 |

---

## 2. Edge Case Matrix

| ID | Edge Case | Viewport | Expected Behavior |
|----|-----------|----------|-------------------|
| E1 | Empty chat list | 390px | Empty state + CTA, no crash |
| E2 | Error state (API down) | 390px | Error banner readable, no overflow |
| E3 | Long message text (500+ chars) | 390px | Text wraps, no horizontal scroll |
| E4 | Many chats (50+) | 390px | List scrolls vertically, no perf issue |
| E5 | Long chat title | 390px | Truncated with ellipsis, tappable |
| E6 | Streaming response | 390px | Streaming visible, input accessible |
| E7 | Keyboard open (mobile) | 390px | Input remains visible or sticky |
| E8 | Dark mode | 390px | Contrast OK, no overflow |
| E9 | Very narrow (320px) | 320px | Layout degrades gracefully or spec defines min width |
| E10 | Rotate device (portrait ↔ landscape) | 390px ↔ 844px | Layout adapts, no broken state |
| E11 | Search with no matches | 390px | Empty filter state clear |
| E12 | Edit chat title inline | 390px | Input usable, save/cancel clear |
| E13 | Rapid tap on Send | 390px | No duplicate sends (or loading prevents) |
| E14 | Placeholder pages (Folders, Assist, Admin) | 390px | Heading + text readable, no overflow |

---

## 3. Error / Empty / Loading State Expectations

| Scenario | UX Requirement (Mobile) |
|----------|-------------------------|
| **Loading chat list** | Skeleton or spinner, min 44px, centered or inline |
| **Loading chat detail** | Skeleton or spinner, no blank area >1s |
| **Empty chat list** | "Keine Chats. Erstellen Sie einen neuen." + CTA |
| **Empty message area** | "Schreiben Sie eine Nachricht, um zu beginnen." |
| **No chat selected** | "Wählen Sie einen Chat oder erstellen Sie einen neuen." + CTA |
| **API error** | User-readable message, no stack trace, fits viewport |
| **Stream error** | Partial text + error banner, retry if available |
| **Search no results** | Clear "Keine Treffer" or similar |
| **Disabled Send** | Visual disabled state, min 44px for touch |

---

## 4. Not Testable / Needs Instrumentation

| Item | Note |
|------|------|
| Touch target pixel measurement | Manual or DevTools; automated pixel check needs visual regression |
| Real device rotation | Best on physical device; emulator may differ |
| Actual touch vs click | Some issues only on real touch (e.g. hover states) |
| Performance (50+ chats) | May need profiling; manual scroll test for jank |
| Accessibility (screen reader) | Separate a11y test plan |

---

## 5. Flow List (for Documentation Agent)

Use these flows to generate sequence diagrams (e.g. Mermaid/PlantUML).

### Flow 1: Mobile Navigation (390px)

1. User opens app at 390px
2. Frontend renders layout (sidebar/bottom nav/hamburger per spec)
3. User taps nav item (e.g. Chat)
4. Frontend navigates to route
5. Page loads (ChatPage / FoldersPage / etc.)
6. User sees content, no horizontal scroll

### Flow 2: Create Chat on Mobile

1. User on Chat page at 390px
2. User taps "+ Neuer Chat"
3. Frontend calls `createChat()` API
4. Backend creates chat, returns ID
5. Frontend navigates to `/chat/:id`
6. Chat detail loads, empty state shown

### Flow 3: Send Message on Mobile

1. User has chat open at 390px
2. User types in input, taps "Senden"
3. Frontend validates (non-empty, not streaming)
4. Frontend calls `streamChatMessage()`
5. Backend streams tokens
6. Frontend appends to UI, input stays accessible
7. On done: refetch, streaming stops

### Flow 4: Error State on Mobile

1. User on Chat at 390px
2. Backend unreachable (network/offline)
3. TanStack Query returns error
4. Frontend shows error banner
5. User sees "API nicht erreichbar..." (or equivalent)
6. No horizontal overflow

### Flow 5: Empty State on Mobile

1. User on Chat with no chats
2. `filteredChats.length === 0`
3. Frontend shows "Keine Chats. Erstellen Sie einen neuen."
4. User taps "Neuer Chat" (or equivalent)
5. Create flow executes

### Flow 6: Chat List as Cards/Stack (Mobile)

1. User on Chat at 390px
2. Chat list rendered as cards or stacked rows
3. User scrolls vertically
4. User taps chat item
5. Frontend navigates to `/chat/:id`
6. Chat detail loads

### Flow 7: Desktop Layout Preservation

1. User at 1280px viewport
2. Layout renders sidebar + main
3. Chat page: left sidebar (chat list) + main (messages)
4. No mobile-specific collapse (unless breakpoint crosses)

---

**Document version:** 1.0  
**Last updated:** 2025-02-20
