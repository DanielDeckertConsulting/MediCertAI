import { existsSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { spawnSync } from "child_process";

// Globals when run under Bun (no @types/node / @types/bun in scope for .cursor/hooks)
declare const process: { cwd(): string; exit(code: number): never };
declare const Bun: { stdin: { json(): Promise<StopHookInput> } };

interface StopHookInput {
  conversation_id: string;
  status: "completed" | "aborted" | "error";
  loop_count: number;
}

const input: StopHookInput = await Bun.stdin.json();

const CWD = process.cwd();
const SCRATCHPAD = join(CWD, ".cursor", "scratchpad.md");
const MAX_ITERATIONS = 8; // total orchestrator cycles
const TEST_CMD = "./scripts/test.sh";

// --- stop early if agent run didn't complete
if (input.status !== "completed") {
  console.log(JSON.stringify({}));
  process.exit(0);
}

// --- stop if too many loops
if (input.loop_count >= MAX_ITERATIONS) {
  append(`\n[ops_orchestrator] STOP: reached MAX_ITERATIONS=${MAX_ITERATIONS}\n`);
  console.log(JSON.stringify({}));
  process.exit(0);
}

const sp = readScratchpad();

// --- initialize orchestrator plan once
if (!sp.includes("ORCH:INIT")) {
  const touched = computeTouchedPaths();
  const plan = buildPlan(touched);

  append([
    `\n# ORCH:INIT`,
    `ORCH:PLAN=${plan.join(",")}`,
    `ORCH:PHASE=${plan[0] ?? "DONE"}`,
    `ORCH:TOUCHED=${touched.join(";") || "(none)"}`,
    `\n`
  ].join("\n"));

  const followup = [
    `[ops_orchestrator] Initialized plan: ${plan.join(" → ") || "DONE"}`,
    `Touched paths: ${touched.length ? touched.join(", ") : "(none)"}`,
    ``,
    `Proceed with phase: ${plan[0] ?? "DONE"}`,
    `Follow the instructions below and update .cursor/scratchpad.md markers when done.`
  ].join("\n");
  const hc = detectHealthcareMode(touched);
  append(`HEALTHCARE_MODE=${hc.enabled ? "YES" : "NO"}\n`);
  if (hc.reason.length) append(`HEALTHCARE_REASON=${hc.reason.join(" | ")}\n`);
  
  console.log(JSON.stringify({ followup_message: followup + "\n\n" + phaseInstructions(plan[0] ?? "DONE") }));
  process.exit(0);
}

// --- determine current phase
const phase = getMarker("ORCH:PHASE");
const plan = (getMarker("ORCH:PLAN") || "").split(",").map(s => s.trim()).filter(Boolean);

// --- route phase handlers
switch (phase) {
  case "GRIND":
    handleGrind(input.loop_count);
    break;

  case "EVENT_SCHEMA":
  case "PROJECTION_CHECK":
  case "GDPR_SCAN":
  case "DIAGRAMS_SYNC":
    handleHumanPhase(phase, plan);
    break;

  case "DONE":
  default:
    append(`\n[ops_orchestrator] ✅ DONE. No further actions.\n`);
    console.log(JSON.stringify({}));
    process.exit(0);
}

// ---------------- phase handlers ----------------

function handleGrind(loopCount: number) {
  const touched = computeTouchedPaths();
  const e2eDecision = isFlowRelevantForE2E(touched);
const runE2E = e2eDecision.run;
append(`\n[ops_orchestrator] E2E_DECISION=${runE2E ? "YES" : "NO"} REASON=${e2eDecision.reasons.join(" | ")}\n`);

  // 1) base checks
  const res = runCmd(TEST_CMD);
  append(formatRunSummary(loopCount + 1, TEST_CMD, res));

  if (res.exitCode !== 0) {
    const msg = [
      `[Iteration ${loopCount + 1}/${MAX_ITERATIONS}] Base tests are NOT green.`,
      `Fix minimal root cause ONLY. Do not expand scope.`,
      ``,
      `Re-run: ${TEST_CMD}`,
    ].join("\n");
    console.log(JSON.stringify({ followup_message: msg }));
    process.exit(0);
  }

  // 2) conditional E2E (only when frontend touched)
  if (runE2E) {
    const e2eCmd = "cd frontend && npx playwright test";
    const e2e = runCmd(e2eCmd);
    append(formatRunSummary(loopCount + 1, e2eCmd, e2e));

    if (e2e.exitCode !== 0) {
      const msg = [
        `[Iteration ${loopCount + 1}/${MAX_ITERATIONS}] E2E is NOT green (frontend touched).`,
        `Fix minimal root cause ONLY. Avoid brittle selectors if possible.`,
        ``,
        `Re-run: ${e2eCmd}`,
      ].join("\n");
      console.log(JSON.stringify({ followup_message: msg }));
      process.exit(0);
    }
  }

  // if checks pass, advance phase
  append(`\n[ops_orchestrator] ✅ GRIND green (base${runE2E ? "+e2e" : ""}). Advancing.\n`);
  advance(plan);
}

function handleHumanPhase(phase: string, plan: string[]) {
  // This phase is performed by the agent; the hook prompts next steps.
  // Completion is signaled by writing "ORCH:PHASE_DONE=<PHASE>" into scratchpad.
  const doneMarker = `ORCH:PHASE_DONE=${phase}`;
  const sp = readScratchpad();

  if (!sp.includes(doneMarker)) {
    const msg = [
      `[ops_orchestrator] Phase "${phase}" pending.`,
      `Complete the phase and then append this exact line to .cursor/scratchpad.md:`,
      `${doneMarker}`,
      ``,
      `Phase instructions:`,
      phaseInstructions(phase),
    ].join("\n");
    console.log(JSON.stringify({ followup_message: msg }));
    process.exit(0);
  }

  append(`\n[ops_orchestrator] ✅ ${phase} completed. Advancing.\n`);
  advance(plan);
}

function advance(plan: string[]) {
  const current = getMarker("ORCH:PHASE");
  const idx = plan.indexOf(current);
  const next = idx >= 0 ? plan[idx + 1] : "DONE";
  setMarker("ORCH:PHASE", next || "DONE");

  if (!next) {
    append(`\n[ops_orchestrator] ✅ All phases done.\n`);
    console.log(JSON.stringify({}));
    process.exit(0);
  }

  const msg = [
    `[ops_orchestrator] Next phase: ${next}`,
    phaseInstructions(next),
  ].join("\n\n");

  console.log(JSON.stringify({ followup_message: msg }));
  process.exit(0);
}

// ---------------- planning ----------------

function buildPlan(touched: string[]): string[] {
  // always start with GRIND
  const plan: string[] = ["GRIND"];

  const touchesEvents =
    touched.some(filePath => filePath.startsWith("shared/events")) ||
    touched.some(filePath => filePath.includes("/domain/events/")) ||
    touched.some(filePath => filePath.includes("schema.json"));

  const touchesProjections =
    touched.some(filePath => filePath.includes("/domain/projections/")) ||
    touched.some(filePath => filePath.toLowerCase().includes("projector")) ||
    touched.some(filePath => filePath.toLowerCase().includes("projection"));

  const touchesDocsOrFlows =
    touched.some(filePath => filePath.startsWith("docs/")) ||
    touchesEvents ||
    touchesProjections ||
    touched.some(filePath => filePath.includes("/api/")) ||
    touched.some(filePath => filePath.startsWith("frontend/"));

  const { enabled: healthcareMode } = detectHealthcareMode(touched);

  // Structural phases
  if (touchesEvents) plan.push("EVENT_SCHEMA");
  if (touchesProjections) plan.push("PROJECTION_CHECK");

  // Governance: only mandatory in healthcare mode; optional otherwise
  // (We keep it in plan always if healthcareMode, else skip to avoid overhead.)
  if (healthcareMode) plan.push("GDPR_SCAN");

  // Docs sync if anything workflow/arch related changed
  if (touchesDocsOrFlows) plan.push("DIAGRAMS_SYNC");

  plan.push("DONE");
  return plan;
}
// ---------------- phase instructions ----------------

function phaseInstructions(phase: string) {
  switch (phase) {
    case "GRIND":
      return [
        `Run and fix until green:`,
        `- Execute: ${TEST_CMD}`,
        `- Fix failing tests with minimal changes`,
        `- Repeat until green (hook will advance automatically)`
      ].join("\n");

    case "EVENT_SCHEMA":
      return [
        `Run Event Schema Guard (skill):`,
        `- Validate event fields, schema_version, naming, and no PII in payload`,
        `- Ensure shared schema/types are aligned`,
        `When complete, append to scratchpad: ORCH:PHASE_DONE=EVENT_SCHEMA`
      ].join("\n");

    case "PROJECTION_CHECK":
      return [
        `Run Projection Rebuild Check (skill):`,
        `- Validate idempotency of projectors`,
        `- Replay/rebuild mental model; ensure deterministic output`,
        `- Add/adjust tests for idempotency if needed`,
        `When complete, append: ORCH:PHASE_DONE=PROJECTION_CHECK`
      ].join("\n");

    case "GDPR_SCAN":
      return [
        `Run GDPR Scan (skill):`,
        `- Verify no PII in logs, tests, docs, diagrams`,
        `- Replace any real-looking emails/phones/names with placeholders`,
        `When complete, append: ORCH:PHASE_DONE=GDPR_SCAN`
      ].join("\n");

    case "DIAGRAMS_SYNC":
      return [
        `Run docs drift + diagram update:`,
        `- Use #diagram_diff to identify diagram impact`,
        `- Then run #update_diagrams_after_feature to update Mermaid diagrams`,
        `When complete, append: ORCH:PHASE_DONE=DIAGRAMS_SYNC`
      ].join("\n");

    case "DONE":
    default:
      return `No further actions.`;
  }
}

// ---------------- git + scratch helpers ----------------

function computeTouchedPaths(): string[] {
  // capture unstaged + staged changes; fallback to status if needed
  const a = runCmd("git diff --name-only");
  const b = runCmd("git diff --cached --name-only");
  const c = runCmd("git status --porcelain");

  const files = new Set<string>();
  for (const line of (a.stdout + "\n" + b.stdout).split("\n")) {
    const f = line.trim();
    if (f) files.add(f);
  }
  // parse status porcelain for safety
  for (const line of c.stdout.split("\n")) {
    const s = line.trim();
    if (!s) continue;
    // format: XY path
    const parts = s.split(/\s+/);
    const path = parts[parts.length - 1];
    if (path) files.add(path);
  }
  return Array.from(files).sort();
}

function readScratchpad() {
  return existsSync(SCRATCHPAD) ? readFileSync(SCRATCHPAD, "utf-8") : "";
}

function append(text: string) {
  const existing = readScratchpad();
  writeFileSync(SCRATCHPAD, existing + text, "utf-8");
}

function getMarker(key: string): string {
  const sp = readScratchpad();
  const re = new RegExp(`^${escapeRegExp(key)}=(.*)$`, "m");
  const m = sp.match(re);
  return m ? m[1].trim() : "";
}

function setMarker(key: string, value: string) {
  const sp = readScratchpad();
  const re = new RegExp(`^${escapeRegExp(key)}=.*$`, "m");
  if (re.test(sp)) {
    const next = sp.replace(re, `${key}=${value}`);
    writeFileSync(SCRATCHPAD, next, "utf-8");
  } else {
    append(`\n${key}=${value}\n`);
  }
}

function escapeRegExp(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function runCmd(cmd: string): { exitCode: number; stdout: string; stderr: string } {
  const res = spawnSync(cmd, {
    shell: true,
    encoding: "utf-8",
    stdio: ["ignore", "pipe", "pipe"],
    cwd: CWD,
  });
  return { exitCode: res.status ?? 1, stdout: (res.stdout ?? "").trim(), stderr: (res.stderr ?? "").trim() };
}

function formatRunSummary(iteration: number, cmd: string, result: { exitCode: number; stdout: string; stderr: string }) {
  const status = result.exitCode === 0 ? "PASS" : "FAIL";
  return [
    `\n==============================`,
    `[ops_orchestrator] GRIND Iteration ${iteration} — ${status}`,
    `Command: ${cmd}`,
    `Exit code: ${result.exitCode}`,
    result.stdout ? `\n--- STDOUT ---\n${truncate(result.stdout)}` : ``,
    result.stderr ? `\n--- STDERR ---\n${truncate(result.stderr)}` : ``,
    `==============================\n`,
  ].filter(Boolean).join("\n");
}

function truncate(s: string, max = 6000) {
  if (s.length <= max) return s;
  return s.slice(0, max) + `\n...[truncated ${s.length - max} chars]`;
}

function detectHealthcareMode(touched: string[]): { enabled: boolean; reason: string[] } {
  const reasons: string[] = [];
  const sp = readScratchpad();

  // Strong signal: explicit marker set by ship_feature_auto
  const mode = getMarker("MODE_SELECTED");
  const sensitivity = getMarker("DATA_SENSITIVITY");

  if (mode === "HEALTHCARE") reasons.push("MODE_SELECTED=HEALTHCARE marker");
  if (sensitivity === "HEALTHCARE_SENSITIVE") reasons.push("DATA_SENSITIVITY=HEALTHCARE_SENSITIVE marker");
  if (sensitivity === "PII") reasons.push("DATA_SENSITIVITY=PII marker");

  // Fallback keyword heuristic (scratchpad + changed files list)
  const haystack = (sp + "\n" + touched.join("\n")).toLowerCase();
  const keywords = [
    "patient", "medical", "therapy", "healthcare", "diagnosis",
    "gdpr", "dsgvo", "phi", "hipaa", "consent", "treatment"
  ];
  const hit = keywords.filter(k => haystack.includes(k));
  if (hit.length) reasons.push(`keyword hits: ${hit.join(", ")}`);

  // Decide
  const enabled = reasons.some(r =>
    r.includes("MODE_SELECTED=HEALTHCARE") ||
    r.includes("HEALTHCARE_SENSITIVE") ||
    r.includes("keyword hits")
  );

  return { enabled, reason: reasons };
}

function frontendTouched(touched: string[]): boolean {
  return touched.some(p => p.startsWith("frontend/"));
}

function isFlowRelevantForE2E(touched: string[]): { run: boolean; reasons: string[] } {
  const reasons: string[] = [];

  const inc = (pattern: RegExp, label: string) => {
    if (touched.some(p => pattern.test(p))) reasons.push(label);
  };

  // --- Strong flow signals (include) ---
  inc(/^frontend\/app\/.*\/page\.tsx$/i, "nextjs app router page changed");
  inc(/^frontend\/pages\/.*\.(tsx|ts|jsx|js)$/i, "nextjs pages router changed");
  inc(/^frontend\/app\/.*\/route\.ts$/i, "nextjs route handler changed");

  inc(/^frontend\/.*\/(actions|hooks|state|stores|services|api)\//i, "frontend logic/state/api changed");
  inc(/^frontend\/.*\/(forms|validators)\//i, "forms/validation changed");

  inc(/^backend\/.*\/(routes|api)\//i, "backend API routes changed");
  inc(/^shared\//i, "shared contracts/types changed");
  inc(/^docs\/diagrams\/flows\//i, "flow diagrams changed");

  // --- Exclusions (style-only changes) ---
  const styleOnlyPatterns = [
    /^frontend\/styles\//i,
    /^frontend\/.*\.css$/i,
    /^frontend\/.*\.scss$/i,
    /^frontend\/.*\.sass$/i,
    /^tailwind\.config\.(js|ts)$/i,
    /^postcss\.config\.(js|ts)$/i,
    /^frontend\/.*\/(tokens|theme)\//i,
  ];

  const nonFlowOnly = touched.every(p => styleOnlyPatterns.some(rx => rx.test(p)));

  // If changes are exclusively style/theme config, do not run E2E.
  if (nonFlowOnly) return { run: false, reasons: ["style/theme-only changes detected"] };

  // If we have any flow reasons, run E2E.
  if (reasons.length) return { run: true, reasons };

  // If frontend touched but no clear flow signal, default to NO (avoid noise).
  // You can flip this to YES if you prefer safety over speed.
  if (frontendTouched(touched)) {
    return { run: false, reasons: ["frontend touched but no flow-relevant signals"] };
  }

  return { run: false, reasons: ["frontend not touched"] };
}
