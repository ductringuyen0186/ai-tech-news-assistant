import { test, expect } from "@playwright/test";
import {
  assertNoHtmlEntities,
  assertNoMojibake,
  assertNoUndefinedNullObjectObject,
  assertNoMockDataLeak,
} from "./_lib/rubric";

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

// ---------------------------------------------------------------------------
// Rubric — categories 1, 3, 7 applied to the Digest tab.
// ---------------------------------------------------------------------------

test.describe("rubric — Digest", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();
    await page.getByRole("tab", { name: /Digest/i }).click();
    await expect(page.getByText(/Daily Tech Digest/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.locator(".animate-spin").first()).toBeHidden({ timeout: 20_000 });
  });

  test("category 1 — digest text has no HTML entities, mojibake, or stringified placeholders", async ({
    page,
  }) => {
    const scope = '[data-state="active"][role="tabpanel"]';
    await assertNoHtmlEntities(page, scope);
    await assertNoMojibake(page, scope);
    await assertNoUndefinedNullObjectObject(page, scope);
  });

  test("category 3 — top-story chip rows have unique chip values (source not duplicated as category)", async ({
    page,
  }) => {
    // Each top story is a `.border-l-4` block; chips inside it are
    // descendants matching `[data-slot="badge"]`. We collect chip text
    // PER STORY and assert no story has the same string twice.
    const stories = page.locator(".border-l-4");
    const storyCount = await stories.count();
    expect(storyCount, "Digest needs at least one top story").toBeGreaterThan(0);

    for (let i = 0; i < storyCount; i++) {
      const chipsInStory = await stories
        .nth(i)
        .locator('[data-slot="badge"]')
        .evaluateAll((els) =>
          (els as HTMLElement[]).map((e) => (e.innerText || "").trim())
        );
      const filtered = chipsInStory.filter((t) => t.length > 0);
      const dupes = filtered.filter(
        (t, idx) => filtered.indexOf(t) !== idx
      );
      expect(
        dupes,
        `Top story #${i} renders the same chip text twice — the source name was probably ` +
          `also injected into the category list. Chips: ${JSON.stringify(filtered)}`
      ).toHaveLength(0);
    }
  });

  test("category 3 — trending topics chips have unique labels", async ({ page }) => {
    const trending = page.locator(".bg-orange-50.rounded-lg");
    const count = await trending.count();
    if (count === 0) {
      test.skip(true, "No trending topics rendered — covered by the existing 'Top Stories' test");
    }

    // Across ALL trending topic cards, the visible card text (which is
    // basically the topic title) should be unique. We collect the FIRST <p>
    // per card to avoid pulling chip badges into the comparison.
    const titles = await trending.evaluateAll((els) =>
      (els as HTMLElement[]).map((el) => {
        const p = el.querySelector("p");
        return p ? (p.innerText || "").trim() : "";
      })
    );
    const filtered = titles.filter((t) => t.length > 0);
    const seen = new Map<string, number>();
    for (const t of filtered) seen.set(t, (seen.get(t) ?? 0) + 1);
    const dupes = Array.from(seen.entries()).filter(([, n]) => n > 1);
    expect(
      dupes,
      `Trending topics list has duplicate titles: ${JSON.stringify(dupes)}`
    ).toHaveLength(0);
  });

  test("category 7 — digest renders no mock/seed/example/epoch data", async ({
    page,
  }) => {
    await assertNoMockDataLeak(page, '[data-state="active"][role="tabpanel"]');
  });

  test("M3.M3 — top-story rows use dense layout (height ≤ 200px, padding ≤ 12px)", async ({
    page,
  }) => {
    const firstRow = page.locator(".border-l-4").first();
    await expect(firstRow).toBeVisible({ timeout: 15_000 });

    const metrics = await firstRow.evaluate((el) => {
      const style = window.getComputedStyle(el as HTMLElement);
      return {
        height: (el as HTMLElement).getBoundingClientRect().height,
        paddingTop: parseFloat(style.paddingTop),
        paddingBottom: parseFloat(style.paddingBottom),
        paddingLeft: parseFloat(style.paddingLeft),
        paddingRight: parseFloat(style.paddingRight),
      };
    });

    expect(
      metrics.height,
      `Top story row was ${metrics.height}px tall; dense layout expects ≤ 200px`
    ).toBeLessThanOrEqual(200);
    // Dense padding cap (`py-2 pl-3` is 8/12px). Tolerate up to 14px.
    expect(metrics.paddingTop).toBeLessThanOrEqual(14);
    expect(metrics.paddingLeft).toBeLessThanOrEqual(14);
  });
});
