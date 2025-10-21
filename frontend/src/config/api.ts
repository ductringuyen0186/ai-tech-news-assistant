/**
 * API Configuration for FastAPI Backend
 * 
 * This file configures the connection to the FastAPI backend
 * instead of Supabase.
 */

// Get API base URL from environment or use default
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
  // News endpoints
  news: '/api/news',
  newsById: (id: string) => `/api/news/${id}`,
  newsSearch: '/api/news/search',
  newsIngest: '/api/news/ingest',
  newsSources: '/api/news/sources',
  newsStats: '/api/news/stats',
  
  // Search endpoints
  search: '/api/search',
  semanticSearch: '/api/search/semantic',
  
  // Summarization endpoints
  summarize: '/api/summarization/summarize',
  summarizeBatch: '/api/summarization/batch',
  
  // Embeddings endpoints
  embeddings: '/api/embeddings/generate',
  embeddingsStats: '/api/embeddings/stats',
  
  // Health check
  health: '/health',
  healthDetailed: '/health/detailed',
};

/**
 * Fetch wrapper with error handling
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, {
    ...defaultOptions,
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP error! status: ${response.status}`,
    }));
    throw new Error(error.detail || `API request failed: ${response.statusText}`);
  }

  return response.json();
}
