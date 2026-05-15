import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { ArrowLeft, AlertCircle, Loader2 } from 'lucide-react';
import {
  acceptProposal,
  applyContribution,
  getContribution,
  rejectContribution,
  rejectProposal,
  type ContributionDetail,
  type ContributionStatus,
  type ProposalStatus,
} from '../../api/contributions';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../components/ui/Toast';
import { cn } from '../../lib/utils';
import PdfPreview from './PdfPreview';
import ProposalsList from './ProposalsList';
import AdminActionBar from './AdminActionBar';

function relevanceColor(score: number): string {
  if (score >= 0.8) return 'border-emerald-300/70 bg-emerald-50/60 text-emerald-800';
  if (score >= 0.6) return 'border-amber-300/70 bg-amber-50/60 text-amber-900';
  if (score >= 0.4) return 'border-orange-300/70 bg-orange-50/60 text-orange-800';
  return 'border-stone-300/70 bg-stone-50/60 text-stone-700';
}

const STATUS_BANNER: Record<ContributionStatus, string> = {
  uploaded: 'border-blue-300/70 bg-blue-50/70 text-blue-800',
  processing: 'border-blue-300/70 bg-blue-50/70 text-blue-800',
  ready: 'border-amber-300/70 bg-amber-50/70 text-amber-900',
  approved: 'border-emerald-300/70 bg-emerald-50/70 text-emerald-800',
  merged: 'border-violet-300/70 bg-violet-50/70 text-violet-800',
  rejected: 'border-rose-300/70 bg-rose-50/70 text-rose-800',
  failed: 'border-red-300/70 bg-red-50/70 text-red-800',
};

function DetailSkeleton() {
  return (
    <div className="grid gap-6 lg:grid-cols-[2fr_3fr]">
      <div className="h-[60vh] animate-pulse rounded-2xl border border-stone-200/50 bg-white/40" />
      <div className="space-y-3">
        <div className="h-20 animate-pulse rounded-2xl border border-stone-200/50 bg-white/40" />
        <div className="h-32 animate-pulse rounded-2xl border border-stone-200/50 bg-white/40" />
        <div className="h-32 animate-pulse rounded-2xl border border-stone-200/50 bg-white/40" />
      </div>
    </div>
  );
}

export default function ContributionDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { showToast } = useToast();

  const [detail, setDetail] = useState<ContributionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [focusedPage, setFocusedPage] = useState<number | null>(null);
  const [busyApply, setBusyApply] = useState(false);
  const [busyReject, setBusyReject] = useState(false);

  const isAdmin = isAuthenticated && user?.role === 'admin';

  const reload = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getContribution(id);
      setDetail(data);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : t('contributions.errors.loadFailed');
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [id, t]);

  useEffect(() => {
    reload();
  }, [reload]);

  const setProposalStatus = useCallback(
    (proposalId: string, status: ProposalStatus) => {
      setDetail((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          proposals: prev.proposals.map((proposal) =>
            proposal.proposal_id === proposalId
              ? { ...proposal, status }
              : proposal
          ),
        };
      });
    },
    []
  );

  const handleAccept = useCallback(
    async (proposalId: string) => {
      if (!detail || !isAdmin) return;
      const previous = detail.proposals.find(
        (p) => p.proposal_id === proposalId
      )?.status;
      setProposalStatus(proposalId, 'accepted');
      try {
        await acceptProposal(detail.contribution_id, proposalId);
      } catch (err) {
        if (previous) setProposalStatus(proposalId, previous);
        const message =
          err instanceof Error
            ? err.message
            : t('contributions.errors.actionFailed');
        showToast(message, 'error');
      }
    },
    [detail, isAdmin, setProposalStatus, showToast, t]
  );

  const handleReject = useCallback(
    async (proposalId: string) => {
      if (!detail || !isAdmin) return;
      const previous = detail.proposals.find(
        (p) => p.proposal_id === proposalId
      )?.status;
      setProposalStatus(proposalId, 'rejected');
      try {
        await rejectProposal(detail.contribution_id, proposalId);
      } catch (err) {
        if (previous) setProposalStatus(proposalId, previous);
        const message =
          err instanceof Error
            ? err.message
            : t('contributions.errors.actionFailed');
        showToast(message, 'error');
      }
    },
    [detail, isAdmin, setProposalStatus, showToast, t]
  );

  const handleApply = useCallback(
    async (reviewerNotes?: string) => {
      if (!detail || !isAdmin) return;
      setBusyApply(true);
      try {
        const result = await applyContribution(
          detail.contribution_id,
          reviewerNotes
        );
        showToast(
          t('contributions.toasts.merged', {
            count: result.merged_proposals,
          }),
          'success'
        );
        navigate('/recherches');
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : t('contributions.errors.applyFailed');
        showToast(message, 'error');
      } finally {
        setBusyApply(false);
      }
    },
    [detail, isAdmin, navigate, showToast, t]
  );

  const handleRejectAll = useCallback(
    async (reviewerNotes?: string) => {
      if (!detail || !isAdmin) return;
      setBusyReject(true);
      try {
        await rejectContribution(detail.contribution_id, reviewerNotes);
        showToast(t('contributions.toasts.rejected'), 'success');
        await reload();
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : t('contributions.errors.rejectFailed');
        showToast(message, 'error');
      } finally {
        setBusyReject(false);
      }
    },
    [detail, isAdmin, reload, showToast, t]
  );

  const relevancePct = useMemo(() => {
    if (typeof detail?.relevance_score !== 'number') return null;
    return Math.max(0, Math.min(1, detail.relevance_score)) * 100;
  }, [detail?.relevance_score]);

  return (
    <div className="min-h-screen w-full bg-transparent">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 pt-24 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-6"
        >
          <Link
            to="/contributions"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-stone-500 hover:text-amber-700 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
            {t('contributions.detail.back')}
          </Link>
        </motion.div>

        {loading && !detail ? (
          <DetailSkeleton />
        ) : error ? (
          <div
            role="alert"
            className="flex items-start gap-3 rounded-xl border border-red-200/60 bg-red-50/70 p-4 text-sm text-red-800"
          >
            <AlertCircle
              className="mt-0.5 h-4 w-4 flex-shrink-0"
              aria-hidden="true"
            />
            <div>
              <p className="font-medium">{t('contributions.errors.title')}</p>
              <p className="text-red-700/80">{error}</p>
            </div>
          </div>
        ) : detail ? (
          <div className="grid gap-6 lg:grid-cols-[2fr_3fr] lg:items-start">
            <PdfPreview
              title={detail.title}
              authors={detail.authors}
              publicationYear={detail.publication_year}
              doi={detail.doi}
              pdfSignedUrl={detail.pdf_signed_url}
              focusedPage={focusedPage}
            />

            <div className="space-y-4">
              <div
                className={cn(
                  'rounded-2xl border p-4',
                  STATUS_BANNER[detail.status]
                )}
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs font-semibold uppercase tracking-wide">
                    {t(`contributions.status.${detail.status}`)}
                  </p>
                  {loading && (
                    <Loader2
                      className="h-3.5 w-3.5 animate-spin"
                      aria-hidden="true"
                    />
                  )}
                </div>
              </div>

              {relevancePct !== null && (
                <div
                  className={cn(
                    'rounded-2xl border p-4',
                    relevanceColor(relevancePct / 100)
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <h2 className="text-sm font-display font-semibold">
                      {t('contributions.detail.relevance.title')}
                    </h2>
                    <span className="text-xs font-semibold">
                      {t('contributions.card.relevance', {
                        value: relevancePct.toFixed(0),
                      })}
                    </span>
                  </div>
                  {detail.relevance_summary && (
                    <p className="mt-2 text-xs leading-relaxed">
                      {detail.relevance_summary}
                    </p>
                  )}
                  {detail.free_will_concepts.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {detail.free_will_concepts.map((concept) => (
                        <span
                          key={concept}
                          className="inline-flex items-center rounded-full border border-current/30 bg-white/40 px-2 py-0.5 text-[10px] font-medium"
                        >
                          {concept}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <ProposalsList
                proposals={detail.proposals}
                isAdmin={Boolean(isAdmin)}
                onAccept={handleAccept}
                onReject={handleReject}
                onJumpToPage={setFocusedPage}
              />

              {isAdmin && detail.status !== 'merged' && (
                <AdminActionBar
                  proposals={detail.proposals}
                  busyApply={busyApply}
                  busyReject={busyReject}
                  onApply={handleApply}
                  onRejectAll={handleRejectAll}
                />
              )}

              {!isAdmin && (
                <div className="rounded-xl border border-stone-200/60 bg-stone-50/60 p-3 text-xs text-stone-500">
                  {t('contributions.detail.readOnlyHint')}
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
