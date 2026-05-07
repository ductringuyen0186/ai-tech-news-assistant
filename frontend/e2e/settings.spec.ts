import { test, expect } from "@playwright/test";

/**
 * Settings tab - asserts category preferences persist across page reload,
 * proving the backend write actually happened (not just optimistic UI).
 *
 * Uses "Hardware" as the toggle target because the chip list is now
 * dynamically derived from /api/news/categories (the union of category
 * tags actually present in the article DB), so the previous "Robotics"
 * choice would not appear unless an ingested feed maps to it. "Hardware"
 * matches the Ars Technica feed mapping in IngestionService.DEFAULT_FEEDS
 * and is reliably present.
 */

const TARGET_CATEGORY = "Hardware";

test.describe("Settings tab", () => {
  test("toggling a category and saving persists across reload", async ({ page }) => {
    test.setTimeout(60_000);

    await page.goto("/");
    await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();

    // Switch to the Settings tab.
    await page.getByRole("tab", { name: /Settings/i }).click();

    // Wait for the topic-preferences card to render.
    await expect(page.getByText(/Topic Preferences/i)).toBeVisible({
      timeout: 10_000,
    });

    // Find the Robotics row. It's a <label> wrapping a Checkbox + text.
    const robotRow = page.locator("label").filter({ hasText: TARGET_CATEGORY });
    await expect(robotRow).toBeVisible();

    // Read its current state (was it already selected?).
    const checkbox = robotRow.locator('button[role="checkbox"]');
    const initialState = await checkbox.getAttribute("aria-checked");
    const wasChecked = initialState === "true";

    // Toggle it (click) - we want to flip and verify the FLIPPED state
    // persists after reload. That proves the backend wrote the new value.
    if (wasChecked) {
      // Toggle off, save, reload - assert it's off after reload.
      await checkbox.click();
      await page.getByRole("button", { name: /Save Preferences/i }).click();
      await expect(
        page.getByText(/Preferences saved successfully/i)
      ).toBeVisible({ timeout: 10_000 });

      await page.reload();
      await page.getByRole("tab", { name: /Settings/i }).click();
      await expect(page.getByText(/Topic Preferences/i)).toBeVisible({
        timeout: 10_000,
      });

      const reloadedRow = page.locator("label").filter({ hasText: TARGET_CATEGORY });
      const reloadedState = await reloadedRow
        .locator('button[role="checkbox"]')
        .getAttribute("aria-checked");
      expect(
        reloadedState,
        `${TARGET_CATEGORY} should have persisted as unchecked after reload`
      ).toBe("false");

      // Restore: toggle it back on so subsequent tests find the original
      // state. (Not strictly required - tests are independent - but it's
      // courteous when sharing a real backend.)
      await reloadedRow.locator('button[role="checkbox"]').click();
      await page.getByRole("button", { name: /Save Preferences/i }).click();
    } else {
      // Standard path: toggle on, save, reload, expect still on.
      await checkbox.click();
      await expect(checkbox).toHaveAttribute("aria-checked", "true");

      await page.getByRole("button", { name: /Save Preferences/i }).click();
      await expect(
        page.getByText(/Preferences saved successfully/i)
      ).toBeVisible({ timeout: 10_000 });

      await page.reload();
      await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();

      await page.getByRole("tab", { name: /Settings/i }).click();
      await expect(page.getByText(/Topic Preferences/i)).toBeVisible({
        timeout: 10_000,
      });

      const reloadedRow = page.locator("label").filter({ hasText: TARGET_CATEGORY });
      const reloadedState = await reloadedRow
        .locator('button[role="checkbox"]')
        .getAttribute("aria-checked");
      expect(
        reloadedState,
        `${TARGET_CATEGORY} should still be selected after reload - proves backend persistence`
      ).toBe("true");
    }
  });
});
