import { Filter, Eye, Layout, Palette, X, Target, Sliders } from 'lucide-react';
import { useEffect, useState } from 'react';

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
  canColorByCommunity?: boolean;
  visibleNodeCount?: number;
  totalNodeCount?: number;
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
  colorByCommunity: boolean;
  // New complexity controls
  maxNodes: number;
  egocentricMode: boolean;
  hopDistance: 1 | 2 | 3;
  minConnections: number;
  edgeLabelsOnHover: boolean;
}

export default function GraphControls({ onFilterChange, onLayoutChange, stats, canColorByCommunity, visibleNodeCount, totalNodeCount }: GraphControlsProps) {
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
    colorByCommunity: false,
    maxNodes: 150,
    egocentricMode: false,
    hopDistance: 1,
    minConnections: 0,
    edgeLabelsOnHover: true,
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

  const setColorMode = (useCommunity: boolean) => {
    if (filters.colorByCommunity === useCommunity) {
      return;
    }
    const newFilters = { ...filters, colorByCommunity: useCommunity };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const getActiveFilterChips = () => {
    const chips: Array<{ label: string; onRemove: () => void }> = [];

    // Node type filters (only show if some are disabled)
    const disabledTypes = nodeTypes.filter(type => !filters[type.key]);
    if (disabledTypes.length > 0 && disabledTypes.length < nodeTypes.length) {
      const enabledTypes = nodeTypes.filter(type => filters[type.key]);
      chips.push({
        label: `Types: ${enabledTypes.map(t => t.label).join(', ')}`,
        onRemove: () => selectAll(),
      });
    }

    // Egocentric mode
    if (filters.egocentricMode) {
      chips.push({
        label: `Focus: ${filters.hopDistance} hop${filters.hopDistance > 1 ? 's' : ''}`,
        onRemove: () => toggleFilter('egocentricMode'),
      });
    }

    // Max nodes (if not default)
    if (filters.maxNodes < 150) {
      chips.push({
        label: `Max: ${filters.maxNodes} nodes`,
        onRemove: () => {
          const newFilters = { ...filters, maxNodes: 150 };
          setFilters(newFilters);
          onFilterChange(newFilters);
        },
      });
    }

    // Min connections
    if (filters.minConnections > 0) {
      chips.push({
        label: `Min connections: ${filters.minConnections}`,
        onRemove: () => {
          const newFilters = { ...filters, minConnections: 0 };
          setFilters(newFilters);
          onFilterChange(newFilters);
        },
      });
    }

    // Color by community
    if (filters.colorByCommunity && canColorByCommunity) {
      chips.push({
        label: 'Community colors',
        onRemove: () => setColorMode(false),
      });
    }

    return chips;
  };

  const activeChips = getActiveFilterChips();

  useEffect(() => {
    if (!canColorByCommunity && filters.colorByCommunity) {
      const newFilters = { ...filters, colorByCommunity: false };
      setFilters(newFilters);
      onFilterChange(newFilters);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canColorByCommunity]);

  return (
    <div className="absolute top-4 left-4 z-10 max-w-[calc(100vw-2rem)] sm:max-w-sm space-y-2">
      {/* Node Count Indicator */}
      {visibleNodeCount !== undefined && totalNodeCount !== undefined && (
        <div className={`text-xs px-3 py-2 rounded-lg shadow-lg ${
          visibleNodeCount > 150 ? 'bg-red-50 border border-red-200 text-red-800' :
          visibleNodeCount > 100 ? 'bg-amber-50 border border-amber-200 text-amber-800' :
          visibleNodeCount > 50 ? 'bg-yellow-50 border border-yellow-200 text-yellow-800' :
          'bg-emerald-50 border border-emerald-200 text-emerald-800'
        }`}>
          <span className="font-semibold">{visibleNodeCount}</span> of {totalNodeCount} nodes displayed
          {visibleNodeCount > 150 && <span className="block mt-1">❌ Graph may be difficult to read</span>}
          {visibleNodeCount > 100 && visibleNodeCount <= 150 && <span className="block mt-1">⚠️ Best for experienced users</span>}
          {visibleNodeCount > 50 && visibleNodeCount <= 100 && <span className="block mt-1">⚠️ Consider additional filtering</span>}
          {visibleNodeCount <= 50 && <span className="block mt-1">✓ Optimal readability</span>}
        </div>
      )}

      {/* Active Filter Chips */}
      {activeChips.length > 0 && (
        <div className="flex flex-wrap gap-2 bg-white/90 backdrop-blur-sm shadow-lg rounded-lg p-2">
          {activeChips.map((chip, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1.5 bg-primary-100 text-primary-700 px-2 py-1 rounded-md text-xs font-medium"
            >
              {chip.label}
              <button
                onClick={chip.onRemove}
                className="hover:bg-primary-200 rounded-full p-0.5 transition-colors"
                aria-label={`Remove filter: ${chip.label}`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Toggle Button */}
      <button
        onClick={() => setShowControls(!showControls)}
        className="bg-white shadow-lg rounded-lg px-3 py-2 hover:bg-gray-50 transition-colors flex items-center gap-2 text-sm font-medium w-full sm:w-auto"
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

          {/* Complexity Controls */}
          <section className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Sliders className="w-4 h-4" />
              Graph Complexity
            </h3>
            <div className="space-y-4">
              {/* Egocentric Mode */}
              <div>
                <label className="flex items-center justify-between cursor-pointer p-2 hover:bg-gray-50 rounded transition-colors">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-gray-500" />
                    <span className="text-sm">Focus Mode</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={filters.egocentricMode}
                    onChange={() => toggleFilter('egocentricMode')}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                  />
                </label>
                {filters.egocentricMode && (
                  <div className="ml-6 mt-2 space-y-2">
                    <label className="block text-xs text-gray-600">
                      Connection Distance:
                    </label>
                    <div className="flex gap-2">
                      {[1, 2, 3].map((hop) => (
                        <button
                          key={hop}
                          onClick={() => {
                            const newFilters = { ...filters, hopDistance: hop as 1 | 2 | 3 };
                            setFilters(newFilters);
                            onFilterChange(newFilters);
                          }}
                          className={`flex-1 px-2 py-1.5 text-xs font-medium rounded border transition-colors ${
                            filters.hopDistance === hop
                              ? 'border-primary-500 bg-primary-50 text-primary-700'
                              : 'border-gray-200 bg-white text-gray-600 hover:border-primary-300'
                          }`}
                        >
                          {hop} hop{hop > 1 ? 's' : ''}
                        </button>
                      ))}
                    </div>
                    <p className="text-[10px] text-gray-500 mt-1">
                      Shows only nodes within {filters.hopDistance} connection{filters.hopDistance > 1 ? 's' : ''} of selected node
                    </p>
                  </div>
                )}
              </div>

              {/* Max Nodes Slider */}
              <div>
                <label className="block text-sm mb-2">
                  Maximum Nodes: <span className="font-semibold text-primary-600">{filters.maxNodes === 500 ? 'All' : filters.maxNodes}</span>
                </label>
                <input
                  type="range"
                  min="25"
                  max="500"
                  step="25"
                  value={filters.maxNodes}
                  onChange={(e) => {
                    const newFilters = { ...filters, maxNodes: parseInt(e.target.value) };
                    setFilters(newFilters);
                    onFilterChange(newFilters);
                  }}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                />
                <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                  <span>25</span>
                  <span>50</span>
                  <span>100</span>
                  <span>150</span>
                  <span>All</span>
                </div>
                <p className="text-[10px] text-gray-500 mt-2">
                  {filters.maxNodes <= 50 && '✓ Optimal readability'}
                  {filters.maxNodes > 50 && filters.maxNodes <= 100 && '⚠️ Use filters to reduce clutter'}
                  {filters.maxNodes > 100 && filters.maxNodes <= 150 && '⚠️ Best for experienced users'}
                  {filters.maxNodes > 150 && '❌ May be difficult to read - consider filtering'}
                </p>
              </div>

              {/* Minimum Connections */}
              <div>
                <label className="block text-sm mb-2">
                  Minimum Connections: <span className="font-semibold text-primary-600">{filters.minConnections}</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="20"
                  step="1"
                  value={filters.minConnections}
                  onChange={(e) => {
                    const newFilters = { ...filters, minConnections: parseInt(e.target.value) };
                    setFilters(newFilters);
                    onFilterChange(newFilters);
                  }}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                />
                <p className="text-[10px] text-gray-500 mt-2">
                  Filter out less-connected nodes (degree filter)
                </p>
              </div>
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
              <div className="space-y-2">
                <label className="flex items-center justify-between cursor-pointer p-2 hover:bg-gray-50 rounded transition-colors">
                  <span className="text-sm">Show Edge Labels</span>
                  <input
                    type="checkbox"
                    checked={filters.showEdgeLabels}
                    onChange={() => toggleFilter('showEdgeLabels')}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                  />
                </label>
                {filters.showEdgeLabels && (
                  <label className="flex items-center justify-between cursor-pointer p-2 pl-6 hover:bg-gray-50 rounded transition-colors">
                    <span className="text-xs text-gray-600">On Hover Only</span>
                    <input
                      type="checkbox"
                      checked={filters.edgeLabelsOnHover}
                      onChange={() => toggleFilter('edgeLabelsOnHover')}
                      className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                    />
                  </label>
                )}
              </div>
              {canColorByCommunity && (
                <div className="p-2 rounded border border-gray-100 bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Node Coloring</span>
                    <span className="text-xs text-gray-500">Choose palette</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setColorMode(false)}
                      className={`px-2 py-1.5 text-xs font-medium rounded border transition-colors ${
                        !filters.colorByCommunity
                          ? 'border-primary-500 bg-white text-primary-700 shadow-sm'
                          : 'border-gray-200 bg-white text-gray-600 hover:border-primary-300'
                      }`}
                    >
                      By Type
                    </button>
                    <button
                      onClick={() => setColorMode(true)}
                      className={`px-2 py-1.5 text-xs font-medium rounded border transition-colors ${
                        filters.colorByCommunity
                          ? 'border-primary-500 bg-primary-50 text-primary-700 shadow-sm'
                          : 'border-gray-200 bg-white text-gray-600 hover:border-primary-300'
                      }`}
                    >
                      By Community
                    </button>
                  </div>
                  <p className="text-[11px] text-gray-500 mt-2 leading-snug">
                    Community colors use the selected detection algorithm. Switch back to type colors any time.
                  </p>
                </div>
              )}
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
