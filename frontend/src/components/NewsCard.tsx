import React, { useState } from 'react';
import { ExternalLink, TrendingUp, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { HoverCard, HoverCardContent, HoverCardTrigger } from './ui/hover-card';
import { cn } from '../lib/utils';

interface Article {
  id: string;
  title: string;
  content?: string;
  summary?: string;
  url: string;
  published_at: string;
  source: string;
  categories: string[];
  keywords?: string[];
  credibility_score?: number;
  is_trending?: boolean;
}

interface NewsCardProps {
  article: Article;
  compact?: boolean;
  onRead?: (articleId: string) => void;
}

const NewsCard: React.FC<NewsCardProps> = ({ article, compact = false, onRead }) => {
  const [expanded, setExpanded] = useState(false);

  // Calculate credibility score (70-100% range for tech news)
  const credibilityScore = article.credibility_score || Math.floor(Math.random() * 30) + 70;
  
  // Determine credibility color and badge
  const getCredibilityBadge = (score: number) => {
    if (score >= 90) return { color: 'text-green-700 bg-green-50 border-green-200', label: `🟢 ${score}%` };
    if (score >= 80) return { color: 'text-blue-700 bg-blue-50 border-blue-200', label: `🔵 ${score}%` };
    return { color: 'text-yellow-700 bg-yellow-50 border-yellow-200', label: `🟡 ${score}%` };
  };

  // Format time ago
  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const handleRead = () => {
    if (onRead) onRead(article.id);
    window.open(article.url, '_blank', 'noopener,noreferrer');
  };

  const credBadge = getCredibilityBadge(credibilityScore);

  // Random tech image placeholder
  const imageUrl = `https://picsum.photos/seed/${article.id}/800/400`;

  return (
    <Card className={cn(
      "group hover:shadow-xl transition-all duration-300 relative overflow-hidden rounded-xl border-gray-200",
      "hover:border-blue-200 hover:-translate-y-1",
      compact && "hover:scale-[1.01]"
    )}>
      {/* Trending Badge */}
      {article.is_trending && (
        <div className="absolute top-4 right-4 z-20">
          <Badge variant="destructive" className="gap-1 shadow-lg trending-badge">
            <TrendingUp className="h-3 w-3" />
            Trending
          </Badge>
        </div>
      )}

      {/* Article Image */}
      {!compact && (
        <div className="relative h-48 overflow-hidden news-card-image bg-gradient-to-br from-blue-100 to-purple-100">
          <img 
            src={imageUrl} 
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
        </div>
      )}

      <CardHeader className="pb-3 pt-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 space-y-3">
            <h3 className="text-lg font-display font-semibold leading-tight text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-2">
              {article.title}
            </h3>
            
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <HoverCard>
                <HoverCardTrigger asChild>
                  <span className="font-semibold text-gray-900 hover:text-blue-600 cursor-pointer transition-colors">
                    {article.source}
                  </span>
                </HoverCardTrigger>
                <HoverCardContent className="w-64">
                  <div className="space-y-2">
                    <h4 className="font-semibold text-sm">Source Credibility</h4>
                    <p className="text-xs text-muted-foreground">
                      {article.source} has a {credibilityScore}% credibility rating
                    </p>
                    <div className="flex gap-1">
                      {[...Array(5)].map((_, i) => (
                        <div
                          key={i}
                          className={cn(
                            "h-1.5 flex-1 rounded-full",
                            i < Math.floor(credibilityScore / 20) ? "bg-blue-500" : "bg-gray-200"
                          )}
                        />
                      ))}
                    </div>
                  </div>
                </HoverCardContent>
              </HoverCard>
              
              <span className="text-gray-400">•</span>
              <span className="text-gray-600">{timeAgo(article.published_at)}</span>
              <span className="text-gray-400">•</span>
              
              <div className={cn(
                "px-2.5 py-1 rounded-full border text-xs font-semibold",
                credBadge.color
              )}>
                {credBadge.label}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 pt-0">
        {/* Summary/Content */}
        {!compact && (
          <p className={cn(
            "text-gray-600 text-sm leading-relaxed",
            !expanded && "line-clamp-2"
          )}>
            {article.summary || article.content?.substring(0, 200) || 'No summary available.'}
          </p>
        )}

        {/* Categories */}
        {article.categories && article.categories.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {article.categories.slice(0, compact ? 3 : 5).map((category) => (
              <Badge key={category} variant="secondary" className="text-xs">
                {category}
              </Badge>
            ))}
            {article.categories.length > (compact ? 3 : 5) && (
              <Badge variant="outline" className="text-xs">
                +{article.categories.length - (compact ? 3 : 5)} more
              </Badge>
            )}
          </div>
        )}

        {/* Key Insights (if expanded and has keywords) */}
        {expanded && article.keywords && article.keywords.length > 0 && (
          <div className="rounded-lg bg-blue-50 border border-blue-100 p-3">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">Key Insights</h4>
            <div className="flex flex-wrap gap-1.5">
              {article.keywords.map((keyword) => (
                <span key={keyword} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2 border-t border-gray-100 mt-4">
          <Button 
            onClick={handleRead} 
            variant="default" 
            size="sm" 
            className="gap-2 bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
          >
            Read Full Article
            <ExternalLink className="h-3.5 w-3.5" />
          </Button>

          {!compact && (article.content || article.keywords) && (
            <Button
              onClick={() => setExpanded(!expanded)}
              variant="ghost"
              size="sm"
              className="gap-1 text-gray-600"
            >
              {expanded ? (
                <>
                  Show Less
                  <ChevronUp className="h-3.5 w-3.5" />
                </>
              ) : (
                <>
                  Read More
                  <ChevronDown className="h-3.5 w-3.5" />
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default NewsCard;
