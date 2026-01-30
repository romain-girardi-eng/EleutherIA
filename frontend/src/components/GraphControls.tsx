import { Filter, Eye, Layout, Palette, X, Target, Sliders } from 'lucide-react';
import { useEffect, useState, memo } from 'react';
import { useTranslation } from 'react-i18next';

interface GraphControlsProps {
  onFilterChange: (filters: NodeFilters) => void;
  onLayoutChange: (layout: string) => void;
  onCurveStyleChange?: (curveStyle: string) => void;
  stats?: {
    person?: number;
    work?: number;
    concept?: number;
    argument?: number;
    debate?: number;
    reformulation?: number;
    quote?: number;
    // Allow additional node types dynamically
    [key: string]: number | undefined;
  };
  canColorByCommunity?: boolean;
  visibleNodeCount?: number;
  totalNodeCount?: number;
  communityAlgorithm?: string;
  onCommunityAlgorithmChange?: (algorithm: string) => void;
  communityMeta?: {
    algorithmUsed: string;
    algorithmRequested: string;
    quality?: number | null;
    communities: Array<{ id: number; size: number; color: string }>;
    availableAlgorithms: Array<{ name: string; available: boolean; description: string }>;
  } | null;
  communityLoading?: boolean;
  // Ancient-only filter for API refetch (excludes modern reception)
  ancientOnly?: boolean;
  onAncientOnlyChange?: (ancientOnly: boolean) => void;
}

export interface NodeFilters {
  person: boolean;
  work: boolean;
  concept: boolean;
  argument: boolean;
  debate: boolean;
  reformulation: boolean;
  quote: boolean;
  // Extended node types (less common)
  group: boolean;
  event: boolean;
  school: boolean;
  controversy: boolean;
  conceptual_evolution: boolean;
  argument_framework: boolean;
  showLabels: boolean;
  showEdgeLabels: boolean;
  colorByCommunity: boolean;
  // Period filter - exclude modern scholarly reception
  ancientOnly: boolean;
  // New complexity controls
  maxNodes: number;
  egocentricMode: boolean;
  hopDistance: 1 | 2 | 3;
  minConnections: number;
  edgeLabelsOnHover: boolean;
}

// Memoized to prevent re-renders when parent updates but props haven't changed
const GraphControls = memo(function GraphControls({
  onFilterChange,
  onLayoutChange,
  onCurveStyleChange,
  stats,
  canColorByCommunity,
  visibleNodeCount,
  totalNodeCount,
  communityAlgorithm,
  onCommunityAlgorithmChange,
  communityMeta,
  communityLoading,
  ancientOnly: ancientOnlyProp,
  onAncientOnlyChange,
}: GraphControlsProps) {
  const { t } = useTranslation();
  const [showControls, setShowControls] = useState(true);
  const [filters, setFilters] = useState<NodeFilters>({
    person: true,
    work: true,
    concept: true,
    argument: true,
    debate: true,
    reformulation: true,
    quote: true,
    group: true,
    event: true,
    school: true,
    controversy: true,
    conceptual_evolution: true,
    argument_framework: true,
    showLabels: true,
    showEdgeLabels: true,
    colorByCommunity: false,
    ancientOnly: false, // Include both ancient sources and modern reception by default
    maxNodes: 1000, // Show all nodes by default (increased from 500)
    egocentricMode: false,
    hopDistance: 1,
    minConnections: 0,
    edgeLabelsOnHover: true,
  });

  const nodeTypes = [
    { key: 'person' as const, label: t('kg.nodeTypes.persons'), color: '#0284c7', icon: '👤' },
    { key: 'work' as const, label: t('kg.nodeTypes.works'), color: '#7dd3fc', icon: '📚' },
    { key: 'concept' as const, label: t('kg.nodeTypes.concepts'), color: '#fbbf24', icon: '💡' },
    { key: 'argument' as const, label: t('kg.nodeTypes.arguments'), color: '#f87171', icon: '⚖️' },
    { key: 'debate' as const, label: t('kg.nodeTypes.debates'), color: '#a78bfa', icon: '💬' },
    { key: 'reformulation' as const, label: 'Reformulations', color: '#34d399', icon: '🔄' },
    { key: 'quote' as const, label: 'Quotes', color: '#fb923c', icon: '💬' },
    { key: 'group' as const, label: 'Groups', color: '#6366f1', icon: '👥' },
    { key: 'event' as const, label: 'Events', color: '#ec4899', icon: '📅' },
    { key: 'school' as const, label: t('kg.nodeTypes.schools'), color: '#14b8a6', icon: '🏛️' },
    { key: 'controversy' as const, label: 'Controversies', color: '#ef4444', icon: '⚔️' },
    { key: 'conceptual_evolution' as const, label: 'Evolutions', color: '#8b5cf6', icon: '📈' },
    { key: 'argument_framework' as const, label: 'Frameworks', color: '#f59e0b', icon: '🏗️' },
  ];

  const layouts = [
    { value: 'hierarchical', label: 'Hierarchical', description: 'Author → Work → Passage structure (zoom to reveal passages)' },
    { value: 'fcose', label: t('kg.layouts.schoolClusters'), description: 'Philosophical schools grouped spatially with balanced hierarchy' },
    { value: 'semantic', label: t('kg.layouts.semanticMap'), description: 'Arranged by conceptual similarity using AI embeddings' },
    { value: 'breadthfirst', label: t('kg.layouts.temporal'), description: 'Chronological tree structure' },
    { value: 'cose', label: 'Force-Directed', description: 'Classic automatic layout' },
    { value: 'concentric', label: t('kg.layouts.circular'), description: 'Rings based on connections' },
    { value: 'grid', label: t('kg.layouts.grid'), description: 'Organized in rows and columns' },
    { value: 'random', label: 'Random', description: 'Randomized positions' },
  ];

  const curveStyles = [
    { value: 'bezier', label: t('kg.edgeStyles.bezier'), description: 'Smooth curved edges' },
    { value: 'taxi', label: t('kg.edgeStyles.taxi'), description: 'Right-angle routing - reduces visual clutter' },
    { value: 'straight', label: t('kg.edgeStyles.straight'), description: 'Direct lines between nodes' },
    { value: 'unbundled-bezier', label: t('kg.edgeStyles.segments'), description: 'Natural curves avoiding nodes' },
  ];

  const toggleFilter = (key: keyof NodeFilters) => {
    const newFilters = { ...filters, [key]: !filters[key] };
    setFilters(newFilters);
    onFilterChange(newFilters);

    // For ancientOnly, also trigger API refetch via callback
    if (key === 'ancientOnly' && onAncientOnlyChange) {
      onAncientOnlyChange(newFilters.ancientOnly);
    }
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
      group: true,
      event: true,
      school: true,
      controversy: true,
      conceptual_evolution: true,
      argument_framework: true,
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
    group: false,
    event: false,
    school: false,
    controversy: false,
    conceptual_evolution: false,
    argument_framework: false,
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

    // Ancient only filter
    if (filters.ancientOnly) {
      chips.push({
        label: 'Ancient sources only',
        onRemove: () => toggleFilter('ancientOnly'),
      });
    }

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

    // Max nodes (if not showing all)
    if (filters.maxNodes < 1000) {
      chips.push({
        label: `Max: ${filters.maxNodes} nodes`,
        onRemove: () => {
          const newFilters = { ...filters, maxNodes: 1000 };
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

  // Sync ancientOnly from prop (for when parent/context changes it)
  useEffect(() => {
    if (ancientOnlyProp !== undefined && filters.ancientOnly !== ancientOnlyProp) {
      const newFilters = { ...filters, ancientOnly: ancientOnlyProp };
      setFilters(newFilters);
      onFilterChange(newFilters);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ancientOnlyProp]);

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
          <span className="font-semibold">{visibleNodeCount}</span> {t('kg.of')} {totalNodeCount} {t('kg.displayed')}
          {visibleNodeCount > 150 && <span className="block mt-1">⚠️ {t('kg.warning')}</span>}
          {visibleNodeCount > 100 && visibleNodeCount <= 150 && <span className="block mt-1">⚠️ Best for experienced users</span>}
          {visibleNodeCount > 50 && visibleNodeCount <= 100 && <span className="block mt-1">⚠️ Consider additional filtering</span>}
          {visibleNodeCount <= 50 && <span className="block mt-1">✓ {t('kg.optimal')}</span>}
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
        <span className="hidden sm:inline">{t('kg.controls')}</span>
      </button>

      {/* Control Panel */}
      {showControls && (
        <div className="bg-white shadow-xl rounded-lg overflow-hidden max-h-[calc(100vh-8rem)] overflow-y-auto">
          {/* Node Type Filters */}
          <section className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Eye className="w-4 h-4" />
                {t('kg.nodeTypes.title')}
              </h3>
              <div className="flex gap-2 text-xs">
                <button
                  onClick={selectAll}
                  className="text-primary-600 hover:underline"
                >
                  {t('kg.all')}
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={deselectAll}
                  className="text-primary-600 hover:underline"
                >
                  {t('kg.none')}
                </button>
              </div>
            </div>
            <div className="space-y-1.5">
              {nodeTypes.map(type => (
                <label
                  key={type.key}
                  className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-2 sm:p-2 rounded transition-colors min-h-[44px]"
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
                    className="w-5 h-5 sm:w-4 sm:h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500 flex-shrink-0"
                  />
                </label>
              ))}
            </div>
          </section>

          {/* Source Layer Filter - Ancient vs Modern Reception */}
          <section className="p-4 border-b border-gray-200 bg-amber-50/50">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Filter className="w-4 h-4" />
              Source Layer
            </h3>
            <div className="space-y-2">
              <label className="flex items-center justify-between cursor-pointer p-2 hover:bg-amber-100/50 rounded transition-colors">
                <div className="flex-1">
                  <span className="text-sm font-medium">Ancient Sources Only</span>
                  <p className="text-xs text-gray-600 mt-0.5">
                    Hide Medieval, Early Modern &amp; Contemporary scholars
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={filters.ancientOnly}
                  onChange={() => toggleFilter('ancientOnly')}
                  className="w-5 h-5 text-amber-600 rounded focus:ring-2 focus:ring-amber-500"
                />
              </label>
              <div className={`text-xs p-2 rounded ${filters.ancientOnly ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-600'}`}>
                {filters.ancientOnly ? (
                  <>
                    <strong>Primary layer:</strong> Showing only ancient philosophers, concepts, and arguments (6th c. BCE - 6th c. CE)
                  </>
                ) : (
                  <>
                    <strong>Full graph:</strong> Including modern scholarly reception (Bobzien, Frede, Kane, etc.)
                  </>
                )}
              </div>
            </div>
          </section>

          {/* Layout Options */}
          <section className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Layout className="w-4 h-4" />
              {t('kg.layoutAlgorithm')}
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

          {/* Edge Curve Style Options */}
          {onCurveStyleChange && (
            <section className="p-4 border-b border-gray-200">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Layout className="w-4 h-4" />
                {t('kg.edgeCurveStyle')}
              </h3>
              <div className="space-y-2">
                {curveStyles.map(style => (
                  <button
                    key={style.value}
                    onClick={() => onCurveStyleChange(style.value)}
                    className="w-full text-left p-2.5 hover:bg-primary-50 rounded transition-colors group"
                  >
                    <div className="text-sm font-medium text-gray-900 group-hover:text-primary-700">
                      {style.label}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {style.description}
                    </div>
                  </button>
                ))}
              </div>
              <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-blue-800">
                <p className="font-medium mb-1">💡 Tip for reducing edge crossings:</p>
                <p>Try <strong>Taxi</strong> curves with <strong>FCOSE</strong> or <strong>Hierarchical</strong> layout for clearest visualization.</p>
              </div>
            </section>
          )}

          {/* Edge Color Legend */}
          <section className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Palette className="w-4 h-4" />
              {t('kg.edgeColorLegend')}
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-8 h-0.5 bg-blue-500"></div>
                <span className="text-gray-700">{t('kg.edgeTypes.influence')}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-0.5 bg-orange-500"></div>
                <span className="text-gray-700">{t('kg.edgeTypes.mentions')}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-0.5 bg-red-500"></div>
                <span className="text-gray-700">{t('kg.edgeTypes.criticisms')}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-0.5 bg-gray-300"></div>
                <span className="text-gray-700">{t('kg.edgeTypes.other')}</span>
              </div>
            </div>
            <p className="mt-3 text-[11px] text-gray-500 leading-snug">
              Edge colors help distinguish relationship types when lines cross. Hover over edges to see specific relationship labels.
            </p>
          </section>

          {/* Complexity Controls */}
          <section className="p-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Sliders className="w-4 h-4" />
              {t('kg.graphComplexity')}
            </h3>
            <div className="space-y-4">
              {/* Egocentric Mode */}
              <div>
                <label className="flex items-center justify-between cursor-pointer p-2 hover:bg-gray-50 rounded transition-colors">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-gray-500" />
                    <span className="text-sm">{t('kg.focusMode')}</span>
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
                      {t('kg.connectionDistance')}
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
                          {t(`kg.hops.${hop === 1 ? 'one' : hop === 2 ? 'two' : 'three'}`)}
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
                  {t('kg.maximumNodes')} <span className="font-semibold text-primary-600">{filters.maxNodes >= 1000 ? t('kg.all') : filters.maxNodes}</span>
                </label>
                <input
                  type="range"
                  min="25"
                  max="1000"
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
                  <span>100</span>
                  <span>250</span>
                  <span>500</span>
                  <span>All</span>
                </div>
                <p className="text-[10px] text-gray-500 mt-2">
                  {filters.maxNodes <= 50 && '✓ Optimal readability'}
                  {filters.maxNodes > 50 && filters.maxNodes <= 100 && '⚠️ Use filters to reduce clutter'}
                  {filters.maxNodes > 100 && filters.maxNodes <= 150 && '⚠️ Best for experienced users'}
                  {filters.maxNodes > 150 && '⚠️ May be difficult to read - consider filtering'}
                </p>
              </div>

              {/* Minimum Connections */}
              <div>
                <label className="block text-sm mb-2">
                  {t('kg.minimumConnections')} <span className="font-semibold text-primary-600">{filters.minConnections}</span>
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
              {t('kg.displayOptions')}
            </h3>
            <div className="space-y-2">
              <label className="flex items-center justify-between cursor-pointer p-2 hover:bg-gray-50 rounded transition-colors">
                <span className="text-sm">{t('kg.showNodeLabels')}</span>
                <input
                  type="checkbox"
                  checked={filters.showLabels}
                  onChange={() => toggleFilter('showLabels')}
                  className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                />
              </label>
              <div className="space-y-2">
                <label className="flex items-center justify-between cursor-pointer p-2 hover:bg-gray-50 rounded transition-colors">
                  <span className="text-sm">{t('kg.showEdgeLabels')}</span>
                  <input
                    type="checkbox"
                    checked={filters.showEdgeLabels}
                    onChange={() => toggleFilter('showEdgeLabels')}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-2 focus:ring-primary-500"
                  />
                </label>
                {filters.showEdgeLabels && (
                  <label className="flex items-center justify-between cursor-pointer p-2 pl-6 hover:bg-gray-50 rounded transition-colors">
                    <span className="text-xs text-gray-600">{t('kg.onHoverOnly')}</span>
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
                    <span className="text-sm font-medium text-gray-700">{t('kg.nodeColoring')}</span>
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
                      {t('kg.colorBy.type')}
                    </button>
                    <button
                      onClick={() => setColorMode(true)}
                      className={`px-2 py-1.5 text-xs font-medium rounded border transition-colors ${
                        filters.colorByCommunity
                          ? 'border-primary-500 bg-primary-50 text-primary-700 shadow-sm'
                          : 'border-gray-200 bg-white text-gray-600 hover:border-primary-300'
                      }`}
                    >
                      {t('kg.colorBy.community')}
                    </button>
                  </div>
                  <p className="text-[11px] text-gray-500 mt-2 leading-snug">
                    Community colors use the selected detection algorithm. Switch back to type colors any time.
                  </p>
                </div>
              )}
            </div>
          </section>

          {/* Advanced Settings - Community Detection */}
          {onCommunityAlgorithmChange && (
            <section className="p-4 border-t border-gray-200">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Sliders className="w-4 h-4" />
                {t('kg.communityDetection')}
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-2">
                    {t('kg.algorithm')}
                  </label>
                  <select
                    value={communityAlgorithm || 'auto'}
                    onChange={(e) => onCommunityAlgorithmChange(e.target.value)}
                    disabled={communityLoading}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  >
                    <option value="auto">{t('kg.algorithms.auto')}</option>
                    <option
                      value="leiden"
                      disabled={communityMeta?.availableAlgorithms?.find(a => a.name === 'leiden')?.available === false}
                    >
                      {t('kg.algorithms.leiden')}{communityMeta?.availableAlgorithms?.find(a => a.name === 'leiden')?.available === false ? ' (unavailable)' : ''}
                    </option>
                    <option
                      value="louvain"
                      disabled={communityMeta?.availableAlgorithms?.find(a => a.name === 'louvain')?.available === false}
                    >
                      {t('kg.algorithms.louvain')}{communityMeta?.availableAlgorithms?.find(a => a.name === 'louvain')?.available === false ? ' (unavailable)' : ''}
                    </option>
                    <option
                      value="greedy"
                      disabled={communityMeta?.availableAlgorithms?.find(a => a.name === 'greedy')?.available === false}
                    >
                      Greedy modularity{communityMeta?.availableAlgorithms?.find(a => a.name === 'greedy')?.available === false ? ' (unavailable)' : ''}
                    </option>
                    <option value="none">No community overlay</option>
                  </select>
                </div>

                {communityLoading && (
                  <p className="text-xs text-gray-500 italic">Updating communities...</p>
                )}

                {communityMeta && !communityLoading && (
                  <div className="text-xs text-gray-600 bg-gray-50 border border-gray-100 rounded p-2 leading-relaxed">
                    {communityMeta.algorithmUsed !== 'none' ? (
                      <>
                        <span className="font-semibold text-gray-800 capitalize">{communityMeta.algorithmUsed}</span>
                        {typeof communityMeta.quality === 'number' && (
                          <span> • Modularity {communityMeta.quality.toFixed(4)}</span>
                        )}
                        {communityMeta.communities.length > 0 && (
                          <span> • {communityMeta.communities.length} communities</span>
                        )}
                      </>
                    ) : (
                      <span>Community detection disabled—nodes colored by type.</span>
                    )}
                  </div>
                )}

                {communityMeta?.availableAlgorithms && communityMeta.availableAlgorithms.length > 0 && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">
                      Algorithm Status
                    </summary>
                    <ul className="mt-2 space-y-1.5 ml-4">
                      {communityMeta.availableAlgorithms.map((algo) => (
                        <li key={algo.name} className="leading-snug">
                          <span className={`font-medium ${algo.available ? 'text-emerald-600' : 'text-gray-400'}`}>
                            {algo.available ? '✓' : '○'} {algo.name.charAt(0).toUpperCase() + algo.name.slice(1)}
                          </span>
                          <div className="text-[11px] text-gray-500 mt-0.5">{algo.description}</div>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            </section>
          )}

          {/* Help Text */}
          <div className="bg-primary-50 p-3 text-xs text-primary-800 border-t border-primary-100">
            <p className="font-medium mb-1">{t('kg.tips.title')}</p>
            <ul className="space-y-1 text-primary-700">
              <li>• {t('kg.tips.clickNodes')}</li>
              <li>• {t('kg.tips.dragNodes')}</li>
              <li>• {t('kg.tips.scrollZoom')}</li>
              <li>• Press <kbd className="px-1 py-0.5 bg-white rounded text-xs">R</kbd> to reset view</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}, (prevProps, nextProps) => {
  // Only re-render if key props changed
  return (
    prevProps.stats === nextProps.stats &&
    prevProps.visibleNodeCount === nextProps.visibleNodeCount &&
    prevProps.communityAlgorithm === nextProps.communityAlgorithm &&
    prevProps.communityLoading === nextProps.communityLoading &&
    prevProps.communityMeta === nextProps.communityMeta
  );
});

export default GraphControls;
