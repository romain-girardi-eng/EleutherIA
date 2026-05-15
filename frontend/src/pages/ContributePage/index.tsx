import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  FileText,
  Sparkles,
  UploadCloud,
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { cn } from '../../utils/cn';
import {
  getContribution,
  rejectContribution,
  uploadContribution,
  type ContributionDetail,
  type Proposal,
  type UploadResponse,
} from '../../api/contributions';
import UploadZone from './UploadZone';
import ProcessingStatus from './ProcessingStatus';
import ProposalCard from './ProposalCard';

const POLL_INTERVAL_MS = 4000;

type PageState =
  | { kind: 'empty' }
  | {
      kind: 'metadata';
      file: File;
    }
  | {
      kind: 'processing';
      file: File;
      contributionId: string;
      upload: UploadResponse;
      detail: ContributionDetail | null;
      startedAt: number;
      uploadProgress: number;
      metadata: MetadataForm;
    }
  | {
      kind: 'review';
      detail: ContributionDetail;
    }
  | {
      kind: 'failed';
      contributionId: string;
      detail: ContributionDetail | null;
      message: string;
    };

interface MetadataForm {
  title: string;
  authors: string;
  doi: string;
  publicationYear: string;
}

type TabKey = 'all' | 'scholars' | 'passages' | 'edges' | 'concepts';

const TABS: TabKey[] = ['all', 'scholars', 'passages', 'edges', 'concepts'];

function isScholarNode(p: Proposal): boolean {
  return p.kind === 'node' && p.payload.node_type === 'scholar';
}

function isConceptNode(p: Proposal): boolean {
  return p.kind === 'node' && p.payload.node_type === 'concept';
}

function matchesTab(p: Proposal, tab: TabKey): boolean {
  if (tab === 'all') return true;
  if (tab === 'scholars') return isScholarNode(p) || p.kind === 'scholar_ref';
  if (tab === 'passages') return p.kind === 'passage_citation';
  if (tab === 'edges') return p.kind === 'edge';
  if (tab === 'concepts') return p.kind === 'concept_attestation' || isConceptNode(p);
  return false;
}

function buildKeptStorageKey(id: string): string {
  return `eleutheria.contributions.${id}.kept_proposals`;
}

function relevanceBucket(score: number): 'high' | 'medium' | 'low' {
  if (score >= 0.7) return 'high';
  if (score >= 0.4) return 'medium';
  return 'low';
}

interface KindCounts {
  all: number;
  scholars: number;
  passages: number;
  edges: number;
  concepts: number;
}

function countByTab(proposals: Proposal[]): KindCounts {
  return proposals.reduce<KindCounts>(
    (acc, p) => {
      acc.all += 1;
      if (isScholarNode(p) || p.kind === 'scholar_ref') acc.scholars += 1;
      if (p.kind === 'passage_citation') acc.passages += 1;
      if (p.kind === 'edge') acc.edges += 1;
      if (p.kind === 'concept_attestation' || isConceptNode(p)) acc.concepts += 1;
      return acc;
    },
    { all: 0, scholars: 0, passages: 0, edges: 0, concepts: 0 }
  );
}

function HowItWorks() {
  const { t } = useTranslation();
  const steps: Array<{ icon: React.ReactNode; label: string }> = [
    {
      icon: <UploadCloud className="h-5 w-5" aria-hidden="true" />,
      label: t('contribute.empty.steps.upload'),
    },
    {
      icon: <Sparkles className="h-5 w-5" aria-hidden="true" />,
      label: t('contribute.empty.steps.analyze'),
    },
    {
      icon: <BookOpen className="h-5 w-5" aria-hidden="true" />,
      label: t('contribute.empty.steps.validate'),
    },
  ];
  return (
    <div className="mt-12">
      <h2 className="text-center text-sm font-semibold uppercase tracking-wide text-stone-500">
        {t('contribute.empty.howItWorks')}
      </h2>
      <ol className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {steps.map((step, index) => (
          <li
            key={step.label}
            className="flex items-start gap-3 rounded-lg border border-stone-200 bg-white/70 p-4"
          >
            <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-700">
              {step.icon}
            </span>
            <div>
              <span className="block text-xs font-semibold text-amber-700">
                {t('contribute.empty.step', { index: index + 1 })}
              </span>
              <p className="mt-1 text-sm text-stone-700">{step.label}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

interface MetadataFormProps {
  file: File;
  initial: MetadataForm;
  onSubmit: (metadata: MetadataForm) => void;
  onReset: () => void;
  submitting: boolean;
}

function MetadataFormSection({
  file,
  initial,
  onSubmit,
  onReset,
  submitting,
}: MetadataFormProps) {
  const { t } = useTranslation();
  const [form, setForm] = useState<MetadataForm>(initial);

  const update = useCallback(
    (key: keyof MetadataForm) =>
      (event: React.ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value;
        setForm((prev) => ({ ...prev, [key]: value }));
      },
    []
  );

  const fileSizeMb = (file.size / (1024 * 1024)).toFixed(1);

  return (
    <form
      className="mx-auto max-w-2xl"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(form);
      }}
    >
      <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50/60 px-4 py-3">
        <FileText className="h-5 w-5 text-amber-700" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-stone-800">{file.name}</p>
          <p className="text-xs text-stone-600">
            {t('contribute.metadata.fileSize', { size: fileSizeMb })}
          </p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField
          id="contribute-title"
          label={t('contribute.metadata.fields.title')}
          value={form.title}
          onChange={update('title')}
          placeholder={t('contribute.metadata.placeholders.title')}
        />
        <FormField
          id="contribute-authors"
          label={t('contribute.metadata.fields.authors')}
          value={form.authors}
          onChange={update('authors')}
          placeholder={t('contribute.metadata.placeholders.authors')}
        />
        <FormField
          id="contribute-doi"
          label={t('contribute.metadata.fields.doi')}
          value={form.doi}
          onChange={update('doi')}
          placeholder={t('contribute.metadata.placeholders.doi')}
        />
        <FormField
          id="contribute-year"
          label={t('contribute.metadata.fields.year')}
          value={form.publicationYear}
          onChange={update('publicationYear')}
          placeholder={t('contribute.metadata.placeholders.year')}
          type="number"
          inputMode="numeric"
        />
      </div>

      <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
        <Button
          type="button"
          variant="ghost"
          onClick={onReset}
          disabled={submitting}
        >
          {t('contribute.metadata.chooseAnother')}
        </Button>
        <Button
          type="submit"
          variant="warning"
          disabled={submitting}
          loading={submitting}
        >
          {t('contribute.metadata.submit')}
        </Button>
      </div>
    </form>
  );
}

interface FormFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  type?: string;
  inputMode?: 'text' | 'numeric';
}

function FormField({
  id,
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  inputMode,
}: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs font-medium text-stone-700">
        {label}
      </label>
      <input
        id={id}
        type={type}
        inputMode={inputMode}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="rounded-md border border-stone-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
      />
    </div>
  );
}

interface RelevancePillProps {
  score: number | null;
}

function RelevancePill({ score }: RelevancePillProps) {
  const { t } = useTranslation();
  if (score === null || Number.isNaN(score)) return null;
  const bucket = relevanceBucket(score);
  const palette: Record<typeof bucket, string> = {
    high: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    medium: 'bg-amber-100 text-amber-800 border-amber-300',
    low: 'bg-stone-100 text-stone-700 border-stone-300',
  };
  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium',
        palette[bucket]
      )}
    >
      <span className="font-mono text-base">{score.toFixed(2)}</span>
      <span>{t(`contribute.review.relevance.${bucket}`)}</span>
    </div>
  );
}

interface ReviewViewProps {
  detail: ContributionDetail;
  onSubmit: () => void;
  onAbandon: () => void;
}

function ReviewView({ detail, onSubmit, onAbandon }: ReviewViewProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabKey>('all');
  const [keptIds, setKeptIds] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    detail.proposals.forEach((p) => {
      if (!p.target_kg_id) initial.add(p.proposal_id);
    });
    return initial;
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(
        buildKeptStorageKey(detail.contribution_id),
        JSON.stringify(Array.from(keptIds))
      );
    } catch {
      // ignore quota errors
    }
  }, [detail.contribution_id, keptIds]);

  const counts = useMemo(() => countByTab(detail.proposals), [detail.proposals]);
  const filtered = useMemo(
    () => detail.proposals.filter((p) => matchesTab(p, activeTab)),
    [detail.proposals, activeTab]
  );

  const totalCount = detail.proposals.length;
  const selectedCount = keptIds.size;

  const toggle = useCallback((proposalId: string) => {
    setKeptIds((prev) => {
      const next = new Set(prev);
      if (next.has(proposalId)) {
        next.delete(proposalId);
      } else {
        next.add(proposalId);
      }
      return next;
    });
  }, []);

  return (
    <div className="space-y-6 pb-32">
      <header className="space-y-3">
        <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-stone-900 sm:text-3xl">
              {detail.title || t('contribute.review.untitled')}
            </h1>
            <p className="mt-1 text-sm text-stone-600">
              {detail.authors.length > 0
                ? detail.authors.join(', ')
                : t('contribute.review.unknownAuthors')}
              {detail.publication_year ? ` · ${detail.publication_year}` : ''}
              {detail.doi ? ` · DOI ${detail.doi}` : ''}
            </p>
          </div>
          <RelevancePill score={detail.relevance_score} />
        </div>

        {detail.free_will_concepts.length > 0 && (
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-stone-500">
              {t('contribute.review.conceptsIdentified')}
            </h2>
            <div className="mt-2 flex flex-wrap gap-2">
              {detail.free_will_concepts.map((concept) => (
                <span
                  key={concept}
                  className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800 ring-1 ring-amber-200"
                >
                  {concept}
                </span>
              ))}
            </div>
          </div>
        )}

        {detail.relevance_summary && (
          <div className="rounded-xl border border-stone-200 bg-white/70 p-4">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-stone-500">
              {t('contribute.review.relevanceSummary')}
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-stone-700">
              {detail.relevance_summary}
            </p>
          </div>
        )}
      </header>

      <nav
        aria-label={t('contribute.review.tabsAria')}
        className="flex flex-wrap gap-2 border-b border-stone-200 pb-1"
      >
        {TABS.map((tab) => {
          const isActive = tab === activeTab;
          return (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              aria-pressed={isActive}
              className={cn(
                'rounded-t-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-amber-100 text-amber-900'
                  : 'text-stone-600 hover:bg-stone-100'
              )}
            >
              {t(`contribute.review.tabs.${tab}`)}{' '}
              <span className="ml-1 rounded-full bg-stone-200/70 px-2 py-0.5 text-xs font-mono">
                {counts[tab]}
              </span>
            </button>
          );
        })}
      </nav>

      {filtered.length === 0 ? (
        <p className="rounded-lg border border-dashed border-stone-300 bg-white/60 px-4 py-8 text-center text-sm text-stone-500">
          {t('contribute.review.emptyTab')}
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((proposal) => (
            <ProposalCard
              key={proposal.proposal_id}
              proposal={proposal}
              selected={keptIds.has(proposal.proposal_id)}
              onToggle={() => toggle(proposal.proposal_id)}
            />
          ))}
        </div>
      )}

      <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-amber-200 bg-white/95 backdrop-blur">
        <div className="academic-container flex flex-col items-stretch justify-between gap-3 py-3 sm:flex-row sm:items-center">
          <p className="text-sm text-stone-600">
            {t('contribute.review.selectionCount', {
              selected: selectedCount,
              total: totalCount,
            })}
          </p>
          <div className="flex gap-2">
            <Button variant="destructive" onClick={onAbandon}>
              {t('contribute.review.abandon')}
            </Button>
            <Button variant="warning" onClick={onSubmit}>
              {t('contribute.review.submit')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ContributePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [state, setState] = useState<PageState>({ kind: 'empty' });
  const pollTimerRef = useRef<number | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (pollTimerRef.current !== null) {
        window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, []);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const pollContribution = useCallback(
    async (contributionId: string) => {
      try {
        const detail = await getContribution(contributionId);
        if (!isMountedRef.current) return;
        setState((prev) => {
          if (prev.kind !== 'processing') return prev;
          if (prev.contributionId !== contributionId) return prev;
          if (detail.status === 'ready') {
            stopPolling();
            return { kind: 'review', detail };
          }
          if (detail.status === 'failed') {
            stopPolling();
            return {
              kind: 'failed',
              contributionId,
              detail,
              message: t('contribute.errors.processingFailed'),
            };
          }
          return { ...prev, detail };
        });
      } catch (err) {
        if (!isMountedRef.current) return;
        const message = err instanceof Error ? err.message : 'unknown_error';
        setState((prev) => {
          if (prev.kind !== 'processing') return prev;
          if (prev.contributionId !== contributionId) return prev;
          stopPolling();
          return {
            kind: 'failed',
            contributionId,
            detail: prev.detail,
            message,
          };
        });
      }
    },
    [stopPolling, t]
  );

  const startPolling = useCallback(
    (contributionId: string) => {
      stopPolling();
      pollTimerRef.current = window.setInterval(() => {
        void pollContribution(contributionId);
      }, POLL_INTERVAL_MS);
      void pollContribution(contributionId);
    },
    [pollContribution, stopPolling]
  );

  const handleFilePicked = useCallback((file: File) => {
    setState({ kind: 'metadata', file });
  }, []);

  const handleSubmitMetadata = useCallback(
    async (file: File, form: MetadataForm) => {
      const startedAt = Date.now();
      const parsedYear = form.publicationYear.trim()
        ? Number(form.publicationYear)
        : undefined;
      const placeholder: PageState = {
        kind: 'processing',
        file,
        contributionId: '',
        upload: {
          contribution_id: '',
          status: 'uploaded',
          pdf_signed_url: '',
          estimated_processing_seconds: 60,
        },
        detail: null,
        startedAt,
        uploadProgress: 0,
        metadata: form,
      };
      setState(placeholder);

      try {
        const upload = await uploadContribution(
          file,
          {
            title: form.title.trim() || undefined,
            authors: form.authors.trim() || undefined,
            doi: form.doi.trim() || undefined,
            publication_year:
              typeof parsedYear === 'number' && !Number.isNaN(parsedYear)
                ? parsedYear
                : undefined,
          },
          {
            onUploadProgress: (ratio) => {
              if (!isMountedRef.current) return;
              setState((prev) => {
                if (prev.kind !== 'processing') return prev;
                return { ...prev, uploadProgress: ratio };
              });
            },
          }
        );

        if (!isMountedRef.current) return;
        setState((prev) => {
          if (prev.kind !== 'processing') return prev;
          return {
            ...prev,
            contributionId: upload.contribution_id,
            upload,
            uploadProgress: 1,
          };
        });
        startPolling(upload.contribution_id);
      } catch (err) {
        if (!isMountedRef.current) return;
        const message = err instanceof Error ? err.message : 'upload_failed';
        setState({
          kind: 'failed',
          contributionId: '',
          detail: null,
          message,
        });
      }
    },
    [startPolling]
  );

  const handleCancelProcessing = useCallback(() => {
    stopPolling();
    setState({ kind: 'empty' });
  }, [stopPolling]);

  const handleAbandon = useCallback(
    async (contributionId: string) => {
      try {
        await rejectContribution(contributionId, 'abandoned by submitter');
      } catch {
        // Best-effort; we still navigate away.
      }
      try {
        window.localStorage.removeItem(buildKeptStorageKey(contributionId));
      } catch {
        // ignore
      }
      navigate('/');
    },
    [navigate]
  );

  const handleSubmitForModeration = useCallback(
    (contributionId: string) => {
      navigate(`/contributions/${contributionId}`);
    },
    [navigate]
  );

  return (
    <div className="min-h-screen w-full pt-28 pb-16">
      <div className="academic-container relative z-10">
        <AnimatePresence mode="wait">
          {state.kind === 'empty' && (
            <motion.section
              key="empty"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="mx-auto max-w-3xl"
            >
              <header className="mb-8 text-center">
                <h1 className="text-3xl font-bold text-stone-900 sm:text-4xl">
                  {t('contribute.empty.title')}
                </h1>
                <p className="mt-3 text-base leading-relaxed text-stone-600">
                  {t('contribute.empty.subtitle')}
                </p>
              </header>
              <UploadZone onFilePicked={handleFilePicked} />
              <HowItWorks />
            </motion.section>
          )}

          {state.kind === 'metadata' && (
            <motion.section
              key="metadata"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="mx-auto max-w-3xl"
            >
              <header className="mb-6">
                <h1 className="text-2xl font-bold text-stone-900">
                  {t('contribute.metadata.title')}
                </h1>
                <p className="mt-2 text-sm text-stone-600">
                  {t('contribute.metadata.subtitle')}
                </p>
              </header>
              <MetadataFormSection
                file={state.file}
                initial={{ title: '', authors: '', doi: '', publicationYear: '' }}
                onSubmit={(form) => void handleSubmitMetadata(state.file, form)}
                onReset={() => setState({ kind: 'empty' })}
                submitting={false}
              />
            </motion.section>
          )}

          {state.kind === 'processing' && (
            <motion.section
              key="processing"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
            >
              <ProcessingStatus
                contributionId={state.contributionId || 'pending'}
                status={state.detail?.status ?? state.upload.status}
                estimatedSeconds={state.upload.estimated_processing_seconds}
                startedAt={state.startedAt}
                uploadProgress={state.uploadProgress}
                metadata={{
                  title: state.metadata.title || state.file.name,
                  authors: state.metadata.authors,
                  doi: state.metadata.doi,
                  publicationYear: state.metadata.publicationYear
                    ? Number(state.metadata.publicationYear)
                    : undefined,
                }}
                onCancel={handleCancelProcessing}
              />
            </motion.section>
          )}

          {state.kind === 'review' && (
            <motion.section
              key="review"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
            >
              <ReviewView
                detail={state.detail}
                onSubmit={() => handleSubmitForModeration(state.detail.contribution_id)}
                onAbandon={() => void handleAbandon(state.detail.contribution_id)}
              />
            </motion.section>
          )}

          {state.kind === 'failed' && (
            <motion.section
              key="failed"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="mx-auto max-w-2xl text-center"
            >
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100 text-red-600">
                <AlertTriangle className="h-8 w-8" aria-hidden="true" />
              </div>
              <h1 className="mt-4 text-2xl font-bold text-stone-900">
                {t('contribute.failed.title')}
              </h1>
              <p className="mt-2 text-sm text-stone-600">
                {state.message || t('contribute.failed.body')}
              </p>
              <div className="mt-6 flex justify-center gap-2">
                <Button variant="ghost" onClick={() => navigate('/')}>
                  <ArrowLeft className="mr-1 h-4 w-4" aria-hidden="true" />
                  {t('contribute.failed.backHome')}
                </Button>
                <Button variant="warning" onClick={() => setState({ kind: 'empty' })}>
                  {t('contribute.failed.retry')}
                </Button>
              </div>
            </motion.section>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
