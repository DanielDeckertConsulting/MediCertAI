# Mobile-Responsive Layout

**Feature:** Mobile-first UI for MentalCarePilot  
**Breakpoints:** xs 390px | sm 640px | md 768px | lg 1024px | xl 1280px

## Layout Strategy

```mermaid
flowchart TD
    subgraph Mobile["< 768px"]
        M1[Hamburger menu]
        M2[Sticky header]
        M3[Full-width main]
        M1 --> M2 --> M3
    end

    subgraph Desktop["≥ 768px"]
        D1[Fixed sidebar nav]
        D2[Main content area]
        D1 --> D2
    end
```

## Chat Page Layout

```mermaid
flowchart LR
    subgraph Mobile["Mobile: Single view"]
        MC1["/chat → Chat list (full width)"]
        MC2["/chat/:id → Chat detail + back button"]
        MC1 --> MC2
    end

    subgraph Desktop["Desktop: Split view"]
        DC1[Chat list sidebar]
        DC2[Chat detail main]
        DC1 --- DC2
    end
```

## Touch Targets

- Primary actions: `min-h-touch` / `min-w-touch` (44px)
- Applied to: nav links, create chat, send, dictation (mic), back, ErrorBoundary retry

## Design Tokens

- Primary: `#0ea5e9` (primary-500), `#0284c7` (primary-600)
- No hardcoded colors outside Tailwind tokens
