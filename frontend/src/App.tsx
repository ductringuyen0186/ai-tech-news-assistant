import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";
import { NewsCard } from "./components/NewsCard";
import { TopicFilter } from "./components/TopicFilter";
import { SearchBar } from "./components/SearchBar";
import { DigestView } from "./components/DigestView";
import { ChatInterface } from "./components/ChatInterface";
import { ResearchMode } from "./components/ResearchMode";
import { KnowledgeGraph } from "./components/KnowledgeGraph";
import { Newspaper, Settings, Mail, MessageCircle, TrendingUp, Loader2, Grid, List, Lightbulb, Network } from "lucide-react";
import { API_BASE_URL, API_ENDPOINTS, apiFetch } from "./config/api";

export default function App() {
  const [articles, setArticles] = useState<any[]>([]);
  const [filteredArticles, setFilteredArticles] = useState<any[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>(["AI", "Machine Learning"]);
  const [searchQuery, setSearchQuery] = useState("");
  const [digest, setDigest] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"compact" | "detailed">("detailed");
  const [showTrendingOnly, setShowTrendingOnly] = useState(false);
  const [isSavingPreferences, setIsSavingPreferences] = useState(false);
  const [savedCategories, setSavedCategories] = useState<string[]>([]);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [totalArticleCount, setTotalArticleCount] = useState<number>(0);

  // Fetch articles
  const fetchArticles = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      // Backend expects page_size, page, source (not limit, q, category)
      params.append("page", "1");
      params.append("page_size", "50");
      
      if (selectedCategories.length > 0) {
        // Backend uses 'source' parameter for filtering, not 'category'
        params.append("source", selectedCategories[0]);
      }
      if (searchQuery) {
        params.append("author", searchQuery);
      }

      const data = await apiFetch<any>(`${API_ENDPOINTS.news}?${params}`);
      console.log("API Response:", data);
      
      // Map FastAPI response to expected format
      // Backend returns PaginatedResponse with "data" field containing articles
      const articles = data.data || data.items || [];
      // Build summaryShort + summaryMedium as truly distinct slices so the
      // NewsCard expanded view doesn't render the same text twice. The
      // backend's ``summary`` column for RSS-only rows is the same string as
      // ``content`` (we only get one body per entry), so we truncate the
      // available body to two different lengths instead of falling back to
      // the same value.
      const buildSummaries = (a: any): { summaryShort: string; summaryMedium: string } => {
        const body: string = (a.summary || a.content || '').toString().trim();
        if (!body) {
          return { summaryShort: '', summaryMedium: '' };
        }
        const short =
          body.length > 200 ? body.slice(0, 200).trimEnd() + '...' : body;
        const medium =
          body.length > 600 ? body.slice(0, 600).trimEnd() + '...' : body;
        return { summaryShort: short, summaryMedium: medium };
      };
      const mappedArticles = articles.map((article: any) => {
        const { summaryShort, summaryMedium } = buildSummaries(article);
        return {
          id: article.id,
          title: article.title,
          content: article.content,
          summaryShort,
          summaryMedium,
          url: article.url,
          publishedAt: article.published_at,
          imageUrl: article.image_url || 'https://via.placeholder.com/400x300?text=Tech+News',
          category: article.categories || [],
          source: article.source,
          credibilityScore: 85, // Default score
          trending: false,
          sentiment: 'neutral',
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

  // Fetch stats - powers the "Articles Today" / total-count badge in the header.
  // Backend wraps ArticleStats in BaseResponse: { success, message, data: { total_articles, recent_articles, ... } }
  // We prefer recent_articles (last-24h) when populated, else fall back to total_articles
  // so the header shows a meaningful number instead of 0.
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

  // Fetch digest - calls the real /api/digest/ endpoint which builds
  // top stories, category breakdown, and trending topics from the DB.
  const fetchDigest = async () => {
    try {
      const data = await apiFetch<any>(API_ENDPOINTS.digest);
      // Endpoint returns the DigestView-shaped payload directly (no envelope).
      setDigest(data);
    } catch (error) {
      console.error("Error fetching digest:", error);
      toast.error("Failed to fetch digest. Please try again.");
    }
  };

  // Save preferences — write to the backend (source of truth) and mirror
  // to localStorage as an offline cache so the next mount has something to
  // fall back on if the network is down.
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

      // Mirror the persisted shape into local state + offline cache.
      const persistedCategories: string[] = Array.isArray(saved?.categories)
        ? saved.categories
        : selectedCategories;
      setSavedCategories([...persistedCategories]);
      setHasUnsavedChanges(false);

      try {
        localStorage.setItem(
          'techpulse_categories',
          JSON.stringify(persistedCategories)
        );
      } catch {
        // Best-effort cache; ignore quota / privacy-mode failures.
      }

      toast.success("Preferences saved successfully!", {
        description: `Your feed will now show ${persistedCategories.length} selected topic${persistedCategories.length !== 1 ? 's' : ''}.`,
        duration: 3000,
      });

      // Refresh articles after saving preferences
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

  // Ask question in chat - calls FastAPI RAG endpoint (retrieval + LLM).
  const handleAskQuestion = async (question: string) => {
    try {
      const envelope = await apiFetch<any>("/api/rag/query", {
        method: "POST",
        body: JSON.stringify({ question, top_k: 5, min_score: 0.3 }),
      });
      // Backend wraps RAG output in BaseResponse: { success, message, data: { answer, sources, ... } }
      const data = envelope?.data ?? envelope;
      const rawSources = (data.sources || []).map((s: any) => ({
        id: String(s.id ?? ""),
        url: s.url ?? "",
        title: s.title ?? "Untitled",
        summaryShort: s.title ?? "",
      }));
      // Dedup by id, url, AND title so repeated retrieval hits on the same
      // article — including duplicates with different ids but identical
      // titles (which previously slipped through and rendered the same card
      // twice in the "Related articles" section) — render only once.
      const seenIds = new Set<string>();
      const seenTitles = new Set<string>();
      const sources = rawSources.filter((s: any) => {
        const idKey = s.id || s.url;
        const titleKey = (s.title || "").trim().toLowerCase();
        if (idKey && seenIds.has(idKey)) return false;
        if (titleKey && seenTitles.has(titleKey)) return false;
        if (idKey) seenIds.add(idKey);
        if (titleKey) seenTitles.add(titleKey);
        return true;
      });
      return { answer: data.answer ?? "(no answer returned)", relevantArticles: sources, success: true };
    } catch (error) {
      console.error("Error processing question:", error);
      return { answer: "Sorry - the chat backend is unreachable right now.", success: false };
    }
  };

  // Load preferences and articles on mount.
  //
  // Source-of-truth order:
  //   1. Backend GET /api/settings (authoritative — wins on success)
  //   2. localStorage 'techpulse_categories' cache (offline fallback)
  //   3. Hard-coded defaults already in component state
  useEffect(() => {
    const loadData = async () => {
      try {
        const envelope = await apiFetch<any>(API_ENDPOINTS.settings);
        const data = envelope?.data ?? envelope;
        if (data && typeof data === 'object') {
          if (Array.isArray(data.categories)) {
            setSelectedCategories(data.categories);
            setSavedCategories(data.categories);
            // Refresh the offline cache with the authoritative value.
            try {
              localStorage.setItem(
                'techpulse_categories',
                JSON.stringify(data.categories)
              );
            } catch {
              // Ignore cache write failures.
            }
          }
          if (data.view_mode === 'compact' || data.view_mode === 'detailed') {
            setViewMode(data.view_mode);
          }
          if (typeof data.show_trending_only === 'boolean') {
            setShowTrendingOnly(data.show_trending_only);
          }
        }
      } catch (backendError) {
        console.warn(
          'Backend settings unreachable; falling back to localStorage cache',
          backendError
        );
        try {
          const saved = localStorage.getItem('techpulse_categories');
          if (saved) {
            const cats = JSON.parse(saved);
            if (Array.isArray(cats)) {
              setSelectedCategories(cats);
              setSavedCategories(cats);
            }
          }
        } catch (cacheError) {
          console.error('Error loading preferences from cache:', cacheError);
        }
      }

      fetchArticles();
      fetchDigest();
      fetchStats();
    };

    loadData();
  }, []);

  // Check for unsaved changes
  useEffect(() => {
    const categoriesChanged = JSON.stringify(selectedCategories.sort()) !== JSON.stringify(savedCategories.sort());
    setHasUnsavedChanges(categoriesChanged);
  }, [selectedCategories, savedCategories]);

  // Refetch when filters change
  useEffect(() => {
    fetchArticles();
  }, [selectedCategories, searchQuery, showTrendingOnly]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 subtle-pattern">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-lg border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center shadow-md">
                <Newspaper className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl text-gradient">TechPulse AI</h1>
                <p className="text-sm text-gray-600">AI-Powered Tech News Aggregation</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="gap-1 border-orange-200 bg-orange-50 text-orange-700">
                <span>🔥</span>
                {articles.filter((a) => a.trending).length} Trending
              </Badge>
              <Badge variant="outline" className="gap-1 border-blue-200 bg-blue-50 text-blue-700">
                {totalArticleCount || articles.length} Articles Today
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <Tabs defaultValue="feed" className="space-y-6">
          <TabsList className="grid grid-cols-6 w-full max-w-4xl mx-auto">
            <TabsTrigger value="feed" className="gap-2">
              <Newspaper className="w-4 h-4" />
              News Feed
            </TabsTrigger>
            <TabsTrigger value="research" className="gap-2">
              <Lightbulb className="w-4 h-4" />
              Research
            </TabsTrigger>
            <TabsTrigger value="knowledge" className="gap-2">
              <Network className="w-4 h-4" />
              Knowledge
            </TabsTrigger>
            <TabsTrigger value="digest" className="gap-2">
              <Mail className="w-4 h-4" />
              Digest
            </TabsTrigger>
            <TabsTrigger value="chat" className="gap-2">
              <MessageCircle className="w-4 h-4" />
              Ask AI
            </TabsTrigger>
            <TabsTrigger value="preferences" className="gap-2 relative">
              <Settings className="w-4 h-4" />
              Settings
              {hasUnsavedChanges && (
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
              )}
            </TabsTrigger>
          </TabsList>

          {/* News Feed Tab */}
          <TabsContent value="feed" className="space-y-6">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              <div className="flex-1 w-full md:max-w-md">
                <SearchBar onSearch={setSearchQuery} />
              </div>
              <div className="flex gap-2 items-center">
                <Button
                  variant={showTrendingOnly ? "default" : "outline"}
                  size="sm"
                  onClick={() => setShowTrendingOnly(!showTrendingOnly)}
                  className="gap-2"
                >
                  <TrendingUp className="w-4 h-4" />
                  Trending Only
                </Button>
                <div className="flex gap-1 border rounded-lg p-1">
                  <Button
                    variant={viewMode === "detailed" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("detailed")}
                  >
                    <Grid className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === "compact" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("compact")}
                  >
                    <List className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {selectedCategories.length > 0 && (
              <div className="flex flex-wrap gap-2 items-center bg-white p-4 rounded-xl border border-gray-200 elevation-sm">
                <span className="text-sm text-gray-600">Filtered by:</span>
                {selectedCategories.map((cat) => (
                  <Badge key={cat} variant="secondary" className="bg-blue-50 text-blue-700 border-blue-200">
                    {cat}
                  </Badge>
                ))}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedCategories([])}
                  className="ml-auto text-gray-600 hover:text-blue-600"
                >
                  Clear Filters
                </Button>
              </div>
            )}

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            ) : filteredArticles.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-xl border border-gray-200 elevation-md">
                <Newspaper className="w-12 h-12 text-blue-600 mx-auto mb-3" />
                <h3 className="text-lg mb-2 text-gray-900">No articles found</h3>
                <p className="text-gray-600 mb-4">
                  Try adjusting your filters or search query
                </p>
                <Button onClick={() => {
                  setSearchQuery("");
                  setShowTrendingOnly(false);
                  setSelectedCategories([]);
                }} className="gradient-primary text-white">
                  Reset Filters
                </Button>
              </div>
            ) : (
              <div className={`grid gap-6 ${
                viewMode === "detailed" 
                  ? "grid-cols-1 lg:grid-cols-2" 
                  : "grid-cols-1"
              }`}>
                {filteredArticles.map((article) => (
                  <NewsCard
                    key={article.id}
                    article={article}
                    viewMode={viewMode}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          {/* Research Mode Tab */}
          <TabsContent value="research">
            <ResearchMode />
          </TabsContent>

          {/* Knowledge Graph Tab */}
          <TabsContent value="knowledge">
            <KnowledgeGraph />
          </TabsContent>

          {/* Daily Digest Tab */}
          <TabsContent value="digest">
            {digest ? (
              <DigestView digest={digest} />
            ) : (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              </div>
            )}
          </TabsContent>

          {/* Chat Tab */}
          <TabsContent value="chat">
            <div className="max-w-4xl mx-auto">
              <ChatInterface onAskQuestion={handleAskQuestion} />
            </div>
          </TabsContent>

          {/* Preferences Tab */}
          <TabsContent value="preferences">
            <div className="max-w-4xl mx-auto">
              <TopicFilter
                selectedCategories={selectedCategories}
                onCategoriesChange={setSelectedCategories}
                onSave={savePreferences}
                isSaving={isSavingPreferences}
                hasUnsavedChanges={hasUnsavedChanges}
              />
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Toast Notifications */}
      <Toaster position="bottom-right" />

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 gradient-primary rounded-lg flex items-center justify-center shadow-md">
                <Newspaper className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm text-gray-700">
                TechPulse AI - Your personalized tech news hub
              </span>
            </div>
            <p className="text-sm text-gray-500">
              Aggregating from TechCrunch, The Verge, Wired, Ars Technica & more
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
