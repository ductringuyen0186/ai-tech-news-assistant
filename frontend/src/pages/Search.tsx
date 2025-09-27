import React, { useState } from 'react';
import { Search as SearchIcon, ExternalLink, Zap, MessageSquare, Heart } from 'lucide-react';

interface SearchResult {
  id: number;
  title: string;
  content: string;
  url: string;
  published: string;
  source: string;
  relevance_score?: number;
}

interface SearchResponse {
  success: boolean;
  query: string;
  results: SearchResult[];
  total: number;
  source: string;
}

interface SummaryResponse {
  success: boolean;
  summary: string;
  method: string;
  model: string;
  original_length: number;
  summary_length: number;
}

export default function Search() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  
  // Summarization state
  const [selectedText, setSelectedText] = useState('');
  const [summary, setSummary] = useState('');
  const [summaryLoading, setSummaryLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8001/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          limit: 10
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SearchResponse = await response.json();
      
      if (data.success) {
        setResults(data.results);
        setTotalResults(data.total);
      } else {
        setError('Search failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSummarize = async (text: string) => {
    if (!text.trim()) return;

    setSummaryLoading(true);
    setSelectedText(text);

    try {
      const response = await fetch('http://localhost:8001/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          max_length: 100
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SummaryResponse = await response.json();
      
      if (data.success) {
        setSummary(data.summary);
      } else {
        setSummary('Summarization failed');
      }
    } catch (err) {
      setSummary('Error: ' + (err instanceof Error ? err.message : 'Summarization failed'));
      console.error('Summary error:', err);
    } finally {
      setSummaryLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + '...';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">AI Search & Summarization</h1>
        <p className="text-gray-600 mt-1">
          Search through articles and test AI summarization features
        </p>
      </div>

      {/* Search Form */}
      <div className="bg-white shadow-sm rounded-lg p-6 border">
        <form onSubmit={handleSearch} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Query
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your search query (e.g., 'AI', 'machine learning', 'OpenAI')..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="submit"
                disabled={isLoading || !query.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <SearchIcon size={16} />
                <span>{isLoading ? 'Searching...' : 'Search'}</span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error: {error}</p>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">
              Search Results ({totalResults} found)
            </h2>
            <span className="text-sm text-gray-600">
              Using keyword search
            </span>
          </div>

          {results.map(article => (
            <div key={article.id} className="bg-white shadow-sm rounded-lg p-6 border hover:shadow-md transition-shadow">
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-semibold text-gray-900 flex-1">
                    {article.title}
                  </h3>
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleSummarize(article.content)}
                      disabled={summaryLoading}
                      className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded hover:bg-purple-200 disabled:bg-gray-100 disabled:text-gray-400 flex items-center space-x-1"
                    >
                      <Zap size={14} />
                      <span>Summarize</span>
                    </button>
                    {article.url && (
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center space-x-1"
                      >
                        <ExternalLink size={14} />
                        <span>View</span>
                      </a>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span className="font-medium">{article.source}</span>
                  <span>•</span>
                  <span>{formatDate(article.published)}</span>
                  {article.relevance_score && (
                    <>
                      <span>•</span>
                      <span className="flex items-center space-x-1">
                        <Heart size={12} className="text-red-500" />
                        <span>Score: {article.relevance_score}</span>
                      </span>
                    </>
                  )}
                </div>

                <p className="text-gray-700 leading-relaxed">
                  {truncateText(article.content, 300)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summarization Results */}
      {(selectedText || summary) && (
        <div className="bg-white shadow-sm rounded-lg p-6 border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <MessageSquare size={20} className="text-purple-600" />
            <span>AI Summarization</span>
          </h3>

          {summaryLoading ? (
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ) : summary ? (
            <div className="space-y-3">
              <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-400">
                <p className="text-gray-800">{summary}</p>
              </div>
              <div className="text-sm text-gray-600">
                <p>Original length: {selectedText.length} characters</p>
                <p>Summary length: {summary.length} characters</p>
                <p>Compression ratio: {Math.round((1 - summary.length / selectedText.length) * 100)}%</p>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* No Results */}
      {!isLoading && query && results.length === 0 && !error && (
        <div className="text-center py-12">
          <SearchIcon size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600">
            Try searching for terms like "AI", "machine learning", or "OpenAI"
          </p>
        </div>
      )}

      {/* Quick Test Examples */}
      {!query && !isLoading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">Quick Test Examples</h3>
          <p className="text-blue-800 mb-4">Try these sample searches to test the AI features:</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {['AI', 'OpenAI', 'machine learning'].map((term) => (
              <button
                key={term}
                onClick={() => setQuery(term)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
              >
                Search "{term}"
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
