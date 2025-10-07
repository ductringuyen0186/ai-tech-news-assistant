import axios from 'axios';
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
} from '../types/api';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
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
  error => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const healthApi = {
  getHealth: (): Promise<HealthStatus> =>
    api.get('/health').then(res => res.data),

  ping: (): Promise<{ message: string; timestamp: string }> =>
    api.get('/').then(res => res.data),
};

export const articlesApi = {
  getArticles: (params?: ArticleSearchParams): Promise<SearchResponse> =>
    api.get('/articles', { params }).then(res => res.data),

  getArticle: (id: string): Promise<Article> =>
    api.get(`/articles/${id}`).then(res => res.data),

  searchArticles: (params: ArticleSearchParams): Promise<SearchResponse> =>
    api.post('/search', { query: params.query || '', limit: params.limit || 10 }).then(res => res.data),

  getSources: (): Promise<SourcesResponse> =>
    api.get('/articles').then(res => ({ sources: {}, count: 0 })),

  getCategories: (): Promise<CategoriesResponse> =>
    api.get('/articles').then(res => ({ categories: [], count: 0 })),

  getArticleStats: (): Promise<StatsResponse> =>
    api.get('/articles').then(res => ({ 
      total_articles: res.data.total || 0, 
      articles_with_summaries: 0,
      articles_with_embeddings: 0,
      top_sources: [],
      recent_articles: 0
    })),
};

export const summaryApi = {
  summarizeContent: (
    request: SummarizationRequest
  ): Promise<SummarizationResponse> =>
    api.post('/summarize', { text: request.content, max_length: request.max_length }).then(res => res.data),

  summarizeArticle: (
    articleId: string,
    params?: { max_length?: number }
  ): Promise<SummarizationResponse> =>
    api.post('/summarize', { text: `Article ${articleId}`, max_length: params?.max_length || 200 }).then(res => res.data),
};

export const searchApi = {
  textSearch: (params: ArticleSearchParams): Promise<SearchResponse> =>
    api.post('/search', { query: params.query || '', limit: params.limit || 10 }).then(res => res.data),

  semanticSearch: (
    params: ArticleSearchParams & { query: string }
  ): Promise<SearchResponse> =>
    api.post('/search', { query: params.query, limit: params.limit || 10 }).then(res => res.data),
};

export default api;
