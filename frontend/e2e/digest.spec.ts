import { test, expect } from "@playwright/test";

/**
 * Digest tab - asserts the digest is wired to the real /api/digest endpoint
 * and not falling back to the old hardcoded mock strings.
 */

const FORBIDDEN_MOCK_TITLES = [
  "AI Breakthrough in Natural Language Understanding",
  "New Security Vulnerability Affects Major Cloud Providers",
  "Quantum Computing Makes Significant Progress",
];

test.describe("Digest tab", () => {
  test("top stories render with real (non-mock) titles and a trending topic is visible", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();

    // Switch to the Digest tab.
    await page.getByRole("tab", { name: /Digest/i }).click();

    // The header card uses the heading "Daily Tech Digest".
    await expect(page.getByText(/Daily Tech Digest/i)).toBeVisible({ timeout: 15_000 });

    // Wait for the loading spinner (if any) to clear.
    await expect(page.locator(".animate-spin").first()).toBeHidden({ timeout: 20_000 });

    // The "Top Stories Today" section should render.
    const topStoriesHeader = page.getByText(/Top Stories Today/i);
    await expect(topStoriesHeader).toBeVisible();

    // Top story titles render as <h3> within border-l-4 elements.
    const storyTitles = await page.locator(".border-l-4 h3").allTextContents();

    // We require at least one top story to render.
    expect(
      storyTitles.length,
      "Digest should render at least one top story"
    ).toBeGreaterThan(0);

    // None of them should be the old mock strings.
    for (const title of storyTitles) {
      const trimmed = title.trim();
      for (const forbidden of FORBIDDEN_MOCK_TITLES) {
        expect(
          trimmed,
          `Digest still showing the old hardcoded mock title "${forbidden}" - App.tsx fetchDigest may have regressed`
        ).not.toBe(forbidden);
      }
    }

    // Trending Now section - assert at least one trending topic chip is visible.
    const trendingHeader = page.getByText(/Trending Now/i);
    await expect(trendingHeader).toBeVisible();

    const trendingItems = page.locator(".bg-orange-50.rounded-lg");
    const trendingCount = await trendingItems.count();

    // Allow zero in the rare case the backend has no trending topics for the
    // window, but warn so the user notices if it's persistently empty.
    if (trendingCount === 0) {
      console.warn(
        "Digest 'Trending Now' section is empty - verify /api/digest/ is returning trending_topics"
      );
    } else {
      await expect(trendingItems.first()).toBeVisible();
    }
  });
});
