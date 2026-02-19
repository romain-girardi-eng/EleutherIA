# GraphRAG UI Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Polish the GraphRAG dual-panel frontend to professional UI/UX level with Cosmograph WebGL graph, Radix UI controls, and light modern SaaS aesthetic.

**Architecture:** Extract the 998-line `GraphRAGPage/index.tsx` monolith into focused components, replace the hand-rolled canvas graph with Cosmograph, replace native form controls with Radix UI primitives styled with Tailwind, and apply consistent spacing/color/typography across all GraphRAG components.

**Tech Stack:** React 19, TypeScript, @cosmograph/react v2, Radix UI (Switch, Select, Tooltip), Tailwind CSS, Framer Motion, Lucide React

---

## Task 1: Install missing Radix UI dependencies

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install Radix primitives**

Run from `frontend/`:
```bash
npm install @radix-ui/react-switch @radix-ui/react-select @radix-ui/react-tooltip @radix-ui/react-popover
```

**Step 2: Verify install**

Run: `npm ls @radix-ui/react-switch @radix-ui/react-select @radix-ui/react-tooltip`
Expected: All three packages listed without errors

**Step 3: Verify build still works**

Run: `cd frontend && npm run build`
Expected: Build completes with no new errors

**Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: add Radix UI Switch, Select, Tooltip, Popover"
```

---

## Task 2: Create shared UI primitives (Toggle, Select, Tooltip)

**Files:**
- Create: `frontend/src/components/ui/Toggle.tsx`
- Create: `frontend/src/components/ui/RadixSelect.tsx`
- Create: `frontend/src/components/ui/RadixTooltip.tsx`

These wrap Radix primitives with Tailwind styling consistent with the project's light SaaS aesthetic.

**Step 1: Create Toggle component**

Create `frontend/src/components/ui/Toggle.tsx`:

```tsx
import * as Switch from '@radix-ui/react-switch';
import { cn } from '../../utils/cn';

interface ToggleProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  label: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export function Toggle({ checked, onCheckedChange, label, description, disabled, className }: ToggleProps) {
  return (
    <label
      className={cn(
        'inline-flex items-center gap-2.5 cursor-pointer select-none',
        disabled && 'opacity-50 cursor-not-allowed',
        className,
      )}
      title={description}
    >
      <Switch.Root
        checked={checked}
        onCheckedChange={onCheckedChange}
        disabled={disabled}
        className={cn(
          'relative h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2',
          checked ? 'bg-blue-600' : 'bg-gray-200',
        )}
      >
        <Switch.Thumb
          className={cn(
            'pointer-events-none block h-5 w-5 rounded-full bg-white shadow-sm ring-0 transition-transform',
            checked ? 'translate-x-5' : 'translate-x-0',
          )}
        />
      </Switch.Root>
      <span className="text-sm text-gray-700">{label}</span>
    </label>
  );
}
```

**Step 2: Create RadixSelect component**

Create `frontend/src/components/ui/RadixSelect.tsx`:

```tsx
import * as Select from '@radix-ui/react-select';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '../../utils/cn';

interface RadixSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  options: { value: string; label: string }[];
  label?: string;
  placeholder?: string;
  className?: string;
}

export function RadixSelect({ value, onValueChange, options, label, placeholder, className }: RadixSelectProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      {label && <span className="text-xs font-medium text-gray-500">{label}</span>}
      <Select.Root value={value} onValueChange={onValueChange}>
        <Select.Trigger
          className={cn(
            'inline-flex items-center justify-between gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-800',
            'hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1',
            'transition-colors min-w-[60px]',
          )}
        >
          <Select.Value placeholder={placeholder} />
          <Select.Icon>
            <ChevronDown className="h-3 w-3 text-gray-400" />
          </Select.Icon>
        </Select.Trigger>

        <Select.Portal>
          <Select.Content
            className="z-50 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg animate-in fade-in-0 zoom-in-95"
            position="popper"
            sideOffset={4}
          >
            <Select.Viewport className="p-1">
              {options.map((opt) => (
                <Select.Item
                  key={opt.value}
                  value={opt.value}
                  className={cn(
                    'relative flex items-center rounded-md px-3 py-1.5 text-xs text-gray-800 outline-none cursor-pointer',
                    'hover:bg-blue-50 hover:text-blue-700 focus:bg-blue-50 focus:text-blue-700',
                    'data-[state=checked]:font-medium',
                  )}
                >
                  <Select.ItemText>{opt.label}</Select.ItemText>
                  <Select.ItemIndicator className="ml-auto">
                    <Check className="h-3 w-3" />
                  </Select.ItemIndicator>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
    </div>
  );
}
```

**Step 3: Create RadixTooltip component**

Create `frontend/src/components/ui/RadixTooltip.tsx`:

```tsx
import * as Tooltip from '@radix-ui/react-tooltip';
import { cn } from '../../utils/cn';

interface RadixTooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  side?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
  delayDuration?: number;
}

export function RadixTooltip({ content, children, side = 'top', className, delayDuration = 300 }: RadixTooltipProps) {
  return (
    <Tooltip.Provider delayDuration={delayDuration}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            side={side}
            sideOffset={6}
            className={cn(
              'z-50 rounded-lg bg-gray-900 px-3 py-2 text-xs text-white shadow-xl',
              'animate-in fade-in-0 zoom-in-95',
              'max-w-xs leading-relaxed',
              className,
            )}
          >
            {content}
            <Tooltip.Arrow className="fill-gray-900" width={10} height={5} />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
```

**Step 4: Verify build**

Run: `cd frontend && npm run build`
Expected: Build completes without errors

**Step 5: Commit**

```bash
git add frontend/src/components/ui/Toggle.tsx frontend/src/components/ui/RadixSelect.tsx frontend/src/components/ui/RadixTooltip.tsx
git commit -m "feat(ui): add Radix Toggle, Select, Tooltip primitives"
```

---

## Task 3: Create CosmographView component

Replace the hand-rolled canvas `KnowledgeGraphMini` with Cosmograph WebGL.

**Files:**
- Create: `frontend/src/components/graphrag/CosmographView.tsx`
- Create: `frontend/src/components/graphrag/GraphLegend.tsx`

**Reference:** The existing `frontend/src/components/CosmographKGVisualizer.tsx` uses the same `@cosmograph/react` API and `TYPE_COLORS` palette. Follow its patterns for Cosmograph setup.

**Step 1: Create GraphLegend component**

Create `frontend/src/components/graphrag/GraphLegend.tsx`:

```tsx
import { cn } from '../../utils/cn';

const LEGEND_ITEMS = [
  { type: 'person', label: 'Person', color: '#60A5FA' },
  { type: 'concept', label: 'Concept', color: '#4ADE80' },
  { type: 'argument', label: 'Argument', color: '#C084FC' },
  { type: 'work', label: 'Work', color: '#FBBF24' },
];

interface GraphLegendProps {
  className?: string;
}

export default function GraphLegend({ className }: GraphLegendProps) {
  return (
    <div className={cn('flex items-center gap-3 px-3 py-2 bg-white/90 backdrop-blur-sm rounded-lg border border-gray-100 shadow-sm', className)}>
      {LEGEND_ITEMS.map((item) => (
        <div key={item.type} className="flex items-center gap-1.5">
          <span
            className="inline-block w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-[10px] font-medium text-gray-500">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
```

**Step 2: Create CosmographView component**

Create `frontend/src/components/graphrag/CosmographView.tsx`:

```tsx
import { useRef, useMemo, useCallback, useEffect, useState } from 'react';
import { Cosmograph, CosmographProvider } from '@cosmograph/react';
import type { CosmographRef } from '@cosmograph/react';
import { ZoomIn, ZoomOut, Maximize2, Pause, Play } from 'lucide-react';
import GraphLegend from './GraphLegend';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse } from '../../types';

const NODE_COLORS: Record<string, string> = {
  person: '#60A5FA',
  concept: '#4ADE80',
  argument: '#C084FC',
  work: '#FBBF24',
  school: '#4ADE80',
  debate: '#FB7185',
  quote: '#FACC15',
  passage: '#94A3B8',
  publication: '#06B6D4',
  default: '#94A3B8',
};

interface GraphNode {
  id: string;
  label: string;
  type: string;
}

interface GraphLink {
  source: string;
  target: string;
}

interface CosmographViewProps {
  response: GraphRAGResponse | null;
  highlightedNodeIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
  className?: string;
  showControls?: boolean;
}

export default function CosmographView({
  response,
  highlightedNodeIndex,
  onNodeClick,
  onHighlightRef,
  className,
  showControls = true,
}: CosmographViewProps) {
  const cosmographRef = useRef<CosmographRef<GraphNode, GraphLink>>(null);
  const [isPaused, setIsPaused] = useState(false);

  const { nodes, links } = useMemo(() => {
    if (!response) return { nodes: [], links: [] };

    const nodeMap = new Map<string, GraphNode>();
    const addNode = (id: string, label: string, type: string) => {
      if (!nodeMap.has(id)) nodeMap.set(id, { id, label, type });
    };

    response.sources?.slice(0, 25).forEach((s) => addNode(s.nodeId, s.nodeLabel, s.nodeType));
    response.reasoning_path?.starting_nodes?.forEach((n) => addNode(n.id, n.label, n.type));
    response.reasoning_path?.expanded_nodes?.slice(0, 15).forEach((n) => addNode(n.id, n.label, n.type));

    const nodes = Array.from(nodeMap.values());
    const links: GraphLink[] = [];

    if (response.reasoning_path?.traversed_edges) {
      response.reasoning_path.traversed_edges.slice(0, 30).forEach((e) => {
        if (nodeMap.has(e.source) && nodeMap.has(e.target)) {
          links.push({ source: e.source, target: e.target });
        }
      });
    } else if (nodes.length > 1) {
      for (let i = 1; i < Math.min(nodes.length, 8); i++) {
        links.push({ source: nodes[0].id, target: nodes[i].id });
      }
    }

    return { nodes, links };
  }, [response]);

  // Highlight a node by citation index
  const highlightNode = useCallback(
    (citationIndex: number) => {
      const node = nodes[citationIndex];
      if (node && cosmographRef.current) {
        cosmographRef.current.zoomToNode(node, 800);
        cosmographRef.current.selectNodes([node]);
      }
    },
    [nodes],
  );

  useEffect(() => {
    onHighlightRef?.(highlightNode);
  }, [highlightNode, onHighlightRef]);

  // Auto-highlight when highlightedNodeIndex changes
  useEffect(() => {
    if (highlightedNodeIndex !== null) highlightNode(highlightedNodeIndex);
  }, [highlightedNodeIndex, highlightNode]);

  const handleNodeClick = useCallback(
    (node: GraphNode | undefined) => {
      if (node) onNodeClick(node.id);
    },
    [onNodeClick],
  );

  const handleZoomIn = () => cosmographRef.current?.zoom(1.5, 400);
  const handleZoomOut = () => cosmographRef.current?.zoom(0.67, 400);
  const handleFitView = () => cosmographRef.current?.fitView(400);
  const handleTogglePause = () => {
    if (isPaused) cosmographRef.current?.restart();
    else cosmographRef.current?.pause();
    setIsPaused(!isPaused);
  };

  if (nodes.length === 0) return null;

  return (
    <div className={cn('relative w-full h-full', className)}>
      <CosmographProvider nodes={nodes} links={links}>
        <Cosmograph
          ref={cosmographRef}
          nodes={nodes}
          links={links}
          nodeColor={(n) => NODE_COLORS[n.type?.toLowerCase()] ?? NODE_COLORS.default}
          nodeSize={8}
          nodeLabelAccessor={(n) => n.label}
          nodeLabelColor="#374151"
          linkColor="#D1D5DB"
          linkWidth={1}
          backgroundColor="#ffffff"
          simulationRepulsion={0.5}
          simulationLinkSpring={1.0}
          simulationLinkDistance={5}
          simulationGravity={0.15}
          simulationDecay={3000}
          onClick={handleNodeClick}
          showDynamicLabels
        />
      </CosmographProvider>

      {/* Control buttons */}
      {showControls && (
        <div className="absolute top-3 right-3 flex flex-col gap-1.5">
          {[
            { icon: ZoomIn, onClick: handleZoomIn, label: 'Zoom in' },
            { icon: ZoomOut, onClick: handleZoomOut, label: 'Zoom out' },
            { icon: Maximize2, onClick: handleFitView, label: 'Fit view' },
            { icon: isPaused ? Play : Pause, onClick: handleTogglePause, label: isPaused ? 'Resume' : 'Pause' },
          ].map(({ icon: Icon, onClick, label }) => (
            <button
              key={label}
              onClick={onClick}
              className="flex items-center justify-center w-8 h-8 rounded-lg bg-white/90 border border-gray-200 text-gray-500 hover:text-gray-700 hover:border-gray-300 shadow-sm transition-all hover:shadow"
              aria-label={label}
              title={label}
            >
              <Icon className="w-3.5 h-3.5" />
            </button>
          ))}
        </div>
      )}

      {/* Legend */}
      <GraphLegend className="absolute bottom-3 left-3" />
    </div>
  );
}
```

**Step 3: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds (components are not yet used but should compile)

**Step 4: Commit**

```bash
git add frontend/src/components/graphrag/CosmographView.tsx frontend/src/components/graphrag/GraphLegend.tsx
git commit -m "feat(graphrag): add CosmographView and GraphLegend components"
```

---

## Task 4: Rewrite AdvancedOptions with Radix primitives

**Files:**
- Modify: `frontend/src/components/graphrag/AdvancedOptions.tsx`

Replace native `<input type="checkbox">` and `<select>` with the new `Toggle` and `RadixSelect` components.

**Step 1: Rewrite AdvancedOptions**

Replace the entire contents of `frontend/src/components/graphrag/AdvancedOptions.tsx` with:

```tsx
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings2 } from 'lucide-react';
import { Toggle } from '../ui/Toggle';
import { RadixSelect } from '../ui/RadixSelect';
import { RadixTooltip } from '../ui/RadixTooltip';

interface AdvancedOptionsProps {
  academicMode: boolean;
  setAcademicMode: (v: boolean) => void;
  useThinking: boolean;
  setUseThinking: (v: boolean) => void;
  ancientOnly: boolean;
  setAncientOnly: (v: boolean) => void;
  agenticMode: boolean;
  setAgenticMode: (v: boolean) => void;
  semanticK: number;
  setSemanticK: (v: number) => void;
  graphDepth: number;
  setGraphDepth: (v: number) => void;
  maxContext: number;
  setMaxContext: (v: number) => void;
}

const TOGGLE_MODES = [
  { key: 'academicMode' as const, label: 'Academic', description: 'Enable scholarly citation format and academic language' },
  { key: 'useThinking' as const, label: 'Deep Reasoning', description: 'Use extended thinking for complex questions (slower, more thorough)' },
  { key: 'ancientOnly' as const, label: 'Ancient Only', description: 'Only use ancient sources (6th c. BCE - 6th c. CE)' },
  { key: 'agenticMode' as const, label: 'Agentic', description: 'Full Pydantic-AI pipeline (experimental, 30s cold start)' },
] as const;

const PARAMETERS = [
  { label: 'Breadth', key: 'semanticK' as const, setKey: 'setSemanticK' as const, options: ['5', '10', '15', '20'] },
  { label: 'Depth', key: 'graphDepth' as const, setKey: 'setGraphDepth' as const, options: ['1', '2', '3'] },
  { label: 'Context', key: 'maxContext' as const, setKey: 'setMaxContext' as const, options: ['10', '15', '20', '25'] },
];

export default function AdvancedOptions(props: AdvancedOptionsProps) {
  const [open, setOpen] = useState(false);

  const getToggleValue = (key: typeof TOGGLE_MODES[number]['key']): boolean => {
    return props[key] as boolean;
  };

  const setToggleValue = (key: typeof TOGGLE_MODES[number]['key'], value: boolean) => {
    const setters: Record<string, (v: boolean) => void> = {
      academicMode: props.setAcademicMode,
      useThinking: props.setUseThinking,
      ancientOnly: props.setAncientOnly,
      agenticMode: props.setAgenticMode,
    };
    setters[key]?.(value);
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-600 transition-colors"
      >
        <Settings2 className={`w-3.5 h-3.5 transition-transform duration-200 ${open ? 'rotate-90' : ''}`} />
        Advanced options
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
            <div className="pt-3 space-y-4">
              {/* Mode toggles */}
              <div className="flex flex-wrap justify-center gap-x-5 gap-y-3">
                {TOGGLE_MODES.map((mode) => (
                  <RadixTooltip key={mode.key} content={mode.description}>
                    <div>
                      <Toggle
                        checked={getToggleValue(mode.key)}
                        onCheckedChange={(v) => setToggleValue(mode.key, v)}
                        label={mode.label}
                      />
                    </div>
                  </RadixTooltip>
                ))}
              </div>

              {/* Parameter selects */}
              <div className="flex flex-wrap justify-center gap-3">
                {PARAMETERS.map((p) => (
                  <RadixSelect
                    key={p.label}
                    label={p.label}
                    value={String(props[p.key])}
                    onValueChange={(v) => props[p.setKey](Number(v))}
                    options={p.options.map((o) => ({ value: o, label: o }))}
                  />
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

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/graphrag/AdvancedOptions.tsx
git commit -m "feat(graphrag): rewrite AdvancedOptions with Radix Toggle/Select/Tooltip"
```

---

## Task 5: Redesign RightPanel states + integrate Cosmograph

**Files:**
- Modify: `frontend/src/components/graphrag/RightPanel.tsx`

Replace the canvas-based graph with `CosmographView` and redesign idle/loading states.

**Step 1: Rewrite RightPanel**

Replace the entire contents of `frontend/src/components/graphrag/RightPanel.tsx` with:

```tsx
import { AnimatePresence, motion } from 'framer-motion';
import { Network } from 'lucide-react';
import CosmographView from './CosmographView';
import SourceDetailCard from './SourceDetailCard';
import { cn } from '../../utils/cn';
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
  const activeSource =
    activeSourceIndex !== null && activeSourceIndex < sources.length
      ? sources[activeSourceIndex]
      : null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const citationTexts = (response as any)?.citationTexts as
    | Record<string, { original: string; originalLanguage: string; translation: string }>
    | undefined;
  const activeCitationText =
    activeSource && citationTexts
      ? (citationTexts[activeSource.nodeLabel] ??
        Object.values(citationTexts)[activeSourceIndex ?? 0] ??
        undefined)
      : undefined;

  return (
    <div className={cn('flex flex-col h-full relative overflow-hidden', className)}>
      <AnimatePresence mode="wait">
        {/* IDLE */}
        {state === 'idle' && (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col items-center justify-center text-center px-8 h-full"
          >
            <div className="space-y-5">
              <div className="mx-auto flex items-center justify-center w-16 h-16 rounded-2xl bg-gray-100">
                <Network className="w-7 h-7 text-gray-400" />
              </div>
              <div className="space-y-1.5">
                <p className="text-sm font-medium text-gray-500">Knowledge Graph</p>
                <p className="text-xs text-gray-400 max-w-[200px] mx-auto leading-relaxed">
                  Ask a question to see the knowledge graph and its connections
                </p>
              </div>
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
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col items-center justify-center gap-4 px-6 h-full"
          >
            {/* Animated radar pulse */}
            <div className="relative w-20 h-20">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  className="absolute inset-0 rounded-full border-2 border-blue-300"
                  initial={{ scale: 0.3, opacity: 0.8 }}
                  animate={{ scale: 1.5, opacity: 0 }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    delay: i * 0.6,
                    ease: 'easeOut',
                  }}
                />
              ))}
              <div className="absolute inset-0 flex items-center justify-center">
                <Network className="w-6 h-6 text-blue-500" />
              </div>
            </div>
            <div className="text-center space-y-1">
              <p className="text-sm font-medium text-gray-600">Building knowledge graph</p>
              <motion.p
                className="text-xs text-gray-400"
                animate={{ opacity: [0.4, 1, 0.4] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                Traversing connections...
              </motion.p>
            </div>
          </motion.div>
        )}

        {/* GRAPH */}
        {state === 'graph' && (
          <motion.div
            key="graph"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex-1 h-full"
          >
            <CosmographView
              response={response}
              highlightedNodeIndex={null}
              onNodeClick={onNodeClick}
              onHighlightRef={onHighlightRef}
            />
          </motion.div>
        )}

        {/* SOURCE DETAIL */}
        {state === 'source-detail' && (
          <motion.div
            key="source-detail"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col h-full"
          >
            {/* Graph top 40% */}
            <div style={{ flex: '0 0 40%' }} className="relative overflow-hidden">
              <CosmographView
                response={response}
                highlightedNodeIndex={activeSourceIndex}
                onNodeClick={onNodeClick}
                onHighlightRef={onHighlightRef}
                showControls={false}
              />
            </div>

            {/* Source detail card bottom 60% */}
            <div className="flex-1 p-3 overflow-hidden">
              <AnimatePresence mode="wait">
                {activeSource ? (
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
                ) : (
                  <motion.div
                    key="no-source"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center justify-center h-full text-sm text-gray-400"
                  >
                    No source selected
                  </motion.div>
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

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/graphrag/RightPanel.tsx
git commit -m "feat(graphrag): redesign RightPanel with Cosmograph and polished states"
```

---

## Task 6: Restyle SourceDetailCard

**Files:**
- Modify: `frontend/src/components/graphrag/SourceDetailCard.tsx`

Polish the card with modern SaaS styling: rounded-xl, better typography, horizontal slide animations for prev/next.

**Step 1: Rewrite SourceDetailCard**

Replace the entire contents of `frontend/src/components/graphrag/SourceDetailCard.tsx` with:

```tsx
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { X, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { cn } from '../../utils/cn';
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

const NODE_TYPE_STYLES: Record<string, string> = {
  person: 'bg-blue-50 text-blue-700 border-blue-200',
  concept: 'bg-green-50 text-green-700 border-green-200',
  argument: 'bg-purple-50 text-purple-700 border-purple-200',
  work: 'bg-amber-50 text-amber-700 border-amber-200',
  default: 'bg-gray-50 text-gray-700 border-gray-200',
};

function getTypeStyle(type: string) {
  return NODE_TYPE_STYLES[type.toLowerCase()] ?? NODE_TYPE_STYLES.default;
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
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden flex flex-col h-full"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <span className="flex items-center justify-center w-6 h-6 rounded-md bg-gray-100 text-xs font-bold text-gray-600">
            {source.id}
          </span>
          <span
            className={cn(
              'inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border',
              getTypeStyle(source.nodeType),
            )}
          >
            {source.nodeType || 'Source'}
          </span>
          <span className="text-sm font-medium text-gray-800 truncate">{source.nodeLabel}</span>
        </div>
        <button
          onClick={onClose}
          className="ml-2 shrink-0 p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close source detail"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 px-4 py-3 space-y-3 text-sm overflow-y-auto">
        {citationText?.original && (
          <div className="space-y-1">
            <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">
              {citationText.originalLanguage === 'greek'
                ? 'Greek'
                : citationText.originalLanguage === 'latin'
                  ? 'Latin'
                  : 'Original'}
            </div>
            <p className="font-serif italic text-gray-700 leading-relaxed text-[13px]">
              {citationText.original}
            </p>
          </div>
        )}
        {citationText?.translation && (
          <div className="space-y-1">
            <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">
              Translation
            </div>
            <p className="text-gray-600 leading-relaxed text-[13px]">{citationText.translation}</p>
          </div>
        )}
        {!citationText?.original && !citationText?.translation && (
          <p className="text-gray-400 italic text-xs">No passage text available for this source.</p>
        )}
        {(source.metadata?.period || source.metadata?.school) && (
          <div className="flex items-center gap-3 pt-1">
            {source.metadata?.period && (
              <span className="text-[10px] text-gray-400 font-medium">
                {source.metadata.period}
              </span>
            )}
            {source.metadata?.school && (
              <span className="text-[10px] text-gray-400 italic">
                {source.metadata.school as string}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-100 bg-gray-50/50 shrink-0">
        <div className="flex items-center gap-1.5">
          <button
            onClick={onPrev}
            disabled={citationIndex <= 0}
            className="p-1.5 rounded-lg hover:bg-gray-200 disabled:opacity-25 transition-colors text-gray-500"
            aria-label="Previous source"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] font-medium text-gray-400 tabular-nums min-w-[40px] text-center">
            {citationIndex + 1} / {totalCitations}
          </span>
          <button
            onClick={onNext}
            disabled={citationIndex >= totalCitations - 1}
            className="p-1.5 rounded-lg hover:bg-gray-200 disabled:opacity-25 transition-colors text-gray-500"
            aria-label="Next source"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
        {source.nodeId && !source.nodeId.startsWith('source_') && (
          <button
            onClick={() => navigate(`/node/${source.nodeId}`)}
            className="flex items-center gap-1 text-[10px] font-medium text-blue-600 hover:text-blue-700 transition-colors"
          >
            View in Visualizer
            <ExternalLink className="w-3 h-3" />
          </button>
        )}
      </div>
    </motion.div>
  );
}
```

**Step 2: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/components/graphrag/SourceDetailCard.tsx
git commit -m "feat(graphrag): restyle SourceDetailCard with modern SaaS look"
```

---

## Task 7: Extract components from GraphRAGPage monolith

**Files:**
- Create: `frontend/src/pages/GraphRAGPage/WelcomeHero.tsx`
- Create: `frontend/src/pages/GraphRAGPage/MessageBubble.tsx`
- Create: `frontend/src/pages/GraphRAGPage/ChatInput.tsx`
- Create: `frontend/src/pages/GraphRAGPage/ChatPanel.tsx`
- Create: `frontend/src/pages/GraphRAGPage/MobileGraphSheet.tsx`
- Modify: `frontend/src/pages/GraphRAGPage/index.tsx`

This is the largest task. Extract each inline component into its own file, then slim down the orchestrator.

**Step 1: Create WelcomeHero.tsx**

Create `frontend/src/pages/GraphRAGPage/WelcomeHero.tsx`:

```tsx
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ShineBorder } from '../../components/ui/shine-border';
import { Typewriter } from '../../components/ui/typewriter';
import AdvancedOptions from '../../components/graphrag/AdvancedOptions';

interface WelcomeHeroProps {
  query: string;
  setQuery: (q: string) => void;
  loading: boolean;
  streaming: boolean;
  error: string | null;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onDemo: () => void;
  advancedProps: {
    academicMode: boolean;
    setAcademicMode: (v: boolean) => void;
    useThinking: boolean;
    setUseThinking: (v: boolean) => void;
    ancientOnly: boolean;
    setAncientOnly: (v: boolean) => void;
    agenticMode: boolean;
    setAgenticMode: (v: boolean) => void;
    semanticK: number;
    setSemanticK: (v: number) => void;
    graphDepth: number;
    setGraphDepth: (v: number) => void;
    maxContext: number;
    setMaxContext: (v: number) => void;
  };
}

export default function WelcomeHero({
  query,
  setQuery,
  loading,
  streaming,
  error,
  inputRef,
  onSubmit,
  onDemo,
  advancedProps,
}: WelcomeHeroProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center min-h-[85vh] px-4 py-12">
      <div className="w-full max-w-2xl">
        <motion.div
          className="text-center mb-10"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-5xl md:text-6xl font-semibold text-gray-900 mb-3 drop-shadow-sm">
            <Typewriter
              text={['HiRAG', 'Knowledge Graph', 'Ancient Philosophy', 'Scholarly Q&A']}
              speed={100}
              waitTime={3500}
              deleteSpeed={60}
              className="text-gray-900"
              cursorChar="_"
            />
          </h1>
          <p className="text-base text-gray-600 max-w-lg mx-auto">{t('graphrag.description')}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="space-y-4"
        >
          <form onSubmit={onSubmit}>
            <ShineBorder
              className="!p-0 bg-white/95 backdrop-blur-sm"
              borderRadius={9999}
              color={['#3B82F6', '#6366F1', '#06B6D4']}
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

          <AdvancedOptions {...advancedProps} />

          <div className="flex justify-center">
            <button
              type="button"
              onClick={onDemo}
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
  );
}
```

**Step 2: Create MessageBubble.tsx**

Create `frontend/src/pages/GraphRAGPage/MessageBubble.tsx`:

```tsx
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Zap } from 'lucide-react';
import { CitationRenderer } from '../../components/CitationRenderer';
import type { GraphRAGChatMessage } from '../../types';

interface MessageBubbleProps {
  message: GraphRAGChatMessage;
  onNodeClick: (nodeId: string) => void;
  onCitationClick: (citationIndex: number) => void;
}

export default function MessageBubble({ message, onNodeClick, onCitationClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.25 }}
      className={isUser ? 'ml-auto max-w-2xl' : 'max-w-full'}
    >
      <div
        className={`rounded-2xl ${
          isUser
            ? 'bg-gradient-to-br from-gray-900 to-gray-800 shadow-md'
            : 'bg-white border border-gray-200 shadow-sm'
        }`}
      >
        <div className={`p-5 ${isUser ? 'text-white' : 'text-gray-900'}`}>
          {isUser ? (
            <p className="text-[15px] leading-relaxed">{message.content}</p>
          ) : (
            <div className="space-y-3">
              {message.graphrag_response?.service && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-blue-50 text-blue-600 border border-blue-100">
                  <Zap className="w-3 h-3" />
                  {message.graphrag_response.service}
                </span>
              )}

              {message.graphrag_response?.sources ? (
                <div className="prose prose-sm max-w-none prose-gray">
                  <CitationRenderer
                    content={message.content}
                    sources={message.graphrag_response.sources}
                    onNodeClick={(nodeId) => {
                      const idx = message.graphrag_response!.sources!.findIndex(
                        (s) => s.nodeId === nodeId,
                      );
                      onNodeClick(nodeId);
                      if (idx !== -1) onCitationClick(idx);
                    }}
                  />
                </div>
              ) : (
                <div className="prose prose-sm max-w-none prose-gray">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}
            </div>
          )}

          <div className={`text-[10px] mt-3 ${isUser ? 'text-white/50' : 'text-gray-400'}`}>
            {typeof message.timestamp === 'string'
              ? new Date(message.timestamp).toLocaleTimeString()
              : message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
```

**Step 3: Create ChatInput.tsx**

Create `frontend/src/pages/GraphRAGPage/ChatInput.tsx`:

```tsx
import { useTranslation } from 'react-i18next';
import { Square } from 'lucide-react';
import { ShineBorder } from '../../components/ui/shine-border';

interface ChatInputProps {
  query: string;
  setQuery: (q: string) => void;
  loading: boolean;
  streaming: boolean;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onStop: () => void;
}

export default function ChatInput({
  query,
  setQuery,
  loading,
  streaming,
  inputRef,
  onSubmit,
  onStop,
}: ChatInputProps) {
  const { t } = useTranslation();

  return (
    <div className="shrink-0 px-4 py-3 border-t border-gray-100 bg-white/80 backdrop-blur-sm">
      <ShineBorder
        className="!p-0 bg-white/95 backdrop-blur-sm shadow-sm"
        borderRadius={9999}
        color={['#3B82F6', '#6366F1', '#06B6D4']}
      >
        <form onSubmit={onSubmit} className="p-2">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('graphrag.placeholder')}
              disabled={loading || streaming}
              className="flex-1 px-6 py-3 text-[15px] bg-transparent focus:outline-none focus:ring-0 border-0"
            />
            {streaming ? (
              <button
                type="button"
                onClick={onStop}
                className="flex items-center gap-1.5 px-5 py-3 bg-red-600 text-white rounded-full hover:bg-red-700 font-medium transition-all text-sm"
              >
                <Square className="w-3 h-3 fill-current" />
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="px-6 py-3 bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-full hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium text-sm"
              >
                {loading ? 'Thinking...' : 'Ask'}
              </button>
            )}
          </div>
        </form>
      </ShineBorder>
    </div>
  );
}
```

**Step 4: Create ChatPanel.tsx**

Create `frontend/src/pages/GraphRAGPage/ChatPanel.tsx`:

```tsx
import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import { TerminalLoader } from '../../components/ui/terminal-loader';
import type { GraphRAGChatMessage } from '../../types';

interface ChatPanelProps {
  messages: GraphRAGChatMessage[];
  query: string;
  setQuery: (q: string) => void;
  loading: boolean;
  streaming: boolean;
  error: string | null;
  setError: (e: string | null) => void;
  agenticMode: boolean;
  inputRef: React.RefObject<HTMLInputElement | null>;
  onSubmit: (e: React.FormEvent) => void;
  onStop: () => void;
  onNodeClick: (nodeId: string) => void;
  onCitationClick: (citationIndex: number) => void;
}

export default function ChatPanel({
  messages,
  query,
  setQuery,
  loading,
  streaming,
  error,
  setError,
  agenticMode,
  inputRef,
  onSubmit,
  onStop,
  onNodeClick,
  onCitationClick,
}: ChatPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prevMessagesLengthRef = useRef(0);

  useEffect(() => {
    if (messages.length > prevMessagesLengthRef.current) {
      prevMessagesLengthRef.current = messages.length;
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div className="flex flex-col w-full lg:w-[65%] h-full overflow-hidden border-r border-gray-200">
      {/* Fixed header */}
      <div className="shrink-0 flex items-center justify-between px-6 py-3 border-b border-gray-100 bg-white/80 backdrop-blur-sm">
        <h1 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">HiRAG Q&A</h1>
      </div>

      {/* Scrollable messages */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
        <AnimatePresence>
          {messages.map((message, index) => (
            <MessageBubble
              key={index}
              message={message}
              onNodeClick={onNodeClick}
              onCitationClick={onCitationClick}
            />
          ))}
        </AnimatePresence>

        {streaming && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex justify-center items-center min-h-[40vh]"
          >
            <TerminalLoader size="large" title={agenticMode ? 'Pydantic-AI Engine' : undefined} />
          </motion.div>
        )}

        {error && !loading && !streaming && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="px-5 py-4 bg-red-50 border border-red-200 text-red-800 rounded-xl text-sm text-center"
          >
            <div className="font-medium mb-1">Query failed</div>
            {error}
            <button
              onClick={() => setError(null)}
              className="mt-2 text-red-600 hover:text-red-800 underline text-xs block mx-auto"
            >
              Dismiss
            </button>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Sticky input */}
      <ChatInput
        query={query}
        setQuery={setQuery}
        loading={loading}
        streaming={streaming}
        inputRef={inputRef}
        onSubmit={onSubmit}
        onStop={onStop}
      />
    </div>
  );
}
```

**Step 5: Create MobileGraphSheet.tsx**

Create `frontend/src/pages/GraphRAGPage/MobileGraphSheet.tsx`:

```tsx
import { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';
import { BottomSheet } from '../../components/ui/BottomSheet';
import RightPanel from '../../components/graphrag/RightPanel';
import type { GraphRAGResponse } from '../../types';

type RightPanelState = 'idle' | 'loading' | 'graph' | 'source-detail';

interface MobileGraphSheetProps {
  rightPanelState: RightPanelState;
  response: GraphRAGResponse | null;
  activeSourceIndex: number | null;
  onNodeClick: (nodeId: string) => void;
  onCloseDetail: () => void;
  onPrevSource: () => void;
  onNextSource: () => void;
  onHighlightRef?: (fn: (citationIndex: number) => void) => void;
}

export default function MobileGraphSheet({
  rightPanelState,
  response,
  activeSourceIndex,
  onNodeClick,
  onCloseDetail,
  onPrevSource,
  onNextSource,
  onHighlightRef,
}: MobileGraphSheetProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (rightPanelState === 'idle') return null;

  return (
    <>
      <motion.button
        className="fixed bottom-24 right-4 z-50 flex lg:hidden items-center justify-center w-12 h-12 rounded-xl bg-gray-900 text-white shadow-lg"
        onClick={() => setIsOpen(true)}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        aria-label="Open knowledge graph"
      >
        <BarChart3 className="w-5 h-5" />
      </motion.button>

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

**Step 6: Rewrite GraphRAGPage/index.tsx orchestrator**

Replace the entire contents of `frontend/src/pages/GraphRAGPage/index.tsx` with the slimmed-down orchestrator. It keeps all the state management and SSE logic but delegates rendering to the extracted components.

The file should contain:
- All imports (from the extracted components)
- All state declarations (unchanged)
- All SSE/streaming logic (unchanged from original)
- `handleSubmit`, `processQuery`, `handleStreamingQuery`, `handleAgenticQuery`, `stopStreaming`, `handleNodeClick`, `loadDemoMode` (unchanged logic)
- The JSX return should use `<WelcomeHero>`, `<ChatPanel>`, `<RightPanel>`, `<MobileGraphSheet>` instead of inline markup

Key changes to the JSX `return`:
- Replace the welcome section (lines 504-602) with `<WelcomeHero ... />`
- Replace the left panel div (lines 619-709) with `<ChatPanel ... />`
- Keep the right panel structure but it now uses the updated `RightPanel` which internally uses `CosmographView`
- Replace inline `MobileGraphButton` (lines 736-745) with `<MobileGraphSheet ... />`
- Remove the inline `MessageBubble` function definition (lines 771-832)
- Remove the inline `MobileGraphButton` function definition (lines 837-897)

The orchestrator file should be ~350-400 lines: all state + SSE logic + compact JSX return.

**Step 7: Delete KnowledgeGraphMini.tsx**

Delete `frontend/src/components/graphrag/KnowledgeGraphMini.tsx` - it's fully replaced by CosmographView.

Run: `git rm frontend/src/components/graphrag/KnowledgeGraphMini.tsx`

**Step 8: Verify build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors

**Step 9: Verify the app runs**

Run: `cd frontend && npm run dev`
Open `http://localhost:5173` and navigate to the GraphRAG page.
Verify:
- Welcome hero renders correctly
- "Try Demo" loads demo data
- Two-column layout appears
- Cosmograph renders the knowledge graph
- Messages display correctly
- Right panel shows idle/loading/graph/source-detail states
- AdvancedOptions toggles and selects work
- Mobile floating button appears on narrow viewport

**Step 10: Commit**

```bash
git add -A frontend/src/pages/GraphRAGPage/ frontend/src/components/graphrag/
git commit -m "feat(graphrag): extract components from monolith, integrate Cosmograph, polish UI

- Extract WelcomeHero, MessageBubble, ChatInput, ChatPanel, MobileGraphSheet
- Replace KnowledgeGraphMini canvas with CosmographView (WebGL)
- Add graph controls (zoom, fit, pause) and color legend
- Restyle messages with modern SaaS look
- Slim GraphRAGPage orchestrator from 998 to ~380 lines"
```

---

## Task 8: Visual polish pass

**Files:**
- Modify: `frontend/src/pages/GraphRAGPage/index.tsx` (minor spacing/styling tweaks)

Final pass for consistency: verify panel divider, spacing, and background colors match the design.

**Step 1: Review and adjust**

In the orchestrator `index.tsx`, ensure:
- Two-column container uses `bg-white` (not `bg-academic-paper`)
- Right panel column uses `bg-gray-50` (not `bg-gray-50/80`)
- Right panel header matches left panel header style (`text-sm font-semibold text-gray-500 uppercase tracking-wider`)
- Panel divider border is `border-gray-200` (not `border-gray-100`)

**Step 2: Verify build and visual check**

Run: `cd frontend && npm run build`
Run: `cd frontend && npm run dev`
Visual verification in browser at http://localhost:5173

**Step 3: Commit**

```bash
git add -A frontend/src/
git commit -m "style(graphrag): final visual polish pass for consistency"
```

---

## Task 9: Run tests and verify nothing is broken

**Files:** None modified

**Step 1: Run frontend tests**

Run: `cd frontend && npm test`
Expected: All tests pass (or pass with `--passWithNoTests` if no GraphRAG-specific tests exist)

**Step 2: Run build**

Run: `cd frontend && npm run build`
Expected: Clean build with no TypeScript or Vite errors

**Step 3: Run linter**

Run: `cd frontend && npm run lint`
Expected: No new lint errors

**Step 4: Commit any fixes if needed**

If lint or type errors were found, fix and commit:
```bash
git add -A frontend/src/
git commit -m "fix(graphrag): resolve lint/type issues from UI polish"
```
