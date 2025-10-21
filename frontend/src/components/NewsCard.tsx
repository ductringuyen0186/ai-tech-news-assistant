import { useState } from "react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { ExternalLink, TrendingUp, Clock, ChevronDown, ChevronUp, Shield, Info } from "lucide-react";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "./ui/hover-card";

interface NewsCardProps {
  article: {
    id: string;
    title: string;
    source: string;
    url: string;
    publishedAt: string;
    imageUrl: string;
    category: string[];
    summaryShort: string;
    summaryMedium: string;
    keyInsights: string[];
    sentiment: string;
    trending: boolean;
    credibilityScore?: number;
    sourcesUsed?: string[];
  };
  viewMode: "compact" | "detailed";
}

export function NewsCard({ article, viewMode }: NewsCardProps) {
  const [expanded, setExpanded] = useState(false);

  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const hours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (hours < 1) return "Just now";
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const sentimentColor = {
    positive: "text-green-600",
    negative: "text-red-600",
    mixed: "text-yellow-600"
  }[article.sentiment] || "text-gray-600";

  const getCredibilityColor = (score: number) => {
    if (score >= 90) return "text-green-600";
    if (score >= 70) return "text-blue-600";
    if (score >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  const getCredibilityLabel = (score: number) => {
    if (score >= 90) return "Highly Reliable";
    if (score >= 70) return "Reliable";
    if (score >= 50) return "Moderate";
    return "Limited";
  };

  if (viewMode === "compact") {
    return (
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                {article.trending && (
                  <Badge variant="default" className="bg-orange-500">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    Trending
                  </Badge>
                )}
                <span className="text-sm text-gray-500">{article.source}</span>
                {article.credibilityScore !== undefined && (
                  <>
                    <span className="text-sm text-gray-400">•</span>
                    <HoverCard>
                      <HoverCardTrigger asChild>
                        <span className={`text-sm flex items-center gap-1 cursor-help ${getCredibilityColor(article.credibilityScore)}`}>
                          <Shield className="w-3 h-3" />
                          {article.credibilityScore}%
                        </span>
                      </HoverCardTrigger>
                      <HoverCardContent className="w-80">
                        <div className="space-y-2">
                          <h4 className="font-semibold flex items-center gap-2">
                            <Shield className="w-4 h-4" />
                            Source Credibility
                          </h4>
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">Reliability:</span>
                              <span className={`text-sm font-semibold ${getCredibilityColor(article.credibilityScore)}`}>
                                {getCredibilityLabel(article.credibilityScore)}
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${article.credibilityScore >= 90 ? 'bg-green-600' : article.credibilityScore >= 70 ? 'bg-blue-600' : article.credibilityScore >= 50 ? 'bg-yellow-600' : 'bg-red-600'}`}
                                style={{ width: `${article.credibilityScore}%` }}
                              />
                            </div>
                          </div>
                          {article.sourcesUsed && article.sourcesUsed.length > 0 && (
                            <div className="pt-2 border-t">
                              <p className="text-sm font-semibold mb-1">Sources Used:</p>
                              <div className="flex flex-wrap gap-1">
                                {article.sourcesUsed.map((src, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    {src}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </HoverCardContent>
                    </HoverCard>
                  </>
                )}
                <span className="text-sm text-gray-400">•</span>
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {timeAgo(article.publishedAt)}
                </span>
              </div>
              <CardTitle className="text-lg leading-snug mb-2">{article.title}</CardTitle>
              <CardDescription>{article.summaryShort}</CardDescription>
            </div>
            <ImageWithFallback
              src={article.imageUrl}
              alt={article.title}
              className="w-24 h-24 object-cover rounded-md flex-shrink-0"
            />
          </div>
        </CardHeader>
        <CardFooter className="pt-0 pb-4 flex flex-wrap gap-2">
          {article.category.map((cat) => (
            <Badge key={cat} variant="outline" className="text-xs">
              {cat}
            </Badge>
          ))}
          <Button variant="ghost" size="sm" className="ml-auto" asChild>
            <a href={article.url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="w-4 h-4" />
            </a>
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <ImageWithFallback
        src={article.imageUrl}
        alt={article.title}
        className="w-full h-48 object-cover rounded-t-lg"
      />
      <CardHeader>
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          {article.trending && (
            <Badge variant="default" className="bg-orange-500">
              <TrendingUp className="w-3 h-3 mr-1" />
              Trending
            </Badge>
          )}
          <span className="text-sm text-gray-500">{article.source}</span>
          {article.credibilityScore !== undefined && (
            <>
              <span className="text-sm text-gray-400">•</span>
              <HoverCard>
                <HoverCardTrigger asChild>
                  <span className={`text-sm flex items-center gap-1 cursor-help ${getCredibilityColor(article.credibilityScore)}`}>
                    <Shield className="w-3 h-3" />
                    {article.credibilityScore}%
                  </span>
                </HoverCardTrigger>
                <HoverCardContent className="w-80">
                  <div className="space-y-2">
                    <h4 className="font-semibold flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      Source Credibility
                    </h4>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Reliability:</span>
                        <span className={`text-sm font-semibold ${getCredibilityColor(article.credibilityScore)}`}>
                          {getCredibilityLabel(article.credibilityScore)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${article.credibilityScore >= 90 ? 'bg-green-600' : article.credibilityScore >= 70 ? 'bg-blue-600' : article.credibilityScore >= 50 ? 'bg-yellow-600' : 'bg-red-600'}`}
                          style={{ width: `${article.credibilityScore}%` }}
                        />
                      </div>
                    </div>
                    {article.sourcesUsed && article.sourcesUsed.length > 0 && (
                      <div className="pt-2 border-t">
                        <p className="text-sm font-semibold mb-1">Sources Used:</p>
                        <div className="flex flex-wrap gap-1">
                          {article.sourcesUsed.map((src, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {src}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </HoverCardContent>
              </HoverCard>
            </>
          )}
          <span className="text-sm text-gray-400">•</span>
          <span className="text-sm text-gray-500 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeAgo(article.publishedAt)}
          </span>
        </div>
        <CardTitle className="text-xl leading-snug">{article.title}</CardTitle>
        <CardDescription className="mt-2">{article.summaryShort}</CardDescription>
      </CardHeader>
      <CardContent>
        {expanded ? (
          <>
            <p className="text-gray-700 mb-4">{article.summaryMedium}</p>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Key Insights</h4>
              <ul className="space-y-1">
                {article.keyInsights.map((insight, idx) => (
                  <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="w-full mt-4"
              onClick={() => setExpanded(false)}
            >
              Show Less <ChevronUp className="w-4 h-4 ml-2" />
            </Button>
          </>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            className="w-full"
            onClick={() => setExpanded(true)}
          >
            Read More <ChevronDown className="w-4 h-4 ml-2" />
          </Button>
        )}
      </CardContent>
      <CardFooter className="flex flex-wrap gap-2 border-t pt-4">
        <div className="flex flex-wrap gap-2 flex-1">
          {article.category.map((cat) => (
            <Badge key={cat} variant="outline">
              {cat}
            </Badge>
          ))}
        </div>
        <Button variant="default" size="sm" asChild>
          <a href={article.url} target="_blank" rel="noopener noreferrer">
            Read Full Article <ExternalLink className="w-4 h-4 ml-2" />
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
}
