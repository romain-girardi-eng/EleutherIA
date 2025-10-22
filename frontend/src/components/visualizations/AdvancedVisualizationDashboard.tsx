import { useMemo, useState } from 'react';
import {
  Clock,
  Sparkles,
  TrendingUp,
  Network,
  BarChart3,
  Activity,
  Layers,
} from 'lucide-react';
import AdvancedTimeline from './AdvancedTimeline';
import ConceptConstellation from './ConceptConstellation';
import InfluenceFlowDiagram from './InfluenceFlowDiagram';
import AdvancedNetworkVisualization from './AdvancedNetworkVisualization';
import AdvancedAnalyticsPanel from './AdvancedAnalyticsPanel';
import type { CytoscapeData } from '../../types';

type VisualizationMode = 
  | 'timeline' 
  | 'constellation' 
  | 'influence' 
  | 'network' 
  | 'analytics' 
  | 'overview';

interface VisualizationTab {
  id: VisualizationMode;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  render: () => JSX.Element;
}

interface AdvancedVisualizationDashboardProps {
  networkData: CytoscapeData | null;
  networkLoading: boolean;
  networkError: string | null;
}

export default function AdvancedVisualizationDashboard({
  networkData,
  networkLoading,
  networkError,
}: AdvancedVisualizationDashboardProps) {
  const [activeMode, setActiveMode] = useState<VisualizationMode>('overview');

  const visualizationTabs: VisualizationTab[] = useMemo(
    () => [
      {
        id: 'overview',
        label: 'Overview',
        icon: Layers,
        description: 'Comprehensive dashboard with all visualizations',
        render: () => (
          <div className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <AdvancedTimeline />
              <ConceptConstellation />
            </div>
            <InfluenceFlowDiagram />
            <AdvancedNetworkVisualization
              data={networkData}
              loading={networkLoading}
              error={networkError}
              standalone
            />
          </div>
        ),
      },
      {
        id: 'timeline',
        label: 'Timeline',
        icon: Clock,
        description: 'Advanced chronological analysis with stream visualization',
        render: () => <AdvancedTimeline />,
      },
      {
        id: 'constellation',
        label: 'Constellations',
        icon: Sparkles,
        description: 'Concept clusters visualized as stellar constellations',
        render: () => <ConceptConstellation />,
      },
      {
        id: 'influence',
        label: 'Influence Flow',
        icon: TrendingUp,
        description: 'Sankey diagram showing philosophical influence patterns',
        render: () => <InfluenceFlowDiagram />,
      },
      {
        id: 'network',
        label: 'Network',
        icon: Network,
        description: 'Advanced force-directed network with intelligent clustering',
        render: () => (
          <AdvancedNetworkVisualization
            data={networkData}
            loading={networkLoading}
            error={networkError}
            standalone={false}
          />
        ),
      },
      {
        id: 'analytics',
        label: 'Analytics',
        icon: BarChart3,
        description: 'Statistical analysis and data insights',
        render: () => <AdvancedAnalyticsPanel />,
      },
    ],
    [networkData, networkLoading, networkError],
  );

  const activeTab = visualizationTabs.find((tab) => tab.id === activeMode);

  return (
    <div className="space-y-6">
      {/* Mode Selector */}
      <div className="academic-card">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-academic-text mb-2">
              Advanced Knowledge Visualization
            </h2>
            <p className="text-sm text-academic-muted">
              Sophisticated academic visualizations for exploring philosophical knowledge graphs
            </p>
          </div>
          <div className="text-xs text-academic-muted max-w-sm text-right">
            Choose from multiple visualization modes, each optimized for different research questions
            and analytical perspectives.
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {visualizationTabs.map((tab) => {
            const IconComponent = tab.icon;
            const isActive = activeMode === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveMode(tab.id)}
                className={`p-4 rounded-lg border transition-all duration-200 ${
                  isActive
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 bg-white hover:border-primary-300 hover:bg-primary-25 text-academic-text'
                }`}
              >
                <div className="flex flex-col items-center space-y-2">
                  <IconComponent className={`w-5 h-5 ${isActive ? 'text-primary-600' : 'text-academic-muted'}`} />
                  <div className="text-center">
                    <div className={`text-xs font-medium ${isActive ? 'text-primary-700' : 'text-academic-text'}`}>
                      {tab.label}
                    </div>
                    <div className="text-[10px] text-academic-muted mt-1 leading-tight">
                      {tab.description}
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Visualization */}
      {activeTab && (
        <div className="academic-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <>
                <activeTab.icon className="w-5 h-5 text-primary-600" />
                <h3 className="text-lg font-semibold text-academic-text">
                  {activeTab.label}
                </h3>
              </>
            </div>
            <div className="text-xs text-academic-muted">
              {activeTab?.description}
            </div>
          </div>
          
          {activeTab.render()}
        </div>
      )}

      {/* Visualization Info */}
      <div className="academic-card bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <div className="flex items-start gap-4">
          <Activity className="w-6 h-6 text-primary-600 mt-1 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-academic-text mb-2">
              Visualization Features
            </h4>
            <div className="grid md:grid-cols-2 gap-4 text-sm text-academic-muted">
              <div>
                <h5 className="font-medium text-academic-text mb-1">Advanced Techniques</h5>
                <ul className="space-y-1 text-xs">
                  <li>• Force-directed layouts with intelligent physics</li>
                  <li>• Sankey diagrams for influence flow analysis</li>
                  <li>• Constellation mapping for concept clusters</li>
                  <li>• Stream graphs for temporal data visualization</li>
                </ul>
              </div>
              <div>
                <h5 className="font-medium text-academic-text mb-1">Academic Quality</h5>
                <ul className="space-y-1 text-xs">
                  <li>• Publication-ready visualizations</li>
                  <li>• Sophisticated color palettes</li>
                  <li>• Interactive exploration tools</li>
                  <li>• Export capabilities for research</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
