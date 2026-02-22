# Unified Parchment Redesign

**Date:** 2026-02-21
**Scope:** Visual polish of all pages except HomePage and KG Visualizer

## Design Brief

Extend the How It Works page design language to the entire site. Remove Aurora backgrounds everywhere. Move GraphRAG from dark to light. Keep typewriter animations. All body text in black/dark. Color accents allowed in headings for keyword emphasis (not systematic).

## Pages NOT Touched

- **HomePage** — no changes
- **KG Visualizer (CosmographPage full-screen)** — stays fully dark

## Global Design Tokens

### Backgrounds
- Page base: `bg-[#fffdf9]` (warm parchment) + `BackgroundMesh` dots variant at 0.04 opacity
- Card containers: GlassCard light variant — `bg-black/4 border-stone-200/80 backdrop-blur-sm rounded-2xl`
- No pure white or pure black backgrounds on content pages
- Remove ALL `AuroraBackground` usage from every page

### Typography
- h1/h2: `font-display` (Instrument Serif), `text-stone-800`
- Body text: `font-body` (DM Sans), `text-stone-800` (primary) / `text-stone-600` (secondary)
- No colored body text — only badges, icons, CTAs use color
- Colored keyword spans allowed in headings for emphasis (like How It Works)

### Accent Palette (cool to warm)
- `border-blue-200` -> `border-amber-200/60`
- `text-blue-600` -> `text-orange-600`
- `from-blue-50 to-indigo-50` -> `from-parchment-50 to-amber-50`
- ShineBorder colors: `["#f97316", "#ea580c", "#fdba74"]`

### Animations (extend, don't change)
- Framer Motion `whileInView` fade+slide from How It Works
- Custom easing `[0.22, 1, 0.36, 1]`
- Staggered children for all list/grid views
- `viewport={{ once: true }}`

## Page-by-Page Specification

### 1. Search Page (`SearchPage.tsx`)

**Remove:** `AuroraBackground` wrapper
**Add:** `bg-[#fffdf9]` + `BackgroundMesh` dots
**Search bar:** Keep ShineBorder, switch to warm orange gradient `["#f97316", "#ea580c", "#fdba74"]`
**Result cards:** `bg-parchment-100/70 border-amber-200/60 rounded-2xl` (replaces `bg-white border-neutral-200`)
**Keep:** Typewriter animation, stagger animations on results
**Typography:** Card titles -> `font-display`, h1 -> `font-display`

### 2. Database Page (`DatabasePage.tsx`)

**Remove:** `AuroraBackground`
**Add:** `bg-[#fffdf9]` + `BackgroundMesh` dots
**Stat cards:** `from-parchment-50 to-amber-50` (replaces blue/purple/green gradients)
**Stat borders:** warm amber (replaces `border-blue-200` etc.)
**Keep:** Typewriter animation
**Typography:** h1/h2 -> `font-display`

### 3. GraphRAG Page (dark -> light)

**Remove:** `AuroraBackground`, all `bg-[#020617]` dark backgrounds
**Chat panel:** `bg-white` -> `bg-[#fffdf9]`
**Right panel:** `bg-[#020617]` -> `bg-[#fffdf9]` with warm borders
**Passage reader:** Dark navy -> parchment light, `border-amber-200/40` dividers
- Highlighted passages: `bg-amber-100/40 border-l-4 border-amber-600`
- Text: `text-stone-800` (primary), `text-stone-600` (secondary)
**User messages:** `from-gray-900 to-gray-800` -> `from-stone-100 to-stone-50`
**Assistant messages:** Keep light, warm borders `border-amber-200`
**Cosmograph in GraphRAG:** Keep dark canvas (graph needs contrast)
**Keep:** Streaming animation, thinking panel, typewriter effects
**ThinkingProcessPanel:** ShineBorder colors -> warm palette `["#dcd7d0", "#c9bfb3", "#d4c9bb"]`

### 4. Ancient Works Listing (`AncientWorksListingPage.tsx`)

**Remove:** `AuroraBackground`
**Add:** Parchment base `bg-[#fffdf9]`
**Header gradient:** `from-gray-50 to-white` -> `from-parchment-100 to-parchment-50`
**Work cards:** `bg-parchment-100/60 border-amber-200/40` with `hover:border-orange-400 hover:shadow-md`
**Add:** Stagger animation on card grid (currently missing)
**Typography:** All headings -> `font-display`

### 5. Bibliography Page (`BibliographyPage.tsx`)

**Remove:** `AuroraBackground`
**Add:** Parchment base
**ShineBorder:** Warm orange gradient `["#f97316", "#ea580c", "#fdba74"]`
**Letter headings:** `text-blue-700` -> `text-orange-600`
**Filter inputs:** `border-gray-200` -> `border-amber-200`
**Entry backgrounds:** `bg-white` -> `bg-parchment-50/40`
**Typography:** h1/h2 -> `font-display`

### 6. About Page (`AboutPage.tsx`)

**Remove:** `AuroraBackground`
**Add:** Parchment base
**Gradient cards:** All cool-toned gradients -> warm amber/parchment variants
- `from-blue-50 to-indigo-50` -> `from-parchment-50 to-amber-50`
- `from-purple-50 to-pink-50` -> `from-amber-50 to-orange-50`
**Profile image border:** `border-white` -> `border-amber-200`
**Section backgrounds:** `bg-white/95` -> `bg-parchment-100/70`
**Typography:** h1/h3 -> `font-display`

### 7. Credits Page (`CreditsPage.tsx`)

**Remove:** `AuroraBackground`
**Add:** Parchment base
**All gradient cards:** Replace cool-toned color-coded sections with warm variants
- Use varying warm tones for differentiation: amber, orange, parchment, stone
**Section backgrounds:** `bg-white/95` -> `bg-parchment-100/70`
**Heading colors:** `text-blue-900` -> `text-stone-800`
**Typography:** h1/h2/h3 -> `font-display`

### 8. Navigation Bar (`Header.tsx`)

**Same structure.** Restyle:
- Background -> parchment tones
- Text -> `text-stone-800`
- Active/hover states -> `text-orange-600`

### 9. How It Works Polish (`HowItWorksPage.tsx`)

**Section 6 (Architecture/HiRAG):**
- Replace teal/cyan gradient cards with warm palette
- `from-teal-50 to-cyan-50 border-teal-200` -> `from-parchment-50 to-amber-50 border-amber-200`
- Improve visual hierarchy, consistent with other sections

**Section 7 (Search methods):**
- Same warm palette treatment
- Ensure consistency with polished sections

**Compare cards (Section 2):**
- Body text: red/green text -> `text-stone-800`
- Keep red/green for badges and icons only (label tags like "BEFORE"/"AFTER")
- Metric numbers can keep semantic color but body descriptions must be dark

**Keep:** Colored keyword spans in section headings, AuroraStrip transitions, scroll-snap behavior

## Tasteful Additions

- Subtle warm gradient dividers between page sections (inspired by AuroraStrip, more minimal)
- Micro-interactions on cards: slight `hover:scale-[1.01]` with `hover:shadow-lg` transition
- Loading states: AI loader in parchment/amber tones instead of default
