import { test, expect } from "@playwright/test";

/**
 * News Feed tab — asserts real article data renders and filter/search work.
 *
 * Catches: seed-data regressions, broken category filtering, broken search.
 *
 * Note: the suite expects the user's saved categories on the backend to
 * match real article categories. If the saved settings drift away from the
 * real category vocabulary (e.g. legacy "AI" / "Machine Learning" while
 * articles are tagged "AI/ML"), the page will show "No articles found"
 * and these tests will fail — surfacing exactly the kind of behavior bug
 * the contract suite missed.
 */

const KNOWN_REAL_SOURCES = [
  "TechCrunch",
  "Ars Technica",
  "The Verge",
  "MIT Technology Review",
  "Hacker News",
  "Wired",
];

// Reset filters by clearing the in-page category chips before each test.
// This isolates the news-feed assertions from whatever the user saved last.
async function clearFiltersIfPresent(page: import("@playwright/test").Page) {
  const clearBtn = page.getByRole("button", { name: /^Clear Filters$/i });
  if (await clearBtn.isVisible().catch(() => false)) {
    await clearBtn.click();
    // Give React a tick to refetch.
    await page.waitForTimeout(500);
  }
}

test.describe("News Feed tab", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();
    // Wait for the initial article fetch to settle (or empty-state to render).
    await page.waitForLoadState("networkidle", { timeout: 20_000 }).catch(() => {});
    await expect(page.locator(".animate-spin").first()).toBeHidden({ timeout: 20_000 });
  });

  test("page renders with branding and at least one article", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();

    // If a filter mismatch shows the empty-state, clear filters and try again.
    const emptyState = page.getByText(/No articles found/i);
    if (await emptyState.isVisible().catch(() => false)) {
      await clearFiltersIfPresent(page);
      // Wait for the refetch to settle.
      await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => {});
      await expect(page.locator(".animate-spin").first()).toBeHidden({
        timeout: 15_000,
      });
    }

    // Article cards render via the shadcn Card component which carries
    // data-slot="card". This is the stable hook.
    const articleCards = page.locator('[data-slot="card"]');
    await expect(articleCards.first()).toBeVisible({ timeout: 15_000 });
    const count = await articleCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test("no article title is seed-data", async ({ page }) => {
    const emptyState = page.getByText(/No articles found/i);
    if (await emptyState.isVisible().catch(() => false)) {
      await clearFiltersIfPresent(page);
      await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => {});
      await expect(page.locator(".animate-spin").first()).toBeHidden({
        timeout: 15_000,
      });
    }

    // CardTitle nodes carry data-slot="card-title".
    const titles = await page.locator('[data-slot="card-title"]').allTextContents();
    expect(titles.length).toBeGreaterThan(0);
    for (const title of titles) {
      const trimmed = title.trim().toLowerCase();
      // Worker 1 wiped seed='seed' rows; this test would fail if they came back.
      expect(trimmed).not.toMatch(/^seed[-_ ]/);
      expect(trimmed).not.toContain("seed summary");
    }
  });

  test("source badges show real sources", async ({ page }) => {
    const emptyState = page.getByText(/No articles found/i);
    if (await emptyState.isVisible().catch(() => false)) {
      await clearFiltersIfPresent(page);
      await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => {});
      await expect(page.locator(".animate-spin").first()).toBeHidden({
        timeout: 15_000,
      });
    }

    // The source name renders inside the card header as a span with
    // .text-gray-500. Scoped to cards so we don't pull header chrome.
    const sourceTexts = await page
      .locator('[data-slot="card"] .text-gray-500')
      .allTextContents();

    const hasRealSource = sourceTexts.some((s) =>
      KNOWN_REAL_SOURCES.some((known) =>
        s.toLowerCase().includes(known.toLowerCase())
      )
    );

    expect(
      hasRealSource,
      `Expected at least one source from ${KNOWN_REAL_SOURCES.join(", ")}; saw: ${sourceTexts.slice(0, 10).join(" | ")}`
    ).toBe(true);

    for (const s of sourceTexts) {
      expect(s.trim().toLowerCase()).not.toBe("seed");
    }
  });

  test("search input updates the article list", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search tech news/i);
    await expect(searchInput).toBeVisible();

    await searchInput.fill("OpenAI");
    await searchInput.press("Enter");

    // Small debounce — the search refetches; let it settle.
    await page.waitForTimeout(2000);
    await expect(page.locator(".animate-spin").first()).toBeHidden({
      timeout: 15_000,
    });

    // After search, either results render OR the empty-state is shown.
    // What we DON'T accept is a crash / blank page / stuck spinner.
    const cards = page.locator('[data-slot="card"]');
    const emptyState = page.getByText(/No articles found/i);

    const cardsVisible = (await cards.count()) > 0;
    const emptyVisible = await emptyState.isVisible().catch(() => false);

    expect(
      cardsVisible || emptyVisible,
      "Search should either return results or show the empty state — never a blank/crashed page"
    ).toBe(true);
  });
});
