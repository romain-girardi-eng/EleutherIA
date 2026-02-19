import { useEffect, useRef, useCallback } from 'react';
import type { GraphRAGResponse } from '../../types';

interface MiniNode {
  id: string;
  label: string;
  type: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  opacity: number;
  targetOpacity: number;
  scale: number;
  highlighted: boolean;
  highlightTimer: number;
}

interface MiniEdge {
  source: MiniNode;
  target: MiniNode;
  progress: number;
}

interface KnowledgeGraphMiniProps {
  response: GraphRAGResponse | null;
  activeCitationIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
}

const NODE_COLORS: Record<string, string> = {
  person:   '#3B82F6',
  concept:  '#22C55E',
  argument: '#A855F7',
  work:     '#F59E0B',
  default:  '#9CA3AF',
};

function getNodeColor(type: string) {
  return NODE_COLORS[type.toLowerCase()] ?? NODE_COLORS.default;
}

export default function KnowledgeGraphMini({
  response,
  activeCitationIndex,
  onNodeClick,
  onHighlightRef,
}: KnowledgeGraphMiniProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<MiniNode[]>([]);
  const edgesRef = useRef<MiniEdge[]>([]);
  const rafRef = useRef<number>(0);
  const hoveredNodeRef = useRef<MiniNode | null>(null);

  const buildGraph = useCallback((resp: GraphRAGResponse) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const W = canvas.width || canvas.offsetWidth || 300;
    const H = canvas.height || canvas.offsetHeight || 400;

    const nodeMap = new Map<string, MiniNode>();

    const addNode = (id: string, label: string, type: string) => {
      if (!nodeMap.has(id)) {
        nodeMap.set(id, {
          id, label, type,
          x: W / 2 + (Math.random() - 0.5) * 100,
          y: H / 2 + (Math.random() - 0.5) * 100,
          vx: 0, vy: 0,
          opacity: 0, targetOpacity: 1,
          scale: 1,
          highlighted: false, highlightTimer: 0,
        });
      }
    };

    if (resp.sources) {
      resp.sources.slice(0, 20).forEach(s => addNode(s.nodeId, s.nodeLabel, s.nodeType));
    }
    if (resp.reasoning_path) {
      resp.reasoning_path.starting_nodes?.forEach(n => addNode(n.id, n.label, n.type));
      resp.reasoning_path.expanded_nodes?.slice(0, 15).forEach(n => addNode(n.id, n.label, n.type));
    }

    const nodes = Array.from(nodeMap.values());
    nodesRef.current = nodes;

    const edges: MiniEdge[] = [];
    if (resp.reasoning_path?.traversed_edges) {
      resp.reasoning_path.traversed_edges.slice(0, 30).forEach(e => {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (src && tgt) edges.push({ source: src, target: tgt, progress: 0 });
      });
    } else if (nodes.length > 1) {
      for (let i = 1; i < Math.min(nodes.length, 8); i++) {
        edges.push({ source: nodes[0], target: nodes[i], progress: 0 });
      }
    }
    edgesRef.current = edges;
  }, []);

  const tick = useCallback(() => {
    const nodes = nodesRef.current;
    const edges = edgesRef.current;
    const canvas = canvasRef.current;
    if (!canvas || nodes.length === 0) {
      rafRef.current = requestAnimationFrame(tick);
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;

    const repulsion = 800;
    const attraction = 0.04;
    const centerForce = 0.01;
    const damping = 0.85;

    for (const n of nodes) {
      n.vx += (W / 2 - n.x) * centerForce;
      n.vy += (H / 2 - n.y) * centerForce;

      for (const m of nodes) {
        if (m === n) continue;
        const dx = n.x - m.x;
        const dy = n.y - m.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = repulsion / (dist * dist);
        n.vx += (dx / dist) * force;
        n.vy += (dy / dist) * force;
      }
    }

    for (const e of edges) {
      const dx = e.target.x - e.source.x;
      const dy = e.target.y - e.source.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist - 80) * attraction;
      e.source.vx += (dx / dist) * force;
      e.source.vy += (dy / dist) * force;
      e.target.vx -= (dx / dist) * force;
      e.target.vy -= (dy / dist) * force;
      e.progress = Math.min(1, e.progress + 0.015);
    }

    for (const n of nodes) {
      n.vx *= damping;
      n.vy *= damping;
      n.x = Math.max(20, Math.min(W - 20, n.x + n.vx));
      n.y = Math.max(20, Math.min(H - 20, n.y + n.vy));
      n.opacity = Math.min(n.targetOpacity, n.opacity + 0.04);

      if (n.highlighted) {
        n.highlightTimer -= 16;
        if (n.highlightTimer <= 0) {
          n.highlighted = false;
          n.scale = 1;
        } else {
          const t = 1 - n.highlightTimer / 800;
          n.scale = 1 + 0.3 * Math.sin(t * Math.PI);
        }
      }
    }

    ctx.clearRect(0, 0, W, H);

    for (const e of edges) {
      if (e.progress <= 0) continue;
      const dx = e.target.x - e.source.x;
      const dy = e.target.y - e.source.y;
      ctx.save();
      ctx.globalAlpha = e.progress * 0.6;
      ctx.strokeStyle = '#D1D5DB';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(e.source.x, e.source.y);
      ctx.lineTo(e.source.x + dx * e.progress, e.source.y + dy * e.progress);
      ctx.stroke();
      ctx.restore();
    }

    for (const n of nodes) {
      const r = 7 * n.scale;
      ctx.save();
      ctx.globalAlpha = n.opacity;
      ctx.fillStyle = getNodeColor(n.type);
      if (n.highlighted) {
        ctx.shadowColor = getNodeColor(n.type);
        ctx.shadowBlur = 12 * n.scale;
      }
      ctx.beginPath();
      ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    const hovered = hoveredNodeRef.current;
    if (hovered && hovered.opacity > 0.1) {
      const label = hovered.label.length > 22 ? hovered.label.slice(0, 22) + '…' : hovered.label;
      ctx.save();
      ctx.font = '11px system-ui, sans-serif';
      const textW = ctx.measureText(label).width;
      const px = 8, bh = 20;
      const bx = Math.min(Math.max(hovered.x - textW / 2 - px, 2), W - textW - 2 * px - 2);
      const by = Math.max(hovered.y - 30, 2);
      ctx.fillStyle = 'rgba(17,24,39,0.85)';
      ctx.beginPath();
      (ctx as any).roundRect(bx, by, textW + 2 * px, bh, 4);
      ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.fillText(label, bx + px, by + 14);
      ctx.restore();
    }

    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const highlightNode = useCallback((citationIndex: number) => {
    const nodes = nodesRef.current;
    const node = nodes[citationIndex] ?? null;
    if (!node) return;
    node.highlighted = true;
    node.highlightTimer = 800;
    node.scale = 1;
  }, []);

  useEffect(() => {
    onHighlightRef?.(highlightNode);
  }, [highlightNode, onHighlightRef]);

  useEffect(() => {
    if (!response) {
      nodesRef.current = [];
      edgesRef.current = [];
      return;
    }
    buildGraph(response);
    nodesRef.current.forEach((n, i) => {
      n.opacity = 0;
      n.targetOpacity = 0;
      setTimeout(() => { n.targetOpacity = 1; }, i * 30);
    });
  }, [response, buildGraph]);

  useEffect(() => {
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [tick]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const observer = new ResizeObserver(() => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    });
    observer.observe(canvas);
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    return () => observer.disconnect();
  }, []);

  // Suppress unused prop warning — activeCitationIndex is used by parent to track state
  void activeCitationIndex;

  const getNodeAt = (x: number, y: number) => {
    return nodesRef.current.find(n => {
      const dx = n.x - x;
      const dy = n.y - y;
      return Math.sqrt(dx * dx + dy * dy) < 10;
    }) ?? null;
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    hoveredNodeRef.current = getNodeAt(x, y);
    canvas.style.cursor = hoveredNodeRef.current ? 'pointer' : 'default';
  };

  const handleMouseLeave = () => {
    hoveredNodeRef.current = null;
  };

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    const node = getNodeAt(x, y);
    if (node) onNodeClick(node.id);
  };

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full block"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
    />
  );
}
