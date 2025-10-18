import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { FileText, Download } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

const ResearchMode: React.FC = () => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="text-center">
        <h2 className="text-3xl font-display font-bold text-blue-600 mb-2">
          Research Mode
        </h2>
        <p className="text-gray-600">
          Deep dive into topics with AI-powered research assistance
        </p>
      </div>

      {/* Main Research Card - Yellow Background */}
      <div className="bg-yellow-300 rounded-lg p-8 space-y-6">
        <div className="flex items-center gap-3">
          <FileText className="h-6 w-6 text-gray-700" />
          <h3 className="text-xl font-bold text-gray-900">Research Topic</h3>
        </div>
        
        <p className="text-gray-800 font-medium">
          Select articles to analyze, and our AI will generate comprehensive research notes, key findings, and exportable reports.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Research Input */}
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-6 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Research Topic</label>
              <input
                type="text"
                placeholder="e.g., AI Developments Q1 2025"
                className="w-full px-4 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <Button className="w-full bg-white hover:bg-gray-50 text-gray-900 border border-gray-300">
              Click to start new research
            </Button>
          </div>

          {/* Right: Results */}
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-6 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900">AI Developments Q1 2025</h4>
              <Badge variant="secondary">3 articles</Badge>
            </div>
            
            <Button variant="outline" className="w-full gap-2 bg-yellow-300 hover:bg-yellow-400 text-gray-900 border-gray-900">
              <Download className="h-4 w-4" />
              Export Markdown
            </Button>
          </div>
        </div>
      </div>

      {/* Key Findings Section - Yellow Background */}
      <div className="bg-yellow-300 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-bold text-gray-900">Key Findings</h3>
        
        <div className="space-y-3">
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4">
            <p className="font-medium text-gray-700">Emerging Trend</p>
          </div>
          
          <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4">
            <p className="font-medium text-gray-700">Market Impact</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearchMode;
