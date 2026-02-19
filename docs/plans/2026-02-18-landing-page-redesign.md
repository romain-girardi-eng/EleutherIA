# Landing Page Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Strip the landing page to hero-only, create `/how-it-works` consolidating all tech pedagogy from `HomePage` and `AboutPage`, add "How it works" to the navbar.

**Architecture:** Move all educational content (8 sections from HomePage + Technical Details + HiRAGImplementationDetails from AboutPage) into a new `HowItWorksPage.tsx`. The landing page becomes hero-only. AboutPage loses its two tech sections.

**Tech Stack:** React 19, TypeScript, react-router-dom, react-i18next, framer-motion, lucide-react, Tailwind CSS

---

### Task 1: Create `HowItWorksPage.tsx`

**Files:**
- Create: `frontend/src/pages/HowItWorksPage.tsx`

No tests needed — this is a pure extraction/move (no logic changes).

**Step 1: Create the file**

Copy everything from `HomePage.tsx` EXCEPT the hero section JSX and the hero-only state/logic, then add the two tech sections from `AboutPage.tsx`.

The file structure:

```tsx
// Same imports as HomePage.tsx (all of them), PLUS:
import DatabaseWithRestApi from '../components/ui/database-with-rest-api';
import HiRAGImplementationDetails from '../components/HiRAGImplementationDetails';
import { Github } from 'lucide-react';
// Remove: HeroSection, MorphingParticles, FeatureCarousel, FeatureCardData
// Remove: Maximize2, Minimize2 (fullscreen icons, not needed)
// Keep: all other imports

// Animation variants - copy verbatim from HomePage.tsx:
const fadeInUp: Variants = { ... }
const staggerContainer: Variants = { ... }
const staggerItem: Variants = { ... }

export default function HowItWorksPage() {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState('overview');
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(true);
  // NO: isFullscreen, particleContainerRef, toggleFullscreen

  // Sections array - add 2 new entries for HiRAG:
  const sections = [
    { id: 'overview', label: t('learn.nav.overview'), icon: Globe },
    { id: 'knowledge-graph', label: t('learn.nav.knowledgeGraph'), icon: Network },
    { id: 'embeddings', label: t('learn.nav.embeddings'), icon: Brain },
    { id: 'graphrag', label: t('learn.nav.graphrag'), icon: Sparkles },
    { id: 'hybrid-search', label: t('learn.nav.hybridSearch'), icon: Search },
    { id: 'ancient-texts', label: t('learn.nav.ancientTexts'), icon: BookOpen },
    { id: 'fair', label: t('learn.nav.fair'), icon: CheckCircle2 },
    { id: 'glossary', label: t('learn.nav.glossary'), icon: BookMarked },
    { id: 'hirag', label: 'HiRAG Technology', icon: Cpu },
    { id: 'hirag-details', label: 'Implementation', icon: Code },
  ];

  const containerRef = useRef<HTMLDivElement>(null);

  // Same scroll listener useEffect as HomePage.tsx - copy verbatim
  // Same scrollToSection function - copy verbatim

  return (
    <div className="min-h-screen relative">
      {/* Aurora effect - copy verbatim from HomePage.tsx */}

      {/* Fixed Navigation Sidebar - copy verbatim from HomePage.tsx */}
      {/* BUT: add GitHub link badge in the sidebar footer area, above the "Try GraphRAG" CTA */}

      {/* Main Content */}
      <main ref={containerRef} className={`min-h-screen overflow-y-auto scroll-smooth transition-[margin] duration-300 ease-out relative z-10 pt-16 ${isMenuCollapsed ? 'lg:ml-[72px]' : 'lg:ml-64'}`}>

        {/* GitHub link header banner */}
        <div className="py-6 px-6 bg-white/80 backdrop-blur-sm border-b border-gray-100 text-center">
          <a
            href="https://github.com/romain-girardi-eng/EleutherIA"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2 bg-gray-900 text-white rounded-full text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            <Github className="w-4 h-4" />
            Open source on GitHub
          </a>
        </div>

        {/* Overview Section - copy verbatim from HomePage.tsx */}
        {/* Knowledge Graph Section - copy verbatim */}
        {/* Embeddings Section - copy verbatim */}
        {/* GraphRAG Section - copy verbatim */}
        {/* Hybrid Search Section - copy verbatim */}
        {/* Ancient Texts Section - copy verbatim */}
        {/* FAIR Section - copy verbatim */}
        {/* Glossary Section - copy verbatim */}

        {/* NEW: HiRAG Technology Section (from AboutPage Technical Details) */}
        <section id="hirag" className="py-20 px-6 bg-white/60 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <SectionHeader
              icon={<Cpu className="w-8 h-8" />}
              title="HiRAG Technology"
              subtitle="Hierarchical Retrieval-Augmented Generation — the AI architecture powering EleutherIA"
            />

            {/* DatabaseWithRestApi visualization */}
            <div className="flex flex-col items-center py-10">
              <div className="w-full max-w-[800px]">
                <DatabaseWithRestApi
                  className="h-[500px] max-w-[800px]"
                  circleText="API"
                  badgeTexts={{ first: "Question", second: "Context", third: "Synthesis", fourth: "Answer" }}
                  buttonTexts={{ first: "Knowledge Graph", second: "AI Model" }}
                  title="GraphRAG Pipeline: Database to AI-Generated Responses"
                  lightColor="#769687"
                />
              </div>
              <p className="text-sm text-gray-600 text-center mt-8 max-w-3xl leading-relaxed">
                The API allows the AI model to communicate with the Knowledge Graph database.
                When you ask a question, it retrieves relevant context from ancient sources and modern scholarship
                through a hierarchical retrieval process, which the AI then synthesizes into a scholarly answer.
              </p>
            </div>

            {/* HiRAG Technology Highlight - copy verbatim from AboutPage */}
            {/* Two-column Philological Work + Technical Infrastructure cards - copy verbatim from AboutPage */}
          </div>
        </section>

        {/* NEW: HiRAG Implementation Details Section */}
        <section id="hirag-details" className="py-20 px-6 bg-white/60 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <HiRAGImplementationDetails />
          </div>
        </section>

      </main>
    </div>
  );
}

// Helper components - copy ALL verbatim from HomePage.tsx:
// SectionHeader, StatCard, PillarCard, NodeTypeCard
// KnowledgeGraphDemo, TimelineVisualization, EmbeddingsExplanation, SemanticSpaceVisualization
// GraphRAGPipelineDemo, HybridSearchExplanation, SearchMethodCard
// AncientTextsShowcase, FAIRPrinciplesDisplay, GlossarySection
```

**Step 2: Verify the file compiles**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/.claude/worktrees/laughing-diffie/frontend
npm run build 2>&1 | head -50
```

Expected: No TypeScript errors related to `HowItWorksPage.tsx`.

**Step 3: Commit**

```bash
git add frontend/src/pages/HowItWorksPage.tsx
git commit -m "feat: create HowItWorksPage with consolidated tech pedagogy"
```

---

### Task 2: Register `/how-it-works` route in `App.tsx`

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Add lazy import**

After line 41 (`const HomePage = lazy(...)`), add:

```tsx
const HowItWorksPage = lazy(() => import('./pages/HowItWorksPage'));
```

**Step 2: Add to `getPageTitle`**

In the `routes` object (lines 46–58), add:

```tsx
'/how-it-works': 'How It Works',
```

**Step 3: Add route**

After line 338 (`<Route path="/" ...>`), add:

```tsx
<Route path="/how-it-works" element={<Suspense fallback={<PageLoadingFallback />}><HowItWorksPage /></Suspense>} />
```

**Step 4: Add desktop nav link**

After line 202 (`<NavLink to="/about">`), add:

```tsx
<NavLink to="/how-it-works">{t('nav.howItWorks')}</NavLink>
```

**Step 5: Add to mobile menu**

In the mobile menu array (around line 274), add:

```tsx
{ to: '/how-it-works', label: t('nav.howItWorks') },
```

Place it after `{ to: '/about', ... }`.

**Step 6: Verify dev server compiles**

```bash
cd frontend && npm run dev &
# Wait 5s, then check
curl -s http://localhost:5173/ | head -5
```

Expected: HTML response (Vite dev server running).

**Step 7: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: register /how-it-works route and nav link"
```

---

### Task 3: Add i18n keys for `nav.howItWorks`

**Files:**
- Modify: `frontend/src/i18n/locales/en.json`
- Modify: `frontend/src/i18n/locales/fr.json`
- Modify: `frontend/src/i18n/locales/de.json`
- Modify: `frontend/src/i18n/locales/it.json`
- Modify: `frontend/src/i18n/locales/el.json`

**Step 1: Add key to each locale**

In the `"nav"` object of each file, after `"about": "..."`, add:

- `en.json`: `"howItWorks": "How it works"`
- `fr.json`: `"howItWorks": "Comment ça marche"`
- `de.json`: `"howItWorks": "Wie es funktioniert"`
- `it.json`: `"howItWorks": "Come funziona"`
- `el.json`: `"howItWorks": "Πώς λειτουργεί"`

**Step 2: Commit**

```bash
git add frontend/src/i18n/locales/en.json frontend/src/i18n/locales/fr.json frontend/src/i18n/locales/de.json frontend/src/i18n/locales/it.json frontend/src/i18n/locales/el.json
git commit -m "feat: add nav.howItWorks i18n keys for all 5 locales"
```

---

### Task 4: Strip `HomePage.tsx` to hero-only

**Files:**
- Modify: `frontend/src/pages/HomePage.tsx`

**Step 1: Remove all non-hero state and logic**

Remove:
- `const [activeSection, setActiveSection] = useState('overview');` (line 43)
- `const [isMenuCollapsed, setIsMenuCollapsed] = useState(true);` (line 44)
- `const featureCards: FeatureCardData[] = [...]` (lines 69–110)
- `const sections = [...]` (lines 113–122)
- `const containerRef = useRef<HTMLDivElement>(null);` (line 123)
- The scroll listener `useEffect` (lines 126–149)
- `const scrollToSection = (...)` (lines 151–159)

**Step 2: Remove non-hero JSX**

In the `return`, remove:
- The entire sidebar `<nav>` (lines 183–253)
- The `<section id="quick-start">` FeatureCarousel section (lines 317–337)
- All 8 section elements (Overview through Glossary, lines 339–725)

Change `<main ref={containerRef} ...>` to just `<main>` (remove ref and margin classes).

**Step 3: Remove unused imports**

Remove these imports (no longer used in `HomePage.tsx`):
- From lucide: `Network, Search, BookOpen, ChevronRight, MessageSquare, Cpu, Layers, GitBranch, Sparkles, Globe, CheckCircle2, ArrowRight, Play, Pause, RotateCcw, PanelLeftClose, PanelLeft, BookMarked, Users, Languages, Quote, Target, Brain, Loader2`

Keep only:
- `useState, useRef, useEffect, useCallback` (useEffect still needed for fullscreen listener)
- `motion` from framer-motion (if aurora div uses it; otherwise remove too)
- `useTranslation`
- `Maximize2, Minimize2` (fullscreen toggle)
- `HeroSection, MorphingParticles`
- `Link` from react-router-dom

Remove:
- `FeatureCarousel, type FeatureCardData`
- `EmbeddingsVisualization3D` (direct import)
- `EmbeddingJourneyUltra` (lazy import)
- `Card, CardHeader, CardTitle, CardContent`
- Animation variants `fadeInUp`, `staggerContainer`, `staggerItem` (no longer used)
- `AnimatePresence` if not used in hero

Remove all helper components at the bottom of the file (lines 732+): `SectionHeader`, `StatCard`, `PillarCard`, `NodeTypeCard`, `KnowledgeGraphDemo`, `TimelineVisualization`, `EmbeddingsExplanation`, `SemanticSpaceVisualization`, `GraphRAGPipelineDemo`, `HybridSearchExplanation`, `SearchMethodCard`, `AncientTextsShowcase`, `FAIRPrinciplesDisplay`, `GlossarySection`.

**Step 4: Verify the file still renders the hero**

Visit `http://localhost:5173/` — should see only the hero (particles, title, aurora, fullscreen button).

**Step 5: Commit**

```bash
git add frontend/src/pages/HomePage.tsx
git commit -m "refactor: strip HomePage to hero-only"
```

---

### Task 5: Clean up `AboutPage.tsx`

**Files:**
- Modify: `frontend/src/pages/AboutPage.tsx`

**Step 1: Remove the "Technical Details" section**

Remove the entire `motion.div` block with `transition={{ delay: 0.4 }}` (lines 200–358). This includes:
- The `<h2>{t('about.implementationTitle')}</h2>` heading
- The `<DatabaseWithRestApi>` visualization
- The HiRAG Technology Highlight purple box
- The Philological Work and Technical Infrastructure two-column cards

**Step 2: Remove the "HiRAG Implementation Details" section**

Remove the entire `motion.div` block with `transition={{ delay: 0.5 }}` (lines 361–368). This contains only `<HiRAGImplementationDetails />`.

**Step 3: Remove unused imports**

Remove:
- `import DatabaseWithRestApi from '../components/ui/database-with-rest-api';` (line 3)
- `import HiRAGImplementationDetails from '../components/HiRAGImplementationDetails';` (line 4)

**Step 4: Adjust animation delays**

The "Open Source Info" section had `transition={{ delay: 0.6 }}`. Update it to `transition={{ delay: 0.4 }}` since two sections were removed.

**Step 5: Verify AboutPage renders correctly**

Visit `http://localhost:5173/about` — should show: header, About the Project, About the Author, Open Source info. No tech sections.

**Step 6: Commit**

```bash
git add frontend/src/pages/AboutPage.tsx
git commit -m "refactor: remove tech sections from AboutPage — moved to /how-it-works"
```

---

### Task 6: End-to-end verification

**Step 1: Verify landing page**

Visit `http://localhost:5173/` — should show ONLY:
- Aurora background
- Morphing particles
- Hero with title/subtitle
- Fullscreen button
- Contact info (DOI, license, GitHub)
- No sidebar, no carousel, no scrollable educational sections

**Step 2: Verify How It Works page**

Visit `http://localhost:5173/how-it-works` — should show:
- GitHub badge at top
- Left sidebar with 10 sections (including HiRAG Technology + Implementation)
- All 8 original learning sections intact
- HiRAG Technology section with DatabaseWithRestApi visualization
- HiRAGImplementationDetails expandable sections
- Footer visible at the bottom

**Step 3: Verify About page**

Visit `http://localhost:5173/about` — should show:
- Header with Typewriter
- About the Project
- About the Author (bio, credentials, social links)
- Open Source & FAIR Compliance (GitHub, DOI, CC BY 4.0)
- No "Technical Details" or "HiRAG Implementation Details" sections

**Step 4: Verify navbar**

Desktop: Check "How it works" link appears in top navbar and navigates correctly.
Mobile: Open hamburger menu, check "How it works" entry exists.

**Step 5: Verify language switching**

Switch language (e.g., to French) on `/how-it-works` — nav label becomes "Comment ça marche", section titles in sidebar update.

**Step 6: Run build**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/.claude/worktrees/laughing-diffie/frontend
npm run build 2>&1 | tail -20
```

Expected: Build completes with no errors. TypeScript errors would show here if any imports are broken.
