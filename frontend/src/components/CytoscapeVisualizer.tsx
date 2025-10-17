import { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import type { CytoscapeData } from '../types';

interface CytoscapeVisualizerProps {
  data: CytoscapeData | null;
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edgeId: string) => void;
}

export default function CytoscapeVisualizer({
  data,
  onNodeClick,
  onEdgeClick,
}: CytoscapeVisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  useEffect(() => {
    if (!containerRef.current || !data) return;

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
      minZoom: 0.1,
      maxZoom: 3,
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

    // Cleanup
    return () => {
      cy.destroy();
    };
  }, [data, onNodeClick, onEdgeClick]);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full graph-container" />

      {/* Node Inspector Panel */}
      {selectedNode && (
        <div className="absolute top-4 right-4 bg-academic-paper border border-academic-border rounded-lg shadow-lg p-4 max-w-md">
          <div className="flex justify-between items-start mb-3">
            <h3 className="text-lg font-semibold">{selectedNode.label}</h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-academic-muted hover:text-academic-text"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2 text-sm">
            <div>
              <span className="font-medium">Type:</span>{' '}
              <span className="text-academic-muted">{selectedNode.type}</span>
            </div>

            {selectedNode.period && (
              <div>
                <span className="font-medium">Period:</span>{' '}
                <span className="text-academic-muted">{selectedNode.period}</span>
              </div>
            )}

            {selectedNode.school && (
              <div>
                <span className="font-medium">School:</span>{' '}
                <span className="text-academic-muted">{selectedNode.school}</span>
              </div>
            )}

            {selectedNode.description && (
              <div className="pt-2 border-t border-academic-border">
                <p className="text-academic-text leading-relaxed">{selectedNode.description}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="absolute bottom-4 right-4 flex flex-col space-y-2">
        <button
          onClick={() => cyRef.current?.fit()}
          className="academic-button-outline"
          title="Fit to screen"
        >
          ⊡
        </button>
        <button
          onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)}
          className="academic-button-outline"
          title="Zoom in"
        >
          +
        </button>
        <button
          onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
          className="academic-button-outline"
          title="Zoom out"
        >
          −
        </button>
      </div>
    </div>
  );
}
