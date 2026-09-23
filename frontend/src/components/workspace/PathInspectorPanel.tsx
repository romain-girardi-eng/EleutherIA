import { ArrowDown, ArrowLeftRight, ArrowUp, BookmarkPlus, Route, X } from 'lucide-react';
import { memo, useDeferredValue, useEffect, useId, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';

import { useGraphWorkspace } from '../../context/GraphWorkspaceContext';
import type { AtlasNodeMeta } from '../cosmograph/AtlasHelpers';
import {
  findShortestPath,
  MAX_PATH_DEPTH,
  searchRows,
  type Adjacency,
  type PathStep,
  type ScholarRow,
} from './scholarModel';
import { useScholarLabels } from './useScholarLabels';

const focusRing = 'outline-none focus-visible:ring-2 focus-visible:ring-orange-700';
const SUGGESTIONS = 8;

interface PathInspectorPanelProps {
  index: ReadonlyArray<ScholarRow>;
  metaById: ReadonlyMap<string, AtlasNodeMeta>;
  adjacency: Adjacency;
}

type PathResult =
  | { status: 'idle' }
  | { status: 'found'; source: string; target: string; steps: PathStep[] }
  | { status: 'none'; source: string; target: string };

function PathInspectorPanelComponent({ index, metaById, adjacency }: PathInspectorPanelProps) {
  const { t } = useTranslation();
  const labels = useScholarLabels();
  const { state, selectPrimary, setEvidenceThread, setCompareIds } = useGraphWorkspace();
  const [sourceId, setSourceId] = useState<string | null>(state.primarySelection);
  const [targetId, setTargetId] = useState<string | null>(null);
  const [result, setResult] = useState<PathResult>({ status: 'idle' });
  const [attempted, setAttempted] = useState(false);

  const labelOf = (id: string) => metaById.get(id)?.label ?? id;

  const run = (event?: FormEvent) => {
    event?.preventDefault();
    setAttempted(true);
    if (!sourceId || !targetId) return;
    const steps = findShortestPath(adjacency, sourceId, targetId);
    setResult(steps ? { status: 'found', source: sourceId, target: targetId, steps } : { status: 'none', source: sourceId, target: targetId });
  };

  const swap = () => {
    setSourceId(targetId);
    setTargetId(sourceId);
    setResult({ status: 'idle' });
  };

  const pathIds = result.status === 'found' ? [result.source, ...result.steps.map((step) => step.to)] : [];

  const addToThread = () => {
    const existing = new Set(state.evidenceThread);
    setEvidenceThread([...state.evidenceThread, ...pathIds.filter((id) => !existing.has(id))]);
  };

  return (
    <div className="space-y-6 p-3 sm:p-5">
      <div className="max-w-2xl">
        <h2 className="flex items-center gap-2 font-display text-3xl text-stone-950">
          <Route className="h-5 w-5 text-orange-800" aria-hidden="true" />
          {t('scholar.path.title')}
        </h2>
        <p className="mt-1.5 font-reader text-base leading-6 text-stone-600">
          {t('scholar.path.description', { depth: MAX_PATH_DEPTH })}
        </p>
      </div>

      <form onSubmit={run} className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)_auto] md:items-end" noValidate>
        <NodePicker
          label={t('scholar.path.source')}
          placeholder={t('scholar.path.sourcePlaceholder')}
          index={index}
          value={sourceId}
          valueLabel={sourceId ? labelOf(sourceId) : ''}
          onChange={(id) => {
            setSourceId(id);
            setResult({ status: 'idle' });
          }}
          invalid={attempted && !sourceId}
        />
        <button
          type="button"
          onClick={swap}
          aria-label={t('scholar.path.swap')}
          title={t('scholar.path.swap')}
          className={`inline-flex h-11 w-11 items-center justify-center self-end border border-stone-300 bg-[#fffdf9] text-stone-600 hover:border-orange-600 hover:text-orange-800 ${focusRing}`}
        >
          <ArrowLeftRight className="h-4 w-4" aria-hidden="true" />
        </button>
        <NodePicker
          label={t('scholar.path.target')}
          placeholder={t('scholar.path.targetPlaceholder')}
          index={index}
          value={targetId}
          valueLabel={targetId ? labelOf(targetId) : ''}
          onChange={(id) => {
            setTargetId(id);
            setResult({ status: 'idle' });
          }}
          invalid={attempted && !targetId}
        />
        <button
          type="submit"
          className={`inline-flex min-h-11 items-center justify-center gap-2 bg-stone-900 px-5 font-body text-sm font-semibold text-[#fffdf9] hover:bg-orange-900 ${focusRing} focus-visible:ring-offset-2`}
        >
          <Route className="h-4 w-4" aria-hidden="true" /> {t('scholar.path.find')}
        </button>
      </form>
      {attempted && (!sourceId || !targetId) && (
        <p role="alert" className="font-body text-sm text-red-800">{t('scholar.path.needBoth')}</p>
      )}

      <div aria-live="polite">
        {result.status === 'none' && (
          <p className="border border-dashed border-stone-300 px-4 py-8 font-reader text-lg leading-7 text-stone-600">
            {t('scholar.path.none', { source: labelOf(result.source), target: labelOf(result.target), depth: MAX_PATH_DEPTH })}
          </p>
        )}
        {result.status === 'found' && result.steps.length === 0 && (
          <p className="font-reader text-lg text-stone-600">{t('scholar.path.same')}</p>
        )}
        {result.status === 'found' && result.steps.length > 0 && (
          <section aria-labelledby="scholar-path-result">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-300 pb-3">
              <h3 id="scholar-path-result" className="font-body text-sm font-semibold text-stone-900">
                {t('scholar.path.found', { count: result.steps.length })}
              </h3>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={addToThread}
                  className={`inline-flex min-h-11 items-center gap-2 border border-orange-700 px-3 font-body text-xs font-semibold text-orange-800 hover:bg-orange-50 ${focusRing}`}
                >
                  <BookmarkPlus className="h-4 w-4" aria-hidden="true" /> {t('scholar.path.addThread')}
                </button>
                <button
                  type="button"
                  onClick={() => setCompareIds([result.source, result.target])}
                  className={`inline-flex min-h-11 items-center gap-2 border border-teal-700 px-3 font-body text-xs font-semibold text-teal-800 hover:bg-teal-50 ${focusRing}`}
                >
                  {t('scholar.path.compareEnds')}
                </button>
              </div>
            </div>
            <ol className="mt-4">
              {pathIds.map((id, position) => {
                const meta = metaById.get(id);
                const step = result.steps[position];
                return (
                  <li key={`${id}-${position}`} className="relative grid grid-cols-[2rem_1fr] gap-x-3">
                    <span
                      aria-hidden="true"
                      className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full font-body text-xs font-bold ${position === 0 || position === pathIds.length - 1 ? 'bg-orange-800 text-[#fffdf9]' : 'border border-stone-400 bg-[#fffdf9] text-stone-700'}`}
                    >
                      {position + 1}
                    </span>
                    <div className="min-w-0 pb-1">
                      <button
                        type="button"
                        onClick={() => selectPrimary(id)}
                        aria-current={state.primarySelection === id ? 'true' : undefined}
                        className={`min-h-8 text-left font-display text-xl leading-tight text-stone-950 hover:text-orange-800 ${focusRing}`}
                      >
                        {meta?.label ?? id}
                      </button>
                      {meta && (
                        <p className="font-body text-xs text-stone-500">
                          {labels.nodeType(meta)} · {labels.period(meta.periodLabel)}
                          {meta.greekTerm || meta.latinTerm ? <span className="ml-2 font-reader text-sm text-stone-600">{meta.greekTerm || meta.latinTerm}</span> : null}
                        </p>
                      )}
                    </div>
                    {step && (
                      <>
                        <span aria-hidden="true" className="mx-auto h-full w-px bg-stone-300" />
                        <p className="flex items-center gap-1.5 py-3 font-body text-[11px] uppercase tracking-[0.08em] text-teal-800">
                          {step.forward
                            ? <ArrowDown className="h-3.5 w-3.5" aria-hidden="true" />
                            : <ArrowUp className="h-3.5 w-3.5" aria-hidden="true" />}
                          <span>{labels.relation(step.relation)}</span>
                          <span className="normal-case tracking-normal text-stone-500">
                            {step.forward ? t('scholar.path.forward') : t('scholar.path.backward')}
                          </span>
                        </p>
                      </>
                    )}
                  </li>
                );
              })}
            </ol>
          </section>
        )}
      </div>
    </div>
  );
}

interface NodePickerProps {
  label: string;
  placeholder: string;
  index: ReadonlyArray<ScholarRow>;
  value: string | null;
  valueLabel: string;
  onChange: (id: string | null) => void;
  invalid: boolean;
}

function NodePicker({ label, placeholder, index, value, valueLabel, onChange, invalid }: NodePickerProps) {
  const { t } = useTranslation();
  const labels = useScholarLabels();
  const inputId = useId();
  const listId = useId();
  const [text, setText] = useState(valueLabel);
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const deferred = useDeferredValue(text);
  const blurTimer = useRef(0);

  useEffect(() => {
    setText(valueLabel);
  }, [valueLabel]);
  useEffect(() => () => window.clearTimeout(blurTimer.current), []);

  const suggestions = useMemo(() => {
    if (!open || deferred.trim().length < 2) return [];
    return searchRows(index, deferred)
      .sort((a, b) => b.score - a.score)
      .slice(0, SUGGESTIONS)
      .map((entry) => entry.row.node);
  }, [deferred, index, open]);

  const choose = (node: AtlasNodeMeta) => {
    onChange(node.id);
    setText(node.label);
    setOpen(false);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setOpen(true);
      setHighlight((current) => Math.min(suggestions.length - 1, current + 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlight((current) => Math.max(0, current - 1));
    } else if (event.key === 'Enter' && open && suggestions[highlight]) {
      event.preventDefault();
      choose(suggestions[highlight]);
    } else if (event.key === 'Escape') {
      setOpen(false);
    }
  };

  const expanded = open && suggestions.length > 0;
  return (
    <div className="relative min-w-0">
      <label htmlFor={inputId} className="mb-1 block font-body text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500">
        {label}
      </label>
      <div className="relative">
        <input
          id={inputId}
          type="text"
          role="combobox"
          autoComplete="off"
          aria-autocomplete="list"
          aria-expanded={expanded}
          aria-controls={listId}
          aria-activedescendant={expanded ? `${listId}-${highlight}` : undefined}
          aria-invalid={invalid || undefined}
          value={text}
          placeholder={placeholder}
          onChange={(event) => {
            setText(event.target.value);
            setOpen(true);
            setHighlight(0);
            if (value) onChange(null);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => {
            blurTimer.current = window.setTimeout(() => setOpen(false), 120);
          }}
          onKeyDown={onKeyDown}
          className={`min-h-11 w-full border bg-[#fffdf9] pl-3 pr-10 font-body text-base text-stone-900 placeholder:text-stone-400 focus:border-orange-700 focus:outline-none focus:ring-1 focus:ring-orange-700 ${invalid ? 'border-red-700' : value ? 'border-stone-500' : 'border-stone-300'}`}
        />
        {text && (
          <button
            type="button"
            aria-label={t('scholar.path.clearField', { label })}
            onClick={() => {
              setText('');
              onChange(null);
            }}
            className={`absolute right-0 top-0 flex h-11 w-11 items-center justify-center text-stone-400 hover:text-stone-800 ${focusRing}`}
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>
      <ul
        id={listId}
        role="listbox"
        aria-label={label}
        className={`${expanded ? 'block' : 'hidden'} absolute inset-x-0 top-full z-30 mt-1 max-h-80 overflow-auto border border-stone-300 bg-[#fffdf9] shadow-[0_12px_32px_rgba(72,52,36,0.14)]`}
      >
        {suggestions.map((node, position) => (
          <li
            key={node.id}
            id={`${listId}-${position}`}
            role="option"
            aria-selected={position === highlight}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => choose(node)}
            onMouseEnter={() => setHighlight(position)}
            className={`flex min-h-11 cursor-pointer flex-col justify-center px-3 py-1.5 font-body text-sm ${position === highlight ? 'bg-orange-50 text-orange-950' : 'text-stone-800'}`}
          >
            <span className="truncate">{node.label}</span>
            <span className="truncate text-xs text-stone-500">
              {labels.nodeType(node)} · {labels.period(node.periodLabel)} · {t('scholar.path.linksCount', { count: node.degree, formatted: labels.number(node.degree) })}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default memo(PathInspectorPanelComponent);
