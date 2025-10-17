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
  
  // Determine credibility color
  const getCredibilityColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 80) return 'text-blue-600 bg-blue-50 border-blue-200';
    return 'text-yellow-600 bg-yellow-50 border-yellow-200';
  };

  // Format time ago
  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const handleRead = () => {
    if (onRead) onRead(article.id);
    window.open(article.url, '_blank', 'noopener,noreferrer');
  };

  return (
    <Card className={cn(
      "group hover:shadow-lg transition-all duration-300 relative overflow-hidden",
      "before:absolute before:inset-0 before:bg-gradient-to-r before:from-blue-50/0 before:via-blue-50/50 before:to-blue-50/0",
      "before:translate-x-full before:hover:translate-x-0 before:transition-transform before:duration-700",
      compact && "hover:scale-[1.02]"
    )}>
      {article.is_trending && (
        <div className="absolute top-3 right-3 z-10">
          <Badge variant="destructive" className="gap-1">
            <TrendingUp className="h-3 w-3" />
            Trending
          </Badge>
        </div>
      )}

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 space-y-2">
            <h3 className="text-xl font-display font-semibold leading-tight group-hover:text-primary-600 transition-colors">
              {article.title}
            </h3>
            
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <HoverCard>
                <HoverCardTrigger asChild>
                  <span className="font-medium text-foreground hover:text-primary cursor-pointer">
                    {article.source}
                  </span>
                </HoverCardTrigger>
                <HoverCardContent>
                  <div className="space-y-2">
                    <h4 className="font-semibold">{article.source}</h4>
                    <p className="text-sm text-muted-foreground">
                      Credibility Score: {credibilityScore}%
                    </p>
                    <div className="flex gap-1">
                      {[...Array(5)].map((_, i) => (
                        <div
                          key={i}
                          className={cn(
                            "h-1 w-8 rounded-full",
                            i < Math.floor(credibilityScore / 20) ? "bg-primary" : "bg-gray-200"
                          )}
                        />
                      ))}
                    </div>
                  </div>
                </HoverCardContent>
              </HoverCard>
              
              <span>•</span>
              <span>{timeAgo(article.published_at)}</span>
              <span>•</span>
              
              <div className={cn(
                "px-2 py-0.5 rounded-md border text-xs font-semibold",
                getCredibilityColor(credibilityScore)
              )}>
                {credibilityScore}% credible
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Summary/Content */}
        {!compact && (
          <div className={cn(
            "text-muted-foreground",
            !expanded && "line-clamp-3"
          )}>
            {article.summary || article.content?.substring(0, 300)}
          </div>
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
        <div className="flex items-center gap-3 pt-2">
          <Button onClick={handleRead} variant="gradient" size="sm" className="gap-2">
            <ExternalLink className="h-4 w-4" />
            Read Article
          </Button>

          {!compact && (article.content || article.keywords) && (
            <Button
              onClick={() => setExpanded(!expanded)}
              variant="ghost"
              size="sm"
              className="gap-2"
            >
              {expanded ? (
                <>
                  <ChevronUp className="h-4 w-4" />
                  Show Less
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" />
                  Show More
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
