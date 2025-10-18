import React, { useState } from 'react';
import { Search, X } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { cn } from '../lib/utils';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  className?: string;
  defaultValue?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  placeholder = "Search articles...",
  className,
  defaultValue = "",
}) => {
  const [query, setQuery] = useState(defaultValue);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  const handleClear = () => {
    setQuery("");
    onSearch("");
  };

  return (
    <form onSubmit={handleSubmit} className={cn("relative", className)}>
      <div className="relative group">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-blue-600 transition-colors" />
        
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="pl-10 pr-24 h-11 text-sm bg-gray-50 border-gray-200 focus:bg-white focus:border-blue-300 rounded-lg transition-all"
        />

        <div className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {query && (
            <Button
              type="button"
              onClick={handleClear}
              variant="ghost"
              size="icon"
              className="h-7 w-7 rounded-md hover:bg-gray-100"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          )}
          
          <Button
            type="submit"
            size="sm"
            className="h-7 bg-blue-600 hover:bg-blue-700 text-white px-3 rounded-md shadow-sm"
          >
            Search
          </Button>
        </div>
      </div>
    </form>
  );
};

export default SearchBar;
