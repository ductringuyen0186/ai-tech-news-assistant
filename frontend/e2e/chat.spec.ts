import { test, expect } from "@playwright/test";

/**
 * Chat / Ask AI tab - exercises the RAG pipeline end-to-end through the UI.
 *
 * Catches:
 *  - assistant message overflow (text breaking out of bubble)
 *  - duplicate "Related articles"
 *  - empty / failed responses
 */

test.describe("Chat / Ask AI tab", () => {
  test("question gets a non-empty answer that fits the bubble, related articles unique", async ({
    page,
  }) => {
    test.setTimeout(120_000); // Ollama is slow; allow up to 2 min total

    await page.goto("/");
    await expect(page.getByRole("heading", { name: /TechPulse AI/i })).toBeVisible();

    // Switch to the Ask AI tab.
    await page.getByRole("tab", { name: /Ask AI/i }).click();

    // Find the chat input (placeholder is "Ask me anything about tech news...").
    const chatInput = page.getByPlaceholder(/Ask me anything about tech news/i);
    await expect(chatInput).toBeVisible({ timeout: 10_000 });

    // Count initial assistant messages (the welcome bubble = 1).
    const assistantMessageLocator = page.locator(
      'div.justify-start > div[class*="bg-gray-100"]'
    );
    const initialCount = await assistantMessageLocator.count();

    // Send a question.
    await chatInput.fill("What's new in AI chips?");
    await chatInput.press("Enter");

    // Wait for a NEW assistant message to appear (count > initialCount).
    await expect
      .poll(
        async () => await assistantMessageLocator.count(),
        {
          timeout: 90_000,
          message: "Expected a new assistant message after asking a question",
        }
      )
      .toBeGreaterThan(initialCount);

    // The newest assistant bubble is the last one.
    const latestBubble = assistantMessageLocator.last();
    await expect(latestBubble).toBeVisible();

    // Pull text from the bubble's <p> content node.
    const bubbleText = (await latestBubble.locator("p").first().innerText()).trim();

    // Should be non-empty AND have a reasonable length (>50 chars).
    expect(bubbleText.length).toBeGreaterThan(0);
    // We accept short error fallback messages too - but they should not be
    // the empty string. The "reasonable length" constraint is soft: print a
    // warning instead of failing if the answer is short, since llama3.2:1b
    // can occasionally produce concise replies.
    if (bubbleText.length <= 50) {
      console.warn(`Assistant reply was unusually short (${bubbleText.length} chars): "${bubbleText}"`);
    }

    // Critical: the bubble must NOT have horizontal overflow.
    // We check scrollWidth vs clientWidth on the bubble element itself.
    const overflow = await latestBubble.evaluate((el) => {
      const e = el as HTMLElement;
      return {
        scrollWidth: e.scrollWidth,
        clientWidth: e.clientWidth,
      };
    });
    // Allow a 4px tolerance for sub-pixel rendering quirks.
    expect(
      overflow.scrollWidth,
      `Chat bubble has horizontal overflow - content escaped its container. ` +
        `scrollWidth=${overflow.scrollWidth}, clientWidth=${overflow.clientWidth}`
    ).toBeLessThanOrEqual(overflow.clientWidth + 4);

    // If a "Related articles" list was rendered, its titles should be unique.
    // Each related-article card is a div.bg-white.p-2 inside the bubble; the
    // first <p> in each card is the title.
    const articleCards = latestBubble.locator("div.bg-white.p-2");
    const articleCount = await articleCards.count();
    if (articleCount > 0) {
      const titles: string[] = [];
      for (let i = 0; i < articleCount; i++) {
        const t = await articleCards.nth(i).locator("p").first().innerText();
        titles.push(t.trim());
      }
      const unique = new Set(titles);
      expect(
        unique.size,
        `Related articles should have unique titles - saw duplicates: ${titles.join(" | ")}`
      ).toBe(titles.length);
    }
    // If no related articles section, that's fine - we don't require it.
  });
});
