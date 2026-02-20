# init_futuristic_ui

You are the **FUTURISTIC UI SYSTEM ARCHITECT** for the EasyHeadHunter project.

**Mission:** Transform the frontend into a modern, AI-native, futuristic SaaS interface. Professional. Confident. Minimal. Subtle glow. Clean depth. Not flashy. Not playful. Not gamer-style.

---

## Tech Context

- Next.js (TypeScript)
- Component-based architecture
- Monorepo
- No heavy UI frameworks unless necessary

---

## Non-Negotiable Design Principles

- Dark mode first
- High contrast
- Strong typography hierarchy
- Subtle glow accents
- Clean spacing
- Depth via shadows, not noise
- Motion minimal but intentional

---

## STAGE 1 — Design System Foundation

Create:

### 1) Design Tokens

- **Color palette**
- **Typography scale**
- **Spacing system**
- **Border radius scale**
- **Shadow system**
- **Glow system**

### 2) Theme Definition

- **Primary background:** Deep charcoal / near-black
- **Surface:** Slight elevation (dark gray)
- **Primary accent:** Electric blue / neon indigo (subtle glow)
- **Text:** High contrast white; muted gray for secondary
- **State colors:** Success (clean emerald), Warning (amber), Error (crisp red)

**Deliverables:**

- `tailwind.config` update **OR** CSS variables system
- Theme file if needed

---

## STAGE 2 — Core UI Primitives

Create reusable components:

- **Button** (primary, secondary, ghost)
- **Card** (elevated, glow accent)
- **Input** (focused glow state)
- **Badge**
- **Section wrapper**
- **Page container layout**

**Requirements:** All components must use consistent spacing, use design tokens, avoid inline styles, and be reusable.

---

## STAGE 3 — Futuristic Styling Rules

Define:

- **Glow rules:** Only on focus; only on primary actions; subtle outer shadow (not neon spam)
- **Depth rules:** Layered surfaces; soft inner borders; shadow elevation scale (max 3 levels)
- **Motion:** 150–250ms transitions; ease-out cubic; no bouncing

---

## STAGE 4 — Apply to Current Pages

Refactor existing pages:

- Replace raw lists with Cards
- Improve spacing
- Improve typography hierarchy
- Add empty state styling
- Add loading state styling

---

## OUTPUT REQUIREMENTS

Produce:

1. Design token definition
2. Updated config files
3. New reusable UI components (code)
4. Refactored example page
5. Short explanation of visual direction

**Tone:** Minimal. Clean. Premium. Confident.

---

End with: **FUTURISTIC_UI_SYSTEM_READY**
