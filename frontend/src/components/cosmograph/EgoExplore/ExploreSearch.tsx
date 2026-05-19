import { ChevronRight, Search, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import type { AtlasNodeMeta } from '../AtlasHelpers';
import NodeTypeIcon from './NodeTypeIcon';

interface ExploreSearchProps {
  readonly nodes: ReadonlyArray<AtlasNodeMeta>;
  readonly onPick: (node: AtlasNodeMeta) => void;
  readonly resultLimit?: number;
}

function scoreNode(node: AtlasNodeMeta, query: string): number {
  if (!query) return node.importance;
  const q = query.toLowerCase();
  const label = node.label.toLowerCase();
  const greek = node.greekTerm.toLowerCase();
  const latin = node.latinTerm.toLowerCase();
  let score = 0;
  if (label === q) score += 200;
  if (label.startsWith(q)) score += 140;
  if (label.includes(q)) score += 90;
  if (greek && (greek.startsWith(q) || greek.includes(q))) score += 100;
  if (latin && (latin.startsWith(q) || latin.includes(q))) score += 60;
  if (node.schoolLabel.toLowerCase().includes(q)) score += 40;
  if (node.periodLabel.toLowerCase().includes(q)) score += 30;
  if (node.typeLabel.toLowerCase().includes(q)) score += 25;
  if (score === 0) return -1;
  return score + node.importance / 25;
}

function rank(
  nodes: ReadonlyArray<AtlasNodeMeta>,
  query: string,
  limit: number,
): AtlasNodeMeta[] {
  const trimmed = query.trim();
  if (!trimmed) {
    return [...nodes].sort((a, b) => b.importance - a.importance).slice(0, limit);
  }
  const scored = nodes
    .map((node) => ({ node, score: scoreNode(node, trimmed) }))
    .filter((entry) => entry.score >= 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
  return scored.map((entry) => entry.node);
}

export default function ExploreSearch({
  nodes,
  onPick,
  resultLimit = 8,
}: ExploreSearchProps) {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [focused, setFocused] = useState(false);
  const [cursor, setCursor] = useState(0);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const results = rank(nodes, query, resultLimit);

  useEffect(() => {
    setCursor(0);
  }, [query]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setFocused(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  function commit(node: AtlasNodeMeta) {
    onPick(node);
    setQuery('');
    setFocused(false);
  }

  const open = focused && (query.trim().length > 0 || results.length > 0);

  return (
    <div ref={wrapperRef} className="relative w-full">
      <div
        className={[
          'flex h-12 items-center gap-2.5 rounded-2xl border bg-white/85 px-4 backdrop-blur-md transition-colors',
          focused
            ? 'border-amber-400/70 shadow-[0_18px_50px_-30px_rgba(124,77,15,0.55)]'
            : 'border-amber-200/60 hover:border-amber-300/80',
        ].join(' ')}
      >
        <Search aria-hidden className="h-4 w-4 text-amber-700/80" />
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onFocus={() => setFocused(true)}
          onKeyDown={(event) => {
            if (event.key === 'ArrowDown') {
              event.preventDefault();
              setCursor((c) => Math.min(results.length - 1, c + 1));
            } else if (event.key === 'ArrowUp') {
              event.preventDefault();
              setCursor((c) => Math.max(0, c - 1));
            } else if (event.key === 'Enter') {
              const next = results[cursor];
              if (next) {
                event.preventDefault();
                commit(next);
              }
            } else if (event.key === 'Escape') {
              event.preventDefault();
              setQuery('');
              setFocused(false);
            }
          }}
          placeholder={t(
            'cosmograph.explore.searchPlaceholder',
            'Jump to a thinker, concept or work…',
          )}
          aria-label={t('cosmograph.explore.searchAria', 'Jump to a node')}
          className="min-w-0 flex-1 bg-transparent text-[14px] text-stone-900 outline-none placeholder:text-stone-500"
        />
        {query && (
          <button
            type="button"
            onClick={() => setQuery('')}
            aria-label={t('common.clear', 'Clear')}
            className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-amber-200/60 bg-white/70 text-amber-800 transition-colors hover:border-amber-300 hover:text-amber-900"
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>

      {open && (
        <div
          role="listbox"
          aria-label={t('cosmograph.explore.searchResults', 'Search results')}
          className="absolute bottom-[calc(100%+0.5rem)] left-0 right-0 z-30 max-h-[20rem] overflow-y-auto rounded-2xl border border-amber-200/60 bg-white/95 p-1.5 shadow-[0_24px_60px_-30px_rgba(124,77,15,0.55)] backdrop-blur-xl md:bottom-auto md:top-[calc(100%+0.5rem)]"
        >
          {results.length === 0 ? (
            <div className="px-4 py-6 text-sm text-stone-600">
              {t(
                'cosmograph.explore.searchEmpty',
                'No match. Try a Greek or Latin term, or a surname.',
              )}
            </div>
          ) : (
            results.map((node, index) => {
              const active = index === cursor;
              const metaLine = [
                node.typeLabel,
                node.periodLabel !== 'Unspecified' ? node.periodLabel : null,
              ]
                .filter(Boolean)
                .join(' · ');
              return (
                <button
                  type="button"
                  key={node.id}
                  role="option"
                  aria-selected={active}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => commit(node)}
                  className={[
                    'flex w-full items-start gap-3 rounded-xl border px-3 py-2.5 text-left transition-colors',
                    active
                      ? 'border-amber-300/70 bg-amber-50'
                      : 'border-transparent hover:border-amber-200/70 hover:bg-amber-50/60',
                  ].join(' ')}
                >
                  <NodeTypeIcon typeKey={node.typeKey} layer={node.layer} size="sm" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-stone-900">{node.label}</p>
                    <p className="mt-0.5 truncate text-[11px] uppercase tracking-[0.16em] text-stone-500">
                      {metaLine || t('cosmograph.explore.graphNode', 'Graph node')}
                    </p>
                    {(node.greekTerm || node.latinTerm) && (
                      <p className="mt-0.5 truncate text-[12px] italic text-stone-700">
                        {[node.greekTerm, node.latinTerm].filter(Boolean).join(' · ')}
                      </p>
                    )}
                  </div>
                  <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-amber-700/70" />
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
