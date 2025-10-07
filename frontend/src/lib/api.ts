import axios, { AxiosError } from 'axios';
import type {
  Article,
  ArticleSearchParams,
  SearchResponse,
  SourcesResponse,
  CategoriesResponse,
  StatsResponse,
  HealthStatus,
  SummarizationRequest,
  SummarizationResponse,
  SemanticSearchRequest,
  SemanticSearchResponse,
  SearchHealthResponse,
} from '../types/api';

// Get API base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(config => {
  console.log(
    `Making ${config.method?.toUpperCase()} request to ${config.url}`
  );
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  (error: AxiosError) => {
    // Handle specific error codes
    if (error.response?.status === 401) {
      console.error('Unauthorized - Authentication required');
    } else if (error.response?.status === 429) {
      console.warn('Rate limit exceeded - Please try again later');
    } else if (error.response?.status === 500) {
      console.error('Server error - Please try again later');
    }
    
    // Log error details
    console.error('API Error:', {
      status: error.response?.status,
      message: error.message,
      data: error.response?.data,
      url: error.config?.url,
    });
    
    return Promise.reject(error);
  }
);

export const healthApi = {
  getHealth: (): Promise<HealthStatus> =>
    api.get('/health').then(res => res.data),

  ping: (): Promise<{ message: string; timestamp: string }> =>
    api.get('/ping').then(res => res.data),
};

export const articlesApi = {
  getArticles: (params?: ArticleSearchParams): Promise<SearchResponse> =>
    api.get('/news/articles', { params }).then(res => res.data),

  getArticle: (id: string): Promise<Article> =>
    api.get(`/news/articles/${id}`).then(res => res.data),

  searchArticles: (params: ArticleSearchParams): Promise<SearchResponse> =>
    api.get('/search/articles', { params }).then(res => res.data),

  getSources: (): Promise<SourcesResponse> =>
    api.get('/news/sources').then(res => res.data),

  getCategories: (): Promise<CategoriesResponse> =>
    api.get('/news/categories').then(res => res.data),

  getArticleStats: (): Promise<StatsResponse> =>
    api.get('/news/stats').then(res => res.data),
};

export const summaryApi = {
  summarizeContent: (
    request: SummarizationRequest
  ): Promise<SummarizationResponse> =>
    api.post('/summarization/summarize', request).then(res => res.data),

  summarizeArticle: (
    articleId: string,
    params?: { max_length?: number }
  ): Promise<SummarizationResponse> =>
    api
      .post(`/summarization/articles/${articleId}/summarize`, params)
      .then(res => res.data),
};

export const searchApi = {
  textSearch: (params: ArticleSearchParams): Promise<SearchResponse> =>
    api.get('/search/text', { params }).then(res => res.data),

  semanticSearch: (
    params: ArticleSearchParams & { query: string }
  ): Promise<SearchResponse> =>
    api.get('/search/semantic', { params }).then(res => res.data),
  
  /**
   * Semantic search with vector similarity (Issue #14)
   * Uses embeddings for natural language search
   */
  vectorSearch: (
    request: SemanticSearchRequest
  ): Promise<SemanticSearchResponse> =>
    api.post('/search', request).then(res => res.data),
  
  /**
   * Check semantic search service health
   */
  searchHealth: (): Promise<SearchHealthResponse> =>
    api.get('/search/health').then(res => res.data),
};

export default api;
