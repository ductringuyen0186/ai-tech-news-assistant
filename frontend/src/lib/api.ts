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
  baseURL: '/api/v1',
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
};

export default api;
