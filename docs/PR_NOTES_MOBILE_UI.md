# PR Notes: Mobile-Ready UI

## What Changed

- **Layout:** Mobile-first navigation. Hamburger menu (< 768px), fixed sidebar (≥ 768px). Overlay drawer for nav on small screens.
- **ChatPage:** On mobile: single view (list OR detail). List full-width at `/chat`; detail full-width at `/chat/:id` with back button. Desktop: two-column (list + detail) preserved.
- **Touch targets:** All primary actions use `min-h-touch` / `min-w-touch` (44px).
- **Breakpoints:** Added xs 390px to `tailwind.config.js`. `overflow-x: hidden` on body/html.
- **Pages:** FoldersPage, AssistModesPage, AdminPage, PingPage, LoginPage, ErrorBoundary: `min-w-0`, responsive padding, no horizontal scroll.
- **Loading/empty/error:** Chat list shows "Laden..." while loading. Empty/error states readable on mobile.

## How to Test

1. **Local frontend**
   ```bash
   cd apps/web && pnpm dev
   ```
   Open http://localhost:5173 (or your Vite port).

2. **Mobile (390px)**
   - DevTools → Toggle device toolbar → 390×844 (iPhone)
   - Navigate: hamburger → Chat, Ordner, Assistenzmodus, Admin, Ping
   - Chat: tap "Neuer Chat", verify chat opens; tap "← Chats" to return
   - No horizontal scroll on any page

3. **Tablet (768px)**
   - Resize to 768px. Sidebar visible. Chat: list + detail side by side.

4. **Desktop (1280px)**
   - Same as before: sidebar + main. No regression.

5. **Automated**
   ```bash
   cd apps/web && npm run test
   ./scripts/responsive-audit.sh
   ```

## Manual Test Plan

See `docs/TEST_PLAN_MOBILE_UI.md` for TC-MOBILE-001 through TC-MOBILE-017.

## Assumptions

- No backend changes; API unchanged.
- Design tokens (primary colors) kept; no new tokens.
- No new dependencies.

## Follow-ups

- Build: pre-existing Vite top-level-await error (unrelated to this PR).
- Consider: chat list skeleton instead of "Laden..."; optional card borders for list items.

## Golden Path Impact

**LOW** — UI-only; core chat flow unchanged.
