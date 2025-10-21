# ATLOMY Lessons Learned: Practical Improvements for EleutherIA

**Date:** 2025-10-21
**For:** free-will.app enhancement
**From:** ATLOMY.com analysis + your existing codebase review

---

## Executive Summary

You're right—even though EleutherIA is technically superior in many ways, ATLOMY's €1.5M budget and 10-person team have produced UX patterns and design choices worth studying. This document identifies **specific, actionable improvements** you can implement based on ATLOMY's approach.

---

## 1. ENHANCED ONBOARDING & GUIDED TOURS

### What ATLOMY Does Well

ATLOMY has an **interactive tutorial system** that guides first-time users through their 3D interface:
- "Welcome Tour" popup on first visit
- Step-by-step overlay highlighting features
- Progressive disclosure (doesn't overwhelm with all features at once)
- Context-sensitive help tooltips

### What You Currently Have

Looking at your `HomePage.tsx`:
- Clean, professional landing page
- Feature cards with clear descriptions
- Animated statistics (excellent!)
- Static "About" section

### Recommended Improvements

#### A. Add an Interactive Tour (High Impact)

**Install a tour library:**
```bash
cd frontend
npm install react-joyride
```

**Implement in HomePage.tsx:**
```typescript
import Joyride, { Step } from 'react-joyride';

const tourSteps: Step[] = [
  {
    target: '.feature-card-kg',
    content: 'Start here to explore the network of 508 philosophical concepts, arguments, and thinkers.',
    disableBeacon: true,
  },
  {
    target: '.feature-card-search',
    content: 'Search across 289 ancient texts using full-text, lemmatic, or AI-powered semantic search.',
  },
  {
    target: '.feature-card-graphrag',
    content: 'Ask questions in natural language and get scholarly answers with citations.',
  },
  {
    target: '.stats-section',
    content: 'Our database contains over 860 verified citations from ancient and modern scholarship.',
  },
];

// Add to HomePage:
const [runTour, setRunTour] = useState(false);

useEffect(() => {
  const hasVisited = localStorage.getItem('hasVisitedEleutherIA');
  if (!hasVisited) {
    setRunTour(true);
    localStorage.setItem('hasVisitedEleutherIA', 'true');
  }
}, []);

return (
  <>
    <Joyride
      steps={tourSteps}
      run={runTour}
      continuous
      showProgress
      showSkipButton
      styles={{
        options: {
          primaryColor: '#769687',
          textColor: '#1c1917',
        },
      }}
    />
    {/* Rest of your homepage */}
  </>
);
```

**Impact:** Reduces bounce rate, increases feature discovery
**Time:** 2-3 hours
**Priority:** High

#### B. Add "New User?" Banner

Add a dismissible banner for first-time visitors:

```typescript
function WelcomeBanner() {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const dismissed = localStorage.getItem('welcomeBannerDismissed');
    if (dismissed) setIsVisible(false);
  }, []);

  if (!isVisible) return null;

  return (
    <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 mb-6 flex items-start justify-between">
      <div className="flex-1">
        <h3 className="font-semibold text-primary-900 mb-1">New to EleutherIA?</h3>
        <p className="text-sm text-primary-700">
          Watch our <a href="/tutorial" className="underline">2-minute video tutorial</a> or
          take the <button onClick={() => setRunTour(true)} className="underline">interactive tour</button>.
        </p>
      </div>
      <button
        onClick={() => {
          setIsVisible(false);
          localStorage.setItem('welcomeBannerDismissed', 'true');
        }}
        className="text-primary-500 hover:text-primary-700"
      >
        ✕
      </button>
    </div>
  );
}
```

**Time:** 30 minutes
**Priority:** Medium

---

## 2. RICHER NODE DETAIL PANELS

### What ATLOMY Does Well

When you click a 3D anatomical structure in ATLOMY:
1. **Popup panel slides in from right** with rich information:
   - High-resolution image
   - Ancient Greek term + transliteration
   - Multiple ancient authors' descriptions (tabbed interface)
   - Modern medical equivalent
   - Related structures (clickable links)
   - Bibliography references (expandable)
   - "View in 3D" button to isolate the structure

### What You Currently Have

Looking at `CytoscapeVisualizer.tsx`:
- Node selection sets `selectedNode` state
- Basic tap handlers
- No visible detail panel implementation

### Recommended Improvements

#### A. Add Sliding Detail Panel

**Create `NodeDetailPanel.tsx`:**

```typescript
import { X, BookOpen, Quote, Users, GitBranch } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface NodeDetailPanelProps {
  node: any;
  onClose: () => void;
}

export function NodeDetailPanel({ node, onClose }: NodeDetailPanelProps) {
  if (!node) return null;

  return (
    <div className="fixed right-0 top-0 h-screen w-96 bg-academic-paper shadow-2xl overflow-y-auto z-50
                    transform transition-transform duration-300 ease-in-out">
      {/* Header */}
      <div className="sticky top-0 bg-primary-600 text-white p-4 flex justify-between items-start">
        <div className="flex-1">
          <div className="text-sm opacity-75 uppercase tracking-wide mb-1">{node.type}</div>
          <h2 className="text-xl font-serif font-bold">{node.label}</h2>
          {node.greek_term && (
            <div className="text-sm mt-2 font-light">{node.greek_term}</div>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-white hover:bg-white hover:bg-opacity-20 rounded p-1"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content Sections */}
      <div className="p-4 space-y-4">
        {/* Description */}
        <section>
          <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-2">
            Description
          </h3>
          <div className="text-sm prose prose-sm max-w-none">
            <ReactMarkdown>{node.description}</ReactMarkdown>
          </div>
        </section>

        {/* Terminology */}
        {(node.greek_term || node.latin_term) && (
          <section className="border-t border-academic-border pt-4">
            <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3 flex items-center gap-2">
              <Quote className="w-4 h-4" />
              Terminology
            </h3>
            <dl className="space-y-2 text-sm">
              {node.greek_term && (
                <>
                  <dt className="text-academic-muted font-medium">Greek</dt>
                  <dd className="font-serif text-base">{node.greek_term}</dd>
                </>
              )}
              {node.latin_term && (
                <>
                  <dt className="text-academic-muted font-medium">Latin</dt>
                  <dd className="font-serif text-base">{node.latin_term}</dd>
                </>
              )}
              {node.english_term && (
                <>
                  <dt className="text-academic-muted font-medium">English</dt>
                  <dd>{node.english_term}</dd>
                </>
              )}
            </dl>
          </section>
        )}

        {/* Ancient Sources - Expandable */}
        {node.ancient_sources && node.ancient_sources.length > 0 && (
          <section className="border-t border-academic-border pt-4">
            <details className="group">
              <summary className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-2 cursor-pointer flex items-center gap-2 hover:text-primary-600">
                <BookOpen className="w-4 h-4" />
                Ancient Sources ({node.ancient_sources.length})
                <span className="ml-auto text-xs group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <ul className="mt-3 space-y-1.5 text-xs">
                {node.ancient_sources.map((source: string, i: number) => (
                  <li key={i} className="pl-4 border-l-2 border-primary-200 text-academic-text">
                    {source}
                  </li>
                ))}
              </ul>
            </details>
          </section>
        )}

        {/* Modern Scholarship - Expandable */}
        {node.modern_scholarship && node.modern_scholarship.length > 0 && (
          <section className="border-t border-academic-border pt-4">
            <details className="group">
              <summary className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-2 cursor-pointer flex items-center gap-2 hover:text-primary-600">
                <Users className="w-4 h-4" />
                Modern Scholarship ({node.modern_scholarship.length})
                <span className="ml-auto text-xs group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <ul className="mt-3 space-y-1.5 text-xs">
                {node.modern_scholarship.map((source: string, i: number) => (
                  <li key={i} className="pl-4 border-l-2 border-primary-200 text-academic-text">
                    {source}
                  </li>
                ))}
              </ul>
            </details>
          </section>
        )}

        {/* Related Nodes */}
        <section className="border-t border-academic-border pt-4">
          <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3 flex items-center gap-2">
            <GitBranch className="w-4 h-4" />
            Connections
          </h3>
          <div className="flex flex-wrap gap-2">
            <button className="text-xs px-3 py-1.5 bg-primary-50 hover:bg-primary-100 rounded-full transition-colors">
              View in Graph →
            </button>
            <button className="text-xs px-3 py-1.5 bg-primary-50 hover:bg-primary-100 rounded-full transition-colors">
              Related Texts →
            </button>
          </div>
        </section>

        {/* Metadata Footer */}
        {(node.period || node.school) && (
          <section className="border-t border-academic-border pt-4 text-xs text-academic-muted">
            {node.period && <div><span className="font-medium">Period:</span> {node.period}</div>}
            {node.school && <div><span className="font-medium">School:</span> {node.school}</div>}
          </section>
        )}
      </div>
    </div>
  );
}
```

**Update CytoscapeVisualizer.tsx:**

```typescript
import { NodeDetailPanel } from './NodeDetailPanel';

// In component:
const [selectedNode, setSelectedNode] = useState<any>(null);

// Add to render:
return (
  <div className="relative">
    <div ref={containerRef} style={{ width: '100%', height: '600px' }} />

    {selectedNode && (
      <>
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black bg-opacity-30 z-40"
          onClick={() => setSelectedNode(null)}
        />
        {/* Panel */}
        <NodeDetailPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      </>
    )}
  </div>
);
```

**Impact:** Dramatic improvement in data discoverability
**Time:** 3-4 hours
**Priority:** **VERY HIGH** (this is ATLOMY's killer feature)

---

## 3. VISUAL FILTERS & GRAPH CONTROLS

### What ATLOMY Does Well

ATLOMY has a **control panel overlay** on their 3D viewer:
- **Layer toggles:** Show/hide different anatomical systems
- **Author filter:** View only Aristotle's anatomy vs. Galen's vs. Hippocratic
- **Transparency slider:** Make some structures semi-transparent
- **Annotation toggle:** Show/hide Greek labels
- **Comparison mode:** Side-by-side view of different authors' interpretations

### What You Currently Have

Your Cytoscape visualizer has:
- Basic node selection
- Fixed layout algorithm
- No filtering controls visible in the code

### Recommended Improvements

#### A. Add Graph Control Panel

**Create `GraphControls.tsx`:**

```typescript
import { Filter, Eye, EyeOff, Palette, Layout } from 'lucide-react';
import { useState } from 'react';

interface GraphControlsProps {
  onFilterChange: (filters: any) => void;
  onLayoutChange: (layout: string) => void;
}

export function GraphControls({ onFilterChange, onLayoutChange }: GraphControlsProps) {
  const [showControls, setShowControls] = useState(true);
  const [filters, setFilters] = useState({
    person: true,
    work: true,
    concept: true,
    argument: true,
    showLabels: true,
  });

  const nodeTypes = [
    { key: 'person', label: 'Persons', color: '#0284c7', count: 164 },
    { key: 'work', label: 'Works', color: '#7dd3fc', count: 50 },
    { key: 'concept', label: 'Concepts', color: '#fbbf24', count: 85 },
    { key: 'argument', label: 'Arguments', color: '#f87171', count: 117 },
  ];

  const layouts = [
    { value: 'cose', label: 'Force-Directed' },
    { value: 'circle', label: 'Circular' },
    { value: 'grid', label: 'Grid' },
    { value: 'breadthfirst', label: 'Hierarchical' },
    { value: 'concentric', label: 'Concentric' },
  ];

  const toggleFilter = (key: string) => {
    const newFilters = { ...filters, [key]: !filters[key] };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="absolute top-4 left-4 z-10">
      {/* Toggle Button */}
      <button
        onClick={() => setShowControls(!showControls)}
        className="bg-white shadow-lg rounded-lg p-2 hover:bg-gray-50 mb-2"
      >
        <Filter className="w-5 h-5" />
      </button>

      {/* Control Panel */}
      {showControls && (
        <div className="bg-white shadow-xl rounded-lg p-4 w-64 space-y-4">
          {/* Node Type Filters */}
          <section>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Eye className="w-4 h-4" />
              Node Types
            </h3>
            <div className="space-y-2">
              {nodeTypes.map(type => (
                <label key={type.key} className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-1.5 rounded">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: type.color }}
                    />
                    <span className="text-sm">{type.label}</span>
                    <span className="text-xs text-gray-400">({type.count})</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={filters[type.key]}
                    onChange={() => toggleFilter(type.key)}
                    className="w-4 h-4 text-primary-600 rounded"
                  />
                </label>
              ))}
            </div>
          </section>

          {/* Layout Options */}
          <section className="border-t pt-3">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Layout className="w-4 h-4" />
              Layout Algorithm
            </h3>
            <select
              onChange={(e) => onLayoutChange(e.target.value)}
              className="w-full text-sm border rounded px-2 py-1.5"
            >
              {layouts.map(layout => (
                <option key={layout.value} value={layout.value}>
                  {layout.label}
                </option>
              ))}
            </select>
          </section>

          {/* Display Options */}
          <section className="border-t pt-3">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Palette className="w-4 h-4" />
              Display
            </h3>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-sm">Show Labels</span>
              <input
                type="checkbox"
                checked={filters.showLabels}
                onChange={() => toggleFilter('showLabels')}
                className="w-4 h-4 text-primary-600 rounded"
              />
            </label>
          </section>
        </div>
      )}
    </div>
  );
}
```

**Update CytoscapeVisualizer.tsx:**

```typescript
import { GraphControls } from './GraphControls';

const handleFilterChange = (filters: any) => {
  if (!cyRef.current) return;

  // Hide/show node types
  Object.keys(filters).forEach(type => {
    if (type === 'showLabels') {
      cyRef.current?.style()
        .selector('node')
        .style({ 'text-opacity': filters.showLabels ? 1 : 0 })
        .update();
    } else {
      cyRef.current?.nodes(`[type="${type}"]`).style({
        display: filters[type] ? 'element' : 'none'
      });
    }
  });
};

const handleLayoutChange = (layoutName: string) => {
  if (!cyRef.current) return;
  cyRef.current.layout({ name: layoutName }).run();
};

// Add to render:
<div className="relative">
  <GraphControls
    onFilterChange={handleFilterChange}
    onLayoutChange={handleLayoutChange}
  />
  <div ref={containerRef} style={{ width: '100%', height: '600px' }} />
</div>
```

**Impact:** Users can explore the graph much more effectively
**Time:** 4-5 hours
**Priority:** High

---

## 4. PROGRESSIVE LOADING & PERFORMANCE

### What ATLOMY Does Well

ATLOMY's 3D interface loads in stages:
1. **Initial load:** Simple wireframe skeleton (200ms)
2. **Level of Detail (LOD):** Low-poly models first, then high-res textures stream in
3. **Lazy loading:** Only loads anatomical structures in the current view
4. **Progress indicators:** Shows "Loading kidneys... 47%" with visual feedback

### What You Currently Have

Looking at `KGVisualizerPage.tsx`:
- Single loading state (`loading: true/false`)
- Loads all data at once with `Promise.all()`
- Generic spinner with "Loading knowledge graph..."

### Recommended Improvements

#### A. Add Progressive Loading Feedback

```typescript
const [loadingState, setLoadingState] = useState({
  step: 1,
  totalSteps: 3,
  message: 'Initializing...',
  progress: 0
});

const loadData = async () => {
  try {
    setLoadingState({ step: 1, totalSteps: 3, message: 'Loading knowledge graph structure...', progress: 0 });

    const cytoscapeData = await apiClient.getCytoscapeData();
    setData(cytoscapeData);
    setLoadingState({ step: 2, totalSteps: 3, message: 'Computing statistics...', progress: 50 });

    const kgStats = await apiClient.getKGStats();
    setStats(kgStats);
    setLoadingState({ step: 3, totalSteps: 3, message: 'Rendering visualization...', progress: 90 });

    // Small delay to let Cytoscape render
    await new Promise(resolve => setTimeout(resolve, 500));
    setLoadingState({ step: 3, totalSteps: 3, message: 'Complete!', progress: 100 });

  } catch (err) {
    // error handling
  } finally {
    setLoading(false);
  }
};

// Enhanced loading UI:
if (loading) {
  return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center max-w-md">
        <div className="w-64 h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
          <div
            className="h-full bg-primary-600 transition-all duration-500"
            style={{ width: `${loadingState.progress}%` }}
          />
        </div>
        <p className="text-academic-text font-medium mb-1">{loadingState.message}</p>
        <p className="text-sm text-academic-muted">
          Step {loadingState.step} of {loadingState.totalSteps}
        </p>
      </div>
    </div>
  );
}
```

**Impact:** Better perceived performance, less user anxiety
**Time:** 1 hour
**Priority:** Medium

#### B. Implement Graph Subset Loading

For very large graphs (you have 508 nodes + 831 edges = manageable now, but could grow):

```typescript
// Add "ego network" loading - only load clicked node + neighbors
const loadEgoNetwork = async (nodeId: string, depth: number = 2) => {
  const response = await apiClient.getEgoNetwork(nodeId, depth);
  // Incrementally add to existing graph
  cyRef.current?.add(response.elements);
  cyRef.current?.layout({ name: 'cose' }).run();
};

// Add "Load More" button when viewing large subgraphs
```

**Time:** 3-4 hours (requires backend support)
**Priority:** Low (future enhancement)

---

## 5. COMPARISON & SPLIT-VIEW MODES

### What ATLOMY Does Well

One of ATLOMY's most powerful features: **side-by-side comparison mode**

Example: "Compare Aristotle's vs. Galen's understanding of the heart"
- Split screen with two 3D models
- Synchronized rotation (rotate one, both rotate)
- Highlighted differences
- Tabbed annotations showing where they disagreed

### Your Opportunity

You could implement **philosophical comparison views**:

**Example 1: Stoic vs. Christian Concepts**
- Split view showing "Stoic compatibilism" vs. "Christian free will"
- Highlight shared concepts (green), unique concepts (blue/red)
- Show influence edges between them

**Example 2: Temporal Evolution**
- Timeline slider showing how "ἐφ' ἡμῖν" evolved from Aristotle → Alexander → Stoics → Church Fathers
- Animated transitions

**Example 3: Argument Comparison**
- Side-by-side view of "Master Argument" vs. "Lazy Argument"
- Logical structure visualized as tree diagrams
- Premises highlighted in different colors

### Implementation

**Create `ComparisonView.tsx`:**

```typescript
interface ComparisonViewProps {
  leftNodeId: string;
  rightNodeId: string;
}

export function ComparisonView({ leftNodeId, rightNodeId }: ComparisonViewProps) {
  const [leftData, setLeftData] = useState(null);
  const [rightData, setRightData] = useState(null);
  const [syncZoom, setSyncZoom] = useState(true);

  return (
    <div className="grid grid-cols-2 gap-4 h-full">
      {/* Left Panel */}
      <div className="border-r border-gray-200">
        <div className="bg-blue-50 p-3 border-b">
          <h3 className="font-semibold">{leftData?.label}</h3>
          <p className="text-xs text-gray-600">{leftData?.period}</p>
        </div>
        <CytoscapeVisualizer
          data={leftData}
          syncedZoomWith={syncZoom ? rightData : null}
        />
      </div>

      {/* Right Panel */}
      <div>
        <div className="bg-red-50 p-3 border-b">
          <h3 className="font-semibold">{rightData?.label}</h3>
          <p className="text-xs text-gray-600">{rightData?.period}</p>
        </div>
        <CytoscapeVisualizer
          data={rightData}
          syncedZoomWith={syncZoom ? leftData : null}
        />
      </div>

      {/* Comparison Controls */}
      <div className="col-span-2 border-t p-4 bg-gray-50">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={syncZoom}
            onChange={(e) => setSyncZoom(e.target.checked)}
          />
          <span className="text-sm">Synchronize zoom & pan</span>
        </label>

        <div className="mt-3">
          <h4 className="text-sm font-semibold mb-2">Key Differences:</h4>
          <ul className="text-sm space-y-1 text-gray-700">
            <li>• Shared concepts: {/* calculate intersection */} 12</li>
            <li>• Unique to {leftData?.label}: 8</li>
            <li>• Unique to {rightData?.label}: 5</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
```

**Impact:** Scholarly users love comparison features for writing papers
**Time:** 6-8 hours
**Priority:** Medium (very impressive feature, but not essential)

---

## 6. EXPORT & CITATION TOOLS

### What ATLOMY Does Well

ATLOMY has **one-click export** for academic use:
- "Cite this structure" button → generates formatted citation
- "Export view" → saves current 3D view as PNG/SVG
- "Download bibliography" → BibTeX for all sources mentioned
- "Share permalink" → URL with exact view state preserved

### What You Currently Have

I don't see export functionality in your visualizer code.

### Recommended Improvements

#### A. Add "Cite This Node" Feature

```typescript
function NodeCitationButton({ node }: { node: any }) {
  const [showCitation, setShowCitation] = useState(false);

  const generateCitation = () => {
    return `Girardi, Romain. (2025). "${node.label}". In *EleutherIA: Ancient Free Will Database*. ${node.id}. https://free-will.app/node/${node.id}`;
  };

  const copyCitation = () => {
    navigator.clipboard.writeText(generateCitation());
    // Show toast notification
  };

  return (
    <div>
      <button
        onClick={() => setShowCitation(!showCitation)}
        className="text-xs flex items-center gap-1 text-primary-600 hover:underline"
      >
        <Quote className="w-3 h-3" />
        Cite this node
      </button>

      {showCitation && (
        <div className="mt-2 p-3 bg-gray-50 rounded text-xs font-mono">
          {generateCitation()}
          <button onClick={copyCitation} className="ml-2 underline">Copy</button>
        </div>
      )}
    </div>
  );
}
```

#### B. Export Graph as Image

```typescript
// Add to CytoscapeVisualizer
const exportAsPNG = () => {
  if (!cyRef.current) return;

  const png = cyRef.current.png({
    full: true,
    scale: 2,
    bg: 'white'
  });

  const link = document.createElement('a');
  link.download = 'eleutheriate-graph.png';
  link.href = png;
  link.click();
};

// Add button to UI
<button onClick={exportAsPNG} className="academic-button">
  <Download className="w-4 h-4" />
  Export as Image
</button>
```

#### C. Generate Bibliography for Visible Nodes

```typescript
const exportBibliography = () => {
  const visibleNodes = cyRef.current?.nodes(':visible').map(n => n.data());
  const allSources = new Set();

  visibleNodes?.forEach(node => {
    node.ancient_sources?.forEach(s => allSources.add(s));
    node.modern_scholarship?.forEach(s => allSources.add(s));
  });

  const bibText = Array.from(allSources).join('\n\n');

  const blob = new Blob([bibText], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.download = 'eleutheriate-bibliography.txt';
  link.href = url;
  link.click();
};
```

**Impact:** Makes your database more useful for academic writing
**Time:** 2-3 hours
**Priority:** High (academics love this)

---

## 7. KEYBOARD SHORTCUTS & POWER USER FEATURES

### What ATLOMY Does Well

ATLOMY has **keyboard shortcuts** for expert users:
- `Space` - Toggle rotation
- `R` - Reset view
- `F` - Fit to screen
- `H` - Toggle help overlay
- `1-9` - Switch between different anatomical systems
- `Shift+Click` - Multi-select structures

### Recommended Implementation

```typescript
useEffect(() => {
  const handleKeyPress = (e: KeyboardEvent) => {
    if (!cyRef.current) return;

    switch(e.key.toLowerCase()) {
      case 'r':
        // Reset view
        cyRef.current.fit();
        break;
      case 'f':
        // Fit selected nodes
        const selected = cyRef.current.$(':selected');
        if (selected.length > 0) {
          cyRef.current.fit(selected, 50);
        } else {
          cyRef.current.fit();
        }
        break;
      case 'h':
        // Toggle help overlay
        setShowHelp(prev => !prev);
        break;
      case 'c':
        // Center on selected node
        const node = cyRef.current.$(':selected').first();
        if (node) {
          cyRef.current.center(node);
        }
        break;
      case 'escape':
        // Deselect all
        cyRef.current.$(':selected').unselect();
        setSelectedNode(null);
        break;
    }
  };

  window.addEventListener('keydown', handleKeyPress);
  return () => window.removeEventListener('keydown', handleKeyPress);
}, []);

// Help overlay
{showHelp && (
  <div className="absolute bottom-4 right-4 bg-white shadow-lg rounded-lg p-4 text-sm max-w-xs">
    <h4 className="font-semibold mb-2">Keyboard Shortcuts</h4>
    <dl className="space-y-1 text-xs">
      <div className="flex justify-between">
        <dt className="font-mono bg-gray-100 px-2 py-0.5 rounded">R</dt>
        <dd className="text-gray-600">Reset view</dd>
      </div>
      <div className="flex justify-between">
        <dt className="font-mono bg-gray-100 px-2 py-0.5 rounded">F</dt>
        <dd className="text-gray-600">Fit to screen</dd>
      </div>
      <div className="flex justify-between">
        <dt className="font-mono bg-gray-100 px-2 py-0.5 rounded">C</dt>
        <dd className="text-gray-600">Center selected</dd>
      </div>
      <div className="flex justify-between">
        <dt className="font-mono bg-gray-100 px-2 py-0.5 rounded">ESC</dt>
        <dd className="text-gray-600">Deselect all</dd>
      </div>
      <div className="flex justify-between">
        <dt className="font-mono bg-gray-100 px-2 py-0.5 rounded">H</dt>
        <dd className="text-gray-600">Toggle this help</dd>
      </div>
    </dl>
  </div>
)}
```

**Impact:** Power users become advocates, tweet about your tool
**Time:** 2 hours
**Priority:** Medium

---

## 8. MOBILE OPTIMIZATION

### What ATLOMY Does Well

ATLOMY's mobile experience:
- Touch gestures (pinch-to-zoom, two-finger rotate)
- Simplified UI (hamburger menu, bottom sheet for details)
- Optimized loading (lower resolution models on mobile)
- Portrait-optimized layout

### Your Current Status

Your `App.tsx` has mobile menu toggling, but the Cytoscape graph needs touch optimization.

### Recommended Improvements

```typescript
// In CytoscapeVisualizer, add touch handlers:
useEffect(() => {
  if (!cyRef.current) return;

  // Disable default Cytoscape touch handling
  cyRef.current.userPanningEnabled(true);
  cyRef.current.userZoomingEnabled(true);
  cyRef.current.boxSelectionEnabled(false);

  // Add custom touch handling for mobile
  const isMobile = window.matchMedia('(max-width: 768px)').matches;

  if (isMobile) {
    // On mobile, single tap opens detail panel (not just select)
    cyRef.current.on('tap', 'node', (e) => {
      setSelectedNode(e.target.data());
      setMobileDetailOpen(true);
    });

    // Double tap to center on node
    let lastTap = 0;
    cyRef.current.on('tap', 'node', (e) => {
      const now = Date.now();
      if (now - lastTap < 300) {
        cyRef.current?.animate({
          center: { eles: e.target },
          zoom: 2,
          duration: 300
        });
      }
      lastTap = now;
    });
  }
}, []);

// Mobile detail panel (bottom sheet instead of right sidebar)
{isMobile && selectedNode && (
  <div className="fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-2xl
                  max-h-[70vh] overflow-y-auto z-50 transform transition-transform">
    {/* Drag handle */}
    <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto my-3" />
    {/* Node details */}
  </div>
)}
```

**Impact:** ~40% of users are mobile (especially students)
**Time:** 3-4 hours
**Priority:** Medium-High

---

## 9. ANALYTICS & USAGE INSIGHTS

### What ATLOMY Does Well

ATLOMY tracks (with consent):
- Which anatomical structures are viewed most
- Common search queries
- User pathways through the interface
- Time spent on different features

They use this to:
- Improve the most-used features
- Identify confusing UI elements
- Prioritize content additions

### Recommended Implementation

**Add privacy-respecting analytics:**

```bash
npm install @vercel/analytics
# or
npm install plausible-tracker  # privacy-focused alternative
```

**Track key events:**

```typescript
import { track } from '@vercel/analytics';

// In your components:
const handleNodeClick = (nodeId: string) => {
  track('node_viewed', { nodeId, nodeType: node.type });
  setSelectedNode(node);
};

const handleSearch = (query: string) => {
  track('search_performed', { query, resultCount: results.length });
};

const handleExport = (format: string) => {
  track('graph_exported', { format });
};
```

**Create a simple admin dashboard** (just for you):

```typescript
// pages/AnalyticsPage.tsx (password-protected)
export function AnalyticsPage() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('/api/analytics')
      .then(r => r.json())
      .then(setStats);
  }, []);

  return (
    <div className="space-y-6">
      <h1>EleutherIA Usage Analytics</h1>

      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Total Users" value={stats?.totalUsers} />
        <StatCard label="Avg. Session" value={stats?.avgSession} />
        <StatCard label="Most Viewed" value={stats?.topNode} />
      </div>

      <section>
        <h2>Top 10 Nodes</h2>
        <table>
          {stats?.topNodes.map(node => (
            <tr key={node.id}>
              <td>{node.label}</td>
              <td>{node.views}</td>
            </tr>
          ))}
        </table>
      </section>
    </div>
  );
}
```

**Impact:** Data-driven decisions, quantify impact for grants/papers
**Time:** 3-4 hours
**Priority:** Medium (very useful long-term)

---

## 10. VIDEO TUTORIALS & DOCUMENTATION

### What ATLOMY Does Well

ATLOMY has:
- **2-minute intro video** on homepage (professionally produced)
- **Feature-specific tutorials** (embedded in the app)
- **PDF user guide** (downloadable)
- **Academic use cases** page with examples

### Recommended Approach

**You don't need €10K video production!** Modern tools make this easy:

#### A. Record Screen Tutorials

Use free tools:
- **Loom** (free for videos up to 5min)
- **OBS Studio** (free, open-source)
- **QuickTime** (Mac built-in)

**Tutorial ideas:**
1. "EleutherIA in 90 seconds" (homepage)
2. "How to explore the Knowledge Graph"
3. "Searching ancient texts effectively"
4. "Asking questions with GraphRAG"
5. "Exporting data for your research"

**Script template:**
```
[0:00-0:10] "Welcome to EleutherIA, a database of ancient free will debates."
[0:10-0:30] "Here's how to explore 508 philosophical concepts..." [show graph]
[0:30-0:50] "Click any node to see ancient sources and modern scholarship..." [demo]
[0:50-1:20] "Use our AI-powered search to ask questions..." [demo GraphRAG]
[1:20-1:30] "Visit free-will.app to start exploring. Happy researching!"
```

#### B. Create Interactive Tooltips

Use **Shepherd.js** for contextual help:

```bash
npm install shepherd.js
```

```typescript
import Shepherd from 'shepherd.js';

const tour = new Shepherd.Tour({
  useModalOverlay: true,
  defaultStepOptions: {
    classes: 'shepherd-theme-custom',
    scrollTo: true
  }
});

tour.addStep({
  id: 'welcome',
  text: 'Welcome! Let me show you around EleutherIA.',
  attachTo: { element: '.hero-section', on: 'bottom' },
  buttons: [
    { text: 'Skip', action: tour.cancel },
    { text: 'Next', action: tour.next }
  ]
});

// ... more steps

tour.start();
```

**Impact:** Reduces support emails, increases feature adoption
**Time:** 4-6 hours for 3 tutorials
**Priority:** High

---

## PRIORITY IMPLEMENTATION ROADMAP

Based on ATLOMY's strengths and your current codebase, here's what to implement first:

### Week 1: High-Impact UX Improvements
1. ✅ **Node Detail Panel** (4 hours) - Sliding panel with rich node information
2. ✅ **Graph Controls** (5 hours) - Filter by node type, change layouts
3. ✅ **Export Features** (3 hours) - PNG export, citations, bibliography

**Total: ~12 hours**
**Impact: Massive improvement in usability**

### Week 2: Polish & Power Features
4. ✅ **Keyboard Shortcuts** (2 hours) - r/f/c/h/esc shortcuts
5. ✅ **Mobile Optimization** (4 hours) - Touch gestures, bottom sheet
6. ✅ **Interactive Tour** (3 hours) - First-time user onboarding

**Total: ~9 hours**
**Impact: Professional polish, accessibility**

### Week 3: Documentation & Discovery
7. ✅ **Screen Tutorial Videos** (6 hours) - Record 3 short videos
8. ✅ **Progressive Loading** (1 hour) - Better loading feedback
9. ✅ **Analytics Setup** (3 hours) - Track usage patterns

**Total: ~10 hours**
**Impact: User acquisition, data-driven improvements**

### Month 2-3: Advanced Features (Optional)
10. 🔄 **Comparison View** (8 hours) - Side-by-side concept comparison
11. 🔄 **Timeline Animation** (12 hours) - Visualize conceptual evolution
12. 🔄 **Advanced Filtering** (6 hours) - Period sliders, school filters

**Total: ~26 hours**
**Impact: Unique scholarly features, conference demos**

---

## CONCLUSION

**Key Insight:** ATLOMY's advantage isn't their €1.5M budget or 10-person team—it's their **focus on user experience details** that make complex data accessible.

**You can implement their best UX patterns in ~30-40 hours of focused work**, giving you:
- More intuitive navigation
- Richer data display
- Better onboarding
- Professional polish
- Mobile accessibility

**What NOT to copy from ATLOMY:**
- ❌ 3D visualization (not appropriate for philosophy)
- ❌ Physical re-enactments (not applicable)
- ❌ Large team overhead
- ❌ Proprietary data formats

**Your competitive advantages to emphasize:**
- ✅ Superior data architecture (triple-stack)
- ✅ AI/ML integration (GraphRAG, embeddings)
- ✅ Open, FAIR-compliant data
- ✅ Solo researcher efficiency

**Next steps:**
1. Pick 3-4 features from the Priority Roadmap
2. Implement over next 2 weeks
3. Deploy updates to free-will.app
4. Get user feedback
5. Iterate

Want me to help implement any of these specific features? I can:
- Generate the complete code for the Node Detail Panel
- Create the Graph Controls component
- Write the export functionality
- Draft video tutorial scripts
- Set up analytics tracking

Just let me know which feature you want to tackle first!
