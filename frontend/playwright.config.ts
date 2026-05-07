import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for the TechPulse AI behavior-test suite.
 *
 * Tests run against the already-running dev stack:
 *   - frontend at http://localhost:3000
 *   - backend at http://127.0.0.1:8000
 *   - Ollama at http://localhost:11434
 *
 * Video is recorded for EVERY test (video: "on") so regressions are
 * obvious visually, not just as failed assertions.
 */
export default defineConfig({
  testDir: "./e2e",
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
