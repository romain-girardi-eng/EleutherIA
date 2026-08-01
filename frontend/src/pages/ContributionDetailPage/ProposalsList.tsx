import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Check,
  X,
  ChevronDown,
  Circle,
  CheckCircle2,
  XCircle,
  Sparkles,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import type {
  Proposal,
  ProposalKind,
  ProposalStatus,
} from '../../api/contributions';

export type { Proposal, ProposalKind, ProposalStatus };

interface ProposalsListProps {
  proposals: Proposal[];
  isAdmin: boolean;
  onAccept: (proposalId: string) => void;
  onReject: (proposalId: string) => void;
  onJumpToPage: (page: number) => void;
}

const KIND_ORDER: ProposalKind[] = [
  'node',
  'edge',
  'passage_citation',
  'scholar_ref',
  'concept_attestation',
];

function pickString(payload: Record<string, unknown>, key: string): string | null {
  const value = payload[key];
  return typeof value === 'string' && value.trim().length > 0 ? value : null;
}

function headlineFor(proposal: Proposal): string {
  const payload = proposal.payload ?? {};
  switch (proposal.kind) {
    case 'node': {
      const label =
        pickString(payload, 'label') ?? pickString(payload, 'name');
      const type = pickString(payload, 'type');
      if (label && type) return `${label} (${type})`;
      return label ?? type ?? 'Node';
    }
    case 'edge': {
      const relation = pickString(payload, 'relation');
      const source =
        pickString(payload, 'source_label') ??
        pickString(payload, 'source');
      const target =
        pickString(payload, 'target_label') ??
        pickString(payload, 'target');
      if (source && relation && target) {
        return `${source} —${relation}→ ${target}`;
      }
      return relation ?? 'Edge';
    }
    case 'passage_citation': {
      const author = pickString(payload, 'author');
      const work = pickString(payload, 'work');
      const locus = pickString(payload, 'locus');
      const passageId = pickString(payload, 'passage_id');
      const parts = [author, work, locus].filter(Boolean).join(', ');
      return parts || passageId || 'Passage citation';
    }
    case 'scholar_ref': {
      const author = pickString(payload, 'author');
      const title = pickString(payload, 'title');
      const year = pickString(payload, 'year');
      const parts = [author, title, year].filter(Boolean).join(', ');
      return parts || 'Scholar reference';
    }
    case 'concept_attestation': {
      const concept = pickString(payload, 'concept');
      const author = pickString(payload, 'author');
      if (concept && author) return `${concept} — ${author}`;
      return concept ?? 'Concept attestation';
    }
    default:
      return proposal.kind;
  }
}

function StatusIcon({ status }: { status: ProposalStatus }) {
  switch (status) {
    case 'accepted':
      return (
        <CheckCircle2
          className="h-4 w-4 text-emerald-600"
          aria-hidden="true"
        />
      );
    case 'rejected':
      return <XCircle className="h-4 w-4 text-rose-600" aria-hidden="true" />;
    case 'applied':
      return <Sparkles className="h-4 w-4 text-violet-600" aria-hidden="true" />;
    case 'pending':
    default:
      return <Circle className="h-4 w-4 text-stone-300" aria-hidden="true" />;
  }
}

function confidenceColor(value: number): string {
  if (value >= 0.8) return 'bg-emerald-500';
  if (value >= 0.6) return 'bg-amber-500';
  if (value >= 0.4) return 'bg-orange-500';
  return 'bg-stone-400';
}

interface ProposalRowProps {
  proposal: Proposal;
  isAdmin: boolean;
  onAccept: (proposalId: string) => void;
  onReject: (proposalId: string) => void;
  onJumpToPage: (page: number) => void;
}

function ProposalRow({
  proposal,
  isAdmin,
  onAccept,
  onReject,
  onJumpToPage,
}: ProposalRowProps) {
  const { t } = useTranslation();
  const confidencePct =
    typeof proposal.confidence === 'number'
      ? Math.max(0, Math.min(1, proposal.confidence)) * 100
      : null;
  const headline = headlineFor(proposal);
  const evidenceExcerpt = proposal.evidence?.excerpt ?? null;
  const evidencePage = proposal.evidence?.page_number ?? null;

  return (
    <li
      className={cn(
        'group rounded-xl border p-3 transition-colors',
        proposal.status === 'rejected'
          ? 'border-rose-200/50 bg-rose-50/40 opacity-70'
          : proposal.status === 'accepted'
            ? 'border-emerald-200/60 bg-emerald-50/40'
            : proposal.status === 'applied'
              ? 'border-violet-200/60 bg-violet-50/40'
              : 'border-stone-200/60 bg-white/50 hover:border-amber-300/60'
      )}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex-shrink-0">
          <StatusIcon status={proposal.status} />
        </div>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-stone-800 leading-snug">
            {headline}
          </p>

          {confidencePct !== null && (
            <div className="mt-1.5 flex items-center gap-2">
              <div
                className="h-1 w-24 overflow-hidden rounded-full bg-stone-100"
                role="progressbar"
                aria-valuenow={Math.round(confidencePct)}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={t('contributions.detail.proposals.confidence')}
              >
                <div
                  className={cn(
                    'h-full rounded-full',
                    confidenceColor(confidencePct / 100)
                  )}
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
              <span className="text-[10px] font-medium text-stone-500">
                {t('contributions.detail.proposals.confidenceValue', {
                  value: confidencePct.toFixed(0),
                })}
              </span>
            </div>
          )}

          {evidenceExcerpt && (
            <p className="mt-2 text-xs italic text-stone-500 leading-relaxed line-clamp-3">
              &laquo; {evidenceExcerpt} &raquo;
            </p>
          )}

          <div className="mt-2 flex flex-wrap items-center gap-2">
            {typeof evidencePage === 'number' && evidencePage > 0 && (
              <button
                type="button"
                onClick={() => onJumpToPage(evidencePage)}
                className="inline-flex items-center gap-1 rounded-full border border-amber-200/70 bg-amber-50/80 px-2 py-0.5 text-[10px] font-semibold text-amber-800 hover:border-amber-400/70 hover:bg-amber-100/80 transition-colors"
              >
                {t('contributions.detail.proposals.page', {
                  page: evidencePage,
                })}
              </button>
            )}
            {proposal.reviewer_notes && (
              <span className="text-[10px] italic text-stone-400">
                {t('contributions.detail.proposals.reviewerNoted')}
              </span>
            )}
          </div>
        </div>

        {isAdmin && proposal.status !== 'applied' && (
          <div className="flex flex-shrink-0 flex-col gap-1 opacity-100 sm:opacity-0 sm:transition-opacity sm:group-hover:opacity-100 sm:focus-within:opacity-100">
            <button
              type="button"
              onClick={() => onAccept(proposal.proposal_id)}
              disabled={proposal.status === 'accepted'}
              className={cn(
                'inline-flex min-h-11 items-center gap-1 rounded-md border px-2.5 text-[10px] font-semibold transition-colors',
                proposal.status === 'accepted'
                  ? 'border-emerald-400 bg-emerald-500 text-white'
                  : 'border-emerald-300/70 bg-white text-emerald-700 hover:bg-emerald-50'
              )}
              aria-label={t('contributions.detail.proposals.actions.accept')}
            >
              <Check className="h-3 w-3" aria-hidden="true" />
              {t('contributions.detail.proposals.actions.accept')}
            </button>
            <button
              type="button"
              onClick={() => onReject(proposal.proposal_id)}
              disabled={proposal.status === 'rejected'}
              className={cn(
                'inline-flex min-h-11 items-center gap-1 rounded-md border px-2.5 text-[10px] font-semibold transition-colors',
                proposal.status === 'rejected'
                  ? 'border-rose-400 bg-rose-500 text-white'
                  : 'border-rose-300/70 bg-white text-rose-700 hover:bg-rose-50'
              )}
              aria-label={t('contributions.detail.proposals.actions.reject')}
            >
              <X className="h-3 w-3" aria-hidden="true" />
              {t('contributions.detail.proposals.actions.reject')}
            </button>
          </div>
        )}
      </div>
    </li>
  );
}

export default function ProposalsList({
  proposals,
  isAdmin,
  onAccept,
  onReject,
  onJumpToPage,
}: ProposalsListProps) {
  const { t } = useTranslation();

  const grouped = useMemo(() => {
    const map = new Map<ProposalKind, Proposal[]>();
    for (const proposal of proposals) {
      const bucket = map.get(proposal.kind) ?? [];
      bucket.push(proposal);
      map.set(proposal.kind, bucket);
    }
    return KIND_ORDER.filter((kind) => map.has(kind)).map((kind) => ({
      kind,
      proposals: map.get(kind) ?? [],
    }));
  }, [proposals]);

  const [openKinds, setOpenKinds] = useState<Set<ProposalKind>>(
    () => new Set(KIND_ORDER)
  );

  const toggleKind = (kind: ProposalKind) => {
    setOpenKinds((prev) => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  };

  if (grouped.length === 0) {
    return (
      <div className="rounded-2xl border border-stone-200/60 bg-white/50 p-8 text-center">
        <p className="text-sm text-stone-500">
          {t('contributions.detail.proposals.empty')}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {grouped.map(({ kind, proposals: kindProposals }) => {
        const isOpen = openKinds.has(kind);
        return (
          <section
            key={kind}
            className="rounded-2xl border border-stone-200/60 bg-white/55 backdrop-blur-sm overflow-hidden"
          >
            <button
              type="button"
              onClick={() => toggleKind(kind)}
              aria-expanded={isOpen}
              className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-stone-50/60"
            >
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-display font-semibold text-stone-800">
                  {t(`contributions.detail.proposals.kinds.${kind}`)}
                </h3>
                <span className="rounded-full bg-stone-100 px-2 py-0.5 text-[10px] font-semibold text-stone-600">
                  {kindProposals.length}
                </span>
              </div>
              <ChevronDown
                className={cn(
                  'h-4 w-4 text-stone-400 transition-transform',
                  isOpen ? 'rotate-180' : ''
                )}
                aria-hidden="true"
              />
            </button>

            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.ul
                  key="content"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2, ease: 'easeInOut' }}
                  className="space-y-2 overflow-hidden px-4 pb-4"
                >
                  {kindProposals.map((proposal) => (
                    <ProposalRow
                      key={proposal.proposal_id}
                      proposal={proposal}
                      isAdmin={isAdmin}
                      onAccept={onAccept}
                      onReject={onReject}
                      onJumpToPage={onJumpToPage}
                    />
                  ))}
                </motion.ul>
              )}
            </AnimatePresence>
          </section>
        );
      })}
    </div>
  );
}
