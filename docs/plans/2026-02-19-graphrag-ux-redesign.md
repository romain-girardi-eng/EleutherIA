# GraphRAG UX Redesign — Two-Panel Research Layout

**Date:** 2026-02-19
**Status:** Approved
**Scope:** `frontend/src/pages/GraphRAGPage/`

---

## Problem Statement

The current GraphRAG page has three UX problems:

1. **Cluttered response area** — the assistant message bubble stacks up to 7 sections (answer, sources panel, reasoning path, citations, evidence chains, bibliography, metadata). The actual answer gets buried.
2. **Overwhelming welcome state** — mode toggles, parameter dropdowns, stats pills, and a demo button all compete for attention before the user has asked anything.
3. **Rough streaming experience** — the terminal loader and a partial answer preview coexist awkwardly, and auto-scroll during streaming was jarring.

## Audience

Both casual users (curious about ancient philosophy) and academic researchers. The design must be approachable on the surface and deep on demand.

---

## Design: Two-Panel Research Layout

### Layout Overview

```
┌──────────────────────────────────────────────┬────────────────────────┐
│  LEFT PANEL (65%)                            │  RIGHT PANEL (35%)     │
│                                              │                        │
│  [Header: HiRAG Q&A  ⚙]                     │  [Knowledge Graph /    │
│                                              │   Source Detail]       │
│  ┌──────────────────────────────────────┐   │                        │
│  │ User: How did Stoics reconcile...    │   │  ● Chrysippus          │
│  └──────────────────────────────────────┘   │    ↕                   │
│  ┌──────────────────────────────────────┐   │  ● Fate (heimarmenē)   │
│  │ HiRAG: The Stoics developed a...    │   │    ↕                   │
│  │                                      │   │  ● eph' hēmin          │
│  │ [1] Chrysippus distinguished...      │   │                        │
│  │ [2] The cylinder analogy...          │   │  ──────────────────── │
│  │                                      │   │  [Source detail card] │
│  └──────────────────────────────────────┘   │                        │
│                                              │                        │
│  [═══════════════════════════════ Ask ►]    │                        │
└──────────────────────────────────────────────┴────────────────────────┘
```

On mobile (`< lg`): right panel collapses. A floating `📊` button (bottom-right, above input) opens a bottom sheet (60vh, draggable to full-screen).

---

## Three Page States

### State 1 — Welcome (no query yet)

Full-width, single-column, vertically centered:

```
        HiRAG
        [Typewriter: Knowledge Graph / Ancient Philosophy / Scholarly Q&A]

   Subtitle: one-line description

   ┌──────────────────────────────────────────────────┐
   │  Ask about ancient debates on free will...    Ask │
   └──────────────────────────────────────────────────┘

            ⚙ Advanced options ▸   Try Demo
```

- **No stats pills, no mode toggle grid, no parameter dropdowns** — all hidden behind `⚙ Advanced options` disclosure
- Advanced options expands inline to show: 4 mode checkboxes (Academic, Deep Reasoning, Ancient Only, Agentic) + 3 parameter dropdowns (Breadth, Depth, Context)
- `Try Demo` is a small grey text link, no button styling

### State 2 — Streaming (query submitted, awaiting response)

- Layout shifts to two-column (Framer Motion `layout` animation)
- **Left panel (65%)**: TerminalLoader centered, full streaming area. No partial answer preview — clean mystery until complete. Keep existing terminal loader as-is.
- **Right panel (35%)**: Skeleton wave animation (faint pulse matching terminal loader vibes). No content yet.

### State 3 — Response (streaming complete)

- **Left panel**: Full answer text with inline `[n]` citation superscripts. Citations are hoverable (tooltip) and clickable (animates right panel to that node).
- **Right panel**: Mini knowledge graph, then source detail card on interaction.

---

## Left Panel — Conversation

### Header
- Fixed at top: "HiRAG Q&A" title + small `⚙` icon that opens Advanced settings in a slide-over modal
- Not in the scroll flow

### Message Thread
- Scrollable
- **User bubbles**: right-aligned, dark gradient card (same as today)
- **Assistant bubbles**: white card, full-width within the column. Contains **only**:
  - Answer text with inline `[n]` citation superscripts
  - No sources panel, no reasoning path accordion, no citations list, no bibliography — all of that moves to the right panel
- Citations `[n]` are rendered as styled `<sup>` elements — hoverable (tooltip with source label) and clickable (triggers right panel animation)

### Streaming Area
- TerminalLoader takes the full streaming area height
- No concurrent partial answer text during streaming
- When streaming completes: loader fades out, full answer fades in with Framer Motion

### Bottom Input
- Sticky `bottom-0`, same ShineBorder design as today
- Shows Stop button during streaming, Ask button otherwise

---

## Right Panel — Dynamic Knowledge Graph

The right panel has **four states** with animated transitions between them (Framer Motion `AnimatePresence`):

### State: `idle`
Shown before any query.
- Faint, low-opacity placeholder graph (static node outlines)
- Text: "Knowledge graph will appear here"
- Subtle pulse animation on the node outlines

### State: `loading`
Shown during streaming.
- Skeleton wave matching terminal loader rhythm
- Node outlines pulse gently

### State: `graph`
Shown after response arrives. Default state.
- **Mini force-directed graph** rendered on a `<canvas>` (D3 force simulation or hand-rolled with `requestAnimationFrame`)
- **Node colors by type**: Person=blue-500, Concept=green-500, Argument=purple-500, Work=amber-500, default=gray-400
- **Edges**: thin lines (gray-300), animated draw-in on arrival
- **Node labels**: shown on hover as tooltip
- **Node interactions**: click → transitions to `source-detail` state
- **Citation link**: when user clicks `[n]` in the left panel, the corresponding node scales up + glows for 800ms, then `source-detail` opens
- Smooth entrance animation: nodes fade in staggered, edges draw in after nodes

### State: `source-detail`
Shown when a node or citation is clicked.
- Graph shrinks to top ~40% of the right panel (still visible, still interactive)
- Source detail card slides up from below with Framer Motion spring animation
- Card contains:
  - Source label + type badge
  - Original Greek/Latin text (if available via `citationTexts`)
  - English translation
  - `→ View in Visualizer` link (navigates to `/visualizer/:nodeId`)
  - `✕` close button → returns to `graph` state
- Multiple sources: card slides to next/prev with swipe or arrow buttons

---

## Component Architecture

### New components to create

| Component | Path | Description |
|-----------|------|-------------|
| `RightPanel` | `components/graphrag/RightPanel.tsx` | Container managing the 4 panel states with AnimatePresence |
| `KnowledgeGraphMini` | `components/graphrag/KnowledgeGraphMini.tsx` | D3/canvas mini force graph |
| `SourceDetailCard` | `components/graphrag/SourceDetailCard.tsx` | Source detail with text/translation |
| `AdvancedOptions` | `components/graphrag/AdvancedOptions.tsx` | Collapsible settings disclosure |

### Modified components

| Component | Change |
|-----------|--------|
| `GraphRAGPage/index.tsx` | Restructure layout to two-column; move source/citation/reasoning data to right panel state; simplify welcome state |
| `MessageBubble` | Remove sources panel, citations section, reasoning path, bibliography, evidence chains — replace with inline `[n]` citation superscripts |

### State additions to `GraphRAGPage`

```typescript
// Right panel state
type RightPanelState = 'idle' | 'loading' | 'graph' | 'source-detail';
const [rightPanelState, setRightPanelState] = useState<RightPanelState>('idle');
const [activeSourceIndex, setActiveSourceIndex] = useState<number | null>(null);

// Citation click handler (called from MessageBubble)
const handleCitationClick = (citationIndex: number) => {
  setActiveSourceIndex(citationIndex);
  setRightPanelState('source-detail');
  // Also trigger node highlight in graph
};
```

---

## Animation Specifications

| Transition | Animation |
|-----------|-----------|
| Welcome → two-column layout | Framer Motion `layout` prop on containers, 400ms ease-in-out |
| Loading skeleton | Pulse opacity 0.3→0.7, 1.2s infinite |
| Graph nodes entrance | Staggered fade-in, 30ms delay per node, 300ms each |
| Graph edges draw-in | SVG `stroke-dashoffset` from length to 0, 400ms after nodes |
| Citation click → node highlight | Scale 1→1.3→1 + box-shadow glow, 800ms |
| graph → source-detail | Graph height 100%→40% spring, card slides up 100%→0%, 500ms spring |
| source-detail → graph | Reverse, 300ms ease-out |
| Streaming loader → answer | Loader opacity 1→0, answer opacity 0→1, 300ms crossfade |

---

## Mobile Behavior

- Below `lg` breakpoint: single column layout (left panel only, full width)
- Floating `📊` button appears bottom-right, above the sticky input, z-50
- Clicking opens a bottom sheet (Framer Motion drag + animate):
  - Initial height: 60vh
  - Drag handle at top
  - Drag up → 95vh (full screen)
  - Drag down past 30vh → closes
  - Contains: right panel content (graph or source detail)

---

## What's Removed

The following sections are **removed** from `MessageBubble` since they move to the right panel:
- `SourcesPanel` component
- Reasoning path accordion
- Citations collapsible (ancient sources + modern scholarship)
- `EvidenceChainPanel`
- `BibliographyPanel`

These components remain in the codebase but are no longer rendered in `MessageBubble`. Their data is passed to `RightPanel` instead.

---

## Out of Scope

- Refactoring streaming event parsing (fragile keyword matching) — left as-is
- Multi-query history sidebar (Approach C) — not in this redesign
- Backend changes — purely frontend
