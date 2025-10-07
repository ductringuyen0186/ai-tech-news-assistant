/**
 * useSemanticSearch Hook
 * 
 * Custom hook for semantic search using vector similarity.
 * Integrates with backend /search endpoint from Issue #14.
 * 
 * Features:
 * - Natural language query support
 * - Advanced filtering (source, category, date, score)
 * - Smart reranking
 * - Automatic caching with TanStack Query
 * - Error handling and loading states
 * 
 * @example
 * ```tsx
 * const { data, isLoading, error, refetch } = useSemanticSearch({
 *   query: "latest AI breakthroughs",
 *   limit: 20,
 *   min_score: 0.6,
 *   use_reranking: true
 * });
 * ```
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { searchApi } from '../lib/api';
import type { SemanticSearchRequest, SemanticSearchResponse } from '../types/api';

export interface UseSemanticSearchOptions extends SemanticSearchRequest {
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

export interface UseSemanticSearchReturn {
  /**
   * Search results
   */
  results: SemanticSearchResponse['results'];
  
  /**
   * Total number of results found
   */
  totalResults: number;
  
  /**
   * Query execution time in milliseconds
   */
  executionTime: number;
  
  /**
   * Whether reranking was applied
   */
  rerankingApplied: boolean;
  
  /**
   * Full search response data
   */
  data?: SemanticSearchResponse;
  
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
   * Is the query enabled
   */
  isSuccess: boolean;
}

/**
 * Semantic search hook using vector similarity
 */
export function useSemanticSearch({
  query,
  limit = 20,
  min_score = 0.5,
  sources,
  categories,
  published_after,
  published_before,
  use_reranking = true,
  enabled = true,
  refetchInterval,
  staleTime = 5 * 60 * 1000, // 5 minutes default
}: UseSemanticSearchOptions): UseSemanticSearchReturn {
  // Build query key for caching
  const queryKey = [
    'semantic-search',
    query,
    limit,
    min_score,
    sources,
    categories,
    published_after,
    published_before,
    use_reranking,
  ];

  // Execute search query
  const queryResult = useQuery({
    queryKey,
    queryFn: () =>
      searchApi.vectorSearch({
        query,
        limit,
        min_score,
        sources,
        categories,
        published_after,
        published_before,
        use_reranking,
      }),
    enabled: enabled && !!query, // Only run if enabled and query is not empty
    staleTime,
    refetchInterval,
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  return {
    results: queryResult.data?.results || [],
    totalResults: queryResult.data?.total_results || 0,
    executionTime: queryResult.data?.execution_time_ms || 0,
    rerankingApplied: queryResult.data?.reranking_applied || false,
    data: queryResult.data,
    isLoading: queryResult.isLoading,
    error: queryResult.error,
    refetch: queryResult.refetch,
    isFetching: queryResult.isFetching,
    isSuccess: queryResult.isSuccess,
  };
}

/**
 * Hook to check semantic search service health
 */
export function useSearchHealth() {
  return useQuery({
    queryKey: ['search-health'],
    queryFn: () => searchApi.searchHealth(),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Check every 5 minutes
  });
}
