/**
 * MethodologyNotesPane — surfaces the agent's methodology flags, citation
 * verdicts, and counter-evidence findings, with anchor links that scroll
 * the affected text into view.
 *
 * Data source: the AgentEvent stream — `methodology_flagged`,
 * `citation_verified`, `counter_evidence_found` events. These are filtered
 * from the events array passed by the parent.
 */

import { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  AlertTriangle,
  CheckCircle2,
  Compass,
  Scale,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import { cn } from '../../../lib/utils';
import type {
  AgentEvent,
  CitationVerifiedEvent,
  CounterEvidenceFoundEvent,
  CounterEvidenceTestimonyType,
  MethodologyFlaggedEvent,
} from '../../../types/agent-events';

/** Glyph + accent class per v2 testimony dimension. Plain emoji glyphs keep
 *  the row scannable in the dense Methodology pane. */
const TESTIMONY_DIMENSION_META: Record<
  CounterEvidenceTestimonyType,
  { glyph: string; tone: string }
> = {
  contradiction: { glyph: '⚔️', tone: 'text-rose-700' },
  qualification: { glyph: '◐', tone: 'text-amber-700' },
  alternative: { glyph: '↔', tone: 'text-sky-700' },
  scholar_critique: { glyph: '🎓', tone: 'text-violet-700' },
  period_shift: { glyph: '⏳', tone: 'text-orange-700' },
  doxographical_alternative: { glyph: '📜', tone: 'text-teal-700' },
  consensus_dispute: { glyph: '⚖️', tone: 'text-indigo-700' },
};

interface Props {
  events: AgentEvent[];
  /** Called when a flag is clicked; parent scrolls/highlights the affected
   *  passage in the answer. */
  onAnchorClick?: (passageId: string) => void;
  className?: string;
}

const severityClass = (sev: MethodologyFlaggedEvent['severity']): string => {
  switch (sev) {
    case 'blocker':
      return 'bg-rose-50 text-rose-800 ring-rose-200';
    case 'major':
      return 'bg-amber-50 text-amber-800 ring-amber-200';
    default:
      return 'bg-stone-50 text-stone-700 ring-stone-200';
  }
};

const severityLabelKey = (sev: MethodologyFlaggedEvent['severity']): string =>
  ({
    blocker: 'research.doctoral.methodology.severity.blocker',
    major: 'research.doctoral.methodology.severity.major',
    minor: 'research.doctoral.methodology.severity.minor',
  })[sev];

const flagTypeLabelKey = (
  flag: MethodologyFlaggedEvent['flag_type'],
): string =>
  ({
    anachronism: 'research.doctoral.methodology.flagType.anachronism',
    source_criticism: 'research.doctoral.methodology.flagType.source_criticism',
    scholarly_consensus:
      'research.doctoral.methodology.flagType.scholarly_consensus',
    period_appropriateness:
      'research.doctoral.methodology.flagType.period_appropriateness',
  })[flag];

export function MethodologyNotesPane({
  events,
  onAnchorClick,
  className,
}: Props) {
  const { t } = useTranslation();

  const flags = useMemo<MethodologyFlaggedEvent[]>(
    () =>
      events.filter(
        (e): e is MethodologyFlaggedEvent => e.type === 'methodology_flagged',
      ),
    [events],
  );

  const verdicts = useMemo<CitationVerifiedEvent[]>(
    () =>
      events.filter(
        (e): e is CitationVerifiedEvent => e.type === 'citation_verified',
      ),
    [events],
  );

  const counters = useMemo<CounterEvidenceFoundEvent[]>(
    () =>
      events.filter(
        (e): e is CounterEvidenceFoundEvent =>
          e.type === 'counter_evidence_found',
      ),
    [events],
  );

  const empty =
    flags.length === 0 && verdicts.length === 0 && counters.length === 0;

  return (
    <section
      aria-labelledby="methodology-notes-title"
      className={cn(
        'flex h-full flex-col rounded-2xl border border-stone-200/70 bg-white/70 backdrop-blur-sm',
        className,
      )}
    >
      <header className="shrink-0 border-b border-stone-200/50 px-4 py-2.5">
        <h2
          id="methodology-notes-title"
          className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-stone-500"
        >
          <Compass className="h-3.5 w-3.5 text-amber-700" aria-hidden="true" />
          {t('research.doctoral.methodology.title')}
        </h2>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        {empty && (
          <p className="px-1 py-6 text-center text-[12px] italic text-stone-400">
            {t('research.doctoral.methodology.empty')}
          </p>
        )}

        {flags.length > 0 && (
          <section className="mb-3">
            <h3 className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
              {t('research.doctoral.methodology.flagsHeader')}
            </h3>
            <ul className="space-y-1.5">
              <AnimatePresence initial={false}>
                {flags.map((f, idx) => (
                  <motion.li
                    key={`flag-${idx}`}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="rounded-lg border border-stone-200/70 bg-white/80 p-2.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span
                        className={cn(
                          'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ring-1',
                          severityClass(f.severity),
                        )}
                      >
                        <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                        {t(severityLabelKey(f.severity))}
                      </span>
                      <span className="text-[10px] uppercase tracking-wider text-stone-400">
                        {t(flagTypeLabelKey(f.flag_type))}
                      </span>
                    </div>
                    <p className="mt-1.5 text-[12.5px] text-stone-800">
                      {f.issue}
                    </p>
                    <p className="mt-1 rounded-md bg-amber-50/60 px-2 py-1 text-[11px] italic text-amber-900">
                      → {f.suggested_revision}
                    </p>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>
          </section>
        )}

        {verdicts.length > 0 && (
          <section className="mb-3">
            <h3 className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
              {t('research.doctoral.methodology.verdictsHeader')}
            </h3>
            <ul className="space-y-1">
              {verdicts.map((v, idx) => (
                <li
                  key={`verdict-${idx}`}
                  className={cn(
                    'flex items-start gap-2 rounded-md border px-2 py-1.5 text-[11.5px]',
                    v.verified
                      ? 'border-emerald-200 bg-emerald-50/50 text-emerald-800'
                      : 'border-rose-200 bg-rose-50/50 text-rose-800',
                  )}
                >
                  {v.verified ? (
                    <ShieldCheck
                      className="h-3.5 w-3.5 shrink-0"
                      aria-hidden="true"
                    />
                  ) : (
                    <ShieldAlert
                      className="h-3.5 w-3.5 shrink-0"
                      aria-hidden="true"
                    />
                  )}
                  <div className="min-w-0 flex-1">
                    <button
                      type="button"
                      onClick={() => onAnchorClick?.(v.passage_id)}
                      className="block truncate text-left font-mono text-[10px] underline-offset-2 hover:underline"
                    >
                      {v.passage_id}
                    </button>
                    {v.reason && <p className="mt-0.5">{v.reason}</p>}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}

        {counters.length > 0 && (
          <section>
            <h3 className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
              {t('research.doctoral.methodology.countersHeader')}
            </h3>
            <ul className="space-y-1">
              {counters.map((c, idx) => {
                const meta =
                  TESTIMONY_DIMENSION_META[c.testimony_type] ?? {
                    glyph: '·',
                    tone: 'text-stone-500',
                  };
                return (
                  <li
                    key={`counter-${idx}`}
                    className="rounded-md border border-stone-200/70 bg-white/80 px-2 py-1.5 text-[11.5px] text-stone-700"
                  >
                    <div className="mb-0.5 flex items-center gap-1 text-[10px] uppercase tracking-wider text-stone-500">
                      <Scale className="h-3 w-3" aria-hidden="true" />
                      <span
                        aria-label={c.testimony_type}
                        className={cn('text-[12px] leading-none', meta.tone)}
                      >
                        {meta.glyph}
                      </span>
                      <span className={meta.tone}>{c.testimony_type}</span>
                      <span>·</span>
                      <span>{c.force}</span>
                      <span>·</span>
                      <span className="truncate">{c.source}</span>
                    </div>
                    <p className="italic">{c.excerpt}</p>
                  </li>
                );
              })}
            </ul>
          </section>
        )}
      </div>

      <footer className="shrink-0 border-t border-stone-200/50 px-3 py-2 text-[10px] uppercase tracking-wider text-stone-400">
        <div className="flex justify-between">
          <span className="flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" aria-hidden="true" />
            {flags.length} {t('research.doctoral.methodology.flagsShort')}
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
            {verdicts.filter((v) => v.verified).length} /{' '}
            {verdicts.length} {t('research.doctoral.methodology.verifiedShort')}
          </span>
          <span className="flex items-center gap-1">
            <XCircle className="h-3 w-3" aria-hidden="true" />
            {counters.length} {t('research.doctoral.methodology.countersShort')}
          </span>
        </div>
      </footer>
    </section>
  );
}

export default MethodologyNotesPane;
