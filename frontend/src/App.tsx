import { useState, useEffect } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Tabs, TabsContent } from "./components/ui/tabs";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { NewsCard } from "./components/NewsCard";
import { Settings } from "./components/Settings";
import { SearchBar } from "./components/SearchBar";
import { DigestView } from "./components/DigestView";
import { TrendingRail } from "./components/TrendingRail";
import { ChatInterface } from "./components/ChatInterface";
import { ResearchMode } from "./components/ResearchMode";
import { KnowledgeGraph } from "./components/KnowledgeGraph";
import { SavedResearchList } from "./components/SavedResearchList";
import { ThemeProvider } from "./components/ThemeProvider";
import { CommandPaletteProvider } from "./components/CommandPalette";
import { Sidebar } from "./components/Sidebar";
import {
  Newspaper,
  TrendingUp,
  Loader2,
  Grid,
  List,
} from "lucide-react";
import { API_ENDPOINTS, apiFetch } from "./config/api";

/**
 * AppShell — the actual UI. Lives inside <ThemeProvider> via the default
 * <App /> export below. The shell renders the sidebar + main content
 * inside a controlled Radix <Tabs> root so we keep the existing
 * `role="tab"` / `role="tablist"` / `role="tabpanel"` accessibility tree
 * that the 35 Playwright tests rely on.
 */
function AppShell() {
  const [articles, setArticles] = useState<any[]>([]);
  const [filteredArticles, setFilteredArticles] = useState<any[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([
    "AI",
    "Machine Learning",
  ]);
  const [searchQuery, setSearchQuery] = useState("");
  const [digest, setDigest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"compact" | "detailed">("detailed");
  const [showTrendingOnly, setShowTrendingOnly] = useState(false);
  const [isSavingPreferences, setIsSavingPreferences] = useState(false);
  const [savedCategories, setSavedCategories] = useState<string[]>([]);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [totalArticleCount, setTotalArticleCount] = useState<number>(0);
  // Active tab — controlled at App level so Sidebar (owns the TabsList) and
  // CommandPalette can both mutate it. Radix Tabs becomes controlled via
  // value/onValueChange.
  const [activeTab, setActiveTab] = useState<string>("feed");
  const reduceMotion = useReducedMotion();
  // Page-tab fade-in: each TabsContent's children are wrapped in a
  // motion.div that fades in from opacity 0 → 1 on mount. Radix unmounts
  // the inactive tab's children, so switching tabs is a natural unmount
  // + remount — and the new motion.div's `initial → animate` is the
  // fade. Reduced-motion resolves to instant.
  const panelInitial = reduceMotion ? { opacity: 1 } : { opacity: 0 };
  const panelAnimate = { opacity: 1 };
  const panelTransition = { duration: reduceMotion ? 0 : 0.2, ease: "easeOut" as const };

  // -------------------------------------------------------------------------
  // Data fetchers (unchanged from M2 — behavior is out of scope for M3.M1).
  // -------------------------------------------------------------------------
  const fetchArticles = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append("page", "1");
      params.append("page_size", "50");

      if (selectedCategories.length > 0) {
        for (const cat of selectedCategories) {
          if (cat && cat.trim()) {
            params.append("category", cat);
          }
        }
      }
      if (searchQuery) {
        params.append("author", searchQuery);
      }

      const data = await apiFetch<any>(`${API_ENDPOINTS.news}?${params}`);
      console.log("API Response:", data);

      const articles = data.data || data.items || [];
      const buildSummaries = (a: any): { summaryShort: string; summaryMedium: string } => {
        const body: string = (a.summary || a.content || "").toString().trim();
        if (!body) {
          return { summaryShort: "", summaryMedium: "" };
        }
        const short =
          body.length > 200 ? body.slice(0, 200).trimEnd() + "..." : body;
        const medium =
          body.length > 600 ? body.slice(0, 600).trimEnd() + "..." : body;
        return { summaryShort: short, summaryMedium: medium };
      };
      const mappedArticles =
        articles.map((article: any) => {
          const { summaryShort, summaryMedium } = buildSummaries(article);
          return {
            id: article.id,
            title: article.title,
            content: article.content,
            summaryShort,
            summaryMedium,
            url: article.url,
            publishedAt: article.published_at,
            imageUrl:
              article.image_url ||
              "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'><rect width='400' height='300' fill='%23e5e7eb'/><text x='50%25' y='50%25' font-family='sans-serif' font-size='24' fill='%236b7280' text-anchor='middle' dominant-baseline='middle'>Tech News</text></svg>",
            category: article.categories || [],
            source: article.source,
            credibilityScore: 85,
            trending: false,
            sentiment: "neutral",
            keyInsights: [],
            sourcesUsed: [article.source],
          };
        }) || [];

      setArticles(mappedArticles);
      setFilteredArticles(mappedArticles);
    } catch (error) {
      console.error("Error fetching articles:", error);
      toast.error("Failed to fetch articles. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const envelope = await apiFetch<any>(API_ENDPOINTS.newsStats);
      const data = envelope?.data ?? envelope;
      const recent = Number(data?.recent_articles ?? 0);
      const total = Number(data?.total_articles ?? 0);
      setTotalArticleCount(recent > 0 ? recent : total);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const fetchDigest = async () => {
    try {
      const data = await apiFetch<any>(API_ENDPOINTS.digest);
      setDigest(data);
    } catch (error) {
      console.error("Error fetching digest:", error);
      toast.error("Failed to fetch digest. Please try again.");
    }
  };

  const savePreferences = async () => {
    setIsSavingPreferences(true);
    try {
      const body = {
        categories: selectedCategories,
        view_mode: viewMode,
        show_trending_only: showTrendingOnly,
      };

      const envelope = await apiFetch<any>(API_ENDPOINTS.settings, {
        method: "PUT",
        body: JSON.stringify(body),
      });
      const saved = envelope?.data ?? envelope;

      const persistedCategories: string[] = Array.isArray(saved?.categories)
        ? saved.categories
        : selectedCategories;
      setSavedCategories([...persistedCategories]);
      setHasUnsavedChanges(false);

      try {
        localStorage.setItem(
          "techpulse_categories",
          JSON.stringify(persistedCategories)
        );
      } catch {
        // Best-effort cache; ignore quota / privacy-mode failures.
      }

      toast.success("Preferences saved successfully!", {
        description: `Your feed will now show ${persistedCategories.length} selected topic${persistedCategories.length !== 1 ? "s" : ""}.`,
        duration: 3000,
      });

      await fetchArticles();
    } catch (error) {
      console.error("Error saving preferences:", error);
      toast.error("Failed to save preferences", {
        description: "Please try again later.",
        duration: 3000,
      });
    } finally {
      setIsSavingPreferences(false);
    }
  };

  const handleAskQuestion = async (question: string) => {
    try {
      const envelope = await apiFetch<any>("/api/rag/query", {
        method: "POST",
        body: JSON.stringify({ question, top_k: 5, min_score: 0.3 }),
      });
      const data = envelope?.data ?? envelope;
      const rawSources = (data.sources || []).map((s: any) => ({
        id: String(s.id ?? ""),
        url: typeof s.url === "string" ? s.url : "",
        title: s.title ?? "Untitled",
        summaryShort: s.source ?? "",
      }));
      const seenUrls = new Set<string>();
      const seenIds = new Set<string>();
      const seenTitles = new Set<string>();
      const sources = rawSources.filter((s: any) => {
        const urlKey = (s.url || "").trim().toLowerCase();
        const idKey = (s.id || "").trim();
        const titleKey = (s.title || "").trim().toLowerCase().replace(/\s+/g, " ");
        if (urlKey && seenUrls.has(urlKey)) return false;
        if (idKey && seenIds.has(idKey)) return false;
        if (titleKey && seenTitles.has(titleKey)) return false;
        if (urlKey) seenUrls.add(urlKey);
        if (idKey) seenIds.add(idKey);
        if (titleKey) seenTitles.add(titleKey);
        return true;
      });
      return {
        answer: data.answer ?? "(no answer returned)",
        relevantArticles: sources,
        success: true,
      };
    } catch (error) {
      console.error("Error processing question:", error);
      return {
        answer: "Sorry - the chat backend is unreachable right now.",
        success: false,
      };
    }
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const envelope = await apiFetch<any>(API_ENDPOINTS.settings);
        const data = envelope?.data ?? envelope;
        if (data && typeof data === "object") {
          if (Array.isArray(data.categories)) {
            setSelectedCategories(data.categories);
            setSavedCategories(data.categories);
            try {
              localStorage.setItem(
                "techpulse_categories",
                JSON.stringify(data.categories)
              );
            } catch {
              // Ignore cache write failures.
            }
          }
          if (data.view_mode === "compact" || data.view_mode === "detailed") {
            setViewMode(data.view_mode);
          }
          if (typeof data.show_trending_only === "boolean") {
            setShowTrendingOnly(data.show_trending_only);
          }
        }
      } catch (backendError) {
        console.warn(
          "Backend settings unreachable; falling back to localStorage cache",
          backendError
        );
        try {
          const saved = localStorage.getItem("techpulse_categories");
          if (saved) {
            const cats = JSON.parse(saved);
            if (Array.isArray(cats)) {
              setSelectedCategories(cats);
              setSavedCategories(cats);
            }
          }
        } catch (cacheError) {
          console.error("Error loading preferences from cache:", cacheError);
        }
      }

      fetchArticles();
      fetchDigest();
      fetchStats();
    };

    loadData();
  }, []);

  useEffect(() => {
    const categoriesChanged =
      JSON.stringify(selectedCategories.sort()) !==
      JSON.stringify(savedCategories.sort());
    setHasUnsavedChanges(categoriesChanged);
  }, [selectedCategories, savedCategories]);

  useEffect(() => {
    fetchArticles();
  }, [selectedCategories, searchQuery, showTrendingOnly]);

  // -------------------------------------------------------------------------
  // Render — sidebar + main pane inside a controlled Radix Tabs root.
  // -------------------------------------------------------------------------
  return (
    <Tabs
      value={activeTab}
      onValueChange={setActiveTab}
      className="min-h-screen flex flex-row bg-background text-foreground"
    >
      <CommandPaletteProvider activeTab={activeTab} onSelectTab={setActiveTab}>
        <Sidebar
          activeTab={activeTab}
          badges={hasUnsavedChanges ? { preferences: "unsaved" } : undefined}
        />

        <main
          data-slot="main-content"
          className="flex-1 min-w-0 flex flex-col overflow-x-hidden"
        >
          {/* Top bar keeps the TechPulse heading visible — the existing
              Playwright suite asserts `getByRole("heading", { name: /TechPulse AI/i })`
              on every test. Brand mark itself lives in the sidebar. */}
          <header className="border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-10">
            <div className="px-6 py-3 flex items-center justify-between">
              <div className="flex items-baseline gap-2">
                <h1 className="text-lg font-semibold tracking-tight">
                  TechPulse AI
                </h1>
                <span className="text-xs text-muted-foreground">
                  AI-powered tech news aggregation
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className="gap-1 text-xs border-border bg-muted/40 text-foreground"
                >
                  <span>🔥</span>
                  {articles.filter((a) => a.trending).length} Trending
                </Badge>
                <Badge
                  variant="outline"
                  className="gap-1 text-xs border-border bg-muted/40 text-foreground"
                >
                  {totalArticleCount || articles.length} Articles Today
                </Badge>
              </div>
            </div>
          </header>

          <div className="px-6 py-5 flex-1">
            {/* Page-tab cross-fade — every TabsContent's children are
                wrapped in a motion.div that fades in on mount. Radix
                unmounts the inactive tab's children, so switching tabs
                triggers a fresh mount + fade-in for the new panel. No
                AnimatePresence required because there's nothing to
                animate out (Radix removes the old children
                instantly). Reduced-motion resolves to instant. */}
            {/* News Feed Tab */}
            <TabsContent value="feed" className="space-y-4 mt-0">
              <motion.div
                initial={panelInitial}
                animate={panelAnimate}
                transition={panelTransition}
              >
              <div className="flex flex-col md:flex-row gap-3 items-start md:items-center justify-between">
                <div className="flex-1 w-full md:max-w-md">
                  <SearchBar onSearch={setSearchQuery} />
                </div>
                <div className="flex gap-2 items-center">
                  <Button
                    variant={showTrendingOnly ? "default" : "outline"}
                    size="sm"
                    onClick={() => setShowTrendingOnly(!showTrendingOnly)}
                    className="h-8 gap-1.5 text-xs"
                  >
                    <TrendingUp className="w-3.5 h-3.5" />
                    Trending Only
                  </Button>
                  <div className="flex gap-0.5 border border-border rounded-md p-0.5 bg-card">
                    <Button
                      variant={viewMode === "detailed" ? "default" : "ghost"}
                      size="sm"
                      onClick={() => setViewMode("detailed")}
                      className="h-7 px-2"
                    >
                      <Grid className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant={viewMode === "compact" ? "default" : "ghost"}
                      size="sm"
                      onClick={() => setViewMode("compact")}
                      className="h-7 px-2"
                    >
                      <List className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Mission 3 / M3.M3 — Trending Now rail. Click a chip to
                  toggle the matching category as a filter. The rail is
                  presentational and self-hides when there are no
                  categories yet. */}
              <TrendingRail
                selectedCategories={selectedCategories}
                onSelectCategory={(cat) => {
                  setSelectedCategories((prev) =>
                    prev.includes(cat)
                      ? prev.filter((c) => c !== cat)
                      : [...prev, cat]
                  );
                }}
              />

              {selectedCategories.length > 0 && (
                <div
                  data-testid="news-feed-active-filters"
                  className="flex flex-wrap gap-1.5 items-center bg-card p-2 rounded-md border border-border"
                >
                  <span className="text-xs text-muted-foreground pr-1">
                    Filtered by:
                  </span>
                  {selectedCategories.map((cat) => (
                    <Badge
                      key={cat}
                      variant="secondary"
                      className="h-5 px-1.5 text-[10px] font-normal"
                    >
                      {cat}
                    </Badge>
                  ))}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedCategories([])}
                    className="ml-auto h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
                  >
                    Clear Filters
                  </Button>
                </div>
              )}

              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : filteredArticles.length === 0 ? (
                <div className="text-center py-12 bg-card rounded-xl border border-border">
                  <Newspaper className="w-12 h-12 text-primary mx-auto mb-3" />
                  <h3 className="text-lg mb-2">No articles found</h3>
                  <p className="text-muted-foreground mb-4">
                    Try adjusting your filters or search query
                  </p>
                  <Button
                    onClick={() => {
                      setSearchQuery("");
                      setShowTrendingOnly(false);
                      setSelectedCategories([]);
                    }}
                  >
                    Reset Filters
                  </Button>
                </div>
              ) : (
                <div
                  data-testid="news-feed-list"
                  className={`grid gap-2 ${
                    viewMode === "detailed"
                      ? "grid-cols-1 lg:grid-cols-2"
                      : "grid-cols-1"
                  }`}
                >
                  {filteredArticles.map((article) => (
                    <NewsCard
                      key={article.id}
                      article={article}
                      viewMode={viewMode}
                    />
                  ))}
                </div>
              )}
              </motion.div>
            </TabsContent>

            {/* Research Mode Tab — unchanged in M1; M2 will polish content. */}
            <TabsContent value="research" className="mt-0">
              <motion.div
                initial={panelInitial}
                animate={panelAnimate}
                transition={panelTransition}
              >
                <ResearchMode />
              </motion.div>
            </TabsContent>

            {/* Knowledge Graph Tab */}
            <TabsContent value="knowledge" className="mt-0">
              <motion.div
                initial={panelInitial}
                animate={panelAnimate}
                transition={panelTransition}
              >
                <KnowledgeGraph />
              </motion.div>
            </TabsContent>

            {/* Daily Digest Tab */}
            <TabsContent value="digest" className="mt-0">
              <motion.div
                initial={panelInitial}
                animate={panelAnimate}
                transition={panelTransition}
              >
                {digest ? (
                  <DigestView digest={digest} />
                ) : (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  </div>
                )}
              </motion.div>
            </TabsContent>

            {/* Chat Tab */}
            <TabsContent value="chat" className="mt-0">
              <motion.div
                initial={panelInitial}
                animate={panelAnimate}
                transition={panelTransition}
                className="max-w-4xl mx-auto"
              >
                <ChatInterface onAskQuestion={handleAskQuestion} />
              </motion.div>
            </TabsContent>

            {/* Saved Research Tab — M3.M5. Lists every persisted
                research report, opens them inline via MarkdownReport,
                and supports per-row deletion. */}
            <TabsContent value="saved" className="mt-0">
              <motion.div
                initial={panelInitial}
                animate={panelAnimate}
                transition={panelTransition}
              >
                <SavedResearchList />
              </motion.div>
            </TabsContent>

            {/* Preferences (Settings) Tab — M3.M4: theme + density toggles
                above the existing topic-preferences card. */}
            <TabsContent value="preferences" className="mt-0">
              <motion.div
                initial={panelInitial}
                animate={panelAnimate}
                transition={panelTransition}
                className="max-w-4xl mx-auto"
              >
                <Settings
                  selectedCategories={selectedCategories}
                  onCategoriesChange={setSelectedCategories}
                  onSave={savePreferences}
                  isSaving={isSavingPreferences}
                  hasUnsavedChanges={hasUnsavedChanges}
                />
              </motion.div>
            </TabsContent>
          </div>

          {/* Toast Notifications */}
          <Toaster position="bottom-right" />

          {/* Footer */}
          <footer className="border-t border-border mt-8">
            <div className="px-6 py-4">
              <div className="flex items-center justify-between gap-4 text-xs text-muted-foreground">
                <span>TechPulse AI — your personalised tech-news hub</span>
                <span>
                  Aggregating from TechCrunch, The Verge, Wired, Ars Technica
                  &amp; more
                </span>
              </div>
            </div>
          </footer>
        </main>
      </CommandPaletteProvider>
    </Tabs>
  );
}

/**
 * Top-level App — wraps the shell in ThemeProvider so the rest of the app
 * (including the inline-bootstrap-set `<html class="dark">`) shares one
 * source of truth for the current theme.
 */
export default function App() {
  return (
    <ThemeProvider>
      <AppShell />
    </ThemeProvider>
  );
}
