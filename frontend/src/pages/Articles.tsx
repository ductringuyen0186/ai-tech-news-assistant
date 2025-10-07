import React, { useState, useEffect } from 'react';
import { ExternalLink, Calendar, User, Tag, Search, Zap, RefreshCw, Globe, TrendingUp } from 'lucide-react';
import api from '../lib/api';

interface Article {
  id: string | number;
  title: string;
  content: string;
  url: string;
  published: string;
  source: string;
}

interface ArticlesResponse {
  success: boolean;
  articles: Article[];
  total: number;
  last_fetch?: string;
}

interface SummaryResponse {
  success: boolean;
  summary: string;
  method: string;
  related_articles?: Array<{title: string, source: string}>;
}

export default function Articles() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<string | null>(null);
  const [isFetching, setIsFetching] = useState(false);
  const [summaries, setSummaries] = useState<Map<string, string>>(new Map());
  const [loadingSummary, setLoadingSummary] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get('/articles');
      const data: ArticlesResponse = response.data;

      if (data.success) {
        setArticles(data.articles);
        setLastFetch(data.last_fetch || null);
      } else {
        setError('Failed to fetch articles');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch articles');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchFreshNews = async () => {
    try {
      setIsFetching(true);
      setError(null);
      await api.post('/fetch-news');

      // Wait a bit then refresh articles
      setTimeout(() => {
        fetchArticles();
        setIsFetching(false);
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch fresh news');
      setIsFetching(false);
    }
  };

  const handleSummarize = async (article: Article) => {
    const articleId = String(article.id);
    setLoadingSummary(prev => new Set([...prev, articleId]));

    try {
      const response = await api.post('/summarize', {
        text: `${article.title}. ${article.content}`,
        max_length: 150,
        use_context: true
      });

      if (response.data.success) {
        const result: SummaryResponse = response.data;
        setSummaries(prev => new Map(prev.set(articleId, result.summary)));
      } else {
        console.error('Failed to generate summary');
      }
    } catch (err) {
      console.error('Error generating summary:', err);
    } finally {
      setLoadingSummary(prev => {
        const newSet = new Set(prev);
        newSet.delete(articleId);
        return newSet;
      });
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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Articles</h1>
          <p className="text-gray-600 mt-1">Browse and manage your articles</p>
        </div>
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading articles...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Articles</h1>
          <p className="text-gray-600 mt-1">Browse and manage your articles</p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">Error: {error}</p>
          <button
            onClick={fetchArticles}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 flex items-center">
            <Globe className="mr-2 h-6 w-6 text-blue-600" />
            Tech News Articles
          </h1>
          <p className="text-gray-600 mt-1">Live tech news with AI-powered insights and RAG search</p>
          {lastFetch && (
            <p className="text-sm text-gray-500 mt-1">
              Last updated: {new Date(lastFetch).toLocaleString()}
            </p>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-600 flex items-center">
            <TrendingUp className="mr-1 h-4 w-4" />
            {articles.length} articles
          </div>
          <button
            onClick={fetchFreshNews}
            disabled={isFetching}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            {isFetching ? 'Fetching...' : 'Fetch Fresh News'}
          </button>
        </div>
      </div>

      {/* Articles Grid */}
      <div className="grid gap-6">
        {articles.map(article => (
          <div key={article.id} className="bg-white shadow-sm rounded-lg p-6 border hover:shadow-md transition-shadow">
            <div className="space-y-4">
              {/* Header */}
              <div className="flex justify-between items-start">
                <h2 className="text-xl font-semibold text-gray-900 flex-1">
                  {article.title}
                </h2>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => handleSummarize(article)}
                    disabled={loadingSummary.has(String(article.id))}
                    className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded hover:bg-purple-200 flex items-center space-x-1 disabled:opacity-50"
                  >
                    <Zap size={14} className={loadingSummary.has(String(article.id)) ? 'animate-pulse' : ''} />
                    <span>{loadingSummary.has(String(article.id)) ? 'Summarizing...' : 'AI Summary'}</span>
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

              {/* Metadata */}
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <Tag size={14} />
                  <span className="font-medium">{article.source}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Calendar size={14} />
                  <span>{formatDate(article.published)}</span>
                </div>
              </div>

              {/* AI Summary */}
              {summaries.has(String(article.id)) && (
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
                  <div className="flex items-center mb-2">
                    <Zap className="h-4 w-4 text-purple-600 mr-2" />
                    <span className="text-sm font-medium text-purple-800">AI Summary</span>
                  </div>
                  <p className="text-purple-700 text-sm leading-relaxed">
                    {summaries.get(String(article.id))}
                  </p>
                </div>
              )}

              {/* Content */}
              <div className="prose prose-sm max-w-none">
                <p className="text-gray-700 leading-relaxed">
                  {truncateText(article.content, 400)}
                </p>
              </div>

              {/* Actions */}
              <div className="flex justify-between items-center pt-4 border-t border-gray-100">
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <span>Source: {article.source}</span>
                  <span>•</span>
                  <span>ID: {String(article.id).substring(0, 8)}...</span>
                </div>
                <div className="flex space-x-2">
                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                    >
                      <ExternalLink size={12} />
                      <span>Read Full Article</span>
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {articles.length === 0 && (
        <div className="text-center py-12">
          <Search size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No articles found</h3>
          <p className="text-gray-600">
            There are no articles available at the moment.
          </p>
          <button
            onClick={fetchArticles}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
      )}

      {/* Test Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Test Features</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-blue-800 mb-2">Articles API</h4>
            <p className="text-sm text-blue-700 mb-2">
              Fetches articles from the backend API
            </p>
            <button
              onClick={fetchArticles}
              className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Refresh Articles
            </button>
          </div>
          <div>
            <h4 className="font-medium text-blue-800 mb-2">AI Summarization</h4>
            <p className="text-sm text-blue-700 mb-2">
              Click "Summarize" on any article to test AI features
            </p>
            <span className="text-xs text-blue-600">Using centralized API configuration</span>
          </div>
        </div>
      </div>
    </div>
  );
}
