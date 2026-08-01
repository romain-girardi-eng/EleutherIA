import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  BookOpen,
  Quote,
  Link2,
  Sparkles,
  Check,
  Plus,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import type { Proposal, ProposalKind } from '../../api/contributions';

interface ProposalCardProps {
  proposal: Proposal;
  selected: boolean;
  onToggle: () => void;
}

function pickString(
  payload: Record<string, unknown>,
  keys: string[]
): string | undefined {
  for (const key of keys) {
    const value = payload[key];
    if (typeof value === 'string' && value.trim().length > 0) return value;
  }
  return undefined;
}

function kindIcon(kind: ProposalKind) {
  switch (kind) {
    case 'passage_citation':
      return <Quote className="h-4 w-4" aria-hidden="true" />;
    case 'edge':
      return <Link2 className="h-4 w-4" aria-hidden="true" />;
    case 'concept_attestation':
      return <Sparkles className="h-4 w-4" aria-hidden="true" />;
    case 'scholar_ref':
    case 'node':
    default:
      return <BookOpen className="h-4 w-4" aria-hidden="true" />;
  }
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.7) return 'bg-emerald-500';
  if (confidence >= 0.4) return 'bg-amber-500';
  return 'bg-stone-400';
}

function getHeadline(proposal: Proposal, fallback: string): string {
  const { payload, kind } = proposal;
  if (kind === 'edge') {
    const subject =
      pickString(payload, ['subject_label', 'source_label', 'source']) ?? '';
    const predicate =
      pickString(payload, ['predicate', 'relation', 'relation_type']) ?? '';
    const object =
      pickString(payload, ['object_label', 'target_label', 'target']) ?? '';
    const text = [subject, predicate, object].filter(Boolean).join(' → ');
    return text || fallback;
  }
  return (
    pickString(payload, [
      'label',
      'name',
      'title',
      'citation_text',
      'concept_label',
      'scholar_name',
      'headline',
    ]) ?? fallback
  );
}

function getBody(proposal: Proposal): React.ReactNode {
  const { payload, kind } = proposal;
  if (kind === 'passage_citation') {
    const ancient = pickString(payload, [
      'ancient_text',
      'original_text',
      'greek_text',
      'latin_text',
    ]);
    const translation = pickString(payload, ['translation', 'english']);
    const reference = pickString(payload, [
      'reference',
      'cts_urn',
      'citation_ref',
    ]);
    return (
      <div className="space-y-1.5">
        {ancient && (
          <p className="font-serif text-sm leading-snug text-stone-800">
            {ancient}
          </p>
        )}
        {translation && (
          <p className="text-sm italic text-stone-700">{translation}</p>
        )}
        {reference && (
          <p className="text-xs font-mono text-stone-500">{reference}</p>
        )}
      </div>
    );
  }
  if (kind === 'edge') {
    const claim = pickString(payload, [
      'claim',
      'description',
      'rationale',
      'summary',
    ]);
    if (claim) {
      return <p className="text-sm text-stone-700">{claim}</p>;
    }
    return null;
  }
  const description = pickString(payload, [
    'description',
    'definition',
    'abstract',
    'summary',
  ]);
  const nodeType = pickString(payload, ['node_type', 'type']);
  return (
    <div className="space-y-1">
      {description && <p className="text-sm text-stone-700">{description}</p>}
      {nodeType && (
        <p className="text-xs uppercase tracking-wide text-stone-500">
          {nodeType}
        </p>
      )}
    </div>
  );
}

export default function ProposalCard({
  proposal,
  selected,
  onToggle,
}: ProposalCardProps) {
  const { t } = useTranslation();
  const confidencePercent = Math.round(proposal.confidence * 100);
  const fallback = t(`contribute.review.proposalKinds.${proposal.kind}`);
  const headline = useMemo(
    () => getHeadline(proposal, fallback),
    [proposal, fallback]
  );
  const body = useMemo(() => getBody(proposal), [proposal]);
  const isExisting = Boolean(proposal.target_kg_id);

  return (
    <article
      className={cn(
        'flex h-full flex-col rounded-xl border bg-white p-4 shadow-sm transition-all',
        selected
          ? 'border-amber-500 ring-2 ring-amber-200'
          : 'border-stone-200 hover:border-amber-300 hover:shadow-md'
      )}
    >
      <header className="mb-3 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-amber-100 text-amber-700">
            {kindIcon(proposal.kind)}
          </span>
          <span className="text-xs font-medium uppercase tracking-wide text-stone-600">
            {t(`contribute.review.proposalKinds.${proposal.kind}`)}
          </span>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="text-xs font-medium text-stone-600">
            {confidencePercent}%
          </span>
          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-stone-200">
            <div
              className={cn('h-full', confidenceColor(proposal.confidence))}
              style={{ width: `${Math.min(100, Math.max(0, confidencePercent))}%` }}
            />
          </div>
        </div>
      </header>

      <h3 className="text-base font-semibold leading-snug text-stone-900">
        {headline}
      </h3>

      <div className="mt-2 flex-1">{body}</div>

      {isExisting && (
        <span className="mt-3 inline-flex w-fit items-center gap-1 rounded-full bg-stone-100 px-2 py-0.5 text-xs text-stone-600">
          {t('contribute.review.alreadyInKg')}
        </span>
      )}

      {(proposal.evidence.excerpt || proposal.evidence.page_number) && (
        <footer className="mt-3 border-t border-stone-100 pt-3">
          {proposal.evidence.excerpt && (
            <p className="line-clamp-3 text-xs italic text-stone-600">
              “{proposal.evidence.excerpt}”
            </p>
          )}
          {typeof proposal.evidence.page_number === 'number' && (
            <span className="mt-2 inline-block rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-800">
              {t('contribute.review.page', {
                page: proposal.evidence.page_number,
              })}
            </span>
          )}
        </footer>
      )}

      <button
        type="button"
        onClick={onToggle}
        aria-pressed={selected}
        className={cn(
          'mt-4 inline-flex min-h-11 items-center justify-center gap-1 rounded-md border px-3 py-1.5 text-sm font-medium transition-colors',
          selected
            ? 'border-amber-500 bg-amber-500 text-white hover:bg-amber-600'
            : 'border-stone-300 bg-white text-stone-700 hover:bg-stone-50'
        )}
      >
        {selected ? (
          <>
            <Check className="h-4 w-4" aria-hidden="true" />
            {t('contribute.review.kept')}
          </>
        ) : (
          <>
            <Plus className="h-4 w-4" aria-hidden="true" />
            {t('contribute.review.keep')}
          </>
        )}
      </button>
    </article>
  );
}
