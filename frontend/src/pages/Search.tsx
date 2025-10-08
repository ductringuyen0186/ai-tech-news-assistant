import React, { useState } from 'react';
import { useSemanticSearch, useSources, useCategories } from '../hooks';
import { formatDate, truncateText } from '@/lib/utils.ts';
import { 
  Search as SearchIcon, 
  ExternalLink, 
  Filter, 
  TrendingUp,
  X,
  Clock,
  Zap,
  Sparkles
} from 'lucide-react';

export default function Search() {
  const [query, setQuery] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  
  // Filter state
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [minScore, setMinScore] = useState(0.5);
  const [useReranking, setUseReranking] = useState(true);
  const [limit, setLimit] = useState(20);

  // Semantic search with new hook (Issue #14 + #18)
  const {
    results,
    totalResults,
    executionTime,
    rerankingApplied,
    isLoading,
    error,
    refetch,
  } = useSemanticSearch({
    query,
    limit,
    min_score: minScore,
    sources: selectedSources.length > 0 ? selectedSources : undefined,
    categories: selectedCategories.length > 0 ? selectedCategories : undefined,
    use_reranking: useReranking,
    enabled: submitted && !!query,
  });

  // Fetch available sources and categories for filters
  const { data: sourcesData } = useSources();
  const { data: categoriesData } = useCategories();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setSubmitted(true);
      // Force refetch when form is submitted
      setTimeout(() => refetch(), 0);
    }
  };

  const toggleSource = (source: string) => {
    setSelectedSources(prev =>
      prev.includes(source) ? prev.filter(s => s !== source) : [...prev, source]
    );
  };

  const toggleCategory = (category: string) => {
    setSelectedCategories(prev =>
      prev.includes(category) ? prev.filter(c => c !== category) : [...prev, category]
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 flex items-center">
          <Sparkles className="h-6 w-6 mr-2 text-primary-600" />
          Semantic Search
        </h1>
        <p className="text-gray-600 mt-1">
          Search articles using natural language with AI-powered vector similarity
        </p>
      </div>

      {/* Search Form */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Query
            </label>
            <div className="relative">
              <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                className="input pl-10"
                placeholder="Try: 'latest AI breakthroughs' or 'explain quantum computing'"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
            </div>
          </div>

          {/* Toggle Filters & Search Button */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <Filter className="h-4 w-4 mr-2" />
              {showFilters ? 'Hide' : 'Show'} Advanced Filters
            </button>
            
            <button 
              type="submit" 
              className="btn-primary flex items-center" 
              disabled={!query.trim()}
            >
              <SearchIcon className="h-4 w-4 mr-2" />
              Search
            </button>
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="p-4 bg-gray-50 rounded-lg space-y-4 border border-gray-200">
              {/* Sources */}
              {sourcesData && Object.keys(sourcesData.sources).length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sources
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {Object.keys(sourcesData.sources).map(source => (
                      <button
                        key={source}
                        type="button"
                        onClick={() => toggleSource(source)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          selectedSources.includes(source)
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {source}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Categories */}
              {categoriesData && categoriesData.categories.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Categories
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {categoriesData.categories.map(category => (
                      <button
                        key={category}
                        type="button"
                        onClick={() => toggleCategory(category)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          selectedCategories.includes(category)
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {category}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Minimum Score */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Minimum Relevance Score: {minScore.toFixed(2)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={minScore}
                  onChange={e => setMinScore(parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Less relevant</span>
                  <span>More relevant</span>
                </div>
              </div>

              {/* Reranking */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="useReranking"
                  checked={useReranking}
                  onChange={e => setUseReranking(e.target.checked)}
                  className="h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <label htmlFor="useReranking" className="ml-2 text-sm text-gray-700 flex items-center">
                  <TrendingUp className="h-4 w-4 mr-1" />
                  Use smart reranking (improves relevance)
                </label>
              </div>

              {/* Result Limit */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Results per page
                </label>
                <select
                  value={limit}
                  onChange={e => setLimit(parseInt(e.target.value))}
                  className="input"
                >
                  <option value="10">10 results</option>
                  <option value="20">20 results</option>
                  <option value="50">50 results</option>
                  <option value="100">100 results</option>
                </select>
              </div>
            </div>
          )}
        </form>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12 card">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="text-gray-500 mt-4">Searching with AI...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="card bg-red-50 border border-red-200">
          <div className="flex items-start">
            <X className="h-5 w-5 text-red-600 mt-0.5 mr-2 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Search Error</h3>
              <p className="text-sm text-red-700 mt-1">{error.message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {submitted && !isLoading && !error && (
        <div className="space-y-4">
          {/* Results Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg border border-primary-200">
            <div className="flex items-center space-x-6">
              <div>
                <p className="text-sm text-gray-600">Results Found</p>
                <p className="text-2xl font-bold text-gray-900">{totalResults}</p>
              </div>
              
              {executionTime > 0 && (
                <div className="flex items-center text-sm text-gray-600">
                  <Clock className="h-4 w-4 mr-1" />
                  {executionTime}ms
                </div>
              )}
              
              {rerankingApplied && (
                <div className="flex items-center text-sm text-primary-600">
                  <TrendingUp className="h-4 w-4 mr-1" />
                  Reranked
                </div>
              )}
            </div>

            {/* Active Filters */}
            {(selectedSources.length > 0 || selectedCategories.length > 0) && (
              <div className="flex flex-wrap gap-2">
                {selectedSources.map(source => (
                  <span
                    key={source}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                  >
                    {source}
                    <button
                      onClick={() => toggleSource(source)}
                      className="ml-1 hover:text-primary-900"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
                {selectedCategories.map(category => (
                  <span
                    key={category}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {category}
                    <button
                      onClick={() => toggleCategory(category)}
                      className="ml-1 hover:text-blue-900"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Results List */}
          {results.length > 0 ? (
            <div className="space-y-4">
              {results.map((result, index) => (
                <div
                  key={result.article_id}
                  className="card hover:shadow-lg transition-shadow"
                >
                  {/* Header with title and score */}
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium text-gray-500">
                          #{index + 1}
                        </span>
                        <div className="flex items-center space-x-1">
                          <Zap className="h-4 w-4 text-yellow-500" />
                          <span className="text-sm font-medium text-gray-700">
                            {(result.score * 100).toFixed(1)}% match
                          </span>
                        </div>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 leading-tight">
                        {result.title}
                      </h3>
                    </div>
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-4 text-primary-600 hover:text-primary-700 flex-shrink-0"
                      title="Open article"
                    >
                      <ExternalLink className="h-5 w-5" />
                    </a>
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center space-x-4 text-sm text-gray-500 mb-3">
                    <span className="font-medium">{result.source}</span>
                    <span>•</span>
                    <span>{formatDate(result.published_date)}</span>
                  </div>

                  {/* Categories */}
                  {result.categories.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {result.categories.map(category => (
                        <span
                          key={category}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                        >
                          {category}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Keywords */}
                  {result.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {result.keywords.slice(0, 5).map((keyword, idx) => (
                        <span 
                          key={idx} 
                          className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 card">
              <SearchIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No results found</p>
              <p className="text-gray-400 text-sm mt-2">
                Try adjusting your filters or using different search terms
              </p>
            </div>
          )}
        </div>
      )}

      {/* Initial State */}
      {!submitted && !isLoading && (
        <div className="text-center py-16 card">
          <Sparkles className="h-16 w-16 text-primary-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            AI-Powered Search
          </h3>
          <p className="text-gray-500 max-w-md mx-auto mb-4">
            Enter a search query above to find relevant articles using AI-powered
            semantic search with vector similarity matching.
          </p>
          <div className="text-sm text-gray-400 space-y-1">
            <p>✨ Natural language queries</p>
            <p>🎯 Relevance scoring</p>
            <p>🔍 Advanced filtering</p>
          </div>
        </div>
      )}
    </div>
  );
}
