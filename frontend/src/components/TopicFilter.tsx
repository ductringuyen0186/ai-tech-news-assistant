import React from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Check } from 'lucide-react';
import { cn } from '../lib/utils';

interface TopicFilterProps {
  topics: string[];
  selectedTopics: string[];
  onToggleTopic: (topic: string) => void;
  onSave?: () => void;
  showSave?: boolean;
}

const TOPIC_COLORS: Record<string, string> = {
  'AI': 'bg-blue-100 text-blue-700 hover:bg-blue-200 border-blue-200',
  'Machine Learning': 'bg-purple-100 text-purple-700 hover:bg-purple-200 border-purple-200',
  'Cloud': 'bg-cyan-100 text-cyan-700 hover:bg-cyan-200 border-cyan-200',
  'Security': 'bg-red-100 text-red-700 hover:bg-red-200 border-red-200',
  'DevOps': 'bg-green-100 text-green-700 hover:bg-green-200 border-green-200',
  'Web Development': 'bg-orange-100 text-orange-700 hover:bg-orange-200 border-orange-200',
  'Mobile': 'bg-pink-100 text-pink-700 hover:bg-pink-200 border-pink-200',
  'Data Science': 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200 border-indigo-200',
  'Blockchain': 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200 border-yellow-200',
  'IoT': 'bg-teal-100 text-teal-700 hover:bg-teal-200 border-teal-200',
};

const TopicFilter: React.FC<TopicFilterProps> = ({
  topics,
  selectedTopics,
  onToggleTopic,
  onSave,
  showSave = false,
}) => {
  const getTopicColor = (topic: string) => {
    return TOPIC_COLORS[topic] || 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-gray-200';
  };

  const isSelected = (topic: string) => selectedTopics.includes(topic);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-display font-semibold text-lg">Filter by Topics</h3>
        {showSave && selectedTopics.length > 0 && (
          <Button onClick={onSave} size="sm" variant="gradient">
            Save Preferences
          </Button>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {topics.map((topic) => {
          const selected = isSelected(topic);
          return (
            <button
              key={topic}
              onClick={() => onToggleTopic(topic)}
              className={cn(
                "relative px-4 py-2 rounded-full border-2 font-medium text-sm transition-all duration-200",
                "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                getTopicColor(topic),
                selected && "ring-2 ring-offset-2",
                selected && "ring-primary shadow-md scale-105"
              )}
            >
              <span className="flex items-center gap-2">
                {topic}
                {selected && (
                  <Check className="h-4 w-4 animate-in zoom-in duration-200" />
                )}
              </span>
            </button>
          );
        })}
      </div>

      {selectedTopics.length > 0 && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="font-medium">{selectedTopics.length} topics selected</span>
          <Button
            onClick={() => selectedTopics.forEach(onToggleTopic)}
            variant="ghost"
            size="sm"
            className="h-auto py-0 px-2"
          >
            Clear all
          </Button>
        </div>
      )}
    </div>
  );
};

export default TopicFilter;
