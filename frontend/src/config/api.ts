/**
 * API Configuration for FastAPI Backend
 *
 * Single source of truth for backend URLs and endpoint paths.
 */

const getApiBaseUrl = (): string => {
  const viteEnv = (import.meta as any).env;
  if (viteEnv?.VITE_API_BASE_URL) {
    return viteEnv.VITE_API_BASE_URL;
  }
  if (
    typeof window !== "undefined" &&
    window.location.hostname.includes("vercel.app")
  ) {
    return "https://ai-tech-news-assistant-backend.onrender.com";
  }
  return "http://localhost:8000";
};

export const API_BASE_URL = getApiBaseUrl();

export const API_ENDPOINTS = {
  // News endpoints
  news: "/api/news",
  newsById: (id: string) => `/api/news/${id}`,
  newsSearch: "/api/news/search",
  newsIngest: "/api/news/ingest",
  newsSources: "/api/news/sources",
  newsStats: "/api/news/stats",
  newsCategories: "/api/news/categories",

  // Search endpoints
  search: "/api/search",
  semanticSearch: "/api/search/semantic",

  // Agentic research endpoint (POST returns text/event-stream)
  research: "/api/research",

  // Summarization endpoints (backend prefix is /api/summarize)
  summarize: "/api/summarize/",
  summarizeBatch: "/api/summarize/batch",
  summarizeArticle: (id: string) => `/api/summarize/article/${id}`,
  summarizeStatus: "/api/summarize/status",

  // Ingestion + orchestration endpoints
  ingest: "/api/ingest/",
  ingestStatus: "/api/ingest/status",
  ingestStats: "/api/ingest/stats",
  summarizePending: "/api/ingest/summarize-pending",

  // Embeddings endpoints
  embeddings: "/api/embeddings/generate",
  embeddingsStats: "/api/embeddings/stats",

  // Settings (user preferences persisted server-side)
  settings: "/api/settings/",

  // Knowledge graph (entity-extraction backed graph view)
  knowledgeGraph: "/api/knowledge-graph/",

  // Daily digest (top stories + breakdown + trending built from DB)
  digest: "/api/digest/",

  // Saved research (M3.M5 — persisted research reports)
  savedResearch: "/api/saved-research",
  savedResearchById: (id: number) => `/api/saved-research/${id}`,

  // Health check
  health: "/health",
  healthDetailed: "/health/detailed",
};

/**
 * Fetch wrapper with error handling.
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultOptions: RequestInit = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  };

  const response = await fetch(url, { ...defaultOptions, ...options });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return (await response.json()) as T;
}
