import { useEffect, useMemo, useState } from 'react';
import { Clock3, ScrollText, X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../utils/cn';
import { formatWaitingElapsed, resolveWaitingPhase } from './waitingExperienceUtils';

const WAITING_LINE_KEYS = [
  'capacity',
  'lazyArgument',
  'carneades',
  'epictetus',
  'origen',
  'alexander',
  'chrysippus',
] as const;

const REASSURANCE_AFTER_MS = 45_000;
const REASSURANCE_PERIOD_MS = 45_000;
const REASSURANCE_VISIBLE_MS = 15_000;
const LINE_ROTATION_MS = 20_000;

export function ScholarlyWaitExpectation({ className }: { className?: string }) {
  const { t } = useTranslation();

  return (
    <p
      className={cn(
        'flex items-center justify-center gap-2 px-2 text-center text-[11px] leading-5 text-stone-500',
        className,
      )}
      data-testid="scholarly-wait-expectation"
    >
      <Clock3 className="h-3.5 w-3.5 shrink-0 text-amber-700" aria-hidden="true" />
      <span>{t('graphRagUi.waiting.expectation')}</span>
    </p>
  );
}

interface WaitingExperienceProps {
  startedAt: number;
  stage?: string;
  statusMessage?: string;
  className?: string;
}

export default function WaitingExperience({
  startedAt,
  stage,
  statusMessage,
  className,
}: WaitingExperienceProps) {
  const { t } = useTranslation();
  const [now, setNow] = useState(() => Date.now());
  const [lineIndex, setLineIndex] = useState(0);
  const [wisdomVisible, setWisdomVisible] = useState(true);
  const phase = useMemo(
    () => resolveWaitingPhase(stage, statusMessage),
    [stage, statusMessage],
  );
  const [phaseStartedAt, setPhaseStartedAt] = useState(startedAt);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    setPhaseStartedAt(Date.now());
  }, [phase]);

  useEffect(() => {
    if (!wisdomVisible) return undefined;
    const timer = window.setInterval(() => {
      setLineIndex((current) => (current + 1) % WAITING_LINE_KEYS.length);
    }, LINE_ROTATION_MS);
    return () => window.clearInterval(timer);
  }, [wisdomVisible]);

  const elapsed = formatWaitingElapsed(now - startedAt);
  const phaseElapsed = now - phaseStartedAt;
  const phaseHasRunLong =
    phaseElapsed >= REASSURANCE_AFTER_MS &&
    (phaseElapsed - REASSURANCE_AFTER_MS) % REASSURANCE_PERIOD_MS <
      REASSURANCE_VISIBLE_MS;
  const waitingLine = t(
    `graphRagUi.waiting.lines.${WAITING_LINE_KEYS[lineIndex]}`,
  );

  return (
    <section
      className={cn('w-full max-w-xl px-2', className)}
      aria-label={t('graphRagUi.waiting.currentPhase')}
      data-testid="waiting-experience"
    >
      <div className="border-y border-amber-200/70 bg-amber-50/45 px-4 py-4 sm:px-5">
        <div className="flex items-start justify-between gap-5">
          <div className="flex min-w-0 items-start gap-3">
            <span className="relative mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-amber-200 bg-white text-amber-800">
              <ScrollText className="h-4 w-4" aria-hidden="true" />
              <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 animate-pulse rounded-full border-2 border-amber-50 bg-amber-500 motion-reduce:animate-none" />
            </span>
            <div className="min-w-0 text-left">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-800/75">
                {t('graphRagUi.waiting.currentPhase')}
              </p>
              <p className="mt-1 font-serif text-sm font-semibold leading-5 text-stone-800" data-testid="waiting-phase">
                {t(`graphRagUi.waiting.phases.${phase}`)}
              </p>
            </div>
          </div>
          <div className="shrink-0 text-right">
            <p className="text-[10px] uppercase tracking-[0.14em] text-stone-400">
              {t('graphRagUi.waiting.elapsed')}
            </p>
            <time
              className="mt-1 block font-mono text-sm font-semibold tabular-nums text-stone-700"
              dateTime={`PT${Math.max(0, Math.floor((now - startedAt) / 1000))}S`}
              data-testid="waiting-elapsed"
            >
              {elapsed}
            </time>
          </div>
        </div>

        {phaseHasRunLong && (
          <p
            className="mt-3 border-l border-amber-400 pl-3 text-left text-xs leading-5 text-amber-900"
            role="status"
            data-testid="waiting-reassurance"
          >
            {t('graphRagUi.waiting.reassurance')}
          </p>
        )}
      </div>

      {wisdomVisible && (
        <div className="relative px-5 pb-2 pt-4 text-left" data-testid="waiting-wisdom">
          <p className="pr-7 font-serif text-[11px] italic leading-5 text-stone-500">
            {waitingLine}
          </p>
          <button
            type="button"
            onClick={() => setWisdomVisible(false)}
            aria-label={t('graphRagUi.waiting.dismissWisdom')}
            title={t('graphRagUi.waiting.dismissWisdom')}
            className="absolute right-3 top-3 inline-flex h-7 w-7 items-center justify-center rounded-full text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500"
          >
            <X className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>
      )}
    </section>
  );
}
