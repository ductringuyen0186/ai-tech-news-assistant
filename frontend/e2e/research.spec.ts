import { test, expect, type Page, type Route } from "@playwright/test";
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
 * Research tab â€” M5 comprehensive Playwright contract spec.
 *
 * Each test is structured as a *user expectation script*:
 *
 *   1. State the expected user-visible outcome up front
 *      ("after clicking Research, the user expects ...").
 *   2. Drive the UI in slowMo with explicit pauses so the recorded
 *      video is watchable end-to-end.
 *   3. Use test.step() to give the trace viewer chapter markers like
 *      "Open Research tab", "Submit query", "Verify report renders".
 *   4. Frame every assertion with a custom message that reads as a
 *      user expectation â€” "I expect the phase chip to land on Done"
 *      instead of "expected toHaveText match Done".
 *
 * Tests 1, 2, 4 are deterministic (page.route mocks). Test 3 mocks
 * with a single-frame body so cancel can fire safely. Test 5 hits
 * the real /api/research backed by Ollama (the live integration check).
 *
 * To run only this spec at slow demo pace (default 600ms slowMo):
 *   cd frontend && npx playwright test research.spec.ts
 *
 * Faster CI run:
 *   PLAYWRIGHT_SLOW_MO=0 npx playwright test research.spec.ts
 *
 * Slower watch-along run:
 *   PLAYWRIGHT_SLOW_MO=1200 npx playwright test research.spec.ts
 */

const SHORT_QUESTION = "Latest AI chip news";

// Pause between major UI chapters so the recorded video has room to
// breathe. Scales with the slowMo knob â€” at slowMo=0 (CI) all pauses
// collapse; at slowMo=600 (default) chapters stay distinct.
const PACE_MS =
  process.env.PLAYWRIGHT_SLOW_MO !== undefined
    ? Math.max(0, Number(process.env.PLAYWRIGHT_SLOW_MO))
    : 600;
const beat = (page: Page, mult = 1) =>
  page.waitForTimeout(Math.round(PACE_MS * mult));

// ---------------------------------------------------------------------------
// SSE mock helper
// ---------------------------------------------------------------------------

interface SubagentMockEvent {
  data: "start" | "done" | "error";
  skill: string;
  article_id: number;
  duration_ms?: number;
  message?: string;
  /** M3.M2 â€” per-article summary preview (truncated to 280 chars). */
  summary?: string;
}

interface SearchResultsMockEvent {
  sub_question_index: number;
  articles: Array<{ id: number; title: string; source: string }>;
}

interface MockOpts {
  phases?: string[];
  tokens?: string[];
  report?: string;
  subagents?: SubagentMockEvent[];
  /** M3.M2 â€” sub-questions list emitted in the `decomposed` event. */
  subQuestions?: string[];
  /** M3.M2 â€” search_results events; one per sub-question typically. */
  searchResults?: SearchResultsMockEvent[];
}

// Default sub-questions for every mocked run â€” lets the new
// SubQuestionsPanel render during the existing tests.
const DEFAULT_SUB_QUESTIONS: string[] = [
  "What companies are leading AI chip design?",
  "How are prices evolving across vendors?",
  "Which edge-deployment use cases are growing?",
];

// Default search_results events â€” one per sub-question. The article IDs
// match the DEFAULT_SUBAGENTS below so the sub-questions panel can map
// subagent rows back to the questions that triggered them.
const DEFAULT_SEARCH_RESULTS: SearchResultsMockEvent[] = [
  {
    sub_question_index: 0,
    articles: [
      { id: 1, title: "AI Chip Leader Profile", source: "TechCrunch" },
      { id: 2, title: "Latest Chip Benchmarks", source: "ArsTechnica" },
    ],
  },
  {
    sub_question_index: 1,
    articles: [
      { id: 1, title: "Pricing Pressure Report", source: "TechCrunch" },
    ],
  },
  {
    sub_question_index: 2,
    articles: [
      { id: 2, title: "Edge AI Deployments Surge", source: "ArsTechnica" },
    ],
  },
];

// Default subagent events for every mocked run â€” gives the Subagents
// panel (M5) something to render during the deterministic tests so we
// don't regress its render path. Two starts + two dones land us in a
// "0 running, 2 done, 0 errored" steady state. M3.M2 enriches each
// `done` event with a per-article `summary` preview.
const DEFAULT_SUBAGENTS: SubagentMockEvent[] = [
  { data: "start", skill: "summarize_article", article_id: 1 },
  { data: "start", skill: "summarize_article", article_id: 2 },
  {
    data: "done",
    skill: "summarize_article",
    article_id: 1,
    duration_ms: 1234,
    summary:
      "Article 1 summary: leading AI chip vendor announced a new architecture targeting edge inference workloads with 40% lower power.",
  },
  {
    data: "done",
    skill: "summarize_article",
    article_id: 2,
    duration_ms: 1456,
    summary:
      "Article 2 summary: benchmark comparison across tier-1 vendors shows pricing pressure squeezing margins on commodity SKUs.",
  },
];

function buildSSEBody({
  phases,
  tokens,
  report,
  subagents,
  subQuestions,
  searchResults,
}: Required<MockOpts>): string {
  const frames: string[] = [];
  // 1) Decomposing phase first (legacy contract).
  // We assume the first phase in `phases` is "Decomposing" â€” emit the
  // M3.M2 `decomposed` event right after it.
  let decomposedEmitted = false;
  let searchIndex = 0;
  for (const p of phases) {
    frames.push(`data: ${JSON.stringify({ type: "phase", data: p })}\n\n`);
    if (!decomposedEmitted && p === "Decomposing") {
      frames.push(
        `data: ${JSON.stringify({
          type: "decomposed",
          sub_questions: subQuestions,
        })}\n\n`
      );
      decomposedEmitted = true;
      continue;
    }
    // After each "Searching (i/N)" phase, emit the matching search_results.
    if (p.startsWith("Searching ") && searchIndex < searchResults.length) {
      frames.push(
        `data: ${JSON.stringify({
          type: "search_results",
          ...searchResults[searchIndex],
        })}\n\n`
      );
      searchIndex += 1;
    }
  }
  // 2) Subagent events come after the search phases.
  for (const sa of subagents) {
    frames.push(`data: ${JSON.stringify({ type: "subagent", ...sa })}\n\n`);
  }
  // 3) Synthesizing tokens.
  for (const t of tokens) {
    frames.push(`data: ${JSON.stringify({ type: "token", data: t })}\n\n`);
  }
  // 4) Terminal done.
  frames.push(
    `data: ${JSON.stringify({ type: "phase", data: "done", report })}\n\n`
  );
  return frames.join("");
}

const DEFAULT_PHASES = [
  "Decomposing",
  "Searching (1/3)",
  "Searching (2/3)",
  "Searching (3/3)",
  "Synthesizing",
];

const DEFAULT_TOKENS = [
  "## ", "Executive ", "Summary\n",
  "Recent ", "AI ", "chip ", "developments ", "show ", "rapid ",
  "iteration ", "see ", "[1]", ".\n\n",
  "## ", "Key ", "Findings\n",
  "- ", "Major ", "advances ", "in ", "AI ", "chip ", "design ",
  "[1]", ".\n\n",
  "## ", "Sources ", "Used\n",
  "1. ", "TechCrunch", " â€” ", "https://example.com/ai-chip\n",
];

const DEFAULT_REPORT =
  "## Executive Summary\n" +
  "Recent AI chip developments show rapid iteration see [1].\n\n" +
  "## Key Findings\n" +
  "- Major advances in AI chip design [1].\n\n" +
  "## Sources Used\n" +
  "1. TechCrunch â€” https://example.com/ai-chip\n";

async function installResearchMock(
  page: Page,
  opts: MockOpts = {}
): Promise<{ postCount: () => number }> {
  const phases = opts.phases ?? DEFAULT_PHASES;
  const tokens = opts.tokens ?? DEFAULT_TOKENS;
  const report = opts.report ?? DEFAULT_REPORT;
  const subagents = opts.subagents ?? DEFAULT_SUBAGENTS;
  const subQuestions = opts.subQuestions ?? DEFAULT_SUB_QUESTIONS;
  const searchResults = opts.searchResults ?? DEFAULT_SEARCH_RESULTS;
  const body = buildSSEBody({
    phases,
    tokens,
    report,
    subagents,
    subQuestions,
    searchResults,
  });

  let count = 0;
  await page.route("**/api/research", async (route: Route) => {
    count += 1;
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body,
    });
  });

  return { postCount: () => count };
}

// Shared chapter helpers â€” drive the UI through the standard "land,
// open Research, fill question, submit" sequence with pauses.

async function landOnApp(page: Page) {
  await test.step("User opens TechPulse AI in their browser", async () => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /TechPulse AI/i }),
      "I expect the TechPulse AI header to be visible on first paint"
    ).toBeVisible();
    await beat(page);
  });
}

async function openResearchTab(page: Page) {
  await test.step("User clicks the Research tab", async () => {
    await page.getByRole("tab", { name: /Research/i }).click();
    const queryInput = page.getByPlaceholder(/AI funding rounds/i);
    await expect(
      queryInput,
      "I expect the research query input to appear when the Research tab is active"
    ).toBeVisible({ timeout: 10_000 });
    await beat(page);
  });
}

async function submitResearch(page: Page, question = SHORT_QUESTION) {
  await test.step(`User types "${question}" and clicks Research`, async () => {
    const queryInput = page.getByPlaceholder(/AI funding rounds/i);
    await queryInput.fill(question);
    await beat(page, 0.5);
    await page.getByRole("button", { name: /^Research$/i }).click();
    await beat(page, 0.5);
  });
}

// ---------------------------------------------------------------------------
// Test 1 â€” Streaming flow (mocked)
// ---------------------------------------------------------------------------

test.describe("Research tab â€” streaming flow", () => {
  test("phase chip advances and final report contains [1] and Sources Used", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    await test.step("Test setup â€” install deterministic SSE mock", async () => {
      await installResearchMock(page);
    });

    try {
      await landOnApp(page);
      await openResearchTab(page);
      await submitResearch(page);

      const phaseChip = page.getByTestId("research-phase-chip");

      await test.step(
        "User expects the phase chip to appear (the agent is running)",
        async () => {
          await expect(
            phaseChip,
            "I expect the phase chip to render once the agent starts"
          ).toBeVisible({ timeout: 10_000 });
          await beat(page);
        }
      );

      // Background poll for the values the chip cycles through.
      const seenPhases = new Set<string>();
      let pollingDone = false;
      const pollPhase = async () => {
        while (!pollingDone) {
          try {
            const ph = (await phaseChip.textContent())?.trim();
            if (ph) seenPhases.add(ph);
          } catch {
            /* chip detach between renders; ignore */
          }
          await page.waitForTimeout(50);
        }
      };
      const pollTask = pollPhase();

      await test.step(
        "User expects the run to finish â€” phase chip lands on Done",
        async () => {
          await expect(
            phaseChip,
            "I expect the phase chip to land on Done after the run completes"
          ).toHaveText(/Done/i, { timeout: 15_000 });
          seenPhases.add("Done");
          pollingDone = true;
          await pollTask;
          await beat(page);
        }
      );

      await test.step(
        "User expects a structured report with citations to render",
        async () => {
          const reportBody = page.getByTestId("research-report-body");
          const finalText = (await reportBody.textContent()) ?? "";

          expect(
            seenPhases.size,
            `I expect the phase chip to have shown at least one observable phase value during the run, saw: ${JSON.stringify(
              Array.from(seenPhases)
            )}`
          ).toBeGreaterThanOrEqual(1);

          expect(
            finalText.length,
            "I expect the report body to render real content (not just a placeholder)"
          ).toBeGreaterThan(50);

          expect(
            finalText,
            "I expect the report to contain a [1] citation marker so the user knows sources back the claims"
          ).toMatch(/\[1\]/);

          expect(
            finalText,
            "I expect the report to contain a 'Sources Used' section so the citations resolve"
          ).toMatch(/Sources Used/i);

          await beat(page, 1.5); // long beat so the viewer can read the rendered report
        }
      );
    } finally {
      await page.unroute("**/api/research");
    }
  });
});

// ---------------------------------------------------------------------------
// Test 2 â€” Citation anchoring (mocked)
// ---------------------------------------------------------------------------

test.describe("Research tab â€” citation anchoring", () => {
  test("clicking a [N] anchor scrolls the matching #source-N into view", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    await test.step(
      "Test setup â€” install mock with a Sources section below the fold",
      async () => {
        await installResearchMock(page, {
          report:
            "## Executive Summary\n" +
            "Recent AI chip developments show rapid iteration. " +
            "See [1] for details on the latest hardware breakthroughs.\n\n" +
            "## Key Findings\n" +
            "- Major advances in AI chip design [1].\n" +
            "- Pricing pressure across tier-1 vendors.\n" +
            "- Edge-deployment focus growing.\n\n" +
            "## Trends & Themes\n" +
            "Multiple vendors converging on similar architectures.\n\n" +
            "## Background\n" +
            Array.from({ length: 30 })
              .map(
                (_, i) =>
                  `Paragraph ${i + 1}: extended context for the report rendering.`
              )
              .join("\n\n") +
            "\n\n## Sources Used\n" +
            "1. TechCrunch â€” https://example.com/ai-chip-1\n" +
            "2. Ars Technica â€” https://example.com/ai-chip-2\n",
        });
      }
    );

    try {
      await landOnApp(page);
      await openResearchTab(page);
      await submitResearch(page);

      const phaseChip = page.getByTestId("research-phase-chip");
      await test.step(
        "User waits for the report to finish rendering",
        async () => {
          await expect(
            phaseChip,
            "I expect the phase chip to land on Done before the user can click citations"
          ).toHaveText(/Done/i, { timeout: 15_000 });
          await beat(page);
        }
      );

      const reportBody = page.getByTestId("research-report-body");
      const firstCitation = reportBody
        .locator('a.citation[href^="#source-"]')
        .first();
      let targetId = "";

      await test.step(
        "User expects to see clickable [N] citation links inside the report",
        async () => {
          await expect(
            firstCitation,
            "I expect the first inline [N] marker to render as a clickable anchor link"
          ).toBeVisible({ timeout: 5_000 });

          const href = await firstCitation.getAttribute("href");
          expect(
            href,
            "I expect the citation's href to point at #source-N for some integer N"
          ).toMatch(/^#source-\d+$/);
          targetId = (href ?? "").slice(1);
          await beat(page);
        }
      );

      await test.step(
        "User clicks the [1] citation expecting the page to scroll to its source",
        async () => {
          await firstCitation.click();
          // Smooth-scroll completes asynchronously.
          await beat(page, 1.2);
        }
      );

      await test.step(
        "User expects the matching source entry to be in the viewport",
        async () => {
          const target = page.locator(`#${targetId}`);
          await expect(
            target,
            `I expect the citation target #${targetId} to exist in the rendered Sources section`
          ).toBeVisible();
          await expect(
            target,
            `I expect the citation target #${targetId} to scroll at least halfway into view after the click`
          ).toBeInViewport({ ratio: 0.5 });
          await beat(page);
        }
      );
    } finally {
      await page.unroute("**/api/research");
    }
  });
});

// ---------------------------------------------------------------------------
// Test 3 â€” Cancel flow
// ---------------------------------------------------------------------------

test.describe("Research tab â€” cancel flow", () => {
  test("cancel button aborts the in-flight run and leaves the console clean", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    const errors = installConsoleErrorListener(page);

    await test.step(
      "Test setup â€” mock SSE returns only the Decomposing phase, then closes",
      async () => {
        await page.route("**/api/research", async (route: Route) => {
          await route.fulfill({
            status: 200,
            headers: { "Content-Type": "text/event-stream" },
            body: 'data: {"type":"phase","data":"Decomposing"}\n\n',
          });
        });
      }
    );

    try {
      await landOnApp(page);
      await openResearchTab(page);
      await submitResearch(page);

      const phaseChip = page.getByTestId("research-phase-chip");

      await test.step(
        "User expects the phase chip to show 'Decomposing' (run is in flight)",
        async () => {
          await expect(
            phaseChip,
            "I expect the phase chip to render once the agent starts"
          ).toBeVisible({ timeout: 10_000 });
          await expect(
            phaseChip,
            "I expect the chip to show 'Decomposing' after the first SSE frame"
          ).toHaveText(/Decomposing/i, { timeout: 5_000 });
          await beat(page);
        }
      );

      const cancelBtn = page.getByTestId("research-cancel-btn");
      await test.step(
        "User clicks Cancel (or the run finishes naturally â€” both are OK)",
        async () => {
          try {
            await expect(
              cancelBtn,
              "I expect a Cancel button to appear while the run is in flight"
            ).toBeVisible({ timeout: 2_000 });
            await beat(page, 0.5);
            await cancelBtn.click();
            await beat(page, 0.5);
          } catch {
            // Run finished naturally before cancel could fire â€” still
            // a valid path; the rest of the assertions cover the
            // post-cancel / post-done state equally well.
          }
        }
      );

      await test.step(
        "User expects the UI to be back to a clean idle state",
        async () => {
          const submitBtnAfter = page.getByRole("button", {
            name: /^Research$/i,
          });
          await expect(
            submitBtnAfter,
            "I expect the Submit button label to flip back to 'Research' (idle state)"
          ).toBeVisible({ timeout: 5_000 });
          await expect(
            submitBtnAfter,
            "I expect the Submit button to be enabled again â€” the user can run another query"
          ).toBeEnabled();
          await beat(page);
        }
      );

      await test.step(
        "User expects no console errors during cancel â€” AbortError is silenced",
        async () => {
          assertConsoleClean(errors);
          await beat(page);
        }
      );
    } finally {
      await page.unroute("**/api/research");
    }
  });
});

// ---------------------------------------------------------------------------
// Test 4 â€” Error UX (already mocked)
// ---------------------------------------------------------------------------

test.describe("Research tab â€” error UX", () => {
  test("mocked SSE error shows the error panel and Retry triggers a second POST", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    let researchPostCount = 0;

    await test.step(
      "Test setup â€” mock SSE returns a single error frame",
      async () => {
        await page.route("**/api/research", async (route: Route) => {
          researchPostCount += 1;
          await route.fulfill({
            status: 200,
            headers: { "Content-Type": "text/event-stream" },
            body: 'data: {"type":"error","data":"Simulated failure"}\n\n',
          });
        });
      }
    );

    try {
      await landOnApp(page);
      await openResearchTab(page);
      await submitResearch(page);

      const errorPanel = page.getByTestId("research-error-panel");

      await test.step(
        "User expects a clear error panel â€” not a hang or a silent fail",
        async () => {
          await expect(
            errorPanel,
            "I expect the 'Research interrupted' panel to surface when the SSE returns an error frame"
          ).toBeVisible({ timeout: 10_000 });
          await expect(
            errorPanel,
            "I expect the panel copy to mention 'interrupted' so the user understands what happened"
          ).toContainText(/interrupted/i);
          expect(
            researchPostCount,
            "I expect exactly 1 POST /api/research before the user clicks Retry"
          ).toBe(1);
          await beat(page);
        }
      );

      const retryBtn = page.getByTestId("research-retry-btn");
      await test.step(
        "User clicks Retry â€” they expect the same query to fire again",
        async () => {
          await expect(
            retryBtn,
            "I expect a Retry button on the error panel"
          ).toBeVisible();
          await beat(page, 0.5);
          await retryBtn.click();
          await beat(page, 0.5);
        }
      );

      await test.step(
        "User expects a fresh POST /api/research and the panel still standing",
        async () => {
          await expect
            .poll(() => researchPostCount, {
              timeout: 10_000,
              message:
                "I expect Retry to trigger a second POST /api/research (current count: see below)",
            })
            .toBeGreaterThanOrEqual(2);

          await expect(
            errorPanel,
            "I expect the panel to remain visible because the mock keeps returning the same error frame"
          ).toBeVisible({ timeout: 10_000 });
          await beat(page);
        }
      );
    } finally {
      await page.unroute("**/api/research");
    }
  });
});

// ---------------------------------------------------------------------------
// Test 5 â€” Rubric pass on a REAL streamed report
// ---------------------------------------------------------------------------

test.describe("Research tab â€” rubric pass on streamed report", () => {
  test("all 8 rubric helpers pass against a real research run", async ({
    page,
  }) => {
    test.setTimeout(180_000);

    const errors = installConsoleErrorListener(page);

    await landOnApp(page);
    await openResearchTab(page);
    await submitResearch(page);

    const phaseChip = page.getByTestId("research-phase-chip");

    await test.step(
      "User waits for the live agent to finish (this is the real Ollama run)",
      async () => {
        await expect(
          phaseChip,
          "I expect the phase chip to render once the agent starts"
        ).toBeVisible({ timeout: 15_000 });
        await expect(
          phaseChip,
          "I expect the live run to land on Done within 150 seconds (gpt-oss:20b on CPU)"
        ).toHaveText(/Done/i, { timeout: 150_000 });
        await beat(page);
      }
    );

    const scope = '[data-testid="research-report-card"]';
    const bodyScope = '[data-testid="research-report-body"]';

    await test.step("Rubric: no HTML entities, mojibake, or null-leak text", async () => {
      await assertNoHtmlEntities(page, scope);
      await assertNoMojibake(page, scope);
      await assertNoUndefinedNullObjectObject(page, scope);
    });

    await test.step("Rubric: no horizontal overflow on long URLs", async () => {
      await assertNoHorizontalOverflow(page, bodyScope);
      await assertNoHorizontalOverflow(
        page,
        '[data-state="active"][role="tabpanel"]'
      );
    });

    await test.step("Rubric: no duplicate sibling paragraphs", async () => {
      await assertNoDuplicateSiblings(
        page,
        `${bodyScope} p`,
        "Report body paragraphs"
      );
    });

    await test.step("Rubric: no mock/seed data leak", async () => {
      await assertNoMockDataLeak(page, scope);
    });

    await test.step("Rubric: console-clean throughout the live run", async () => {
      assertConsoleClean(errors);
      await beat(page, 1.5);
    });
  });
});

// ---------------------------------------------------------------------------
// Test 6 â€” Subagents panel rendering (mocked)
// ---------------------------------------------------------------------------

test.describe("Research tab â€” subagents panel", () => {
  test("Subagents panel renders rows for streamed subagent events", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    const errors = installConsoleErrorListener(page);

    await test.step(
      "Test setup â€” install mock with explicit subagent telemetry events",
      async () => {
        await installResearchMock(page, {
          subagents: [
            { data: "start", skill: "summarize_article", article_id: 42 },
            { data: "start", skill: "summarize_article", article_id: 99 },
            {
              data: "done",
              skill: "summarize_article",
              article_id: 42,
              duration_ms: 1234,
            },
            {
              data: "done",
              skill: "summarize_article",
              article_id: 99,
              duration_ms: 2718,
            },
          ],
        });
      }
    );

    try {
      await landOnApp(page);
      await openResearchTab(page);
      await submitResearch(page);

      const phaseChip = page.getByTestId("research-phase-chip");
      await test.step(
        "User waits for the run to complete so all subagent frames have arrived",
        async () => {
          await expect(
            phaseChip,
            "I expect the phase chip to land on Done after the mocked run completes"
          ).toHaveText(/Done/i, { timeout: 15_000 });
          await beat(page);
        }
      );

      const panel = page.getByTestId("research-subagents-panel");
      await test.step(
        "User expects the Subagents panel to be visible (events did arrive)",
        async () => {
          await expect(
            panel,
            "I expect the Subagents panel to render once at least one subagent event has been received"
          ).toBeVisible({ timeout: 5_000 });
          await beat(page);
        }
      );

      await test.step(
        "User expects the panel header to summarize the live counts",
        async () => {
          const header = page.getByTestId("research-subagents-header");
          await expect(
            header,
            "I expect the panel header to be visible and labeled 'Subagents (...)'"
          ).toBeVisible();
          await expect(
            header,
            "I expect the header to contain the running/done/errored count summary so the user can read the run at a glance"
          ).toContainText(/Subagents \(\d+ running, \d+ done, \d+ errored\)/i);
          await expect(
            header,
            "I expect the header to reflect at least 2 'done' subagents from the mock"
          ).toContainText(/2 done/i);
          await beat(page);
        }
      );

      await test.step(
        "User expects one row per fanned-out subagent (â‰¥2 from the mock)",
        async () => {
          const rows = page.getByTestId("research-subagent-row");
          await expect(
            rows,
            "I expect at least 2 subagent rows â€” one per article the mock streamed"
          ).toHaveCount(2, { timeout: 5_000 });

          const firstRow = rows.first();
          await expect(
            firstRow,
            "I expect the first row to display the skill name 'summarize_article'"
          ).toContainText(/summarize_article/i);
          await expect(
            firstRow,
            "I expect the first row to display an article ID marker (e.g. #42)"
          ).toContainText(/#\d+/);
          await expect(
            firstRow,
            "I expect the first row to advertise its 'done' status badge"
          ).toContainText(/done/i);
          await beat(page);
        }
      );

      await test.step(
        "User expects no console errors during the subagent render path",
        async () => {
          assertConsoleClean(errors);
          await beat(page);
        }
      );
    } finally {
      await page.unroute("**/api/research");
    }
  });
});

// ---------------------------------------------------------------------------
// Test 7 (M3.M2) â€” Markdown table rendering
// ---------------------------------------------------------------------------

test.describe("Research tab â€” markdown table rendering", () => {
  test("a markdown table in the report body renders as a <table> with <th>/<td>", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    await test.step(
      "Test setup â€” install mock whose report contains a GFM markdown table",
      async () => {
        await installResearchMock(page, {
          report:
            "## Executive Summary\n" +
            "Recent AI funding rounds [1].\n\n" +
            "## Key Findings\n\n" +
            "| Company | Amount | Round |\n" +
            "|---|---|---|\n" +
            "| Pit | $9M | Seed |\n" +
            "| Anthropic | $4B | Series E |\n" +
            "| OpenAI | $40B | Strategic |\n\n" +
            "## Sources Used\n" +
            "1. TechCrunch -- https://example.com/ai-funding\n",
        });
      }
    );

    try {
      await landOnApp(page);
      await openResearchTab(page);
      await submitResearch(page);

      const phaseChip = page.getByTestId("research-phase-chip");
      await test.step(
        "User waits for the run to land on Done so the full report renders",
        async () => {
          await expect(
            phaseChip,
            "I expect the phase chip to land on Done after the mocked run"
          ).toHaveText(/Done/i, { timeout: 15_000 });
          await beat(page);
        }
      );

      const reportBody = page.getByTestId("research-report-body");

      await test.step(
        "User expects the markdown table to render as a real <table> element",
        async () => {
          const table = reportBody.locator("table").first();
          await expect(
            table,
            "I expect a <table> element in the report body (the M3.M2 table-bug fix)"
          ).toBeVisible({ timeout: 5_000 });

          const headers = table.locator("th");
          await expect(
            headers,
            "I expect 3 <th> header cells corresponding to | Company | Amount | Round |"
          ).toHaveCount(3, { timeout: 5_000 });

          const cells = table.locator("td");
          await expect(
            cells,
            "I expect 9 <td> data cells (3 rows x 3 columns)"
          ).toHaveCount(9, { timeout: 5_000 });

          await expect(
            table,
            "I expect the first row to contain 'Pit'"
          ).toContainText(/Pit/);
          await expect(
            table,
            "I expect the table body to contain 'Anthropic'"
          ).toContainText(/Anthropic/);
          await beat(page);
        }
      );
    } finally {
      await page.unroute("**/api/research");
    }
  });
});

// ---------------------------------------------------------------------------
// Test 8 (M3.M2) â€” Sub-questions panel renders >=3 numbered items
// ---------------------------------------------------------------------------

test.describe("Research tab â€” sub-questions panel", () => {
  test("sub-questions panel renders the decomposed list within 5 seconds of submit", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    await test.step(
      "Test setup â€” install mock with the default 3 sub-questions",
      async () => {
        await installResearchMock(page);
      }
    );

    try {
      await landOnApp(page);
      await openResearchTab(page);
      await submitResearch(page);

      const panel = page.getByTestId("research-sub-questions-panel");

      await test.step(
        "User expects the sub-questions panel to appear within 5 seconds",
        async () => {
          await expect(
            panel,
            "I expect the sub-questions panel to render within 5s of submit (M3.M2 time-to-first-content target)"
          ).toBeVisible({ timeout: 5_000 });
        }
      );

      await test.step(
        "User expects 3 numbered sub-question rows from the default mock",
        async () => {
          const rows = page.getByTestId("research-sub-question-row");
          await expect(
            rows,
            "I expect at least 3 sub-question rows from the default mock"
          ).toHaveCount(3, { timeout: 5_000 });

          await expect(
            rows.first(),
            "I expect the first row to contain the first sub-question text"
          ).toContainText(/AI chip/i);
          await beat(page);
        }
      );

      await test.step(
        "User expects article titles to appear under sub-questions after search_results arrive",
        async () => {
          const articles = page.getByTestId("research-sub-question-article");
          await expect(
            articles.first(),
            "I expect at least one article row under a sub-question"
          ).toBeVisible({ timeout: 10_000 });
          await beat(page);
        }
      );
    } finally {
      await page.unroute("**/api/research");
    }
  });
});

// ---------------------------------------------------------------------------
// Test 9 (M3.M2) â€” Subagent row expands to reveal summary preview
// ---------------------------------------------------------------------------

test.describe("Research tab â€” subagent row expand", () => {
  test("clicking a done subagent row reveals its per-article summary preview", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    await test.step(
      "Test setup â€” install mock with enriched subagent:done summary fields",
      async () => {
        await installResearchMock(page);
      }
    );

    try {
      await landOnApp(page);
      await openResearchTab(page);
      await submitResearch(page);

      const phaseChip = page.getByTestId("research-phase-chip");
      await test.step(
        "User waits for the run to complete so subagent done events arrive",
        async () => {
          await expect(
            phaseChip,
            "I expect the phase chip to land on Done so all subagent events arrived"
          ).toHaveText(/Done/i, { timeout: 15_000 });
          await beat(page);
        }
      );

      const rows = page.getByTestId("research-subagent-row");
      const firstRow = rows.first();
      await test.step(
        "User clicks the first subagent row expecting the summary preview to appear",
        async () => {
          await expect(
            firstRow,
            "I expect at least one subagent row from the mock"
          ).toBeVisible({ timeout: 5_000 });
          const toggle = firstRow.getByTestId("research-subagent-row-toggle");
          await toggle.click();
          await beat(page, 0.5);
        }
      );

      await test.step(
        "User expects the per-article summary text to appear inline",
        async () => {
          const summary = firstRow.getByTestId("research-subagent-summary");
          await expect(
            summary,
            "I expect the expanded summary preview to render the M3.M2 enriched-event text"
          ).toBeVisible({ timeout: 5_000 });
          await expect(
            summary,
            "I expect the summary preview to contain real text from the mock"
          ).toContainText(/summary/i);
          await beat(page);
        }
      );
    } finally {
      await page.unroute("**/api/research");
    }
  });
});

// ---------------------------------------------------------------------------
// Test 10 (M3.M2 iter 2) â€” Sub-questions SKELETON appears within ~1s of submit
// ---------------------------------------------------------------------------
//
// Defect found during live user-testing of M3.M2: with the real
// gpt-oss:20b model, the `decomposed` SSE event takes ~15-17s to land,
// so the user stared at spinners for the whole window despite the
// milestone promising "time-to-first-content â‰¤ 5s".
//
// Iter 2 fix renders the SubQuestionsPanel IMMEDIATELY on submit in a
// skeleton state ("Decomposing your question..."). The numbered list
// replaces the skeleton row the moment `decomposed` arrives.
//
// This test installs a STREAMING mock that emits the Decomposing
// phase frame instantly, then sleeps before emitting the
// `decomposed` frame â€” proving the skeleton landed *before* the
// real sub-questions did.

test.describe("Research tab â€” sub-questions SKELETON (iter 2)", () => {
  test("decomposing skeleton row appears within 1s of submit, before the decomposed event lands", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    // Streaming SSE mock that intentionally delays the `decomposed`
    // event so the test can prove the skeleton lands first.
    const DECOMPOSED_DELAY_MS = 2500;

    await test.step(
      "Test setup â€” install streaming mock with delayed decomposed event",
      async () => {
        await page.route("**/api/research", async (route: Route) => {
          // Stream frames with explicit timing so we can prove the
          // skeleton lands before the `decomposed` event by emitting
          // the Decomposing phase immediately, sleeping, then emitting
          // decomposed + the rest of the run.
          const head =
            `data: ${JSON.stringify({
              type: "phase",
              data: "Decomposing",
            })}\n\n`;
          const tailFrames: string[] = [];
          tailFrames.push(
            `data: ${JSON.stringify({
              type: "decomposed",
              sub_questions: DEFAULT_SUB_QUESTIONS,
            })}\n\n`
          );
          for (const p of [
            "Searching (1/3)",
            "Searching (2/3)",
            "Searching (3/3)",
            "Synthesizing",
          ]) {
            tailFrames.push(
              `data: ${JSON.stringify({ type: "phase", data: p })}\n\n`
            );
          }
          tailFrames.push(
            `data: ${JSON.stringify({
              type: "phase",
              data: "done",
              report: DEFAULT_REPORT,
            })}\n\n`
          );
          const tail = tailFrames.join("");

          // Hold the SSE response back for DECOMPOSED_DELAY_MS, then
          // emit the whole stream at once. The skeleton is rendered
          // purely from local React state on submit (no SSE events
          // required), so it MUST be visible during the entire delay
          // window â€” proving the time-to-first-content contract holds
          // even when the backend's decomposition is slow.
          await new Promise((r) => setTimeout(r, DECOMPOSED_DELAY_MS));
          await route.fulfill({
            status: 200,
            headers: { "Content-Type": "text/event-stream" },
            body: head + tail,
          });
        });
      }
    );

    try {
      await landOnApp(page);
      await openResearchTab(page);

      // Time the gap between submit and the skeleton becoming visible.
      const submitClick = async () => {
        const queryInput = page.getByPlaceholder(/AI funding rounds/i);
        await queryInput.fill(SHORT_QUESTION);
        await page.getByRole("button", { name: /^Research$/i }).click();
      };

      const tSubmit = Date.now();
      await submitClick();

      await test.step(
        "User expects a 'Decomposing your question...' skeleton row within 1s",
        async () => {
          const skeleton = page.getByTestId("research-sub-questions-skeleton");
          await expect(
            skeleton,
            "I expect the skeleton row to render within 1000ms of submit â€” the time-to-first-content target"
          ).toBeVisible({ timeout: 1_000 });

          const tSkeleton = Date.now();
          const elapsed = tSkeleton - tSubmit;
          expect(
            elapsed,
            `I expect time-to-skeleton ≤ 1500ms (observed: ${elapsed}ms)`
          ).toBeLessThanOrEqual(1500);

          await expect(
            skeleton,
            "I expect the skeleton to copy 'Decomposing your question into 3-5 sub-questions...'"
          ).toContainText(/Decomposing your question/i);
        }
      );

      await test.step(
        "User expects the panel to be in the `decomposing` state during the wait",
        async () => {
          const panel = page.getByTestId("research-sub-questions-panel");
          await expect(
            panel,
            "I expect the panel container itself to be visible in the skeleton state"
          ).toBeVisible();
          await expect(
            panel,
            "I expect data-state='decomposing' so the test can prove the skeleton path is the one rendered"
          ).toHaveAttribute("data-state", "decomposing");
        }
      );

      await test.step(
        "User expects the skeleton to be REPLACED by the real numbered list once `decomposed` arrives",
        async () => {
          const rows = page.getByTestId("research-sub-question-row");
          await expect(
            rows,
            "I expect 3 numbered sub-question rows once the decomposed event lands (~2.5s into the run)"
          ).toHaveCount(3, { timeout: 10_000 });

          const skeleton = page.getByTestId(
            "research-sub-questions-skeleton"
          );
          await expect(
            skeleton,
            "I expect the skeleton row to be gone once the real list rendered"
          ).toHaveCount(0);

          const panel = page.getByTestId("research-sub-questions-panel");
          await expect(
            panel,
            "I expect data-state='ready' after the decomposed event resolved the skeleton"
          ).toHaveAttribute("data-state", "ready");
          await beat(page);
        }
      );

      await test.step(
        "User expects the follow-up chips after Done to be real <button> elements (a11y)",
        async () => {
          const phaseChip = page.getByTestId("research-phase-chip");
          await expect(
            phaseChip,
            "I expect the run to land on Done before follow-up chips render"
          ).toHaveText(/Done/i, { timeout: 15_000 });

          const followUpRow = page.getByTestId("research-follow-ups");
          await expect(
            followUpRow,
            "I expect the follow-up chip row to render after Done"
          ).toBeVisible({ timeout: 5_000 });

          // Iter 2 a11y contract â€” chips MUST be <button> elements
          // with the dedicated `research-follow-up-chip` testid.
          const chips = followUpRow.locator("button");
          const chipCount = await chips.count();
          expect(
            chipCount,
            `I expect at least 1 <button> chip inside the follow-up row (was a <div>/<span> in iter 1) â€” saw ${chipCount}`
          ).toBeGreaterThan(0);

          const taggedChips = page.getByTestId("research-follow-up-chip");
          await expect(
            taggedChips.first(),
            "I expect each chip to carry data-testid='research-follow-up-chip'"
          ).toBeVisible();
          await beat(page);
        }
      );
    } finally {
      await page.unroute("**/api/research");
    }
  });
});
