---
name: dynamic-skills-hooks
description: Explains Cursor Agent Skills (dynamic loading, custom commands, hooks). Covers hooks.json, stop-hook scripts, and long-running agent loops (e.g. grind-until-tests-pass). Use when configuring skills, hooks, agent loops, grind scripts, hooks.json, or when the user asks about dynamic capabilities and workflows.
---

# Dynamic Skills and Hooks

Agent Skills extend what agents can do. They package domain knowledge, workflows, and scripts that agents load **when relevant** (unlike Rules, which are always included). This keeps context smaller while giving the agent specialized capabilities.

## What Skills Can Include

- **Custom commands**: Reusable workflows triggered with `/` in the agent input
- **Hooks**: Scripts that run before or after agent actions (e.g. on "stop")
- **Domain knowledge**: Instructions for specific tasks the agent pulls in on demand

## Hooks Configuration

Hooks are defined in `.cursor/hooks.json`:

```json
{
  "version": 1,
  "hooks": {
    "stop": [{ "command": "bun run .cursor/hooks/grind.ts" }]
  }
}
```

The **stop** hook runs when the agent would normally stop. The script receives context on stdin and can return a `followup_message` to keep the agent loop running.

## Long-Running Agent Loop Pattern

Use a stop hook to keep the agent iterating until a verifiable goal is met (e.g. all tests pass, UI matches mockup).

**1. hooks.json**

```json
{
  "version": 1,
  "hooks": {
    "stop": [{ "command": "bun run .cursor/hooks/grind.ts" }]
  }
}
```

**2. Hook script (.cursor/hooks/grind.ts)**

The script reads JSON from stdin. To continue the loop, output a JSON object with `followup_message`. To stop, output `{}` or omit followup_message.

```typescript
import { readFileSync, existsSync } from "fs";

interface StopHookInput {
  conversation_id: string;
  status: "completed" | "aborted" | "error";
  loop_count: number;
}

const input: StopHookInput = await Bun.stdin.json();
const MAX_ITERATIONS = 5;

if (input.status !== "completed" || input.loop_count >= MAX_ITERATIONS) {
  console.log(JSON.stringify({}));
  process.exit(0);
}

const scratchpad = existsSync(".cursor/scratchpad.md")
  ? readFileSync(".cursor/scratchpad.md", "utf-8")
  : "";

if (scratchpad.includes("DONE")) {
  console.log(JSON.stringify({}));
} else {
  console.log(JSON.stringify({
    followup_message: `[Iteration ${input.loop_count + 1}/${MAX_ITERATIONS}] Continue working. Update .cursor/scratchpad.md with DONE when complete.`
  }));
}
```

**3. Success condition**

- The hook decides "done" by some observable (e.g. scratchpad contains "DONE", or run tests and check exit code). When done, output `{}` so the agent stops.
- Use a `loop_count` / `MAX_ITERATIONS` guard to avoid infinite loops.

## Use Cases

- Run tests and re-run the agent until all tests pass
- Iterate on UI until it matches a design mockup
- Any goal-oriented task where success is verifiable

## Integration Notes

- Hooks can call into security tools, secrets managers, and observability platforms (see hooks documentation for partner integrations).
- **Agent Skills and hooks** are available in the **Nightly** release channel: Cursor settings → Beta → set update channel to Nightly, then restart.
- For external integrations (Slack, Datadog, Sentry, databases), use MCP (Model Context Protocol) in addition to or instead of hooks.

## Variant: Golden Grind

Same pattern with a differently named hook script:

```json
{
  "version": 1,
  "hooks": {
    "stop": [{ "command": "bun run .cursor/hooks/golden_grind.ts" }]
  }
}
```

Implement `golden_grind.ts` with the same stdin/stdout contract: read `StopHookInput`, output `{}` to stop or `{ "followup_message": "..." }` to continue.

## Reference

- For the exact hook stdin/stdout contract, see [reference.md](reference.md).
