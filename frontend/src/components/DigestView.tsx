import { Mail, TrendingUp, Calendar, BarChart3 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";

interface DigestViewProps {
  digest: {
    date: string;
    topStories: Array<{
      id: string;
      title: string;
      source: string;
      summaryShort: string;
      category: string[];
    }>;
    categoryBreakdown: Record<string, number>;
    trendingTopics: Array<{
      id: string;
      title: string;
      category: string[];
    }>;
  };
}

export function DigestView({ digest }: DigestViewProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
        <CardHeader>
          <div className="flex items-center gap-3">
            <Mail className="w-8 h-8 text-blue-600" />
            <div>
              <CardTitle className="text-2xl">Daily Tech Digest</CardTitle>
              <CardDescription className="flex items-center gap-2 mt-1">
                <Calendar className="w-4 h-4" />
                {formatDate(digest.date)}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Top Stories */}
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">📰 Top Stories Today</CardTitle>
          <CardDescription>
            The most important tech news you shouldn't miss
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {digest.topStories.map((story, idx) => (
              <div key={story.id} className="border-l-4 border-blue-500 pl-4 py-2">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <h3 className="mb-1">{story.title}</h3>
                    <p className="text-sm text-gray-600 mb-2">{story.summaryShort}</p>
                    <div className="flex gap-2">
                      <Badge variant="outline" className="text-xs">
                        {story.source}
                      </Badge>
                      {story.category.slice(0, 2).map((cat) => (
                        <Badge key={cat} variant="secondary" className="text-xs">
                          {cat}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Trending Topics */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-500" />
              <CardTitle>🔥 Trending Now</CardTitle>
            </div>
            <CardDescription>Most discussed topics today</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {digest.trendingTopics.map((topic) => (
                <div key={topic.id} className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                  <p className="text-sm mb-2">{topic.title}</p>
                  <div className="flex flex-wrap gap-1">
                    {topic.category.map((cat) => (
                      <Badge key={cat} variant="outline" className="text-xs">
                        {cat}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Category Breakdown */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-green-500" />
              <CardTitle>📊 Coverage by Topic</CardTitle>
            </div>
            <CardDescription>News distribution across categories</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(digest.categoryBreakdown)
                .sort(([, a], [, b]) => b - a)
                .slice(0, 6)
                .map(([category, count]) => (
                  <div key={category} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">{category}</span>
                        <span className="text-sm text-gray-500">{count} articles</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full transition-all"
                          style={{
                            width: `${(count / Math.max(...Object.values(digest.categoryBreakdown))) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Email Subscribe CTA */}
      <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
        <CardContent className="pt-6">
          <div className="text-center">
            <Mail className="w-12 h-12 text-purple-600 mx-auto mb-3" />
            <h3 className="text-xl mb-2">Get Your Daily Digest via Email</h3>
            <p className="text-gray-600 mb-4">
              Never miss important tech news. Receive a personalized digest every morning.
            </p>
            <Button size="lg" className="bg-purple-600 hover:bg-purple-700">
              Subscribe to Daily Digest
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
