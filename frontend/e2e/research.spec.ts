import { test, expect } from "@playwright/test";
import {
  assertNoHtmlEntities,
  assertNoMojibake,
  assertNoUndefinedNullObjectObject,
  assertNoHorizontalOverflow,
  assertNoDuplicateSiblings,
  assertNoMockDataLeak,
  installConsoleErrorListener,
  assertConsoleClean,
} from "./_lib/rubric";

/**
 * Research tab — M5 comprehensive Playwright contract spec.
 *
 * Replaces the M3 placeholder with a 5-test suite that exercises the full
 * SSE streaming roundtrip end-to-end through the real UI.
 *
 * Tests:
 *   1. Streaming flow             — phase chip advances, DOM text grows
 *      strictly over time, [N] markers and "Sources Used" appear post-done
 *   2. Citation anchoring         — clicking [N] scrolls #source-N into view
 *   3. Cancel flow                — Cancel button aborts in-flight, no errors
 *   4. Error UX                   — page.route mocks an SSE error frame, the
 *      error panel appears, Retry triggers a second POST
 *   5. Rubric pass                — all 8 rubric helpers against a real run
 *
 * The 5 tests share testid hooks (research-phase-chip, research-report-body,
 * research-error-panel, research-retry-btn, research-cancel-btn,
 * research-copy-btn, research-download-btn) rather than fragile text.
 *
 * To run only this spec:
 *   cd frontend && npx playwright test research.spec.ts
 *
 * Suite-level wall-clock budget is under 90 seconds — the slow streaming
 * tests (1 + 5) use generous per-step timeouts but the cancel and error
 * tests finish in seconds and don't depend on Ollama.
 */

// A short question keeps Test 1 + Test 5 inside their per-test budget.
const SHORT_QUESTION = "Latest AI chip news";

test.describe("Research tab — streaming flow", () => {
  test("phase chip advances, DOM text grows over time, citations + Sources appear", async ({
    page,
  }) => {
    test.setTimeout(120_000);

    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /TechPulse AI/i })
    ).toBeVisible();
    await page.getByRole("tab", { name: /Research/i }).click();

    const queryInput = page.getByPlaceholder(/AI funding rounds/i);
    await expect(queryInput).toBeVisible({ timeout: 10_000 });
    await queryInput.fill(SHORT_QUESTION);

    const submitBtn = page.getByRole("button", { name: /^Research$/i });
    await submitBtn.click();

    // Wait for the phase chip to render — proves SSE plumbing fired.
    const phaseChip = page.getByTestId("research-phase-chip");
    await expect(phaseChip).toBeVisible({ timeout: 15_000 });

    // Collect the distinct phase-chip values we observe over the run.
    // We poll the chip text in the background so we capture transient
    // phases (Decomposing, Searching (1/4), Searching (2/4), ...,
    // Synthesizing, Done) regardless of when our sampling runs.
    const seenPhases = new Set<string>();
    const reportBody = page.getByTestId("research-report-body");
    let pollingDone = false;
    const pollPhase = async () => {
      while (!pollingDone) {
        try {
          const ph = (await phaseChip.textContent())?.trim();
          if (ph) seenPhases.add(ph);
        } catch {
          // Chip may briefly detach between renders; ignore.
        }
        await page.waitForTimeout(150);
      }
    };
    const pollTask = pollPhase();

    // Phase-aware sampling. On real hardware with gpt-oss:20b on CPU,
    // the Decompose + Search phases consume ~12-15s before any token
    // arrives, so a 1s/4s/8s sample window from submit lands entirely
    // inside the placeholder period. Wait until the synthesizing phase
    // begins (tokens are about to flow), then sample at +1s/+3s/+6s
    // from THAT moment. Once tokens are streaming, length grows each
    // sample.
    await expect(phaseChip).toHaveText(/synthesizing/i, { timeout: 60_000 });
    const synthStart = Date.now();

    const samples: number[] = [];
    const sampleAt = async (msAfterSynth: number): Promise<number> => {
      const elapsed = Date.now() - synthStart;
      if (elapsed < msAfterSynth) {
        await page.waitForTimeout(msAfterSynth - elapsed);
      }
      const t = (await reportBody.textContent()) ?? "";
      return t.length;
    };

    samples.push(await sampleAt(1_000));
    samples.push(await sampleAt(3_000));
    samples.push(await sampleAt(6_000));

    // Wait for the run to finish — phase chip becomes "Done" (the chip
    // shows the literal string "Done" once phase === "done"; see
    // ResearchMode.tsx). Generous timeout for slow Ollama hosts.
    await expect(phaseChip).toHaveText(/Done/i, { timeout: 90_000 });
    seenPhases.add("Done");
    pollingDone = true;
    await pollTask;

    // Strictly-increasing DOM text length proves streaming is happening,
    // not all-at-once. Sampling starts AT synthesizing-phase begin, so
    // each sample lands inside the token stream and length must grow.
    const finalText = (await reportBody.textContent()) ?? "";
    const finalLen = finalText.length;
    expect(
      finalLen,
      `Final report text was empty after done — got ${finalLen} chars`
    ).toBeGreaterThan(0);
    expect(
      samples[1],
      `Expected DOM text length at synth+3s (${samples[1]}) > at synth+1s (${samples[0]})`
    ).toBeGreaterThan(samples[0]);
    expect(
      samples[2],
      `Expected DOM text length at synth+6s (${samples[2]}) > at synth+3s (${samples[1]})`
    ).toBeGreaterThan(samples[1]);

    // Phase advanced through at least 3 distinct values across the run
    // (Decomposing → Searching → Synthesizing → Done is the full set).
    expect(
      seenPhases.size,
      `Expected phase chip to advance through ≥3 distinct values, ` +
        `saw: ${JSON.stringify(Array.from(seenPhases))}`
    ).toBeGreaterThanOrEqual(3);

    // After "done", citation markers and the Sources Used section must
    // be present in the rendered report.
    expect(
      finalText,
      `Report did not contain a citation marker [1] after done. ` +
        `First 200 chars: ${finalText.slice(0, 200)}`
    ).toMatch(/\[1\]/);
    expect(
      finalText,
      `Report did not contain "Sources Used" section after done.`
    ).toMatch(/Sources Used/i);
  });
});

test.describe("Research tab — citation anchoring", () => {
  test("clicking a [N] anchor scrolls the matching #source-N into view", async ({
    page,
  }) => {
    test.setTimeout(120_000);

    await page.goto("/");
    await page.getByRole("tab", { name: /Research/i }).click();

    const queryInput = page.getByPlaceholder(/AI funding rounds/i);
    await expect(queryInput).toBeVisible({ timeout: 10_000 });
    await queryInput.fill(SHORT_QUESTION);
    await page.getByRole("button", { name: /^Research$/i }).click();

    const phaseChip = page.getByTestId("research-phase-chip");
    await expect(phaseChip).toHaveText(/Done/i, { timeout: 90_000 });

    // Locate the first inline citation anchor inside the report body.
    // Post-done, the renderer wraps `[N]` markers in <a class="citation"
    // href="#source-N">. We pick the first link that targets a source.
    const reportBody = page.getByTestId("research-report-body");
    const firstCitation = reportBody.locator('a.citation[href^="#source-"]').first();
    await expect(
      firstCitation,
      "Expected at least one inline [N] citation anchor in the report"
    ).toBeVisible({ timeout: 5_000 });

    // Pull the source number off the href so we know which target to
    // assert visibility on.
    const href = await firstCitation.getAttribute("href");
    expect(href).toMatch(/^#source-\d+$/);
    const targetId = (href ?? "").slice(1); // strip leading "#"

    await firstCitation.click();

    // Smooth-scroll completes asynchronously; give the browser a
    // moment to settle before asserting in-viewport.
    await page.waitForTimeout(700);

    const target = page.locator(`#${targetId}`);
    await expect(target).toBeVisible();
    await expect(target).toBeInViewport({ ratio: 0.5 });
  });
});

test.describe("Research tab — cancel flow", () => {
  test("cancel button aborts the in-flight run and leaves the console clean", async ({
    page,
  }) => {
    test.setTimeout(30_000);

    const errors = installConsoleErrorListener(page);

    await page.goto("/");
    await page.getByRole("tab", { name: /Research/i }).click();

    const queryInput = page.getByPlaceholder(/AI funding rounds/i);
    await expect(queryInput).toBeVisible({ timeout: 10_000 });
    await queryInput.fill(SHORT_QUESTION);

    const submitBtn = page.getByRole("button", { name: /^Research$/i });
    await submitBtn.click();

    // The Submit button flips to "Researching..." while in flight, which
    // means its disabled attribute is set. We wait for that flip to be
    // sure we're cancelling a real in-flight run, not a no-op.
    await expect(
      page.getByRole("button", { name: /Researching/i })
    ).toBeVisible({ timeout: 10_000 });

    // The phase chip becomes visible early in the run (well before
    // any Ollama generation completes — "Decomposing" fires
    // synchronously on submit).
    const phaseChip = page.getByTestId("research-phase-chip");
    await expect(phaseChip).toBeVisible({ timeout: 10_000 });

    // Click Cancel while the run is in flight.
    const cancelBtn = page.getByTestId("research-cancel-btn");
    await expect(cancelBtn).toBeVisible({ timeout: 5_000 });
    await cancelBtn.click();

    // Cancel button disappears (only rendered while isResearching).
    await expect(cancelBtn).toBeHidden({ timeout: 5_000 });

    // Submit button re-enables — its disabled attribute is removed
    // and the label flips back to "Research".
    const submitBtnAfter = page.getByRole("button", { name: /^Research$/i });
    await expect(submitBtnAfter).toBeVisible({ timeout: 5_000 });
    await expect(submitBtnAfter).toBeEnabled();

    // No console errors during the cancel flow. AbortError is a normal
    // signal that the SSE reader exits via the silent catch path; the
    // frontend swallows it before it ever reaches console.error.
    assertConsoleClean(errors);
  });
});

test.describe("Research tab — error UX", () => {
  test("mocked SSE error shows the error panel and Retry triggers a second POST", async ({
    page,
  }) => {
    test.setTimeout(30_000);

    let researchPostCount = 0;

    // Intercept the SSE endpoint and return a properly-framed
    // text/event-stream response with a single error frame. The
    // frontend's SSE parser splits on \n\n, so the trailing blank line
    // is required.
    await page.route("**/api/research", async (route) => {
      researchPostCount += 1;
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
        body:
          'data: {"type":"error","data":"Simulated failure"}\n\n',
      });
    });

    try {
      await page.goto("/");
      await page.getByRole("tab", { name: /Research/i }).click();

      const queryInput = page.getByPlaceholder(/AI funding rounds/i);
      await expect(queryInput).toBeVisible({ timeout: 10_000 });
      await queryInput.fill(SHORT_QUESTION);
      await page.getByRole("button", { name: /^Research$/i }).click();

      // Error panel appears with the "Research interrupted" copy.
      const errorPanel = page.getByTestId("research-error-panel");
      await expect(errorPanel).toBeVisible({ timeout: 10_000 });
      await expect(errorPanel).toContainText(/interrupted/i);

      expect(
        researchPostCount,
        `Expected exactly 1 POST /api/research before retry, saw ${researchPostCount}`
      ).toBe(1);

      // Click Retry — the route handler is still installed, so the
      // second POST returns the same error frame and the panel stays.
      const retryBtn = page.getByTestId("research-retry-btn");
      await expect(retryBtn).toBeVisible();
      await retryBtn.click();

      // Wait for the post counter to bump. The route handler increments
      // synchronously when the request is intercepted, so a short
      // expect.poll is enough.
      await expect
        .poll(() => researchPostCount, {
          timeout: 10_000,
          message: "Retry did not trigger a second POST /api/research",
        })
        .toBeGreaterThanOrEqual(2);

      // Error panel still visible after the retry (same mocked frame).
      await expect(errorPanel).toBeVisible({ timeout: 10_000 });
    } finally {
      // Always tear down the route handler so it doesn't leak into
      // sibling tests.
      await page.unroute("**/api/research");
    }
  });
});

test.describe("Research tab — rubric pass on streamed report", () => {
  test("all 8 rubric helpers pass against a real research run", async ({
    page,
  }) => {
    test.setTimeout(120_000);

    const errors = installConsoleErrorListener(page);

    await page.goto("/");
    await page.getByRole("tab", { name: /Research/i }).click();

    const queryInput = page.getByPlaceholder(/AI funding rounds/i);
    await expect(queryInput).toBeVisible({ timeout: 10_000 });
    await queryInput.fill(SHORT_QUESTION);
    await page.getByRole("button", { name: /^Research$/i }).click();

    const phaseChip = page.getByTestId("research-phase-chip");
    await expect(phaseChip).toBeVisible({ timeout: 15_000 });
    await expect(phaseChip).toHaveText(/Done/i, { timeout: 90_000 });

    // Stable scope selector — the report card has its own testid and
    // the body is its child. Helpers walk visible text only, so the
    // scope can be the whole research card without false positives
    // from other tabs.
    const scope = '[data-testid="research-report-card"]';
    const bodyScope = '[data-testid="research-report-body"]';

    // ---- Category 1: content integrity ----------------------------------
    await assertNoHtmlEntities(page, scope);
    await assertNoMojibake(page, scope);
    await assertNoUndefinedNullObjectObject(page, scope);

    // ---- Category 4: layout / overflow ----------------------------------
    // Both the body itself and the active tab's panel root must not
    // overflow horizontally — long URLs / unbroken tokens are the
    // common culprit and we have overflowWrap:anywhere set in
    // ResearchMode to defeat them.
    await assertNoHorizontalOverflow(page, bodyScope);
    await assertNoHorizontalOverflow(
      page,
      '[data-state="active"][role="tabpanel"]'
    );

    // ---- Category 3: no duplicate sibling paragraphs --------------------
    // The agent shouldn't render the same paragraph twice. We scope
    // to the report body's direct paragraph children.
    await assertNoDuplicateSiblings(
      page,
      `${bodyScope} p`,
      "Report body paragraphs"
    );

    // ---- Category 7: no mock / seed data leak ---------------------------
    await assertNoMockDataLeak(page, scope);

    // ---- Category 6: console hygiene ------------------------------------
    assertConsoleClean(errors);
  });
});
