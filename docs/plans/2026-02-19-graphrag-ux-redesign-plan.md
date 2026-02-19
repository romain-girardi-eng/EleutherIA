# GraphRAG UX Redesign — Two-Panel Research Layout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign the GraphRAG page from a single-column chat into a two-panel editorial/research tool: left panel (65%) for the conversation thread, right panel (35%) for a live, animated knowledge graph and source detail cards.

**Architecture:** New `RightPanel` container manages four states (`idle`, `loading`, `graph`, `source-detail`) with Framer Motion `AnimatePresence`. `KnowledgeGraphMini` renders a D3 force-directed graph on `<canvas>`. Citation clicks in the left panel pass a citation index up to `GraphRAGPage`, which drives the right panel state. Mobile collapses to single column with a floating `📊` button opening the existing `BottomSheet` component.

**Tech Stack:** React 19, TypeScript, Framer Motion (already installed), D3 (already used in the project), Tailwind CSS, existing `BottomSheet` component (`components/ui/BottomSheet.tsx`), existing `ShineBorder` + `TerminalLoader` + `CitationRenderer`.

---

## Task 1: Add RightPanel state types to `GraphRAGPage`

**Files:**
- Modify: `frontend/src/pages/GraphRAGPage/index.tsx`

No new component yet. Just add the state variables that the rest of the plan will wire up.

**Step 1:** Open `frontend/src/pages/GraphRAGPage/index.tsx` and locate the existing state declarations (lines ~29-66).

**Step 2:** Add right-panel state after the existing `kgStats` state:

```typescript
// Right panel
type RightPanelState = 'idle' | 'loading' | 'graph' | 'source-detail';
const [rightPanelState, setRightPanelState] = useState<RightPanelState>('idle');
const [activeSourceIndex, setActiveSourceIndex] = useState<number | null>(null);
const [rightPanelResponse, setRightPanelResponse] = useState<GraphRAGResponse | null>(null);
const highlightNodeRef = useRef<((citationIndex: number) => void) | null>(null);

const handleCitationClick = (citationIndex: number) => {
  setActiveSourceIndex(citationIndex);
  setRightPanelState('source-detail');
  highlightNodeRef.current?.(citationIndex);
};
```

**Step 3:** In `handleStreamingQuery`, set `rightPanelState` to `'loading'` when streaming starts:

Find the line `setStreaming(true);` and add immediately below it:
```typescript
setRightPanelState('loading');
setRightPanelResponse(null);
```

**Step 4:** When streaming completes (in the `if (finalResponse)` block, after `setMessages(prev => [...prev, assistantMessage])`), add:
```typescript
setRightPanelResponse(finalResponse);
setRightPanelState('graph');
```

Also add the same transition after `setMessages` in the `else if (fullAnswer)` block (no sources in that case, so keep `idle`):
```typescript
setRightPanelState('idle');
```

**Step 5:** In `loadDemoMode`, after `setMessages([demoMessage, assistantMessage])`, add:
```typescript
setRightPanelResponse(mockGraphRAGResponse);
setRightPanelState('graph');
```

**Step 6:** Run the dev server to verify no TypeScript errors:
```bash
cd frontend && npm run dev
```
Expected: server starts, no TS errors in terminal.

**Step 7:** Commit:
```bash
git add frontend/src/pages/GraphRAGPage/index.tsx
git commit -m "feat(graphrag): add right panel state management to GraphRAGPage"
```

---

## Task 2: Create `KnowledgeGraphMini` canvas component

**Files:**
- Create: `frontend/src/components/graphrag/KnowledgeGraphMini.tsx`

This is the D3 force-directed mini graph rendered on `<canvas>`.

**Step 1:** Create the directory:
```bash
mkdir -p frontend/src/components/graphrag
```

**Step 2:** Create `frontend/src/components/graphrag/KnowledgeGraphMini.tsx` with this full content:

```tsx
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
  fx?: number | null;
  fy?: number | null;
  // Animation
  opacity: number;
  targetOpacity: number;
  scale: number;
  highlighted: boolean;
  highlightTimer: number;
}

interface MiniEdge {
  source: MiniNode;
  target: MiniNode;
  progress: number; // 0 → 1 draw-in animation
}

interface KnowledgeGraphMiniProps {
  response: GraphRAGResponse | null;
  activeCitationIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  /** Ref setter so parent can trigger citation highlight */
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
}

const NODE_COLORS: Record<string, string> = {
  person:   '#3B82F6', // blue-500
  concept:  '#22C55E', // green-500
  argument: '#A855F7', // purple-500
  work:     '#F59E0B', // amber-500
  default:  '#9CA3AF', // gray-400
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

  // Build graph from response
  const buildGraph = useCallback((resp: GraphRAGResponse) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const W = canvas.width;
    const H = canvas.height;

    const nodeMap = new Map<string, MiniNode>();

    const addNode = (id: string, label: string, type: string) => {
      if (!nodeMap.has(id)) {
        nodeMap.set(id, {
          id,
          label,
          type,
          x: W / 2 + (Math.random() - 0.5) * 100,
          y: H / 2 + (Math.random() - 0.5) * 100,
          vx: 0,
          vy: 0,
          opacity: 0,
          targetOpacity: 1,
          scale: 1,
          highlighted: false,
          highlightTimer: 0,
        });
      }
    };

    // Sources-based nodes
    if (resp.sources) {
      resp.sources.slice(0, 20).forEach(s => addNode(s.nodeId, s.nodeLabel, s.nodeType));
    }

    // reasoning_path nodes
    if (resp.reasoning_path) {
      resp.reasoning_path.starting_nodes?.forEach(n => addNode(n.id, n.label, n.type));
      resp.reasoning_path.expanded_nodes?.slice(0, 15).forEach(n => addNode(n.id, n.label, n.type));
    }

    const nodes = Array.from(nodeMap.values());
    nodesRef.current = nodes;

    // Build edges
    const edges: MiniEdge[] = [];
    if (resp.reasoning_path?.traversed_edges) {
      resp.reasoning_path.traversed_edges.slice(0, 30).forEach(e => {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (src && tgt) {
          edges.push({ source: src, target: tgt, progress: 0 });
        }
      });
    } else if (nodes.length > 1) {
      // Fallback: connect first node to others
      for (let i = 1; i < Math.min(nodes.length, 8); i++) {
        edges.push({ source: nodes[0], target: nodes[i], progress: 0 });
      }
    }
    edgesRef.current = edges;
  }, []);

  // Force simulation tick
  const tick = useCallback(() => {
    const nodes = nodesRef.current;
    const edges = edgesRef.current;
    const canvas = canvasRef.current;
    if (!canvas || nodes.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const now = performance.now();

    // Forces
    const repulsion = 800;
    const attraction = 0.04;
    const centerForce = 0.01;
    const damping = 0.85;

    for (const n of nodes) {
      if (n.fx != null) continue;
      // Center force
      n.vx += (W / 2 - n.x) * centerForce;
      n.vy += (H / 2 - n.y) * centerForce;

      // Repulsion
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

    // Attraction along edges
    for (const e of edges) {
      const dx = e.target.x - e.source.x;
      const dy = e.target.y - e.source.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist - 80) * attraction;
      if (!e.source.fx) {
        e.source.vx += (dx / dist) * force;
        e.source.vy += (dy / dist) * force;
      }
      if (!e.target.fx) {
        e.target.vx -= (dx / dist) * force;
        e.target.vy -= (dy / dist) * force;
      }
      // Animate draw-in
      e.progress = Math.min(1, e.progress + 0.015);
    }

    // Integrate
    for (const n of nodes) {
      if (n.fx != null) { n.x = n.fx; n.y = n.fy!; continue; }
      n.vx *= damping;
      n.vy *= damping;
      n.x = Math.max(20, Math.min(W - 20, n.x + n.vx));
      n.y = Math.max(20, Math.min(H - 20, n.y + n.vy));

      // Fade in
      n.opacity = Math.min(n.targetOpacity, n.opacity + 0.04);

      // Highlight decay
      if (n.highlighted) {
        n.highlightTimer -= 16;
        if (n.highlightTimer <= 0) {
          n.highlighted = false;
          n.scale = 1;
        } else {
          // Scale pulse: 1 → 1.3 → 1 over 800ms
          const t = 1 - n.highlightTimer / 800;
          n.scale = 1 + 0.3 * Math.sin(t * Math.PI);
        }
      }
    }

    // Draw
    ctx.clearRect(0, 0, W, H);

    // Edges
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
      ctx.lineTo(
        e.source.x + dx * e.progress,
        e.source.y + dy * e.progress
      );
      ctx.stroke();
      ctx.restore();
    }

    // Nodes
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

    // Hover label
    const hovered = hoveredNodeRef.current;
    if (hovered) {
      ctx.save();
      ctx.fillStyle = 'rgba(17,24,39,0.85)';
      const label = hovered.label.length > 20 ? hovered.label.slice(0, 20) + '…' : hovered.label;
      const textW = ctx.measureText(label).width;
      const px = 8, py = 4;
      const bx = Math.min(hovered.x - textW / 2 - px, W - textW - 2 * px - 4);
      const by = hovered.y - 28;
      ctx.beginPath();
      ctx.roundRect(bx, by, textW + 2 * px, 20, 4);
      ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.font = '11px system-ui, sans-serif';
      ctx.fillText(label, bx + px, by + 14);
      ctx.restore();
    }

    rafRef.current = requestAnimationFrame(tick);
  }, []);

  // Highlight a node by citation index
  const highlightNode = useCallback((citationIndex: number) => {
    const nodes = nodesRef.current;
    const node = nodes[citationIndex] ?? nodes.find(
      (_, i) => i === citationIndex
    );
    if (!node) return;
    node.highlighted = true;
    node.highlightTimer = 800;
    node.scale = 1;
  }, []);

  // Expose highlightNode to parent
  useEffect(() => {
    onHighlightRef?.(highlightNode);
  }, [highlightNode, onHighlightRef]);

  // Re-build graph when response changes
  useEffect(() => {
    if (!response) {
      nodesRef.current = [];
      edgesRef.current = [];
      return;
    }
    buildGraph(response);
    // Stagger node fade-in
    nodesRef.current.forEach((n, i) => {
      n.opacity = 0;
      n.targetOpacity = 1;
      // Delay each node by 30ms
      setTimeout(() => { n.targetOpacity = 1; }, i * 30);
    });
  }, [response, buildGraph]);

  // Start/stop RAF
  useEffect(() => {
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [tick]);

  // Canvas resize observer
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

  // Mouse interaction
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
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);
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
    const x = (e.clientX - rect.left) * (canvas.width / rect.width);
    const y = (e.clientY - rect.top) * (canvas.height / rect.height);
    const node = getNodeAt(x, y);
    if (node) onNodeClick(node.id);
  };

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-full"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
    />
  );
}
```

**Step 3:** Run dev server and verify no TypeScript errors:
```bash
cd frontend && npm run dev
```

**Step 4:** Commit:
```bash
git add frontend/src/components/graphrag/KnowledgeGraphMini.tsx
git commit -m "feat(graphrag): add KnowledgeGraphMini canvas force-directed graph component"
```

---

## Task 3: Create `SourceDetailCard` component

**Files:**
- Create: `frontend/src/components/graphrag/SourceDetailCard.tsx`

Displays source detail for a single `SourceCitation` node — label, type badge, Greek/Latin text if available, translation, and a link to the Visualizer.

**Step 1:** Create `frontend/src/components/graphrag/SourceDetailCard.tsx`:

```tsx
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import type { SourceCitation } from '../../types';

interface SourceDetailCardProps {
  source: SourceCitation;
  citationText?: { original: string; originalLanguage: string; translation: string };
  citationIndex: number;
  totalCitations: number;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
}

const NODE_TYPE_COLORS: Record<string, string> = {
  person:   'bg-blue-100 text-blue-800 border-blue-200',
  concept:  'bg-green-100 text-green-800 border-green-200',
  argument: 'bg-purple-100 text-purple-800 border-purple-200',
  work:     'bg-amber-100 text-amber-800 border-amber-200',
  default:  'bg-gray-100 text-gray-800 border-gray-200',
};

function getTypeColor(type: string) {
  return NODE_TYPE_COLORS[type.toLowerCase()] ?? NODE_TYPE_COLORS.default;
}

export default function SourceDetailCard({
  source,
  citationText,
  citationIndex,
  totalCitations,
  onClose,
  onPrev,
  onNext,
}: SourceDetailCardProps) {
  const navigate = useNavigate();

  return (
    <motion.div
      initial={{ y: '100%', opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: '100%', opacity: 0 }}
      transition={{ type: 'spring', damping: 28, stiffness: 280 }}
      className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-bold text-gray-900 text-sm">
            [{source.id}]
          </span>
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getTypeColor(source.nodeType)}`}>
            {source.nodeType || 'Source'}
          </span>
          <span className="text-sm font-medium text-gray-800 truncate">{source.nodeLabel}</span>
        </div>
        <button
          onClick={onClose}
          className="ml-2 shrink-0 p-1 rounded-full hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
          aria-label="Close source detail"
        >
          ✕
        </button>
      </div>

      {/* Body */}
      <div className="px-4 py-3 space-y-3 text-sm overflow-y-auto max-h-48">
        {citationText?.original && (
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              {citationText.originalLanguage === 'greek' ? 'Greek' :
               citationText.originalLanguage === 'latin' ? 'Latin' : 'Original'}
            </div>
            <p className="font-serif italic text-gray-800 leading-relaxed">
              {citationText.original}
            </p>
          </div>
        )}
        {citationText?.translation && (
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Translation</div>
            <p className="text-gray-700 leading-relaxed">{citationText.translation}</p>
          </div>
        )}
        {!citationText?.original && !citationText?.translation && (
          <p className="text-gray-500 italic text-xs">No passage text available for this source.</p>
        )}
        {source.metadata?.period && (
          <div className="text-xs text-gray-500">Period: {source.metadata.period}</div>
        )}
        {source.metadata?.school && (
          <div className="text-xs text-gray-500">School: {source.metadata.school}</div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100 bg-gray-50">
        <div className="flex items-center gap-2">
          <button
            onClick={onPrev}
            disabled={citationIndex <= 0}
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-30 transition-colors text-gray-600"
            aria-label="Previous source"
          >
            ‹
          </button>
          <span className="text-xs text-gray-500">{citationIndex + 1} / {totalCitations}</span>
          <button
            onClick={onNext}
            disabled={citationIndex >= totalCitations - 1}
            className="p-1 rounded hover:bg-gray-200 disabled:opacity-30 transition-colors text-gray-600"
            aria-label="Next source"
          >
            ›
          </button>
        </div>
        {source.nodeId && !source.nodeId.startsWith('source_') && (
          <button
            onClick={() => navigate(`/node/${source.nodeId}`)}
            className="text-xs text-blue-600 hover:text-blue-800 hover:underline transition-colors"
          >
            View in Visualizer →
          </button>
        )}
      </div>
    </motion.div>
  );
}
```

**Step 2:** Run dev server to verify no TypeScript errors.

**Step 3:** Commit:
```bash
git add frontend/src/components/graphrag/SourceDetailCard.tsx
git commit -m "feat(graphrag): add SourceDetailCard component with Greek/Latin text display"
```

---

## Task 4: Create `AdvancedOptions` disclosure component

**Files:**
- Create: `frontend/src/components/graphrag/AdvancedOptions.tsx`

Collapsible disclosure that hides all the mode checkboxes and parameter dropdowns behind a single toggle.

**Step 1:** Create `frontend/src/components/graphrag/AdvancedOptions.tsx`:

```tsx
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface AdvancedOptionsProps {
  // Mode flags
  academicMode: boolean;
  setAcademicMode: (v: boolean) => void;
  useThinking: boolean;
  setUseThinking: (v: boolean) => void;
  ancientOnly: boolean;
  setAncientOnly: (v: boolean) => void;
  agenticMode: boolean;
  setAgenticMode: (v: boolean) => void;
  // Parameter dropdowns
  semanticK: number;
  setSemanticK: (v: number) => void;
  graphDepth: number;
  setGraphDepth: (v: number) => void;
  maxContext: number;
  setMaxContext: (v: number) => void;
}

const CHECKBOX_MODES = [
  { key: 'academicMode', label: '🎓 Academic', color: 'text-blue-600', title: undefined },
  { key: 'useThinking', label: '🧠 Deep Reasoning', color: 'text-purple-600', title: undefined },
  { key: 'ancientOnly', label: '🏛️ Ancient Only', color: 'text-amber-600', title: 'Only use ancient sources (6th c. BCE – 6th c. CE)' },
  { key: 'agenticMode', label: '⚡ Agentic', color: 'text-orange-600', title: 'Full pydantic-AI pipeline (experimental, 30s cold start)' },
] as const;

export default function AdvancedOptions(props: AdvancedOptionsProps) {
  const [open, setOpen] = useState(false);

  const getValue = (key: typeof CHECKBOX_MODES[number]['key']) => props[key] as boolean;
  const setValue = (key: typeof CHECKBOX_MODES[number]['key'], v: boolean) => {
    const setters: Record<typeof CHECKBOX_MODES[number]['key'], (v: boolean) => void> = {
      academicMode: props.setAcademicMode,
      useThinking: props.setUseThinking,
      ancientOnly: props.setAncientOnly,
      agenticMode: props.setAgenticMode,
    };
    setters[key](v);
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
      >
        <svg
          className={`w-3.5 h-3.5 transition-transform ${open ? 'rotate-90' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        ⚙ Advanced options
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.22, ease: 'easeInOut' }}
            className="overflow-hidden w-full"
          >
            <div className="pt-2 space-y-3">
              {/* Checkboxes */}
              <div className="flex flex-wrap justify-center gap-x-6 gap-y-2">
                {CHECKBOX_MODES.map(mode => (
                  <label
                    key={mode.key}
                    className="flex items-center gap-2 cursor-pointer text-sm"
                    title={mode.title}
                  >
                    <input
                      type="checkbox"
                      checked={getValue(mode.key)}
                      onChange={e => setValue(mode.key, e.target.checked)}
                      className={`w-4 h-4 ${mode.color} bg-white border-gray-300 rounded focus:ring-2`}
                    />
                    <span className="text-gray-700">{mode.label}</span>
                  </label>
                ))}
              </div>

              {/* Parameters */}
              <div className="flex flex-wrap justify-center gap-3">
                {[
                  { label: 'Breadth', value: props.semanticK, set: props.setSemanticK, options: [5, 10, 15, 20] },
                  { label: 'Depth', value: props.graphDepth, set: props.setGraphDepth, options: [1, 2, 3] },
                  { label: 'Context', value: props.maxContext, set: props.setMaxContext, options: [10, 15, 20, 25] },
                ].map(p => (
                  <div key={p.label} className="flex items-center gap-2 text-xs bg-white/60 backdrop-blur-md px-4 py-2 rounded-full border border-gray-200">
                    <span className="text-gray-700">{p.label}:</span>
                    <select
                      value={p.value}
                      onChange={e => p.set(Number(e.target.value))}
                      className="px-2 py-0.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-black text-xs"
                    >
                      {p.options.map(o => (
                        <option key={o} value={o}>{o}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

**Step 2:** Run dev server, verify no TypeScript errors.

**Step 3:** Commit:
```bash
git add frontend/src/components/graphrag/AdvancedOptions.tsx
git commit -m "feat(graphrag): add AdvancedOptions collapsible disclosure component"
```

---

## Task 5: Create `RightPanel` container component

**Files:**
- Create: `frontend/src/components/graphrag/RightPanel.tsx`

Orchestrates the four states with `AnimatePresence`. When state is `graph`, shows `KnowledgeGraphMini` full height. When `source-detail`, shrinks graph to 40% and slides up `SourceDetailCard`.

**Step 1:** Create `frontend/src/components/graphrag/RightPanel.tsx`:

```tsx
import { motion, AnimatePresence } from 'framer-motion';
import KnowledgeGraphMini from './KnowledgeGraphMini';
import SourceDetailCard from './SourceDetailCard';
import type { GraphRAGResponse, SourceCitation } from '../../types';

type RightPanelState = 'idle' | 'loading' | 'graph' | 'source-detail';

interface RightPanelProps {
  state: RightPanelState;
  response: GraphRAGResponse | null;
  activeSourceIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onCloseDetail: () => void;
  onPrevSource: () => void;
  onNextSource: () => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
  className?: string;
}

export default function RightPanel({
  state,
  response,
  activeSourceIndex,
  onNodeClick,
  onCloseDetail,
  onPrevSource,
  onNextSource,
  onHighlightRef,
  className = '',
}: RightPanelProps) {
  const sources: SourceCitation[] = response?.sources ?? [];
  const activeSource = activeSourceIndex !== null ? sources[activeSourceIndex] ?? null : null;
  const citationTexts = (response as any)?.citationTexts;
  const activeCitationText = activeSource && citationTexts
    ? citationTexts[(activeSource as any)?.nodeLabel ?? ''] ?? citationTexts[Object.keys(citationTexts)[activeSourceIndex ?? 0] ?? ''] ?? undefined
    : undefined;

  return (
    <div className={`flex flex-col h-full relative ${className}`}>
      <AnimatePresence mode="wait">

        {/* IDLE */}
        {state === 'idle' && (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex flex-col items-center justify-center text-center px-6"
          >
            <div className="space-y-4">
              {/* Placeholder node outlines — pulse animation */}
              <div className="relative w-48 h-48 mx-auto">
                {[0, 1, 2, 3, 4].map(i => (
                  <motion.div
                    key={i}
                    className="absolute rounded-full border-2 border-gray-200"
                    style={{
                      width: 14 + i * 4,
                      height: 14 + i * 4,
                      left: `${20 + i * 14}%`,
                      top: `${15 + (i % 3) * 25}%`,
                    }}
                    animate={{ opacity: [0.3, 0.7, 0.3] }}
                    transition={{ duration: 1.8, repeat: Infinity, delay: i * 0.3 }}
                  />
                ))}
                {/* Faint lines between nodes */}
                <svg className="absolute inset-0 w-full h-full opacity-20" viewBox="0 0 200 200">
                  <line x1="40" y1="30" x2="80" y2="70" stroke="#9CA3AF" strokeWidth="1" />
                  <line x1="80" y1="70" x2="130" y2="50" stroke="#9CA3AF" strokeWidth="1" />
                  <line x1="80" y1="70" x2="100" y2="130" stroke="#9CA3AF" strokeWidth="1" />
                  <line x1="130" y1="50" x2="160" y2="100" stroke="#9CA3AF" strokeWidth="1" />
                </svg>
              </div>
              <p className="text-sm text-gray-400">Knowledge graph will appear here</p>
            </div>
          </motion.div>
        )}

        {/* LOADING */}
        {state === 'loading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex flex-col items-center justify-center gap-4 px-6"
          >
            {[0, 1, 2, 3].map(i => (
              <motion.div
                key={i}
                className="w-full h-8 rounded-lg bg-gray-100"
                animate={{ opacity: [0.3, 0.7, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.15 }}
              />
            ))}
            <div className="flex gap-3 mt-2">
              {[0, 1, 2].map(i => (
                <motion.div
                  key={i}
                  className="w-8 h-8 rounded-full bg-gray-100"
                  animate={{ opacity: [0.3, 0.7, 0.3] }}
                  transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                />
              ))}
            </div>
          </motion.div>
        )}

        {/* GRAPH (no source detail) */}
        {state === 'graph' && (
          <motion.div
            key="graph"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 relative"
          >
            <KnowledgeGraphMini
              response={response}
              activeCitationIndex={null}
              onNodeClick={onNodeClick}
              onHighlightRef={onHighlightRef}
            />
          </motion.div>
        )}

        {/* SOURCE DETAIL — graph shrinks to 40%, card slides up */}
        {state === 'source-detail' && (
          <motion.div
            key="source-detail"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col h-full"
          >
            {/* Graph top 40% */}
            <motion.div
              className="relative"
              style={{ flex: '0 0 40%' }}
            >
              <KnowledgeGraphMini
                response={response}
                activeCitationIndex={activeSourceIndex}
                onNodeClick={onNodeClick}
                onHighlightRef={onHighlightRef}
              />
            </motion.div>

            {/* Source detail card bottom 60% */}
            <div className="flex-1 p-3 overflow-hidden">
              <AnimatePresence mode="wait">
                {activeSource && (
                  <SourceDetailCard
                    key={activeSource.id}
                    source={activeSource}
                    citationText={activeCitationText}
                    citationIndex={activeSourceIndex!}
                    totalCitations={sources.length}
                    onClose={onCloseDetail}
                    onPrev={onPrevSource}
                    onNext={onNextSource}
                  />
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}
```

**Step 2:** Run dev server, verify no TypeScript errors.

**Step 3:** Commit:
```bash
git add frontend/src/components/graphrag/RightPanel.tsx
git commit -m "feat(graphrag): add RightPanel container with four animated states"
```

---

## Task 6: Refactor `GraphRAGPage` — two-column layout

**Files:**
- Modify: `frontend/src/pages/GraphRAGPage/index.tsx`

This is the largest task. It restructures the layout into the two-column design and wires everything together.

**Step 1:** Add the necessary imports at the top of `index.tsx`. After the existing imports, add:

```typescript
import RightPanel from '../../components/graphrag/RightPanel';
import AdvancedOptions from '../../components/graphrag/AdvancedOptions';
```

**Step 2:** Add the `onPrevSource` and `onNextSource` handlers next to `handleCitationClick`:

```typescript
const onPrevSource = () => {
  if (activeSourceIndex === null || activeSourceIndex <= 0) return;
  setActiveSourceIndex(prev => (prev !== null ? prev - 1 : null));
};

const onNextSource = () => {
  const sources = rightPanelResponse?.sources ?? [];
  if (activeSourceIndex === null || activeSourceIndex >= sources.length - 1) return;
  setActiveSourceIndex(prev => (prev !== null ? prev + 1 : null));
};
```

**Step 3:** Replace the entire `return (...)` block with the new two-column layout. The current return is lines 487-777. Replace it entirely with:

```tsx
return (
  <AuroraBackground className="!min-h-screen !h-auto">
    <div className="relative min-h-screen overflow-hidden">
      <div className="relative z-10 min-h-screen">

        {/* ─── WELCOME STATE ─── */}
        {messages.length === 0 && !streaming && (
          <div className="flex flex-col items-center justify-center min-h-[85vh] px-4 py-12">
            <div className="w-full max-w-2xl">

              {/* Header */}
              <motion.div
                className="text-center mb-10"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <h1 className="text-5xl md:text-6xl font-semibold text-gray-900 mb-3 drop-shadow-sm">
                  <Typewriter
                    text={["HiRAG", "Knowledge Graph", "Ancient Philosophy", "Scholarly Q&A"]}
                    speed={100}
                    waitTime={3500}
                    deleteSpeed={60}
                    className="text-gray-900"
                    cursorChar="_"
                  />
                </h1>
                <p className="text-base text-gray-600 max-w-lg mx-auto">
                  {t('graphrag.description')}
                </p>
              </motion.div>

              {/* Input */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="space-y-4"
              >
                <form onSubmit={handleSubmit}>
                  <ShineBorder
                    className="!p-0 bg-white/95 backdrop-blur-sm"
                    borderRadius={9999}
                    color={["#3B82F6", "#6366F1", "#06B6D4"]}
                  >
                    <div className="flex gap-3 p-2">
                      <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder={t('graphrag.placeholder')}
                        className="flex-1 px-6 py-3 text-base bg-transparent focus:outline-none focus:ring-0 border-0"
                        autoFocus
                        disabled={loading || streaming}
                      />
                      <button
                        type="submit"
                        disabled={!query.trim() || loading || streaming}
                        className="px-8 py-3 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all text-base font-medium whitespace-nowrap"
                      >
                        {loading ? 'Thinking...' : t('graphrag.ask')}
                      </button>
                    </div>
                  </ShineBorder>
                </form>

                {/* Advanced options */}
                <AdvancedOptions
                  academicMode={academicMode}
                  setAcademicMode={setAcademicMode}
                  useThinking={useThinking}
                  setUseThinking={setUseThinking}
                  ancientOnly={ancientOnly}
                  setAncientOnly={setAncientOnly}
                  agenticMode={agenticMode}
                  setAgenticMode={setAgenticMode}
                  semanticK={semanticK}
                  setSemanticK={setSemanticK}
                  graphDepth={graphDepth}
                  setGraphDepth={setGraphDepth}
                  maxContext={maxContext}
                  setMaxContext={setMaxContext}
                />

                {/* Try Demo link */}
                <div className="flex justify-center">
                  <button
                    type="button"
                    onClick={loadDemoMode}
                    className="text-sm text-gray-400 hover:text-gray-700 transition-colors"
                  >
                    Try Demo
                  </button>
                </div>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 px-6 py-4 bg-red-50 border border-red-200 text-red-800 rounded-2xl text-sm text-center"
                  >
                    {error}
                  </motion.div>
                )}
              </motion.div>
            </div>
          </div>
        )}

        {/* ─── TWO-COLUMN LAYOUT (streaming or has messages) ─── */}
        {(messages.length > 0 || streaming) && (
          <motion.div
            layout
            className="flex h-screen overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
          >

            {/* LEFT PANEL — 65% */}
            <div className="flex flex-col w-full lg:w-[65%] h-full overflow-hidden border-r border-gray-100">

              {/* Fixed header */}
              <div className="shrink-0 flex items-center justify-between px-6 py-3 border-b border-gray-100 bg-white/80 backdrop-blur-sm">
                <h1 className="text-lg font-semibold text-gray-800 tracking-tight">HiRAG Q&A</h1>
              </div>

              {/* Scrollable messages */}
              <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
                <AnimatePresence>
                  {messages.map((message, index) => (
                    <MessageBubble
                      key={index}
                      message={message}
                      onNodeClick={handleNodeClick}
                      onCitationClick={handleCitationClick}
                    />
                  ))}
                </AnimatePresence>

                {/* Streaming state */}
                {streaming && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="flex justify-center items-center min-h-[50vh]"
                  >
                    <TerminalLoader size="large" title={agenticMode ? "Pydantic-AI Engine" : undefined} />
                  </motion.div>
                )}

                {error && !loading && !streaming && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="px-6 py-4 bg-red-50 border border-red-200 text-red-800 rounded-2xl text-sm text-center"
                  >
                    <div className="font-medium mb-1">Query failed</div>
                    {error}
                    <button onClick={() => setError(null)} className="mt-2 text-red-600 hover:text-red-800 underline text-xs block mx-auto">Dismiss</button>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Sticky input */}
              <div className="shrink-0 px-4 py-3 border-t border-gray-100 bg-white/80 backdrop-blur-sm">
                <ShineBorder
                  className="!p-0 bg-white/95 backdrop-blur-sm shadow-sm"
                  borderRadius={9999}
                  color={["#3B82F6", "#6366F1", "#06B6D4"]}
                >
                  <form onSubmit={handleSubmit} className="p-2">
                    <div className="flex gap-2">
                      <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder={t('graphrag.placeholder')}
                        disabled={loading || streaming}
                        className="flex-1 px-6 py-3 text-base bg-transparent focus:outline-none focus:ring-0 border-0"
                      />
                      {streaming ? (
                        <button
                          type="button"
                          onClick={stopStreaming}
                          className="px-6 py-3 bg-red-600 text-white rounded-full hover:bg-red-700 font-medium transition-all"
                        >
                          Stop
                        </button>
                      ) : (
                        <button
                          type="submit"
                          disabled={loading || !query.trim()}
                          className="px-6 py-3 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
                        >
                          {loading ? 'Thinking...' : 'Ask'}
                        </button>
                      )}
                    </div>
                  </form>
                </ShineBorder>
              </div>
            </div>

            {/* RIGHT PANEL — 35% (desktop only) */}
            <div className="hidden lg:flex flex-col w-[35%] h-full bg-gray-50/80 backdrop-blur-sm">
              <div className="shrink-0 px-4 py-3 border-b border-gray-100">
                <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Knowledge Graph</h2>
              </div>
              <div className="flex-1 overflow-hidden">
                <RightPanel
                  state={rightPanelState}
                  response={rightPanelResponse}
                  activeSourceIndex={activeSourceIndex}
                  onNodeClick={handleNodeClick}
                  onCloseDetail={() => setRightPanelState('graph')}
                  onPrevSource={onPrevSource}
                  onNextSource={onNextSource}
                  onHighlightRef={(fn) => { highlightNodeRef.current = fn; }}
                  className="h-full"
                />
              </div>
            </div>

            {/* MOBILE: floating 📊 button + bottom sheet */}
            <MobileGraphButton
              rightPanelState={rightPanelState}
              response={rightPanelResponse}
              activeSourceIndex={activeSourceIndex}
              onNodeClick={handleNodeClick}
              onCloseDetail={() => setRightPanelState('graph')}
              onPrevSource={onPrevSource}
              onNextSource={onNextSource}
              onHighlightRef={(fn) => { highlightNodeRef.current = fn; }}
            />

          </motion.div>
        )}

      </div>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => { setShowAuthModal(false); setPendingQuery(null); }}
        onSuccess={handleAuthSuccess}
        title="Authentication Required"
        message="Please log in to use HiRAG Q&A"
      />

      {selectedNode && (
        <NodeDetailPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  </AuroraBackground>
);
```

**Step 4:** Run the dev server. You'll see TypeScript errors for `MobileGraphButton` and the updated `MessageBubble` signature (which gains an `onCitationClick` prop). These will be fixed in Tasks 7 and 8. For now just confirm the layout compiles otherwise.

**Step 5:** Commit what works:
```bash
git add frontend/src/pages/GraphRAGPage/index.tsx
git commit -m "feat(graphrag): restructure GraphRAGPage to two-column layout"
```

---

## Task 7: Update `MessageBubble` — remove inline panels, add `onCitationClick`

**Files:**
- Modify: `frontend/src/pages/GraphRAGPage/index.tsx` (the `MessageBubble` function at the bottom)

Remove `SourcesPanel`, reasoning path accordion, citations collapsible, `EvidenceChainPanel`, `BibliographyPanel` from the bubble. Wire `CitationRenderer`'s existing `onNodeClick` to also call `onCitationClick`.

**Step 1:** Find the `MessageBubble` function (line ~783). Update the props interface to add `onCitationClick`:

```typescript
function MessageBubble({
  message,
  onNodeClick,
  onCitationClick,
}: {
  message: GraphRAGChatMessage;
  onNodeClick: (nodeId: string) => void;
  onCitationClick: (citationIndex: number) => void;
})
```

**Step 2:** Remove all the internal state for `showCitations` and `showReasoningPath`.

**Step 3:** Replace the assistant content block. The bubble body should become:

```tsx
{message.role === 'user' ? (
  <p className="text-base leading-relaxed">{message.content}</p>
) : (
  <div className="space-y-3">

    {/* Service badge */}
    {message.graphrag_response?.service && (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
        <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        {message.graphrag_response.service}
      </span>
    )}

    {/* Answer text with inline citation superscripts */}
    {message.graphrag_response?.sources ? (
      <div className="prose prose-sm max-w-none">
        <CitationRenderer
          content={message.content}
          sources={message.graphrag_response.sources}
          onNodeClick={(nodeId) => {
            // Find citation index by nodeId
            const idx = message.graphrag_response!.sources!.findIndex(s => s.nodeId === nodeId);
            onNodeClick(nodeId);
            if (idx !== -1) onCitationClick(idx);
          }}
        />
      </div>
    ) : (
      <div className="prose prose-sm max-w-none">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>
    )}

  </div>
)}
```

**Step 4:** Remove the imports for `BibliographyPanel`, `EvidenceChainPanel`, `SourcesPanel` from the top of the file only if they are no longer used anywhere else. Check before removing — they may still be in the codebase for other uses. Leave the imports but remove the usage from `MessageBubble`.

**Step 5:** Run dev server, verify no TypeScript errors. The bubble should now only show answer text.

**Step 6:** Commit:
```bash
git add frontend/src/pages/GraphRAGPage/index.tsx
git commit -m "feat(graphrag): simplify MessageBubble to answer-only with citation click wiring"
```

---

## Task 8: Add `MobileGraphButton` component (inside `index.tsx`)

**Files:**
- Modify: `frontend/src/pages/GraphRAGPage/index.tsx`

Add the `MobileGraphButton` helper component right after the closing `}` of the `MessageBubble` function, at the bottom of `index.tsx`.

**Step 1:** Add this component at the end of `index.tsx` (after `MessageBubble`):

```tsx
// ─── Mobile Graph Button ──────────────────────────────────────────────────────

import { BottomSheet } from '../../components/ui/BottomSheet';

function MobileGraphButton({
  rightPanelState,
  response,
  activeSourceIndex,
  onNodeClick,
  onCloseDetail,
  onPrevSource,
  onNextSource,
  onHighlightRef,
}: {
  rightPanelState: 'idle' | 'loading' | 'graph' | 'source-detail';
  response: GraphRAGResponse | null;
  activeSourceIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onCloseDetail: () => void;
  onPrevSource: () => void;
  onNextSource: () => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);

  if (rightPanelState === 'idle') return null;

  return (
    <>
      {/* Floating button */}
      <motion.button
        className="fixed bottom-24 right-4 z-50 flex lg:hidden items-center justify-center w-12 h-12 rounded-full bg-gray-900 text-white shadow-lg"
        onClick={() => setIsOpen(true)}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        aria-label="Open knowledge graph"
      >
        📊
      </motion.button>

      {/* Bottom sheet */}
      <BottomSheet
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Knowledge Graph"
        height="60%"
        showHandle
        dragToClose
      >
        <div className="h-full min-h-[300px]">
          <RightPanel
            state={rightPanelState}
            response={response}
            activeSourceIndex={activeSourceIndex}
            onNodeClick={onNodeClick}
            onCloseDetail={onCloseDetail}
            onPrevSource={onPrevSource}
            onNextSource={onNextSource}
            onHighlightRef={onHighlightRef}
            className="h-full"
          />
        </div>
      </BottomSheet>
    </>
  );
}
```

**Note:** The `import { BottomSheet }` statement must move to the top of the file with the other imports, not inline here.

**Step 2:** Move `import { BottomSheet } from '../../components/ui/BottomSheet';` to the top of `index.tsx` with the other imports.

**Step 3:** Run dev server and verify the layout works:
- Welcome state: single input, typewriter title, `⚙ Advanced options` disclosure, Try Demo link
- After query / demo: two columns on `lg+`, single column on mobile with 📊 button
- No TypeScript errors

**Step 4:** Commit:
```bash
git add frontend/src/pages/GraphRAGPage/index.tsx
git commit -m "feat(graphrag): add MobileGraphButton with BottomSheet for mobile right panel"
```

---

## Task 9: Clean up unused imports

**Files:**
- Modify: `frontend/src/pages/GraphRAGPage/index.tsx`

**Step 1:** Run a check for unused imports by looking at what's no longer referenced in the JSX:

After all previous tasks, these imports from `index.tsx` might now be unused in the render:
- `CitationPreview` (was in the old citations collapsible) — check if still used elsewhere in the file
- `BibliographyPanel` — check if still used
- `EvidenceChainPanel` — check if still used

**Step 2:** Remove imports that are truly unused. Do NOT remove `SourcesPanel` or `CitationRenderer` if they're still used.

**Step 3:** Run:
```bash
cd frontend && npm run build 2>&1 | grep "TS" | head -30
```
Expected: zero TypeScript errors. If there are warnings about unused variables (`_setLoading`, `_streamStatus`, etc.), those already existed — don't introduce new ones.

**Step 4:** Run `npm run build` to completion. Expected: successful build with no new errors.

**Step 5:** Commit:
```bash
git add frontend/src/pages/GraphRAGPage/index.tsx
git commit -m "chore(graphrag): remove unused imports after UX redesign"
```

---

## Task 10: Visual verification with browser-use

**Step 1:** Start the dev server:
```bash
cd frontend && npm run dev
```

**Step 2:** Open browser to `http://localhost:5173/graphrag` (or wherever the route is).

**Step 3:** Verify welcome state:
- Full-width centered input
- Typewriter animation in title
- `⚙ Advanced options` link — clicking expands checkboxes + dropdowns
- `Try Demo` as a plain text link (not a button)
- No stats pills visible

**Step 4:** Click `Try Demo`:
- Layout shifts to two-column
- Left panel: shows user message + assistant answer with `[n]` citation markers
- Right panel: mini knowledge graph appears with animated nodes and edges

**Step 5:** Click a `[n]` citation in the answer:
- Right panel: graph shrinks to 40% height
- Source detail card slides up with source info
- Navigation arrows (prev/next) work

**Step 6:** Verify mobile: resize browser to < `lg` (1024px):
- Right panel hidden
- 📊 button appears (bottom right, above input)
- Clicking opens bottom sheet with graph

**Step 7:** If all looks correct, proceed to deploy. If any issue, fix before committing.

---

## Task 11: Deploy to production

**Step 1:** Run final build check:
```bash
cd frontend && npm run build
```
Expected: successful build.

**Step 2:** Deploy:
```bash
vercel --prod
```

**Step 3:** Verify live site at `https://free-will.app/graphrag`.
