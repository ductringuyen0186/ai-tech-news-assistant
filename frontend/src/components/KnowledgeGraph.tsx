import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Network, Zap } from 'lucide-react';

const KnowledgeGraph: React.FC = () => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-3xl font-display font-bold text-gradient mb-2">
          Knowledge Graph
        </h2>
        <p className="text-muted-foreground">
          Explore connections between technologies, companies, and people
        </p>
      </div>

      <Card className="h-[600px]">
        <CardHeader className="border-b">
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5 text-primary" />
            Tech Ecosystem Map
          </CardTitle>
        </CardHeader>
        <CardContent className="h-full flex items-center justify-center">
          <div className="text-center space-y-4">
            <div className="w-24 h-24 mx-auto rounded-full gradient-primary flex items-center justify-center">
              <Zap className="h-12 w-12 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-2">Interactive Graph Coming Soon</h3>
              <p className="text-muted-foreground max-w-md">
                Visualize relationships between companies, technologies, and key figures in the tech industry.
                This feature will use force-directed graphs to show connections discovered from news articles.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default KnowledgeGraph;
