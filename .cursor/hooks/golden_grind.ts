import { existsSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { spawnSync } from "child_process";

const CWD = process.cwd();

interface StopHookInput {
  conversation_id: string;
  status: "completed" | "aborted" | "error";
  loop_count: number;
}

const input: StopHookInput = await Bun.stdin.json();

// ---- Config ----
const MAX_ITERATIONS = 5;
// Prefer single entrypoint; keep it consistent with your repo.
const COMMAND = "./scripts/test.sh";
// If you want to include E2E in the grind, ensure scripts/test.sh runs it,
// or add a separate step here.
const SCRATCHPAD_PATH = join(CWD, ".cursor", "scratchpad.md");

// If the agent run did not complete successfully, do not continue looping.
if (input.status !== "completed") {
  console.log(JSON.stringify({}));
  process.exit(0);
}

// Stop if reached max iterations
if (input.loop_count >= MAX_ITERATIONS) {
  appendScratchpad(`\n[golden_path_grind] Reached MAX_ITERATIONS=${MAX_ITERATIONS}. STOP.\n`);
  console.log(JSON.stringify({}));
  process.exit(0);
}

// Run the test command
const result = runCommand(COMMAND);

// Update scratchpad with results
appendScratchpad(formatRunSummary(input.loop_count + 1, COMMAND, result));

// Check for DONE marker AND tests passed
const scratchpad = existsSync(SCRATCHPAD_PATH) ? readFileSync(SCRATCHPAD_PATH, "utf-8") : "";
const hasDone = scratchpad.includes("DONE");
const testsPassed = result.exitCode === 0;

// Continue loop if not green yet
if (!testsPassed || !hasDone) {
  const followup = [
    `[Iteration ${input.loop_count + 1}/${MAX_ITERATIONS}] Golden Path is not green yet.`,
    `- Tests passed: ${testsPassed}`,
    `- Scratchpad DONE: ${hasDone}`,
    ``,
    `Continue working with minimal fixes only. Do not expand scope.`,
    `1) Read latest failures from .cursor/scratchpad.md`,
    `2) Fix the root cause`,
    `3) Re-run ${COMMAND}`,
    `4) When fully green, add 'DONE' to .cursor/scratchpad.md`
  ].join("\n");

  console.log(JSON.stringify({ followup_message: followup }));
  process.exit(0);
}

// If all good, stop looping
appendScratchpad(`\n[golden_path_grind] ✅ Green state confirmed. STOP.\n`);
console.log(JSON.stringify({}));
process.exit(0);

// ---------- helpers ----------

function runCommand(cmd: string): { exitCode: number; stdout: string; stderr: string } {
  // Run through shell for portability (scripts/test.sh)
  const res = spawnSync(cmd, {
    shell: true,
    encoding: "utf-8",
    stdio: ["ignore", "pipe", "pipe"],
    cwd: CWD,
  });

  return {
    exitCode: res.status ?? 1,
    stdout: trim(res.stdout),
    stderr: trim(res.stderr),
  };
}

function appendScratchpad(text: string) {
  const existing = existsSync(SCRATCHPAD_PATH) ? readFileSync(SCRATCHPAD_PATH, "utf-8") : "";
  writeFileSync(SCRATCHPAD_PATH, existing + text, "utf-8");
}

function formatRunSummary(iteration: number, cmd: string, result: { exitCode: number; stdout: string; stderr: string }) {
  const status = result.exitCode === 0 ? "PASS" : "FAIL";
  return [
    `\n==============================`,
    `[golden_path_grind] Iteration ${iteration} — ${status}`,
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

function trim(s?: string) {
  return (s ?? "").toString().trim();
}
