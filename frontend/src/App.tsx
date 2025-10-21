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

  // Fetch articles
  const fetchArticles = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedCategories.length > 0) {
        params.append("category", selectedCategories.join(","));
      }
      if (searchQuery) {
        params.append("q", searchQuery);
      }
      params.append("limit", "50");

      const data = await apiFetch<any>(`${API_ENDPOINTS.news}?${params}`);
      
      // Map FastAPI response to expected format
      // Backend returns PaginatedResponse with "data" field, not "items"
      const articles = data.data || data.items || [];
      const mappedArticles = articles.map((article: any) => ({
        id: article.id,
        title: article.title,
        content: article.content,
        summaryShort: article.summary || article.content?.substring(0, 200) + '...',
        summaryMedium: article.summary || article.content?.substring(0, 400) + '...',
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
      })) || [];
      
      setArticles(mappedArticles);
      setFilteredArticles(mappedArticles);
    } catch (error) {
      console.error("Error fetching articles:", error);
      toast.error("Failed to fetch articles. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Fetch digest - Create mock data for now (can be implemented later)
  const fetchDigest = async () => {
    try {
      // Mock digest data matching DigestView expected structure
      setDigest({
        date: new Date().toISOString(),
        topStories: [
          {
            id: "digest-1",
            title: "AI Breakthrough in Natural Language Understanding",
            source: "TechCrunch",
            summaryShort: "Researchers achieve significant improvements in LLM reasoning capabilities, bringing AI closer to human-level understanding.",
            category: ["AI", "Machine Learning"]
          },
          {
            id: "digest-2",
            title: "New Security Vulnerability Affects Major Cloud Providers",
            source: "SecurityWeek",
            summaryShort: "Critical security flaw discovered in major cloud infrastructure, prompting immediate patches across the industry.",
            category: ["Security", "Cloud"]
          },
          {
            id: "digest-3",
            title: "Quantum Computing Makes Significant Progress",
            source: "Nature",
            summaryShort: "Scientists demonstrate quantum advantage in practical applications, marking a milestone in quantum computing development.",
            category: ["Quantum", "Hardware"]
          }
        ],
        categoryBreakdown: {
          "AI": 15,
          "Machine Learning": 12,
          "Security": 8,
          "Cloud": 6,
          "Quantum": 4,
          "Hardware": 5
        },
        trendingTopics: [
          {
            id: "trend-1",
            title: "Large Language Models",
            category: ["AI", "Machine Learning"]
          },
          {
            id: "trend-2",
            title: "Zero-Day Exploits",
            category: ["Security"]
          },
          {
            id: "trend-3",
            title: "Quantum Supremacy",
            category: ["Quantum"]
          }
        ]
      });
    } catch (error) {
      console.error("Error fetching digest:", error);
    }
  };

  // Save preferences - Store locally for now
  const savePreferences = async () => {
    setIsSavingPreferences(true);
    try {
      // Save to localStorage
      localStorage.setItem('techpulse_categories', JSON.stringify(selectedCategories));
      
      // Update saved categories state
      setSavedCategories([...selectedCategories]);
      setHasUnsavedChanges(false);

      toast.success("Preferences saved successfully!", {
        description: `Your feed will now show ${selectedCategories.length} selected topic${selectedCategories.length !== 1 ? 's' : ''}.`,
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

  // Ask question in chat - Can be connected to summarization API later
  const handleAskQuestion = async (question: string) => {
    try {
      // Mock response for now
      return {
        answer: "This is a placeholder response. Connect to your FastAPI summarization endpoint for real AI responses.",
        success: true
      };
    } catch (error) {
      console.error("Error processing question:", error);
      throw error;
    }
  };

  // Load preferences and articles on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load from localStorage
        const saved = localStorage.getItem('techpulse_categories');
        if (saved) {
          const cats = JSON.parse(saved);
          setSelectedCategories(cats);
          setSavedCategories(cats);
        }
      } catch (error) {
        console.error("Error loading preferences:", error);
      }
      
      fetchArticles();
      fetchDigest();
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
                {articles.length} Articles Today
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