import { CornerDownLeft, Search, X } from 'lucide-react';
import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import type { AtlasNodeMeta } from './AtlasHelpers';
import { useGraphVocabulary } from './graphVocabulary';
import { getSearchIndex, groupHits, matchRange, searchNodes, type SearchHit } from './searchIndex';

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
  /** Open the result panel above the field (bottom-docked search bars). */
  dropUp?: boolean;
  /** Empty the field after a pick instead of echoing the chosen label. */
  clearOnPick?: boolean;
  autoFocus?: boolean;
}

const DEBOUNCE_MS = 90;
const MAX_CHIPS = 6;

function useDebounced<T>(value: T, delay: number, immediate: boolean): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    if (immediate) {
      setDebounced(value);
      return;
    }
    const id = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(id);
  }, [value, delay, immediate]);
  return immediate ? value : debounced;
}

export function HighlightedLabel({ label, query }: { label: string; query: string }): ReactNode {
  const range = query.trim() ? matchRange(label, query) : null;
  if (!range) return label;
  const [start, end] = range;
  return (
    <>
      {label.slice(0, start)}
      <mark className="rounded-[2px] bg-orange-100 text-orange-950">
        {label.slice(start, end)}
      </mark>
      {label.slice(end)}
    </>
  );
}

export default function KgSearchBar({
  placeholder,
  nodes,
  onPick,
  size = 'lg',
  initialQuery = '',
  resultLimit = 12,
  ariaLabel,
  emptyLabel,
  resultsLabel,
  dropUp = false,
  clearOnPick = false,
  autoFocus = false,
}: KgSearchBarProps) {
  const { t } = useTranslation();
  const vocabulary = useGraphVocabulary();
  const baseId = useId();
  const listId = `${baseId}-list`;
  const [query, setQuery] = useState(initialQuery);
  const [open, setOpen] = useState(false);
  const [armed, setArmed] = useState(initialQuery.length > 0 || autoFocus);
  const [group, setGroup] = useState<string | null>(null);
  const [cursor, setCursor] = useState(0);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebounced(query, DEBOUNCE_MS, query.trim() === '');

  // The index costs one pass over every label: build it only once the user
  // shows intent (hover or focus), never during the first paint.
  const index = useMemo(() => (armed ? getSearchIndex(nodes) : null), [armed, nodes]);

  const outcome = useMemo(
    () => (index ? searchNodes(index, debouncedQuery, { limit: resultLimit, group }) : null),
    [index, debouncedQuery, resultLimit, group],
  );

  const grouped = useMemo(() => (outcome ? groupHits(outcome.hits) : []), [outcome]);
  const flat = useMemo<ReadonlyArray<SearchHit>>(
    () => grouped.flatMap((bucket) => bucket.hits),
    [grouped],
  );
  const chips = useMemo(
    () =>
      outcome
        ? [...outcome.groupTotals.entries()]
            .sort((a, b) => b[1] - a[1])
            .slice(0, MAX_CHIPS)
        : [],
    [outcome],
  );

  useEffect(() => {
    setCursor(0);
  }, [debouncedQuery, group]);

  useEffect(() => {
    function handlePointerDown(event: PointerEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('pointerdown', handlePointerDown, true);
    return () => document.removeEventListener('pointerdown', handlePointerDown, true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const active = listRef.current?.querySelector<HTMLElement>('[aria-selected="true"]');
    if (active && typeof active.scrollIntoView === 'function') {
      active.scrollIntoView({ block: 'nearest' });
    }
  }, [cursor, open]);

  function commit(node: AtlasNodeMeta) {
    onPick(node);
    setQuery(clearOnPick ? '' : node.label);
    setGroup(null);
    setOpen(false);
  }

  const hasQuery = query.trim().length > 0;
  const pending = hasQuery && debouncedQuery !== query;
  const optionId = (i: number) => `${baseId}-opt-${i}`;
  const activeHit = open ? flat[cursor] : undefined;

  const field =
    size === 'lg'
      ? 'h-14 gap-3 px-5 text-base'
      : 'h-10 gap-2.5 px-3.5 text-sm [@media(pointer:coarse)]:h-11 [@media(pointer:coarse)]:text-base';

  let statusText = '';
  if (open && outcome && !pending) {
    statusText = hasQuery
      ? outcome.total === 0
        ? emptyLabel
        : t('cosmograph.search.resultCount', { count: outcome.total, formatted: vocabulary.count(outcome.total), defaultValue: '{{formatted}} matches' })
      : '';
  }

  return (
    <div
      ref={wrapperRef}
      className="relative w-full"
      onPointerEnter={() => setArmed(true)}
      onBlur={(event) => {
        if (!wrapperRef.current?.contains(event.relatedTarget as Node | null)) setOpen(false);
      }}
    >
      <div
        className={[
          'flex items-center rounded-2xl border bg-[#fffdf9] text-stone-900 shadow-[0_10px_34px_rgba(72,52,36,0.10)] transition-[border-color,box-shadow] duration-150',
          open
            ? 'border-teal-700 shadow-[0_0_0_3px_rgba(15,118,110,0.14),0_18px_50px_rgba(15,118,110,0.12)]'
            : 'border-stone-300 hover:border-stone-400',
          field,
        ].join(' ')}
        onClick={() => inputRef.current?.focus()}
      >
        <Search
          aria-hidden
          className={size === 'lg' ? 'h-5 w-5 shrink-0 text-teal-700' : 'h-4 w-4 shrink-0 text-stone-500'}
        />
        <input
          ref={inputRef}
          type="text"
          inputMode="search"
          enterKeyHint="go"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={activeHit ? optionId(cursor) : undefined}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
          spellCheck={false}
          autoFocus={autoFocus}
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setArmed(true);
            setOpen(true);
          }}
          onFocus={() => {
            setArmed(true);
            setOpen(true);
          }}
          onKeyDown={(event) => {
            if (event.key === 'ArrowDown') {
              event.preventDefault();
              setOpen(true);
              if (flat.length > 0) setCursor((c) => (c + 1) % flat.length);
            } else if (event.key === 'ArrowUp') {
              event.preventDefault();
              setOpen(true);
              if (flat.length > 0) setCursor((c) => (c - 1 + flat.length) % flat.length);
            } else if (event.key === 'Enter') {
              // Typing faster than the debounce must not make Enter a no-op.
              const next = pending && index
                ? searchNodes(index, query, { limit: 1, group }).hits[0]
                : flat[cursor] ?? flat[0];
              if (next) {
                event.preventDefault();
                commit(next.node);
              }
            } else if (event.key === 'Escape') {
              event.preventDefault();
              if (open) setOpen(false);
              else {
                setQuery('');
                setGroup(null);
              }
            } else if (event.key === 'Tab') {
              setOpen(false);
            }
          }}
          placeholder={placeholder}
          aria-label={ariaLabel}
          className="min-w-0 flex-1 bg-transparent font-body text-stone-900 outline-none placeholder:text-stone-500"
        />
        {query && (
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              setQuery('');
              setGroup(null);
              setCursor(0);
              inputRef.current?.focus();
            }}
            aria-label={t('cosmograph.search.clear', 'Clear search')}
            className="relative inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-stone-500 transition-colors after:absolute after:-inset-2 after:content-[''] hover:bg-stone-100 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
          >
            <X className="h-3.5 w-3.5" aria-hidden />
          </button>
        )}
      </div>

      <p className="sr-only" role="status" aria-live="polite">
        {statusText}
      </p>

      {open && outcome && (
        <div
          className={[
            'absolute left-0 right-0 z-40 flex max-h-[min(28rem,62vh)] flex-col overflow-hidden rounded-2xl border border-stone-300 bg-[#fffdf9] shadow-[0_24px_60px_rgba(72,52,36,0.18)]',
            dropUp ? 'bottom-[calc(100%+0.5rem)]' : 'top-[calc(100%+0.5rem)]',
          ].join(' ')}
        >
          {chips.length > 1 && (
            <div
              role="group"
              aria-label={t('cosmograph.search.refine', 'Narrow by kind')}
              className="flex shrink-0 gap-1.5 overflow-x-auto border-b border-stone-200 px-2 py-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
            >
              <ChipButton
                active={group === null}
                onSelect={() => setGroup(null)}
                label={t('cosmograph.search.all', 'All')}
                count={hasQuery ? vocabulary.count(outcome.total) : null}
              />
              {chips.map(([key, total]) => (
                <ChipButton
                  key={key}
                  active={group === key}
                  onSelect={() => setGroup(group === key ? null : key)}
                  label={vocabulary.group(key)}
                  count={hasQuery ? vocabulary.count(total) : null}
                />
              ))}
            </div>
          )}

          <div
            ref={listRef}
            id={listId}
            role="listbox"
            aria-label={resultsLabel}
            className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-1.5"
          >
            {!hasQuery && (
              <p className="px-2.5 pb-1 pt-1.5 font-body text-[12px] text-stone-500">
                {t('cosmograph.search.suggestions', 'Most connected entries')}
              </p>
            )}
            {flat.length === 0 && !pending ? (
              <div className="px-3 py-5 font-body text-sm leading-6 text-stone-600">{emptyLabel}</div>
            ) : (
              grouped.map((bucket) => {
                const headerId = `${baseId}-grp-${bucket.group}`;
                const groupTotal = outcome.groupTotals.get(bucket.group) ?? bucket.hits.length;
                return (
                  <div key={bucket.group} role="group" aria-labelledby={headerId} className="pb-1">
                    <div
                      id={headerId}
                      className="flex items-baseline justify-between px-2.5 pb-1 pt-2 font-body text-[11px] font-semibold text-stone-500"
                    >
                      <span>{vocabulary.group(bucket.group)}</span>
                      {hasQuery && groupTotal > bucket.hits.length && (
                        <button
                          type="button"
                          tabIndex={-1}
                          onMouseDown={(event) => event.preventDefault()}
                          onClick={() => setGroup(bucket.group)}
                          className="font-normal text-teal-800 underline decoration-teal-700/30 underline-offset-2 hover:decoration-teal-700"
                        >
                          {t('cosmograph.search.seeAll', { count: groupTotal, formatted: vocabulary.count(groupTotal), defaultValue: 'See all {{formatted}}' })}
                        </button>
                      )}
                    </div>
                    {bucket.hits.map((hit) => {
                      const flatIndex = flat.indexOf(hit);
                      const active = flatIndex === cursor;
                      const node = hit.node;
                      const detail = [
                        node.periodLabel !== 'Unspecified' ? vocabulary.period(node.periodLabel) : null,
                        node.schoolLabel !== 'Unattached' ? vocabulary.school(node.schoolLabel) : null,
                      ]
                        .filter(Boolean)
                        .join(' · ');
                      const terms = [node.greekTerm, node.latinTerm].filter(Boolean).join(' · ');
                      return (
                        <div
                          key={node.id}
                          id={optionId(flatIndex)}
                          role="option"
                          aria-selected={active}
                          onMouseDown={(event) => event.preventDefault()}
                          onMouseMove={() => {
                            if (!active) setCursor(flatIndex);
                          }}
                          onClick={() => commit(node)}
                          className={[
                            'flex min-h-11 cursor-pointer items-start gap-3 rounded-xl px-2.5 py-2 text-left',
                            active ? 'bg-teal-50 ring-1 ring-inset ring-teal-700/25' : '',
                          ].join(' ')}
                        >
                          <span
                            aria-hidden
                            className="mt-[0.4rem] h-2.5 w-2.5 shrink-0 rounded-full ring-1 ring-stone-900/10"
                            style={{ backgroundColor: node.color }}
                          />
                          <span className="min-w-0 flex-1">
                            <span className="line-clamp-2 break-words font-body text-sm font-semibold leading-5 text-stone-950">
                              <HighlightedLabel label={node.label} query={debouncedQuery} />
                            </span>
                            {(detail || terms) && (
                              <span className="mt-0.5 block truncate font-body text-[12px] text-stone-500">
                                {terms && (
                                  <span className="font-reader text-stone-700">
                                    <HighlightedLabel label={terms} query={debouncedQuery} />
                                  </span>
                                )}
                                {terms && detail ? ' · ' : ''}
                                {detail}
                              </span>
                            )}
                          </span>
                          {active && (
                            <CornerDownLeft
                              aria-hidden
                              className="mt-1 hidden h-3.5 w-3.5 shrink-0 text-teal-700 [@media(pointer:fine)]:block"
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })
            )}
          </div>

          <p
            aria-hidden
            className="hidden shrink-0 border-t border-stone-200 px-3 py-1.5 font-body text-[11px] text-stone-500 [@media(pointer:fine)]:block"
          >
            {t('cosmograph.search.keyboardHint', '↑ ↓ move · Enter open · Esc close')}
          </p>
        </div>
      )}
    </div>
  );
}

function ChipButton({
  active,
  onSelect,
  label,
  count,
}: {
  active: boolean;
  onSelect: () => void;
  label: string;
  count: string | null;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onMouseDown={(event) => event.preventDefault()}
      onClick={onSelect}
      className={[
        'inline-flex h-8 shrink-0 items-center gap-1.5 rounded-full border px-3 font-body text-[12px] transition-colors [@media(pointer:coarse)]:h-9',
        active
          ? 'border-teal-700 bg-teal-700 text-white'
          : 'border-stone-300 bg-white text-stone-700 hover:border-stone-500',
      ].join(' ')}
    >
      <span>{label}</span>
      {count !== null && (
        <span className={active ? 'text-teal-50/85' : 'text-stone-500'}>{count}</span>
      )}
    </button>
  );
}
