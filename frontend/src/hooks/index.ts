/**
 * Custom React Hooks
 * 
 * Centralized exports for all custom hooks used in the application.
 * These hooks integrate with TanStack Query for server state management.
 */

// Article hooks
export {
  useArticles,
  useArticle,
  useArticleStats,
  useSources,
  useCategories,
} from './useArticles';

// Semantic search hooks
export {
  useSemanticSearch,
  useSearchHealth,
} from './useSemanticSearch';

// Re-export types
export type { UseArticlesOptions, UseArticlesReturn } from './useArticles';
export type {
  UseSemanticSearchOptions,
  UseSemanticSearchReturn,
} from './useSemanticSearch';
