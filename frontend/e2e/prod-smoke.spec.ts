/**
 * Comprehensive smoke test across the LIVE production app.
 *
 * Goal: catch any CORS / 4xx / 5xx errors on the endpoints that each
 * page fans out to on mount. The user has repeatedly seen "blocked by
 * CORS policy" errors that turned out to be Fly proxy 5xx during machine
 * restarts -- the proxy strips CORS headers on its own error responses.
 *
 * Pages exercised:
 *   /          (Welcome -- masthead + LIVE WIRE pane)
 *   /feed      (News Feed grid + TrendingRail + masthead stats + digest)
 *   /research  (App shell + research textarea)
 *
 * For each page we assert:
 *   - Every /api/* fetch returned 2xx
 *   - No browser-level failed requests
 *   - No console errors from our code (MetaMask extension filtered)
 */
import { test, expect } from "@playwright/test";

const FRONTEND = "https://techpulse-ai-phi.vercel.app";

async function visitAndCollect(page: any, path: string, settleMs = 8000) {
  const consoleErrors: string[] = [];
  const failedRequests: string[] = [];
  const apiResponses: { url: string; status: number }[] = [];

  page.on("console", (msg: any) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err: any) =>
    consoleErrors.push(`pageerror: ${err.message}`)
  );
  page.on("requestfailed", (req: any) => {
    failedRequests.push(
      `${req.method()} ${req.url()} -- ${req.failure()?.errorText ?? ""}`
    );
  });
  page.on("response", (resp: any) => {
    if (resp.url().includes("/api/")) {
      apiResponses.push({ url: resp.url(), status: resp.status() });
    }
  });

  await page.goto(`${FRONTEND}${path}`, {
    waitUntil: "domcontentloaded",
    timeout: 30_000,
  });
  // Give all page-mount fetches time to land.
  await page.waitForLoadState("networkidle", { timeout: settleMs }).catch(() => {});
  await page.waitForTimeout(2000); // catch any late TrendingRail fetches

  return { consoleErrors, failedRequests, apiResponses };
}

function summarize(
  label: string,
  out: { consoleErrors: string[]; failedRequests: string[]; apiResponses: { url: string; status: number }[] }
) {
  const ourErrors = out.consoleErrors.filter(
    (e) => !e.includes("MetaMask") && !e.includes("inpage.js")
  );
  const failures = out.apiResponses.filter((r) => r.status >= 400);
  console.log(`\n=== ${label} ===`);
  out.apiResponses.forEach((r) => {
    const p = r.url.replace("https://techpulse-ai-backend.fly.dev", "");
    console.log(`  ${r.status}  ${p}`);
  });
  if (failures.length) {
    console.log("API FAILURES:");
    failures.forEach((f) => console.log(`  ${f.status}  ${f.url}`));
  }
  if (out.failedRequests.length) {
    console.log("REQUEST FAILURES:");
    out.failedRequests.forEach((r) => console.log(`  ${r}`));
  }
  if (ourErrors.length) {
    console.log("CONSOLE ERRORS:");
    ourErrors.forEach((e) => console.log(`  ${e.slice(0, 240)}`));
  }
  return { ourErrors, failures };
}

test.describe("prod smoke -- every page boots clean", () => {
  test.setTimeout(120_000);

  for (const path of ["/", "/feed", "/research"]) {
    test(`${path} -- zero CORS/4xx/5xx errors on mount`, async ({ page }) => {
      const out = await visitAndCollect(page, path);
      const { ourErrors, failures } = summarize(path, out);

      expect(
        failures,
        `${path}: every /api fetch must be 2xx. ${JSON.stringify(failures)}`
      ).toEqual([]);
      expect(
        out.failedRequests,
        `${path}: no browser request failures. ${out.failedRequests.join(" | ")}`
      ).toEqual([]);
      expect(
        ourErrors,
        `${path}: no console errors. ${ourErrors.join(" | ")}`
      ).toEqual([]);
    });
  }
});
