/**
 * Comprehensive end-to-end test of the LIVE Research tab.
 *
 * The Research page boots the App.tsx shell which fans out fetches to
 * ~9 endpoints (news feed, masthead stats, daily digest, trending
 * knowledge-graph entities, knowledge-graph nodes for the sidebar,
 * saved-research list, settings, etc.). All of those need to land
 * before the user even submits a question. We assert:
 *
 *   A. Every sidebar/masthead fetch returns 2xx with CORS headers.
 *   B. No console errors during initial load.
 *   C. Submitting a question yields a real streamed report (>1000 chars).
 *   D. The streamed phases reach Synthesizing or Done.
 *
 * Captures POST URL, every /api response status, failed requests, and
 * console errors so when something breaks we see it instead of guessing.
 */
import { test, expect } from "@playwright/test";

const FRONTEND = "https://techpulse-ai-phi.vercel.app";

test.describe("prod research", () => {
  test("all sidebar fetches + research submission work end-to-end", async ({
    page,
  }) => {
    test.setTimeout(180_000);

    const consoleErrors: string[] = [];
    const failedRequests: string[] = [];
    const seenPostUrls: string[] = [];
    const apiResponses: { url: string; status: number; ms: number }[] = [];
    const requestStartTimes = new Map<string, number>();

    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) =>
      consoleErrors.push(`pageerror: ${err.message}`)
    );
    page.on("requestfailed", (req) => {
      failedRequests.push(
        `${req.method()} ${req.url()} -- ${req.failure()?.errorText ?? ""}`
      );
    });
    page.on("request", (req) => {
      if (req.url().includes("/api/")) {
        requestStartTimes.set(req.url() + req.method(), Date.now());
        if (req.method() === "POST" && req.url().includes("/api/research")) {
          seenPostUrls.push(req.url());
        }
      }
    });
    page.on("response", (resp) => {
      const url = resp.url();
      if (url.includes("/api/")) {
        const key = url + resp.request().method();
        const t0 = requestStartTimes.get(key) ?? Date.now();
        apiResponses.push({
          url,
          status: resp.status(),
          ms: Date.now() - t0,
        });
      }
    });

    // 1. Load the Research page.
    await page.goto(`${FRONTEND}/research`, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });

    // 2. Give the sidebar fetches time to complete. The app fans out
    // many requests on mount; wait until network looks quiet OR 12s.
    await page.waitForLoadState("networkidle", { timeout: 12_000 }).catch(() => {
      // SSE keepalives can prevent "idle" from firing; that's OK.
    });

    // 3. Find the research textarea and submit a question.
    const input = page
      .locator('textarea[placeholder*="ask the desk"]')
      .first();
    await input.waitFor({ state: "visible", timeout: 20_000 });
    await input.fill("What are the latest developments in AI agents?");

    const submitBtn = page
      .locator('button:has-text("Research")')
      .filter({ hasText: /Research/ })
      .last();
    await submitBtn.click();
    console.log("Clicked submit button.");

    // 4. Wait for the research run.
    const started = Date.now();
    let lastLen = 0;
    const seenPhases = new Set<string>();
    let saw = {
      phases: [] as string[],
      bodyLen: 0,
      errorMsg: null as string | null,
      phaseChip: "",
    };

    while (Date.now() - started < 120_000) {
      saw = await page.evaluate(() => {
        const text = document.body.innerText || "";
        const phaseTokens = [
          "Decomposing",
          "Searching",
          "Synthesizing",
          "Done",
          "done",
        ];
        const phases = phaseTokens.filter((p) => text.includes(p));
        const chipEl = document.querySelector(
          '[data-testid="research-phase-chip"]'
        );
        const reportEl = document.querySelector(
          '[data-testid="research-report-body"]'
        );
        const errEl = document.querySelector(
          '[data-testid="research-error-panel"]'
        );
        return {
          phases,
          bodyLen: (reportEl?.textContent || text).length,
          errorMsg: errEl ? (errEl.textContent || "").slice(0, 200) : null,
          phaseChip: chipEl ? (chipEl.textContent || "").slice(0, 80) : "",
        };
      });
      saw.phases.forEach((p) => seenPhases.add(p));
      if (saw.phaseChip) seenPhases.add(saw.phaseChip);

      if (saw.errorMsg) break;
      if (saw.bodyLen > lastLen + 100) {
        console.log(
          `t+${((Date.now() - started) / 1000).toFixed(
            1
          )}s chip="${saw.phaseChip}" bodyLen=${saw.bodyLen} seen=${Array.from(
            seenPhases
          ).join(",")}`
        );
        lastLen = saw.bodyLen;
      }
      if (
        (saw.phaseChip === "Done" || saw.phases.includes("Done")) &&
        saw.bodyLen > 1500
      ) {
        break;
      }
      await page.waitForTimeout(500);
    }
    saw.phases = Array.from(seenPhases);

    // 5. Report everything we learned.
    console.log("");
    console.log("==================== TRACE ====================");
    console.log("--- /api/ responses (status + ms) ---");
    apiResponses.forEach((r) => {
      const path = r.url.replace("https://techpulse-ai-backend.fly.dev", "");
      console.log(`  ${r.status}  ${r.ms.toString().padStart(5)}ms  ${path}`);
    });
    console.log("--- POST URLs to /api/research ---");
    seenPostUrls.forEach((u) => console.log(`  ${u}`));
    console.log("--- failed requests ---");
    failedRequests.forEach((r) => console.log(`  ${r}`));
    console.log("--- console errors (non-MetaMask) ---");
    consoleErrors
      .filter((e) => !e.includes("MetaMask") && !e.includes("inpage.js"))
      .forEach((e) => console.log(`  ${e.slice(0, 240)}`));
    console.log("--- final state ---");
    console.log(JSON.stringify(saw, null, 2));

    await page.screenshot({ path: "research-result.png", fullPage: true });

    // ----- Assertions -----

    // A. Every /api fetch the page kicked off should have returned 2xx.
    //    Anything 4xx/5xx (or a network-level failure recorded earlier)
    //    means the user will see a CORS-looking error in DevTools.
    const apiFailures = apiResponses.filter((r) => r.status >= 400);
    expect(
      apiFailures,
      `Sidebar/masthead /api fetches must all be 2xx. Saw: ${JSON.stringify(
        apiFailures
      )}`
    ).toEqual([]);
    expect(
      failedRequests,
      `Browser-level request failures must be zero. Saw: ${failedRequests.join(
        " | "
      )}`
    ).toEqual([]);

    // B. No console errors from our code (MetaMask extension errors filtered).
    const ourErrors = consoleErrors.filter(
      (e) => !e.includes("MetaMask") && !e.includes("inpage.js")
    );
    expect(ourErrors, `No console errors from our code`).toEqual([]);

    // C. Research POST went out and got 200.
    expect(
      seenPostUrls.length,
      "Frontend must POST /api/research"
    ).toBeGreaterThan(0);
    expect(
      seenPostUrls[0],
      "POST should hit /api/research without trailing slash"
    ).toMatch(/\/api\/research(?:\?|$)/);
    const researchResp = apiResponses.find(
      (r) => r.url.includes("/api/research") && !r.url.includes("/api/research-")
    );
    expect(researchResp?.status, "Research SSE should return 200").toBe(200);

    // D. Pipeline ran -- saw at least Synthesizing or Done.
    const reachedSynthesisOrDone =
      saw.phases.includes("Synthesizing") ||
      saw.phases.includes("Done") ||
      saw.phases.includes("done");
    expect(
      reachedSynthesisOrDone,
      `Should reach Synthesizing or Done; saw=${saw.phases.join(",")}`
    ).toBe(true);

    // E. Report has real content.
    expect(
      saw.bodyLen,
      "Report body must contain >1000 chars of streamed content"
    ).toBeGreaterThan(1000);
  });
});
