export interface Article {
  id: string;
  title: string;
  url: string;
  content: string;
  summary?: string;
  author?: string;
  published_at: string;
  source: string;
  categories: string[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ArticleSearchParams {
  query?: string;
  source?: string;
  category?: string;
  limit?: number;
  offset?: number;
  published_after?: string;
  published_before?: string;
}

export interface SearchResponse {
  articles: Article[];
  total: number;
  limit: number;
  offset: number;
}

export interface SourcesResponse {
  sources: Record<string, any>;
  count: number;
}

export interface CategoriesResponse {
  categories: string[];
  count: number;
}

export interface StatsResponse {
  total_articles: number;
  articles_with_summaries: number;
  articles_with_embeddings: number;
  top_sources: Array<{ source: string; count: number }>;
  recent_articles: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  components: Record<
    string,
    {
      status: 'healthy' | 'degraded' | 'unhealthy';
      [key: string]: any;
    }
  >;
}

export interface SummarizationRequest {
  content: string;
  max_length?: number;
  temperature?: number;
}

export interface SummarizationResponse {
  summary: string;
  original_length: number;
  summary_length: number;
  compression_ratio: number;
  processing_time: number;
  model_used: string;
  created_at: string;
}

// ============================================================================
// Semantic Search Types (Issue #14)
// Mirror backend models from src/models/search.py
// ============================================================================

export interface SearchResultItem {
  article_id: string;
  title: string;
  url: string;
  source: string;
  categories: string[];
  keywords: string[];
  published_date: string;
  score: number;
  embedding_id: string;
}

export interface SemanticSearchRequest {
  query: string;
  limit?: number;
  min_score?: number;
  sources?: string[];
  categories?: string[];
  published_after?: string;
  published_before?: string;
  use_reranking?: boolean;
}

export interface SemanticSearchResponse {
  query: string;
  results: SearchResultItem[];
  total_results: number;
  execution_time_ms: number;
  reranking_applied: boolean;
  filters_applied: {
    sources?: string[];
    categories?: string[];
    min_score?: number;
    date_range?: {
      start?: string;
      end?: string;
    };
    limit: number;
  };
}

export interface SearchHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  total_indexed_articles: number;
  embedding_dimensions: number;
  model_name: string;
  timestamp: string;
}
