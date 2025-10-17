import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { TrendingUp, Users, Zap } from 'lucide-react';
import { Badge } from './ui/badge';

const DigestView: React.FC = () => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-3xl font-display font-bold text-gradient mb-2">
          Daily Digest
        </h2>
        <p className="text-muted-foreground">
          Your personalized summary of today's top tech news
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="gradient-primary text-white">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingUp className="h-5 w-5" />
              Trending Topics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">12</div>
            <p className="text-sm opacity-90 mt-1">Hot discussions today</p>
          </CardContent>
        </Card>

        <Card className="gradient-accent text-white">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Zap className="h-5 w-5" />
              Breaking News
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">8</div>
            <p className="text-sm opacity-90 mt-1">Major updates</p>
          </CardContent>
        </Card>

        <Card className="bg-green-500 text-white">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Users className="h-5 w-5" />
              Community Picks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">25</div>
            <p className="text-sm opacity-90 mt-1">Top-rated articles</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Today's Highlights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { title: 'AI Breakthrough in Natural Language Understanding', category: 'AI', score: 95 },
              { title: 'New Security Vulnerability Affects Major Cloud Providers', category: 'Security', score: 92 },
              { title: 'Quantum Computing Makes Significant Progress', category: 'Quantum', score: 88 },
            ].map((item, idx) => (
              <div key={idx} className="flex items-start justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex-1">
                  <h4 className="font-semibold mb-1">{item.title}</h4>
                  <Badge variant="secondary" className="text-xs">{item.category}</Badge>
                </div>
                <div className="text-sm font-semibold text-green-600">
                  {item.score}% credible
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DigestView;
