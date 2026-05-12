# [Feature] Design system foundation — sidebar + dark theme + Cmd+K palette

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P0                                                                     |
| Estimate       | L                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | frontend, design-system, breaking-internal                             |
| Linked PRD     | [docs/prds/ui-polish.md](../prds/ui-polish.md) — Milestone 1           |
| Linked design  | [docs/designs/ui-polish.md](../designs/ui-polish.md)                   |

## Context
The current top-tabs layout looks like a basic shadcn/ui demo. Mission 3 rebuilds the chrome to a Vercel/Linear developer-dashboard aesthetic. This is the foundation milestone — no tab content changes yet, just the shell.

## Description
**Today:** Top horizontal tabs, light theme, no command palette, no keyboard nav.

**After:** Left sidebar nav with 6 entries + Saved Research entry + theme toggle. Dark default; light option. Cmd+K (Ctrl+K on Win) opens a command palette listing tabs and recent research. Typography refined to Linear-dense.

1. Install `cmdk` for the command palette primitive
2. `App.tsx` rewritten:
   - Wraps everything in `ThemeProvider` (custom, ~50 lines — Tailwind class strategy)
   - Wraps in `CommandPaletteProvider` (provides `useCommandPalette` hook with `open()` / `close()`)
   - Renders `<Sidebar />` + `<MainContent />` in a flex layout
3. `Sidebar.tsx` — 6 nav items (News Feed, Research, Knowledge Graph, Digest, Ask AI, Settings) + Saved entry. Theme toggle at bottom. Active state with accent-color left border. **Each nav item MUST have `role="tab"`** and the wrapper `role="tablist"` so the existing 35 Playwright tests' `getByRole("tab", {name: /Research/i})` selectors keep working
4. `CommandPalette.tsx` — `cmdk`-based modal. Cmd+K opens, Esc closes, arrow keys + Enter navigate. Lists: 6 tabs + last 10 research queries (from localStorage). Backdrop click closes
5. Theme system:
   - Tailwind `darkMode: 'class'` in config
   - `index.html` inline script reads `localStorage.techpulse-theme` and sets `<html class="dark">` BEFORE React mounts (FOUC-free)
   - Default: `dark` if no preference
6. `styles/globals.css` + `tailwind.config.ts`:
   - New CSS variables for dark/light themes (background, surface, text, muted, accent, running, done, error)
   - System-font stack (no web fonts) so Playwright baselines don't flake
   - 13-14px base body, 1.4 line-height (Linear-dense)

## Acceptance criteria
- [ ] `cmdk` installed and pinned in `package.json`
- [ ] `App.tsx` renders sidebar layout; all 6 tabs reachable via sidebar click
- [ ] Sidebar's nav items have `role="tab"` so existing selectors work
- [ ] Theme is dark by default; toggle in sidebar bottom flips between dark/light
- [ ] `localStorage.techpulse-theme` persists across reload; NO theme flash
- [ ] Cmd+K opens the palette; arrow keys + Enter navigate; Esc closes
- [ ] Palette lists 6 tabs + last 10 research queries from localStorage
- [ ] Tailwind config has `darkMode: 'class'` + new semantic colors
- [ ] All 35 existing Playwright tests pass against the new layout
- [ ] New `frontend/e2e/sidebar.spec.ts` with: (a) sidebar renders, (b) theme toggle flips class, (c) Cmd+K opens palette, (d) Esc closes
- [ ] Backend untouched. Backend test suite still green

## Implementation notes
Files:
- `frontend/package.json` — add `cmdk`
- `frontend/src/App.tsx` — rewrite layout
- `frontend/src/components/Sidebar.tsx` — NEW
- `frontend/src/components/CommandPalette.tsx` — NEW
- `frontend/src/components/ThemeProvider.tsx` — NEW (or use a 30-line ad-hoc context)
- `frontend/index.html` — inline theme bootstrap script
- `frontend/tailwind.config.ts` — dark mode + semantic colors
- `frontend/src/styles/globals.css` — CSS variables, typography
- `frontend/e2e/sidebar.spec.ts` — NEW

Gotchas:
- The Playwright selectors `getByRole("tab", {name: /Research/i})` rely on the tab having `role="tab"` AND an accessible name. Verify in DevTools after the rewrite
- `cmdk` ships its own styling; override with Tailwind to match the dark theme
- The inline theme bootstrap script MUST run synchronously before React. Use a `<script>` tag in `<head>`, NOT a module import
- DON'T migrate tab content in this milestone. Tabs render their existing components unchanged

## Out of scope
- Markdown rendering migration (M2)
- Tab content polish (M3-M4)
- Saved Research wiring (M5)
- framer-motion (M6)

## Verification
- `cd frontend && npx playwright test` — all 35 + 4 new = 39 tests pass
- Manual: load app, verify dark default, toggle to light, reload, verify persistence
- Manual: Cmd+K, navigate, Enter, Esc — no console errors

## Risks
- The existing 35 tests are fragile to selector changes. Take care preserving `role="tab"` semantics
- Theme flash on reload is a common pitfall; verify by hard-refreshing in DevTools 5+ times
