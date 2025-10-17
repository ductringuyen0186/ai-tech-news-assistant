import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { FileText, Download } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

const ResearchMode: React.FC = () => {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-3xl font-display font-bold text-gradient mb-2">
          Research Mode
        </h2>
        <p className="text-muted-foreground">
          Deep dive into topics with AI-powered research assistance
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Research Topic
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">
            Select articles to analyze, and our AI will generate comprehensive research notes,
            key findings, and exportable reports.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-2 border-dashed hover:border-primary cursor-pointer transition-colors">
              <CardContent className="p-6 text-center">
                <p className="text-muted-foreground">Click to start new research</p>
              </CardContent>
            </Card>

            <Card className="border-2 border-blue-200 bg-blue-50">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-sm">AI Developments Q1 2025</h4>
                  <Badge variant="info">3 articles</Badge>
                </div>
                <p className="text-xs text-muted-foreground mb-3">Last updated 2h ago</p>
                <Button size="sm" variant="outline" className="w-full gap-2">
                  <Download className="h-3 w-3" />
                  Export Markdown
                </Button>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Key Findings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
              <h4 className="font-semibold text-sm mb-1">Emerging Trend</h4>
              <p className="text-sm text-muted-foreground">
                AI models are becoming more efficient with smaller parameter counts
              </p>
            </div>
            <div className="p-3 rounded-lg bg-purple-50 border border-purple-100">
              <h4 className="font-semibold text-sm mb-1">Market Impact</h4>
              <p className="text-sm text-muted-foreground">
                Cloud providers are investing heavily in AI infrastructure
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResearchMode;
