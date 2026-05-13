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
 * Dismissal persists in `localStorage` under `techpulse-welcome-seen`.
 * Once set, the welcome screen never appears again unless the user
 * manually clears the key.
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
    // ignore quota / privacy errors
  }
}

interface WelcomeScreenProps {
  onTryResearch: () => void;
  onBrowseFeed: () => void;
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
      "Hand-picked tech headlines from TechCrunch, The Verge, Wired, and Ars Technica with AI-generated summaries.",
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
      className="min-h-[70vh] flex flex-col items-center justify-center py-16 px-4"
    >
      <div className="max-w-3xl w-full">
        {/* Hero block — logo + headline + tagline */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary shadow-lg mb-6">
            <Newspaper className="w-9 h-9 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground mb-3">
            Welcome to TechPulse AI
          </h1>
          <p className="text-base text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Your AI-powered tech-news research assistant. Aggregate the day's
            stories, ask deep questions to an agentic research mode, and
            explore the entities behind the headlines.
          </p>
        </div>

        {/* Primary CTAs — Try Research is the hero action. Both buttons
            are inline (md: is in the prebuilt bundle; sm: is not).
            Auto width with px-7 keeps them as proper buttons. */}
        <div className="flex md:flex-row flex-col items-center justify-center gap-4 mb-6">
          <Button
            data-testid="welcome-cta-research"
            size="lg"
            onClick={onTryResearch}
            className="gap-2 h-11 px-7 text-sm font-medium shadow-sm"
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
            className="gap-2 h-11 px-7 text-sm font-medium"
          >
            <Newspaper className="w-4 h-4" />
            Browse News Feed
          </Button>
        </div>

        {/* Keyboard tip — sits close to the CTAs (mb-6 above) as a
            footnote, then mb-14 pushes the feature grid clearly into
            its own section. */}
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground mb-14">
          <Search className="w-3 h-3" />
          <span>Tip: press</span>
          <kbd className="text-[10px] px-1.5 py-[1px] border border-border rounded bg-muted font-mono">
            ⌘K
          </kbd>
          <span>anytime to jump anywhere.</span>
        </div>

        {/* Feature grid — 2x2 at md+, single column below. p-6 padding
            and bumped typography (text-base title, text-sm body) so
            cards read as substantial info blocks. */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-12">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="p-6 rounded-xl border border-border bg-card hover:border-primary/30 transition-colors"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
                    <Icon className="w-4 h-4 text-primary" />
                  </div>
                  <h3 className="text-base font-semibold text-foreground">
                    {feature.title}
                  </h3>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>

        {/* Skip link — quiet text button, generous padding so it
            doesn't crowd the feature grid above. */}
        <div className="text-center">
          <button
            data-testid="welcome-dismiss"
            type="button"
            onClick={onSkip}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors px-3 py-2"
          >
            Skip intro
          </button>
        </div>
      </div>
    </div>
  );
}
