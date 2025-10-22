import { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import type { CytoscapeData, KGNode } from '../types';
import NodeDetailPanel from './NodeDetailPanel';
import GraphControls, { type NodeFilters } from './GraphControls';
import GraphExportTools from './GraphExportTools';
import { Maximize, Minimize } from 'lucide-react';

const INITIAL_FILTERS: NodeFilters = {
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
};

interface CytoscapeVisualizerProps {
  data: CytoscapeData | null;
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edgeId: string) => void;
  selectedNodeIds?: string[];
  focusNodeId?: string | null;
}

export default function CytoscapeVisualizerEnhanced({
  data,
  onNodeClick,
  onEdgeClick,
  selectedNodeIds,
  focusNodeId,
}: CytoscapeVisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const containerDivRef = useRef<HTMLDivElement | null>(null);
  const colorModeRef = useRef<boolean>(INITIAL_FILTERS.colorByCommunity);
  const [selectedNode, setSelectedNode] = useState<KGNode | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const [nodeStats, setNodeStats] = useState<Record<string, number>>({});
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentFilters, setCurrentFilters] = useState<NodeFilters>(INITIAL_FILTERS);
  const [communityColors, setCommunityColors] = useState<Record<number, string>>({});

  useEffect(() => {
    if (!data && cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
      setSelectedNode(null);
      setNodeStats({});
      setCommunityColors({});
    }
  }, [data]);

  useEffect(() => {
    if (!data?.meta?.community?.communities?.length) {
      setCommunityColors({});
      return;
    }
    const palette: Record<number, string> = {};
    for (const community of data.meta.community.communities) {
      palette[community.id] = community.color;
    }
    setCommunityColors(palette);
  }, [data]);

  useEffect(() => {
    colorModeRef.current = currentFilters.colorByCommunity;
  }, [currentFilters.colorByCommunity]);

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current || !data) return;

    // Calculate node type statistics
    const stats: Record<string, number> = {};
    data.elements.nodes.forEach(n => {
      const type = n.data.type || 'unknown';
      stats[type] = (stats[type] || 0) + 1;
    });
    setNodeStats(stats);

    // Initialize Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...data.elements.nodes.map((n) => ({ data: n.data, classes: n.classes })),
        ...data.elements.edges.map((e) => ({ data: e.data, classes: e.classes })),
      ],
      style: [
        // Node styles
        {
          selector: 'node',
          style: {
            'background-color': '#0ea5e9',
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '10px',
            'font-family': 'Georgia, serif',
            color: '#1c1917',
            'text-outline-width': 2,
            'text-outline-color': '#fff',
            width: 30,
            height: 30,
          },
        },
        // Node type-specific colors
        {
          selector: 'node[type="person"]',
          style: {
            'background-color': '#0284c7',
          },
        },
        {
          selector: 'node[type="work"]',
          style: {
            'background-color': '#7dd3fc',
          },
        },
        {
          selector: 'node[type="concept"]',
          style: {
            'background-color': '#fbbf24',
          },
        },
        {
          selector: 'node[type="argument"]',
          style: {
            'background-color': '#f87171',
          },
        },
        {
          selector: 'node[type="debate"]',
          style: {
            'background-color': '#a78bfa',
          },
        },
        {
          selector: 'node[type="reformulation"]',
          style: {
            'background-color': '#34d399',
          },
        },
        {
          selector: 'node[type="quote"]',
          style: {
            'background-color': '#fb923c',
          },
        },
        // Selected node
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#0c4a6e',
            'background-color': '#0369a1',
          },
        },
        // Edge styles
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#d4d4d8',
            'target-arrow-color': '#d4d4d8',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(relation)',
            'font-size': '8px',
            'text-rotation': 'autorotate',
            color: '#78716c',
            'text-background-opacity': 1,
            'text-background-color': '#fff',
            'text-background-padding': '2px',
          },
        },
        // Selected edge
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#0369a1',
            'target-arrow-color': '#0369a1',
            width: 3,
          },
        },
      ],
      layout: {
        name: 'cose',
        idealEdgeLength: 100,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 30,
        randomize: false,
        componentSpacing: 100,
        nodeRepulsion: 400000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      },
      minZoom: 0.01,
      maxZoom: 10,
    });

    cyRef.current = cy;

    // Event handlers
    cy.on('tap', 'node', (event) => {
      const node = event.target;
      setSelectedNode(node.data());
      if (onNodeClick) {
        onNodeClick(node.id());
      }
    });

    cy.on('tap', 'edge', (event) => {
      const edge = event.target;
      if (onEdgeClick) {
        onEdgeClick(edge.id());
      }
    });

    // Double-click to center on node
    let lastTapTime = 0;
    cy.on('tap', 'node', (event) => {
      const now = Date.now();
      if (now - lastTapTime < 300) {
        // Double-click detected
        cy.animate({
          center: { eles: event.target },
          zoom: 1.5,
          duration: 300,
        });
      }
      lastTapTime = now;
    });

    if (colorModeRef.current) {
      applyColorMode(true);
    }

    // Cleanup
    return () => {
      cy.destroy();
    };
  }, [data, onNodeClick, onEdgeClick]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.$(':selected').unselect();

    if (selectedNodeIds && selectedNodeIds.length > 0) {
      selectedNodeIds.forEach((id) => {
        const node = cy.getElementById(id);
        if (node && !node.empty()) {
          node.select();
        }
      });
      const firstSelected = cy.getElementById(selectedNodeIds[0]);
      if (firstSelected && !firstSelected.empty()) {
        setSelectedNode(firstSelected.data());
      }
    } else if (focusNodeId) {
      const focusNode = cy.getElementById(focusNodeId);
      if (focusNode && !focusNode.empty()) {
        focusNode.select();
        setSelectedNode(focusNode.data());
      }
    } else {
      setSelectedNode(null);
    }

    if (focusNodeId) {
      const focusNode = cy.getElementById(focusNodeId);
      if (focusNode && !focusNode.empty()) {
        cy.animate({
          center: { eles: focusNode },
          duration: 300,
          zoom: Math.min(Math.max(cy.zoom(), 1.2), 2),
        });
      }
    }
  }, [selectedNodeIds, focusNodeId]);

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!containerDivRef.current) return;

    if (!isFullscreen) {
      if (containerDivRef.current.requestFullscreen) {
        containerDivRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!cyRef.current) return;

      // Don't trigger if user is typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key.toLowerCase()) {
        case 'r':
          // Reset view
          cyRef.current.fit();
          break;
        case 'f':
          // Fullscreen toggle (with Shift) or Fit (without Shift)
          if (e.shiftKey) {
            toggleFullscreen();
          } else {
            // Fit selected nodes or all
            const selected = cyRef.current.$(':selected');
            if (selected.length > 0) {
              cyRef.current.fit(selected, 50);
            } else {
              cyRef.current.fit();
            }
          }
          break;
        case 'h':
        case '?':
          // Toggle help overlay
          setShowHelp(prev => !prev);
          break;
        case 'c':
          // Center on selected node
          const node = cyRef.current.$(':selected').first();
          if (node.length > 0) {
            cyRef.current.center(node);
          }
          break;
        case 'escape':
          // Deselect all or exit fullscreen
          if (isFullscreen) {
            toggleFullscreen();
          } else {
            cyRef.current.$(':selected').unselect();
            setSelectedNode(null);
          }
          break;
        case '+':
        case '=':
          // Zoom in
          cyRef.current.zoom(cyRef.current.zoom() * 1.2);
          break;
        case '-':
        case '_':
          // Zoom out
          cyRef.current.zoom(cyRef.current.zoom() * 0.8);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isFullscreen]);

  const applyColorMode = (useCommunity: boolean) => {
    if (!cyRef.current) return;

    if (useCommunity && Object.keys(communityColors).length > 0) {
      cyRef.current.nodes().forEach((node) => {
        const communityId = node.data('communityId');
        if (communityId === undefined || communityId === null) {
          node.style('background-color', '#94a3b8');
          return;
        }
        const color = communityColors[Number(communityId)];
        node.style('background-color', color || '#38bdf8');
      });
    } else {
      cyRef.current.nodes().forEach((node) => {
        node.removeStyle('background-color');
      });
    }
  };

  // Handle filter changes
  const handleFilterChange = (filters: NodeFilters) => {
    if (!cyRef.current) return;

    setCurrentFilters(filters);

    const typeKeys: Array<keyof NodeFilters> = [
      'person',
      'work',
      'concept',
      'argument',
      'debate',
      'reformulation',
      'quote',
    ];

    typeKeys.forEach((key) => {
      const shouldShow = filters[key];
      cyRef.current?.nodes(`[type="${key}"]`).style({
        display: shouldShow ? 'element' : 'none',
      });
    });

    cyRef.current
      .style()
      .selector('node')
      .style({ 'text-opacity': filters.showLabels ? 1 : 0 })
      .update();

    cyRef.current
      .style()
      .selector('edge')
      .style({ 'text-opacity': filters.showEdgeLabels ? 1 : 0 })
      .update();

    applyColorMode(filters.colorByCommunity);
  };

  useEffect(() => {
    if (currentFilters.colorByCommunity) {
      applyColorMode(true);
    }
  }, [communityColors, currentFilters.colorByCommunity]);

  // Handle layout changes
  const handleLayoutChange = (layoutName: string) => {
    if (!cyRef.current) return;

    const layoutOptions: any = {
      name: layoutName,
      animate: true,
      animationDuration: 500,
      fit: true,
      padding: 30,
    };

    // Add specific options for certain layouts
    if (layoutName === 'cose') {
      layoutOptions.idealEdgeLength = 100;
      layoutOptions.nodeRepulsion = 400000;
      layoutOptions.edgeElasticity = 100;
    } else if (layoutName === 'breadthfirst') {
      layoutOptions.directed = true;
      layoutOptions.spacingFactor = 1.5;
    } else if (layoutName === 'concentric') {
      layoutOptions.minNodeSpacing = 50;
    }

    cyRef.current.layout(layoutOptions).run();
  };

  return (
    <div
      ref={containerDivRef}
      className={`relative w-full ${isFullscreen ? 'h-screen' : ''}`}
      style={isFullscreen ? {} : { height: '600px' }}
    >
      {/* Main graph container */}
      <div ref={containerRef} className="w-full h-full graph-container bg-gray-50 rounded-lg" />

      {/* Graph Controls */}
      <GraphControls
        onFilterChange={handleFilterChange}
        onLayoutChange={handleLayoutChange}
        stats={nodeStats}
        canColorByCommunity={Boolean(data?.meta?.community?.communities?.length)}
      />

      {/* Export Tools */}
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <button
          onClick={toggleFullscreen}
          className="bg-white shadow-lg rounded-lg p-2 hover:bg-gray-50 transition-colors"
          title={isFullscreen ? 'Exit Fullscreen (Shift+F or ESC)' : 'Enter Fullscreen (Shift+F)'}
        >
          {isFullscreen ? <Minimize className="w-5 h-5" /> : <Maximize className="w-5 h-5" />}
        </button>
        <GraphExportTools cyRef={cyRef} />
      </div>

      {/* Node Detail Panel */}
      {selectedNode && (
        <NodeDetailPanel
          node={selectedNode}
          onClose={() => {
            setSelectedNode(null);
            cyRef.current?.$(':selected').unselect();
          }}
          onNavigateToNode={(nodeId) => {
            const node = cyRef.current?.$(`#${nodeId}`).first();
            if (node && node.length > 0) {
              // Unselect previous node
              cyRef.current?.$(':selected').unselect();
              // Select new node
              node.select();
              // Animate to new node
              cyRef.current?.animate({
                center: { eles: node },
                zoom: 1.5,
                duration: 300,
              });
              // Update selected node
              setSelectedNode(node.data());
            }
          }}
          relationships={
            cyRef.current && selectedNode
              ? (() => {
                  const cy = cyRef.current;
                  const nodeId = selectedNode.id;
                  const relationships: Array<{
                    id: string;
                    label: string;
                    type: string;
                    relation: string;
                    direction: 'incoming' | 'outgoing';
                  }> = [];

                  // Get outgoing edges (this node is source)
                  cy.edges(`[source="${nodeId}"]`).forEach((edge) => {
                    const targetNode = cy.$(`#${edge.data('target')}`).first();
                    if (targetNode.length > 0) {
                      relationships.push({
                        id: targetNode.id(),
                        label: targetNode.data('label') || targetNode.id(),
                        type: targetNode.data('type') || 'unknown',
                        relation: edge.data('relation') || 'related_to',
                        direction: 'outgoing',
                      });
                    }
                  });

                  // Get incoming edges (this node is target)
                  cy.edges(`[target="${nodeId}"]`).forEach((edge) => {
                    const sourceNode = cy.$(`#${edge.data('source')}`).first();
                    if (sourceNode.length > 0) {
                      relationships.push({
                        id: sourceNode.id(),
                        label: sourceNode.data('label') || sourceNode.id(),
                        type: sourceNode.data('type') || 'unknown',
                        relation: edge.data('relation') || 'related_to',
                        direction: 'incoming',
                      });
                    }
                  });

                  return relationships;
                })()
              : []
          }
        />
      )}

      {/* Keyboard Shortcuts Help */}
      {showHelp && (
        <div className="absolute bottom-4 left-4 bg-white shadow-xl rounded-lg p-4 max-w-xs z-20">
          <div className="flex justify-between items-start mb-3">
            <h4 className="font-semibold text-sm">Keyboard Shortcuts</h4>
            <button
              onClick={() => setShowHelp(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <dl className="space-y-2 text-xs">
            <div className="flex justify-between gap-4">
              <dt className="font-mono bg-gray-100 px-2 py-1 rounded flex-shrink-0">R</dt>
              <dd className="text-gray-600">Reset view</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="font-mono bg-gray-100 px-2 py-1 rounded flex-shrink-0">F</dt>
              <dd className="text-gray-600">Fit to screen</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="font-mono bg-gray-100 px-2 py-1 rounded flex-shrink-0">Shift+F</dt>
              <dd className="text-gray-600">Toggle fullscreen</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="font-mono bg-gray-100 px-2 py-1 rounded flex-shrink-0">C</dt>
              <dd className="text-gray-600">Center selected</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="font-mono bg-gray-100 px-2 py-1 rounded flex-shrink-0">H / ?</dt>
              <dd className="text-gray-600">Toggle this help</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="font-mono bg-gray-100 px-2 py-1 rounded flex-shrink-0">ESC</dt>
              <dd className="text-gray-600">Deselect all</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="font-mono bg-gray-100 px-2 py-1 rounded flex-shrink-0">+/-</dt>
              <dd className="text-gray-600">Zoom in/out</dd>
            </div>
          </dl>
          <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
            <p className="mb-1"><strong>Mouse:</strong></p>
            <ul className="space-y-1">
              <li>• Click node to view details</li>
              <li>• Double-click to center</li>
              <li>• Drag to pan, scroll to zoom</li>
            </ul>
          </div>
        </div>
      )}

      {/* Floating help button (mobile-friendly) */}
      {!showHelp && (
        <button
          onClick={() => setShowHelp(true)}
          className="absolute bottom-4 left-4 bg-primary-600 hover:bg-primary-700 text-white rounded-full w-10 h-10 flex items-center justify-center shadow-lg transition-colors z-20"
          title="Show keyboard shortcuts (H)"
        >
          ?
        </button>
      )}
    </div>
  );
}
