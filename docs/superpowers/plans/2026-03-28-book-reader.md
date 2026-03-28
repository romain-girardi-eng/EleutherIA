# Book Reader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paginated "book mode" reader to EleutherIA with Loeb-style bilingual face-to-face layout, Pretext-powered pagination, and mobile support.

**Architecture:** Hybrid approach — Pretext (`@chenglou/pretext`) measures text and calculates page breaks via canvas, DOM renders the pages. New route `/texts/:textId/book` alongside existing scroll reader. Backend extended with `include_translations` param to join KG translation nodes.

**Tech Stack:** React 19, TypeScript, Pretext, Tailwind CSS, EB Garamond (Google Fonts), Vite, FastAPI (backend)

**Spec:** `docs/superpowers/specs/2026-03-28-book-reader-design.md`

---

## File Structure

### New Files (Frontend)

| File | Responsibility |
|---|---|
| `src/components/book-reader/BookReaderPage.tsx` | Page component for `/texts/:textId/book` route |
| `src/components/book-reader/useBookPagination.ts` | Hook: Pretext prepare/layout → `BookPage[]` |
| `src/components/book-reader/usePageSync.ts` | Hook: bilingual page synchronization |
| `src/components/book-reader/BookSpread.tsx` | Double-page spread (left original + right translation) |
| `src/components/book-reader/BookPage.tsx` | Single page rendering (text + refs + page number) |
| `src/components/book-reader/BookHeader.tsx` | Running header (title + author, small caps) |
| `src/components/book-reader/BookControls.tsx` | Navigation arrows, page input, toggles, font size |
| `src/components/book-reader/BookProgress.tsx` | Progress bar + position in work |
| `src/components/book-reader/MobileBookReader.tsx` | Mobile: single-column + Original/Translation toggle |
| `src/components/book-reader/KGPassageLink.tsx` | Hover KG icon per passage |
| `src/components/book-reader/types.ts` | Shared types for book reader |
| `src/components/book-reader/useCalibration.ts` | Hook: Pretext↔DOM calibration ratio |
| `src/hooks/useSwipeNavigation.ts` | Hook: horizontal swipe gesture detection |

### Modified Files

| File | Change |
|---|---|
| `src/App.tsx:405` | Add route `/texts/:textId/book` → `BookReaderPage` |
| `src/pages/CanonicalTextReader.tsx:~260` | Add "Mode livre" button in header |
| `src/hooks/useLazyPassages.ts:17-25` | Extend `Passage` interface with optional `translation` |
| `src/api/cachedClient.ts:128` | Add `include_translations` option to `getWorkPassages` |
| `tailwind.config.js:132` | Add `garamond` font family |
| `index.html` or `index.css` | Import EB Garamond from Google Fonts |

### Backend

| File | Change |
|---|---|
| `database/src/eleutheria_database/api/works.py:103-147` | Add `include_translations` query param, LEFT JOIN KG translation nodes |

---

## Task 1: Install Pretext + EB Garamond font

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/tailwind.config.js:132-185`
- Modify: `frontend/index.html` (or `frontend/src/index.css`)

- [ ] **Step 1: Install Pretext**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npm install @chenglou/pretext
```

- [ ] **Step 2: Add EB Garamond Google Font import**

In `frontend/index.html`, add in the `<head>`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">
```

- [ ] **Step 3: Add garamond to Tailwind font config**

In `frontend/tailwind.config.js`, add a new `garamond` entry in the `fontFamily` section (after the `ancient` entry):

```javascript
garamond: [
  '"EB Garamond"',
  '"Palatino Linotype"',
  '"Book Antiqua"',
  'Palatino',
  'Georgia',
  'serif',
],
```

- [ ] **Step 4: Verify font loads**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/tailwind.config.js frontend/index.html
git commit -m "feat(reader): install pretext and add EB Garamond font"
```

---

## Task 2: Shared types

**Files:**
- Create: `frontend/src/components/book-reader/types.ts`

- [ ] **Step 1: Create types file**

```typescript
export interface PageConfig {
  /** Text area width in px (excluding ref margin) */
  width: number;
  /** Text area height in px (excluding header/footer) */
  height: number;
  /** Width of canonical ref margin column in px */
  marginRef: number;
  /** Body font size in px */
  fontSize: number;
  /** Line-height ratio */
  lineHeight: number;
  /** CSS font-family string for Pretext canvas measurement */
  fontFamily: string;
}

export interface PagePassage {
  passageId: string;
  canonicalRef: string;
  /** Full text, or partial if split across pages */
  text: string;
  /** Character offset if passage continues from previous page */
  startOffset?: number;
  /** Character offset if passage continues on next page */
  endOffset?: number;
  /** Number of KG nodes linked to this passage (0 = no icon) */
  kgNodeCount: number;
}

export interface BookPage {
  pageNumber: number;
  passages: PagePassage[];
}

export interface BookSpreadData {
  /** Left page (original language) */
  left: BookPage;
  /** Right page (translation) */
  right: BookPage;
}

export type FontSizePreset = 'small' | 'normal' | 'large';

export const FONT_SIZE_MAP: Record<FontSizePreset, number> = {
  small: 14,
  normal: 17,
  large: 20,
};

export const MOBILE_BREAKPOINT = 900;
```

- [ ] **Step 2: Verify types compile**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npx tsc --noEmit --pretty
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/book-reader/types.ts
git commit -m "feat(reader): add book reader shared types"
```

---

## Task 3: Backend — add translations to passages endpoint

**Files:**
- Modify: `database/src/eleutheria_database/api/works.py:103-147`

- [ ] **Step 1: Add `include_translations` param and LEFT JOIN**

Replace the `list_passages` function in `database/src/eleutheria_database/api/works.py` (lines 103-147):

```python
@router.get("/works/{work_id}/passages")
async def list_passages(
    work_id: UUID,
    db: Annotated[DatabaseService, Depends(get_db)],
    book: str | None = Query(None, description="Filter by book"),
    chapter: str | None = Query(None, description="Filter by chapter"),
    include_translations: bool = Query(False, description="Include KG translation nodes"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """
    List passages for a specific work.

    Returns paginated passages in sequence order.
    When include_translations=true, joins KG translation nodes via
    passage_citation → kg_node translation_of edges.
    """
    conditions = ["p.work_id = $1"]
    params: list = [work_id]
    param_count = 1

    if book:
        param_count += 1
        conditions.append(f"p.book = ${param_count}")
        params.append(book)

    if chapter:
        param_count += 1
        conditions.append(f"p.chapter = ${param_count}")
        params.append(chapter)

    where_clause = " AND ".join(conditions)

    param_count += 1
    limit_param = param_count
    param_count += 1
    offset_param = param_count
    params.extend([limit, offset])

    if include_translations:
        sql = f"""
        SELECT
            p.*,
            tn.description AS translation_text,
            CASE
                WHEN tn.node_id IS NOT NULL THEN 'en'
                ELSE NULL
            END AS translation_language,
            CASE
                WHEN tn.node_id LIKE '%_ai_%' THEN 'ai_generated'
                WHEN tn.node_id IS NOT NULL THEN 'scholarly'
                ELSE NULL
            END AS translation_source,
            COALESCE(kg_count.cnt, 0) AS kg_node_count
        FROM free_will.passages p
        LEFT JOIN free_will.passage_citations pc ON p.passage_id = pc.passage_id
        LEFT JOIN free_will.kg_edges te
            ON te.source_id = pc.kg_node_id || '_en'
            AND te.relation = 'translation_of'
        LEFT JOIN free_will.kg_nodes tn
            ON tn.node_id = te.source_id
        LEFT JOIN LATERAL (
            SELECT COUNT(DISTINCT pc2.kg_node_id) AS cnt
            FROM free_will.passage_citations pc2
            WHERE pc2.passage_id = p.passage_id
        ) kg_count ON true
        WHERE {where_clause}
        ORDER BY p.sequence_number
        LIMIT ${limit_param} OFFSET ${offset_param}
        """
    else:
        sql = f"""
        SELECT p.*
        FROM free_will.passages p
        WHERE {where_clause}
        ORDER BY p.sequence_number
        LIMIT ${limit_param} OFFSET ${offset_param}
        """

    return await db.fetch(sql, *params)
```

- [ ] **Step 2: Test the endpoint manually**

```bash
cd /Users/romaingirardi/Projects/EleutherIA
# Start the backend if not running, then:
curl -s "http://localhost:8000/api/works/<any_work_id>/passages?limit=3&include_translations=true" | python3 -m json.tool | head -40
```

Expected: Passages with `translation_text`, `translation_language`, `translation_source`, `kg_node_count` fields (null when no translation exists).

- [ ] **Step 3: Commit**

```bash
git add database/src/eleutheria_database/api/works.py
git commit -m "feat(api): add include_translations param to passages endpoint"
```

---

## Task 4: Frontend — extend passage types and API client

**Files:**
- Modify: `frontend/src/hooks/useLazyPassages.ts:17-25`
- Modify: `frontend/src/api/cachedClient.ts`

- [ ] **Step 1: Extend Passage interface in useLazyPassages.ts**

In `frontend/src/hooks/useLazyPassages.ts`, replace the `Passage` interface (lines 17-25):

```typescript
interface Passage {
  passage_id: string;
  canonical_ref: string;
  cts_urn: string | null;
  sequence_number: number;
  text_content: string;
  char_length: number;
  citation_hierarchy?: Record<string, unknown>;
  translation_text?: string | null;
  translation_language?: string | null;
  translation_source?: 'scholarly' | 'ai_generated' | null;
  kg_node_count?: number;
}
```

- [ ] **Step 2: Add `include_translations` to cachedClient**

In `frontend/src/api/cachedClient.ts`, find the `getWorkPassages` method and add the option. The method signature should accept `includeTranslations`:

```typescript
async getWorkPassages(
  workId: string,
  options?: {
    offset?: number;
    limit?: number;
    forceRefresh?: boolean;
    includeTranslations?: boolean;
  }
): Promise<PassagesResponse>
```

And in the API call URL, append `&include_translations=true` when the option is set. Find where the URL is built and add:

```typescript
const translationsParam = options?.includeTranslations ? '&include_translations=true' : '';
// Append to the fetch URL
```

- [ ] **Step 3: Verify build**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npx tsc --noEmit --pretty
```

Expected: No type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useLazyPassages.ts frontend/src/api/cachedClient.ts
git commit -m "feat(reader): extend passage types with translation and KG fields"
```

---

## Task 5: Calibration hook

**Files:**
- Create: `frontend/src/components/book-reader/useCalibration.ts`

- [ ] **Step 1: Create calibration hook**

```typescript
import { useCallback, useRef, useState } from 'react';
import { prepare } from '@chenglou/pretext';
import type { PageConfig } from './types';

interface CalibrationResult {
  /** Ratio: DOM measured height / Pretext predicted height */
  correctionRatio: number;
  /** Whether calibration has been performed */
  calibrated: boolean;
}

/**
 * Measures a sample text in both DOM and Pretext canvas,
 * then returns a correction ratio to compensate for differences
 * (especially with Greek diacritics).
 */
export function useCalibration(config: PageConfig): CalibrationResult & {
  calibrate: (sampleText: string) => void;
  hiddenRef: React.RefCallback<HTMLDivElement>;
} {
  const [result, setResult] = useState<CalibrationResult>({
    correctionRatio: 1,
    calibrated: false,
  });
  const sampleTextRef = useRef<string>('');
  const hiddenElRef = useRef<HTMLDivElement | null>(null);

  const hiddenRef = useCallback(
    (node: HTMLDivElement | null) => {
      hiddenElRef.current = node;
      if (node && sampleTextRef.current) {
        performCalibration(node, sampleTextRef.current);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [config.fontSize, config.lineHeight, config.fontFamily, config.width]
  );

  const performCalibration = useCallback(
    (el: HTMLDivElement, text: string) => {
      // Measure DOM height
      el.style.cssText = `
        position: absolute;
        visibility: hidden;
        width: ${config.width}px;
        font-family: ${config.fontFamily};
        font-size: ${config.fontSize}px;
        line-height: ${config.lineHeight};
        white-space: pre-wrap;
        word-wrap: break-word;
      `;
      el.textContent = text;
      const domHeight = el.getBoundingClientRect().height;

      // Measure with Pretext
      const prepared = prepare(text, {
        font: `${config.fontSize}px ${config.fontFamily}`,
        width: config.width,
        lineHeight: config.fontSize * config.lineHeight,
      });
      const pretextHeight = prepared.lines.length * config.fontSize * config.lineHeight;

      const ratio = pretextHeight > 0 ? domHeight / pretextHeight : 1;
      setResult({ correctionRatio: ratio, calibrated: true });
    },
    [config.width, config.fontSize, config.lineHeight, config.fontFamily]
  );

  const calibrate = useCallback(
    (sampleText: string) => {
      sampleTextRef.current = sampleText;
      if (hiddenElRef.current) {
        performCalibration(hiddenElRef.current, sampleText);
      }
    },
    [performCalibration]
  );

  return { ...result, calibrate, hiddenRef };
}
```

- [ ] **Step 2: Verify types compile**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npx tsc --noEmit --pretty
```

Expected: No errors. (Note: `prepare` API may need adjustment once we see the actual Pretext exports — verify against `@chenglou/pretext` types after install.)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/book-reader/useCalibration.ts
git commit -m "feat(reader): add Pretext calibration hook"
```

---

## Task 6: Pagination hook (useBookPagination)

**Files:**
- Create: `frontend/src/components/book-reader/useBookPagination.ts`

- [ ] **Step 1: Create pagination hook**

```typescript
import { useMemo } from 'react';
import { prepare } from '@chenglou/pretext';
import type { BookPage, PageConfig, PagePassage } from './types';

interface PaginationInput {
  passages: {
    passage_id: string;
    canonical_ref: string;
    text_content: string;
    kg_node_count?: number;
  }[];
  config: PageConfig;
  correctionRatio: number;
}

interface PaginationResult {
  pages: BookPage[];
  totalPages: number;
}

/**
 * Takes a list of passages and a page config, uses Pretext to measure
 * each passage, then distributes them across fixed-height pages.
 */
export function useBookPagination({
  passages,
  config,
  correctionRatio,
}: PaginationInput): PaginationResult {
  return useMemo(() => {
    if (passages.length === 0 || config.height <= 0 || config.width <= 0) {
      return { pages: [], totalPages: 0 };
    }

    const fontString = `${config.fontSize}px ${config.fontFamily}`;
    const lineHeightPx = config.fontSize * config.lineHeight;
    const pageHeight = config.height;

    // Measure all passages
    const measured = passages.map((p) => {
      const prepared = prepare(p.text_content, {
        font: fontString,
        width: config.width,
        lineHeight: lineHeightPx,
      });
      const rawHeight = prepared.lines.length * lineHeightPx;
      return {
        ...p,
        measuredHeight: rawHeight * correctionRatio,
        lineCount: prepared.lines.length,
        lines: prepared.lines,
      };
    });

    // Distribute passages across pages
    const pages: BookPage[] = [];
    let currentPage: PagePassage[] = [];
    let currentHeight = 0;
    let pageNumber = 1;
    const passageGap = lineHeightPx * 1.5; // Gap between passages

    for (const passage of measured) {
      const neededHeight = passage.measuredHeight + (currentPage.length > 0 ? passageGap : 0);

      if (currentHeight + neededHeight <= pageHeight || currentPage.length === 0) {
        // Passage fits on current page (or it's the first passage on a page)
        currentPage.push({
          passageId: passage.passage_id,
          canonicalRef: passage.canonical_ref,
          text: passage.text_content,
          kgNodeCount: passage.kg_node_count ?? 0,
        });
        currentHeight += neededHeight;
      } else {
        // Start new page
        pages.push({ pageNumber, passages: currentPage });
        pageNumber++;
        currentPage = [
          {
            passageId: passage.passage_id,
            canonicalRef: passage.canonical_ref,
            text: passage.text_content,
            kgNodeCount: passage.kg_node_count ?? 0,
          },
        ];
        currentHeight = passage.measuredHeight;
      }
    }

    // Push last page
    if (currentPage.length > 0) {
      pages.push({ pageNumber, passages: currentPage });
    }

    return { pages, totalPages: pages.length };
  }, [passages, config, correctionRatio]);
}
```

- [ ] **Step 2: Verify types compile**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npx tsc --noEmit --pretty
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/book-reader/useBookPagination.ts
git commit -m "feat(reader): add Pretext-powered pagination hook"
```

---

## Task 7: Bilingual sync hook (usePageSync)

**Files:**
- Create: `frontend/src/components/book-reader/usePageSync.ts`

- [ ] **Step 1: Create sync hook**

```typescript
import { useMemo } from 'react';
import type { BookPage, BookSpreadData } from './types';

interface PageSyncInput {
  originalPages: BookPage[];
  translationPages: BookPage[];
}

/**
 * Aligns original and translation pages so each spread
 * covers the same passages. When one side has more pages
 * for the same content, the other side gets a partial/padded page.
 */
export function usePageSync({
  originalPages,
  translationPages,
}: PageSyncInput): BookSpreadData[] {
  return useMemo(() => {
    if (originalPages.length === 0) return [];
    if (translationPages.length === 0) {
      // No translation — return original pages as left-only spreads
      return originalPages.map((page) => ({
        left: page,
        right: { pageNumber: page.pageNumber, passages: [] },
      }));
    }

    const spreads: BookSpreadData[] = [];
    let origIdx = 0;
    let transIdx = 0;
    let spreadNumber = 0;

    while (origIdx < originalPages.length || transIdx < translationPages.length) {
      spreadNumber++;
      const leftPageNum = spreadNumber * 2;
      const rightPageNum = leftPageNum + 1;

      const left: BookPage = origIdx < originalPages.length
        ? { ...originalPages[origIdx], pageNumber: leftPageNum }
        : { pageNumber: leftPageNum, passages: [] };

      const right: BookPage = transIdx < translationPages.length
        ? { ...translationPages[transIdx], pageNumber: rightPageNum }
        : { pageNumber: rightPageNum, passages: [] };

      spreads.push({ left, right });
      origIdx++;
      transIdx++;
    }

    return spreads;
  }, [originalPages, translationPages]);
}
```

- [ ] **Step 2: Verify types compile**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npx tsc --noEmit --pretty
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/book-reader/usePageSync.ts
git commit -m "feat(reader): add bilingual page sync hook"
```

---

## Task 8: KGPassageLink component

**Files:**
- Create: `frontend/src/components/book-reader/KGPassageLink.tsx`

- [ ] **Step 1: Create component**

```tsx
import { Link } from 'react-router-dom';

interface KGPassageLinkProps {
  passageId: string;
  nodeCount: number;
}

export function KGPassageLink({ passageId, nodeCount }: KGPassageLinkProps) {
  if (nodeCount === 0) return null;

  return (
    <Link
      to={`/visualizer?passage=${passageId}`}
      className="absolute -right-2 top-0.5 w-[18px] h-[18px] rounded-full border border-amber-600/25 flex items-center justify-center text-[9px] text-amber-600 opacity-0 group-hover:opacity-60 hover:!opacity-100 hover:bg-amber-600/10 transition-opacity"
      title={`${nodeCount} nœud${nodeCount > 1 ? 's' : ''} lié${nodeCount > 1 ? 's' : ''}`}
    >
      ⟁
    </Link>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/book-reader/KGPassageLink.tsx
git commit -m "feat(reader): add KG passage link component"
```

---

## Task 9: BookHeader component

**Files:**
- Create: `frontend/src/components/book-reader/BookHeader.tsx`

- [ ] **Step 1: Create component**

```tsx
interface BookHeaderProps {
  leftText: string;
  rightText: string;
}

export function BookHeader({ leftText, rightText }: BookHeaderProps) {
  return (
    <div className="flex justify-between font-garamond text-[10px] tracking-[2px] uppercase text-stone-400 mb-7 pb-2 border-b border-stone-900/8">
      <span>{leftText}</span>
      <span>{rightText}</span>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/book-reader/BookHeader.tsx
git commit -m "feat(reader): add book running header component"
```

---

## Task 10: BookPage component

**Files:**
- Create: `frontend/src/components/book-reader/BookPage.tsx`

- [ ] **Step 1: Create component**

```tsx
import { BookHeader } from './BookHeader';
import { KGPassageLink } from './KGPassageLink';
import type { BookPage as BookPageData } from './types';

interface BookPageProps {
  page: BookPageData;
  headerLeft: string;
  headerRight: string;
  isGreek?: boolean;
  langLabel?: string;
  fontSize: number;
  side?: 'left' | 'right' | 'single';
}

export function BookPage({
  page,
  headerLeft,
  headerRight,
  isGreek = false,
  langLabel,
  fontSize,
  side = 'single',
}: BookPageProps) {
  const sideClasses =
    side === 'left'
      ? 'pr-8 border-r border-stone-900/4'
      : side === 'right'
        ? 'pl-8'
        : '';

  return (
    <div className={`flex-1 p-10 min-h-[560px] flex flex-col text-stone-800 ${sideClasses}`}>
      <BookHeader leftText={headerLeft} rightText={headerRight} />

      {langLabel && (
        <div className="font-sans text-[9px] tracking-[1.5px] uppercase text-stone-400 mb-5">
          {langLabel}
        </div>
      )}

      <div className="flex-1">
        {page.passages.map((passage) => (
          <div key={passage.passageId} className="group relative flex gap-4 mb-6">
            <div className="font-garamond text-[11px] text-stone-400 min-w-[28px] text-right pt-[3px] shrink-0">
              {passage.canonicalRef}
            </div>
            <div
              className={`font-garamond leading-[1.75] text-stone-700 flex-1 ${isGreek ? 'italic text-stone-800' : ''}`}
              style={{ fontSize: `${fontSize}px` }}
            >
              {passage.text}
            </div>
            <KGPassageLink passageId={passage.passageId} nodeCount={passage.kgNodeCount} />
          </div>
        ))}
      </div>

      <div className="mt-auto text-center font-garamond text-xs text-stone-400 pt-5 tracking-[1px]">
        {page.pageNumber}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/book-reader/BookPage.tsx
git commit -m "feat(reader): add book page rendering component"
```

---

## Task 11: BookSpread component

**Files:**
- Create: `frontend/src/components/book-reader/BookSpread.tsx`

- [ ] **Step 1: Create component**

```tsx
import { BookPage } from './BookPage';
import type { BookSpreadData } from './types';

interface BookSpreadProps {
  spread: BookSpreadData;
  title: string;
  author: string;
  originalLanguage: string;
  translationLanguage: string;
  fontSize: number;
}

const LANG_LABELS: Record<string, string> = {
  grc: 'Grec ancien',
  lat: 'Latin',
  en: 'English',
  fr: 'Français',
};

export function BookSpread({
  spread,
  title,
  author,
  originalLanguage,
  translationLanguage,
  fontSize,
}: BookSpreadProps) {
  const isGreek = originalLanguage === 'grc';

  return (
    <div className="flex bg-[#fdfbf7] rounded-sm shadow-[0_1px_3px_rgba(0,0,0,0.3),0_8px_24px_rgba(0,0,0,0.25)] overflow-hidden relative">
      {/* Spine shadow */}
      <div className="absolute left-1/2 top-0 bottom-0 w-6 -translate-x-1/2 bg-gradient-to-r from-transparent via-black/[0.07] to-transparent pointer-events-none z-10" />

      <BookPage
        page={spread.left}
        headerLeft={title}
        headerRight={author}
        isGreek={isGreek}
        langLabel={LANG_LABELS[originalLanguage] ?? originalLanguage}
        fontSize={fontSize}
        side="left"
      />
      <BookPage
        page={spread.right}
        headerLeft={LANG_LABELS[translationLanguage] ?? translationLanguage}
        headerRight={`Livre ${spread.left.passages[0]?.canonicalRef.split('.')[0] ?? ''}`}
        isGreek={false}
        langLabel={LANG_LABELS[translationLanguage] ?? translationLanguage}
        fontSize={fontSize}
        side="right"
      />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/book-reader/BookSpread.tsx
git commit -m "feat(reader): add book spread (double-page) component"
```

---

## Task 12: BookProgress component

**Files:**
- Create: `frontend/src/components/book-reader/BookProgress.tsx`

- [ ] **Step 1: Create component**

```tsx
interface BookProgressProps {
  currentPage: number;
  totalPages: number;
  currentRef?: string;
}

export function BookProgress({ currentPage, totalPages, currentRef }: BookProgressProps) {
  const percentage = totalPages > 0 ? Math.round((currentPage / totalPages) * 100) : 0;

  return (
    <div className="w-full max-w-[920px] mx-auto mb-10">
      <div className="h-0.5 bg-white/[0.06] rounded-sm overflow-hidden mb-1.5">
        <div
          className="h-full bg-gradient-to-r from-amber-600 to-amber-700 rounded-sm transition-[width] duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] opacity-35">
        <span>{currentRef ?? ''}</span>
        <span>
          Pages {currentPage}–{Math.min(currentPage + 1, totalPages)} / {totalPages}
        </span>
        <span>{percentage} %</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/book-reader/BookProgress.tsx
git commit -m "feat(reader): add book progress bar component"
```

---

## Task 13: BookControls component

**Files:**
- Create: `frontend/src/components/book-reader/BookControls.tsx`

- [ ] **Step 1: Create component**

```tsx
import { ChevronLeft, ChevronRight, Type, Columns2, AlignJustify } from 'lucide-react';
import type { FontSizePreset } from './types';
import { FONT_SIZE_MAP } from './types';

interface BookControlsProps {
  currentPage: number;
  totalPages: number;
  onPrevious: () => void;
  onNext: () => void;
  onGoToPage: (page: number) => void;
  fontSize: FontSizePreset;
  onFontSizeChange: (size: FontSizePreset) => void;
  isBilingual: boolean;
  hasBilingual: boolean;
  onToggleBilingual: () => void;
  isPaginated: boolean;
  onToggleMode: () => void;
}

const FONT_PRESETS: FontSizePreset[] = ['small', 'normal', 'large'];

export function BookControls({
  currentPage,
  totalPages,
  onPrevious,
  onNext,
  onGoToPage,
  fontSize,
  onFontSizeChange,
  isBilingual,
  hasBilingual,
  onToggleBilingual,
  isPaginated,
  onToggleMode,
}: BookControlsProps) {
  const nextFontSize = () => {
    const idx = FONT_PRESETS.indexOf(fontSize);
    onFontSizeChange(FONT_PRESETS[(idx + 1) % FONT_PRESETS.length]);
  };

  return (
    <div className="flex items-center justify-center gap-8 mb-12">
      <button
        onClick={onPrevious}
        disabled={currentPage <= 1}
        className="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center text-white/80 hover:border-amber-600/40 hover:text-amber-600 transition disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ChevronLeft size={18} />
      </button>

      <span className="font-garamond text-sm opacity-50 tracking-[1px] tabular-nums">
        {currentPage}–{Math.min(currentPage + 1, totalPages)} sur {totalPages}
      </span>

      <button
        onClick={onNext}
        disabled={currentPage >= totalPages}
        className="w-10 h-10 rounded-full border border-white/10 flex items-center justify-center text-white/80 hover:border-amber-600/40 hover:text-amber-600 transition disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ChevronRight size={18} />
      </button>

      <div className="w-px h-6 bg-white/10" />

      {/* Font size */}
      <button
        onClick={nextFontSize}
        className="flex items-center gap-1.5 text-xs opacity-50 hover:opacity-80 transition"
        title={`Taille : ${FONT_SIZE_MAP[fontSize]}px`}
      >
        <Type size={14} />
        <span className="uppercase tracking-wider">{fontSize === 'small' ? 'P' : fontSize === 'normal' ? 'M' : 'G'}</span>
      </button>

      {/* Toggle bilingual */}
      {hasBilingual && (
        <button
          onClick={onToggleBilingual}
          className={`flex items-center gap-1.5 text-xs transition ${isBilingual ? 'text-amber-600 opacity-80' : 'opacity-50 hover:opacity-80'}`}
          title={isBilingual ? 'Mode monolingue' : 'Mode bilingue'}
        >
          <Columns2 size={14} />
        </button>
      )}

      {/* Toggle paginated/scroll */}
      <button
        onClick={onToggleMode}
        className="flex items-center gap-1.5 text-xs opacity-50 hover:opacity-80 transition"
        title={isPaginated ? 'Mode scroll' : 'Mode livre'}
      >
        <AlignJustify size={14} />
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/book-reader/BookControls.tsx
git commit -m "feat(reader): add book controls (nav, font size, toggles)"
```

---

## Task 14: Swipe navigation hook

**Files:**
- Create: `frontend/src/hooks/useSwipeNavigation.ts`

- [ ] **Step 1: Create hook**

```typescript
import { useCallback, useRef } from 'react';

interface SwipeOptions {
  onSwipeLeft: () => void;
  onSwipeRight: () => void;
  threshold?: number;
}

export function useSwipeNavigation({
  onSwipeLeft,
  onSwipeRight,
  threshold = 50,
}: SwipeOptions) {
  const startX = useRef(0);
  const startY = useRef(0);

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    startX.current = e.touches[0].clientX;
    startY.current = e.touches[0].clientY;
  }, []);

  const onTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      const deltaX = e.changedTouches[0].clientX - startX.current;
      const deltaY = e.changedTouches[0].clientY - startY.current;

      // Only trigger if horizontal swipe dominates
      if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > threshold) {
        if (deltaX > 0) {
          onSwipeRight();
        } else {
          onSwipeLeft();
        }
      }
    },
    [onSwipeLeft, onSwipeRight, threshold]
  );

  return { onTouchStart, onTouchEnd };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useSwipeNavigation.ts
git commit -m "feat(reader): add swipe navigation hook"
```

---

## Task 15: MobileBookReader component

**Files:**
- Create: `frontend/src/components/book-reader/MobileBookReader.tsx`

- [ ] **Step 1: Create component**

```tsx
import { useState } from 'react';
import { BookPage } from './BookPage';
import { useSwipeNavigation } from '../../hooks/useSwipeNavigation';
import type { BookPage as BookPageData } from './types';

interface MobileBookReaderProps {
  originalPages: BookPageData[];
  translationPages: BookPageData[];
  currentPage: number;
  onPageChange: (page: number) => void;
  title: string;
  author: string;
  originalLanguage: string;
  fontSize: number;
  hasBilingual: boolean;
}

export function MobileBookReader({
  originalPages,
  translationPages,
  currentPage,
  onPageChange,
  title,
  author,
  originalLanguage,
  fontSize,
  hasBilingual,
}: MobileBookReaderProps) {
  const [activeTab, setActiveTab] = useState<'original' | 'translation'>('original');
  const pages = activeTab === 'original' ? originalPages : translationPages;
  const page = pages[currentPage - 1];
  const isGreek = originalLanguage === 'grc' && activeTab === 'original';

  const swipeHandlers = useSwipeNavigation({
    onSwipeLeft: () => {
      if (currentPage < pages.length) onPageChange(currentPage + 1);
    },
    onSwipeRight: () => {
      if (currentPage > 1) onPageChange(currentPage - 1);
    },
  });

  if (!page) return null;

  return (
    <div {...swipeHandlers} className="w-full">
      {hasBilingual && translationPages.length > 0 && (
        <div className="flex justify-center gap-1 mb-4">
          <button
            onClick={() => setActiveTab('original')}
            className={`px-4 py-1.5 rounded-full text-xs transition ${
              activeTab === 'original'
                ? 'bg-amber-600/20 text-amber-500'
                : 'text-white/40 hover:text-white/60'
            }`}
          >
            Original
          </button>
          <button
            onClick={() => setActiveTab('translation')}
            className={`px-4 py-1.5 rounded-full text-xs transition ${
              activeTab === 'translation'
                ? 'bg-amber-600/20 text-amber-500'
                : 'text-white/40 hover:text-white/60'
            }`}
          >
            Traduction
          </button>
        </div>
      )}

      <div className="max-w-[560px] mx-auto">
        <div className="bg-[#fdfbf7] rounded-sm shadow-[0_1px_3px_rgba(0,0,0,0.3),0_8px_24px_rgba(0,0,0,0.25)]">
          <BookPage
            page={page}
            headerLeft={title}
            headerRight={author}
            isGreek={isGreek}
            fontSize={Math.min(fontSize, 15)}
            side="single"
          />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/book-reader/MobileBookReader.tsx
git commit -m "feat(reader): add mobile book reader with bilingual toggle"
```

---

## Task 16: BookReaderPage — main page component

**Files:**
- Create: `frontend/src/components/book-reader/BookReaderPage.tsx`

- [ ] **Step 1: Create the main page component**

```tsx
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useLazyPassages } from '../../hooks/useLazyPassages';
import { cachedApiClient } from '../../api/cachedClient';
import { useBookPagination } from './useBookPagination';
import { usePageSync } from './usePageSync';
import { useCalibration } from './useCalibration';
import { BookSpread } from './BookSpread';
import { BookPage } from './BookPage';
import { BookControls } from './BookControls';
import { BookProgress } from './BookProgress';
import { MobileBookReader } from './MobileBookReader';
import { FONT_SIZE_MAP, MOBILE_BREAKPOINT } from './types';
import type { FontSizePreset, PageConfig } from './types';

export function BookReaderPage() {
  const { textId } = useParams<{ textId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // State
  const [work, setWork] = useState<{
    title: string;
    author: string;
    language: string;
    has_translation?: boolean;
  } | null>(null);
  const [currentPage, setCurrentPage] = useState(
    Number(searchParams.get('page')) || 1
  );
  const [isBilingual, setIsBilingual] = useState(false);
  const [fontSize, setFontSize] = useState<FontSizePreset>(
    () => (localStorage.getItem('book-reader-font-size') as FontSizePreset) ?? 'normal'
  );
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  const isMobile = windowWidth < MOBILE_BREAKPOINT;

  // Load work metadata
  useEffect(() => {
    if (!textId) return;
    cachedApiClient.getWork(textId).then(setWork).catch(console.error);
  }, [textId]);

  // Load passages with translations
  const { passages, loading, hasMore, loadMore, totalCount } = useLazyPassages(textId, {
    initialLimit: 200, // Load more for book mode (paginated, no lazy scroll)
    batchSize: 200,
    autoLoad: false, // We control loading manually
  });

  // Load all passages for pagination
  useEffect(() => {
    if (hasMore && !loading) {
      loadMore();
    }
  }, [hasMore, loading, loadMore]);

  // Page config based on viewport
  const config: PageConfig = useMemo(() => {
    const fs = FONT_SIZE_MAP[fontSize];
    const width = isMobile ? windowWidth - 80 : 360;
    const height = isMobile ? window.innerHeight - 200 : 460;
    return {
      width,
      height,
      marginRef: 28,
      fontSize: fs,
      lineHeight: 1.75,
      fontFamily: '"EB Garamond", "Palatino Linotype", Georgia, serif',
    };
  }, [fontSize, isMobile, windowWidth]);

  // Calibration
  const { correctionRatio, calibrated, calibrate, hiddenRef } = useCalibration(config);

  useEffect(() => {
    if (passages.length > 0 && !calibrated) {
      calibrate(passages[0].text_content);
    }
  }, [passages, calibrated, calibrate]);

  // Separate original and translation texts
  const originalPassages = useMemo(
    () =>
      passages.map((p) => ({
        passage_id: p.passage_id,
        canonical_ref: p.canonical_ref,
        text_content: p.text_content,
        kg_node_count: p.kg_node_count ?? 0,
      })),
    [passages]
  );

  const translationPassages = useMemo(
    () =>
      passages
        .filter((p) => p.translation_text)
        .map((p) => ({
          passage_id: p.passage_id + '_tr',
          canonical_ref: p.canonical_ref,
          text_content: p.translation_text!,
          kg_node_count: 0,
        })),
    [passages]
  );

  // Paginate
  const { pages: origPages, totalPages: origTotal } = useBookPagination({
    passages: originalPassages,
    config,
    correctionRatio,
  });

  const { pages: transPages } = useBookPagination({
    passages: translationPassages,
    config,
    correctionRatio,
  });

  // Sync bilingual
  const spreads = usePageSync({
    originalPages: origPages,
    translationPages: isBilingual ? transPages : [],
  });

  const totalPages = isBilingual ? spreads.length * 2 : origTotal;

  // Navigation
  const goToPage = useCallback(
    (page: number) => {
      const clamped = Math.max(1, Math.min(page, totalPages));
      setCurrentPage(clamped);
      setSearchParams({ page: String(clamped) });
    },
    [totalPages, setSearchParams]
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;
      switch (e.key) {
        case 'ArrowLeft':
          goToPage(currentPage - (isBilingual ? 2 : 1));
          break;
        case 'ArrowRight':
          goToPage(currentPage + (isBilingual ? 2 : 1));
          break;
        case 'Home':
          goToPage(1);
          break;
        case 'End':
          goToPage(totalPages);
          break;
        case 't':
          if (work?.has_translation) setIsBilingual((b) => !b);
          break;
        case 'v':
          navigate(`/texts/${textId}`);
          break;
        case 'Escape':
          navigate(`/texts/${textId}`);
          break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [currentPage, totalPages, isBilingual, goToPage, navigate, textId, work]);

  // Window resize
  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    const handler = () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => setWindowWidth(window.innerWidth), 150);
    };
    window.addEventListener('resize', handler);
    return () => {
      window.removeEventListener('resize', handler);
      clearTimeout(timeout);
    };
  }, []);

  // Font size persistence
  useEffect(() => {
    localStorage.setItem('book-reader-font-size', fontSize);
  }, [fontSize]);

  if (loading && passages.length === 0) {
    return (
      <div className="min-h-screen bg-[#1a1a1e] flex items-center justify-center text-white/40">
        Chargement...
      </div>
    );
  }

  if (!work) return null;

  const currentSpreadIdx = Math.floor((currentPage - 1) / 2);
  const currentSpread = spreads[currentSpreadIdx];
  const currentRef = origPages[currentPage - 1]?.passages[0]?.canonicalRef;

  return (
    <div className="min-h-screen bg-[#1a1a1e] text-white/80 flex flex-col items-center px-4 py-8">
      {/* Hidden calibration element */}
      <div ref={hiddenRef} aria-hidden="true" />

      {isMobile ? (
        <MobileBookReader
          originalPages={origPages}
          translationPages={transPages}
          currentPage={currentPage}
          onPageChange={goToPage}
          title={work.title}
          author={work.author}
          originalLanguage={work.language}
          fontSize={FONT_SIZE_MAP[fontSize]}
          hasBilingual={!!work.has_translation}
        />
      ) : isBilingual && currentSpread ? (
        <div className="w-full max-w-[920px] mb-10">
          <BookSpread
            spread={currentSpread}
            title={work.title}
            author={work.author}
            originalLanguage={work.language}
            translationLanguage="en"
            fontSize={FONT_SIZE_MAP[fontSize]}
          />
        </div>
      ) : origPages[currentPage - 1] ? (
        <div className="max-w-[560px] w-full mx-auto mb-10">
          <div className="bg-[#fdfbf7] rounded-sm shadow-[0_1px_3px_rgba(0,0,0,0.3),0_8px_24px_rgba(0,0,0,0.25)]">
            <BookPage
              page={origPages[currentPage - 1]}
              headerLeft={work.title}
              headerRight={work.author}
              isGreek={work.language === 'grc'}
              fontSize={FONT_SIZE_MAP[fontSize]}
              side="single"
            />
          </div>
        </div>
      ) : null}

      <BookProgress
        currentPage={currentPage}
        totalPages={totalPages}
        currentRef={currentRef}
      />

      <BookControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPrevious={() => goToPage(currentPage - (isBilingual ? 2 : 1))}
        onNext={() => goToPage(currentPage + (isBilingual ? 2 : 1))}
        onGoToPage={goToPage}
        fontSize={fontSize}
        onFontSizeChange={setFontSize}
        isBilingual={isBilingual}
        hasBilingual={!!work.has_translation}
        onToggleBilingual={() => setIsBilingual((b) => !b)}
        isPaginated={true}
        onToggleMode={() => navigate(`/texts/${textId}`)}
      />
    </div>
  );
}
```

Note: This imports `BookPage` component directly — make sure the import path is correct. The `cachedApiClient.getWork()` method should already exist (it's used by `CanonicalTextReader`).

- [ ] **Step 2: Verify types compile**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npx tsc --noEmit --pretty
```

Fix any type errors that appear.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/book-reader/BookReaderPage.tsx
git commit -m "feat(reader): add main BookReaderPage component"
```

---

## Task 17: Wire up route and link from existing reader

**Files:**
- Modify: `frontend/src/App.tsx:405`
- Modify: `frontend/src/pages/CanonicalTextReader.tsx`

- [ ] **Step 1: Add route in App.tsx**

After the existing `/texts/:textId` route (line 405), add:

```tsx
<Route path="/texts/:textId/book" element={<BookReaderPage />} />
```

And add the lazy import at the top with other lazy imports:

```tsx
const BookReaderPage = lazy(() =>
  import('./components/book-reader/BookReaderPage').then((m) => ({
    default: m.BookReaderPage,
  }))
);
```

- [ ] **Step 2: Add "Mode livre" button in CanonicalTextReader**

In `CanonicalTextReader.tsx`, find the header controls area (around line 260) and add a link to book mode. Add the import:

```tsx
import { BookOpen } from 'lucide-react';
```

Then add a button in the header controls row:

```tsx
<Link
  to={`/texts/${textId}/book`}
  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-stone-600 hover:text-stone-800 hover:bg-amber-100/40 transition"
  title="Mode livre"
>
  <BookOpen size={14} />
  <span className="hidden sm:inline">Mode livre</span>
</Link>
```

- [ ] **Step 3: Verify build**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npm run build
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx frontend/src/pages/CanonicalTextReader.tsx
git commit -m "feat(reader): wire up book reader route and link from existing reader"
```

---

## Task 18: Visual QA + fix

**Files:** Various (bug fixes)

- [ ] **Step 1: Start dev server and test**

```bash
cd /Users/romaingirardi/Projects/EleutherIA/frontend
npm run dev
```

Open `http://localhost:5173/texts/<any_work_id>` in browser. Click "Mode livre".

- [ ] **Step 2: Verify checklist**

Check each item visually:
- [ ] Pages render with EB Garamond font
- [ ] Running header shows title + author
- [ ] Page numbers appear centered at bottom
- [ ] Canonical refs appear in left margin
- [ ] KG icon appears on hover (for passages with KG links)
- [ ] Progress bar updates on page change
- [ ] Arrow keys navigate pages
- [ ] `t` toggles bilingual mode (only if work has translations)
- [ ] `v` or `Esc` returns to scroll reader
- [ ] Font size toggle cycles through S/M/L
- [ ] Resize to < 900px switches to mobile single-column
- [ ] Deep link `/texts/:id/book?page=5` loads correct page

- [ ] **Step 3: Fix any visual issues found**

Address layout, spacing, or rendering issues discovered during QA.

- [ ] **Step 4: Commit fixes**

```bash
git add -A
git commit -m "fix(reader): visual QA fixes for book reader"
```

---

## Task 19: Add `.superpowers/` to .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add to gitignore**

```bash
echo '.superpowers/' >> /Users/romaingirardi/Projects/EleutherIA/.gitignore
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add .superpowers/ to gitignore"
```
