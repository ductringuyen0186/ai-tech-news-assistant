import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { articlesApi } from '../lib/api'
import { formatDate, truncateText } from '../lib/utils'
import { ExternalLink, Calendar, User, Tag } from 'lucide-react'

export default function Articles() {
  const [searchParams, setSearchParams] = useState({
    limit: 20,
    offset: 0,
    source: '',
    category: '',
  })

  const { data: articles, isLoading } = useQuery({
    queryKey: ['articles', searchParams],
    queryFn: () => articlesApi.getArticles(searchParams),
  })

  const { data: sourcesData, isLoading: isSourcesLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: articlesApi.getSources,
  })

  const { data: categoriesData, isLoading: isCategoriesLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: articlesApi.getCategories,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Articles</h1>
        <p className="text-gray-600 mt-1">Browse and manage your articles</p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Source
            </label>
            <select 
              className="input"
              value={searchParams.source}
              onChange={(e) => setSearchParams(prev => ({ ...prev, source: e.target.value }))}
              disabled={isSourcesLoading}
            >
              <option value="">All Sources</option>
              {isSourcesLoading && <option disabled>Loading sources...</option>}
              {sourcesData?.sources && Object.keys(sourcesData.sources).map((sourceKey) => (
                <option key={sourceKey} value={sourceKey}>
                  {sourcesData.sources[sourceKey].name || sourceKey}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select 
              className="input"
              value={searchParams.category}
              onChange={(e) => setSearchParams(prev => ({ ...prev, category: e.target.value }))}
              disabled={isCategoriesLoading}
            >
              <option value="">All Categories</option>
              {isCategoriesLoading && <option disabled>Loading categories...</option>}
              {categoriesData?.categories && categoriesData.categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Limit
            </label>
            <select 
              className="input"
              value={searchParams.limit}
              onChange={(e) => setSearchParams(prev => ({ ...prev, limit: Number(e.target.value) }))}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>
      </div>

      {/* Articles List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="text-gray-500 mt-4">Loading articles...</p>
          </div>
        ) : articles?.articles.length ? (
          articles.articles.map((article) => (
            <div key={article.id} className="card hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-semibold text-gray-900 leading-tight">
                  {article.title}
                </h3>
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-4 text-primary-600 hover:text-primary-700"
                >
                  <ExternalLink className="h-5 w-5" />
                </a>
              </div>

              <div className="flex items-center space-x-4 text-sm text-gray-500 mb-3">
                <div className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  {formatDate(article.published_at)}
                </div>
                {article.author && (
                  <div className="flex items-center">
                    <User className="h-4 w-4 mr-1" />
                    {article.author}
                  </div>
                )}
                <span>{article.source}</span>
              </div>

              {article.categories.length > 0 && (
                <div className="flex items-center mb-3">
                  <Tag className="h-4 w-4 mr-2 text-gray-400" />
                  <div className="flex space-x-2">
                    {article.categories.slice(0, 3).map((category) => (
                      <span
                        key={category}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                      >
                        {category}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-gray-700 leading-relaxed">
                {truncateText(article.content, 300)}
              </p>

              {article.summary && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm font-medium text-green-800 mb-1">AI Summary:</p>
                  <p className="text-green-700 text-sm">{article.summary}</p>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">No articles found</p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {articles && articles.total > searchParams.limit && (
        <div className="flex justify-center">
          <div className="flex space-x-2">
            <button
              className="btn-secondary"
              disabled={searchParams.offset === 0}
              onClick={() => setSearchParams(prev => ({ 
                ...prev, 
                offset: Math.max(0, prev.offset - prev.limit) 
              }))}
            >
              Previous
            </button>
            <button
              className="btn-secondary"
              disabled={searchParams.offset + searchParams.limit >= articles.total}
              onClick={() => setSearchParams(prev => ({ 
                ...prev, 
                offset: prev.offset + prev.limit 
              }))}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
