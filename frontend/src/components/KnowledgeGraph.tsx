import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Network, Zap } from 'lucide-react';

const KnowledgeGraph: React.FC = () => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="text-center">
        <h2 className="text-3xl font-display font-bold text-blue-600 mb-2">
          Knowledge Graph
        </h2>
        <p className="text-gray-600">
          Explore connections between technologies, companies, and people
        </p>
      </div>

      {/* Main Graph Card - Yellow Background */}
      <div className="bg-yellow-300 rounded-lg p-8">
        <div className="flex items-center gap-3 mb-6">
          <Network className="h-6 w-6 text-gray-700" />
          <h3 className="text-xl font-bold text-gray-900">Tech Ecosystem Map</h3>
        </div>

        {/* Graph visualization area */}
        <div className="bg-white/80 backdrop-blur-sm rounded-lg p-12 min-h-[500px] flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-20 h-20 rounded-full bg-blue-600 flex items-center justify-center">
            <Zap className="h-10 w-10 text-white" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900">Interactive Graph Coming Soon</h3>
          <p className="text-gray-700 max-w-md font-medium">
            Visualize relationships between companies, technologies, and key figures in the tech industry. This feature will use force-directed graphs to show connections discovered from news articles.
          </p>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph;
