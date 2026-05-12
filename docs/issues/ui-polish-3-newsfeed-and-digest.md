# [Feature] News Feed + Digest tab polish (Trending rail + Linear-dense layout)

| Field          | Value                                                                  |
|----------------|------------------------------------------------------------------------|
| Type           | Feature                                                                |
| Priority       | P1                                                                     |
| Estimate       | M                                                                      |
| Assignee       | unassigned                                                             |
| Labels         | frontend, news-feed, digest                                            |
| Linked PRD     | [docs/prds/ui-polish.md](../prds/ui-polish.md) — Milestone 3           |
| Linked design  | [docs/designs/ui-polish.md](../designs/ui-polish.md)                   |

## Context
Two discovery surfaces need the new design language: News Feed (browse-discovery) and Digest (curated-discovery). After M1 lands the sidebar + theme, these tabs need to feel like Linear/Vercel lists.

## Description
**News Feed changes:**
1. **Trending Now rail** at the top of the tab. Renders 3-5 categories ordered by article count in the past 7 days. Each rail item: category name + count + click to filter feed
2. **Linear-dense article cards**: 13px body text, 4-8px row padding, thumbnail-as-square (left), title + source + date stacked (right). Hover state: subtle accent-color background tint
3. Existing filter chips at the top stay but reformat to match the density
4. Existing search input stays at the top

**Digest changes:**
1. Top stories: each row is dense (similar to News Feed cards)
2. Source distribution chips use status-color tokens (TechCrunch = blue, Ars = orange, etc — or just neutral with article-count badge)
3. Trending topics section reformatted as a horizontal chip row

## Acceptance criteria
- [ ] News Feed: Trending Now rail visible at the top with at least 3 categories. Click filters the feed below
- [ ] News Feed: article cards are linear-dense (verify CSS: `padding: ≤8px`, `font-size: ≤14px`)
- [ ] News Feed: hover state on cards shows accent-tint background
- [ ] Digest: top stories rendered in dense layout
- [ ] Digest: source distribution rendered with consistent color tokens
- [ ] All existing `news-feed.spec.ts` tests still pass (~7 tests)
- [ ] All existing `digest.spec.ts` tests still pass (~5 tests)
- [ ] New assertion in `news-feed.spec.ts`: Trending Now rail with ≥3 category items
- [ ] New assertion in `digest.spec.ts`: dense layout (max-height per row constraint)

## Implementation notes
Files:
- `frontend/src/components/NewsFeed.tsx` — add Trending rail, reformat cards
- `frontend/src/components/DigestView.tsx` — dense layout, color tokens
- `frontend/src/components/TrendingRail.tsx` — NEW. Reusable horizontal chip row
- `frontend/e2e/news-feed.spec.ts` — add trending rail assertion
- `frontend/e2e/digest.spec.ts` — add density assertion

Gotchas:
- Trending Now needs a way to compute "top categories by article count this week" — either reuse `/api/news/categories` or add a new endpoint `/api/news/trending-categories?days=7`. Lean on the existing endpoint first; only add a new one if necessary
- The 8-category rubric tests already assert no horizontal overflow on cards — keep that holding after the density change
- Don't change the `data-testid` hooks the existing tests use (article-card, category-chip, etc) — preserve them

## Out of scope
- Knowledge Graph / Ask AI / Settings (M4)
- Saved Research (M5)
- Animations (M6)

## Verification
- `cd frontend && npx playwright test news-feed.spec.ts digest.spec.ts` — all pass
- Manual: dark theme — verify cards readable; light theme — verify cards readable

## Risks
- The Trending Now rail competes for vertical space with the existing filter chips. Make sure both fit comfortably above the fold on a 1280×720 viewport
- "Top categories this week" might return only 1-2 categories if the corpus is small — handle gracefully (show what you have, no error)
