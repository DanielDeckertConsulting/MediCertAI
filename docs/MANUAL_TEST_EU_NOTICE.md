# Manual Test: EU Processing Notice (4.1)

**Feature:** Visible EU Processing Notice  
**Golden Path impact:** LOW

## Prerequisites

- App running: `cd apps/web && npm run dev`
- Browser at 390px and 768px+ viewports

## Test Cases

### TC-4.1.1 Banner visible on Chat page

1. Open `/chat` (or `/chat/:id`).
2. **Expected:** Banner above message list with text "Alle Daten werden innerhalb der EU verarbeitet."
3. **Expected:** "Mehr erfahren" link and "Ausblenden" button visible.
4. **Expected:** Info icon (ℹ️) visible.

### TC-4.1.2 Responsive layout (390px)

1. Resize viewport to 390px width.
2. Open Chat page.
3. **Expected:** Banner text wraps; no horizontal scroll.
4. **Expected:** Touch targets (Mehr erfahren, Ausblenden) at least 44x44px.

### TC-4.1.3 No horizontal scroll

1. At 390px, verify no horizontal scrollbar.
2. **Expected:** All content fits within viewport width.

### TC-4.1.4 Dismiss persists across reload

1. On Chat page, click "Ausblenden".
2. **Expected:** Banner disappears.
3. Reload the page.
4. **Expected:** Banner stays hidden.

### TC-4.1.5 "Mehr erfahren" navigates to /privacy

1. Click "Mehr erfahren".
2. **Expected:** Navigate to `/privacy`.
3. **Expected:** Privacy page shows headline "Datenschutz" and section "Datenverarbeitung innerhalb der EU".
4. **Expected:** Bullet list includes Azure Germany West Central, anonymization, export/delete.

### TC-4.1.6 Notice on Login page

1. Open `/login`.
2. **Expected:** EU notice visible below login card.

### TC-4.1.7 Accessibility

1. Tab through banner: link and button receive focus.
2. **Expected:** Visible focus ring on "Mehr erfahren" and "Ausblenden".
3. **Expected:** Enter/Space activate button.
4. **Expected:** Banner has `role="status"` (inspect with DevTools).
