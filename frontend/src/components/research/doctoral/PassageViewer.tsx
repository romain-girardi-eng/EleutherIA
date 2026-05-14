/**
 * PassageViewer — modal slide-over for inspecting a single ancient passage.
 *
 * Fetches three Y2 endpoints in parallel:
 *   - /api/passages/{id}                 — full passage with provenance
 *   - /api/works/{id}/section?around=…   — surrounding context (±1 by default)
 *   - /api/kg/nodes/{id}/neighbors       — 1-hop KG graph
 *
 * Renders the Greek/Latin original, transliteration, translation (with a
 * provenance badge — "AI batch" vs "Crisp 2000" etc.), CTS URN linked to
 * Scaife, edition info, surrounding context, KG neighbors grouped by edge
 * type, and the scholars who cite the passage (incoming
 * `cites_primary_source` edges).
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  BookOpen,
  ExternalLink,
  Loader2,
  Network,
  Quote,
  Save,
  X,
} from 'lucide-react';
import { cn } from '../../../lib/utils';
import { doctoralApi } from '../../../services/doctoralApi';
import type {
  KGNeighbor,
  PassageDetail,
  SectionResponse,
  TranslationProvenance,
} from '../../../types/doctoral';
import type { BibliographyEntry } from '../../../hooks/useBibliography';
import { useFocusTrap } from '../../../hooks/useFocusTrap';

interface Props {
  passageId: string;
  open: boolean;
  onClose: () => void;
  onSaveToBibliography?: (entry: Omit<BibliographyEntry, 'added_at'>) => void;
  onOpenInCosmograph?: (nodeId: string) => void;
}

const provenanceLabel = (p: TranslationProvenance | undefined, t: (k: string) => string): string => {
  switch (p) {
    case 'ai_batch':
      return t('research.doctoral.provenance.ai_batch');
    case 'crisp_2000':
      return t('research.doctoral.provenance.crisp_2000');
    case 'loeb':
      return t('research.doctoral.provenance.loeb');
    case 'editor':
      return t('research.doctoral.provenance.editor');
    default:
      return t('research.doctoral.provenance.unknown');
  }
};

const provenanceClass = (p: TranslationProvenance | undefined): string => {
  switch (p) {
    case 'crisp_2000':
    case 'loeb':
    case 'editor':
      return 'bg-emerald-50 text-emerald-700 ring-emerald-200';
    case 'ai_batch':
      return 'bg-amber-50 text-amber-800 ring-amber-200';
    default:
      return 'bg-stone-100 text-stone-600 ring-stone-200';
  }
};

const scaifeUrl = (urn: string): string =>
  `https://scaife.perseus.org/reader/${encodeURIComponent(urn)}/`;

export function PassageViewer({
  passageId,
  open,
  onClose,
  onSaveToBibliography,
  onOpenInCosmograph,
}: Props) {
  const { t } = useTranslation();
  const [passage, setPassage] = useState<PassageDetail | null>(null);
  const [section, setSection] = useState<SectionResponse | null>(null);
  const [neighbors, setNeighbors] = useState<KGNeighbor[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const focusRef = useFocusTrap(open);

  useEffect(() => {
    if (!open || !passageId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setPassage(null);
    setSection(null);
    setNeighbors([]);

    const run = async (): Promise<void> => {
      try {
        const p = await doctoralApi.getPassage(passageId);
        if (cancelled) return;
        setPassage(p);

        const [sec, neigh] = await Promise.all([
          p.work_id && p.work_id !== 'unknown'
            ? doctoralApi.getSection(p.work_id, passageId, 1, 1)
            : Promise.resolve({
                before: [],
                passage: { passage_id: passageId, text_original: p.text_original },
                after: [],
              } as SectionResponse),
          doctoralApi.getNeighbors(passageId),
        ]);
        if (cancelled) return;
        setSection(sec);
        setNeighbors(neigh.neighbors);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [open, passageId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === 'Escape' && open) onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const grouped = useMemo(() => {
    const map = new Map<string, KGNeighbor[]>();
    for (const n of neighbors) {
      const list = map.get(n.edge_type) ?? [];
      list.push(n);
      map.set(n.edge_type, list);
    }
    return map;
  }, [neighbors]);

  const citingScholars = useMemo(
    () =>
      neighbors.filter(
        (n) =>
          n.direction === 'incoming' &&
          (n.edge_type === 'cites_primary_source' || n.node_type === 'scholar'),
      ),
    [neighbors],
  );

  const handleSave = useCallback(() => {
    if (!passage || !onSaveToBibliography) return;
    onSaveToBibliography({
      id: `passage:${passage.passage_id}`,
      kind: 'primary',
      title: passage.work_label ?? passage.reference ?? passage.passage_id,
      cts_urn: passage.cts_urn,
      passage_id: passage.passage_id,
      excerpt: passage.text_original.slice(0, 240),
      edition: passage.edition,
      annotation: '',
      bibtex_key: passage.cts_urn ?? passage.passage_id,
    });
  }, [passage, onSaveToBibliography]);

  if (!open) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <motion.div
        key="panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="passage-viewer-title"
        ref={focusRef}
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', stiffness: 280, damping: 32 }}
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-2xl flex-col bg-[#fdfaf3] shadow-2xl ring-1 ring-stone-200"
      >
        <header className="flex shrink-0 items-start justify-between gap-3 border-b border-stone-200/70 px-5 py-3">
          <div className="min-w-0 flex-1">
            <h2
              id="passage-viewer-title"
              className="truncate font-display text-[15px] font-semibold text-stone-900"
            >
              {passage?.work_label ?? passage?.reference ?? passageId}
            </h2>
            {passage?.cts_urn && (
              <a
                href={scaifeUrl(passage.cts_urn)}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-0.5 inline-flex items-center gap-1 text-[11px] font-mono text-amber-700 hover:underline"
              >
                {passage.cts_urn}
                <ExternalLink className="h-3 w-3" aria-hidden="true" />
              </a>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('research.doctoral.close')}
            className="shrink-0 rounded-full p-1.5 text-stone-500 hover:bg-stone-100"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          {loading && (
            <div className="flex items-center gap-2 text-[13px] text-stone-500">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              {t('research.doctoral.loading')}
            </div>
          )}
          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50/70 px-3 py-2 text-[13px] text-rose-700">
              {error}
            </div>
          )}

          {passage && !loading && (
            <article className="space-y-5">
              <section aria-labelledby="passage-original">
                <h3
                  id="passage-original"
                  className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500"
                >
                  {t('research.doctoral.section.original')}
                </h3>
                <p className="whitespace-pre-wrap font-serif text-[15px] leading-7 text-stone-900">
                  {passage.text_original || (
                    <em className="text-stone-400">
                      {t('research.doctoral.section.noText')}
                    </em>
                  )}
                </p>
              </section>

              {passage.transliteration && (
                <section aria-labelledby="passage-translit">
                  <h3
                    id="passage-translit"
                    className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500"
                  >
                    {t('research.doctoral.section.transliteration')}
                  </h3>
                  <p className="font-mono text-[13px] italic leading-6 text-stone-700">
                    {passage.transliteration}
                  </p>
                </section>
              )}

              {passage.translation && (
                <section aria-labelledby="passage-translation">
                  <div className="mb-1.5 flex items-center gap-2">
                    <h3
                      id="passage-translation"
                      className="text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500"
                    >
                      {t('research.doctoral.section.translation')}
                    </h3>
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-[10px] font-medium ring-1',
                        provenanceClass(passage.translation_provenance),
                      )}
                      title={passage.translation_source}
                    >
                      {provenanceLabel(passage.translation_provenance, t)}
                    </span>
                  </div>
                  <p className="text-[14px] leading-7 text-stone-800">
                    {passage.translation}
                  </p>
                </section>
              )}

              {passage.edition && (
                <section
                  className="rounded-lg border border-stone-200/70 bg-white/60 px-3 py-2 text-[12px] text-stone-700"
                  aria-labelledby="passage-edition"
                >
                  <h3
                    id="passage-edition"
                    className="mb-0.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500"
                  >
                    {t('research.doctoral.section.edition')}
                  </h3>
                  <p>
                    {passage.edition}
                    {passage.editor ? `, ${passage.editor}` : ''}
                    {passage.year ? ` (${passage.year})` : ''}
                  </p>
                </section>
              )}

              {section && (section.before.length > 0 || section.after.length > 0) && (
                <section aria-labelledby="passage-context">
                  <h3
                    id="passage-context"
                    className="mb-1.5 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500"
                  >
                    <BookOpen className="h-3 w-3" aria-hidden="true" />
                    {t('research.doctoral.section.context')}
                  </h3>
                  <div className="space-y-2 border-l-2 border-amber-200 pl-3 text-[13px] leading-6 text-stone-600">
                    {section.before.map((p) => (
                      <p key={`b-${p.passage_id}`} className="italic">
                        {p.reference && (
                          <span className="mr-1 font-mono text-[11px] text-stone-400">
                            {p.reference}
                          </span>
                        )}
                        {p.text_original}
                      </p>
                    ))}
                    {section.after.map((p) => (
                      <p key={`a-${p.passage_id}`} className="italic">
                        {p.reference && (
                          <span className="mr-1 font-mono text-[11px] text-stone-400">
                            {p.reference}
                          </span>
                        )}
                        {p.text_original}
                      </p>
                    ))}
                  </div>
                </section>
              )}

              {grouped.size > 0 && (
                <section aria-labelledby="passage-neighbors">
                  <h3
                    id="passage-neighbors"
                    className="mb-1.5 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500"
                  >
                    <Network className="h-3 w-3" aria-hidden="true" />
                    {t('research.doctoral.section.neighbors')}
                  </h3>
                  <div className="space-y-2">
                    {[...grouped.entries()].map(([edgeType, list]) => (
                      <div key={edgeType}>
                        <p className="mb-0.5 text-[11px] font-mono text-amber-700">
                          {edgeType}
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {list.map((n) => (
                            <button
                              key={`${edgeType}-${n.node_id}`}
                              type="button"
                              onClick={() => onOpenInCosmograph?.(n.node_id)}
                              className="rounded-full border border-stone-200 bg-white/70 px-2.5 py-0.5 text-[11px] text-stone-700 hover:border-amber-300 hover:bg-amber-50"
                            >
                              <span className="mr-1 text-[9px] uppercase tracking-wider text-stone-400">
                                {n.node_type}
                              </span>
                              {n.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {citingScholars.length > 0 && (
                <section aria-labelledby="passage-scholars">
                  <h3
                    id="passage-scholars"
                    className="mb-1.5 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500"
                  >
                    <Quote className="h-3 w-3" aria-hidden="true" />
                    {t('research.doctoral.section.scholars')}
                  </h3>
                  <ul className="space-y-1 text-[13px] text-stone-700">
                    {citingScholars.map((s) => (
                      <li
                        key={`scholar-${s.node_id}`}
                        className="flex items-center justify-between"
                      >
                        <span>{s.label}</span>
                        <span className="text-[10px] uppercase tracking-wider text-stone-400">
                          {s.period}
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </article>
          )}
        </div>

        <footer className="flex shrink-0 items-center justify-end gap-2 border-t border-stone-200/70 bg-white/60 px-5 py-3">
          {onSaveToBibliography && (
            <button
              type="button"
              onClick={handleSave}
              disabled={!passage}
              className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-[12px] font-medium text-amber-800 hover:bg-amber-100 disabled:opacity-50"
            >
              <Save className="h-3.5 w-3.5" aria-hidden="true" />
              {t('research.doctoral.actions.saveToBibliography')}
            </button>
          )}
          {onOpenInCosmograph && passage && (
            <button
              type="button"
              onClick={() => onOpenInCosmograph(passage.passage_id)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-stone-300 bg-white px-3 py-1.5 text-[12px] font-medium text-stone-700 hover:bg-stone-50"
            >
              <Network className="h-3.5 w-3.5" aria-hidden="true" />
              {t('research.doctoral.actions.openInCosmograph')}
            </button>
          )}
        </footer>
      </motion.div>
    </AnimatePresence>
  );
}

export default PassageViewer;
