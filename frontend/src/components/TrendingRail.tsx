import { useEffect, useState } from "react";
import { Skeleton } from "./ui/skeleton";
import { API_ENDPOINTS, apiFetch } from "../config/api";

/**
 * TrendingRail -- horizontal ticker tape of the top entities by mention
 * count this week.
 *
 * M2 rewrite: drops the rounded pill row in favour of a mono ticker tape
 * with a leading "> trending" label, dot separators implied by gap, and
 * a signal-color count flag (`|N`) on each entity. The whole rail sits
 * inside a hairline-ruled band (`border-y border-[var(--rule)]`) and uses
 * `whitespace-nowrap` so entries never wrap.
 *
 * Test-contract preservation:
 *   - data-testid="news-feed-trending-rail"      (root)
 *   - data-testid="news-feed-trending-chip"      (per-entity buttons)
 *   - data-category="<entity name>"              (per-button data attr)
 *   - data-entity-type="<entity type>"           (per-button data attr)
 */

interface TrendingRailProps {
  /** Currently-selected entity names. A chip whose name matches an entry
   *  in this list renders in its "selected" variant. */
  selectedCategories: string[];
  /** Fired when a chip is clicked. The entity name is the only argument. */
  onSelectCategory: (entityName: string) => void;
  /** Maximum number of chips to render (default 12 -- longer ticker reads
   *  more like a wire feed than a 5-chip toolbar). */
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
  limit = 12,
}: TrendingRailProps) {
  const [trending, setTrending] = useState<TrendingEntity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const loadTrending = async () => {
      try {
        setLoading(true);
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

  if (loading) {
    return (
      <div
        data-testid="news-feed-trending-rail"
        className="relative border-y border-[var(--rule)] py-2 overflow-hidden"
      >
        <div className="flex items-center gap-4 font-mono-tx text-[11px] uppercase-eyebrow whitespace-nowrap">
          <span className="text-foreground-soft shrink-0">&#9658; trending</span>
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-20" />
          ))}
        </div>
      </div>
    );
  }

  if (trending.length === 0) {
    return null;
  }

  return (
    <div
      data-testid="news-feed-trending-rail"
      className="relative border-y border-[var(--rule)] py-2 overflow-hidden"
    >
      <div className="flex items-center gap-4 font-mono-tx text-[11px] uppercase-eyebrow whitespace-nowrap">
        <span className="text-foreground-soft shrink-0">&#9658; trending</span>
        {trending.map((t) => {
          const isActive = selectedCategories.includes(t.name);
          return (
            <button
              key={`${t.id}-${t.name}`}
              type="button"
              data-testid="news-feed-trending-chip"
              data-category={t.name}
              data-entity-type={t.type}
              onClick={() => onSelectCategory(t.name)}
              className={[
                "shrink-0 px-1.5 py-0.5 border transition-colors",
                isActive
                  ? "text-signal border-[var(--rule)]"
                  : "text-foreground-soft border-transparent hover:border-[var(--rule)] hover:text-foreground",
              ].join(" ")}
            >
              {t.name.toUpperCase()}{" "}
              <span className="text-signal">&#9612;{t.mention_count}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
