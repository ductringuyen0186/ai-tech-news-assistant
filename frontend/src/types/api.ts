export interface Article {
  id: string
  title: string
  url: string
  content: string
  summary?: string
  author?: string
  published_at: string
  source: string
  categories: string[]
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ArticleSearchParams {
  query?: string
  source?: string
  category?: string
  limit?: number
  offset?: number
  published_after?: string
  published_before?: string
}

export interface SearchResponse {
  articles: Article[]
  total: number
  limit: number
  offset: number
}

export interface SourcesResponse {
  sources: Record<string, any>
  count: number
}

export interface CategoriesResponse {
  categories: string[]
  count: number
}

export interface StatsResponse {
  total_articles: number
  articles_with_summaries: number
  articles_with_embeddings: number
  top_sources: Array<{ source: string; count: number }>
  recent_articles: number
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  version: string
  components: Record<string, {
    status: 'healthy' | 'degraded' | 'unhealthy'
    [key: string]: any
  }>
}

export interface SummarizationRequest {
  content: string
  max_length?: number
  temperature?: number
}

export interface SummarizationResponse {
  summary: string
  original_length: number
  summary_length: number
  compression_ratio: number
  processing_time: number
  model_used: string
  created_at: string
}
