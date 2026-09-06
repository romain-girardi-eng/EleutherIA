import { BookOpen, CircleHelp, ShieldCheck, ShieldAlert } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { GraphRAGResponse } from '../../types';

interface EvidenceReviewProps {
  response?: GraphRAGResponse;
  onPassageClick?: (id: string) => void;
  onNodeClick?: (id: string) => void;
}

/** Publication status is an observed gate result, never an accuracy percentage. */
export default function EvidenceReview({ response, onPassageClick, onNodeClick }: EvidenceReviewProps) {
  const { t } = useTranslation();
  const gate = response?.metadata?.publication_gate;
  const state = gate?.publishable === false ? 'blocked'
    : gate?.publishable === true ? (gate.status === 'partial' ? 'partial' : 'passed') : 'unknown';
  const Icon = state === 'passed' ? ShieldCheck : state === 'unknown' ? CircleHelp : ShieldAlert;
  const citations = response?.passage_citations ?? [];
  const primary = citations.filter(c => c.layer !== 'secondary').length;
  const secondary = citations.filter(c => c.layer === 'secondary').length;
  const ledger = (response?.claim_ledger ?? []).filter(c => c.status?.toLowerCase() !== 'insufficient');
  const reasons = [...new Set([
    ...(gate?.reasons ?? []),
    ...Object.keys(gate?.withholding?.reasons ?? {}),
    ...Object.keys(gate?.withholding?.pair_reasons ?? {}),
  ])];

  return (
    <section aria-label={t('graphRagUi.evidence.title')} className="border-y border-stone-200 py-4 font-body">
      <div role="status" className="flex items-start gap-3">
        <Icon aria-hidden="true" className={`mt-0.5 h-5 w-5 shrink-0 ${state === 'passed' ? 'text-emerald-800' : 'text-amber-800'}`} />
        <div>
          <h2 className="text-sm font-semibold text-stone-900">{t(`graphRagUi.evidence.${state}`)}</h2>
          <p className="mt-1 max-w-prose text-sm leading-6 text-stone-600">{t(`graphRagUi.evidence.${state}Body`)}</p>
        </div>
      </div>
      {citations.length > 0 && (
        <p className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 pl-8 text-xs font-medium text-stone-700">
          <span>{t('graphRagUi.evidence.primary', { count: primary })}</span>
          <span>{t('graphRagUi.evidence.secondary', { count: secondary })}</span>
        </p>
      )}
      {typeof gate?.withholding?.withheld_sentences === 'number' && gate.withholding.withheld_sentences > 0 && (
        <p className="mt-2 pl-8 text-sm text-amber-900">{t('graphRagUi.evidence.omitted', { count: gate.withholding.withheld_sentences })}</p>
      )}
      {(ledger.length > 0 || reasons.length > 0) && (
        <details className="mt-2 pl-8">
          <summary className="cursor-pointer py-2 text-sm font-medium text-orange-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-orange-700">{t('graphRagUi.evidence.inspect')}</summary>
          {reasons.length > 0 && (
            <div className="mb-3 text-xs leading-6 text-stone-600">
              <p>{t('graphRagUi.evidence.reasonHint')}</p>
              <ul className="list-disc pl-4">{reasons.map(reason => <li key={reason}>{t(`graphRagUi.evidence.reasons.${reason}`, { defaultValue: t('graphRagUi.evidence.reasonFallback') })}</li>)}</ul>
            </div>
          )}
          <ol className="divide-y divide-stone-200">
            {ledger.map((claim, index) => (
              <li key={index} className="py-3 text-sm leading-6 text-stone-800">
                <p>{claim.claim}</p>
                <div className="mt-1 flex flex-wrap gap-2">
                  {claim.evidence_ids.map(id => {
                    const citation = citations.find(c => c.id === id);
                    if (!citation?.label) return null;
                    const onOpen = citation.type === 'passage' ? onPassageClick : onNodeClick;
                    return onOpen ? <button key={id} type="button" onClick={() => onOpen(id)} className="inline-flex min-h-11 items-center gap-1.5 text-xs text-orange-800 underline underline-offset-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-orange-700"><BookOpen className="h-3.5 w-3.5" aria-hidden="true" />{citation.label}</button>
                      : <span key={id} className="text-xs text-stone-600">{citation.label}</span>;
                  })}
                </div>
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
}
