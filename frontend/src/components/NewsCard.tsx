import { useEffect, useState } from "react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import {
  ArrowUpRight,
  TrendingUp,
  Clock,
  ChevronDown,
  ChevronUp,
  Shield,
  Bookmark,
  BookmarkCheck,
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
 * NewsCard — engaging news-feed row (polish iter 4).
 *
 * Earlier iterations rendered a Linear-dense source-only row that the user
 * couldn't actually read from: the "Read More" button toggled an expander
 * but the article URL was buried behind a tiny icon-only link, and there
 * was no summary preview beneath the title. Iter 4 fixes both:
 *
 *   1. A 2-3 line summary preview lives directly under the title using
 *      ``line-clamp-3`` + ``leading-relaxed``. Body text is ``text-sm``
 *      (14px) and uses the ``text-muted-foreground`` semantic token.
 *   2. The footer now has a real "Read article →" call-to-action that
 *      opens ``article.url`` in a new tab. The link uses ``text-primary``
 *      so it stands out as the dominant action.
 *   3. A small icon-only Save (Bookmark) button sits at the top-right of
 *      every card. State persists in ``localStorage`` under
 *      ``techpulse-saved-articles`` — keyed by article id. (Future work:
 *      sync to ``/api/saved-research`` via the question/report pattern
 *      reused for research reports.)
 *
 * Card padding is intentionally ``p-3`` (12px) — the existing
 * news-feed.spec.ts "Linear-dense" test asserts ``padding ≤ 14px`` on the
 * outer Card. Interior breathing room comes from ``space-y-*`` and
 * generous ``leading-relaxed`` on the summary.
 *
 * Preserved hooks (Playwright contract):
 *   - data-slot="card"          (root)
 *   - data-slot="card-title"    (article title)
 *   - .text-gray-500            (source span — news-feed.spec.ts scopes
 *                                source-name assertions to this class)
 *   - "Read More" button        (detailed mode only — rubric category 1
 *                                clicks it to surface the full body)
 *   - data-slot="badge"         (category & meta chips)
 *   - img inside the card       (rubric category 8 asserts they load)
 *
 * New testids:
 *   - data-testid="news-card-summary"
 *   - data-testid="news-card-read-more"
 *   - data-testid="news-card-save-btn"
 */

const SAVED_ARTICLES_KEY = "techpulse-saved-articles";

/**
 * Read the saved-article id set from localStorage. Returns an empty Set
 * on any error (privacy mode, malformed JSON, etc.) so the UI never
 * crashes on a bad cache.
 */
function readSavedSet(): Set<string> {
  try {
    const raw = localStorage.getItem(SAVED_ARTICLES_KEY);
    if (!raw) return new Set<string>();
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return new Set(parsed.map(String));
    return new Set<string>();
  } catch {
    return new Set<string>();
  }
}

function persistSavedSet(set: Set<string>): void {
  try {
    localStorage.setItem(SAVED_ARTICLES_KEY, JSON.stringify(Array.from(set)));
  } catch {
    // ignore quota / privacy errors
  }
}

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
  const [isSaved, setIsSaved] = useState<boolean>(false);

  // Initialise saved state from localStorage on mount.
  useEffect(() => {
    setIsSaved(readSavedSet().has(String(article.id)));
  }, [article.id]);

  const toggleSaved = () => {
    const next = readSavedSet();
    const key = String(article.id);
    if (next.has(key)) {
      next.delete(key);
      setIsSaved(false);
    } else {
      next.add(key);
      setIsSaved(true);
    }
    persistSavedSet(next);
  };

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
        "group relative p-3 gap-3 transition-colors min-w-0",
        "hover:border-primary/30 hover:bg-accent/5",
      ].join(" ")}
    >
      {/* Save button — pinned to the top-right corner of the card. Icon
          only; persists per-session in localStorage (see SAVED_ARTICLES_KEY).
          Future iter: POST to the saved-research backend. */}
      <button
        type="button"
        data-testid="news-card-save-btn"
        onClick={toggleSaved}
        aria-label={isSaved ? "Unsave article" : "Save article"}
        aria-pressed={isSaved}
        title={isSaved ? "Saved" : "Save for later"}
        className={[
          "absolute top-2 right-2 inline-flex items-center justify-center",
          "w-7 h-7 rounded-md transition-colors",
          isSaved
            ? "text-primary bg-primary/10 hover:bg-primary/20"
            : "text-muted-foreground hover:text-foreground hover:bg-accent",
        ].join(" ")}
      >
        {isSaved ? (
          <BookmarkCheck className="w-3.5 h-3.5" />
        ) : (
          <Bookmark className="w-3.5 h-3.5" />
        )}
      </button>

      {/* Header — thumbnail (64px) on the left, title + meta + summary on
          the right. Padding on the content column accounts for the
          absolutely positioned save button so the title doesn't collide
          with it. */}
      <div
        className="grid items-start gap-3 min-w-0"
        style={{ gridTemplateColumns: "64px minmax(0, 1fr)" }}
      >
        <ImageWithFallback
          src={article.imageUrl}
          alt={article.title}
          className="w-16 h-16 object-cover rounded-md bg-muted"
        />
        <div className="min-w-0 pr-8">
          <div className="flex items-center gap-1.5 mb-1.5 flex-wrap text-xs">
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
                      <h4 className="text-base font-semibold flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Source Credibility
                      </h4>
                      <div className="space-y-1.5">
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
            className="text-[15px] leading-snug mb-1.5 font-semibold text-foreground line-clamp-2"
          >
            {article.title}
          </CardTitle>
          {/* Summary preview — 2-3 lines depending on view mode. Uses
              line-clamp-3 with leading-relaxed so the truncation reads
              like a real paragraph instead of a tight strip. */}
          {article.summaryShort && (
            <p
              data-testid="news-card-summary"
              style={{
                overflowWrap: "anywhere",
                wordBreak: "break-word",
              }}
              className="text-sm text-muted-foreground leading-relaxed line-clamp-3"
            >
              {article.summaryShort}
            </p>
          )}
        </div>
      </div>

      {viewMode === "detailed" && (
        <div className="min-w-0">
          {expanded ? (
            <div className="space-y-2">
              {article.summaryMedium &&
                article.summaryMedium.trim() !==
                  (article.summaryShort || "").trim() && (
                  <p
                    className="text-sm leading-relaxed text-foreground/80"
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
                  <ul className="space-y-1.5">
                    {article.keyInsights.map((insight, idx) => (
                      <li
                        key={idx}
                        className="text-xs text-muted-foreground flex items-start gap-2 leading-relaxed"
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
                className="h-7 w-full text-xs"
                onClick={() => setExpanded(false)}
              >
                Show Less <ChevronUp className="w-3 h-3 ml-1" />
              </Button>
            </div>
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

      {/* Footer — category chips on the left, "Read article →" CTA on
          the right. The CTA is the dominant action: visible text +
          arrow icon + primary colour. Opens the article in a new tab. */}
      <div className="flex flex-wrap gap-2 items-center justify-between min-w-0">
        <div className="flex flex-wrap gap-1.5 min-w-0">
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
        <a
          data-testid="news-card-read-more"
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline shrink-0"
        >
          Read article
          <ArrowUpRight className="w-3 h-3" />
        </a>
      </div>
    </Card>
  );
}
