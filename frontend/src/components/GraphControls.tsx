import { Filter, Eye, Layout, Palette, X } from 'lucide-react';
import { useState } from 'react';

interface GraphControlsProps {
  onFilterChange: (filters: NodeFilters) => void;
  onLayoutChange: (layout: string) => void;
  stats?: {
    person?: number;
    work?: number;
    concept?: number;
    argument?: number;
    debate?: number;
    reformulation?: number;
    quote?: number;
  };
}

export interface NodeFilters {
  person: boolean;
  work: boolean;
  concept: boolean;
  argument: boolean;
  debate: boolean;
  reformulation: boolean;
  quote: boolean;
  showLabels: boolean;
  showEdgeLabels: boolean;
}

export default function GraphControls({ onFilterChange, onLayoutChange, stats }: GraphControlsProps) {
  const [showControls, setShowControls] = useState(true);
  const [filters, setFilters] = useState<NodeFilters>({
    person: true,
    work: true,
    concept: true,
    argument: true,
    debate: true,
    reformulation: true,
    quote: true,
    showLabels: true,
    showEdgeLabels: true,
  });

  const nodeTypes = [
    { key: 'person' as const, label: 'Persons', color: '#0284c7', icon: '👤' },
    { key: 'work' as const, label: 'Works', color: '#7dd3fc', icon: '📚' },
    { key: 'concept' as const, label: 'Concepts', color: '#fbbf24', icon: '💡' },
    { key: 'argument' as const, label: 'Arguments', color: '#f87171', icon: '⚖️' },
    { key: 'debate' as const, label: 'Debates', color: '#a78bfa', icon: '💬' },
    { key: 'reformulation' as const, label: 'Reformulations', color: '#34d399', icon: '🔄' },
    { key: 'quote' as const, label: 'Quotes', color: '#fb923c', icon: '💬' },
  ];

  const layouts = [
    { value: 'cose', label: 'Force-Directed (Recommended)', description: 'Automatic layout based on connections' },
    { value: 'circle', label: 'Circular', description: 'Nodes arranged in a circle' },
    { value: 'grid', label: 'Grid', description: 'Organized in rows and columns' },
    { value: 'breadthfirst', label: 'Hierarchical', description: 'Tree-like structure' },
    { value: 'concentric', label: 'Concentric', description: 'Rings based on connections' },
    { value: 'random', label: 'Random', description: 'Randomized positions' },
  ];

  const toggleFilter = (key: keyof NodeFilters) => {
    const newFilters = { ...filters, [key]: !filters[key] };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const selectAll = () => {
    const newFilters = {
      ...filters,
      person: true,
      work: true,
      concept: true,
      argument: true,
      debate: true,
      reformulation: true,
      quote: true,
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const deselectAll = () => {
    const newFilters = {
      ...filters,
      person: false,
      work: false,
      concept: false,
      argument: false,
      debate: false,
      reformulation: false,
      quote: false,
    };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="absolute top-4 left-4 z-10 max-w-[calc(100vw-2rem)] sm:max-w-sm">
      {/* Toggle Button */}
      <button
        onClick={() => setShowControls(!showControls)}
        className="bg-white shadow-lg rounded-lg px-3 py-2 hover:bg-gray-50 transition-colors flex items-center gap-2 mb-2 text-sm font-medium"
        aria-label={showControls ? 'Hide controls' : 'Show controls'}
      >
        {showControls ? <X className="w-4 h-4" /> : <Filter className="w-4 h-4" />}
        <span className="hidden sm:inline">Graph Controls</span>
      </button>

      {/* Control Panel */}
      {showControls && (
        <div className="bg-white shadow-xl rounded-lg overflow-hidden max-h-[calc(100vh-8rem)] overflow-y-auto">
          {/* Node Type Filters */}
          <section className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Eye className="w-4 h-4" />
                Node Types
              </h3>
              <div className="flex gap-2 text-xs">
                <button
                  onClick={selectAll}
                  className="text-primary-600 hover:underline"
                >
                  All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={deselectAll}
                  className="text-primary-600 hover:underline"
                >
                  None
                </button>
              </div>
            </div>
            <div className="space-y-1.5">
              {nodeTypes.map(type => (
                <label
                  key={type.key}
                  className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-2 rounded transition-colors"
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <span className="text-base flex-shrink-0">{type.icon}</span>
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: type.color }}
                    />
                    <span className="text-sm truncate">{type.label}</span>
                    {stats && stats[type.key] !== undefined && (
                      <span className="text-xs text-gray-400 flex-shrink-0">
                        ({stats[type.key]})
                      </span>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    checked={filters[type.key]}
                    onChange={() => toggleFilter(type.key)}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500 flex-shrink-0"
                  />
                </label>
              ))}
            </div>
          </section>

          {/* Layout Options */}
          <section className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Layout className="w-4 h-4" />
              Layout Algorithm
            </h3>
            <div className="space-y-2">
              {layouts.map(layout => (
                <button
                  key={layout.value}
                  onClick={() => onLayoutChange(layout.value)}
                  className="w-full text-left p-2.5 hover:bg-primary-50 rounded transition-colors group"
                >
                  <div className="text-sm font-medium text-gray-900 group-hover:text-primary-700">
                    {layout.label}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {layout.description}
                  </div>
                </button>
              ))}
            </div>
          </section>

          {/* Display Options */}
          <section className="p-4">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Palette className="w-4 h-4" />
              Display Options
            </h3>
            <div className="space-y-2">
              <label className="flex items-center justify-between cursor-pointer p-2 hover:bg-gray-50 rounded transition-colors">
                <span className="text-sm">Show Node Labels</span>
                <input
                  type="checkbox"
                  checked={filters.showLabels}
                  onChange={() => toggleFilter('showLabels')}
                  className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                />
              </label>
              <label className="flex items-center justify-between cursor-pointer p-2 hover:bg-gray-50 rounded transition-colors">
                <span className="text-sm">Show Edge Labels</span>
                <input
                  type="checkbox"
                  checked={filters.showEdgeLabels}
                  onChange={() => toggleFilter('showEdgeLabels')}
                  className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                />
              </label>
            </div>
          </section>

          {/* Help Text */}
          <div className="bg-primary-50 p-3 text-xs text-primary-800 border-t border-primary-100">
            <p className="font-medium mb-1">💡 Tips:</p>
            <ul className="space-y-1 text-primary-700">
              <li>• Click nodes to view details</li>
              <li>• Drag to pan, scroll to zoom</li>
              <li>• Double-click to center on node</li>
              <li>• Press <kbd className="px-1 py-0.5 bg-white rounded text-xs">R</kbd> to reset view</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
