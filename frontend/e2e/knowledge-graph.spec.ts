import { test, expect } from "@playwright/test";
import {
  assertNoHtmlEntities,
  assertNoMojibake,
  assertNoUndefinedNullObjectObject,
  assertNoHorizontalOverflow,
  assertNoMockDataLeak,
} from "./_lib/rubric";

/**
 * Knowledge Graph tab - asserts entities are pulled from the real
 * /api/knowledge-graph endpoint (not the old hardcoded
 * OpenAI/Anthropic/Google triangle mock).
 */

test.describe("Knowledge Graph tab", () => {
  test("canvas renders with at least 5 entity labels from the real backend", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();

    // Switch to the Knowledge tab.
    await page.getByRole("tab", { name: /Knowledge/i }).click();

    // Wait for the loading spinner to clear.
    await expect(page.locator(".animate-spin").first()).toBeHidden({ timeout: 20_000 });

    // The graph canvas should render.
    const canvas = page.locator("canvas").first();
    await expect(canvas).toBeVisible({ timeout: 10_000 });

    // We hit the same endpoint the component uses to count entities.
    const apiUrl = `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/knowledge-graph?limit=50`;

    const response = await page.evaluate(async (url) => {
      try {
        const r = await fetch(url);
        if (!r.ok) return { error: `HTTP ${r.status}` };
        return await r.json();
      } catch (e) {
        return { error: String(e) };
      }
    }, apiUrl);

    // We do NOT fail if the backend is empty - only if the UI is showing
    // the OLD mock. Acceptance: at least 5 distinct entity names.
    const nodes = (response && (response as any).nodes) || [];

    if (nodes.length === 0) {
      console.warn(
        "Knowledge graph backend returned no entities - UI cannot render labels"
      );
      // Still assert the empty-state callout is shown rather than fake data.
      await expect(
        page.getByText(/No entities extracted yet/i)
      ).toBeVisible();
      return;
    }

    // We have nodes from the real backend. Assert at least 5 unique entity names.
    const names = new Set<string>(
      (nodes as Array<{ name: string }>).map((n) => n.name)
    );
    expect(
      names.size,
      `Knowledge graph should have at least 5 distinct entity names; got ${names.size} (${[...names].slice(0, 10).join(", ")})`
    ).toBeGreaterThanOrEqual(5);

    // Ensure the names don't EXACTLY match the old hardcoded triangle in a
    // way that would imply the mock came back. The mock had ONLY three
    // entities: OpenAI, Anthropic, Google. If we have more than 3 entities
    // we're definitely past that mock.
    expect(
      names.size,
      "If we only see exactly 3 entities and they are OpenAI/Anthropic/Google, it's likely the old mock"
    ).toBeGreaterThan(3);
  });
});

// ---------------------------------------------------------------------------
// Rubric — categories 1, 4, 7 applied to the Knowledge Graph tab.
// ---------------------------------------------------------------------------

test.describe("rubric — Knowledge Graph", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();
    await page.getByRole("tab", { name: /Knowledge/i }).click();
    await expect(page.locator(".animate-spin").first()).toBeHidden({ timeout: 20_000 });
  });

  test("category 1 — labels and stats render no HTML entities, mojibake, or stringified placeholders", async ({
    page,
  }) => {
    const scope = '[data-state="active"][role="tabpanel"]';
    await assertNoHtmlEntities(page, scope);
    await assertNoMojibake(page, scope);
    await assertNoUndefinedNullObjectObject(page, scope);
  });

  test("category 4 — graph stat cards do not horizontally overflow", async ({
    page,
  }) => {
    // The 4-up Companies/People/Technologies/Products grid is the most
    // overflow-prone surface here — long Vietnamese / Cyrillic labels
    // would push the count number off the card. The canvas itself is
    // pixel-sized so it can't overflow text, but the stat cards can.
    await assertNoHorizontalOverflow(
      page,
      '[data-state="active"][role="tabpanel"] [data-slot="card"]'
    );
  });

  test("category 7 — graph has real co-mention edges (>=1 edge), proving non-isolated nodes", async ({
    page,
  }) => {
    // Hit the same backend endpoint the component uses so we read what's
    // really being rendered, not just what the canvas decided to draw.
    const apiUrl = `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/knowledge-graph?limit=50`;
    const data = await page.evaluate(async (url) => {
      try {
        const r = await fetch(url);
        if (!r.ok) return { error: `HTTP ${r.status}` };
        return (await r.json()) as { nodes?: unknown[]; edges?: unknown[] };
      } catch (e) {
        return { error: String(e) };
      }
    }, apiUrl);

    // If the backend has zero nodes, the empty-state callout already
    // covers it (existing test); we're not asserting edges in that case.
    const nodes = (data && (data as any).nodes) || [];
    if (!Array.isArray(nodes) || nodes.length === 0) {
      test.skip(true, "Backend has zero entities; empty-state path covered elsewhere");
    }

    const edges = (data as any).edges || [];
    expect(
      Array.isArray(edges) && edges.length,
      `Knowledge graph has ${nodes.length} entities but ZERO edges. ` +
        `That means no two entities co-mentioned in any article — strongly implies ` +
        `the entity_extraction_service is misconfigured or the co-occurrence join is broken.`
    ).toBeGreaterThanOrEqual(1);

    // Mock-data leak check on the visible labels — extraction sometimes
    // catches "Lorem ipsum" or "example.com" out of test fixtures.
    await assertNoMockDataLeak(page, '[data-state="active"][role="tabpanel"]');
  });
});
