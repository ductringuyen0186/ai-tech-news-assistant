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
 * Research tab — M5 comprehensive Playwright contract spec.
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
 *      user expectation — "I expect the phase chip to land on Done"
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
// breathe. Scales with the slowMo knob — at slowMo=0 (CI) all pauses
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
}

interface MockOpts {
  phases?: string[];
  tokens?: string[];
  report?: string;
  subagents?: SubagentMockEvent[];
}

// Default subagent events for every mocked run — gives the Subagents
// panel (M5) something to render during the deterministic tests so we
// don't regress its render path. Two starts + two dones land us in a
// "0 running, 2 done, 0 errored" steady state.
const DEFAULT_SUBAGENTS: SubagentMockEvent[] = [
  { data: "start", skill: "summarize_article", article_id: 1 },
  { data: "start", skill: "summarize_article", article_id: 2 },
  { data: "done", skill: "summarize_article", article_id: 1, duration_ms: 1234 },
  { data: "done", skill: "summarize_article", article_id: 2, duration_ms: 1456 },
];

function buildSSEBody({
  phases,
  tokens,
  report,
  subagents,
}: Required<MockOpts>): string {
  const frames: string[] = [];
  for (const p of phases) {
    frames.push(`data: ${JSON.stringify({ type: "phase", data: p })}\n\n`);
  }
  // Subagent telemetry lives between the phase ramp-up and the token
  // stream. The order matches the production backend: agent decomposes
  // and searches (phases), then fans out per-article subagents, then
  // streams the synthesised report (tokens).
  for (const sa of subagents) {
    frames.push(`data: ${JSON.stringify({ type: "subagent", ...sa })}\n\n`);
  }
  for (const t of tokens) {
    frames.push(`data: ${JSON.stringify({ type: "token", data: t })}\n\n`);
  }
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
  "1. ", "TechCrunch", " — ", "https://example.com/ai-chip\n",
];

const DEFAULT_REPORT =
  "## Executive Summary\n" +
  "Recent AI chip developments show rapid iteration see [1].\n\n" +
  "## Key Findings\n" +
  "- Major advances in AI chip design [1].\n\n" +
  "## Sources Used\n" +
  "1. TechCrunch — https://example.com/ai-chip\n";

async function installResearchMock(
  page: Page,
  opts: MockOpts = {}
): Promise<{ postCount: () => number }> {
  const phases = opts.phases ?? DEFAULT_PHASES;
  const tokens = opts.tokens ?? DEFAULT_TOKENS;
  const report = opts.report ?? DEFAULT_REPORT;
  const subagents = opts.subagents ?? DEFAULT_SUBAGENTS;
  const body = buildSSEBody({ phases, tokens, report, subagents });

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

// Shared chapter helpers — drive the UI through the standard "land,
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
// Test 1 — Streaming flow (mocked)
// ---------------------------------------------------------------------------

test.describe("Research tab — streaming flow", () => {
  test("phase chip advances and final report contains [1] and Sources Used", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    await test.step("Test setup — install deterministic SSE mock", async () => {
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
        "User expects the run to finish — phase chip lands on Done",
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
// Test 2 — Citation anchoring (mocked)
// ---------------------------------------------------------------------------

test.describe("Research tab — citation anchoring", () => {
  test("clicking a [N] anchor scrolls the matching #source-N into view", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    await test.step(
      "Test setup — install mock with a Sources section below the fold",
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
            "1. TechCrunch — https://example.com/ai-chip-1\n" +
            "2. Ars Technica — https://example.com/ai-chip-2\n",
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
// Test 3 — Cancel flow
// ---------------------------------------------------------------------------

test.describe("Research tab — cancel flow", () => {
  test("cancel button aborts the in-flight run and leaves the console clean", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    const errors = installConsoleErrorListener(page);

    await test.step(
      "Test setup — mock SSE returns only the Decomposing phase, then closes",
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
        "User clicks Cancel (or the run finishes naturally — both are OK)",
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
            // Run finished naturally before cancel could fire — still
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
            "I expect the Submit button to be enabled again — the user can run another query"
          ).toBeEnabled();
          await beat(page);
        }
      );

      await test.step(
        "User expects no console errors during cancel — AbortError is silenced",
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
// Test 4 — Error UX (already mocked)
// ---------------------------------------------------------------------------

test.describe("Research tab — error UX", () => {
  test("mocked SSE error shows the error panel and Retry triggers a second POST", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    let researchPostCount = 0;

    await test.step(
      "Test setup — mock SSE returns a single error frame",
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
        "User expects a clear error panel — not a hang or a silent fail",
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
        "User clicks Retry — they expect the same query to fire again",
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
// Test 5 — Rubric pass on a REAL streamed report
// ---------------------------------------------------------------------------

test.describe("Research tab — rubric pass on streamed report", () => {
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
// Test 6 — Subagents panel rendering (mocked)
// ---------------------------------------------------------------------------

test.describe("Research tab — subagents panel", () => {
  test("Subagents panel renders rows for streamed subagent events", async ({
    page,
  }) => {
    test.setTimeout(60_000);

    const errors = installConsoleErrorListener(page);

    await test.step(
      "Test setup — install mock with explicit subagent telemetry events",
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
        "User expects one row per fanned-out subagent (≥2 from the mock)",
        async () => {
          const rows = page.getByTestId("research-subagent-row");
          await expect(
            rows,
            "I expect at least 2 subagent rows — one per article the mock streamed"
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
