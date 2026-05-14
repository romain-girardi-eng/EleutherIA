/**
 * BibliographyPane — persistent session bibliography.
 *
 * Tabs:  Primary / Secondary / Notes
 * Per-entry: editable annotation, drag handle (reorder), remove
 * Footer: export buttons (Markdown / LaTeX / BibTeX / Zotero / RIS / Word /
 *         share URL) backed by /api/graphrag/query/{trace_id}/export
 *
 * Drag-and-drop uses a minimal pointer-based implementation rather than
 * pulling in @dnd-kit; the surface area is small enough that the extra
 * dependency isn't worth it.
 */

import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import {
  BookMarked,
  ExternalLink,
  FileDown,
  Library,
  StickyNote,
  Trash2,
} from 'lucide-react';
import { cn } from '../../../lib/utils';
import { doctoralApi } from '../../../services/doctoralApi';
import type {
  BibliographyEntry,
  UseBibliographyReturn,
} from '../../../hooks/useBibliography';

type Tab = 'primary' | 'secondary' | 'notes';

interface Props {
  bibliography: UseBibliographyReturn;
  traceId?: string;
  shareUrl?: string;
  className?: string;
}

const EXPORT_FORMATS: ReadonlyArray<{
  fmt: 'markdown' | 'latex' | 'bibtex' | 'zotero' | 'ris' | 'docx';
  labelKey: string;
}> = [
  { fmt: 'markdown', labelKey: 'research.doctoral.export.markdown' },
  { fmt: 'latex', labelKey: 'research.doctoral.export.latex' },
  { fmt: 'bibtex', labelKey: 'research.doctoral.export.bibtex' },
  { fmt: 'zotero', labelKey: 'research.doctoral.export.zotero' },
  { fmt: 'ris', labelKey: 'research.doctoral.export.ris' },
  { fmt: 'docx', labelKey: 'research.doctoral.export.docx' },
];

export function BibliographyPane({
  bibliography,
  traceId,
  shareUrl,
  className,
}: Props) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>('primary');
  const [copied, setCopied] = useState(false);

  const list = useMemo<BibliographyEntry[]>(() => {
    if (tab === 'primary') return bibliography.primary;
    if (tab === 'secondary') return bibliography.secondary;
    return bibliography.notes;
  }, [tab, bibliography]);

  const tabs: { id: Tab; labelKey: string; count: number; Icon: typeof Library }[] = [
    { id: 'primary', labelKey: 'research.doctoral.bibliography.tabs.primary', count: bibliography.primary.length, Icon: Library },
    { id: 'secondary', labelKey: 'research.doctoral.bibliography.tabs.secondary', count: bibliography.secondary.length, Icon: BookMarked },
    { id: 'notes', labelKey: 'research.doctoral.bibliography.tabs.notes', count: bibliography.notes.length, Icon: StickyNote },
  ];

  const handleReorder = useCallback(
    (next: BibliographyEntry[]) => {
      bibliography.reorder(next.map((e) => e.id));
    },
    [bibliography],
  );

  const handleCopy = useCallback(async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // No clipboard access — fail silently.
    }
  }, [shareUrl]);

  return (
    <section
      aria-labelledby="bibliography-header"
      className={cn(
        'flex h-full flex-col rounded-2xl border border-stone-200/70 bg-white/70 backdrop-blur-sm',
        className,
      )}
    >
      <header className="shrink-0 border-b border-stone-200/50 px-4 py-2.5">
        <h2
          id="bibliography-header"
          className="text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500"
        >
          {t('research.doctoral.bibliography.title')}
        </h2>
      </header>

      <div className="flex shrink-0 border-b border-stone-200/50" role="tablist">
        {tabs.map(({ id, labelKey, count, Icon }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
            className={cn(
              'flex flex-1 items-center justify-center gap-1.5 border-b-2 px-2 py-2 text-[11px] font-medium transition',
              tab === id
                ? 'border-amber-400 text-amber-800'
                : 'border-transparent text-stone-500 hover:text-stone-700',
            )}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            {t(labelKey)}
            <span className="ml-0.5 rounded-full bg-stone-100 px-1.5 text-[10px] text-stone-500">
              {count}
            </span>
          </button>
        ))}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        {list.length === 0 ? (
          <p className="px-1 py-6 text-center text-[12px] italic text-stone-400">
            {t('research.doctoral.bibliography.empty')}
          </p>
        ) : (
          <Reorder.Group
            axis="y"
            values={list}
            onReorder={handleReorder}
            className="space-y-2"
          >
            <AnimatePresence initial={false}>
              {list.map((entry) => (
                <Reorder.Item
                  key={entry.id}
                  value={entry}
                  className="group rounded-xl border border-stone-200/70 bg-white/70 p-2.5 shadow-sm"
                >
                  <BibliographyEntryRow
                    entry={entry}
                    onAnnotate={(text) => bibliography.annotate(entry.id, text)}
                    onRemove={() => bibliography.remove(entry.id)}
                  />
                </Reorder.Item>
              ))}
            </AnimatePresence>
          </Reorder.Group>
        )}
      </div>

      <footer className="shrink-0 space-y-2 border-t border-stone-200/50 px-3 py-2.5">
        {traceId ? (
          <div className="flex flex-wrap gap-1.5">
            {EXPORT_FORMATS.map(({ fmt, labelKey }) => (
              <a
                key={fmt}
                href={doctoralApi.buildExportUrl(traceId, fmt)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 rounded-full border border-stone-200 bg-white px-2.5 py-1 text-[11px] font-medium text-stone-700 hover:border-amber-300 hover:bg-amber-50"
              >
                <FileDown className="h-3 w-3" aria-hidden="true" />
                {t(labelKey)}
              </a>
            ))}
          </div>
        ) : (
          <p className="text-[11px] italic text-stone-400">
            {t('research.doctoral.bibliography.exportLocked')}
          </p>
        )}
        {shareUrl && (
          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-stone-200 bg-white px-2.5 py-1.5 text-[11px] font-medium text-stone-700 hover:bg-stone-50"
          >
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
            {copied
              ? t('research.doctoral.bibliography.copied')
              : t('research.doctoral.bibliography.shareUrl')}
          </button>
        )}
      </footer>
    </section>
  );
}

interface RowProps {
  entry: BibliographyEntry;
  onAnnotate: (text: string) => void;
  onRemove: () => void;
}

function BibliographyEntryRow({ entry, onAnnotate, onRemove }: RowProps) {
  const { t } = useTranslation();
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      className="space-y-1"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-semibold text-stone-900">
            {entry.title}
          </p>
          {(entry.author || entry.year) && (
            <p className="text-[11px] text-stone-500">
              {[entry.author, entry.year].filter(Boolean).join(' · ')}
            </p>
          )}
          {entry.cts_urn && (
            <p className="truncate font-mono text-[10px] text-amber-700">
              {entry.cts_urn}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onRemove}
          aria-label={t('research.doctoral.actions.remove')}
          className="shrink-0 rounded-full p-1 text-stone-400 opacity-0 transition group-hover:opacity-100 hover:bg-rose-50 hover:text-rose-600"
        >
          <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      </div>
      {entry.excerpt && (
        <p className="line-clamp-2 text-[11px] italic text-stone-600">
          {entry.excerpt}
        </p>
      )}
      <textarea
        value={entry.annotation}
        onChange={(e) => onAnnotate(e.target.value)}
        placeholder={t('research.doctoral.bibliography.annotationPlaceholder')}
        rows={2}
        className="w-full resize-none rounded-md border border-stone-200 bg-white/70 px-2 py-1 text-[12px] text-stone-700 placeholder:text-stone-400 focus:border-amber-300 focus:outline-none focus:ring-1 focus:ring-amber-200"
      />
    </motion.div>
  );
}

export default BibliographyPane;
