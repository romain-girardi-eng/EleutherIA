import { ChevronRight, Search, X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import type { AtlasNodeMeta } from './AtlasHelpers';

interface KgSearchBarProps {
  placeholder: string;
  nodes: ReadonlyArray<AtlasNodeMeta>;
  onPick: (node: AtlasNodeMeta) => void;
  size?: 'lg' | 'sm';
  initialQuery?: string;
  resultLimit?: number;
  ariaLabel: string;
  emptyLabel: string;
  resultsLabel: string;
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

function rank(nodes: ReadonlyArray<AtlasNodeMeta>, query: string, limit: number): AtlasNodeMeta[] {
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

export default function KgSearchBar({
  placeholder,
  nodes,
  onPick,
  size = 'lg',
  initialQuery = '',
  resultLimit = 8,
  ariaLabel,
  emptyLabel,
  resultsLabel,
}: KgSearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
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
    setQuery(node.label);
    setFocused(false);
  }

  const inputSize =
    size === 'lg'
      ? 'h-14 text-base px-5'
      : 'h-10 text-sm px-3.5';

  const open = focused && (query.trim().length > 0 || results.length > 0);

  return (
    <div ref={wrapperRef} className="relative w-full">
      <div
        className={[
          'flex items-center gap-3 rounded-2xl border bg-[#fffdf9]/94 text-stone-900 shadow-[0_10px_34px_rgba(72,52,36,0.11)] backdrop-blur-xl transition-colors',
          focused
            ? 'border-teal-700 shadow-[0_18px_50px_rgba(15,118,110,0.16)]'
            : 'border-stone-300 hover:border-orange-500',
          inputSize,
        ].join(' ')}
      >
        <Search
          aria-hidden
          className={size === 'lg' ? 'h-5 w-5 text-teal-700' : 'h-4 w-4 text-stone-500'}
        />
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
          placeholder={placeholder}
          aria-label={ariaLabel}
          className="min-w-0 flex-1 bg-transparent text-stone-900 outline-none placeholder:text-stone-400"
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setCursor(0);
            }}
            aria-label="Clear search"
            className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-stone-300 bg-white/70 text-stone-500 transition-colors hover:border-orange-500 hover:text-orange-800"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {open && (
        <div
          role="listbox"
          aria-label={resultsLabel}
          className="absolute left-0 right-0 top-[calc(100%+0.5rem)] z-40 max-h-[22rem] overflow-y-auto rounded-2xl border border-stone-300 bg-[#fffdf9]/98 p-1.5 shadow-[0_24px_60px_rgba(72,52,36,0.18)] backdrop-blur-xl"
        >
          {results.length === 0 ? (
            <div className="px-4 py-6 text-sm text-stone-500">{emptyLabel}</div>
          ) : (
            results.map((node, index) => {
              const active = index === cursor;
              const meta = [node.typeLabel, node.periodLabel !== 'Unspecified' ? node.periodLabel : null]
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
                      ? 'border-teal-700/30 bg-teal-50'
                      : 'border-transparent hover:border-stone-200 hover:bg-stone-50',
                  ].join(' ')}
                >
                  <span
                    aria-hidden
                    className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full border border-stone-300"
                    style={{ backgroundColor: node.color }}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-stone-950">{node.label}</p>
                    <p className="mt-0.5 truncate text-[11px] uppercase tracking-[0.16em] text-stone-500">
                      {meta || 'Graph node'}
                    </p>
                    {(node.greekTerm || node.latinTerm) && (
                      <p className="mt-0.5 truncate text-[12px] text-stone-600">
                        {[node.greekTerm, node.latinTerm].filter(Boolean).join(' · ')}
                      </p>
                    )}
                  </div>
                  <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-stone-400" />
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
