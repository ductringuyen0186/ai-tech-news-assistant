import { test, expect, type Page, type Route } from "@playwright/test";

/**
 * Saved Research — M3.M5 Playwright contract.
 *
 * Validates the full Save -> list -> open -> delete loop end-to-end with
 * the /api/research SSE stream and the /api/saved-research CRUD surface
 * both mocked so the test is deterministic and does not depend on Ollama
 * or on the host SQLite file.
 *
 * Run only this spec:
 *   cd frontend && npx playwright test saved-research.spec.ts
 */

const SHORT_QUESTION = "Latest AI chip news";

const PACE_MS =
  process.env.PLAYWRIGHT_SLOW_MO !== undefined
    ? Math.max(0, Number(process.env.PLAYWRIGHT_SLOW_MO))
    : 250;
const beat = (page: Page, mult = 1) =>
  page.waitForTimeout(Math.round(PACE_MS * mult));

// ------------------------------------------------------------------ //
//  /api/research SSE mock
// ------------------------------------------------------------------ //

const DEFAULT_REPORT =
  "## Executive Summary\n" +
  "Recent AI chip developments show rapid iteration. OpenAI Anthropic Google announced new architectures [1].\n\n" +
  "## Key Findings\n" +
  "- Major advances in AI chip design [1].\n\n" +
  "## Sources Used\n" +
  "1. TechCrunch — https://example.com/ai-chip\n";

function buildSSEBody(report: string): string {
  const frames: string[] = [];
  frames.push(`data: ${JSON.stringify({ type: "phase", data: "Decomposing" })}\n\n`);
  frames.push(
    `data: ${JSON.stringify({
      type: "decomposed",
      sub_questions: ["What companies are leading?", "How is pricing evolving?"],
    })}\n\n`
  );
  frames.push(`data: ${JSON.stringify({ type: "phase", data: "Searching (1/2)" })}\n\n`);
  frames.push(
    `data: ${JSON.stringify({
      type: "search_results",
      sub_question_index: 0,
      articles: [{ id: 1, title: "Article", source: "TechCrunch" }],
    })}\n\n`
  );
  frames.push(`data: ${JSON.stringify({ type: "phase", data: "Synthesizing" })}\n\n`);
  frames.push(`data: ${JSON.stringify({ type: "token", data: report })}\n\n`);
  frames.push(
    `data: ${JSON.stringify({ type: "phase", data: "done", report })}\n\n`
  );
  return frames.join("");
}

async function installResearchMock(page: Page) {
  const body = buildSSEBody(DEFAULT_REPORT);
  await page.route("**/api/research", async (route: Route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body,
    });
  });
}

// ------------------------------------------------------------------ //
//  /api/saved-research CRUD mock — in-memory backed.
// ------------------------------------------------------------------ //

interface SavedRow {
  id: number;
  question: string;
  report_md: string;
  sources: Array<Record<string, unknown>>;
  created_at: string;
}

async function installSavedResearchMock(page: Page) {
  const state = {
    rows: [] as SavedRow[],
    nextId: 1,
  };

  // POST + GET (list).
  await page.route("**/api/saved-research", async (route: Route) => {
    const method = route.request().method();
    if (method === "POST") {
      const body = route.request().postDataJSON() as {
        question: string;
        report_md: string;
        sources?: Array<Record<string, unknown>>;
      };
      const row: SavedRow = {
        id: state.nextId++,
        question: body.question,
        report_md: body.report_md,
        sources: body.sources ?? [],
        created_at: new Date().toISOString().replace("T", " ").slice(0, 19),
      };
      state.rows.unshift(row);
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(row),
      });
      return;
    }
    if (method === "GET") {
      const list = state.rows.map((r) => ({
        id: r.id,
        question: r.question,
        created_at: r.created_at,
      }));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(list),
      });
      return;
    }
    await route.continue();
  });

  // GET (by id) + DELETE.
  await page.route("**/api/saved-research/*", async (route: Route) => {
    const method = route.request().method();
    const url = route.request().url();
    const idMatch = url.match(/saved-research\/(\d+)/);
    const id = idMatch ? parseInt(idMatch[1], 10) : NaN;
    const idx = state.rows.findIndex((r) => r.id === id);
    if (method === "GET") {
      if (idx === -1) {
        await route.fulfill({ status: 404, body: "" });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(state.rows[idx]),
      });
      return;
    }
    if (method === "DELETE") {
      if (idx === -1) {
        await route.fulfill({ status: 404, body: "" });
        return;
      }
      state.rows.splice(idx, 1);
      await route.fulfill({ status: 204, body: "" });
      return;
    }
    await route.continue();
  });

  return state;
}

// ------------------------------------------------------------------ //
//  Helpers
// ------------------------------------------------------------------ //

async function landOnApp(page: Page) {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /TechPulse AI/i })
  ).toBeVisible({ timeout: 15_000 });
}

async function runResearchAndWaitForDone(page: Page) {
  await page.getByRole("tab", { name: "Research", exact: true }).click();
  const queryInput = page.getByPlaceholder(/AI funding rounds/i);
  await expect(queryInput).toBeVisible({ timeout: 10_000 });
  await queryInput.fill(SHORT_QUESTION);
  await page.getByRole("button", { name: /^Research$/i }).click();

  // Wait for the report to render and the Save button to appear.
  await expect(page.getByTestId("research-save-btn")).toBeVisible({
    timeout: 20_000,
  });
}

// ------------------------------------------------------------------ //
//  Tests
// ------------------------------------------------------------------ //

test.describe("Saved research — full Save -> list -> open -> delete flow", () => {
  test("save button persists report, then list/open/delete cycle works", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    await installResearchMock(page);
    await installSavedResearchMock(page);

    await landOnApp(page);
    await runResearchAndWaitForDone(page);

    // 1) Click Save — button flips to "Saved ✓" + success toast.
    const saveBtn = page.getByTestId("research-save-btn");
    await expect(saveBtn).toHaveText(/Save/);
    await saveBtn.click();
    await expect(saveBtn).toHaveText(/Saved/, { timeout: 5_000 });
    await expect(saveBtn).toBeDisabled();
    await beat(page);

    // 2) Navigate to the Saved tab — the list should contain the row.
    await page.getByRole("tab", { name: "Saved", exact: true }).click();
    await expect(page.getByTestId("saved-research-list")).toBeVisible({
      timeout: 10_000,
    });
    const items = page.getByTestId("saved-research-item");
    await expect(items).toHaveCount(1);
    await expect(items.first()).toContainText(SHORT_QUESTION);

    // 3) Open the saved report — detail view renders the markdown.
    await items.first().locator("button").first().click();
    await expect(page.getByTestId("saved-research-detail")).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText(/Executive Summary/i)).toBeVisible();
    await expect(page.getByText(/Sources Used/i)).toBeVisible();

    // 4) Back to list -> delete the row.
    await page.getByTestId("saved-research-back-btn").click();
    await expect(page.getByTestId("saved-research-list")).toBeVisible();
    await page.getByTestId("saved-research-delete-btn").first().click();

    // Empty state should appear (optimistic delete drops the row instantly).
    await expect(page.getByTestId("saved-research-empty")).toBeVisible({
      timeout: 5_000,
    });
    await expect(page.getByTestId("saved-research-item")).toHaveCount(0);
  });

  test("empty state renders when no saved research", async ({ page }) => {
    await installSavedResearchMock(page);
    await landOnApp(page);

    await page.getByRole("tab", { name: "Saved", exact: true }).click();
    await expect(page.getByTestId("saved-research-list")).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByTestId("saved-research-empty")).toBeVisible();
    await expect(
      page.getByText(/No saved research yet/i)
    ).toBeVisible();
  });

  test("Saved sidebar entry no longer shows the Soon placeholder", async ({
    page,
  }) => {
    await installSavedResearchMock(page);
    await landOnApp(page);

    const savedTab = page.getByRole("tab", { name: "Saved", exact: true });
    await expect(savedTab).toBeVisible();
    // The placeholder badge text "Soon" should not appear on the Saved tab.
    await expect(savedTab).not.toContainText(/Soon/i);
  });

  test("follow-up suggestion chips render after a completed research run", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    await installResearchMock(page);
    await installSavedResearchMock(page);

    await landOnApp(page);
    await runResearchAndWaitForDone(page);

    const followUps = page.getByTestId("research-follow-ups");
    await expect(followUps).toBeVisible({ timeout: 10_000 });
    const chips = page.getByTestId("research-follow-up-chip");
    await expect(chips).toHaveCount(3);
  });
});
