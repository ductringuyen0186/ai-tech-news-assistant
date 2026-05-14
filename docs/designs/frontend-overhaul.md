# TechPulse AI — Frontend Overhaul Design Doc

> **Executive summary.** TechPulse AI currently reads as a generic shadcn/Radix application: Inter + Space Grotesk over a beige-taupe palette adapted from claude.ai, with rounded cards, soft borders, and almost no motion budget spent on what is actually distinctive about the product — the streaming research agent. This document proposes an **editorial broadsheet meets terminal-cockpit** aesthetic: a serif display face (Fraunces) paired with a precision grotesk (IBM Plex Sans) and a true monospace (JetBrains Mono) for live agent telemetry; a near-monochrome ink-on-paper palette (warm off-white in light, cold off-black in dark) with **one** electric accent (signal cyan in dark / oxblood ink in light); generous editorial gutters in static surfaces and grid-locked terminal density in the live research panel. Six phased milestones land the redesign without breaking any of the 53 Playwright contracts. The riskiest tradeoff is that the visual-baseline screenshots (`m3-visual-baselines.spec.ts`) will require a one-time `--update-snapshots` regeneration; the `data-testid` and `role` graph is preserved.

---

## 0. How to read this doc

1. Section 1 inventories the current aesthetic. Section 2 diagnoses 9 specific failure modes with file:line citations.
2. Section 3 commits to **The Broadsheet Terminal** as the bold direction, and lists two alternates in case you push back.
3. Sections 4–9 are the phased plan (M0–M5), each with goal, files touched, concrete changes, and test-contract risk.
4. Section 10 lists fonts and any other downloadable assets.
5. Section 11 enumerates open questions for you to answer before workers start.

---

## 1. Inventory — what the current app projects today

| Surface | What it currently is |
| --- | --- |
| `App.tsx` shell | A flex row: 288px (`w-72`) sidebar on the left, a sticky top bar with `border-b border-border` and `bg-background/80 backdrop-blur-sm`, content gutter of `px-6 py-6`, footer `border-t`. Generic SaaS dashboard frame. |
| Top bar | `<h1 className="text-xl font-semibold tracking-tight">TechPulse AI</h1>` + 12px muted tagline + two `Badge` chips (🔥 trending count, articles today). Reads like a stock Linear/Notion clone. |
| Sidebar | Logo button → search-CTA-as-button → vertical `TabsList` with 6 entries → theme toggle pinned to bottom. All items get the same rounded-md treatment with a `border-l-2 border-l-primary` strip when active. Identical to every shadcn template on GitHub. |
| `WelcomeScreen` | Centered hero with a `rounded-2xl` icon block, `text-3xl font-semibold` title, paragraph tagline, two CTA buttons, a ⌘K keyboard hint, then a 2×2 feature grid of bordered cards. The literal shadcn "starter" landing. |
| `NewsCard` | A `Card` with `p-3 gap-3`, a 64×64 image thumbnail, title in `text-[15px] leading-snug font-semibold line-clamp-2`, a clamped 3-line summary, a bookmark button in the top-right corner, category badges + a "Read article" link at the bottom. The vibe is "Hacker News meets Notion" but without the personality of either. |
| `ResearchMode` | The killer feature, currently rendered as a Claude.ai chat clone: user-message bubble in `bg-secondary` rounded-2xl, agent card with collapsible "tool use" blocks, monochrome chevrons, generic "Researching..." spinner. Nothing about the streaming agent feels alive on screen. |
| `KnowledgeGraph` | A `<canvas>` rendering with primary/border/muted CSS-variable colors plus four hardcoded entity-type colors (`#3b82f6` blue, `#10b981` green, `#f59e0b` amber, `#a855f7` purple) — the universal D3 starter palette. |
| `DigestView` | Card-stack of titled sections: hero summary, curated headlines grid, trending now chip row, top stories list with `border-l-4` accents (test-pinned), category bar chart. Reads like an email newsletter, but not a *designed* one. |
| `index.css` / `globals.css` | Imports **Inter** + **Space Grotesk** at the top of both files — the exact two fonts SKILL.md flags as never-use. Background `hsl(40 24% 95%)` cream, primary `hsl(35 14% 47%)` taupe. Dark mode flips to `hsl(35 12% 18%)` warm dark gray with a `hsl(35 24% 70%)` desert sand accent. |

**Net impression:** the app dresses itself as "warm beige Linear with a Claude haircut." It is competent and uncontroversial, and that is exactly the problem.

---

## 2. Diagnosis — nine specific things that read as generic AI

1. **Font choice violates the design philosophy outright.** `frontend/src/index.css:1` and `frontend/src/styles/globals.css:1` both `@import` **Inter** and **Space Grotesk** — the two faces SKILL.md explicitly singles out. The `body` rule at `globals.css:412` then sets `font-family: Inter, …`. There is no display face with a point of view anywhere in the system.
2. **Monochrome warm-grey palette with no signal color.** `globals.css:18` sets `--primary: hsl(35 14% 47%)` — that's a 47%-lightness taupe. There is no chromatic anchor; every active element is the same color as the room it sits in. The eye has nowhere to land.
3. **Rounded-2xl on everything.** Welcome hero icon (`WelcomeScreen.tsx:106`), agent message bubble (`ResearchMode.tsx:923`), every Card and Badge. Rounding this aggressive is the literal house style of every shadcn-based product launched in the last 18 months.
4. **The Research mode is dressed as a chat app, not a research instrument.** `ResearchMode.tsx:923` renders the user's question as a `max-w-2xl bg-secondary rounded-2xl px-4 py-3` bubble — a direct visual quote of claude.ai. The streaming agent — the actual *killer feature* — has no surface that signals "machinery at work." `ResearchMode.tsx:1289` falls back to a single `<Loader2 className="w-4 h-4 animate-spin" /> Thinking...` row.
5. **No motion budget on what matters.** Tab cross-fades are 200ms opacity-only (`App.tsx:169-171`), sub-question rows have a 50ms stagger capped at 250ms (`ResearchMode.tsx:1157-1162`), and that is the entire animation language. There is no token-stream typewriter effect, no agent-phase choreography, no scroll-anchored sequence on the welcome page.
6. **Knowledge graph palette is the D3 starter kit.** `KnowledgeGraph.tsx:184-187` and again `:683-686` and again `:704/720/736/752/854-866` — five copies of the same four hex codes (`#3b82f6`, `#10b981`, `#f59e0b`, `#a855f7`). These are the Tailwind defaults; the user has seen them in 200 other apps this year.
7. **The top bar carries no editorial identity.** `App.tsx:484-510` is a `border-b backdrop-blur-sm` row with a `text-xl font-semibold` title and a 12px subtitle. It could be any analytics dashboard, news reader, or LLM playground. There is no date line, no issue number, no masthead, nothing that says "this is a publication."
8. **The welcome page is a shadcn template.** `WelcomeScreen.tsx:106-198` — circle icon, big heading, tagline, two CTA buttons, four feature cards. Identical to maybe a hundred Vercel templates. There is no narrative scroll, no signature device, no piece of visual writing the user remembers afterward.
9. **Decorative density is zero.** `index.css` contains four leftover utility classes for `glass-card`, `elevation-md`, `subtle-pattern`, `text-gradient` (`globals.css:227-277`). None of them are used in the app. No grain, no noise, no rules, no tickers, no rotating callout — every surface is a flat color with rounded borders. The eye has no texture to grip.

A reader's one-sentence impression after 5 seconds: *"another AI product, looks fine, can't remember the name."*

---

## 3. Aesthetic direction — **The Broadsheet Terminal**

**Commit:** TechPulse becomes the digital love-child of a Sunday broadsheet front page (FT, NYT Magazine, Le Monde) and a Bloomberg terminal. Editorial typography and ink-on-paper restraint in the static surfaces — News Feed, Digest, Welcome — and grid-locked monospaced telemetry in the live surfaces — Research agent, Knowledge Graph, command palette.

**The signature device:** a horizontal "issue dateline" rule across the top of every page that reads like a real newspaper masthead — `TECHPULSE — VOL III · NO. 137 · TUE 12 MAY 2026 · LIVE` — with a blinking signal-color cursor for the `LIVE` token whenever the agent is streaming. This rule is the recurring artifact that brands every screenshot.

**Why this fits a tech-news / agentic-research tool, in one paragraph.** TechPulse has two atomic verbs: *read* and *investigate*. Editorial typography has been the high-trust visual code for "read this carefully" for two centuries; monospaced telemetry is the high-trust visual code for "a machine is doing real work on your behalf" for sixty years. Fusing them tells the user, at a glance, exactly what the product does — without resorting to the third-rate purple-gradient sci-fi that every AI startup uses to fake the same idea. The serif weights into authority for the news; the mono leans into transparency for the agent (every sub-question, every subagent, every token is something the user can see). The single chromatic accent — a signal cyan (`#22d3ee`-adjacent) in dark mode, an oxblood ink (`#8a1538`-adjacent) in light mode — is reserved exclusively for *live agent state* and *citation links*. Everything else is ink on paper. The accent becomes the user's eye-leash to where the intelligence is firing.

### Alternates (one sentence each so you can push back)

- **B. Risograph almanac.** Hand-printed two-color zine: cream paper background, halftone grain texture, a duotone of warm red + dark teal, hand-drawn rules and chunky Söhne-like sans for body. Warmer, more indie, but harder to pull off on a desktop tool and the grain texture risks fighting the canvas-based Knowledge Graph.
- **C. Brutalist data-bunker.** Pure black + electric green CRT, IBM Plex Mono everywhere including body copy, hard 90-degree corners, hairline rules, ASCII section headers. More distinctive, but pushes the news-reading surface into "hostile to ten-minute reading," which is the wrong place for the marquee Digest tab.

If you have a third taste — say, *late-90s magazine art direction (Wired/Ray Gun)*, or *Swiss Bauhaus rationalist*, or *retro-futurist Apollo console* — say which way and I'll re-pitch.

---

## 4. Milestone M0 — Foundations (palette, typography, asset preload)

**Goal.** Replace the font stack and color tokens at the root before touching any component.

**Files touched.**
- `frontend/index.html` (preconnect + font preload `<link>` tags)
- `frontend/src/styles/globals.css` (theme tokens, font face declarations, body font-family)
- `frontend/src/index.css` (the prebuilt Tailwind bundle — manually add the new utility classes the redesign needs; remove the unused `glass-card` / `subtle-pattern` / `gradient-primary` block at the tail of the file)

**Concrete changes.**

1. Delete the `@import url("https://fonts.googleapis.com/css2?family=Inter…&family=Space+Grotesk…")` line at the top of both `index.css` and `globals.css`.
2. Add a `<link rel="preconnect">` for `fonts.googleapis.com` and `fonts.gstatic.com` in `index.html`, then `@import` the new stack in `globals.css`:

   ```css
   @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,600;9..144,700;9..144,900&family=IBM+Plex+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
   ```

   Fraunces is a variable opsz serif with real personality — high optical-size headlines look like 19th-century broadsheet display, low optical-size body looks editorial. IBM Plex Sans (open-source, mature, distinctly Bloomberg-adjacent) is the precision grotesk. JetBrains Mono is the terminal face.
3. Replace the theme tokens. Both light and dark should be near-monochrome, with one signal accent.

   ```css
   :root {
     /* Light = newsprint */
     --background: oklch(0.985 0.005 80);      /* cream-paper #f7f4ec-adjacent */
     --background-tint: oklch(0.965 0.008 75); /* tinted card surface */
     --foreground: oklch(0.18 0.01 50);        /* deep ink #1c1a16 */
     --foreground-soft: oklch(0.36 0.01 50);   /* secondary ink */
     --rule: oklch(0.78 0.005 70);             /* hairline rule */
     --accent-signal: oklch(0.45 0.18 12);     /* oxblood ink #8a1f2a-ish */
     --accent-signal-bg: oklch(0.94 0.04 12);  /* wash for chips */
     --grain-opacity: 0.035;
   }
   .dark {
     /* Dark = terminal */
     --background: oklch(0.16 0.01 240);       /* cold off-black */
     --background-tint: oklch(0.21 0.012 235); /* card surface */
     --foreground: oklch(0.94 0.008 80);       /* warm paper text */
     --foreground-soft: oklch(0.68 0.01 80);
     --rule: oklch(0.32 0.012 235);
     --accent-signal: oklch(0.82 0.18 200);    /* signal cyan #22d3ee-ish */
     --accent-signal-bg: oklch(0.32 0.08 220);
     --grain-opacity: 0.06;
   }
   ```

   We keep `--primary`, `--card`, `--border`, `--muted`, `--accent`, `--sidebar-*` as aliases pointing to the new tokens so existing class consumers don't have to be rewritten in M0.

4. Body sets `font-family: 'IBM Plex Sans', ...` with `font-feature-settings: 'ss01', 'cv11'` to switch on the alt single-story 'a'. Headlines use Fraunces:

   ```css
   body { font-family: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
          font-feature-settings: "ss01", "cv11"; }
   .display, h1.masthead { font-family: 'Fraunces', 'Times New Roman', serif;
                            font-optical-sizing: auto;
                            font-variation-settings: "opsz" 96, "SOFT" 50;
                            letter-spacing: -0.025em; }
   .mono, code, kbd, [data-mono] { font-family: 'JetBrains Mono', ui-monospace, monospace;
                                    font-feature-settings: "calt", "ss02"; }
   ```

5. Add to `index.css` (prebuilt Tailwind bundle) a new `@layer utilities` block with the redesign's bespoke classes. Tailwind v4 prebuilt does not regenerate on the fly — every new utility MUST be hand-written:

   ```css
   @layer utilities {
     .font-display { font-family: 'Fraunces', 'Times New Roman', serif; font-optical-sizing: auto; }
     .font-mono-tx { font-family: 'JetBrains Mono', ui-monospace, monospace; }
     .text-signal { color: var(--accent-signal); }
     .bg-signal-wash { background: var(--accent-signal-bg); }
     .rule-h { border-top: 1px solid var(--rule); }
     .rule-h-thick { border-top: 2px solid var(--foreground); }
     .grain { position: relative; }
     .grain::after {
       content: ""; position: absolute; inset: 0; pointer-events: none;
       background-image: url("/textures/grain.png"); background-size: 240px 240px;
       opacity: var(--grain-opacity); mix-blend-mode: multiply;
     }
     .dark .grain::after { mix-blend-mode: screen; }
     .live-cursor::after {
       content: "▌"; margin-left: 0.15em; color: var(--accent-signal);
       animation: blink 1s steps(2, start) infinite;
     }
     @keyframes blink { 50% { opacity: 0; } }
     .tick-rule {
       background-image: repeating-linear-gradient(
         to right, var(--rule) 0 1px, transparent 1px 8px);
       height: 8px;
     }
     .stream-caret { display: inline-block; width: 2px; height: 1em;
                     background: var(--accent-signal); vertical-align: -2px;
                     animation: blink 0.9s steps(2, start) infinite; }
     .uppercase-eyebrow { font-family: 'JetBrains Mono', ui-monospace, monospace;
                          letter-spacing: 0.14em; text-transform: uppercase;
                          font-size: 11px; font-weight: 500; color: var(--foreground-soft); }
     .editorial-drop::first-letter {
       font-family: 'Fraunces', serif; font-weight: 700;
       float: left; font-size: 4.6em; line-height: 0.82;
       padding: 0.08em 0.12em 0 0; color: var(--accent-signal); }
   }
   ```

**Test risk.** M0 is invisible to the testid graph. The visual-baseline screenshots (`e2e/m3-visual-baselines.spec.ts:127–195`) WILL diff. We mitigate by running `--update-snapshots` once at M0 end. The Linear-density assertion in `news-feed.spec.ts:166` checks card padding `≤ 14px` and computed font-size on the title — keep `NewsCard`'s outer `Card` at `p-3` (12px) and don't bump body to >14px until M2 (and even then, only the new editorial article-detail surface, not the feed-card itself).

---

## 5. Milestone M1 — Sidebar + Top bar masthead

**Goal.** Replace the dashboard chrome with an editorial masthead and a typographic sidebar.

**Files touched.**
- `frontend/src/App.tsx` (top-bar `<header>` block, lines 484–510)
- `frontend/src/components/Sidebar.tsx` (entire component)

**Concrete changes.**

1. **Masthead.** Replace the `<header>` in `App.tsx` with a two-row composition:

   ```
   ┌─ TECHPULSE ──────── VOL III · NO. 137 · TUE 12 MAY 2026 ─── ◉ LIVE ──┐
   │ Tech intelligence,                                 [🔥 12 trending]  │
   │ from the agentic desk.                             [128 today]       │
   └────────────────────────────────────────────────────────────────────┘
   ```

   - Row 1 = a single hairline-bordered band with `font-mono-tx text-[11px] uppercase-eyebrow tracking-wide`. The `LIVE` token has the `live-cursor` class and only shows the signal accent when `isResearching` is true (lift the boolean out of `ResearchMode` into a tiny `ResearchContext` exported via `CommandPaletteProvider`'s sibling, OR put it on `window` as a lightweight pub-sub).
   - Row 2 = an `h1.font-display text-[32px] font-medium tracking-tight` reading `Tech intelligence,` on line 1, `from the agentic desk.` on line 2, italic. Right side: the existing two `Badge` chips, restyled as terminal pills (`font-mono-tx px-2 py-0.5 rule-h text-[11px]` with no rounded corners, hard 1px border).
   - **Keep** the `<h1>` with accessible name `/TechPulse AI/i` — `sidebar.spec.ts:38` and `news-feed.spec.ts:49` assert this heading exists. Solution: render the masthead `<h1>` with an `aria-label="TechPulse AI"` and a visually-hidden span:

     ```tsx
     <h1 className="font-display text-[32px] tracking-tight"
         aria-label="TechPulse AI">
       <span className="sr-only">TechPulse AI</span>
       <span aria-hidden>Tech intelligence,</span><br/>
       <em aria-hidden>from the agentic desk.</em>
     </h1>
     ```

     This preserves `getByRole("heading", { name: /TechPulse AI/i })` while the visible name carries the editorial voice.

2. **Sidebar.** Rebuild as a typographic stack with no rounded card slabs:

   - Width stays `w-72` (fixed; you ruled out responsive). Background switches to `--background` (no separate `--sidebar`), separated from main by a single `border-r border-[var(--rule)]`.
   - Top: hairline `rule-h-thick`; below it, the wordmark in `font-display italic font-medium text-2xl` reading `TechPulse` with a small `vol. iii` superscript in mono. Click goes home.
   - "Search…" CTA becomes a one-line input-shaped affordance with no rounded corners: `border-b border-[var(--rule)] py-2`, mono placeholder `> jump anywhere   ⌘K`. Click opens cmdk.
   - Nav items become an unstyled `<ul>`. Each item: a `uppercase-eyebrow` numeric prefix (`01.`, `02.`, …) on the left, the label in `IBM Plex Sans 14px medium` in the middle, an icon in 14px on the right. Active row gets a left-side block character `▌` in `--accent-signal` (NOT a left border — the block character reads more "terminal cursor" than "shadcn sidebar"). Hover: a subtle `background: var(--background-tint)` slab the full row.
   - **Test-pinning:** `TabsList` and `TabsTrigger` continue to be the rendering primitives — Radix still emits `role="tablist"` / `role="tab"` / accessible name = visible text — `sidebar.spec.ts:43-57` keeps passing. The accessible name MUST remain the unprefixed label ("News Feed", "Research", …); the `01.` prefix can either be added via an `aria-hidden` span OR we set `aria-label="News Feed"` on the TabsTrigger and let the visible text be `01. News Feed`. Recommend the first: cleaner DOM, no risk of label drift.
   - Bottom: theme toggle becomes a single-line tickered row — `[ light ] · ⬤ dark` with the active option in `--accent-signal`. Preserves `data-testid="theme-toggle"`.

3. **Footer** (`App.tsx:765-775`). Replace with a single hairline + a single mono line: `— end of issue — set in Fraunces & IBM Plex · ⓒ techpulse 2026 · agentic desk`. Removes the dashboard feel.

**Test risk.** Highest concentration of test-name assertions in the app. Inventory of contracts that must survive:

- `getByRole("heading", { name: /TechPulse AI/i })` — preserved via `aria-label` trick above.
- `getByRole("tablist")` — Radix `TabsList` still renders this.
- `getByRole("tab", { name: <Label> })` for each of `News Feed`, `Research`, `Knowledge`, `Digest`, `Saved`, `Settings` — preserved by keeping `TabsTrigger` and the visible label string as accessible name.
- `data-testid="theme-toggle"` — preserved.
- `data-slot="sidebar"` on the `<aside>` — `sidebar.spec.ts` uses it (line 78 reference) — preserved.

Visual baselines: all six will diff; regenerate at M1 end.

---

## 6. Milestone M2 — News Feed redesign as front-page broadsheet

**Goal.** Replace the uniform 2-column NewsCard grid with a real front-page composition: one large lead article, a column of secondaries, a digest band.

**Files touched.**
- `frontend/src/App.tsx` (the `<TabsContent value="feed">` block, lines 541–680)
- `frontend/src/components/NewsCard.tsx` (rewrite)
- `frontend/src/components/TrendingRail.tsx` (light skin only)

**Concrete changes.**

1. **Asymmetric grid.** The feed becomes a 12-column grid:

   ```
   ┌────────────── 12 cols ─────────────────────────────────┐
   │ LEAD STORY (cols 1-8, 2 rows tall)    │ DECK (9-12)    │
   │ ── massive Fraunces headline          │ smaller items  │
   │ ── pull-quote with editorial-drop     │ stacked, mono  │
   │ ── meta line (source · time · cred)   │ time stamps    │
   ├──────────────────────────────────────────────────────  │
   │ tick-rule with category label                          │
   ├────────────── rest of feed in 3 cols ───────────────── │
   │ NewsCard │ NewsCard │ NewsCard                         │
   │ NewsCard │ NewsCard │ NewsCard                         │
   └────────────────────────────────────────────────────────┘
   ```

   First article in `filteredArticles` is rendered as `LeadStoryCard`; next 3 in the deck; remaining in the 3-col grid. Compact view collapses to a list of single-row entries (Fraunces 18px title, mono 11px meta line).

2. **`NewsCard` rewrite** — strip everything rounded:

   - No `Card` wrapper. Render as a `<article>` with `border-top: 1px solid var(--rule)` and no bottom border (the next sibling's top border continues the rule).
   - Title in `font-display font-medium text-[22px] leading-[1.15] tracking-tight`. Hover: title gets `text-signal` and an underline appears.
   - Source row replaces the badge chips: `<span className="uppercase-eyebrow">TechCrunch · 4h ago · v85</span>` — `v85` is the credibility score in mono. The existing `.text-gray-500` class on the source span (preserved for `news-feed.spec.ts` source assertions) becomes a span class — keep both: `<span className="text-gray-500 uppercase-eyebrow">TechCrunch</span>`. `text-gray-500` exists in `index.css`; no change needed.
   - Summary in Fraunces 9pt-opsz at 15px, `leading-[1.55]`. `data-testid="news-card-summary"` preserved.
   - The image becomes a 16:10 letterbox at the top of the article block, NOT a 64×64 thumbnail. Background black behind it. Lead story gets a 16:9 large image; secondary cards get 16:10; compact list rows get no image (mono-only).
   - Bookmark in the top-right corner becomes a tiny mono toggle: `[ saved ]` vs `[+ save ]`. `data-testid="news-card-save-btn"` preserved.
   - "Read article" CTA becomes a mono link row at the foot: `read at techcrunch.com →` in `--accent-signal`. `data-testid="news-card-read-more"` preserved.
   - **Padding.** Card outer padding stays at 12px to keep `news-feed.spec.ts:166` ("padding ≤ 14px") green. Border + typographic generosity carries the editorial weight — no need for fluffy padding.

3. **Trending rail** becomes a horizontally-scrolling ticker tape:

   ```
   ► ANTHROPIC ▌4.2k ─ OPENAI ▌3.9k ─ NVIDIA ▌3.1k ─ APPLE INTELLIGENCE ▌2.4k ─ …
   ```

   Mono, `--accent-signal` on the count number, dot leaders between entries, slow CSS-only scroll on mount that pauses on hover.

4. **Active filters strip.** `data-testid="news-feed-active-filters"` preserved. Restyle as a hairline-ruled band with mono `filtered ▸` prefix and chips rendered as outline `[ AI ]`-style pills.

**Test risk.**

- `news-feed.spec.ts:166` — card font-size ≤ 14px, padding ≤ 14px. Card body padding stays `p-3`. The title is bigger but only at the lead-story scale; verify the spec's selector targets a `Card` not the new `<article>` (the spec searches by `data-slot="card"` per `NewsCard.tsx:163`). Keep `data-slot="card"` on the new `<article>` so the assertion still binds, and ensure title's computed font-size on a SECONDARY card stays at the asserted threshold. Lead story gets a distinct testid `news-card-lead` that the test ignores.
- `data-testid="news-feed-list"` — preserved as the wrapper around the post-lead grid (or wrap the whole composition).
- `news-feed.spec.ts:286` — `assertNoMockDataLeak(page, '[data-state="active"][role="tabpanel"]')` — Radix tabpanel attributes preserved automatically.
- All `Read More` button text — preserved; only the typographic skin changes.

Visual baselines: `news-feed-final.png` will diff. Regenerate.

---

## 7. Milestone M3 — Research mode as live newsroom telex

**Goal.** Make the marquee feature unmistakably the marquee feature. Strip the Claude-chat skin and replace it with a wire-service teleprinter aesthetic.

**Files touched.**
- `frontend/src/components/ResearchMode.tsx` (heavy rewrite of the render block, lines 842–end)
- `frontend/src/components/SubQuestionsPanel.tsx` (light restyle)
- `frontend/src/components/MarkdownReport.tsx` (typography only)

**Concrete changes.**

1. **Header.** Replace the polite card-with-icon header with a teleprinter masthead:

   ```
   ━━━ AGENTIC DESK ━━━ DISPATCH #00237 ━━━ FILED 14:08:11 UTC ━━━ ◉ STREAMING
   ```

   in `JetBrains Mono 12px uppercase`. The "STREAMING" / "FILED" / "ERROR" token at the end uses `--accent-signal` and the `live-cursor` class while running. The dispatch number is `Date.now()` short-hash. This replaces the `Lightbulb + "Research"` title (lines 851-859).

2. **Query bar.** Becomes the bottom of the screen, sticky, full-width inside the content gutter. Above it, a hairline `rule-h-thick`. The input has no rounded corners, no `Input` shadcn skin — render as a `<textarea>` that grows to 4 lines max, with a mono caret prompt `>` to the left and a `[ submit ⏎ ]` mono button to the right. While `isResearching`, the prompt becomes `▌` blinking. Suggested-queries strip moves above the input.

3. **User question** (`ResearchMode.tsx:906-932`). Drop the right-aligned `bg-secondary rounded-2xl` bubble entirely. Replace with a quoted editorial block:

   ```
   THE QUESTION
   ────────────────────────────────────────────
   How is Anthropic positioned vs OpenAI in the
   last 30 days?
                                — you, just now
   ```

   `font-display italic` for the question, mono eyebrow above. Keep `data-testid="research-user-message"`.

4. **The agent's work-in-progress** is the centerpiece. Replace the two collapsible `ToolUseBlock` widgets with a single live transcript pane styled as a teleprinter scroll:

   ```
   ━ DECOMPOSITION ━━━━━━━━━━━━━━━━━━━━━━ 0.42s ━
   01 ▸ how has anthropic's revenue evolved
   02 ▸ which enterprise customers have they won
   03 ▸ what models have shipped in the last 30d
   04 ▸ how does pricing compare to gpt-4 family

   ━ DISPATCHING SUBAGENTS ━━━━━━━━━━━━━━ 9 reading ━
   ▸ summarize_article #1142 ◉ running   ──   ───
   ▸ summarize_article #1138 ✓ done      0.9s
   ▸ summarize_article #1141 ✗ error     rate limit
   ▸ summarize_article #1140 ◉ running   ──   ───

   ━ SYNTHESIZING REPORT ━━━━━━━━━━━━━━ 4.1s elapsed ━
   ```

   Each step is its own block separated by horizontal rules made of `─` characters in mono. Status dots are unicode (◉, ✓, ✗). The `data-testid` graph stays identical: every existing `research-sub-questions-block`, `research-subagents-block`, `research-subagent-row`, `research-subagent-row-toggle`, `research-subagent-summary` survives, just rerendered with the teleprinter skin.

   Critical regex preserved: the header line `Subagents (X running, Y done, Z errored)` regex (`ResearchMode.tsx:762`) must continue to match — keep this exact string somewhere in the DOM under `data-testid="research-subagents-header"`. Recommend a `sr-only` span carrying it, with the visible mono line `▸ 9 reading · 3 done · 1 error` shown above.

5. **Token streaming.** Currently the report just appears as `<MarkdownReport>` text growing in place. Upgrade:
   - Each new token shown gets a brief opacity-0 → opacity-1 fade-in via a `<span className="tok">` wrapper added by a small `useTokenStream` hook that splits the streamed text on word boundaries.
   - A blinking `stream-caret` follows the last character while `phase === "Synthesizing"`.
   - `data-testid="research-report-body"` stays on the wrapper.

6. **Citation bar.** Currently mono outline pills `[1] [2] [3]` (`ResearchMode.tsx:1310-1326`). Keep the structure, restyle as ticker entries in mono with the signal accent on the bracketed number and a 9pt source-name preview after each:

   ```
   sources ▸ [1] techcrunch  [2] ars technica  [3] wired  [4] verge
   ```

7. **Done state.** When `phase === "done"`, replace the `Save / Copy / Download` action row's outlined buttons with a single mono action strip pinned to the right of the masthead: `[ ⌃S save ] [ ⌃C copy ] [ ⌃D .md ]`. The icon-only `Button`s currently rendered (`ResearchMode.tsx:986-1064`) still exist but get the new mono skin via a wrapper className — testids `research-save-btn`, `research-copy-btn`, `research-download-btn` preserved.

8. **Markdown report typography.** Headers in `font-display`, body in IBM Plex Sans 15px / 1.65 line-height, blockquotes in Fraunces italic. First paragraph of the executive summary gets `.editorial-drop` for the drop cap — the only place in the app where this lives, so it remains a one-off visual signature.

**Test risk.** This is where the surface changes most, but the testid graph is identical. Inventory:

- `research-phase-chip` — keep this `<span>` exactly, just with the mono masthead skin. The text must still be `Decomposing` / `Searching (i/N)` / `Synthesizing` / `Done` / `Error` — the chip is asserted against these strings via `getByText` in some tests.
- `research-report-card` — keep on the outer wrapper around the agent transcript.
- `research-subagents-panel` — keep on the subagent list.
- `research-subagents-header` regex `/Subagents \(\d+ running, \d+ done, \d+ errored\)/i` — preserved via `sr-only` span.
- `research-subagent-row` / `research-subagent-row-toggle` / `research-subagent-summary` — preserved on each row.
- `research-sub-questions-panel` / `research-sub-question-row` / `research-sub-question-article` / `research-sub-questions-skeleton` — preserved inside `SubQuestionsPanel`.
- `research-report-body` / `research-error-panel` / `research-retry-btn` / `research-save-btn` / `research-copy-btn` / `research-download-btn` / `research-cancel-btn` — preserved.
- `research-follow-ups` / `research-follow-up-chip` / `research-empty-suggestions` — preserved; follow-ups bar becomes a ticker-style row of `[ continue: <q> ]` mono chips.

Visual baseline `research-final.png` will diff. Regenerate.

---

## 8. Milestone M4 — Welcome page as scroll-narrative cover

**Goal.** Make the homepage memorable in 5 seconds.

**Files touched.**
- `frontend/src/components/WelcomeScreen.tsx` (rewrite)

**Concrete changes.**

1. Drop the centered hero + 2×2 feature grid pattern entirely. Replace with a scroll-anchored magazine cover that has four panels:

   - **Panel 1 — Cover.** Full-height (`min-h-[calc(100vh-72px)]`). Left half: Fraunces 9-opsz reading `TechPulse` (display 120px), italic subhead `Volume III · A reader's terminal for the agentic era.` in 18px. Right half: a live, scrolling block of mono "telex" showing recent headlines auto-piping in from `/api/news/?page_size=12` — this gives the user immediate proof that "the wire is alive." The blinking `▌` cursor sits at the bottom of the telex stream.
   - **Panel 2 — The pitch.** Below the fold, a Fraunces blockquote (40px) with a serif rule: *"Reading the news is now a research problem. We give you the desk, the wire, and the agent."* Author dateline below in mono.
   - **Panel 3 — The four columns.** The four features (Agentic Research, Curated Feed, Knowledge Graph, Daily Digest) become four newspaper columns separated by hairline rules. Each column: a serif numeral (`I.`, `II.`, `III.`, `IV.`), a Fraunces headline (28px italic), three lines of body in Plex Sans, a mono link `read the docs ↗`.
   - **Panel 4 — CTA strip.** Two buttons across the bottom of the cover: `[ START A RESEARCH DISPATCH → ]` (primary, signal-color background) and `[ READ TODAY'S FEED ]` (outline). These keep `data-testid="welcome-cta-research"` and `data-testid="welcome-cta-feed"`. The `welcome-dismiss` skip link sits at the bottom right in mono 11px.

2. **Page-load choreography.** Framer-motion staggered reveal:
   - `0.00s` cover wordmark fades in (opacity 0 → 1, 320ms).
   - `0.18s` italic subhead slides up 8px.
   - `0.32s` telex stream "boots" (a mono `BOOTING WIRE…` line types itself, then the headlines pipe in one per 80ms).
   - On scroll, IntersectionObserver triggers the next panel's serif numeral to "drop" (translateY -12px → 0, 380ms).

3. Respect `useReducedMotion` — all animations resolve to instant when set.

**Test risk.**

- `data-testid="welcome-screen"` — preserved.
- `data-testid="welcome-cta-research"` / `welcome-cta-feed` / `welcome-dismiss` — preserved.
- The `<h1>` accessible name — not asserted on the welcome page; the masthead's `<h1>` handles the `TechPulse AI` heading check (the welcome page sits inside the main content area while the masthead is in `<header>`).

Visual baseline: no per-tab welcome snapshot exists in `m3-visual-baselines.spec.ts` (the suite navigates to feed/research/knowledge/digest/saved/settings, not `/`). Zero visual-baseline risk.

---

## 9. Milestone M5 — Knowledge Graph, Digest, Saved, Settings polish

**Goal.** Bring the remaining three tabs into the system without disturbing test contracts. Lighter touch than M1-M4.

**Files touched.**
- `frontend/src/components/KnowledgeGraph.tsx` (palette + chrome only)
- `frontend/src/components/DigestView.tsx` (typography + tick-rule sections)
- `frontend/src/components/SavedResearchList.tsx`
- `frontend/src/components/Settings.tsx`
- `frontend/src/components/MarkdownReport.tsx` (typography pass — also feeds the SavedResearch detail view)

**Concrete changes.**

1. **KnowledgeGraph.** Replace the four hardcoded type colors (`#3b82f6` blue, `#10b981` green, `#f59e0b` amber, `#a855f7` purple) with a near-monochrome palette where ONLY mention-count drives saturation:

   ```ts
   const NODE_INK = (mentions: number) => {
     const t = Math.min(1, mentions / 50);   // 0..1
     return mixOklch(/*ink*/ 0.18, /*signal*/ var(--accent-signal), t);
   };
   // type still drives shape, not color:
   // company = square, person = circle, technology = triangle, product = diamond
   ```

   Result: the graph reads as a real entity network (importance = saturation) instead of as a pie chart. The four `kg-stat-companies / kg-stat-people / kg-stat-technologies / kg-stat-products` cards keep their testids; the colored count numbers (lines 704/720/736/752) get small inline shape glyphs (`■ ● ▲ ◆`) in `--foreground` instead of color.

2. **DigestView.** Restyle the existing three Cards as newspaper sections separated by `rule-h-thick` and `uppercase-eyebrow` section labels:
   - "Today's Tech Pulse" → "■ DAILY BRIEF — 12 MAY 2026" with the LLM paragraph in Fraunces 18px italic and the `editorial-drop` class.
   - "Today's Headlines" → grid stays, but each card becomes a serif-title block with a mono source line.
   - "Top Stories Today" — `border-l-4` test selector preserved (`digest.spec.ts:41` and `:104` query `.border-l-4`). We keep the `.border-l-4` class on each top-story row, but the visible left border becomes a 4-character vertical mono index `001`, `002`, … above a 4px-wide left-rule.
   - "Trending Now" — preserves `.bg-orange-50.rounded-lg` per `digest.spec.ts:64`. We keep both class names on the trending chip wrapper for test-compat, then visually override with a `[]` mono wrapper and signal-color hover. The orange-50 background is invisible in dark mode and visually subdued in light mode — acceptable carry.

3. **Settings.** The category checkbox cards become a tabular pivot with mono labels: each category is a row with a `[ ✓ ]` mono checkbox glyph. No rounded cards. Theme + density toggles get the same `[ light · dark ]` ticker treatment as the sidebar.

4. **SavedResearchList.** Each saved report becomes a single broadsheet-style row: `▸ FILED — TUE 12 MAY 14:08` mono eyebrow, Fraunces 22px question title, mono `283 lines · 9 sources · saved 2h ago` meta. Delete is a `[ × ]` mono button.

5. **MarkdownReport.** Typography pass:
   - h1: `font-display text-[28px] font-medium border-b border-[var(--rule)] pb-2 mt-6`
   - h2: `font-display text-[22px] font-medium mt-5`
   - p: `text-[15px] leading-[1.65]`
   - blockquote: `font-display italic text-[18px] border-l-2 border-[var(--accent-signal)] pl-4`
   - code: `font-mono-tx text-[13px] bg-[var(--background-tint)] px-1 py-0.5`
   - The citation anchor `#source-N` styling: `[N]` becomes a true mono bracket with signal-color number.

**Test risk.**

- `digest.spec.ts:41` selects `.border-l-4 h3` — preserved.
- `digest.spec.ts:64` selects `.bg-orange-50.rounded-lg` — preserved (carry the class, override visually with a wrapping `[]` mono frame).
- `kg-stat-*` testids — preserved.
- `kg-type-filter-companies/people/technologies/products` — preserved; chip background swap from per-type color to signal-color when active.
- `saved-research-*` testids — preserved.
- `settings.spec.ts` checkbox role assertions — preserved (Radix Checkbox still renders `role="checkbox"`).

Visual baselines: `knowledge-final.png` / `digest-final.png` / `saved-final.png` / `settings-final.png` all diff; regenerate.

---

## 10. Asset list

### Fonts (Google Fonts CDN, single import line)

- **Fraunces** — opsz 9..144, weights 300/400/500/600/700/900 (display, headlines, drop caps). License: SIL OFL.
- **IBM Plex Sans** — weights 300/400/500/600/700 (body, UI). License: SIL OFL.
- **JetBrains Mono** — weights 400/500/700 (telemetry, mastheads, code). License: SIL OFL.

All three are free for commercial use, all three have variable / wide character coverage, none are on SKILL.md's banned list (Inter, Roboto, Arial, system, Space Grotesk).

### Icons

- Continue using **lucide-react**. Add **@phosphor-icons/react** for the small set of variants where lucide reads too "shadcn-default" — specifically:
  - `<Newspaper weight="duotone" />` for the sidebar mark
  - `<Lightning weight="fill" />` for the streaming-active accent
- Optional: hand-author 4 inline SVG glyphs (◉ ▌ ▸ ━) baked into a small `<TerminalGlyph />` component so they don't anti-alias differently across OSes.

### Textures

- **`/public/textures/grain.png`** — 240×240px tileable noise at ~5% opacity. Generate once (Photoshop noise filter or scripted Perlin). Total weight ~24 KB. Loaded into `.grain::after`.
- **`/public/textures/halftone-32.png`** — optional, 32×32 halftone dot pattern for the digest "front-page" mode, applied to lead-story images at low opacity to fake newsprint screening. Skip if low-priority.

### Misc

- Favicon refresh: a small Fraunces capital `T` over a mono `▌` cursor. Render once as a 32×32 PNG + a 256×256 PNG + an SVG.
- `<title>` becomes `TechPulse — Agentic Desk`.

---

## 11. Open questions — RESOLVED

User signed off on the following (Tue 12 May 2026):

1. **Default theme — LIGHT (newsprint cream).** Dark mode (terminal) is opt-in via the theme toggle. The marketing screenshots can still be taken in dark mode where the signal-cyan accent pops, but the cold-open default is paper-on-ink.
2. **Welcome — SINGLE SCREEN.** Drop the 4-panel scroll narrative. The cover panel IS the entire welcome page; everything fits in the viewport. Faster repeat visits, simpler layout, no IntersectionObserver. The four feature columns and the CTA strip and the dateline all live above the fold.
3. **Drop cap — WIDER scope.** `.editorial-drop` is applied to the first paragraph of: (a) the Digest daily brief, (b) the Research executive summary, (c) the lead story on the News Feed front page, (d) the saved-research detail view, (e) globally on `MarkdownReport`'s first `<p>` when length > 200 chars. The signal-accent drop cap becomes a recurring editorial signature, not a one-off.
4. **Knowledge graph — MONOCHROME, shape + saturation.** Drop the four per-type hex colors entirely. Node fill is `--foreground` lerped toward `--accent-signal` by `mentions / 50` clamped to 1. Type is encoded by shape only — square (company), circle (person), triangle (technology), diamond (product). The stat-card numeric counts get the corresponding shape glyph (`■ ● ▲ ◆`) in `--foreground` next to the number, no color.
5. **Live wire on Welcome — LIVE API feed.** Render an actual mono telex stream of `/api/news/?page_size=12` headlines on the cover. Boot animation types `BOOTING WIRE…` then pipes headlines in at 80ms each. Single fetch on mount, cached in `useState` so revisits don't re-hit the API. Includes a `BOOTING…` → headlines fallback skeleton if the request takes >400ms.

---

## 12. Implementation sequencing summary

| M | Goal | Files | Visual baselines diff? |
| --- | --- | --- | --- |
| **M0** | Foundations: fonts, palette tokens, utilities | `index.html`, `globals.css`, `index.css` | Yes (all 6) |
| **M1** | Sidebar + top-bar masthead | `App.tsx`, `Sidebar.tsx` | Yes (all 6) |
| **M2** | News Feed broadsheet layout | `App.tsx`, `NewsCard.tsx`, `TrendingRail.tsx` | Yes (news-feed) |
| **M3** | Research mode teleprinter | `ResearchMode.tsx`, `SubQuestionsPanel.tsx`, `MarkdownReport.tsx` | Yes (research) |
| **M4** | Welcome scroll narrative | `WelcomeScreen.tsx` | No (route not in baseline suite) |
| **M5** | Knowledge / Digest / Saved / Settings polish | `KnowledgeGraph.tsx`, `DigestView.tsx`, `SavedResearchList.tsx`, `Settings.tsx`, `MarkdownReport.tsx` | Yes (knowledge, digest, saved, settings) |

A single `--update-snapshots` run at the end of each milestone (or one big run at the end if we're feeling brave) is the gating step.

---

## 13. Constraint acknowledgments

- **Tailwind v4 prebuilt bundle, NOT a live compiler.** Every new utility class (`.font-display`, `.uppercase-eyebrow`, `.tick-rule`, `.editorial-drop`, etc.) must be manually authored inside `src/index.css` in an `@layer utilities { }` block. Worker agents cannot run `npx tailwindcss` to regenerate. The list in §4 step 5 is exhaustive for M0-M5; if a worker needs a utility not in that list, they must add it by hand AND record it in this doc.
- **No React Router migration.** History-API routing stays in `App.tsx`.
- **No mobile breakpoints.** Desktop-only; `w-72` sidebar fixed.
- **53 Playwright contracts preserved.** Every `data-testid` and `role` in current use is named in this doc and kept. The `text-gray-500` source-name class is kept on `NewsCard`. The `.border-l-4` class on digest top stories is kept. The `.bg-orange-50.rounded-lg` class on digest trending chips is kept. The `getByRole("heading", { name: /TechPulse AI/i })` is preserved via `aria-label` on the masthead's `<h1>`.
- **Visual baselines will require regeneration.** Documented above. Worker agents must run `PLAYWRIGHT_SLOW_MO=0 npx playwright test m3-visual-baselines.spec.ts --update-snapshots` once per milestone (or final).

---

*— end of design doc —*
