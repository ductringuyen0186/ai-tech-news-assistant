import { useQuery } from '@tanstack/react-query';
import { articlesApi, healthApi } from '@/lib/api.ts';
import { BarChart, TrendingUp, FileText, Activity } from 'lucide-react';

export default function Dashboard() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.getHealth,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: articlesApi.getArticleStats,
    refetchInterval: 60000, // Refetch every minute
  });

  const { data: recentArticles } = useQuery({
    queryKey: ['articles', 'recent'],
    queryFn: () => articlesApi.getArticles({ limit: 5 }),
  });

  const statsCards = [
    {
      title: 'Total Articles',
      value: stats?.total_articles || 0,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'With Summaries',
      value: stats?.articles_with_summaries || 0,
      icon: BarChart,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'With Embeddings',
      value: stats?.articles_with_embeddings || 0,
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
    {
      title: 'Recent Articles',
      value: stats?.recent_articles || 0,
      icon: Activity,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Overview of your AI Tech News Assistant
        </p>
      </div>

      {/* System Status */}
      <div className="card">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">System Status</h2>
          <div
            className={`
            inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
            ${
              health?.status === 'healthy'
                ? 'bg-green-100 text-green-800'
                : health?.status === 'degraded'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
            }
          `}
          >
            {health?.status || 'Unknown'}
          </div>
        </div>

        {health?.components && (
          <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(health.components).map(([name, component]) => (
              <div key={name} className="flex items-center space-x-2">
                <div
                  className={`
                  h-2 w-2 rounded-full
                  ${
                    component.status === 'healthy'
                      ? 'bg-green-500'
                      : component.status === 'degraded'
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                  }
                `}
                />
                <span className="text-sm text-gray-600 capitalize">{name}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statsCards.map(stat => (
          <div key={stat.title} className="card">
            <div className="flex items-center">
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">
                  {stat.title}
                </p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stat.value}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Articles */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Recent Articles
        </h2>
        {recentArticles?.articles.length ? (
          <div className="space-y-4">
            {recentArticles.articles.map(article => (
              <div
                key={article.id}
                className="border-b border-gray-200 pb-4 last:border-0"
              >
                <h3 className="font-medium text-gray-900 mb-1">
                  {article.title}
                </h3>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>{article.source}</span>
                  <span>•</span>
                  <span>
                    {new Date(article.published_at).toLocaleDateString()}
                  </span>
                  {article.summary && (
                    <>
                      <span>•</span>
                      <span className="text-green-600">Summarized</span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No recent articles found</p>
        )}
      </div>

      {/* Top Sources */}
      {stats?.top_sources && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Top Sources
          </h2>
          <div className="space-y-3">
            {stats.top_sources.slice(0, 5).map(source => (
              <div
                key={source.source}
                className="flex items-center justify-between"
              >
                <span className="text-sm font-medium text-gray-900">
                  {source.source}
                </span>
                <span className="text-sm text-gray-500">
                  {source.count} articles
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
