import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { TrendingUp, Users, Zap } from 'lucide-react';
import { Badge } from './ui/badge';

const DigestView: React.FC = () => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="text-center">
        <h2 className="text-3xl font-display font-bold text-blue-600 mb-2">
          Daily Digest
        </h2>
        <p className="text-gray-600">
          Your personalized summary of today's top tech news
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-blue-500 text-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-5 w-5" />
            <h3 className="font-semibold">Trending Topics</h3>
          </div>
          <div className="text-4xl font-bold">12</div>
          <p className="text-sm opacity-90 mt-1">Hot discussions today</p>
        </div>

        <div className="bg-purple-500 text-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="h-5 w-5" />
            <h3 className="font-semibold">Breaking News</h3>
          </div>
          <div className="text-4xl font-bold">8</div>
          <p className="text-sm opacity-90 mt-1">Major updates</p>
        </div>

        <div className="bg-green-500 text-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-3">
            <Users className="h-5 w-5" />
            <h3 className="font-semibold">Community Picks</h3>
          </div>
          <div className="text-4xl font-bold">25</div>
          <p className="text-sm opacity-90 mt-1">Top-rated articles</p>
        </div>
      </div>

      {/* Today's Highlights - Yellow Background */}
      <div className="bg-yellow-300 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Today's Highlights</h3>
        
        <div className="space-y-3">
          {[
            { title: 'AI Breakthrough in Natural Language Understanding', category: 'AI', score: 95 },
            { title: 'New Security Vulnerability Affects Major Cloud Providers', category: 'Security', score: 92 },
            { title: 'Quantum Computing Makes Significant Progress', category: 'Quantum', score: 88 },
          ].map((item, idx) => (
            <div key={idx} className="flex items-start justify-between p-4 rounded-lg bg-white/80 backdrop-blur-sm hover:bg-white transition-colors">
              <div className="flex-1">
                <h4 className="font-semibold mb-2 text-gray-900">{item.title}</h4>
                <Badge className="text-xs bg-blue-100 text-blue-700">{item.category}</Badge>
              </div>
              <div className="text-sm font-semibold text-green-600">
                {item.score}% credible
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DigestView;
