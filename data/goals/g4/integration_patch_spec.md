# G4 Integration Patch Spec

Three discrete wiring tasks. All paths are relative to `frontend/src/`.

---

## 1. CitationGenerator — mount on three surfaces

`CitationGenerator` (`components/CitationGenerator.tsx`) accepts:
```ts
interface CitationGeneratorProps {
  citations: Citation[];   // { id?, text, source, format?, citation?, url?, doi?, node_id? }
  className?: string;
}
```

The `Citation.text` field is the context snippet; `Citation.source` is the formatted
label (e.g. `"Cicero, De Fato 41"`); `Citation.citation` is the pre-formatted string
used for copy/export; `Citation.id`/`node_id` are optional KG node identifiers.

---

### 1a. CanonicalTextReader (scroll reader) — `pages/CanonicalTextReader.tsx`

**Where to add state (around line 47, after existing `useState` declarations):**
```ts
const [showCitationPanel, setShowCitationPanel] = useState(false);
```

**Add import at top:**
```ts
import { CitationGenerator } from '../components/CitationGenerator';
```

**Insert toggle button in the header toolbar** (around line 256, alongside the existing
`Mode livre` link and TOC button — inside the `<div className="flex items-center gap-2">`):
```tsx
<button
  onClick={() => setShowCitationPanel(p => !p)}
  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-stone-600 hover:text-stone-800 hover:bg-amber-100/40 transition"
  title="Citations"
>
  <FileText size={14} />
  <span className="hidden sm:inline">Citations</span>
</button>
```
Add `FileText` to the existing `lucide-react` import on line 2.

**Build the citations array** (after the `if (loading)` early return, before the main
`return` at line 240, using `useMemo`):
```ts
const workCitations = useMemo<CitationGeneratorProps['citations']>(() => {
  if (!work) return [];
  return [{
    id: work.canonical_id,
    text: `${work.title}${work.author ? ' — ' + work.author : ''}`,
    source: [
      work.author,
      work.title,
      work.editor ? `Ed. ${work.editor}` : null,
      work.publisher,
      work.publication_date,
      work.pub_place,
    ].filter(Boolean).join(', '),
    citation: [
      work.author,
      work.title,
      work.editor ? `Ed. ${work.editor}` : null,
      work.publisher,
      work.publication_date,
    ].filter(Boolean).join('. '),
    url: work.doi_url ?? undefined,
  }];
}, [work]);
```
Import `useMemo` is already present (it's used nowhere currently but `useRef`/`useCallback`
are — add `useMemo` to the existing react import on line 1).

**Render the panel** (add before the closing `</div>` of the main `return`, around
line 481, before the keyboard-shortcuts hint):
```tsx
{showCitationPanel && (
  <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40"
       onClick={() => setShowCitationPanel(false)}>
    <div className="w-full sm:max-w-2xl max-h-[80vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl shadow-2xl"
         onClick={e => e.stopPropagation()}>
      <CitationGenerator citations={workCitations} />
    </div>
  </div>
)}
```

---

### 1b. CanonicalPassageDetailPage — `pages/CanonicalPassageDetailPage/index.tsx`

**Add import at top (after existing imports):**
```ts
import { CitationGenerator } from '../../components/CitationGenerator';
```

**Add state (inside the component, after existing `useState` declarations ~line 61):**
```ts
const [showCitationPanel, setShowCitationPanel] = useState(false);
```

**Build citations from `detail`** (in the `{detail && !loading && !error && ...}` block,
add a `useMemo` derived value — add `useMemo` to the react import on line 1):
```ts
const passageCitations = useMemo<CitationGeneratorProps['citations']>(() => {
  if (!detail) return [];
  const items: CitationGeneratorProps['citations'] = [];
  // Primary passage citation
  items.push({
    id: detail.passage_id,
    text: detail.full_text ?? detail.label,
    source: [detail.author, detail.work_title, detail.canonical_ref].filter(Boolean).join(', '),
    citation: [detail.author, detail.work_title, detail.canonical_ref].filter(Boolean).join('. '),
    node_id: detail.passage_id,
  });
  return items;
}, [detail]);
```

**Insert "Export citations" button** in the article hero section (around line 164,
after the period/language badges row, before the `<h1>`):
```tsx
<button
  onClick={() => setShowCitationPanel(p => !p)}
  className="inline-flex items-center gap-1.5 rounded-full border border-amber-200/60 bg-amber-50/70 px-3 py-1 text-[11px] font-medium text-amber-800 hover:bg-amber-100 transition-colors"
>
  <FileText className="h-3 w-3" aria-hidden="true" />
  Export citation
</button>
```
Add `FileText` to the existing `lucide-react` import on line 7.

**Render modal** (just before the closing `</div>` of the outer `max-w-6xl` container,
around line 379, before the `{loading && ...}` block):
```tsx
{showCitationPanel && detail && (
  <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40"
       onClick={() => setShowCitationPanel(false)}>
    <div className="w-full sm:max-w-2xl max-h-[80vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl shadow-2xl"
         onClick={e => e.stopPropagation()}>
      <CitationGenerator citations={passageCitations} />
    </div>
  </div>
)}
```

**Add missing imports:** `useMemo` to react import; `FileText` to lucide-react import;
`CitationGeneratorProps` is not explicitly needed (use inline type or import the interface).

---

### 1c. GraphRAG answer — `pages/GraphRAGPage/MessageBubble.tsx`

The GraphRAG answer already surfaces `ancient_sources` and `modern_scholarship` arrays
inside `message.citations`. Both are `string[]` where each string is an already-formatted
citation label (e.g. `"Cicero, De Fato 41-43"`).

**Add import at top (after existing imports):**
```ts
import { CitationGenerator } from '../../components/CitationGenerator';
```

**Add state in `MessageBubble` component (around line 21):**
```ts
const [showCitationPanel, setShowCitationPanel] = useState(false);
```

**Build citations array** (derived inline, not memoised — the component is small):
```ts
const allCitations = useMemo(() => {
  if (!message.citations) return [];
  const ancient = (message.citations.ancient_sources ?? []).map((s, i) => ({
    id: `ancient_${i}`,
    text: s,
    source: s,
    citation: s,
  }));
  const modern = (message.citations.modern_scholarship ?? []).map((s, i) => ({
    id: `modern_${i}`,
    text: s,
    source: s,
    citation: s,
  }));
  return [...ancient, ...modern];
}, [message.citations]);
```
Add `useMemo` to the existing react import on line 1.

**Insert the "Export bibliography" button** at the bottom of the assistant message block,
inside the `!isUser` branch, after the Sources panel collapse (`{sources && sources.length > 0 && ...}` block)
at approximately line 373, before the closing `</div>` of `<div className="space-y-4">`:
```tsx
{allCitations.length > 0 && (
  <div className="border-t border-amber-200/40 pt-3">
    <button
      onClick={() => setShowCitationPanel(p => !p)}
      className="flex items-center gap-2 text-sm xl:text-base font-medium text-stone-700 hover:text-stone-800 transition-colors w-full"
    >
      <FileText className="w-4 h-4" />
      <span>Export bibliography ({allCitations.length} citations)</span>
      {showCitationPanel ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
    </button>
    <AnimatePresence>
      {showCitationPanel && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="overflow-hidden mt-3"
        >
          <CitationGenerator citations={allCitations} />
        </motion.div>
      )}
    </AnimatePresence>
  </div>
)}
```
`FileText` is already imported on line 5. `AnimatePresence`, `motion`, `ChevronUp`,
`ChevronDown` are already imported.

---

## 2. BookReaderPage as default `/texts/:textId`

**Goal:** `/texts/:textId` → BookReaderPage (book/spread view);
`/texts/:textId/scroll` → CanonicalTextReader (current scroll view).

### 2a. `App.tsx` — route swap (lines 447-449)

**Current routes:**
```tsx
<Route path="/texts/:textId/book" element={<BookReaderPage />} />
<Route path="/texts/:textId" element={<CanonicalTextReader />} />
```

**Replace with:**
```tsx
<Route path="/texts/:textId" element={<BookReaderPage />} />
<Route path="/texts/:textId/scroll" element={<CanonicalTextReader />} />
```

No import changes needed — both lazy imports already exist (lines 35-36 in App.tsx).

### 2b. BookReaderPage — fix "Mode scroll" button (`components/book-reader/BookReaderPage.tsx`)

The button at line 327 navigates to `/texts/${textId}` (the old CanonicalTextReader URL).
The keyboard handler at line 261 does the same.

**Button onClick (line 327):**
```tsx
onClick={() => { if (textId) navigate(`/texts/${textId}/scroll`); }}
```

**Keyboard handler (line 261 — case 'v'/'Escape'):**
```ts
case 'v': case 'Escape': if (textId) navigate(`/texts/${textId}/scroll`); break;
```

### 2c. CanonicalTextReader — fix "Mode livre" link (`pages/CanonicalTextReader.tsx`)

The `<Link>` at line 257 currently goes to `/texts/${textId}/book`.

**Change to:**
```tsx
<Link to={`/texts/${textId}`} ...>
```

---

## 3. Replace `window.prompt()` model selector — `pages/GraphRAGPage/index.tsx`

### Context

`handleRetry` (line 854–859) calls `window.prompt()` to get the model key:
```ts
const newModel = window.prompt('Enter model key to retry with ...', selectedModel);
```
This is the only interactive model-selection UI. The backend model is already hardcoded
as `'kimi-k2.6'` (line 78) and `selectedModel` is a plain const, not state.

### Replacement

**Add state for the inline dropdown (after the `ancientOnly` state, around line 83):**
```ts
const [showRetryDropdown, setShowRetryDropdown] = useState(false);
const [retryModel, setRetryModel] = useState('kimi-k2.6');
```

**Available models** (sourced from the `/api/graphrag/models` endpoint already fetched
into `modelContextMap` at line 134). Use `Object.keys(modelContextMap)` as the option
list; fall back to a hardcoded minimal list while the fetch is pending:
```ts
const availableModels = Object.keys(modelContextMap).length > 0
  ? Object.keys(modelContextMap)
  : ['kimi-k2.6', 'gemini-3.1-pro-preview', 'kimi-k2.5-thinking'];
```

**Rewrite `handleRetry`:**
```ts
const handleRetry = useCallback(() => {
  if (!initialQuestion) return;
  setShowRetryDropdown(p => !p);
}, [initialQuestion]);

const handleRetryWithModel = useCallback((model: string) => {
  setShowRetryDropdown(false);
  processQuery(initialQuestion, model, selectedMode);
}, [initialQuestion, selectedMode, processQuery]);
```

**Inline dropdown component** — mount inside the `ChatPanel` wrapper. The cleanest
anchor point is in `ChatPanel.tsx` via a new optional prop, but since `handleRetry`
is already passed as `onRetry` and `ResponseTabs` uses it, the simplest non-invasive
placement is to render the dropdown overlay directly inside the `GraphRAGPage` return,
overlaying the two-column layout:

**In `GraphRAGPage/index.tsx`, inside the `{(messages.length > 0 || streaming) && ...}` block,
add after the `<MobileGraphSheet>` (around line 989), before the closing `</div>` of the
fixed two-column container:**
```tsx
{showRetryDropdown && (
  <div
    className="absolute top-0 left-0 right-0 bottom-0 z-50 flex items-start justify-center pt-16 bg-black/20"
    onClick={() => setShowRetryDropdown(false)}
  >
    <div
      className="bg-white rounded-2xl shadow-xl border border-amber-200/60 p-4 w-72"
      onClick={e => e.stopPropagation()}
    >
      <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3">
        Retry with model
      </p>
      <div className="space-y-1">
        {availableModels.map(model => (
          <button
            key={model}
            onClick={() => handleRetryWithModel(model)}
            className={[
              'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
              model === retryModel
                ? 'bg-amber-50 text-amber-900 font-medium border border-amber-200/60'
                : 'text-stone-700 hover:bg-stone-50',
            ].join(' ')}
          >
            {model}
          </button>
        ))}
      </div>
    </div>
  </div>
)}
```

The parent `<div className="flex bg-parchment-50">` at line 897 needs `relative` added
to its className so the absolute overlay is scoped to the two-column region.

**Add `useState` to the existing react import** (line 1 already has `useState` — no
change needed; `showRetryDropdown` and `retryModel` use it).

**Remove the `window.prompt` call entirely** from the old `handleRetry` (the new version
above replaces it in full).

---

## Summary of files touched

| File | Changes |
|------|---------|
| `frontend/src/App.tsx` | Swap `/texts/:textId` ↔ `/texts/:textId/scroll` routes |
| `frontend/src/components/book-reader/BookReaderPage.tsx` | 2 URL fixes: button + keyboard handler |
| `frontend/src/pages/CanonicalTextReader.tsx` | Fix "Mode livre" link URL; add CitationGenerator panel + state + useMemo |
| `frontend/src/pages/CanonicalPassageDetailPage/index.tsx` | Add CitationGenerator panel + state + useMemo + button |
| `frontend/src/pages/GraphRAGPage/MessageBubble.tsx` | Add CitationGenerator expand/collapse below Sources panel |
| `frontend/src/pages/GraphRAGPage/index.tsx` | Replace `window.prompt` with inline dropdown; add 2 state vars + `handleRetryWithModel`; add `relative` to container |

No new files need to be created. No new npm packages required.
