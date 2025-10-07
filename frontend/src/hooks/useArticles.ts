/**
 * useArticles Hook
 * 
 * Custom hook for fetching articles from the backend API.
 * Manages article state with TanStack Query for caching and error handling.
 * 
 * @example
 * ```tsx
 * const { articles, total, isLoading, error } = useArticles({
 *   params: { source: 'hackernews', limit: 20 },
 *   enabled: true
 * });
 * ```
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { articlesApi } from '../lib/api';
import type { Article, ArticleSearchParams, SearchResponse } from '../types/api';

export interface UseArticlesOptions {
  /**
   * Search/filter parameters
   */
  params?: ArticleSearchParams;
  
  /**
   * Enable/disable auto-fetching
   * @default true
   */
  enabled?: boolean;
  
  /**
   * Refetch interval in milliseconds
   * @default undefined (no auto-refetch)
   */
  refetchInterval?: number;
  
  /**
   * Cache time in milliseconds
   * @default 5 minutes
   */
  staleTime?: number;
}

export interface UseArticlesReturn {
  /**
   * List of articles
   */
  articles: Article[];
  
  /**
   * Total article count
   */
  total: number;
  
  /**
   * Loading state
   */
  isLoading: boolean;
  
  /**
   * Error state
   */
  error: Error | null;
  
  /**
   * Refetch function
   */
  refetch: () => void;
  
  /**
   * Is fetching (including background refetch)
   */
  isFetching: boolean;
  
  /**
   * Full response data
   */
  data?: SearchResponse;
}

/**
 * Hook to fetch paginated articles
 */
export function useArticles({
  params = {},
  enabled = true,
  refetchInterval,
  staleTime = 5 * 60 * 1000, // 5 minutes default
}: UseArticlesOptions = {}): UseArticlesReturn {
  const queryResult = useQuery({
    queryKey: ['articles', params],
    queryFn: () => articlesApi.getArticles(params),
    enabled,
    staleTime,
    refetchInterval,
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  return {
    articles: queryResult.data?.articles || [],
    total: queryResult.data?.total || 0,
    isLoading: queryResult.isLoading,
    error: queryResult.error,
    refetch: queryResult.refetch,
    isFetching: queryResult.isFetching,
    data: queryResult.data,
  };
}

/**
 * Hook to fetch a single article by ID
 */
export function useArticle(id: string, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: ['article', id],
    queryFn: () => articlesApi.getArticle(id),
    enabled: options.enabled !== false && !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes (articles don't change often)
    retry: 3,
  });
}

/**
 * Hook to get article statistics
 */
export function useArticleStats() {
  return useQuery({
    queryKey: ['article-stats'],
    queryFn: () => articlesApi.getArticleStats(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
}

/**
 * Hook to get available sources
 */
export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: () => articlesApi.getSources(),
    staleTime: 30 * 60 * 1000, // 30 minutes (sources rarely change)
  });
}

/**
 * Hook to get available categories
 */
export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => articlesApi.getCategories(),
    staleTime: 30 * 60 * 1000, // 30 minutes (categories rarely change)
  });
}
