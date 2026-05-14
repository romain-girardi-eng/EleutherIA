import { useTranslation } from 'react-i18next';
import { ArrowRight, GitBranch } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { ProofChainStep, ProofTriple } from '../../types/graphrag';
import { shortenIri } from './iri';

interface ProofChainPanelProps {
  steps: readonly ProofChainStep[];
  className?: string;
}

interface TripleRowProps {
  triple: ProofTriple;
  emphasis?: 'premise' | 'conclusion';
}

function formatRuleKey(rule: string): string {
  return `claimLedger.rule.${rule}`;
}

function TripleRow({ triple, emphasis = 'premise' }: TripleRowProps) {
  const [subject, predicate, object] = triple;
  const subjectShort = shortenIri(subject);
  const predicateShort = shortenIri(predicate);
  const objectShort = shortenIri(object);

  const isConclusion = emphasis === 'conclusion';
  const tone = isConclusion
    ? 'border-emerald-200/80 bg-emerald-50/80 text-emerald-900'
    : 'border-stone-200/70 bg-white/85 text-stone-800';

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-1.5 rounded-2xl border px-2.5 py-1.5 font-mono text-[11px] leading-5',
        tone,
      )}
    >
      <span
        title={subjectShort.iri}
        className="rounded-md bg-stone-100/90 px-1.5 py-0.5 text-stone-700"
      >
        {subjectShort.display}
      </span>
      <ArrowRight aria-hidden="true" className="h-3 w-3 text-stone-400" />
      <span
        title={predicateShort.iri}
        className={cn(
          'rounded-md px-1.5 py-0.5 font-semibold',
          isConclusion ? 'bg-emerald-100/90 text-emerald-800' : 'bg-amber-50/90 text-amber-800',
        )}
      >
        {predicateShort.display}
      </span>
      <ArrowRight aria-hidden="true" className="h-3 w-3 text-stone-400" />
      <span
        title={objectShort.iri}
        className="rounded-md bg-stone-100/90 px-1.5 py-0.5 text-stone-700"
      >
        {objectShort.display}
      </span>
    </div>
  );
}

function StepCard({ step, index }: { step: ProofChainStep; index: number }) {
  const { t } = useTranslation();
  const ruleKey = formatRuleKey(step.rule);
  const ruleLabel = t(ruleKey, { defaultValue: step.rule });
  const confidence = Number.isFinite(step.confidence)
    ? `${Math.round(step.confidence * 100)}%`
    : '--';

  return (
    <article
      className="rounded-[18px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.97),rgba(252,249,244,0.95))] p-3 shadow-[0_10px_24px_-22px_rgba(120,53,15,0.35)]"
      aria-label={`${t('claimLedger.derivation')} ${index + 1}`}
    >
      <header className="flex flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200/80 bg-amber-50/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-700">
          <GitBranch aria-hidden="true" className="h-3 w-3" />
          {ruleLabel}
        </span>
        <span className="inline-flex rounded-full border border-emerald-200/80 bg-emerald-50/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
          {t('claimLedger.confidence')}: {confidence}
        </span>
      </header>

      <div className="mt-3">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
          {t('claimLedger.premises')}
        </p>
        <div className="mt-1.5 flex flex-col gap-1.5">
          {step.premises.map((premise, premiseIndex) => (
            <TripleRow
              key={`${premise.join('|')}-${premiseIndex}`}
              triple={premise}
              emphasis="premise"
            />
          ))}
        </div>
      </div>

      <div className="mt-3 border-t border-dashed border-stone-200/80 pt-3">
        <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
          {t('claimLedger.conclusion')}
        </p>
        <div className="mt-1.5">
          <TripleRow triple={step.conclusion} emphasis="conclusion" />
        </div>
      </div>
    </article>
  );
}

export default function ProofChainPanel({ steps, className }: ProofChainPanelProps) {
  if (steps.length === 0) {
    return null;
  }

  return (
    <div className={cn('mt-3 flex flex-col gap-2', className)} data-testid="proof-chain-panel">
      {steps.map((step, index) => (
        <StepCard key={`${step.rule}-${index}`} step={step} index={index} />
      ))}
    </div>
  );
}
