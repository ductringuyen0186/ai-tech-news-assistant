import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";
import { API_ENDPOINTS, apiFetch } from "../config/api";

/**
 * TrendingRail — horizontal chip row of the top ENTITIES by mention count
 * this week.
 *
 * Polish iter 3 / Part D — previously this rendered top categories using
 * the per-category article-count rollup. We swapped to the knowledge-graph
 * trending-entities endpoint (added in Part B) so the chips show what's
 * actually being talked about across the corpus, not just which bucket
 * has the most articles.
 *
 * Click behaviour: calls ``onSelectCategory(entityName)`` — the parent owns
 * the actual filter state. The prop name is kept as ``onSelectCategory``
 * even though we now pass entity names, because the parent's filter pipeline
 * (App.tsx ``selectedCategories``) is reused as-is. Filtering is approximate
 * (see note in App.tsx) — when an entity name is in the selected list we
 * do a case-insensitive substring match on each article's title and summary.
 *
 * The ``data-testid="news-feed-trending-rail"`` and
 * ``data-testid="news-feed-trending-chip"`` selectors are PRESERVED so the
 * existing Playwright assertions still pass (the semantics are now "entity"
 * but the testid stays).
 */

interface TrendingRailProps {
  /** Currently-selected entity names. A chip whose name matches an entry
   *  in this list renders in its "selected" variant. */
  selectedCategories: string[];
  /** Fired when a chip is clicked. The entity name is the only argument. */
  onSelectCategory: (entityName: string) => void;
  /** Maximum number of chips to render (default 8 — bumped from 5 for the
   *  news-feed surface so the rail feels populated). */
  limit?: number;
}

interface TrendingEntity {
  id: number;
  name: string;
  type: string;
  mention_count: number;
  score: number;
}

export function TrendingRail({
  selectedCategories,
  onSelectCategory,
  limit = 8,
}: TrendingRailProps) {
  const [trending, setTrending] = useState<TrendingEntity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const loadTrending = async () => {
      try {
        setLoading(true);
        // Polish iter 3 / Part D — reuse the Part B knowledge-graph trending
        // endpoint instead of building a parallel "trending categories"
        // pipeline. ``days=7&limit=N`` matches the rail's "this week" framing.
        const params = new URLSearchParams({
          days: "7",
          limit: String(limit),
        });
        const data = await apiFetch<any>(
          `${API_ENDPOINTS.knowledgeGraphTrending}?${params}`
        );
        if (cancelled) return;
        const entities: TrendingEntity[] = Array.isArray(data?.entities)
          ? data.entities
          : [];
        // Defensive sort by mention_count desc — backend already returns
        // them in score order, but the chip badge shows mention_count so we
        // make sure the displayed number monotonically descends.
        const sorted = [...entities].sort(
          (a, b) => (b.mention_count || 0) - (a.mention_count || 0)
        );
        setTrending(sorted);
      } catch (err) {
        if (!cancelled) {
          console.error("TrendingRail: failed to load trending entities", err);
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
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground pr-2 font-medium">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>Trending Now</span>
        </div>
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-7 w-24 rounded-full" />
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
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground pr-2 shrink-0 font-medium">
        <TrendingUp className="w-3.5 h-3.5" />
        <span>Trending Now</span>
      </div>
      {trending.map((t) => {
        const isActive = selectedCategories.includes(t.name);
        return (
          <button
            key={`${t.id}-${t.name}`}
            type="button"
            data-testid="news-feed-trending-chip"
            // ``data-category`` is preserved (and now carries the entity
            // name) so the existing Playwright assertion that reads this
            // attribute keeps working.
            data-category={t.name}
            data-entity-type={t.type}
            onClick={() => onSelectCategory(t.name)}
            className={[
              "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition-colors",
              isActive
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-card text-foreground hover:bg-accent/40 hover:text-accent-foreground",
            ].join(" ")}
          >
            <span className="font-medium">{t.name}</span>
            <Badge
              variant="secondary"
              className="h-4 px-1.5 text-[10px] font-normal leading-none"
            >
              {t.mention_count}
            </Badge>
          </button>
        );
      })}
    </div>
  );
}
