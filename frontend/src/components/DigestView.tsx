import {
  Mail,
  TrendingUp,
  Calendar,
  BarChart3,
  Newspaper,
  Sparkles,
  ExternalLink,
  Layers,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Skeleton } from "./ui/skeleton";

/**
 * DigestView — daily digest tab, restyled for Mission 3 / Milestone 3 and
 * extended for polish iter 3 / Part C.
 *
 * Polish iter 3 additions (rendered above the existing layout):
 *   1. "Today's Tech Pulse" hero card — AI-generated executive overview
 *      from ``/api/digest/daily-summary``. Cached server-side per day.
 *   2. "Today's Headlines" — curated top 3-5 stories from
 *      ``/api/digest/curated``, ranked by recency × source-weight ×
 *      mention-count.
 *   3. "Today by Topic" — articles grouped by the ``categories`` JSON
 *      field, from ``/api/digest/topics``.
 *
 * Density + design-token treatment (existing):
 *   - Top stories use a dense one-line-per-row layout (numbered marker,
 *     title, source/category chips). `border-l-4` and an inner `<h3>` are
 *     preserved so the existing Playwright selectors still match.
 *   - Trending topics become a horizontal chip row using design tokens.
 *   - Source distribution ("Coverage by Topic") uses a single accent
 *     colour for the bars (no per-source palette), via the `--primary`
 *     token, so the visual coherence the ticket asks for is automatic.
 *
 * Preserved selectors:
 *   - text "Daily Tech Digest"
 *   - text "Top Stories Today"
 *   - text "Trending Now"
 *   - `.border-l-4` blocks each containing one `<h3>` (top stories)
 *   - `[data-slot="badge"]` chips inside each top story
 *   - `.bg-orange-50.rounded-lg` on each trending topic chip (compat)
 */

interface DigestStory {
  id: string;
  title: string;
  source: string;
  summaryShort: string;
  category: string[];
}

interface DigestTrendingTopic {
  id: string;
  title: string;
  category: string[];
}

interface DailySummary {
  summary: string;
  generated_at: string;
  article_count: number;
}

interface CuratedHeadline {
  id: number;
  title: string;
  source: string;
  summary: string;
  url: string;
  image_url: string | null;
  published_at: string;
  categories: string[];
  score: number;
  mention_count: number;
}

interface TopicCluster {
  name: string;
  slug: string;
  count: number;
  preview: Array<{
    id: number;
    title: string;
    source: string;
    summary: string;
    url: string;
    published_at: string;
  }>;
}

interface DigestViewProps {
  digest: {
    date: string;
    topStories: DigestStory[];
    categoryBreakdown: Record<string, number>;
    trendingTopics: DigestTrendingTopic[];
  };
  /** Polish iter 3 / Part C — optional. Renders the hero summary card. */
  dailySummary?: DailySummary | null;
  /** True while the daily-summary fetch is in flight. */
  dailySummaryLoading?: boolean;
  /** Polish iter 3 / Part C — optional. Renders the curated headlines. */
  curatedHeadlines?: CuratedHeadline[] | null;
  /** Polish iter 3 / Part C — optional. Renders the topic clusters. */
  topicClusters?: TopicCluster[] | null;
}

function relativeTime(iso: string | undefined | null): string {
  if (!iso) return "";
  try {
    const date = new Date(iso);
    const now = Date.now();
    const diffSec = Math.floor((now - date.getTime()) / 1000);
    if (diffSec < 60) return "just now";
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)} min ago`;
    if (diffSec < 86_400) return `${Math.floor(diffSec / 3600)} hr ago`;
    if (diffSec < 7 * 86_400) return `${Math.floor(diffSec / 86_400)} d ago`;
    return date.toLocaleDateString();
  } catch {
    return "";
  }
}

export function DigestView({
  digest,
  dailySummary,
  dailySummaryLoading,
  curatedHeadlines,
  topicClusters,
}: DigestViewProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const maxBreakdown = Math.max(
    1,
    ...Object.values(digest.categoryBreakdown || {})
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-card border-border">
        <CardHeader className="py-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center">
              <Mail className="w-5 h-5 text-primary" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-xl font-semibold text-foreground">Daily Tech Digest</CardTitle>
              <CardDescription className="flex items-center gap-1.5 text-xs">
                <Calendar className="w-3.5 h-3.5" />
                {formatDate(digest.date)}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Polish iter 3 / Part C1 — "Today's Tech Pulse" AI summary hero card.
          Accent-bordered warm-beige tint with the LLM-generated paragraph and
          a footer line showing how recently it was generated and how many
          articles fed the prompt. Hidden if neither a summary nor a loading
          state was passed in.

          IMPORTANT: do NOT use ``border-l-4`` here — the existing digest
          density test (digest.spec.ts:162) selects the first ``.border-l-4``
          element on the page expecting a top-story row, and our hero card
          renders well above 200px tall. We use a 2px accent border + tinted
          background for visual emphasis instead. */}
      {(dailySummary || dailySummaryLoading) && (
        <Card
          data-testid="digest-daily-summary-card"
          className="border-2 border-accent/60 bg-accent/10"
        >
          <CardHeader className="py-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <CardTitle className="text-base font-semibold text-foreground">Today's Tech Pulse</CardTitle>
            </div>
            <CardDescription className="text-xs">
              AI-generated overview of the day's most important stories
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-5">
            {dailySummaryLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-4/5" />
              </div>
            ) : dailySummary ? (
              <>
                <p
                  data-testid="digest-daily-summary-text"
                  className="text-sm leading-relaxed text-foreground"
                  style={{
                    overflowWrap: "anywhere",
                    wordBreak: "break-word",
                  }}
                >
                  {dailySummary.summary}
                </p>
                <div className="mt-3 flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>
                    Generated {relativeTime(dailySummary.generated_at) || "today"}
                    {" • "}
                    {dailySummary.article_count} article
                    {dailySummary.article_count === 1 ? "" : "s"}
                  </span>
                </div>
              </>
            ) : null}
          </CardContent>
        </Card>
      )}

      {/* Polish iter 3 / Part C2 — Curated headlines. Up to 5 stories chosen
          by the backend's recency × source-weight × mention-count formula.
          Single column on narrow screens; 2 across at md; 3 across at lg. */}
      {curatedHeadlines && curatedHeadlines.length > 0 && (
        <Card>
          <CardHeader className="py-4">
            <div className="flex items-center gap-2">
              <Newspaper className="w-4 h-4 text-primary" />
              <CardTitle className="text-base font-semibold text-foreground">Today's Headlines</CardTitle>
            </div>
            <CardDescription className="text-xs">
              The day's most important stories, ranked by recency, source
              weight, and how often they're mentioned across the corpus
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-5">
            <div
              data-testid="digest-curated-headlines"
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            >
              {curatedHeadlines.map((story) => (
                <a
                  key={story.id}
                  data-testid={`digest-curated-story-${story.id}`}
                  href={story.url || "#"}
                  target={story.url ? "_blank" : undefined}
                  rel={story.url ? "noopener noreferrer" : undefined}
                  className="group flex flex-col rounded-md border border-border bg-card hover:bg-accent/10 hover:border-accent/60 transition-colors overflow-hidden"
                >
                  {story.image_url ? (
                    <div className="w-full aspect-[16/9] overflow-hidden bg-muted">
                      <img
                        src={story.image_url}
                        alt=""
                        loading="lazy"
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.currentTarget as HTMLImageElement).style.display =
                            "none";
                        }}
                      />
                    </div>
                  ) : null}
                  <div className="p-4 flex flex-col gap-2 flex-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <Badge
                        variant="outline"
                        className="h-5 px-1.5 text-[10px] font-medium border-border bg-muted text-foreground"
                      >
                        {story.source}
                      </Badge>
                      {story.categories
                        .slice(0, 1)
                        .filter((c) => c && c !== story.source)
                        .map((cat) => (
                          <Badge
                            key={cat}
                            variant="secondary"
                            className="h-5 px-1.5 text-[10px] font-normal"
                          >
                            {cat}
                          </Badge>
                        ))}
                    </div>
                    <h3
                      className="text-[15px] font-semibold text-foreground leading-snug line-clamp-3"
                      style={{
                        overflowWrap: "anywhere",
                        wordBreak: "break-word",
                      }}
                    >
                      {story.title}
                    </h3>
                    {story.summary ? (
                      <p
                        className="text-sm text-muted-foreground leading-relaxed line-clamp-2"
                        style={{
                          overflowWrap: "anywhere",
                          wordBreak: "break-word",
                        }}
                      >
                        {story.summary}
                      </p>
                    ) : null}
                    <div className="mt-auto flex items-center justify-between gap-2 pt-2 text-xs text-muted-foreground">
                      <span>{relativeTime(story.published_at)}</span>
                      <span className="inline-flex items-center gap-1 text-primary font-medium group-hover:underline">
                        Read more
                        <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Polish iter 3 / Part C3 — Topic clusters. Today's articles grouped
          by their ``categories`` JSON field. Each block shows the topic name,
          count badge, 2-3 article previews, and a "See all" link. */}
      {topicClusters && topicClusters.length > 0 && (
        <Card>
          <CardHeader className="py-4">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-primary" />
              <CardTitle className="text-base font-semibold text-foreground">Today by Topic</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Articles grouped by category
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-5">
            <div
              data-testid="digest-topic-clusters"
              className="flex flex-col gap-3"
            >
              {topicClusters.map((cluster) => (
                <div
                  key={cluster.slug}
                  data-testid={`digest-topic-cluster-${cluster.slug}`}
                  className="rounded-md border border-border bg-card p-4"
                >
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 min-w-0">
                      <h3 className="text-base font-semibold text-foreground truncate">
                        {cluster.name}
                      </h3>
                      <Badge
                        variant="secondary"
                        className="h-5 px-1.5 text-[10px] font-normal"
                      >
                        {cluster.count}
                      </Badge>
                    </div>
                    {cluster.count > cluster.preview.length ? (
                      <span className="text-xs text-muted-foreground shrink-0">
                        +{cluster.count - cluster.preview.length} more
                      </span>
                    ) : null}
                  </div>
                  <div className="flex flex-col gap-2">
                    {cluster.preview.map((article) => (
                      <a
                        key={article.id}
                        data-testid={`digest-cluster-article-${article.id}`}
                        href={article.url || "#"}
                        target={article.url ? "_blank" : undefined}
                        rel={article.url ? "noopener noreferrer" : undefined}
                        className="flex items-start gap-2 rounded px-2 py-2 hover:bg-accent/10 transition-colors"
                      >
                        <div className="flex-1 min-w-0 space-y-1">
                          <p
                            className="text-sm font-medium text-foreground leading-snug line-clamp-2"
                            style={{
                              overflowWrap: "anywhere",
                              wordBreak: "break-word",
                            }}
                          >
                            {article.title}
                          </p>
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs text-muted-foreground">
                              {article.source}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              ·
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {relativeTime(article.published_at)}
                            </span>
                          </div>
                        </div>
                        <ExternalLink className="w-3 h-3 text-muted-foreground mt-1 shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top Stories — dense one-row-per-story layout. */}
      <Card>
        <CardHeader className="py-4">
          <div className="flex items-center gap-2">
            <Newspaper className="w-4 h-4 text-primary" />
            <CardTitle className="text-base font-semibold text-foreground">Top Stories Today</CardTitle>
          </div>
          <CardDescription className="text-xs">
            The most important tech news you shouldn't miss
          </CardDescription>
        </CardHeader>
        <CardContent className="pb-5">
          <div
            data-testid="digest-top-stories"
            className="flex flex-col gap-2"
          >
            {digest.topStories.map((story, idx) => (
              <div
                key={story.id}
                data-testid="digest-top-story-row"
                className="border-l-4 border-primary pl-3 py-2 rounded-r-md hover:bg-accent/5 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-semibold">
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0 space-y-1.5">
                    <h3
                      className="text-[15px] font-semibold text-foreground leading-snug"
                      style={{
                        overflowWrap: "anywhere",
                        wordBreak: "break-word",
                      }}
                    >
                      {story.title}
                    </h3>
                    <p
                      className="text-sm text-muted-foreground leading-relaxed line-clamp-2"
                      style={{
                        overflowWrap: "anywhere",
                        wordBreak: "break-word",
                      }}
                    >
                      {story.summaryShort}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      <Badge
                        variant="outline"
                        className="h-5 px-1.5 text-[10px] font-medium border-border bg-muted text-foreground"
                      >
                        {story.source}
                      </Badge>
                      {story.category
                        .filter((cat) => cat && cat !== story.source)
                        .slice(0, 2)
                        .map((cat) => (
                          <Badge
                            key={cat}
                            variant="secondary"
                            className="h-5 px-1.5 text-[10px] font-normal"
                          >
                            {cat}
                          </Badge>
                        ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Trending Topics — horizontal chip row (dense). */}
        <Card>
          <CardHeader className="py-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              <CardTitle className="text-base font-semibold text-foreground">Trending Now</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Most discussed topics today
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-5">
            <div
              data-testid="digest-trending-row"
              className="flex flex-wrap gap-1.5"
            >
              {digest.trendingTopics.map((topic) => (
                <div
                  key={topic.id}
                  data-testid="digest-trending-chip"
                  /*
                    The `bg-orange-50 rounded-lg` literals are intentionally
                    preserved so the existing digest.spec.ts trending selector
                    keeps matching. We layer design-token classes on top so
                    dark mode reads as a subtle accent tint rather than
                    plain orange.
                  */
                  className="bg-orange-50 dark:bg-orange-500/10 rounded-lg border border-orange-200 dark:border-orange-500/20 px-2.5 py-1.5 inline-flex items-center gap-1.5 max-w-full"
                >
                  <p
                    className="text-xs font-medium text-foreground truncate"
                    style={{
                      overflowWrap: "anywhere",
                      wordBreak: "break-word",
                    }}
                  >
                    {topic.title}
                  </p>
                  {topic.category
                    .filter((c) => c && c.trim().length > 0)
                    .slice(0, 1)
                    .map((cat) => (
                      <Badge
                        key={cat}
                        variant="outline"
                        className="h-4 px-1 text-[10px] font-normal border-border"
                      >
                        {cat}
                      </Badge>
                    ))}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Source / coverage distribution — single accent color, no
            per-source palette (visual coherence). */}
        <Card>
          <CardHeader className="py-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              <CardTitle className="text-base font-semibold text-foreground">Coverage by Topic</CardTitle>
            </div>
            <CardDescription className="text-xs">
              News distribution across categories
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-5">
            <div
              data-testid="digest-source-distribution"
              className="space-y-3"
            >
              {Object.entries(digest.categoryBreakdown)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 6)
                .map(([category, count]) => (
                  <div
                    key={category}
                    data-testid="digest-source-row"
                    className="flex items-center gap-3"
                  >
                    <div className="flex-1 min-w-0 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-foreground truncate">
                          {category}
                        </span>
                        <span className="text-xs text-muted-foreground tabular-nums">
                          {count} articles
                        </span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-primary h-1.5 rounded-full transition-all"
                          style={{
                            width: `${(count / maxBreakdown) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Email Subscribe CTA */}
      <Card className="bg-card border-border">
        <CardContent className="py-6">
          <div className="text-center space-y-3">
            <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center mx-auto">
              <Mail className="w-5 h-5 text-primary" />
            </div>
            <h3 className="text-base font-semibold text-foreground">
              Get Your Daily Digest via Email
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-sm mx-auto">
              Never miss important tech news. Receive a personalized digest
              every morning.
            </p>
            <Button size="sm" className="h-8 text-xs">
              Subscribe to Daily Digest
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
