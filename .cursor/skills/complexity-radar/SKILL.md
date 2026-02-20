---
name: complexity-radar
description: Continuously assesses architectural complexity using event count, projection count, cross-layer changes, branch size, and new entity introduction. Use when evaluating a branch or release, before major refactors, or when the user asks for complexity assessment, DEV split, or bounded context review. Outputs LOW/MEDIUM/HIGH and, if HIGH, recommends DEV split and bounded context review.
---

# Complexity Radar

Assesses architectural complexity from observable signals and outputs a level plus actionable recommendations when complexity is high.

## When to apply

- Evaluating a **branch or release** before merge
- Before **major refactors** or multi-team work
- User asks for **complexity assessment**, **DEV split**, or **bounded context review**
- After adding several events, projections, or new entities in one change set

## Signals to gather

1. **Event count**  
   Count distinct `event_type` values.  
   Source: `backend/app/domain/events/event_types.py` (constants) and `docs/events.md` (catalog).

2. **Projection count**  
   Count projector modules (excluding base/registry).  
   Source: `backend/app/domain/projections/*_projector.py`.

3. **Cross-layer changes**  
   In the change set (diff/branch): do touches span **API + domain + projections + frontend** in a single feature?  
   Heuristic: same ticket touches `api/`, `domain/`, `services/`, and `frontend/` or multiple projections.

4. **Branch size**  
   Scope of the branch: file count, new event types, new projectors, new routes/screens.  
   Use `git diff --stat` (or equivalent) against main.

5. **New entity introduction**  
   New `entity_type` or new aggregate (new event family, new read model).  
   Source: `event_types.py`, new projector files, new tables/read models.

For how to count and precise definitions, see [reference.md](reference.md).

## Scoring (guidance)

| Signal              | LOW                    | MEDIUM                         | HIGH                                |
|---------------------|------------------------|---------------------------------|-------------------------------------|
| Event count         | ≤ 15                   | 16–25                           | > 25                                |
| Projection count    | ≤ 5                    | 6–8                             | > 8                                 |
| Cross-layer         | Single layer or 2      | 3 layers                        | 4+ layers in one feature            |
| Branch size         | Small, focused         | Medium (e.g. 10–25 files)       | Large (e.g. 25+ files, many new)    |
| New entities        | 0                      | 1                               | 2+                                  |

Overall level: **worst signal wins** (e.g. one HIGH signal → overall HIGH). If all signals are LOW → LOW; if any MEDIUM and none HIGH → MEDIUM.

## Output format

Always end with:

```markdown
## COMPLEXITY_RADAR – Result

**Complexity:** LOW | MEDIUM | HIGH

**Signals:**
- Event count: [N] ([LOW|MEDIUM|HIGH])
- Projection count: [N] ([LOW|MEDIUM|HIGH])
- Cross-layer changes: [yes|no] ([LOW|MEDIUM|HIGH])
- Branch size: [brief] ([LOW|MEDIUM|HIGH])
- New entity introduction: [N] ([LOW|MEDIUM|HIGH])

**Reasoning:** [1–3 sentences]

[If HIGH:]
**Recommendations:**
- **DEV split:** Consider splitting into BACKEND_ENGINEER_AGENT and FRONTEND_ENGINEER_AGENT (see user rule "MANUAL - DEV Split Trigger" for role definitions and flow).
- **Bounded context review:** Map new events/entities to bounded contexts; consider splitting or clarifying context boundaries and updating docs/architecture.md and docs/diagrams/.
```

## Checklist before finishing

- [ ] All five signals gathered (with concrete numbers or yes/no where applicable)
- [ ] Each signal rated LOW/MEDIUM/HIGH and overall complexity set
- [ ] If HIGH: DEV split and bounded context review recommendations included
- [ ] Reasoning is brief and traceable to the signals
