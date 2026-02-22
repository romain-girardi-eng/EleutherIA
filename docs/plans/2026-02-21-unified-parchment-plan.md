# Unified Parchment Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the How It Works page design language (warm parchment, GlassCards, Instrument Serif headings) to all pages except HomePage and KG Visualizer, and remove Aurora backgrounds site-wide.

**Architecture:** Pure CSS/Tailwind class changes across ~12 files. No structural/routing changes. Each task targets one page or component group, verified visually in the browser via hot reload (`npm run dev` on port 5173).

**Tech Stack:** React 19 + TypeScript, Tailwind CSS 3.4, Framer Motion, Vite 7 (HMR)

**Design reference:** `docs/plans/2026-02-21-unified-parchment-redesign.md`

---

### Task 0: Start Dev Server

**Step 1: Start the frontend dev server**

Run: `cd /Users/romaingirardi/Projects/EleutherIA/frontend && npm run dev`

Keep this running in background for the entire session. All subsequent tasks use hot reload to verify changes.

---

### Task 1: Search Page — Remove Aurora, Apply Parchment

**Files:**
- Modify: `frontend/src/pages/SearchPage.tsx`

**Step 1: Remove AuroraBackground import and usage**

Find the `AuroraBackground` import and its wrapper JSX. Replace the `<AuroraBackground>` wrapper with a plain `<div>` using parchment styling:

```tsx
// REMOVE: import { AuroraBackground } from '../components/ui/aurora-background';

// REPLACE the <AuroraBackground className="!min-h-screen !h-auto !w-full pt-20 pb-12">
// WITH:
<div className="min-h-screen w-full pt-20 pb-12 bg-[#fffdf9]">
```

**Step 2: Update search bar container**

If ShineBorder is used, change its color prop from blue values to warm orange:
```tsx
color={["#f97316", "#ea580c", "#fdba74"]}
```

**Step 3: Update result cards**

Change result card classes from cool grays to warm parchment:
- `bg-white` or `bg-white/95` -> `bg-parchment-100/70`
- `border-neutral-200` or `border-gray-200` -> `border-amber-200/60`
- `dark:bg-neutral-900` -> remove dark variants (we're going light-only)

**Step 4: Update typography**

- h1 heading: add `font-display` class (Instrument Serif)
- Card titles: add `font-display` class
- Ensure all body text uses `text-stone-800` or `text-stone-600`

**Step 5: Verify in browser**

Open `http://localhost:5173/search`. Check:
- Parchment background visible
- No Aurora shimmer
- Warm card borders
- Serif headings
- Typewriter animation still works

**Step 6: Commit**

```bash
git add frontend/src/pages/SearchPage.tsx
git commit -m "feat(frontend): redesign Search page with unified parchment theme"
```

---

### Task 2: Database Page — Remove Aurora, Apply Parchment

**Files:**
- Modify: `frontend/src/pages/DatabasePage.tsx`

**Step 1: Remove AuroraBackground**

Replace `<AuroraBackground>` wrapper with:
```tsx
<div className="min-h-screen w-full pt-20 pb-12 bg-[#fffdf9]">
```

**Step 2: Update stat cards**

Replace cool-toned gradient cards:
- `from-blue-50 to-indigo-50 border-blue-200` -> `from-parchment-50 to-amber-50 border-amber-200/60`
- `from-purple-50 to-pink-50 border-purple-200` -> `from-amber-50 to-orange-50 border-orange-200/60`
- `from-green-50 to-emerald-50 border-green-200` -> `from-orange-50 to-parchment-50 border-amber-200/60`

**Step 3: Update stat pills**

- `bg-white/90` -> `bg-parchment-100/70`
- `bg-blue-50 text-blue-700` -> `bg-amber-50 text-orange-700`

**Step 4: Update section containers**

- `bg-white/95 backdrop-blur-sm` -> `bg-parchment-100/70 backdrop-blur-sm`

**Step 5: Typography**

- h1, h2: add `font-display`
- `text-gray-900` -> `text-stone-800`
- `text-gray-700` -> `text-stone-600`

**Step 6: Verify in browser**

Open `http://localhost:5173/database`. Check warm parchment look, no Aurora, typewriter animation works.

**Step 7: Commit**

```bash
git add frontend/src/pages/DatabasePage.tsx
git commit -m "feat(frontend): redesign Database page with unified parchment theme"
```

---

### Task 3: GraphRAG Page — Dark to Light Redesign

This is the biggest task. Multiple files.

**Files:**
- Modify: `frontend/src/components/graphrag/index.tsx`
- Modify: `frontend/src/components/graphrag/ChatPanel.tsx`
- Modify: `frontend/src/components/graphrag/ChatInput.tsx`
- Modify: `frontend/src/components/graphrag/MessageBubble.tsx`
- Modify: `frontend/src/components/graphrag/RightPanel.tsx`
- Modify: `frontend/src/components/graphrag/PassageReaderPanel.tsx`
- Modify: `frontend/src/components/graphrag/SourceDetailCard.tsx`
- Modify: `frontend/src/components/graphrag/ThinkingProcessPanel.tsx`

**Step 1: Main page wrapper (`index.tsx`)**

Remove `<AuroraBackground>` wrapper. Replace with:
```tsx
<div className="min-h-screen w-full bg-[#fffdf9]">
```

**Step 2: Chat panel (`ChatPanel.tsx`)**

- Background: `bg-white` -> `bg-[#fffdf9]`
- Borders: gray tones -> `border-amber-200/40`

**Step 3: Chat input (`ChatInput.tsx`)**

- Input background: warm parchment
- Border: `border-amber-200` with `focus:border-orange-400 focus:ring-orange-400/20`

**Step 4: Message bubbles (`MessageBubble.tsx`)**

- User messages: `from-gray-900 to-gray-800` -> `from-stone-100 to-stone-50 border border-amber-200/60`
- User message text: `text-white` -> `text-stone-800`
- Assistant messages: Keep light, warm borders `border-amber-200`
- Service badges: `bg-blue-50 text-blue-600` -> `bg-amber-50 text-orange-600`

**Step 5: Right panel (`RightPanel.tsx`)**

- `bg-[#020617]` -> `bg-[#fffdf9]`
- `text-white/50` -> `text-stone-600`
- `border-white/10` -> `border-amber-200/40`
- Tab buttons: warm hover states

**Step 6: Passage reader (`PassageReaderPanel.tsx`)**

- `bg-[#020617]` -> `bg-[#fffdf9]`
- `bg-[#0a1128]` header/footer -> `bg-parchment-100 border-amber-200/40`
- `text-white` -> `text-stone-800`
- `text-white/60` -> `text-stone-600`
- Highlighted passage: `bg-amber-500/10 border-amber-400` -> `bg-amber-100/40 border-l-4 border-amber-600`
- Language badges: keep semantic colors but adjust for light bg
- `hover:bg-white/[0.03]` -> `hover:bg-amber-50/50`

**Step 7: Source detail card (`SourceDetailCard.tsx`)**

- Already mostly light. Warm up borders:
- `border-gray-200` -> `border-amber-200`
- `bg-gray-50/50` -> `bg-parchment-50/50`

**Step 8: Thinking process panel (`ThinkingProcessPanel.tsx`)**

- ShineBorder colors: `["#e0e7ff", "#dbeafe", "#ede9fe"]` -> `["#fdba74", "#f97316", "#fbbf24"]`
- Keep `bg-white/80 backdrop-blur-xl`

**Step 9: Verify in browser**

Open `http://localhost:5173/graphrag`. Check:
- Entire page is light/parchment
- Chat works, messages render correctly
- Passage reader is readable on light background
- Cosmograph graph canvas stays dark (if visible)
- Streaming/typewriter still works
- Thinking panel renders correctly

**Step 10: Commit**

```bash
git add frontend/src/components/graphrag/
git commit -m "feat(frontend): redesign GraphRAG page from dark to light parchment theme"
```

---

### Task 4: Ancient Works Listing — Parchment + Animations

**Files:**
- Modify: `frontend/src/pages/AncientWorksListingPage.tsx`

**Step 1: Remove AuroraBackground**

Replace with parchment `<div>`.

**Step 2: Update header gradient**

- `from-gray-50 to-white` -> `from-parchment-100 to-[#fffdf9]`
- `border-gray-200` -> `border-amber-200/40`

**Step 3: Update work cards**

- `bg-white border-gray-200` -> `bg-parchment-100/60 border-amber-200/40`
- `hover:border-gray-400` -> `hover:border-orange-400`
- Add `hover:shadow-md transition-all duration-300`

**Step 4: Update filter controls**

- `border-gray-300` -> `border-amber-200`
- `focus:border-gray-900 focus:ring-gray-900` -> `focus:border-orange-500 focus:ring-orange-500/20`

**Step 5: Add stagger animation to card grid**

Wrap the card grid in a Framer Motion container with stagger:
```tsx
import { motion } from 'framer-motion';

// Wrap grid items:
<motion.div
  initial={{ opacity: 0, y: 20 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}
  transition={{ duration: 0.5, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
>
```

**Step 6: Typography**

- Headings: add `font-display`
- `text-gray-900` -> `text-stone-800`

**Step 7: Verify and commit**

```bash
git add frontend/src/pages/AncientWorksListingPage.tsx
git commit -m "feat(frontend): redesign Ancient Works page with parchment theme and stagger animations"
```

---

### Task 5: Bibliography Page — Parchment

**Files:**
- Modify: `frontend/src/pages/BibliographyPage.tsx`

**Step 1: Remove AuroraBackground, apply parchment base**

**Step 2: Update ShineBorder colors**

- `["#60A5FA", "#3B82F6", "#93C5FD"]` -> `["#f97316", "#ea580c", "#fdba74"]`

**Step 3: Update letter headings**

- `text-blue-700` -> `text-orange-600`

**Step 4: Update filter inputs**

- `border-gray-200` -> `border-amber-200`
- `bg-white/60` -> `bg-parchment-50/60`

**Step 5: Update bibliography entries**

- `bg-white` -> `bg-parchment-50/40`
- `border-gray-200` -> `border-amber-200/40`

**Step 6: Typography, verify, commit**

```bash
git add frontend/src/pages/BibliographyPage.tsx
git commit -m "feat(frontend): redesign Bibliography page with parchment theme"
```

---

### Task 6: About Page — Warm Palette

**Files:**
- Modify: `frontend/src/pages/AboutPage.tsx`

**Step 1: Remove AuroraBackground**

**Step 2: Replace gradient cards**

- `from-blue-50 to-indigo-50 border-blue-200` -> `from-parchment-50 to-amber-50 border-amber-200/60`
- `from-purple-50 to-pink-50 border-purple-200` -> `from-amber-50 to-orange-50 border-orange-200/60`

**Step 3: Update section containers**

- `bg-white/95` -> `bg-parchment-100/70`

**Step 4: Profile image**

- `border-white` -> `border-amber-200`

**Step 5: Typography, link colors, verify, commit**

- `text-blue-600` -> `text-orange-600`

```bash
git add frontend/src/pages/AboutPage.tsx
git commit -m "feat(frontend): redesign About page with parchment theme"
```

---

### Task 7: Credits Page — Warm Palette

**Files:**
- Modify: `frontend/src/pages/CreditsPage.tsx`

**Step 1: Remove AuroraBackground**

**Step 2: Replace ALL gradient card colors with warm variants**

Use these replacements for differentiation across sections:
- Data sources: `from-parchment-50 to-amber-50 border-amber-200/60`
- Tech stack: `from-amber-50 to-orange-50 border-orange-200/60`
- Libraries: `from-orange-50 to-parchment-50 border-amber-200/60`
- Other sections: vary between these warm tones

**Step 3: Update section headings**

- `text-blue-900` -> `text-stone-800`

**Step 4: Container backgrounds**

- `bg-white/95` -> `bg-parchment-100/70`

**Step 5: Typography, verify, commit**

```bash
git add frontend/src/pages/CreditsPage.tsx
git commit -m "feat(frontend): redesign Credits page with parchment theme"
```

---

### Task 8: Navigation Bar — Warm Polish

**Files:**
- Modify: `frontend/src/App.tsx` (header section, roughly lines 185-362)

**Step 1: Update desktop header background**

- `bg-academic-paper` is already a warm token — check if it maps to parchment. If it's pure white, change to parchment.
- `border-academic-border` -> verify it's warm-toned

**Step 2: Update nav link colors**

- `text-academic-muted` hover states -> ensure they use `hover:text-orange-600`
- Active link state -> `text-orange-600`

**Step 3: Mobile menu on non-homepage**

- If currently white, warm it to parchment
- `bg-zinc-900/95` on homepage is fine (homepage stays dark)

**Step 4: Verify across pages, commit**

Check nav looks consistent on search, database, graphrag, etc.

```bash
git add frontend/src/App.tsx
git commit -m "feat(frontend): polish navigation bar with warm parchment tones"
```

---

### Task 9: How It Works — Polish Sections 6, 7, and Fix Compare Cards

**Files:**
- Modify: `frontend/src/pages/HowItWorksPage.tsx`
- Modify: `frontend/src/components/how-it-works/CompareCards.tsx`

**Step 1: Fix compare card body text**

In `CompareCards.tsx`:
- Red body text (`text-red-700/80`, `text-red-800`) -> `text-stone-800`
- Green body text (`text-emerald-800/80`, `text-emerald-800`) -> `text-stone-800`
- Keep red/green ONLY on: badge labels ("BEFORE"/"AFTER"), icons, metric numbers

**Step 2: Polish Section 6 (Architecture/HiRAG)**

In `HowItWorksPage.tsx`, find the tech/architecture section (~line 526+):
- Replace teal/cyan gradient cards: `from-teal-50 to-cyan-50 border-teal-200` -> `from-parchment-50 to-amber-50 border-amber-200/60`
- Ensure heading uses `font-display text-stone-800`
- Fix any blue/indigo accent colors -> warm amber/orange

**Step 3: Polish Section 7 (Search methods)**

Find search comparison section (~line 697+):
- Same warm palette treatment
- Ensure method comparison cards use consistent GlassCard-like styling
- Fix any remaining cool-toned borders or text

**Step 4: Verify scroll through all How It Works sections**

Open `http://localhost:5173/how-it-works`. Scroll through all 9 sections:
- Section 2: Compare cards have dark body text, colored badges only
- Section 6: Warm palette, no teal/cyan
- Section 7: Warm palette, consistent with other sections
- All other sections: unchanged (they already look good)

**Step 5: Commit**

```bash
git add frontend/src/pages/HowItWorksPage.tsx frontend/src/components/how-it-works/CompareCards.tsx
git commit -m "feat(frontend): polish How It Works sections 6, 7 and fix compare card text colors"
```

---

### Task 10: Final Sweep — Remove Remaining Aurora Imports

**Files:**
- Possibly: any file still importing AuroraBackground

**Step 1: Search for remaining Aurora usage**

```bash
grep -r "AuroraBackground\|aurora-background" frontend/src/ --include="*.tsx" --include="*.ts" -l
```

**Step 2: Remove unused imports**

If any pages still import AuroraBackground but no longer use it, remove the import.

**Step 3: Check for any remaining cool-toned remnants**

Quick grep for obvious patterns:
```bash
grep -r "from-blue-50\|border-blue-200\|text-blue-700\|bg-\[#020617\]" frontend/src/pages/ frontend/src/components/graphrag/ --include="*.tsx" -l
```

Fix any stragglers.

**Step 4: Full visual walkthrough**

Visit every page in browser:
- `/search` - parchment, warm, typewriter works
- `/database` - parchment, warm, typewriter works
- `/graphrag` - light, warm, streaming works
- `/texts` - parchment, stagger animations
- `/bibliography` - parchment, warm ShineBorder
- `/about` - warm gradients
- `/credits` - warm gradients
- `/how-it-works` - polished sections 6, 7; dark body text on compare cards
- `/` - UNCHANGED (particles, dark hero)
- `/graph` or `/visualizer` - UNCHANGED (dark KG viz)

**Step 5: Final commit**

```bash
git add -A frontend/src/
git commit -m "chore(frontend): cleanup remaining Aurora imports and cool-tone remnants"
```

---

### Task Dependency Summary

```
Task 0 (dev server) ──> Tasks 1-9 (parallel-safe, independent pages)
                    ──> Task 10 (final sweep, depends on all above)
```

Tasks 1-9 can be executed in any order. Task 3 (GraphRAG) is the largest.
Task 10 must be last.
