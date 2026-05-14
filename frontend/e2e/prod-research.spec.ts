/**
 * Drives the LIVE Research tab through a real browser and verifies the
 * full agentic loop works end-to-end. Targets the exact textarea +
 * submit button from ResearchMode.tsx.
 */
import { test, expect } from "@playwright/test";

const FRONTEND = "https://techpulse-ai-phi.vercel.app";

test.describe("prod research", () => {
  test("research run streams through and renders a report", async ({ page }) => {
    test.setTimeout(180_000);

    const consoleErrors: string[] = [];
    const failedRequests: string[] = [];
    const seenPostUrls: string[] = [];
    const seenResponses: { url: string; status: number }[] = [];

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
      if (req.method() === "POST" && req.url().includes("/api/research")) {
        seenPostUrls.push(req.url());
      }
    });
    page.on("response", (resp) => {
      const url = resp.url();
      if (url.includes("/api/")) {
        seenResponses.push({ url, status: resp.status() });
      }
    });

    // 1. Land on Research and wait for it to finish loading.
    await page.goto(`${FRONTEND}/research`, {
      waitUntil: "domcontentloaded",
      timeout: 30_000,
    });

    // Warm the backend with a no-op fetch (CORS preflight + masthead
    // articles) so the cold-start doesn't tank the test.
    await page.waitForTimeout(3000);

    // 2. Locate the research textarea by placeholder.
    const input = page.locator(
      'textarea[placeholder*="ask the desk"]'
    ).first();
    await input.waitFor({ state: "visible", timeout: 20_000 });
    await input.fill("What are the latest developments in AI agents?");

    // 3. The submit button has the visible text "[ Research" and a Send
    // arrow. Match by visible text inside the button.
    const submitBtn = page.locator('button:has-text("Research")').filter({
      hasText: /Research/,
    }).last(); // last because the sidebar also has "Research" -- the in-form button is later in DOM order
    await submitBtn.click();
    console.log("Clicked submit button.");

    // 4. Wait for the research run. We poll the DOM for phase chips +
    // streamed report body. The "research-phase-chip" testid lights up
    // with the current phase string; "research-report-body" wraps the
    // streamed markdown.
    const started = Date.now();
    let lastLen = 0;
    // Accumulate every phase we've EVER seen so the final assertion isn't
    // tripped by the chip text snapping from "Synthesizing" to "Done" right
    // before our final snapshot.
    const seenPhases = new Set<string>();
    let saw: { phases: string[]; bodyLen: number; errorMsg: string | null; phaseChip: string } = {
      phases: [],
      bodyLen: 0,
      errorMsg: null,
      phaseChip: "",
    };

    while (Date.now() - started < 120_000) {
      saw = await page.evaluate(() => {
        const text = document.body.innerText || "";
        const phaseTokens = ["Decomposing", "Searching", "Synthesizing", "Done", "done"];
        const phases = phaseTokens.filter((p) => text.includes(p));
        const chipEl = document.querySelector('[data-testid="research-phase-chip"]');
        const reportEl = document.querySelector('[data-testid="research-report-body"]');
        const errEl = document.querySelector('[data-testid="research-error-panel"]');
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
          `t+${((Date.now() - started) / 1000).toFixed(1)}s chip="${saw.phaseChip}" bodyLen=${saw.bodyLen} seen=${Array.from(seenPhases).join(",")}`
        );
        lastLen = saw.bodyLen;
      }
      // Success: chip says Done AND body has real content.
      if ((saw.phaseChip === "Done" || saw.phases.includes("Done")) && saw.bodyLen > 1500) {
        break;
      }
      await page.waitForTimeout(500);
    }
    // Surface every phase we observed over the run, not just the last frame.
    saw.phases = Array.from(seenPhases);

    console.log("");
    console.log("==================== TRACE ====================");
    console.log("--- POST URLs to /api/research ---");
    seenPostUrls.forEach((u) => console.log(`  ${u}`));
    console.log("--- /api/ responses ---");
    seenResponses.forEach((r) => console.log(`  ${r.status}  ${r.url}`));
    console.log("--- failed requests ---");
    failedRequests.forEach((r) => console.log(`  ${r}`));
    console.log("--- console errors ---");
    consoleErrors.forEach((e) => console.log(`  ${e.slice(0, 240)}`));
    console.log("--- final state ---");
    console.log(JSON.stringify(saw, null, 2));

    await page.screenshot({ path: "research-result.png", fullPage: true });

    // Hard expectations.
    expect(
      saw.errorMsg,
      `Visible error in research-error-panel: ${saw.errorMsg}`
    ).toBeNull();
    expect(
      seenPostUrls.length,
      "Frontend should have POSTed /api/research"
    ).toBeGreaterThan(0);
    expect(seenPostUrls[0], "POST should target /api/research without trailing slash").toMatch(
      /\/api\/research(?:\?|$)/
    );
    // Either Synthesizing or the terminal Done phase signals the agent
    // ran the full pipeline. We accept either since the chip flips fast.
    const reachedSynthesisOrDone =
      saw.phases.includes("Synthesizing") ||
      saw.phases.includes("Done") ||
      saw.phases.includes("done");
    expect(
      reachedSynthesisOrDone,
      `Should reach Synthesizing or Done; saw=${saw.phases.join(",")}`,
    ).toBe(true);
    expect(saw.bodyLen, "Report body must contain real synthesised content").toBeGreaterThan(1000);
  });
});
