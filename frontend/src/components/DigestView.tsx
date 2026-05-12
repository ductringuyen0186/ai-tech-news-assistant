import {
  Mail,
  TrendingUp,
  Calendar,
  BarChart3,
  Newspaper,
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

/**
 * DigestView — daily digest tab, restyled for Mission 3 / Milestone 3.
 *
 * Density + design-token treatment:
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

interface DigestViewProps {
  digest: {
    date: string;
    topStories: Array<{
      id: string;
      title: string;
      source: string;
      summaryShort: string;
      category: string[];
    }>;
    categoryBreakdown: Record<string, number>;
    trendingTopics: Array<{
      id: string;
      title: string;
      category: string[];
    }>;
  };
}

export function DigestView({ digest }: DigestViewProps) {
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
    <div className="space-y-4">
      {/* Header */}
      <Card className="bg-card border-border">
        <CardHeader className="py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center">
              <Mail className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">Daily Tech Digest</CardTitle>
              <CardDescription className="flex items-center gap-1.5 mt-0.5 text-xs">
                <Calendar className="w-3.5 h-3.5" />
                {formatDate(digest.date)}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Top Stories — dense one-row-per-story layout. */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center gap-2">
            <Newspaper className="w-4 h-4 text-primary" />
            <CardTitle className="text-base">Top Stories Today</CardTitle>
          </div>
          <CardDescription className="text-xs">
            The most important tech news you shouldn't miss
          </CardDescription>
        </CardHeader>
        <CardContent className="pb-4">
          <div
            data-testid="digest-top-stories"
            className="flex flex-col gap-1.5"
          >
            {digest.topStories.map((story, idx) => (
              <div
                key={story.id}
                data-testid="digest-top-story-row"
                className="border-l-4 border-primary pl-3 py-2 rounded-r-md hover:bg-accent/5 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-medium">
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3
                      className="text-sm font-medium mb-1 text-foreground leading-snug"
                      style={{
                        overflowWrap: "anywhere",
                        wordBreak: "break-word",
                      }}
                    >
                      {story.title}
                    </h3>
                    <p
                      className="text-xs text-muted-foreground mb-2 line-clamp-2"
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
          <CardHeader className="py-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              <CardTitle className="text-base">Trending Now</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Most discussed topics today
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-4">
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
          <CardHeader className="py-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              <CardTitle className="text-base">Coverage by Topic</CardTitle>
            </div>
            <CardDescription className="text-xs">
              News distribution across categories
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-4">
            <div
              data-testid="digest-source-distribution"
              className="space-y-2"
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
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-foreground truncate">
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
        <CardContent className="py-5">
          <div className="text-center">
            <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center mx-auto mb-2">
              <Mail className="w-5 h-5 text-primary" />
            </div>
            <h3 className="text-sm font-medium mb-1">
              Get Your Daily Digest via Email
            </h3>
            <p className="text-xs text-muted-foreground mb-3">
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
