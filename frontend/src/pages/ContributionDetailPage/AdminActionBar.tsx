import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, ShieldCheck, Trash2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Proposal, ProposalStatus } from '../../api/contributions';

interface AdminActionBarProps {
  proposals: Proposal[];
  busyApply: boolean;
  busyReject: boolean;
  onApply: (reviewerNotes?: string) => Promise<void> | void;
  onRejectAll: (reviewerNotes?: string) => Promise<void> | void;
}

interface DiffCounts {
  nodes: number;
  edges: number;
  citations: number;
  other: number;
  total: number;
}

function diffFromAccepted(proposals: Proposal[]): DiffCounts {
  let nodes = 0;
  let edges = 0;
  let citations = 0;
  let other = 0;
  for (const proposal of proposals) {
    if (proposal.status !== 'accepted') continue;
    switch (proposal.kind) {
      case 'node':
        nodes += 1;
        break;
      case 'edge':
        edges += 1;
        break;
      case 'passage_citation':
        citations += 1;
        break;
      default:
        other += 1;
    }
  }
  return { nodes, edges, citations, other, total: nodes + edges + citations + other };
}

function countByStatus(
  proposals: Proposal[]
): Record<ProposalStatus, number> {
  const counts: Record<ProposalStatus, number> = {
    pending: 0,
    accepted: 0,
    rejected: 0,
    applied: 0,
    superseded: 0,
  };
  for (const proposal of proposals) {
    counts[proposal.status] += 1;
  }
  return counts;
}

export default function AdminActionBar({
  proposals,
  busyApply,
  busyReject,
  onApply,
  onRejectAll,
}: AdminActionBarProps) {
  const { t } = useTranslation();
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [applyNotes, setApplyNotes] = useState('');
  const [rejectNotes, setRejectNotes] = useState('');

  const statusCounts = useMemo(() => countByStatus(proposals), [proposals]);
  const diff = useMemo(() => diffFromAccepted(proposals), [proposals]);

  const canApply =
    statusCounts.accepted > 0 && statusCounts.pending === 0 && !busyApply;

  const total = proposals.length;

  const handleApplyConfirm = async () => {
    await onApply(applyNotes.trim() || undefined);
    setShowApplyModal(false);
    setApplyNotes('');
  };

  const handleRejectConfirm = async () => {
    await onRejectAll(rejectNotes.trim() || undefined);
    setShowRejectModal(false);
    setRejectNotes('');
  };

  return (
    <>
      <div
        className={cn(
          'sticky bottom-4 z-20 mt-6 rounded-2xl border border-amber-200/60 bg-white/85 backdrop-blur-md p-4 shadow-[0_10px_40px_-10px_rgba(180,83,9,0.25)]'
        )}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-stone-600">
            {t('contributions.detail.adminBar.counts', {
              accepted: statusCounts.accepted,
              rejected: statusCounts.rejected,
              pending: statusCounts.pending,
              total,
            })}
          </p>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setShowRejectModal(true)}
              disabled={busyReject || total === 0}
              className={cn(
                'inline-flex min-h-11 items-center gap-1.5 rounded-full border border-rose-300/70 bg-white px-3 text-xs font-semibold text-rose-700 transition-colors',
                'hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-50'
              )}
            >
              {busyReject ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
              ) : (
                <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
              )}
              {t('contributions.detail.adminBar.rejectAll')}
            </button>

            <button
              type="button"
              onClick={() => setShowApplyModal(true)}
              disabled={!canApply}
              className={cn(
                'inline-flex min-h-11 items-center gap-1.5 rounded-full px-4 text-xs font-semibold text-white transition-colors',
                canApply
                  ? 'bg-violet-600 hover:bg-violet-700 shadow-sm'
                  : 'bg-stone-300 cursor-not-allowed'
              )}
              title={
                !canApply
                  ? t('contributions.detail.adminBar.applyDisabledHint')
                  : undefined
              }
            >
              {busyApply ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
              ) : (
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
              )}
              {t('contributions.detail.adminBar.apply', {
                count: statusCounts.accepted,
              })}
            </button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showApplyModal && (
          <ConfirmModal
            key="apply-modal"
            title={t('contributions.detail.applyModal.title')}
            description={t('contributions.detail.applyModal.body', {
              nodes: diff.nodes,
              edges: diff.edges,
              citations: diff.citations,
            })}
            extraNote={t('contributions.detail.applyModal.note')}
            notesLabel={t('contributions.detail.applyModal.notesLabel')}
            notesPlaceholder={t(
              'contributions.detail.applyModal.notesPlaceholder'
            )}
            notesValue={applyNotes}
            onNotesChange={setApplyNotes}
            confirmLabel={t('contributions.detail.applyModal.confirm')}
            cancelLabel={t('contributions.detail.applyModal.cancel')}
            confirmTone="violet"
            busy={busyApply}
            onConfirm={handleApplyConfirm}
            onCancel={() => setShowApplyModal(false)}
          />
        )}
        {showRejectModal && (
          <ConfirmModal
            key="reject-modal"
            title={t('contributions.detail.rejectModal.title')}
            description={t('contributions.detail.rejectModal.body')}
            notesLabel={t('contributions.detail.rejectModal.notesLabel')}
            notesPlaceholder={t(
              'contributions.detail.rejectModal.notesPlaceholder'
            )}
            notesValue={rejectNotes}
            onNotesChange={setRejectNotes}
            confirmLabel={t('contributions.detail.rejectModal.confirm')}
            cancelLabel={t('contributions.detail.rejectModal.cancel')}
            confirmTone="rose"
            busy={busyReject}
            onConfirm={handleRejectConfirm}
            onCancel={() => setShowRejectModal(false)}
          />
        )}
      </AnimatePresence>
    </>
  );
}

interface ConfirmModalProps {
  title: string;
  description: string;
  extraNote?: string;
  notesLabel: string;
  notesPlaceholder: string;
  notesValue: string;
  onNotesChange: (value: string) => void;
  confirmLabel: string;
  cancelLabel: string;
  confirmTone: 'violet' | 'rose';
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmModal({
  title,
  description,
  extraNote,
  notesLabel,
  notesPlaceholder,
  notesValue,
  onNotesChange,
  confirmLabel,
  cancelLabel,
  confirmTone,
  busy,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="contribution-confirm-title"
    >
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 8, scale: 0.98 }}
        transition={{ duration: 0.2 }}
        className="w-full max-w-md max-h-[85vh] overflow-y-auto rounded-2xl border border-stone-200 bg-parchment-50 p-6 shadow-xl"
      >
        <h2
          id="contribution-confirm-title"
          className="text-base font-display font-semibold text-stone-800"
        >
          {title}
        </h2>
        <p className="mt-2 text-sm text-stone-600 leading-relaxed">
          {description}
        </p>
        {extraNote && (
          <p className="mt-2 text-xs italic text-stone-500">{extraNote}</p>
        )}

        <label className="mt-4 block text-xs font-medium text-stone-600">
          {notesLabel}
          <textarea
            value={notesValue}
            onChange={(event) => onNotesChange(event.target.value)}
            placeholder={notesPlaceholder}
            rows={3}
            className="mt-1 w-full rounded-lg border border-stone-200 bg-white px-3 py-2 text-base text-stone-700 placeholder:text-stone-400 focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-400/30"
          />
        </label>

        <div className="mt-5 flex flex-col-reverse justify-end gap-2 sm:flex-row">
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="min-h-11 rounded-full border border-stone-300 bg-white px-4 text-xs font-semibold text-stone-700 hover:bg-stone-50 disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={busy}
            className={cn(
              'inline-flex min-h-11 items-center gap-1.5 rounded-full px-4 text-xs font-semibold text-white transition-colors',
              confirmTone === 'violet'
                ? 'bg-violet-600 hover:bg-violet-700'
                : 'bg-rose-600 hover:bg-rose-700',
              busy && 'opacity-70'
            )}
          >
            {busy && (
              <Loader2
                className="h-3.5 w-3.5 animate-spin"
                aria-hidden="true"
              />
            )}
            {confirmLabel}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
