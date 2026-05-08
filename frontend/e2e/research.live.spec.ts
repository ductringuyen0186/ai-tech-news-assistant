import { test, expect } from "@playwright/test";

/**
 * Research tab — LIVE Ollama integration spec.
 *
 * These tests hit the real /api/research SSE endpoint backed by Ollama
 * (gpt-oss:20b on CPU). Wall-clock can run 30-180s per test; this spec
 * is excluded from the default `npx playwright test` run (see
 * `playwright.config.ts`) and should be invoked explicitly:
 *
 *   cd frontend && npx playwright test research.live.spec.ts \
 *     --config playwright.live.config.ts
 *
 * OR by passing the file path directly when the default config's
 * testIgnore is overridden:
 *
 *   cd frontend && npx playwright test --grep @live
 *
 * The mocked counterparts in `research.spec.ts` (Tests 1 + 2) cover the
 * frontend's SSE consumption logic deterministically; this file is the
 * release-verification check that the agent itself works end-to-end.
 */

const SHORT_QUESTION = "Latest AI chip news";

test.describe("Research tab — live streaming flow @live", () => {
  test("phase chip advances, DOM text grows over time, citations + Sources appear", async ({
    page,
  }) => {
    test.setTimeout(180_000);

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

    const phaseChip = page.getByTestId("research-phase-chip");
    await expect(phaseChip).toBeVisible({ timeout: 15_000 });

    const seenPhases = new Set<string>();
    const reportBody = page.getByTestId("research-report-body");
    let pollingDone = false;
    const pollPhase = async () => {
      while (!pollingDone) {
        try {
          const ph = (await phaseChip.textContent())?.trim();
          if (ph) seenPhases.add(ph);
        } catch {
          // chip may detach between renders
        }
        await page.waitForTimeout(150);
      }
    };
    const pollTask = pollPhase();

    // gpt-oss:20b decompose+search is slow; allow up to 120s before tokens.
    await expect(phaseChip).toHaveText(/synthesizing/i, { timeout: 120_000 });

    // Wait for the placeholder text to be replaced before sampling.
    await expect
      .poll(
        async () => {
          const t = (await reportBody.textContent()) ?? "";
          return t.length > 30 || /##\s/.test(t);
        },
        { timeout: 60_000, message: "tokens never started flowing in 60s" }
      )
      .toBeTruthy();
    const tokensStart = Date.now();

    const samples: number[] = [];
    const sampleAt = async (msAfterTokens: number): Promise<number> => {
      const elapsed = Date.now() - tokensStart;
      if (elapsed < msAfterTokens) {
        await page.waitForTimeout(msAfterTokens - elapsed);
      }
      const t = (await reportBody.textContent()) ?? "";
      return t.length;
    };

    samples.push(await sampleAt(0));
    samples.push(await sampleAt(2_000));
    samples.push(await sampleAt(5_000));

    await expect(phaseChip).toHaveText(/Done/i, { timeout: 90_000 });
    seenPhases.add("Done");
    pollingDone = true;
    await pollTask;

    const finalText = (await reportBody.textContent()) ?? "";
    expect(finalText.length).toBeGreaterThan(0);
    expect(samples[1]).toBeGreaterThan(samples[0]);
    expect(samples[2]).toBeGreaterThan(samples[1]);
    expect(seenPhases.size).toBeGreaterThanOrEqual(3);
    expect(finalText).toMatch(/\[1\]/);
    expect(finalText).toMatch(/Sources Used/i);
  });
});

test.describe("Research tab — live citation anchoring @live", () => {
  test("clicking a [N] anchor scrolls the matching #source-N into view", async ({
    page,
  }) => {
    test.setTimeout(180_000);

    await page.goto("/");
    await page.getByRole("tab", { name: /Research/i }).click();

    const queryInput = page.getByPlaceholder(/AI funding rounds/i);
    await expect(queryInput).toBeVisible({ timeout: 10_000 });
    await queryInput.fill(SHORT_QUESTION);
    await page.getByRole("button", { name: /^Research$/i }).click();

    const phaseChip = page.getByTestId("research-phase-chip");
    await expect(phaseChip).toHaveText(/Done/i, { timeout: 150_000 });

    const reportBody = page.getByTestId("research-report-body");
    const firstCitation = reportBody
      .locator('a.citation[href^="#source-"]')
      .first();
    await expect(firstCitation).toBeVisible({ timeout: 10_000 });

    const href = await firstCitation.getAttribute("href");
    expect(href).toMatch(/^#source-\d+$/);
    const targetId = (href ?? "").slice(1);

    await firstCitation.click();
    await page.waitForTimeout(700);

    const target = page.locator(`#${targetId}`);
    await expect(target).toBeVisible();
    await expect(target).toBeInViewport({ ratio: 0.5 });
  });
});
