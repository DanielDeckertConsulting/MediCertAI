# Desktop Chat Layout - Feature Complete

## Iteration 1

**Commands executed:** `npm run build`, `npm run test`, `npm run lint`

**Summary:** All checks passed.

**Changes implemented:**
1. ChatPage desktop layout: overflow-hidden, messages area scrollable (flex-1 overflow-y-auto min-h-0), composer sticky at bottom
2. FolderGroup.tsx: collapsible folders with localStorage persistence (clinai_chat_folder_collapsed)
3. ChatList: scrollable "Alte Chats" area, collapsible folder groups when "Alle" selected
4. ChatListItem.tsx: Meatball menu (⋯) on desktop (md:), inline icons on mobile
5. handleMoveToFolder for meatball "In Ordner verschieben" with submenu
6. Delete confirm dialog in meatball menu

**How to test:**
- Desktop (≥768px): Create 200+ chats (or seed), verify message input stays visible without page scroll. Verify folder expand/collapse, meatball actions (rename, favorite, move, export, delete). Verify no horizontal overflow.
- Mobile (390px, 768px): TC-MOBILE-001, 003, 009, 010 - Golden Path unchanged, inline icons visible, no regression.
- Refresh page: folder collapsed state persists in localStorage.

**Impact:** Golden Path MEDIUM - desktop UX improved, mobile unchanged.

DONE
