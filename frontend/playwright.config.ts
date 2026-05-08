import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for the TechPulse AI behavior-test suite.
 *
 * Tests run against the already-running dev stack:
 *   - frontend at http://localhost:3000
 *   - backend at http://127.0.0.1:8000
 *   - Ollama at http://localhost:11434 (only used by `*.live.spec.ts`)
 *
 * Default `npx playwright test` runs the deterministic spec suite (no
 * Ollama dependency for tests 1-4 of research.spec.ts; Test 5 is the
 * single live integration test).
 *
 * To run the slow live-Ollama integration spec on demand:
 *   npx playwright test research.live.spec.ts --grep @live
 *
 * Video is recorded for EVERY test (video: "on") so regressions are
 * obvious visually, not just as failed assertions.
 */
export default defineConfig({
  testDir: "./e2e",
  // Skip the slow live-Ollama spec on the default run. Override with
  // `--testIgnore="" research.live.spec.ts` (or rely on --grep @live)
  // to opt in.
  testIgnore: ["**/*.live.spec.ts"],
  timeout: 60_000,
  fullyParallel: false, // serial; this is a small suite
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://localhost:3000",
    headless: false, // visible — user wants to watch
    video: "on", // record EVERY test
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    viewport: { width: 1440, height: 900 },
    actionTimeout: 15_000,
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
