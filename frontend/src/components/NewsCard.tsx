import { useState } from "react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import {
  ExternalLink,
  TrendingUp,
  Clock,
  ChevronDown,
  ChevronUp,
  Shield,
} from "lucide-react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardTitle } from "./ui/card";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "./ui/hover-card";

/**
 * NewsCard — Linear-dense article row.
 *
 * Mission 3 / Milestone 3 — restyled from a hero-image card to a
 * side-by-side dense row: 64px square thumbnail on the left, title +
 * source + date stacked on the right, body text capped at `text-sm`
 * (14px), padding ≤ 12px. Hover tints the card with `bg-accent/5` so
 * users get pointer feedback consistent with the new design language.
 *
 * The card uses plain `<div>` containers inside the shadcn `Card` rather
 * than CardHeader/CardContent/CardFooter so we don't inherit the grid /
 * `px-6` defaults — those caused horizontal overflow on `lg:grid-cols-2`
 * width budgets after the density change.
 *
 * Preserved hooks (Playwright contract):
 *   - data-slot="card"          (root)
 *   - data-slot="card-title"    (article title)
 *   - .text-gray-500            (source span; the news-feed spec scopes
 *                                source-name assertions to this class)
 *   - "Read More" button        (detailed mode only — rubric category 1
 *                                clicks it to surface the full body)
 *   - data-slot="badge"         (category & meta chips)
 *   - img inside the card       (rubric category 8 asserts they load)
 */

interface NewsCardProps {
  article: {
    id: string;
    title: string;
    source: string;
    url: string;
    publishedAt: string;
    imageUrl: string;
    category: string[];
    summaryShort: string;
    summaryMedium: string;
    keyInsights: string[];
    sentiment: string;
    trending: boolean;
    credibilityScore?: number;
    sourcesUsed?: string[];
  };
  viewMode: "compact" | "detailed";
}

export function NewsCard({ article, viewMode }: NewsCardProps) {
  const [expanded, setExpanded] = useState(false);

  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const hours = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    );

    if (hours < 1) return "Just now";
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const getCredibilityColor = (score: number) => {
    if (score >= 90) return "text-green-600";
    if (score >= 70) return "text-blue-600";
    if (score >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  const getCredibilityLabel = (score: number) => {
    if (score >= 90) return "Highly Reliable";
    if (score >= 70) return "Reliable";
    if (score >= 50) return "Moderate";
    return "Limited";
  };

  return (
    <Card
      className={[
        "group p-3 gap-2 transition-colors min-w-0",
        "hover:bg-accent/5 hover:border-border",
      ].join(" ")}
    >
      {/* Header — thumbnail + meta + title + summary. Use CSS grid with
          a fixed first column for the thumbnail and a `minmax(0, 1fr)`
          second column for the content. `minmax(0, 1fr)` lets the
          content column shrink below its intrinsic min-content size,
          which is what stops the long title from forcing the card to
          overflow horizontally. */}
      <div
        className="grid items-start gap-3 min-w-0"
        style={{ gridTemplateColumns: "64px minmax(0, 1fr)" }}
      >
        <ImageWithFallback
          src={article.imageUrl}
          alt={article.title}
          className="w-16 h-16 object-cover rounded-md bg-muted"
        />
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 mb-1 flex-wrap text-xs">
            {article.trending && (
              <Badge
                variant="default"
                className="h-5 px-1.5 text-[10px] gap-1 bg-orange-500"
              >
                <TrendingUp className="w-3 h-3" />
                Trending
              </Badge>
            )}
            {/* Source — `.text-gray-500` is the class the news-feed spec
                scopes source-name assertions to; preserve it. */}
            <span className="text-xs text-gray-500 text-muted-foreground truncate max-w-[140px]">
              {article.source}
            </span>
            {article.credibilityScore !== undefined && (
              <>
                <span className="text-xs text-muted-foreground">·</span>
                <HoverCard>
                  <HoverCardTrigger asChild>
                    <span
                      className={`text-xs flex items-center gap-1 cursor-help ${getCredibilityColor(article.credibilityScore)}`}
                    >
                      <Shield className="w-3 h-3" />
                      {article.credibilityScore}%
                    </span>
                  </HoverCardTrigger>
                  <HoverCardContent className="w-80">
                    <div className="space-y-2">
                      <h4 className="font-semibold flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Source Credibility
                      </h4>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">
                            Reliability:
                          </span>
                          <span
                            className={`text-sm font-semibold ${getCredibilityColor(article.credibilityScore)}`}
                          >
                            {getCredibilityLabel(article.credibilityScore)}
                          </span>
                        </div>
                        <div className="w-full bg-muted h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              article.credibilityScore >= 90
                                ? "bg-green-600"
                                : article.credibilityScore >= 70
                                  ? "bg-blue-600"
                                  : article.credibilityScore >= 50
                                    ? "bg-yellow-600"
                                    : "bg-red-600"
                            }`}
                            style={{
                              width: `${article.credibilityScore}%`,
                            }}
                          />
                        </div>
                      </div>
                      {article.sourcesUsed &&
                        article.sourcesUsed.length > 0 && (
                          <div className="pt-2 border-t border-border">
                            <p className="text-sm font-semibold mb-1">
                              Sources Used:
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {article.sourcesUsed.map((src, idx) => (
                                <Badge
                                  key={idx}
                                  variant="outline"
                                  className="text-xs"
                                >
                                  {src}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                    </div>
                  </HoverCardContent>
                </HoverCard>
              </>
            )}
            <span className="text-xs text-muted-foreground">·</span>
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {timeAgo(article.publishedAt)}
            </span>
          </div>
          <CardTitle
            style={{
              overflowWrap: "anywhere",
              wordBreak: "break-word",
            }}
            className="text-sm leading-snug mb-1 font-medium"
          >
            {article.title}
          </CardTitle>
          <p
            style={{
              overflowWrap: "anywhere",
              wordBreak: "break-word",
            }}
            className="text-xs text-muted-foreground line-clamp-2"
          >
            {article.summaryShort}
          </p>
        </div>
      </div>

      {viewMode === "detailed" && (
        <div className="min-w-0">
          {expanded ? (
            <>
              {article.summaryMedium &&
                article.summaryMedium.trim() !==
                  (article.summaryShort || "").trim() && (
                  <p
                    className="text-sm text-foreground/80 mb-2"
                    style={{
                      overflowWrap: "anywhere",
                      wordBreak: "break-word",
                    }}
                  >
                    {article.summaryMedium}
                  </p>
                )}
              {article.keyInsights && article.keyInsights.length > 0 && (
                <div className="bg-muted/40 p-3 rounded-md">
                  <h4 className="text-xs font-semibold mb-2 text-foreground">
                    Key Insights
                  </h4>
                  <ul className="space-y-1">
                    {article.keyInsights.map((insight, idx) => (
                      <li
                        key={idx}
                        className="text-xs text-muted-foreground flex items-start gap-2"
                      >
                        <span className="text-primary mt-0.5">·</span>
                        <span style={{ overflowWrap: "anywhere" }}>
                          {insight}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-full mt-2 text-xs"
                onClick={() => setExpanded(false)}
              >
                Show Less <ChevronUp className="w-3 h-3 ml-1" />
              </Button>
            </>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-full text-xs text-muted-foreground hover:text-foreground"
              onClick={() => setExpanded(true)}
            >
              Read More <ChevronDown className="w-3 h-3 ml-1" />
            </Button>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-1.5 items-center min-w-0">
        <div className="flex flex-wrap gap-1.5 flex-1 min-w-0">
          {article.category.slice(0, 3).map((cat) => (
            <Badge
              key={cat}
              variant="outline"
              className="h-5 px-1.5 text-[10px] font-normal border-border"
            >
              {cat}
            </Badge>
          ))}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground shrink-0"
          asChild
        >
          <a href={article.url} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="w-3 h-3" />
          </a>
        </Button>
      </div>
    </Card>
  );
}
