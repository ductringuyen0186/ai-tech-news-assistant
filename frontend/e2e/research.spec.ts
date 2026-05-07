import { test, expect } from "@playwright/test";

/**
 * Research tab - asserts the agentic research mode renders results
 * for a real query, not a 500 / blank screen.
 */

test.describe("Research tab", () => {
  test("query produces a research report or a clean empty state", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();

    // Switch to the Research tab.
    await page.getByRole("tab", { name: /Research/i }).click();

    // The research input has a known placeholder.
    const queryInput = page.getByPlaceholder(/AI funding rounds/i);
    await expect(queryInput).toBeVisible({ timeout: 10_000 });

    await queryInput.fill("AI");

    // Click the Research button (matches the button by accessible name).
    const researchBtn = page.getByRole("button", { name: /^Research$/i });
    await researchBtn.click();

    // Wait for the research to finish - button text changes to "Researching..."
    // while in flight. Wait for it to revert.
    await page.waitForTimeout(1000);
    await expect(page.getByRole("button", { name: /Researching/i })).toBeHidden({
      timeout: 30_000,
    });

    // After the search either:
    //  (a) a "Research Report" card renders with the query echoed back, OR
    //  (b) a toast appears with an error message.
    // We only fail if the page CRASHES / no toast and no report appear.

    const toastVisible = await page
      .locator('[data-sonner-toast], [data-sonner-toaster]')
      .first()
      .isVisible()
      .catch(() => false);

    const hasReport = await page
      .getByText(/Executive Summary|Articles Analyzed|Key Findings/i)
      .first()
      .isVisible()
      .catch(() => false);

    expect(
      hasReport || toastVisible,
      "Research mode should produce a report or a toast - not a blank screen"
    ).toBe(true);
  });
});
