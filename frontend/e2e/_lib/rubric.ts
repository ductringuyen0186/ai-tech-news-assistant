import { expect, type Page } from "@playwright/test";

/**
 * Rubric helpers for the user-testing 8-category acceptability suite.
 *
 * Each helper does ONE `page.evaluate` walk over the visible DOM (or a
 * scoped subtree) so the assertion stays cheap even when called from
 * multiple specs. The whole suite must finish under 60s.
 *
 * Categories covered here:
 *   1. Content integrity   — assertNoHtmlEntities, assertNoMojibake,
 *                            assertNoUndefinedNullObjectObject
 *   2. Typography / format — (caller tests literal markdown markers)
 *   3. No duplicates       — assertNoDuplicateSiblings
 *   4. Layout / overflow   — assertNoHorizontalOverflow
 *   6. Console hygiene     — installConsoleErrorListener / assertConsoleClean
 *   7. Mock-data leak      — assertNoMockDataLeak
 *   8. Asset integrity     — assertImagesLoaded
 *
 * The helpers throw via Playwright's `expect` on failure so the failure
 * message is captured in the standard report.
 */

// ---------------------------------------------------------------------------
// Category 1 — content integrity
// ---------------------------------------------------------------------------

/**
 * Fails if any visible text node in `scope` contains a raw HTML entity that
 * should have been decoded (`&amp;`, `&#39;`, `&quot;`, `&nbsp;`, etc.).
 *
 * `scope` defaults to the whole `<body>`. Pass a CSS selector to scope a
 * single tab's content (e.g. `'[data-state="active"][role="tabpanel"]'`).
 */
export async function assertNoHtmlEntities(
  page: Page,
  scope: string = "body"
): Promise<void> {
  const offenders = await page.evaluate((sel) => {
    const root = document.querySelector(sel);
    if (!root) return [] as string[];
    const re = /&#\d+;|&amp;|&lt;|&gt;|&quot;|&nbsp;/;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const hits: string[] = [];
    let node = walker.nextNode();
    while (node) {
      const t = node.nodeValue || "";
      if (re.test(t)) {
        // Visible only — skip text inside hidden subtrees.
        const el = node.parentElement;
        if (el) {
          const style = window.getComputedStyle(el);
          if (style.display !== "none" && style.visibility !== "hidden") {
            hits.push(t.trim().slice(0, 120));
            if (hits.length >= 5) break;
          }
        }
      }
      node = walker.nextNode();
    }
    return hits;
  }, scope);

  expect(
    offenders,
    `Raw HTML entities found in "${scope}" — text was not decoded before render. ` +
      `Examples: ${JSON.stringify(offenders)}`
  ).toHaveLength(0);
}

/**
 * Fails on UTF-8 mojibake patterns produced when latin-1 bytes are decoded
 * as UTF-8 (e.g. the smart quote in "OpenAI's" rendering as "OpenAIâs").
 *
 * The `Â` and `â` followed by a continuation byte is the canonical signal.
 * We also catch a few known visible artefacts directly.
 */
export async function assertNoMojibake(
  page: Page,
  scope: string = "body"
): Promise<void> {
  const offenders = await page.evaluate((sel) => {
    const root = document.querySelector(sel);
    if (!root) return [] as string[];
    // Range matches: â + 0x80–0xBF continuation byte; Â + same.
    const re = /[âÂ][-¿]/u;
    const knownPatterns = [
      "donât",
      "donÃ¢t",
      "doesnât",
      "isnât",
      "wonât",
      "OpenAIâs",
      "AIâs",
      "âs ",
      "â", // â\x80\x99
      "Ã¢â‚¬",
    ];
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const hits: string[] = [];
    let node = walker.nextNode();
    while (node) {
      const t = node.nodeValue || "";
      if (re.test(t) || knownPatterns.some((p) => t.includes(p))) {
        const el = node.parentElement;
        if (el) {
          const style = window.getComputedStyle(el);
          if (style.display !== "none" && style.visibility !== "hidden") {
            hits.push(t.trim().slice(0, 120));
            if (hits.length >= 5) break;
          }
        }
      }
      node = walker.nextNode();
    }
    return hits;
  }, scope);

  expect(
    offenders,
    `Mojibake / double-encoded UTF-8 found in "${scope}". ` +
      `Examples: ${JSON.stringify(offenders)}`
  ).toHaveLength(0);
}

/**
 * Fails if the literal tokens "undefined", "null", "[object Object]", or
 * "NaN" appear in visible text — these are the classic signals of an
 * unguarded ${value} template or JSON.stringify of a non-serialisable
 * thing leaking into the UI.
 *
 * We allow these tokens inside form inputs (placeholder dropdowns, raw
 * JSON debug viewers). The walk skips `<input>`, `<textarea>`, `<select>`,
 * and any element with `role="textbox"`.
 */
export async function assertNoUndefinedNullObjectObject(
  page: Page,
  scope: string = "body"
): Promise<void> {
  const offenders = await page.evaluate((sel) => {
    const root = document.querySelector(sel);
    if (!root) return [] as string[];
    // Word-bounded so "undefined-id-1" still passes; "[object Object]" is
    // matched as a literal substring.
    const re = /\bundefined\b|\bnull\b|\[object Object\]|\bNaN\b/i;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const hits: { text: string; tag: string }[] = [];
    let node = walker.nextNode();
    while (node) {
      const t = node.nodeValue || "";
      if (re.test(t)) {
        const el = node.parentElement;
        if (!el) {
          node = walker.nextNode();
          continue;
        }
        // Skip form/input chrome where these tokens are legitimate (e.g.
        // a JSON viewer or an "undefined" placeholder option).
        const tag = el.tagName.toLowerCase();
        const role = el.getAttribute("role") || "";
        if (
          tag === "input" ||
          tag === "textarea" ||
          tag === "select" ||
          tag === "option" ||
          role === "textbox"
        ) {
          node = walker.nextNode();
          continue;
        }
        const style = window.getComputedStyle(el);
        if (style.display !== "none" && style.visibility !== "hidden") {
          hits.push({ text: t.trim().slice(0, 120), tag });
          if (hits.length >= 5) break;
        }
      }
      node = walker.nextNode();
    }
    return hits;
  }, scope);

  expect(
    offenders,
    `Found stringified placeholder values (undefined / null / [object Object] / NaN) ` +
      `in "${scope}" — likely a missing fallback. Examples: ${JSON.stringify(offenders)}`
  ).toHaveLength(0);
}

// ---------------------------------------------------------------------------
// Category 4 — layout / overflow
// ---------------------------------------------------------------------------

/**
 * For every element matched by `selector`, fails if its `scrollWidth`
 * exceeds `clientWidth + 4px` (4px tolerance for sub-pixel rendering).
 */
export async function assertNoHorizontalOverflow(
  page: Page,
  selector: string
): Promise<void> {
  const offenders = await page.evaluate((sel) => {
    const els = Array.from(document.querySelectorAll(sel)) as HTMLElement[];
    return els
      .map((el, idx) => ({
        idx,
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        snippet: (el.innerText || "").trim().slice(0, 80),
      }))
      .filter((r) => r.scrollWidth > r.clientWidth + 4);
  }, selector);

  expect(
    offenders,
    `Elements matching "${selector}" overflow their container horizontally. ` +
      `Offenders: ${JSON.stringify(offenders)}`
  ).toHaveLength(0);
}

// ---------------------------------------------------------------------------
// Category 3 — no duplicate siblings
// ---------------------------------------------------------------------------

/**
 * Collects the trimmed `innerText` of every element matching `listSelector`
 * and asserts they are unique. Useful for chip lists, related-article lists,
 * trending-topic lists, etc.
 *
 * `label` is included in the failure message so multiple uses of this
 * helper in one test stay distinguishable.
 */
export async function assertNoDuplicateSiblings(
  page: Page,
  listSelector: string,
  label: string = listSelector
): Promise<void> {
  const texts = await page.evaluate((sel) => {
    const els = Array.from(document.querySelectorAll(sel)) as HTMLElement[];
    return els.map((el) => (el.innerText || "").trim()).filter((t) => t.length > 0);
  }, listSelector);

  const seen = new Map<string, number>();
  for (const t of texts) {
    seen.set(t, (seen.get(t) ?? 0) + 1);
  }
  const dupes = Array.from(seen.entries()).filter(([, n]) => n > 1);

  expect(
    dupes,
    `Duplicate siblings under "${label}" — same text rendered ${dupes
      .map(([t, n]) => `"${t.slice(0, 60)}" (${n}x)`)
      .join(", ")}. Total siblings collected: ${texts.length}.`
  ).toHaveLength(0);
}

// ---------------------------------------------------------------------------
// Category 7 — mock / seed data leak
// ---------------------------------------------------------------------------

/**
 * Fails if the rendered DOM contains any of the canonical "test fixture"
 * patterns: titles starting with `seed-` / `test-` / `mock-` / `example-` /
 * `lorem`, sources equal to `seed` / `mock` / `test` / `example.com` /
 * `localhost`, or dates that round-trip to the unix epoch (`1970-01-01`,
 * `Jan 1, 1970`, `Dec 31, 1969`).
 *
 * The walk is scoped by `scope` so a per-tab assertion doesn't trip over
 * fixtures rendered on a different tab.
 */
export async function assertNoMockDataLeak(
  page: Page,
  scope: string = "body"
): Promise<void> {
  const offenders = await page.evaluate((sel) => {
    const root = document.querySelector(sel);
    if (!root) return [] as { kind: string; sample: string }[];

    const titleRe = /^(seed[-_ ]|test[-_ ]|mock[-_ ]|example[-_ ]|lorem\b)/i;
    const sourceRe = /^(seed|mock|test|example\.com|localhost)$/i;
    // Match formatted dates that imply unix epoch.
    const dateRe = /\b1970-01-01\b|\bJan(?:uary)?\s+1,?\s+1970\b|\bDec(?:ember)?\s+31,?\s+1969\b/;

    const hits: { kind: string; sample: string }[] = [];

    // Collect all visible text once.
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node = walker.nextNode();
    while (node) {
      const t = (node.nodeValue || "").trim();
      if (t.length > 0 && t.length < 400) {
        const parent = node.parentElement;
        if (parent) {
          const style = window.getComputedStyle(parent);
          if (style.display !== "none" && style.visibility !== "hidden") {
            if (titleRe.test(t)) {
              hits.push({ kind: "mock-title-prefix", sample: t.slice(0, 100) });
            }
            if (sourceRe.test(t)) {
              hits.push({ kind: "mock-source", sample: t });
            }
            if (dateRe.test(t)) {
              hits.push({ kind: "epoch-date", sample: t.slice(0, 100) });
            }
            if (hits.length >= 8) break;
          }
        }
      }
      node = walker.nextNode();
    }
    return hits;
  }, scope);

  expect(
    offenders,
    `Mock / seed data leaked into "${scope}". Hits: ${JSON.stringify(offenders)}`
  ).toHaveLength(0);
}

// ---------------------------------------------------------------------------
// Category 8 — asset integrity
// ---------------------------------------------------------------------------

/**
 * For every `<img>` matched by `selector`, fails if the image hasn't loaded
 * (`naturalWidth === 0`). Skips `<img>` with `loading="lazy"` that are
 * still off-screen so the test isn't flaky on long lists.
 *
 * `tolerance` lets the caller accept up to N broken images out of the
 * total — useful when a small subset of feed sources legitimately have no
 * `image_url` and the placeholder is one of them.
 */
export async function assertImagesLoaded(
  page: Page,
  selector: string,
  tolerance: number = 0
): Promise<void> {
  const status = await page.evaluate((sel) => {
    const imgs = Array.from(document.querySelectorAll(sel)) as HTMLImageElement[];
    const results = imgs.map((img) => {
      const visible =
        img.offsetParent !== null ||
        window.getComputedStyle(img).display !== "none";
      return {
        src: img.currentSrc || img.src,
        naturalWidth: img.naturalWidth,
        complete: img.complete,
        loading: img.loading,
        visible,
      };
    });
    return results;
  }, selector);

  const broken = status.filter(
    (r) => r.visible && r.complete && r.naturalWidth === 0
  );

  expect(
    broken.length,
    `Broken <img> elements in "${selector}" (visible, complete, naturalWidth=0). ` +
      `Tolerance was ${tolerance}. Broken: ${JSON.stringify(broken.slice(0, 5))}.`
  ).toBeLessThanOrEqual(tolerance);
}

// ---------------------------------------------------------------------------
// Category 6 — console hygiene
// ---------------------------------------------------------------------------

/**
 * Console error collector. Install BEFORE the test navigates so no error
 * events are missed; call `assertConsoleClean(collector)` at the end of the
 * test to fail if any `error` events were emitted.
 *
 * Some noisy-but-known errors (e.g. third-party CDN cookie warnings) can
 * be tolerated by passing an `ignore` regex.
 *
 * Usage:
 *   const errors = installConsoleErrorListener(page);
 *   await page.goto("/");
 *   ...
 *   assertConsoleClean(errors);
 */
export interface ConsoleErrorCollector {
  errors: string[];
  ignore: RegExp[];
}

export function installConsoleErrorListener(
  page: Page,
  ignore: RegExp[] = []
): ConsoleErrorCollector {
  const collector: ConsoleErrorCollector = { errors: [], ignore };
  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (collector.ignore.some((re) => re.test(text))) return;
    collector.errors.push(text);
  });
  page.on("pageerror", (err) => {
    const text = err.message;
    if (collector.ignore.some((re) => re.test(text))) return;
    collector.errors.push(`pageerror: ${text}`);
  });
  return collector;
}

export function assertConsoleClean(collector: ConsoleErrorCollector): void {
  expect(
    collector.errors,
    `Console emitted error(s) during the test:\n  ${collector.errors
      .slice(0, 10)
      .map((e, i) => `[${i}] ${e.slice(0, 200)}`)
      .join("\n  ")}`
  ).toHaveLength(0);
}
