# How It Works Page — Scroll-Locked Redesign

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign `/how-it-works` as a fullscreen scroll-snap page with warm amber-orange aesthetic, scroll-triggered animations, dot navigator, and aurora accent on the overview section.

**Architecture:** Replace the current sidebar + scrollable layout with 10 fullscreen `100vh` sections using CSS `scroll-snap-type: y mandatory`. Each section reveals content via framer-motion `whileInView`. A fixed dot navigator (right side) replaces the collapsible sidebar. The aurora rainbow appears only on section 1 (Overview) for brand coherence; sections 2–10 use warm parchment backgrounds (`#fdf8f3` / `#fef3e8`) with orange-amber (`#f97316` / `#f59e0b`) gradient accents.

**Tech Stack:** React 19, TypeScript, framer-motion, Tailwind CSS (existing config), lucide-react icons. No new dependencies.

**Design reference:** `frontend/public/prototype-how-it-works.html` (approved by user on localhost:4321)

---

### Task 1: Add orange-amber tokens to Tailwind config

**Files:**
- Modify: `frontend/tailwind.config.js`

**Step 1: Add the new color tokens**

In `theme.extend.colors`, add an `orange` palette alongside the existing `primary` and `accent`:

```js
orange: {
  50:  '#fff7ed',
  100: '#ffedd5',
  200: '#fed7aa',
  300: '#fdba74',
  400: '#fb923c',
  500: '#f97316',
  600: '#ea580c',
  700: '#c2410c',
  800: '#9a3412',
  900: '#7c2d12',
},
```

Also add a `parchment` shorthand:

```js
parchment: {
  DEFAULT: '#fdf8f3',
  warm: '#fef3e8',
},
```

And add a `glow-orange` box-shadow alongside existing `glow` and `glow-accent`:

```js
'glow-orange': '0 0 20px rgba(249, 115, 22, 0.3)',
```

**Step 2: Verify the build still works**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors.

**Step 3: Commit**

```bash
git add frontend/tailwind.config.js
git commit -m "feat: add orange-amber and parchment color tokens to tailwind config"
```

---

### Task 2: Create the DotNavigator component

**Files:**
- Create: `frontend/src/components/how-it-works/DotNavigator.tsx`

**Step 1: Write the component**

Props: `sections: { id: string; label: string }[]`, `activeSection: string`, `onNavigate: (id: string) => void`.

Renders a `fixed right-6 top-1/2 -translate-y-1/2 z-[100]` column of dots. Active dot: `w-2 h-6 rounded-full bg-orange-500` with `box-shadow: 0 0 12px rgba(249,115,22,0.4)`. Inactive: `w-2 h-2 rounded-full bg-parchment-warm/60`. On hover, show a tooltip label to the left via `opacity-0 group-hover:opacity-100` transition. Use `motion.div layoutId="active-dot"` for the pill shape animation on the active state.

Hide on `lg:` breakpoint below (mobile) — `hidden lg:flex`.

```tsx
import { motion } from 'framer-motion';

interface DotNavigatorProps {
  sections: { id: string; label: string }[];
  activeSection: string;
  onNavigate: (id: string) => void;
}

export default function DotNavigator({ sections, activeSection, onNavigate }: DotNavigatorProps) {
  return (
    <nav className="fixed right-7 top-1/2 -translate-y-1/2 z-[100] hidden lg:flex flex-col gap-2.5">
      {sections.map((section) => {
        const isActive = activeSection === section.id;
        return (
          <button
            key={section.id}
            onClick={() => onNavigate(section.id)}
            className="group flex items-center gap-2.5 justify-end"
            aria-label={section.label}
          >
            <span className="text-[11px] font-medium text-parchment-warm opacity-0 group-hover:opacity-100 transition-all duration-200 translate-x-1.5 group-hover:translate-x-0 whitespace-nowrap pointer-events-none"
              style={{ color: isActive ? '#f97316' : '#7c6a56' }}
            >
              {section.label}
            </span>
            <motion.span
              className="rounded-full flex-shrink-0"
              animate={{
                width: 8,
                height: isActive ? 24 : 8,
                backgroundColor: isActive ? '#f97316' : '#e8d9c5',
                boxShadow: isActive ? '0 0 12px rgba(249,115,22,0.4)' : '0 0 0px transparent',
              }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
            />
          </button>
        );
      })}
    </nav>
  );
}
```

**Step 2: Verify it compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors from the new file.

**Step 3: Commit**

```bash
git add frontend/src/components/how-it-works/DotNavigator.tsx
git commit -m "feat: create DotNavigator component for how-it-works page"
```

---

### Task 3: Create the ScrollSection wrapper component

**Files:**
- Create: `frontend/src/components/how-it-works/ScrollSection.tsx`

**Step 1: Write the component**

A `100vh` fullscreen section with scroll-snap, reveal animations, and alternating backgrounds. Takes children, an `id`, a section `index` (for the counter "01 / 10"), and optional `className` override.

```tsx
import { motion } from 'framer-motion';
import { type ReactNode } from 'react';

interface ScrollSectionProps {
  id: string;
  index: number;
  totalSections: number;
  children: ReactNode;
  className?: string;
  /** Optional decorative blobs */
  blobs?: ReactNode;
}

const revealVariants = {
  hidden: { opacity: 0, y: 28 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

export default function ScrollSection({
  id,
  index,
  totalSections,
  children,
  className = '',
  blobs,
}: ScrollSectionProps) {
  const isEven = index % 2 === 0;
  const bgClass = isEven ? 'bg-parchment' : 'bg-parchment-warm';

  return (
    <section
      id={id}
      className={`min-h-screen snap-start snap-always relative flex flex-col justify-center px-6 py-20 md:px-20 lg:px-24 lg:pr-28 overflow-hidden ${bgClass} ${className}`}
    >
      {/* Section counter */}
      <span className="absolute top-12 right-20 text-[11px] font-semibold tracking-[0.12em] text-orange-200/60 z-[2] hidden md:block">
        {String(index + 1).padStart(2, '0')} / {String(totalSections).padStart(2, '0')}
      </span>

      {/* Left accent line */}
      <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-gradient-to-b from-orange-500 via-amber-400 to-transparent opacity-40" />

      {/* Decorative blobs */}
      {blobs}

      {/* Content */}
      <div className="relative z-[2] max-w-[960px] w-full">
        {children}
      </div>
    </section>
  );
}

/** Eyebrow label used above headings */
export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <motion.span
      variants={revealVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      custom={0}
      className="inline-flex items-center gap-1.5 text-xs font-semibold tracking-[0.1em] uppercase text-orange-500 mb-4"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
      {children}
    </motion.span>
  );
}

/** Animated heading */
export function SectionHeading({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <motion.h2
      variants={revealVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      custom={1}
      className={`font-serif text-3xl md:text-4xl lg:text-[2.8rem] leading-tight text-[#1a1208] mb-4 ${className}`}
    >
      {children}
    </motion.h2>
  );
}

/** Animated lead paragraph */
export function SectionLead({ children }: { children: ReactNode }) {
  return (
    <motion.p
      variants={revealVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      custom={2}
      className="text-base md:text-lg leading-relaxed text-[#7c6a56] max-w-[620px] mb-10"
    >
      {children}
    </motion.p>
  );
}

/** Animated content block (for cards, pipelines, etc.) */
export function SectionContent({ children, delay = 3 }: { children: ReactNode; delay?: number }) {
  return (
    <motion.div
      variants={revealVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      custom={delay}
    >
      {children}
    </motion.div>
  );
}

/** Orange gradient accent text */
export function AccentWord({ children }: { children: ReactNode }) {
  return (
    <span className="bg-gradient-to-r from-orange-500 to-amber-500 bg-clip-text text-transparent">
      {children}
    </span>
  );
}

/** Decorative blur blob */
export function Blob({ color, className }: { color: 'orange' | 'amber' | 'aurora' | 'teal'; className: string }) {
  const colorMap = {
    orange: 'rgba(249,115,22,0.25)',
    amber:  'rgba(245,158,11,0.2)',
    aurora: 'rgba(167,139,250,0.15)',
    teal:   'rgba(52,211,153,0.12)',
  };
  return (
    <div
      className={`absolute rounded-full blur-[80px] opacity-50 pointer-events-none z-[1] ${className}`}
      style={{ background: `radial-gradient(circle, ${colorMap[color]}, transparent 70%)` }}
    />
  );
}

export { revealVariants };
```

**Step 2: Verify it compiles**

Run: `cd frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add frontend/src/components/how-it-works/ScrollSection.tsx
git commit -m "feat: create ScrollSection, Eyebrow, Blob primitives for how-it-works"
```

---

### Task 4: Create the GlassCard component

**Files:**
- Create: `frontend/src/components/how-it-works/GlassCard.tsx`

**Step 1: Write the component**

The warm-parchment version of glassmorphism: `bg-white/70 backdrop-blur-sm border border-[#e8d9c5] rounded-2xl` with orange glow on hover.

```tsx
import { type ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  icon?: ReactNode;
  title?: string;
}

export default function GlassCard({ children, className = '', icon, title }: GlassCardProps) {
  return (
    <div className={`bg-white/70 backdrop-blur-sm border border-[#e8d9c5] rounded-2xl p-6 transition-all duration-250 hover:border-orange-500/35 hover:shadow-[0_4px_24px_rgba(249,115,22,0.12)] hover:-translate-y-0.5 ${className}`}>
      {icon && (
        <div className="w-10 h-10 rounded-[10px] bg-gradient-to-br from-orange-500/15 to-amber-500/10 flex items-center justify-center text-xl mb-3">
          {icon}
        </div>
      )}
      {title && <h3 className="text-[15px] font-semibold text-[#1a1208] mb-1.5">{title}</h3>}
      <div className="text-[13.5px] leading-relaxed text-[#7c6a56]">{children}</div>
    </div>
  );
}
```

**Step 2: Verify it compiles**

Run: `cd frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add frontend/src/components/how-it-works/GlassCard.tsx
git commit -m "feat: create GlassCard component with orange hover glow"
```

---

### Task 5: Create the PipelineSteps component

**Files:**
- Create: `frontend/src/components/how-it-works/PipelineSteps.tsx`

**Step 1: Write the component**

Numbered vertical pipeline with orange gradient step circles (matching prototype).

```tsx
import { type ReactNode } from 'react';

interface Step {
  label: string;
  title: string;
  description: string;
}

interface PipelineStepsProps {
  steps: Step[];
}

export default function PipelineSteps({ steps }: PipelineStepsProps) {
  return (
    <div className="flex flex-col max-w-[700px] mt-8">
      {steps.map((step, i) => (
        <div key={i} className="flex gap-5 items-start py-5 border-b border-[#e8d9c5] last:border-b-0">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-orange-500 to-amber-500 text-white text-sm font-bold flex items-center justify-center flex-shrink-0 shadow-[0_2px_10px_rgba(249,115,22,0.3)]">
            {step.label}
          </div>
          <div>
            <h4 className="text-[15px] font-semibold text-[#1a1208] mb-1">{step.title}</h4>
            <p className="text-[13.5px] text-[#7c6a56] leading-relaxed">{step.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/how-it-works/PipelineSteps.tsx
git commit -m "feat: create PipelineSteps component with orange gradient numbers"
```

---

### Task 6: Create the CompareCards component

**Files:**
- Create: `frontend/src/components/how-it-works/CompareCards.tsx`

**Step 1: Write the component**

Side-by-side comparison layout (Keyword Search vs Semantic Search) matching the prototype's warm style — left card neutral, right card with orange tint.

```tsx
interface CompareRow {
  label: string;
  value: string;
}

interface CompareCardsProps {
  left: { title: string; rows: CompareRow[] };
  right: { title: string; rows: CompareRow[] };
}

export default function CompareCards({ left, right }: CompareCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 max-w-[760px]">
      {/* Left — neutral */}
      <div className="rounded-2xl p-7 border border-[#e8d9c5] bg-white/80">
        <h4 className="text-[13px] font-bold tracking-[0.06em] uppercase text-[#7c6a56] mb-4">{left.title}</h4>
        {left.rows.map((row, i) => (
          <div key={i} className="flex justify-between items-center py-2 border-b border-black/[.04] last:border-b-0 text-[13.5px]">
            <span className="text-[#7c6a56]">{row.label}</span>
            <span className="font-semibold text-[#1a1208]">{row.value}</span>
          </div>
        ))}
      </div>
      {/* Right — orange accent */}
      <div className="rounded-2xl p-7 border border-orange-500/25 bg-gradient-to-br from-orange-500/[.08] to-amber-500/[.06]">
        <h4 className="text-[13px] font-bold tracking-[0.06em] uppercase text-orange-500 mb-4">{right.title}</h4>
        {right.rows.map((row, i) => (
          <div key={i} className="flex justify-between items-center py-2 border-b border-black/[.04] last:border-b-0 text-[13.5px]">
            <span className="text-[#7c6a56]">{row.label}</span>
            <span className="font-semibold text-orange-500">{row.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/how-it-works/CompareCards.tsx
git commit -m "feat: create CompareCards with orange-accented right card"
```

---

### Task 7: Create the FAIRBadges component

**Files:**
- Create: `frontend/src/components/how-it-works/FAIRBadges.tsx`

**Step 1: Write the component**

Four square badges with orange gradient letters (F, A, I, R) matching prototype.

```tsx
const badges = [
  { letter: 'F', label: 'Findable' },
  { letter: 'A', label: 'Accessible' },
  { letter: 'I', label: 'Interoperable' },
  { letter: 'R', label: 'Reusable' },
];

export default function FAIRBadges() {
  return (
    <div className="flex flex-wrap gap-3.5 mt-8">
      {badges.map((b) => (
        <div
          key={b.letter}
          className="w-20 h-20 rounded-[20px] bg-white/80 border border-[#e8d9c5] flex flex-col items-center justify-center gap-1.5 transition-all duration-200 hover:border-orange-500 hover:text-orange-500 hover:shadow-[0_0_16px_rgba(249,115,22,0.15)] hover:-translate-y-0.5 cursor-default"
        >
          <span className="text-[28px] font-serif leading-none bg-gradient-to-br from-orange-500 to-amber-500 bg-clip-text text-transparent">
            {b.letter}
          </span>
          <span className="text-[11px] font-bold tracking-[0.08em] uppercase text-[#7c6a56]">
            {b.label}
          </span>
        </div>
      ))}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/how-it-works/FAIRBadges.tsx
git commit -m "feat: create FAIRBadges component with gradient letters"
```

---

### Task 8: Create the GitHubPill component

**Files:**
- Create: `frontend/src/components/how-it-works/GitHubPill.tsx`

**Step 1: Write the component**

Fixed floating pill at top center (matching prototype). Appears with 1s delay animation.

```tsx
import { motion } from 'framer-motion';
import { Github } from 'lucide-react';

export default function GitHubPill() {
  return (
    <motion.a
      href="https://github.com/romain-girardi-eng/EleutherIA"
      target="_blank"
      rel="noopener noreferrer"
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 1, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="fixed top-5 left-1/2 -translate-x-1/2 z-[999] flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/70 backdrop-blur-xl border border-[#e8d9c5] text-[13px] font-medium text-[#1a1208] shadow-[0_2px_16px_rgba(249,115,22,0.08)] hover:border-orange-500 hover:shadow-[0_2px_20px_rgba(249,115,22,0.18)] transition-all duration-200"
    >
      <Github className="w-4 h-4" />
      EleutherIA
      <span className="bg-gradient-to-r from-orange-500 to-amber-500 text-white text-[11px] font-semibold px-2 py-0.5 rounded-full ml-1">
        ★ Open Source
      </span>
    </motion.a>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/how-it-works/GitHubPill.tsx
git commit -m "feat: create GitHubPill floating component"
```

---

### Task 9: Create the ScrollHint component

**Files:**
- Create: `frontend/src/components/how-it-works/ScrollHint.tsx`

**Step 1: Write the component**

Mouse wheel + "Scroll to explore" at the bottom of section 1. Animated bouncing + scrolling dot inside the wheel outline. Uses Tailwind `@keyframes` (add to tailwind config) or inline CSS animation.

```tsx
export default function ScrollHint() {
  return (
    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 z-[2] animate-bounce-slow">
      <div className="w-[22px] h-[34px] border-2 border-[#e8d9c5] rounded-[11px] relative">
        <div className="absolute top-[5px] left-1/2 -translate-x-1/2 w-1 h-2 rounded-sm bg-orange-500 animate-[scrollDot_2s_ease-in-out_infinite]" />
      </div>
      <span className="text-xs font-medium tracking-[0.08em] uppercase text-[#7c6a56]">
        Scroll to explore
      </span>
    </div>
  );
}
```

Add `scrollDot` keyframes to `tailwind.config.js` alongside the other keyframes:

```js
scrollDot: {
  '0%, 100%': { top: '5px', opacity: '1' },
  '50%': { top: '14px', opacity: '0.4' },
},
```

And add the animation shorthand:

```js
'scroll-dot': 'scrollDot 2s ease-in-out infinite',
```

**Step 2: Commit**

```bash
git add frontend/src/components/how-it-works/ScrollHint.tsx frontend/tailwind.config.js
git commit -m "feat: create ScrollHint component with animated wheel"
```

---

### Task 10: Create the AuroraStrip component

**Files:**
- Create: `frontend/src/components/how-it-works/AuroraStrip.tsx`

**Step 1: Write the component**

The 4px animated rainbow gradient strip + warm glow bleed — placed only on the Overview section. Uses the existing `animate-aurora` keyframe but with a custom gradient of aurora colors ending in orange.

```tsx
export default function AuroraStrip() {
  return (
    <>
      {/* 4px rainbow line */}
      <div
        className="absolute top-0 left-0 right-0 h-1 z-[3]"
        style={{
          background: 'linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6, #34d399, #fbbf24, #f97316)',
          backgroundSize: '300% 100%',
          animation: 'aurora 8s linear infinite',
        }}
      />
      {/* Warm glow bleed below */}
      <div className="absolute top-1 left-0 right-0 h-28 bg-gradient-to-b from-orange-500/[.08] to-transparent z-[2]" />
    </>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/how-it-works/AuroraStrip.tsx
git commit -m "feat: create AuroraStrip with rainbow gradient and warm glow"
```

---

### Task 11: Create the BackgroundMesh component

**Files:**
- Create: `frontend/src/components/how-it-works/BackgroundMesh.tsx`

**Step 1: Write the component**

Fixed full-viewport radial gradient mesh (warm orange tones) behind all sections.

```tsx
export default function BackgroundMesh() {
  return (
    <div
      className="fixed inset-0 pointer-events-none z-0"
      style={{
        background: [
          'radial-gradient(ellipse 80% 60% at 10% 0%, rgba(249,115,22,0.07) 0%, transparent 60%)',
          'radial-gradient(ellipse 60% 80% at 90% 20%, rgba(245,158,11,0.06) 0%, transparent 60%)',
          'radial-gradient(ellipse 70% 50% at 50% 100%, rgba(253,230,138,0.12) 0%, transparent 60%)',
          '#fdf8f3',
        ].join(', '),
      }}
    />
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/how-it-works/BackgroundMesh.tsx
git commit -m "feat: create BackgroundMesh with warm orange radial gradients"
```

---

### Task 12: Rewrite HowItWorksPage.tsx — page shell and scroll-snap container

**Files:**
- Modify: `frontend/src/pages/HowItWorksPage.tsx`

**Step 1: Replace the entire page with the new scroll-snap layout**

This is the largest task. The page shell becomes:

1. Remove: the aurora background layer, the sidebar nav, the GitHub banner, and all 10 inline section blocks
2. Add: `BackgroundMesh`, `GitHubPill`, `DotNavigator`, and a `<main>` with `snap-y snap-mandatory overflow-y-scroll h-screen`
3. Each of the 10 sections becomes a `<ScrollSection>` calling the new primitives

The page should:
- Import all new components from `./components/how-it-works/`
- Keep existing component imports: `EmbeddingsVisualization3D`, `EmbeddingJourneyUltra` (lazy), `DatabaseWithRestApi`, `HiRAGImplementationDetails`
- Keep `useTranslation()` — all text comes from `learn.*` i18n keys (already exist in `en.json`)
- Use `IntersectionObserver` (via `useEffect`) to track `activeSection` for the dot navigator — observe each `<section>` with `threshold: 0.5`
- `scrollToSection(id)` uses `document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })`

**Section mapping (preserving all existing interactive demos):**

| # | id | Content | Special |
|---|---|---|---|
| 1 | overview | Stats, challenge/solution cards, three pillars | AuroraStrip, ScrollHint |
| 2 | knowledge-graph | KG explanation, NodeTypeCards, KnowledgeGraphDemo, TimelineVisualization | — |
| 3 | embeddings | EmbeddingsExplanation, EmbeddingJourneyUltra (lazy), EmbeddingsVisualization3D | CompareCards |
| 4 | graphrag | 5-stage pipeline animation | PipelineSteps |
| 5 | hybrid-search | 3 search method cards, RRF diagram | GlassCard grid |
| 6 | ancient-texts | School tags, CTS URN explanation | Greek quote block |
| 7 | fair | FAIR badges, Zenodo DOI | FAIRBadges |
| 8 | glossary | Search + term cards | GlassCard grid |
| 9 | hirag | 3-level hierarchy diagram | PipelineSteps (L1/L2/L3) |
| 10 | hirag-details | DatabaseWithRestApi, HiRAGImplementationDetails | GitHub CTA button |

**Key structural rules:**
- Every section wraps content in `<ScrollSection id={...} index={...} totalSections={10}>`
- Headings use `<SectionHeading>` with `<AccentWord>` for the orange gradient word
- Body text uses `<SectionLead>`
- Card grids use `<SectionContent>` wrapper for stagger delay
- Existing interactive components (`KnowledgeGraphDemo`, `TimelineVisualization`, `EmbeddingsVisualization3D`, `EmbeddingJourneyUltra`, `EmbeddingsExplanation`, `DatabaseWithRestApi`, `HiRAGImplementationDetails`) are kept as-is but wrapped in `<SectionContent>` for reveal animation
- All helper components currently defined inline in HowItWorksPage.tsx (`SectionHeader`, `StatCard`, `PillarCard`, `NodeTypeCard`, `KnowledgeGraphDemo`, `TimelineVisualization`, `EmbeddingsExplanation`, `GraphRAGPipeline`) — extract only if they clash with the new design. Otherwise keep inline but restyle classes.

**Step 2: Verify the build**

Run: `cd frontend && npm run build`
Expected: Build succeeds.

**Step 3: Visual check**

Run: `cd frontend && npm run dev`
Open: `http://localhost:5173/how-it-works`
Verify: 10 fullscreen sections snap on scroll, dot navigator tracks active, aurora strip on section 1 only, orange accents throughout, all interactive demos render.

**Step 4: Commit**

```bash
git add frontend/src/pages/HowItWorksPage.tsx
git commit -m "feat: rewrite HowItWorksPage with scroll-snap layout and orange-amber design"
```

---

### Task 13: Add Instrument Serif font

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/tailwind.config.js`

**Step 1: Add Google Fonts preconnect + stylesheet to index.html**

In `<head>`, add:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet" />
```

**Step 2: Update tailwind font families**

In `tailwind.config.js`, update the `fontFamily.serif` and `fontFamily.sans` to prioritize our new fonts:

```js
serif: [
  '"Instrument Serif"',
  'Georgia',
  '"Times New Roman"',
  'Times',
  'serif',
],
sans: [
  '"DM Sans"',
  'system-ui',
  '-apple-system',
  'BlinkMacSystemFont',
  '"Segoe UI"',
  'Roboto',
  '"Helvetica Neue"',
  'Arial',
  'sans-serif',
],
```

**Step 3: Verify fonts load**

Run: `cd frontend && npm run dev`
Open: `http://localhost:5173/how-it-works`
Verify: Headings render in Instrument Serif (editorial look), body in DM Sans (clean).

**Step 4: Commit**

```bash
git add frontend/index.html frontend/tailwind.config.js
git commit -m "feat: add Instrument Serif and DM Sans fonts for how-it-works page"
```

---

### Task 14: Full build verification + visual QA

**Files:**
- No file changes (verification only)

**Step 1: Run the full build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors.

**Step 2: Run TypeScript check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No type errors.

**Step 3: Visual QA checklist**

Open `http://localhost:5173/how-it-works` and verify:

- [ ] 10 fullscreen sections snap correctly on scroll (scroll-snap works)
- [ ] Dot navigator on right side tracks active section (orange pill)
- [ ] Aurora rainbow strip visible on section 1 only
- [ ] GitHub pill appears with delay animation at top center
- [ ] Scroll hint with animated wheel at bottom of section 1
- [ ] Orange gradient text on section headings (AccentWord)
- [ ] GlassCards have orange border/glow on hover
- [ ] Comparison cards in Embeddings section are fully readable (no contrast issues)
- [ ] Pipeline steps have orange gradient numbers
- [ ] FAIR badges have gradient letters
- [ ] All interactive demos render (KnowledgeGraphDemo, 3D embeddings, embedding journey, DatabaseWithRestApi, HiRAGImplementationDetails)
- [ ] Background mesh gradient visible behind all sections
- [ ] Warm parchment / warm-parchment alternating backgrounds
- [ ] Section counters visible (01/10 through 10/10)
- [ ] Mobile responsive — dot nav hidden on small screens, sections still scroll
- [ ] No text contrast issues anywhere (all text readable on warm backgrounds)
- [ ] Existing i18n keys still work (no missing translations)

**Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: visual QA fixes for how-it-works redesign"
```

---

## Execution Notes

- **No new npm dependencies.** Everything uses existing framer-motion + Tailwind.
- **Existing interactive components preserved.** `KnowledgeGraphDemo`, `TimelineVisualization`, `EmbeddingsVisualization3D`, `EmbeddingJourneyUltra`, `EmbeddingsExplanation`, `DatabaseWithRestApi`, `HiRAGImplementationDetails` are kept unchanged — only wrapped in reveal animation containers and restyled with warm background classes.
- **All i18n keys already exist** in `learn.*` namespace. No new translation keys needed.
- **Task 12 is the heaviest** (~80% of the work). Tasks 1–11 create the building blocks; Task 12 assembles them.
- **The prototype** at `frontend/public/prototype-how-it-works.html` serves as the visual reference for every decision. When in doubt, match the prototype.
