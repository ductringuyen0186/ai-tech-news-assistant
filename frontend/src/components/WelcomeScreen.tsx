/**
 * WelcomeScreen — Polish iter 5.
 *
 * First-load landing pane shown to new visitors. Explains what TechPulse
 * AI does, highlights the marquee features, and offers two prominent
 * call-to-action buttons:
 *
 *   - "Try Research Mode" (primary) — switches to the Research tab and
 *     dismisses the welcome screen. This is the hero CTA because the
 *     agentic research loop is the most differentiating feature of the
 *     product.
 *   - "Browse News Feed" (secondary) — switches to the News Feed tab and
 *     dismisses the welcome screen.
 *
 * Dismissal persists in ``localStorage`` under
 * ``techpulse-welcome-seen``. Once set, the welcome screen never appears
 * again unless the user manually clears the key. (Future iter: a
 * "What's this app?" footer link could re-trigger the screen.)
 *
 * Test hooks:
 *   - data-testid="welcome-screen"
 *   - data-testid="welcome-cta-research"
 *   - data-testid="welcome-cta-feed"
 *   - data-testid="welcome-dismiss"  (small "Skip intro" link)
 */
import { Button } from "./ui/button";
import {
  Sparkles,
  Newspaper,
  Lightbulb,
  Network,
  Mail,
  ArrowRight,
  Search,
} from "lucide-react";

export const WELCOME_SEEN_KEY = "techpulse-welcome-seen";

/**
 * Read the welcome-seen flag from localStorage. Returns ``true`` if the
 * user has dismissed the welcome screen before, ``false`` otherwise.
 * Defaults to ``false`` on any error so the welcome screen still works
 * in privacy mode.
 */
export function hasSeenWelcome(): boolean {
  try {
    return localStorage.getItem(WELCOME_SEEN_KEY) === "1";
  } catch {
    return false;
  }
}

export function markWelcomeSeen(): void {
  try {
    localStorage.setItem(WELCOME_SEEN_KEY, "1");
  } catch {
    // ignore quota / privacy errors — worst case the user sees the screen again
  }
}

interface WelcomeScreenProps {
  /** Called when the user picks "Try Research Mode". */
  onTryResearch: () => void;
  /** Called when the user picks "Browse News Feed". */
  onBrowseFeed: () => void;
  /** Called when the user dismisses via the skip link. */
  onSkip: () => void;
}

interface FeatureHighlight {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}

const FEATURES: FeatureHighlight[] = [
  {
    icon: Lightbulb,
    title: "Agentic Research",
    description:
      "Ask a question; watch the agent decompose it, dispatch subagents in parallel, and synthesize a cited answer in real time.",
  },
  {
    icon: Newspaper,
    title: "Curated News Feed",
    description:
      "Hand-picked tech headlines from TechCrunch, The Verge, Wired, and Ars Technica — with AI-generated summaries.",
  },
  {
    icon: Network,
    title: "Knowledge Graph",
    description:
      "Explore the entities behind the news: companies, products, people, and how they connect across stories.",
  },
  {
    icon: Mail,
    title: "Daily Digest",
    description:
      "A morning briefing with the day's top stories, trending topics, and a one-paragraph AI summary.",
  },
];

export function WelcomeScreen({
  onTryResearch,
  onBrowseFeed,
  onSkip,
}: WelcomeScreenProps) {
  return (
    <div
      data-testid="welcome-screen"
      className="min-h-[70vh] flex flex-col items-center justify-center py-12 px-4"
    >
      <div className="max-w-3xl w-full space-y-10">
        {/* Hero — product mark, tagline, brief description. */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary shadow-lg">
            <Newspaper className="w-9 h-9 text-primary-foreground" />
          </div>
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight text-foreground">
              Welcome to TechPulse AI
            </h1>
            <p className="text-base text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Your AI-powered tech-news research assistant. Aggregate the day's
              stories, ask deep questions to an agentic research mode, and
              explore the entities behind the headlines.
            </p>
          </div>
        </div>

        {/* Primary CTA — Try Research Mode. The most catchy feature is the
            agentic research loop; we lead with that. */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button
            data-testid="welcome-cta-research"
            size="lg"
            onClick={onTryResearch}
            className="w-full sm:w-auto gap-2 h-11 px-6 text-sm font-medium"
          >
            <Sparkles className="w-4 h-4" />
            Try Research Mode
            <ArrowRight className="w-4 h-4" />
          </Button>
          <Button
            data-testid="welcome-cta-feed"
            variant="outline"
            size="lg"
            onClick={onBrowseFeed}
            className="w-full sm:w-auto gap-2 h-11 px-6 text-sm font-medium"
          >
            <Newspaper className="w-4 h-4" />
            Browse News Feed
          </Button>
        </div>

        {/* Quick keyboard hint — press ⌘K to search. */}
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <Search className="w-3 h-3" />
          <span>Tip: press</span>
          <kbd className="text-[10px] px-1.5 py-[1px] border border-border rounded bg-muted font-mono">
            ⌘K
          </kbd>
          <span>anytime to jump anywhere.</span>
        </div>

        {/* Feature grid — 2×2 on desktop, 1×4 on mobile. Each cell is a
            short blurb on one of the four marquee features. */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="p-5 rounded-xl border border-border bg-card hover:border-primary/30 transition-colors space-y-2"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
                    <Icon className="w-4 h-4 text-primary" />
                  </div>
                  <h3 className="text-sm font-semibold text-foreground">
                    {feature.title}
                  </h3>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>

        {/* Skip link — quiet text button at the bottom for users who
            don't want the intro. */}
        <div className="text-center pt-2">
          <button
            data-testid="welcome-dismiss"
            type="button"
            onClick={onSkip}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Skip intro
          </button>
        </div>
      </div>
    </div>
  );
}
