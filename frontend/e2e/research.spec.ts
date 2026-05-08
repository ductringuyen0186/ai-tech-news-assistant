import { test, expect } from "@playwright/test";

/**
 * Research tab — M3 placeholder spec.
 *
 * The full streaming / phase-chip / citations spec lands in M5. For M3 we
 * confirm two minimum invariants:
 *   1. Submitting a query opens a single ``POST /api/research`` request
 *      against the backend (the SSE endpoint), proving the new wiring is
 *      hooked up and the old ``/api/search/semantic`` path is gone.
 *   2. Submitting a query produces SOME visible output — either a phase
 *      chip, a streamed/finalised report, an error panel, or a toast — so
 *      the page is never blank after a click.
 */

test.describe("Research tab", () => {
  test("submit POSTs /api/research and renders a non-blank UI", async ({
    page,
  }) => {
    test.setTimeout(120_000); // Ollama is slow; allow up to 2 min total

    // Capture every request that hits the research endpoint so we can
    // assert at the end that exactly one POST was issued.
    const researchRequests: string[] = [];
    page.on("request", (req) => {
      if (req.url().includes("/api/research") && req.method() === "POST") {
        researchRequests.push(req.url());
      }
    });

    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /TechPulse AI/i })
    ).toBeVisible();

    await page.getByRole("tab", { name: /Research/i }).click();

    const queryInput = page.getByPlaceholder(/AI funding rounds/i);
    await expect(queryInput).toBeVisible({ timeout: 10_000 });
    await queryInput.fill("AI");

    const researchBtn = page.getByRole("button", { name: /^Research$/i });
    await researchBtn.click();

    // The button text changes to "Researching..." while the SSE stream
    // is in flight. We wait for that flip first, then for it to revert.
    await page.waitForTimeout(500);

    // Wait for the run to finish — the in-flight indicator goes away on
    // both ``done`` and ``error`` paths.
    await expect(
      page.getByRole("button", { name: /Researching/i })
    ).toBeHidden({ timeout: 110_000 });

    // Invariant 1: the network panel saw exactly one POST /api/research.
    expect(
      researchRequests.length,
      `Expected exactly one POST /api/research, got ${researchRequests.length}: ${JSON.stringify(researchRequests)}`
    ).toBe(1);

    // Invariant 2: the page is not blank — at minimum, the report card,
    // the phase chip, the error panel, or a toast is visible.
    const phaseChipVisible = await page
      .getByTestId("research-phase-chip")
      .isVisible()
      .catch(() => false);
    const reportBodyVisible = await page
      .getByTestId("research-report-body")
      .isVisible()
      .catch(() => false);
    const errorPanelVisible = await page
      .getByTestId("research-error-panel")
      .isVisible()
      .catch(() => false);
    const toastVisible = await page
      .locator('[data-sonner-toast], [data-sonner-toaster]')
      .first()
      .isVisible()
      .catch(() => false);

    expect(
      phaseChipVisible || reportBodyVisible || errorPanelVisible || toastVisible,
      "Research mode should produce a phase chip, report body, error panel, or toast — not a blank screen"
    ).toBe(true);
  });
});
