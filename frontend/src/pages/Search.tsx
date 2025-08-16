import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchApi, articlesApi } from '@/lib/api.ts'
import { formatDate, truncateText } from '@/lib/utils.ts'
import { Search as SearchIcon, ExternalLink } from 'lucide-react'

export default function Search() {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState<'text' | 'semantic'>('text')
  const [submitted, setSubmitted] = useState(false)

  const { data: results, isLoading, error } = useQuery({
    queryKey: ['search', searchType, query],
    queryFn: () => {
      if (searchType === 'semantic') {
        return searchApi.semanticSearch({ query, limit: 20 })
      } else {
        return searchApi.textSearch({ query, limit: 20 })
      }
    },
    enabled: !!query && submitted,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      setSubmitted(true)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Search</h1>
        <p className="text-gray-600 mt-1">Search through articles using text or semantic search</p>
      </div>

      {/* Search Form */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Query
            </label>
            <div className="relative">
              <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                className="input pl-10"
                placeholder="Enter your search query..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search Type
            </label>
            <div className="flex space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  className="h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                  name="searchType"
                  value="text"
                  checked={searchType === 'text'}
                  onChange={(e) => setSearchType(e.target.value as 'text' | 'semantic')}
                />
                <span className="ml-2 text-sm text-gray-700">Text Search</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  className="h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                  name="searchType"
                  value="semantic"
                  checked={searchType === 'semantic'}
                  onChange={(e) => setSearchType(e.target.value as 'text' | 'semantic')}
                />
                <span className="ml-2 text-sm text-gray-700">Semantic Search</span>
              </label>
            </div>
          </div>

          <button type="submit" className="btn-primary">
            Search
          </button>
        </form>
      </div>

      {/* Results */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="text-gray-500 mt-4">Searching...</p>
        </div>
      )}

      {error && (
        <div className="card bg-red-50 border border-red-200">
          <p className="text-red-800">Error: {error.message}</p>
        </div>
      )}

      {results && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-900">
              Search Results ({results.total} found)
            </h2>
            <div className="text-sm text-gray-500">
              Using {searchType} search
            </div>
          </div>

          {results.articles.length ? (
            results.articles.map((article) => (
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
                  <span>{article.source}</span>
                  <span>•</span>
                  <span>{formatDate(article.published_at)}</span>
                  {article.author && (
                    <>
                      <span>•</span>
                      <span>{article.author}</span>
                    </>
                  )}
                </div>

                <p className="text-gray-700 leading-relaxed">
                  {truncateText(article.content, 300)}
                </p>

                {article.categories.length > 0 && (
                  <div className="mt-3 flex space-x-2">
                    {article.categories.slice(0, 3).map((category) => (
                      <span
                        key={category}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                      >
                        {category}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No results found for your query</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
