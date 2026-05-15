import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Loader2, X, FileText, CheckCircle2 } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { cn } from '../../utils/cn';
import type { ContributionStatus } from '../../api/contributions';

interface ProcessingStatusProps {
  contributionId: string;
  status: ContributionStatus;
  estimatedSeconds: number;
  startedAt: number;
  uploadProgress: number;
  metadata: {
    title?: string;
    authors?: string;
    doi?: string;
    publicationYear?: number;
  };
  onCancel: () => void;
}

type Phase = 'upload' | 'extract' | 'relevance' | 'proposals';

function statusToPhase(status: ContributionStatus, uploadProgress: number): Phase {
  if (status === 'uploaded') {
    return uploadProgress < 1 ? 'upload' : 'extract';
  }
  if (status === 'processing') return 'relevance';
  return 'proposals';
}

const PHASES: Phase[] = ['upload', 'extract', 'relevance', 'proposals'];

export default function ProcessingStatus({
  contributionId,
  status,
  estimatedSeconds,
  startedAt,
  uploadProgress,
  metadata,
  onCancel,
}: ProcessingStatusProps) {
  const { t } = useTranslation();
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => {
      setElapsed((Date.now() - startedAt) / 1000);
    }, 500);
    return () => window.clearInterval(id);
  }, [startedAt]);

  const currentPhase = statusToPhase(status, uploadProgress);
  const currentIndex = PHASES.indexOf(currentPhase);

  const progress = useMemo(() => {
    if (currentPhase === 'upload') return uploadProgress * 0.25;
    if (currentPhase === 'extract') return 0.25 + 0.25 * Math.min(1, elapsed / 8);
    if (currentPhase === 'relevance') {
      const base = 0.5;
      const target = 0.85;
      const ratio = Math.min(1, elapsed / Math.max(8, estimatedSeconds));
      return base + (target - base) * ratio;
    }
    return 0.95;
  }, [currentPhase, uploadProgress, elapsed, estimatedSeconds]);

  const remaining = Math.max(0, Math.ceil(estimatedSeconds - elapsed));

  return (
    <div className="mx-auto max-w-3xl">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-700">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-stone-900">
              {t('contribute.processing.title')}
            </h2>
            <p className="text-sm text-stone-600">
              {t('contribute.processing.subtitle')}
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
          aria-label={t('contribute.processing.cancel')}
        >
          <X className="mr-1 h-4 w-4" aria-hidden="true" />
          {t('contribute.processing.cancel')}
        </Button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mt-6 rounded-xl border border-amber-200 bg-amber-50/40 p-5"
      >
        <div className="flex items-center gap-2 text-sm font-medium text-stone-800">
          <FileText className="h-4 w-4 text-amber-700" aria-hidden="true" />
          <span className="truncate">
            {metadata.title || t('contribute.processing.untitled')}
          </span>
        </div>
        {metadata.authors && (
          <p className="mt-1 text-sm text-stone-700">{metadata.authors}</p>
        )}
        <div className="mt-2 flex flex-wrap gap-2 text-xs text-stone-600">
          {metadata.doi && (
            <span className="rounded-full bg-white/70 px-2 py-0.5">
              DOI: {metadata.doi}
            </span>
          )}
          {metadata.publicationYear && (
            <span className="rounded-full bg-white/70 px-2 py-0.5">
              {metadata.publicationYear}
            </span>
          )}
          <span className="rounded-full bg-white/70 px-2 py-0.5 font-mono">
            #{contributionId.slice(0, 8)}
          </span>
        </div>
      </motion.div>

      <div className="mt-6">
        <div className="mb-2 flex items-baseline justify-between">
          <span className="text-sm font-medium text-stone-700">
            {t(`contribute.processing.phases.${currentPhase}`)}
          </span>
          <span className="text-sm text-stone-500">
            {t('contribute.processing.remaining', { seconds: remaining })}
          </span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-stone-200">
          <motion.div
            className="h-full bg-amber-500"
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, progress * 100)}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        </div>
        <ol className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs">
          {PHASES.map((phase, index) => {
            const done = index < currentIndex;
            const active = index === currentIndex;
            return (
              <li
                key={phase}
                className={cn(
                  'flex items-center gap-1.5',
                  done && 'text-emerald-700',
                  active && 'text-amber-700 font-semibold',
                  !done && !active && 'text-stone-400'
                )}
              >
                {done ? (
                  <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                ) : (
                  <span
                    className={cn(
                      'inline-block h-2 w-2 rounded-full',
                      active ? 'bg-amber-500' : 'bg-stone-300'
                    )}
                    aria-hidden="true"
                  />
                )}
                <span>{t(`contribute.processing.phases.${phase}`)}</span>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
