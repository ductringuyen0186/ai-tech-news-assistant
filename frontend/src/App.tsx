import React, { useState, useEffect } from 'react';
import { Newspaper, Search as SearchIcon, Network, FileText, MessageCircle, Settings as SettingsIcon, Sparkles } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Toaster } from './components/ui/sonner';
import { toast } from 'sonner';

// Components
import NewsCard from './components/NewsCard';
import SearchBar from './components/SearchBar';
import TopicFilter from './components/TopicFilter';
import DigestView from './components/DigestView';
import ChatInterface from './components/ChatInterface';
import ResearchMode from './components/ResearchMode';
import KnowledgeGraph from './components/KnowledgeGraph';
import { Switch } from './components/ui/switch';
import { Button } from './components/ui/button';
import { Separator } from './components/ui/separator';

// API
import { useArticles, useSemanticSearch } from './hooks';

// Types
interface Preferences {
  topics: string[];
  compactView: boolean;
  autoRefresh: boolean;
}

function App() {
  const [activeTab, setActiveTab] = useState('feed');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [compactView, setCompactView] = useState(false);
  const [preferences, setPreferences] = useState<Preferences>({
    topics: [],
    compactView: false,
    autoRefresh: true,
  });
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Available topics
  const availableTopics = [
    'AI',
    'Machine Learning',
    'Cloud',
    'Security',
    'DevOps',
    'Web Development',
    'Mobile',
    'Data Science',
    'Blockchain',
    'IoT',
  ];

  // Fetch articles
  const { articles, isLoading, error, refetch } = useArticles({
    params: {
      limit: 20,
      category: selectedTopics.length > 0 ? selectedTopics[0] : undefined,
    },
  });

  // Search functionality
  const { data: searchResults, refetch: searchRefetch, isLoading: searchLoading } = useSemanticSearch({
    query: searchQuery,
    categories: selectedTopics.length > 0 ? selectedTopics : undefined,
    enabled: false,
  });

  // Handle topic toggle
  const handleToggleTopic = (topic: string) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
    setHasUnsavedChanges(true);
  };

  // Save preferences
  const handleSavePreferences = () => {
    setPreferences({
      topics: selectedTopics,
      compactView,
      autoRefresh: preferences.autoRefresh,
    });
    setHasUnsavedChanges(false);
    toast.success('Preferences saved successfully!');
  };

  // Search handler
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (query.trim()) {
      setTimeout(() => searchRefetch(), 0);
    }
  };

  // Transform search results to articles
  const searchArticles = searchResults?.results?.map(result => ({
    id: result.article_id,
    title: result.title,
    url: result.url,
    source: result.source,
    categories: result.categories,
    keywords: result.keywords,
    published_at: result.published_date,
    content: '', // Not included in search results
    metadata: {},
    created_at: result.published_date,
    updated_at: result.published_date,
  })) || [];
  
  const displayArticles = searchQuery && searchArticles.length > 0
    ? searchArticles 
    : articles;

  return (
    <div className="min-h-screen bg-gray-50 subtle-pattern">
      <Toaster />
      
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50 elevation-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-display font-bold text-gradient">
                  TechPulse AI
                </h1>
                <p className="text-xs text-muted-foreground">Intelligent News Aggregation</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {hasUnsavedChanges && (
                <Button onClick={handleSavePreferences} size="sm" variant="gradient">
                  Save Changes
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Tab Navigation */}
          <TabsList className="grid w-full grid-cols-6 lg:w-auto lg:inline-flex">
            <TabsTrigger value="feed" className="gap-2">
              <Newspaper className="h-4 w-4" />
              <span className="hidden sm:inline">News Feed</span>
            </TabsTrigger>
            <TabsTrigger value="research" className="gap-2">
              <FileText className="h-4 w-4" />
              <span className="hidden sm:inline">Research</span>
            </TabsTrigger>
            <TabsTrigger value="knowledge" className="gap-2">
              <Network className="h-4 w-4" />
              <span className="hidden sm:inline">Knowledge</span>
            </TabsTrigger>
            <TabsTrigger value="digest" className="gap-2">
              <Sparkles className="h-4 w-4" />
              <span className="hidden sm:inline">Digest</span>
            </TabsTrigger>
            <TabsTrigger value="chat" className="gap-2">
              <MessageCircle className="h-4 w-4" />
              <span className="hidden sm:inline">Ask AI</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2">
              <SettingsIcon className="h-4 w-4" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
          </TabsList>

          {/* News Feed Tab */}
          <TabsContent value="feed" className="space-y-6">
            {/* Search and Filters */}
            <div className="space-y-4">
              <SearchBar onSearch={handleSearch} defaultValue={searchQuery} />
              
              <TopicFilter
                topics={availableTopics}
                selectedTopics={selectedTopics}
                onToggleTopic={handleToggleTopic}
                onSave={handleSavePreferences}
                showSave={hasUnsavedChanges}
              />

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Switch checked={compactView} onCheckedChange={setCompactView} />
                  <span className="text-sm text-muted-foreground">Compact view</span>
                </div>
              </div>
            </div>

            <Separator />

            {/* Articles Grid */}
            <div>
              {isLoading || searchLoading ? (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  <p className="mt-2 text-muted-foreground">Loading articles...</p>
                </div>
              ) : error ? (
                <div className="text-center py-12">
                  <p className="text-red-600">Error loading articles. Please try again.</p>
                </div>
              ) : displayArticles.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">No articles found. Try adjusting your filters.</p>
                </div>
              ) : (
                <div className={`grid gap-6 ${compactView ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'}`}>
                  {displayArticles.map((article: any) => (
                    <NewsCard
                      key={article.id}
                      article={article}
                      compact={compactView}
                    />
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Research Tab */}
          <TabsContent value="research">
            <ResearchMode />
          </TabsContent>

          {/* Knowledge Graph Tab */}
          <TabsContent value="knowledge">
            <KnowledgeGraph />
          </TabsContent>

          {/* Digest Tab */}
          <TabsContent value="digest">
            <DigestView />
          </TabsContent>

          {/* Chat Tab */}
          <TabsContent value="chat" className="h-[calc(100vh-250px)]">
            <ChatInterface />
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <div>
              <h2 className="text-3xl font-display font-bold text-gradient mb-2">
                Settings
              </h2>
              <p className="text-muted-foreground">
                Customize your news experience
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-white rounded-lg border">
                <div>
                  <h3 className="font-semibold">Auto Refresh</h3>
                  <p className="text-sm text-muted-foreground">
                    Automatically check for new articles
                  </p>
                </div>
                <Switch
                  checked={preferences.autoRefresh}
                  onCheckedChange={(checked) => {
                    setPreferences({ ...preferences, autoRefresh: checked });
                    setHasUnsavedChanges(true);
                  }}
                />
              </div>

              <div className="flex items-center justify-between p-4 bg-white rounded-lg border">
                <div>
                  <h3 className="font-semibold">Compact View by Default</h3>
                  <p className="text-sm text-muted-foreground">
                    Use compact cards for article display
                  </p>
                </div>
                <Switch
                  checked={preferences.compactView}
                  onCheckedChange={(checked) => {
                    setPreferences({ ...preferences, compactView: checked });
                    setCompactView(checked);
                    setHasUnsavedChanges(true);
                  }}
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-muted-foreground">
            <p>TechPulse AI • Powered by Advanced Machine Learning</p>
            <p className="mt-1">Stay informed with intelligent news aggregation</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
