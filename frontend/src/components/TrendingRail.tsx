import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";
import { API_ENDPOINTS, apiFetch } from "../config/api";

/**
 * TrendingRail — horizontal chip row of the top categories by article count.
 *
 * Mission 3 / Milestone 3 — sits above the news-feed filter chips and gives
 * the user a one-click jump into the largest categories. Categories are
 * pulled from `/api/news/categories`, then counts come from `/api/news?
 * category=X&page_size=1` (we only need the total_items from pagination —
 * cheap because page_size=1 fetches almost nothing).
 *
 * Click behaviour: calls `onSelectCategory(name)` with the chip's category.
 * The parent owns the actual filter state — this component is presentational
 * past the count-aggregation effect.
 */

interface TrendingRailProps {
  /** Currently-selected categories from the parent. The chip whose name
   *  matches an entry in this list renders in its "selected" variant. */
  selectedCategories: string[];
  /** Fired when a chip is clicked. The chip name is the only argument. */
  onSelectCategory: (category: string) => void;
  /** Maximum number of chips to render (default 5). */
  limit?: number;
}

interface TrendingCategory {
  name: string;
  count: number;
}

export function TrendingRail({
  selectedCategories,
  onSelectCategory,
  limit = 5,
}: TrendingRailProps) {
  const [trending, setTrending] = useState<TrendingCategory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const loadTrending = async () => {
      try {
        setLoading(true);

        // 1. Pull the live category vocabulary from the backend. This matches
        //    what `/api/news` will actually filter against.
        const envelope = await apiFetch<any>(API_ENDPOINTS.newsCategories);
        if (cancelled) return;
        const data = envelope?.data ?? envelope;
        const categories: string[] = Array.isArray(data?.categories)
          ? data.categories
          : [];

        if (categories.length === 0) {
          setTrending([]);
          return;
        }

        // 2. Fetch a one-article page per category in parallel; we only need
        //    pagination.total_items. This avoids an extra backend route.
        const results = await Promise.all(
          categories.map(async (cat) => {
            try {
              const params = new URLSearchParams({
                page: "1",
                page_size: "1",
                category: cat,
              });
              const res = await apiFetch<any>(
                `${API_ENDPOINTS.news}?${params}`
              );
              const total = Number(res?.pagination?.total_items ?? 0);
              return { name: cat, count: total };
            } catch {
              return { name: cat, count: 0 };
            }
          })
        );

        if (cancelled) return;

        // 3. Sort by count descending, take the top `limit`, drop empties.
        const top = results
          .filter((r) => r.count > 0)
          .sort((a, b) => b.count - a.count)
          .slice(0, limit);

        setTrending(top);
      } catch (err) {
        if (!cancelled) {
          console.error("TrendingRail: failed to load trending categories", err);
          setTrending([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadTrending();
    return () => {
      cancelled = true;
    };
  }, [limit]);

  // Loading: render 4 skeleton chips so the layout doesn't jump.
  if (loading) {
    return (
      <div
        data-testid="news-feed-trending-rail"
        className="flex items-center gap-2 flex-wrap"
      >
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground pr-2">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>Trending Now</span>
        </div>
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-6 w-24 rounded-full" />
        ))}
      </div>
    );
  }

  // Empty: hide the rail entirely (per ticket).
  if (trending.length === 0) {
    return null;
  }

  return (
    <div
      data-testid="news-feed-trending-rail"
      className="flex items-center gap-2 flex-wrap max-w-3xl"
    >
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground pr-2 shrink-0">
        <TrendingUp className="w-3.5 h-3.5" />
        <span>Trending Now</span>
      </div>
      {trending.map((t) => {
        const isActive = selectedCategories.includes(t.name);
        return (
          <button
            key={t.name}
            type="button"
            data-testid="news-feed-trending-chip"
            data-category={t.name}
            onClick={() => onSelectCategory(t.name)}
            className={[
              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors",
              isActive
                ? "border-primary bg-primary/10 text-primary"
                : "border-border bg-card text-foreground hover:bg-accent/40 hover:text-accent-foreground",
            ].join(" ")}
          >
            <span className="font-medium">{t.name}</span>
            <Badge
              variant="secondary"
              className="h-4 px-1.5 text-[10px] font-normal leading-none"
            >
              {t.count}
            </Badge>
          </button>
        );
      })}
    </div>
  );
}
