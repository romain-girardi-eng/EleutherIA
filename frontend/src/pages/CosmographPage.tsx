/**
 * CosmographPage - GPU-Powered Knowledge Graph Page
 *
 * Modern, ultra-fast graph visualization using Cosmograph
 */

import { useState, useCallback, useMemo, useEffect, Component } from 'react';
import type { ReactNode } from 'react';
import { useParams, Link } from 'react-router-dom';
import CosmographKGVisualizer from '../components/CosmographKGVisualizer';
import { CosmicNodePanel } from '../components/cosmos/CosmicNodePanel';
import ModeSwitcher from '../components/canvas/ModeSwitcher';
import BottomTabNav from '../components/mobile/BottomTabNav';
import { HelpCircle, Monitor, Network } from 'lucide-react';
import type { KGNode } from '../types';
import { apiClient } from '../api/client';
import { useDevice } from '../context/DeviceContext';

/** Scoped error boundary — catches Cosmograph/WebGL crashes without reloading the page */
class GraphErrorBoundary extends Component<
  { children: ReactNode; onError?: () => void },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.error('GraphErrorBoundary caught:', error);
    this.props.onError?.();
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4 max-w-sm text-center p-6">
            <div className="w-16 h-16 rounded-full bg-amber-500/20 flex items-center justify-center border border-amber-500/30">
              <Network className="w-8 h-8 text-amber-400" />
            </div>
            <p className="text-white/80 font-medium">Graph visualization failed to load</p>
            <p className="text-white/40 text-sm">Your device may not have enough GPU resources for the interactive graph.</p>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="px-5 py-2.5 bg-white/10 text-white/80 rounded-xl hover:bg-white/15 transition-all border border-white/10 text-sm"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

/** Mobile fallback — shown instead of the GPU graph on phones/tablets */
function MobileGraphFallback({ nodeCount, edgeCount }: { nodeCount: number; edgeCount: number }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center px-6">
      <div className="flex flex-col items-center gap-6 max-w-sm text-center">
        <div className="w-20 h-20 rounded-2xl bg-violet-500/20 flex items-center justify-center border border-violet-500/30">
          <Monitor className="w-10 h-10 text-violet-400" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white mb-2">Desktop Recommended</h2>
          <p className="text-white/50 text-sm leading-relaxed">
            The interactive knowledge graph ({nodeCount.toLocaleString()} nodes, {edgeCount.toLocaleString()} edges)
            requires GPU acceleration and works best on desktop browsers.
          </p>
        </div>
        <div className="flex flex-col gap-3 w-full">
          <Link
            to="/search"
            className="px-5 py-3 bg-violet-600/80 text-white rounded-xl hover:bg-violet-600 transition-all border border-violet-500/30 text-sm font-medium"
          >
            Search the Knowledge Graph
          </Link>
          <Link
            to="/database"
            className="px-5 py-3 bg-white/10 text-white/80 rounded-xl hover:bg-white/15 transition-all border border-white/10 text-sm"
          >
            Browse the Database
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function CosmographPage() {
  const { nodeId } = useParams<{ nodeId?: string }>();
  const { isMobile, isTablet } = useDevice();
  const isMobileOrTablet = isMobile || isTablet;
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const [allNodes, setAllNodes] = useState<KGNode[]>([]);
  const [cyData, setCyData] = useState<{ elements?: { edges?: Array<{ data: Record<string, unknown> }> } } | null>(null);

  // Load data for relationships
  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await apiClient.getCytoscapeData();
        setCyData(data);
        if (data.elements?.nodes) {
          setAllNodes(data.elements.nodes.map(n => n.data as KGNode));
        }
      } catch (err) {
        console.error('Failed to load data:', err);
      }
    };
    loadData();
  }, []);

  // Auto-select node from URL
  useEffect(() => {
    if (nodeId && allNodes.length > 0) {
      const node = allNodes.find(n => n.id === nodeId);
      if (node) {
        setSelectedNode(node);
      }
    }
  }, [nodeId, allNodes]);

  // Handle node click
  const handleNodeClick = useCallback((node: KGNode | null) => {
    console.log('📍 CosmographPage: handleNodeClick called', { node: node?.label, nodeId: node?.id });
    setSelectedNode(node);
  }, []);

  // Handle close panel
  const handleClosePanel = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Handle navigate to related node
  const handleNavigateToNode = useCallback((nodeId: string) => {
    const node = allNodes.find(n => n.id === nodeId);
    if (node) {
      setSelectedNode(node);
    }
  }, [allNodes]);

  // Get relationships for selected node
  const relationships = useMemo(() => {
    if (!selectedNode || !cyData?.elements?.edges) return [];

    const rels: Array<{
      id: string;
      label: string;
      type: string;
      relation: string;
      direction: 'incoming' | 'outgoing';
    }> = [];

    cyData.elements.edges.forEach(edge => {
      const source = edge.data.source ?? edge.data.source_id;
      const target = edge.data.target ?? edge.data.target_id;
      const relation = edge.data.relation || 'related_to';

      if (source === selectedNode.id) {
        const targetNode = allNodes.find(n => n.id === target);
        if (targetNode) {
          rels.push({
            id: targetNode.id,
            label: targetNode.label || targetNode.id,
            type: targetNode.type || 'unknown',
            relation: String(relation),
            direction: 'outgoing',
          });
        }
      } else if (target === selectedNode.id) {
        const sourceNode = allNodes.find(n => n.id === source);
        if (sourceNode) {
          rels.push({
            id: sourceNode.id,
            label: sourceNode.label || sourceNode.id,
            type: sourceNode.type || 'unknown',
            relation: String(relation),
            direction: 'incoming',
          });
        }
      }
    });

    return rels;
  }, [selectedNode, cyData, allNodes]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.key === '?') {
        e.preventDefault();
        setShowHelp(prev => !prev);
      } else if (e.key === 'Escape') {
        setShowHelp(false);
        setSelectedNode(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="fixed top-12 left-0 right-0 bottom-0 overflow-hidden bg-[#030712]">
      {/* Main visualization — mobile gets a fallback, desktop gets the GPU graph */}
      {isMobileOrTablet ? (
        <MobileGraphFallback
          nodeCount={allNodes.length}
          edgeCount={cyData?.elements?.edges?.length ?? 0}
        />
      ) : (
        <div className="absolute inset-0">
          <GraphErrorBoundary>
            <CosmographKGVisualizer
              onNodeClick={handleNodeClick}
              selectedNodeId={selectedNode?.id}
            />
          </GraphErrorBoundary>
        </div>
      )}

      {/* Mode Switcher - Top Right */}
      <div className="absolute top-4 right-4 z-30 flex items-center gap-2">
        <button
          onClick={() => setShowHelp(true)}
          className="p-2.5 bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-xl text-slate-400 hover:text-white hover:border-slate-600/50 transition-colors"
          title="Help (?)"
        >
          <HelpCircle className="w-5 h-5" />
        </button>
        <ModeSwitcher />
      </div>

      {/* Node Detail Panel */}
      <CosmicNodePanel
        node={selectedNode}
        onClose={handleClosePanel}
        onNavigateToNode={handleNavigateToNode}
        relationships={relationships}
      />

      {/* Help Modal */}
      {showHelp && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          onClick={() => setShowHelp(false)}
        >
          <div
            className="w-full max-w-md bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Keyboard Shortcuts</h2>
              <button
                onClick={() => setShowHelp(false)}
                className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors text-xl leading-none"
              >
                &times;
              </button>
            </div>
            <div className="p-6 space-y-6">
              {/* Keyboard Shortcuts */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Toggle help</span>
                  <kbd className="px-2.5 py-1 text-xs font-medium text-white/80 bg-white/10 border border-white/10 rounded-lg">?</kbd>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Reset view</span>
                  <kbd className="px-2.5 py-1 text-xs font-medium text-white/80 bg-white/10 border border-white/10 rounded-lg">R</kbd>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Fit to view</span>
                  <kbd className="px-2.5 py-1 text-xs font-medium text-white/80 bg-white/10 border border-white/10 rounded-lg">F</kbd>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Deselect / Close</span>
                  <kbd className="px-2.5 py-1 text-xs font-medium text-white/80 bg-white/10 border border-white/10 rounded-lg">Esc</kbd>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/60">Focus on node</span>
                  <kbd className="px-2.5 py-1 text-xs font-medium text-white/80 bg-white/10 border border-white/10 rounded-lg">2×click</kbd>
                </div>
              </div>

              {/* Mouse Controls */}
              <div className="pt-4 border-t border-white/10">
                <h3 className="text-xs font-medium uppercase tracking-wider text-white/40 mb-3">Mouse Controls</h3>
                <div className="space-y-2 text-sm text-white/50">
                  <p><span className="text-white/70">Click node</span> — Select and zoom</p>
                  <p><span className="text-white/70">Drag canvas</span> — Pan view</p>
                  <p><span className="text-white/70">Scroll</span> — Zoom in/out</p>
                  <p><span className="text-white/70">Drag node</span> — Move node</p>
                </div>
              </div>

              {/* Footer */}
              <div className="pt-4 border-t border-white/10">
                <div className="flex items-center gap-2 text-xs text-white/40">
                  <span className="inline-block w-2 h-2 rounded-full bg-violet-500 shadow-lg shadow-violet-500/50"></span>
                  <span>GPU-accelerated • Cosmograph Engine</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Bottom Navigation */}
      <div className="md:hidden">
        <BottomTabNav />
      </div>
    </div>
  );
}
