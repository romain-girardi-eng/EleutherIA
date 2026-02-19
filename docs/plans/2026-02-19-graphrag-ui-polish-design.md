# GraphRAG UI Polish Design

**Date:** 2026-02-19
**Status:** Approved
**Approach:** Big Bang Refactor (Approach A)

## Decisions

| Decision | Choice |
|----------|--------|
| Graph visualization | Cosmograph WebGL (`@cosmograph/react` v2, already installed) |
| Interactive controls | Radix UI primitives + Tailwind |
| Visual identity | Light modern SaaS (bright, contemporary, rounded cards, vibrant accents) |
| Strategy | Single coordinated pass, no intermediate states |

## 1. Component Architecture

Extract the 998-line `GraphRAGPage/index.tsx` monolith into clean components:

```
pages/GraphRAGPage/
  index.tsx              (~250 lines - orchestrator, state, SSE logic)
  WelcomeHero.tsx        (~100 lines - landing state with typewriter + input)
  ChatPanel.tsx          (~120 lines - left panel container + message list)
  MessageBubble.tsx      (~80 lines - single user/assistant message)
  ChatInput.tsx          (~60 lines - ShineBorder input with stop button)
  MobileGraphSheet.tsx   (~40 lines - floating button + BottomSheet wrapper)

components/graphrag/
  RightPanel.tsx         (refine idle/loading/graph/source-detail states)
  CosmographView.tsx     (NEW - replaces KnowledgeGraphMini canvas)
  SourceDetailCard.tsx   (restyle with modern SaaS look)
  AdvancedOptions.tsx    (rewrite with Radix Switch/Select/Tooltip)
  GraphLegend.tsx        (NEW - horizontal node-type color legend)

components/ui/
  Toggle.tsx             (NEW - Radix Switch with Tailwind styling)
  Select.tsx             (NEW - Radix Select with Tailwind styling)
  Tooltip.tsx            (NEW - Radix Tooltip with Tailwind styling)
```

## 2. Cosmograph Integration

Replace `KnowledgeGraphMini` (hand-rolled canvas force layout) with `@cosmograph/react`.

**Data mapping (same sources, new renderer):**
- Nodes from `response.sources` + `response.reasoning_path.starting_nodes/expanded_nodes`
- Links from `reasoning_path.traversed_edges`
- Node color per type: `nodeColor={n => NODE_COLORS[n.type]}`
- Node size: base 8, highlighted 14

**Configuration:**
- `backgroundColor="#ffffff"` (white)
- `simulationRepulsion={0.5}`
- `simulationLinkSpring={1.0}`
- `simulationLinkDistance={5}`
- `simulationGravity={0.15}`

**Interactions:**
- Built-in hover labels (Cosmograph native)
- Click handler → `onNodeClick(nodeId)`
- Built-in zoom/pan
- Ref: `CosmographRef` for `zoomToNode()` on citation click

**Overlay controls:**
- Top-right: zoom +, zoom -, fit-to-view, pause/play
- Bottom-left: GraphLegend (Person, Concept, Argument, Work color indicators)

## 3. Right Panel States

### Idle
- Clean empty state with subtle SVG graph illustration
- "Ask a question to see the knowledge graph" text
- Soft gradient background

### Loading
- Animated concentric rings expanding (radar pulse effect)
- "Building knowledge graph..." with animated dots
- Replaces flat skeleton bars

### Graph
- Cosmograph fills panel
- Floating legend overlay (bottom-left)
- Floating control buttons (top-right)

### Source Detail
- Top 40%: Cosmograph with zoom-to-node animation on highlighted citation
- Bottom 60%: Redesigned SourceDetailCard with horizontal slide for prev/next

## 4. Radix UI Controls

### New Radix dependencies to install
- `@radix-ui/react-switch`
- `@radix-ui/react-select`
- `@radix-ui/react-tooltip`

### AdvancedOptions rewrite
- Native checkboxes → Radix Switch as pill toggles
- Native selects → Radix Select with custom styled dropdown
- Labels wrapped with Radix Tooltip for descriptions
- Layout: horizontal pill bar for modes, compact inline selects for parameters
- Consistent `rounded-xl`, subtle shadows, smooth transitions

### Citation tooltips
- Replace custom positioned tooltip with Radix Tooltip (collision-aware, accessible)
- Animated entry using `--radix-tooltip-content-transform-origin`

## 5. Visual Style: Light Modern SaaS

### Colors
- Left panel bg: `#ffffff`
- Right panel bg: `#f9fafb` (gray-50)
- Card bg: `#ffffff` with `shadow-sm` + `border border-gray-200`
- Accent: blue-indigo gradient (`#3B82F6` → `#6366F1`)
- Node types (softer): person `#60A5FA`, concept `#4ADE80`, argument `#C084FC`, work `#FBBF24`

### Typography
- Panel headers: `text-sm font-semibold text-gray-500 uppercase tracking-wider`
- Message content: `text-[15px] leading-relaxed`
- Ancient text: serif font
- Metadata: sans-serif

### Spacing
- Messages: `gap-4`, `px-6`
- Cards: `p-4`, `rounded-xl`
- Panel divider: `border-r border-gray-200` with optional `shadow-sm`

### Micro-interactions
- Message appear: `y: 12 -> 0`, `duration: 0.25`
- Source card prev/next: horizontal slide
- Button hover: `scale(1.02)` + `shadow-md`
- Graph node: Cosmograph built-in glow + label

## 6. Out of Scope

- Welcome page hero (already polished)
- Streaming SSE logic / backend integration
- Authentication flow
- Mobile bottom sheet mechanism
- TerminalLoader component
