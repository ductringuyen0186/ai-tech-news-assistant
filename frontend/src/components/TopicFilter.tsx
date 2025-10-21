import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Checkbox } from "./ui/checkbox";
import { Filter, X, Loader2, Check } from "lucide-react";

interface TopicFilterProps {
  selectedCategories: string[];
  onCategoriesChange: (categories: string[]) => void;
  onSave: () => void;
  isSaving?: boolean;
  hasUnsavedChanges?: boolean;
}

const AVAILABLE_CATEGORIES = [
  { id: "AI/ML", label: "AI/ML", icon: "🤖" },
  { id: "AI Agents", label: "AI Agents", icon: "🎯" },
  { id: "Robotics", label: "Robotics", icon: "🦾" },
  { id: "Biotech", label: "Biotech", icon: "🧬" },
  { id: "Military Tech", label: "Military Tech", icon: "⚔️" },
  { id: "Hardware", label: "Hardware", icon: "💻" },
  { id: "Cloud", label: "Cloud", icon: "☁️" },
  { id: "Security", label: "Security", icon: "🔒" },
  { id: "Quantum Computing", label: "Quantum Computing", icon: "⚛️" },
  { id: "Healthcare", label: "Healthcare", icon: "🏥" },
];

export function TopicFilter({ selectedCategories, onCategoriesChange, onSave, isSaving = false, hasUnsavedChanges = false }: TopicFilterProps) {
  const toggleCategory = (categoryId: string) => {
    if (selectedCategories.includes(categoryId)) {
      onCategoriesChange(selectedCategories.filter((c) => c !== categoryId));
    } else {
      onCategoriesChange([...selectedCategories, categoryId]);
    }
  };

  const clearAll = () => {
    onCategoriesChange([]);
  };

  const selectAll = () => {
    onCategoriesChange(AVAILABLE_CATEGORIES.map((c) => c.id));
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            <CardTitle>Topic Preferences</CardTitle>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={clearAll}>
              Clear All
            </Button>
            <Button variant="outline" size="sm" onClick={selectAll}>
              Select All
            </Button>
          </div>
        </div>
        <CardDescription>
          Choose topics you're interested in to personalize your news feed
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          {AVAILABLE_CATEGORIES.map((category) => (
            <label
              key={category.id}
              className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
            >
              <Checkbox
                checked={selectedCategories.includes(category.id)}
                onCheckedChange={() => toggleCategory(category.id)}
              />
              <span className="text-2xl">{category.icon}</span>
              <span className="flex-1">{category.label}</span>
            </label>
          ))}
        </div>

        {selectedCategories.length > 0 && (
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-gray-600">
                Selected Topics ({selectedCategories.length})
              </p>
              {hasUnsavedChanges && (
                <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-300">
                  Unsaved changes
                </Badge>
              )}
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              {selectedCategories.map((catId) => {
                const category = AVAILABLE_CATEGORIES.find((c) => c.id === catId);
                return (
                  <Badge key={catId} variant="default" className="gap-1">
                    <span>{category?.icon}</span>
                    <span>{category?.label}</span>
                    <button
                      onClick={() => toggleCategory(catId)}
                      className="ml-1 hover:bg-white/20 rounded-full"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                );
              })}
            </div>
            <Button onClick={onSave} className="w-full" disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Save Preferences
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
