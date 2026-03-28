# Book Reader — Paginated Mode for EleutherIA

**Date:** 2026-03-28
**Status:** Design approved

## Overview

A paginated "book mode" reader for EleutherIA's ancient text corpus (17k+ passages, Greek/Latin). Adds a Loeb-meets-Budé reading experience alongside the existing scroll-based `CanonicalTextReader`. Uses Pretext (`@chenglou/pretext`) for canvas-based text measurement and page layout, with DOM rendering.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Aesthetic direction | Between Loeb Classical Library and luxury edition (Budé) | Academic rigor + beautiful typography |
| Navigation | Classic pagination (arrows, page numbers) | Familiar, simple |
| Bilingual layout | Face-to-face by page (original left, translation right) | Loeb standard, most elegant |
| Bilingual sync | Pretext measures both languages, pages cover same passages | Prevents desynchronization |
| Bilingual availability | Only when translation data exists (`has_translation` flag) | No false promises |
| Page chrome | Running header, page number, marginal refs, progress bar, KG link | Full academic + digital experience |
| Monolingue mode | Toggle between scroll (existing) and paginated | Existing reader preserved |
| Mobile bilingual | Single-column paginated + Original/Translation toggle | Synchronized tabs, swipe for pages |
| Architecture | Hybrid: Pretext for measurement, DOM for rendering | CSS can't predict pages or sync columns; Pretext can |

## Architecture

### Component Structure

```
BookReader/
├── BookReaderPage.tsx          # Route: /texts/:textId/book
├── useBookPagination.ts        # Pretext prepare() + layout() → pages[]
├── usePageSync.ts              # Bilingual sync (same passages per spread)
├── BookSpread.tsx              # Double page (left original + right translation)
├── BookPage.tsx                # Single page (text + marginal refs + page number)
├── BookHeader.tsx              # Running header (title + author, small caps)
├── BookControls.tsx            # Navigation (arrows, page number, toggle scroll/paginated, font size)
├── BookProgress.tsx            # Progress bar + position in work
├── MobileBookReader.tsx        # Single-column paginated + Original/Translation toggle
└── KGPassageLink.tsx           # Discreet KG icon per passage
```

### Data Flow

```
useLazyPassages (existing, reused)
  → loads passages + translations (via ?include_translations=true)
    → useBookPagination
      → Pretext prepare(): measures each passage in target font/size
      → Pretext layout(): slices into fixed-height pages
      → Returns: Page[] with { pageNumber, passages[], startRef, endRef }
    → usePageSync (bilingual mode)
      → Aligns original and translated pages by passage
      → Inserts padding so each spread covers the same segment
```

## Pagination Engine (Pretext)

### Calibration

At mount, render one invisible passage in a hidden DOM element with exact styles (font-family, font-size, line-height, width). Measure real height vs. Pretext prediction. Store correction ratio and apply to all subsequent measurements. Compensates for `canvas.measureText()` vs. DOM rendering differences, especially for Greek diacritics.

### Page Configuration

```typescript
interface PageConfig {
  width: number;          // Text width (excluding ref margins)
  height: number;         // Text height (excluding header/footer)
  marginRef: number;      // Canonical ref column width
  fontSize: number;       // In px, extracted from CSS computed
  lineHeight: number;     // Ratio, extracted from CSS computed
  fontFamily: string;     // "Palatino Linotype", "Georgia", etc.
}
```

Dimensions calculated from viewport minus chrome (header, footer, margins, page number). On resize, recalculate — Pretext `layout()` is ~0.09ms/500 texts, so instantaneous.

### Page Data Model

```typescript
interface BookPage {
  pageNumber: number;
  passages: {
    passageId: string;
    canonicalRef: string;
    text: string;           // Full or partial (if split across pages)
    startOffset?: number;   // If passage overflows from previous page
    endOffset?: number;     // If passage continues on next page
    kgNodeCount: number;    // For KG icon (0 = no icon)
  }[];
}
```

Long passages can span 2+ pages. Pretext calculates exactly where to cut (at the last complete word that fits within remaining height).

### Bilingual Synchronization

For each passage, Pretext measures height in both languages. The page takes the max height of both. If the original is shorter, it is vertically centered in its space. Result: each spread covers exactly the same passages, no drift.

```
Page 4 left (Greek)      |  Page 5 right (French)
─────────────────────────|──────────────────────────
[3.1] ἐν ἀρχῇ ἦν...     |  [3.1] Au commencement...
      (space)            |        ...était Dieu.
[3.2] οὗτος ἦν ἐν...    |  [3.2] Il était au...
[3.3] πάντα δι'...       |  [3.3] Tout a été fait...
```

## Typography & Layout

### Fonts

- **Display/headers:** EB Garamond — small caps for running headers
- **Body text:** EB Garamond at 17px, line-height 1.75 — optimized for extended reading
- **Greek text:** Same font, italic — consistent with classical convention
- **Marginal refs:** EB Garamond at 11px, muted color
- **UI controls:** DM Sans (existing body font)

### Color Palette

- **Page background:** `#fdfbf7` (warm parchment)
- **App background:** `#1a1a1e` (dark surround — frames the pages)
- **Primary text:** `#3d3427` (warm dark brown)
- **Greek text:** `#2c2418` (slightly darker for emphasis)
- **Secondary/refs:** `#b8a88a` (muted gold-brown)
- **Accent:** `#d4a853` (Signal Gold — KG links, progress bar)
- **Spine shadow:** Gradient overlay at center of spread

### Page Chrome

1. **Running header:** Title (left) + author/book (right), small caps, 10px, separated by hairline
2. **Page number:** Centered bottom, 12px, letter-spaced
3. **Marginal refs:** Canonical references (1.1, 1.2) in outer margin, aligned with passage start
4. **Progress bar:** 2px bar below spread, shows position in work (book + chapter + percentage)
5. **KG link:** `⟁` icon per passage, visible on hover, links to `/visualizer?passage={id}`

### Font Size Control

3 presets accessible via `Aa` button in reader controls:
- **Small:** 14px body
- **Normal:** 17px body (default)
- **Large:** 20px body

Font size change triggers Pretext repagination (same as resize). Preference persisted in `localStorage`.

## Data & API

### Enriched Passage Endpoint

Add query parameter to existing endpoint:

```
GET /api/works/{workId}/passages?include_translations=true&limit=30&offset=0
```

### Response Shape

```typescript
interface PassageWithTranslation extends Passage {
  translation?: {
    text: string;
    language: string;     // 'fr', 'en', etc.
    source: 'scholarly' | 'ai_generated';
  };
  kg_node_count: number;  // For KG icon (0 = no icon)
}
```

### Caching

Reuse existing IndexedDB 7-day cache from `cachedApiClient`. Translations are immutable like original passages — same strategy.

### Bilingual Detection

The `has_translation` flag already exists on `ResearchGraphWork`. The "Bilingual mode" toggle only appears when `has_translation === true`.

## Mobile (< 900px)

### Layout

- Spread disappears → single-column paginated
- Reduced margins, slightly smaller font (15px instead of 17px)
- Running header simplified (title only, no author)

### Bilingual Toggle

- Two tabs at top: `Original` | `Traduction`
- Each view paginated independently but synchronized on same passage
- Switching tab shows same text segment
- Swipe left/right changes page (not tab — no confusion)

### Navigation

- Horizontal swipe to change page
- Tap left/right edges as fallback
- Progress bar always visible at bottom

### Breakpoints

- `≥ 900px`: spread double-page mode
- `< 900px`: single-page + bilingual toggle

No intermediate breakpoint — spread works from 900px upward thanks to Pretext dimensions adapting to viewport.

## Interactions & Shortcuts

### Keyboard (Desktop)

| Key | Action |
|---|---|
| `←` / `→` | Previous / next page |
| `Home` / `End` | First / last page |
| `g` then number | Go to page (Vim-style) |
| `t` | Toggle bilingual (if available) |
| `v` | Toggle scroll / paginated |
| `Esc` | Back to current reader |

### KG Links

- Hover passage → `⟁` icon appears
- Click → navigates to `/visualizer?passage={id}`
- No inline panel — don't break the reading experience

### Resize

- Pretext `layout()` recalculated on resize (debounce 150ms)
- Current page preserved: find first visible passage, navigate to its page after recalculation
- Desktop ↔ mobile transition is seamless

### Deep Linking

- URL: `/texts/:textId/book?page=42`
- Sharing URL restores exact page
- Canonical refs work too: `/texts/:textId/book?ref=1.3`

## Integration with Existing Reader

- `CanonicalTextReader` remains intact — no modifications
- New route: `/texts/:textId/book`
- Button in existing reader header: "Mode livre" → navigates to book mode at same passage
- Button in book mode: `Esc` or back button → returns to scroll reader at same passage
- Both readers share `useLazyPassages` and IndexedDB cache

## Dependencies

- `@chenglou/pretext` — text measurement and page layout (MIT, zero deps)
- No other new dependencies

## Out of Scope

- On-demand translation generation via LLM (future feature)
- Marginal annotations/scholies (architecture supports it, not implemented)
- Comparative reader (two works side by side)
- Linguistic analysis panel (lemma data in reader)
- Dark mode for pages (pages are always parchment; app surround is dark)
