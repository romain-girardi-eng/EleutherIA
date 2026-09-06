import {
  ArrowRight,
  BookOpen,
  Check,
  Copy,
  ExternalLink,
  FileText,
  GitBranch,
  Hash,
  LoaderCircle,
  Quote,
  RefreshCw,
  Sparkles,
  Users,
  X,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { memo, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import type { KGNode } from '../types';
import {
  buildNodeCitation,
  isNodeCitationEligible,
  type FrozenCitationArchive,
} from './nodeCitation';

interface RelatedNode {
  id: string;
  label: string;
  type: string;
  relation: string;
  direction: 'incoming' | 'outgoing';
}

interface NodeDetailPanelProps {
  node: KGNode | null;
  onClose: () => void;
  onNavigateToNode?: (nodeId: string) => void;
  relationships?: RelatedNode[];
  /**
   * When true, render the panel as a half-height bottom sheet (mobile)
   * instead of the full-height right rail (desktop). The graph beneath
   * stays visible so the user can keep zooming/panning.
   */
  mobileHalf?: boolean;
  /** Reserve the graph workspace control row above the desktop dossier. */
  workspaceChromeOffset?: boolean;
  detailState?: { loading: boolean; error: Error | null };
  onRetryDetail?: () => void;
  releaseId?: string | null;
}

const APP_COMMIT = [
  import.meta.env.VITE_APP_COMMIT,
  import.meta.env.VITE_COMMIT_SHA,
].find((value): value is string => typeof value === 'string' && value.trim().length > 0)?.trim();
const ZENODO_VERSION_DOI = typeof import.meta.env.VITE_ZENODO_VERSION_DOI === 'string'
  ? import.meta.env.VITE_ZENODO_VERSION_DOI.trim()
  : '';
const KG_SNAPSHOT_DATE = typeof import.meta.env.VITE_KG_SNAPSHOT_DATE === 'string'
  ? import.meta.env.VITE_KG_SNAPSHOT_DATE.trim()
  : '';
const ARCHIVED_KG_RELEASE_ID = typeof import.meta.env.VITE_KG_RELEASE_ID === 'string'
  ? import.meta.env.VITE_KG_RELEASE_ID.trim()
  : '';
const FROZEN_CITATION_ARCHIVE: FrozenCitationArchive | null =
  APP_COMMIT
  && ZENODO_VERSION_DOI
  && ARCHIVED_KG_RELEASE_ID
  && /^\d{4}-\d{2}-\d{2}$/.test(KG_SNAPSHOT_DATE)
    ? {
        versionDoi: ZENODO_VERSION_DOI,
        commit: APP_COMMIT,
        snapshotDate: KG_SNAPSHOT_DATE,
        releaseId: ARCHIVED_KG_RELEASE_ID,
      }
    : null;

function getTypePresentation(type: string) {
  const palette: Record<string, { label: string; color: string }> = {
    person: { label: 'Thinker', color: '#1d4e89' },
    work: { label: 'Work', color: '#a16207' },
    concept: { label: 'Concept', color: '#c2410c' },
    argument: { label: 'Argument', color: '#9f1239' },
    debate: { label: 'Debate', color: '#7c2d12' },
    school: { label: 'School', color: '#3f6212' },
    quote: { label: 'Quote', color: '#b45309' },
    passage: { label: 'Passage', color: '#0369a1' },
    publication: { label: 'Publication', color: '#0f766e' },
    event: { label: 'Event', color: '#9f1239' },
    group: { label: 'Group', color: '#57534e' },
    controversy: { label: 'Controversy', color: '#b91c1c' },
    reformulation: { label: 'Reformulation', color: '#4d7c0f' },
  };

  return palette[type] ?? {
    label: type.replace(/_/g, ' '),
    color: '#57534e',
  };
}

function formatRelationLabel(relation: string) {
  return relation
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatScholarshipItem(source: string | { author?: string; year?: number; title?: string; publication?: string; citation?: string; text?: string }) {
  if (typeof source === 'string') {
    return source;
  }

  if (source.citation) return source.citation;
  if (source.text) return source.text;

  const parts = [
    source.author,
    source.year ? `(${source.year})` : undefined,
    source.title,
    source.publication,
  ].filter(Boolean);

  return parts.join('. ');
}

function markdownClassName() {
  return [
    'prose prose-stone prose-sm max-w-none font-reader',
    'prose-headings:font-display prose-headings:font-medium prose-headings:text-stone-950',
    'prose-p:text-stone-700 prose-p:leading-7',
    'prose-strong:text-stone-950',
    'prose-em:text-stone-700',
    'prose-li:text-stone-700',
    'prose-ul:my-4 prose-ol:my-4',
    'prose-blockquote:border-l-orange-700 prose-blockquote:text-stone-700',
    'prose-code:text-stone-900 prose-code:before:content-none prose-code:after:content-none',
    'prose-a:text-orange-800 prose-a:underline-offset-4',
  ].join(' ');
}

function displayMetadataValue(value: unknown): string | null {
  if (typeof value === 'string' && value.trim()) return value;
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return null;
}

const NodeDetailPanel = memo(function NodeDetailPanel({
  node,
  onClose,
  onNavigateToNode,
  relationships = [],
  mobileHalf = false,
  workspaceChromeOffset = false,
  detailState,
  onRetryDetail,
  releaseId,
}: NodeDetailPanelProps) {
  const { t } = useTranslation();
  const [copiedCitation, setCopiedCitation] = useState(false);
  const [citationError, setCitationError] = useState(false);
  const [linkedTextId, setLinkedTextId] = useState<string | null>(null);
  const [checkingText, setCheckingText] = useState(false);
  const panelRef = useRef<HTMLElement | null>(null);
  const navigate = useNavigate();
  const nodeId = node?.id;
  const nodeType = node?.type;

  useEffect(() => {
    if (!nodeId) return;
    panelRef.current?.focus({ preventScroll: true });
  }, [nodeId]);

  useEffect(() => {
    if (!node) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      event.preventDefault();
      onClose();
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [node, onClose]);

  useEffect(() => {
    let cancelled = false;
    if (nodeType === 'work' && nodeId) {
      setCheckingText(true);
      setLinkedTextId(null);
      apiClient.getWork(nodeId)
        .then((work) => {
          if (cancelled) return;
          if (work) {
            setLinkedTextId(work.work_id);
          } else {
            setLinkedTextId(null);
          }
        })
        .catch((error) => {
          console.error('Error checking for linked work:', error);
          setLinkedTextId(null);
        })
        .finally(() => {
          if (!cancelled) setCheckingText(false);
        });
    } else {
      setLinkedTextId(null);
      setCheckingText(false);
    }
    return () => {
      cancelled = true;
    };
  }, [nodeId, nodeType]);

  if (!node) return null;

  const typePresentation = getTypePresentation(node.type);
  const ancientSources = node.ancient_sources ?? [];
  const modernScholarship = Array.isArray(node.modern_scholarship)
    ? node.modern_scholarship
    : Array.isArray(node.metadata?.modern_scholarship)
      ? node.metadata.modern_scholarship
      : typeof node.metadata?.modern_scholarship === 'string'
        ? [node.metadata.modern_scholarship]
        : [];
  const metadata = node.metadata ?? {};
  const ancientLocus = ['passage', 'quote'].includes(node.type)
    && ['grc', 'lat', 'el', 'la'].includes(String(metadata.language ?? '').toLowerCase())
    && Boolean(metadata.canonical_ref || (typeof metadata.cts_urn === 'string' && metadata.cts_urn.split(':').length === 5))
    && Boolean(metadata.work_title || metadata.work_canonical_id || metadata.cts_urn);
  const sourceDebts = ['needs_page_verification', 'needs_reference_remapping', 'source_identity_unresolved', 'needs_reocr', 'needs_locus_mapping', 'needs_text_ingestion']
    .filter(key => key !== 'needs_page_verification' || !ancientLocus)
    .map(key => metadata[key])
    .filter(value => typeof value === 'string'
      ? !['', 'false', '0', 'no', 'off', 'none', 'null'].includes(value.trim().toLowerCase())
      : value === true || value === 1);
  const scholarlyStatus = sourceDebts.length > 0
    ? t('graphRagUi.evidence.sourceFlagged', 'Source verification required')
    : displayMetadataValue(node.scholarly_role)
    ?? displayMetadataValue(metadata.citability)
    ?? displayMetadataValue(metadata.provenance_status)
    ?? t('kg.nodeDetail.editorialRecord', 'Editorial graph record');

  const quickFacts = [
    node.period
      ? {
          key: 'period',
          label: 'Period',
          value: node.period,
        }
      : null,
    node.school
      ? {
          key: 'school',
          label: 'School',
          value: node.school,
        }
      : null,
    node.dates
      ? {
          key: 'dates',
          label: 'Dates',
          value: node.dates,
        }
      : null,
  ].filter(Boolean) as Array<{ key: string; label: string; value: string }>;
  const scholarlyMetadata = [
    ['Citability', metadata.citability],
    ['Citation verdict', sourceDebts.length ? undefined : metadata.citation_verdict],
    ['Citation verified', sourceDebts.length ? undefined : metadata.citation_verified],
    ['Provenance status', metadata.provenance_status],
    ['Provenance note', metadata.provenance_note],
    ['Canonical locus', metadata.canonical_locus],
    ['CTS URN', metadata.cts_urn],
    ['Source locator', metadata.source_locator],
    ['Publication ID', metadata.publication_id],
    ['Passage ID', metadata.passage_id],
    ['Work ID', metadata.work_id],
  ].map(([label, value]) => ({ label: String(label), value: displayMetadataValue(value) }))
    .filter((row): row is { label: string; value: string } => row.value !== null);

  const generateCitation = () => {
    if (!releaseId || !FROZEN_CITATION_ARCHIVE) return '';
    return buildNodeCitation(node, releaseId, FROZEN_CITATION_ARCHIVE);
  };

  const citationReady = Boolean(
    releaseId
    && FROZEN_CITATION_ARCHIVE
    && FROZEN_CITATION_ARCHIVE.releaseId === releaseId
    && sourceDebts.length === 0
    && isNodeCitationEligible(node)
    && node.description !== undefined
    && !detailState?.loading
    && !detailState?.error,
  );

  const copyCitation = async () => {
    if (!citationReady) return;
    try {
      await navigator.clipboard.writeText(generateCitation());
      setCitationError(false);
      setCopiedCitation(true);
      window.setTimeout(() => setCopiedCitation(false), 2000);
    } catch {
      setCopiedCitation(false);
      setCitationError(true);
    }
  };

  return (
    <>
      <aside
        ref={panelRef}
        tabIndex={-1}
        aria-labelledby="node-detail-title"
        aria-busy={detailState?.loading || undefined}
        className={
          mobileHalf
            ? 'fixed inset-x-0 bottom-0 z-50 h-[55svh] max-h-[55svh] overflow-hidden rounded-t-[1.5rem] border-t border-stone-300 bg-[#fcf9f4] text-stone-900 shadow-[0_-20px_55px_rgba(72,52,36,0.18)]'
            : 'fixed inset-y-12 right-0 z-50 w-full overflow-hidden border-l border-t-[3px] border-l-stone-300 border-t-orange-800 bg-[#fcf9f4] text-stone-900 shadow-[-24px_0_70px_rgba(72,52,36,0.16)] sm:w-[26rem] xl:w-[29rem]'
        }
      >
        <div className="flex h-full flex-col">
          <div
            className={[
              'sticky top-0 z-10 border-b border-stone-300 bg-[#fcf9f4] px-5 pb-4 sm:px-6',
              workspaceChromeOffset && !mobileHalf ? 'pt-[4.5rem]' : 'pt-3.5',
            ].join(' ')}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className="inline-flex items-center gap-2 border-b px-0 pb-1 font-body text-[10px] font-semibold uppercase tracking-[0.16em]"
                    style={{
                      borderColor: typePresentation.color,
                      color: typePresentation.color,
                    }}
                  >
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: typePresentation.color }}
                    />
                    {typePresentation.label}
                  </span>
                  {node.category && (
                    <span className="font-body text-[10px] font-medium uppercase tracking-[0.14em] text-stone-500">
                      {node.category}
                    </span>
                  )}
                </div>

                <h2 id="node-detail-title" className="mt-3 font-display text-[1.7rem] font-medium leading-tight text-stone-950 sm:text-[1.95rem]">
                  {node.label}
                </h2>

                {(node.greek_term || node.latin_term) && (
                  <div className="mt-3 space-y-1 font-reader">
                    {node.greek_term && (
                      <p className="break-words text-base text-stone-800">
                        {node.greek_term}
                      </p>
                    )}
                    {node.latin_term && (
                      <p className="break-words text-sm italic text-stone-600">
                        {node.latin_term}
                      </p>
                    )}
                  </div>
                )}
                {node.english_term && (
                  <p className="mt-1 font-reader text-sm text-stone-600">{node.english_term}</p>
                )}
              </div>

              <button
                type="button"
                onClick={onClose}
                className="inline-flex h-11 w-11 shrink-0 items-center justify-center border border-stone-300 bg-[#fffdf9] text-stone-600 transition-colors hover:border-orange-700 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
                aria-label="Close panel"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-5 border-t border-stone-200 pt-3 font-body">
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-500">
                  {t('kg.nodeDetail.scholarlyStatus', 'Scholarly status')}
                </p>
                {releaseId && (
                  <p className="font-mono text-[10px] text-stone-400" title={releaseId}>
                    release …{releaseId.slice(-10)}
                  </p>
                )}
              </div>
              <p className="mt-1 text-sm font-semibold text-stone-800">{scholarlyStatus}</p>
              {sourceDebts.length > 0 && (
                <div role="note" className="mt-3 rounded-lg border border-amber-300 bg-amber-50 px-3 py-3 text-sm leading-6 text-amber-950">
                  <p>{t('graphRagUi.evidence.sourceFlaggedBody', 'This record can help locate a source, but must not be cited as verified evidence until its outstanding checks are resolved.')}</p>
                  {sourceDebts.filter((value): value is string => typeof value === 'string').map((note, index) => <p key={index} className="mt-2">{note}</p>)}
                </div>
              )}
              {quickFacts.length > 0 && (
                <dl className="mt-3 grid grid-cols-3 gap-3 border-t border-stone-200 pt-3">
                  {quickFacts.map((fact) => (
                    <div key={fact.key} className="min-w-0">
                      <dt className="text-[9px] font-semibold uppercase tracking-[0.12em] text-stone-400">{fact.label}</dt>
                      <dd className="mt-1 truncate text-xs text-stone-700" title={fact.value}>{fact.value}</dd>
                    </div>
                  ))}
                </dl>
              )}
              <p className="mt-3 text-[11px] text-stone-500">
                {ancientSources.length} ancient sources · {modernScholarship.length} modern references · {relationships.length} relations
              </p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto px-5 pb-8 sm:px-6">
            <div className="space-y-0">
              <PanelCard
                title={t('kg.nodeDetail.description')}
                icon={Sparkles}
              >
                {detailState?.loading && (
                  <p role="status" aria-live="polite" className="mb-4 flex items-center gap-2 border-l-2 border-amber-600 pl-3 font-body text-sm text-stone-600">
                    <LoaderCircle className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
                    {t('kg.nodeDetail.loadingDetail', 'Loading release-bound editorial detail…')}
                  </p>
                )}
                {detailState?.error && (
                  <div role="alert" className="mb-4 border-l-2 border-red-700 pl-3 font-body text-sm leading-6 text-stone-700">
                    <p>{t('kg.nodeDetail.detailError', 'Full editorial detail could not be loaded. The release-bound summary remains available.')}</p>
                    {onRetryDetail && (
                      <button
                        type="button"
                        onClick={onRetryDetail}
                        className="mt-2 inline-flex min-h-11 items-center gap-2 font-semibold text-red-800 underline decoration-red-300 underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-700"
                      >
                        <RefreshCw className="h-4 w-4" aria-hidden="true" />
                        {t('kg.nodeDetail.retryDetail', 'Retry full detail')}
                      </button>
                    )}
                  </div>
                )}
                <div className={markdownClassName()}>
                  <ReactMarkdown>{node.description || 'No description available.'}</ReactMarkdown>
                </div>
              </PanelCard>

              {node.position_on_free_will && (
                <PanelCard
                  title={t('kg.nodeDetail.position')}
                  icon={Quote}
                  accentColor={typePresentation.color}
                >
                  <div className="border-l-2 border-orange-700 pl-4">
                    <div className={markdownClassName()}>
                      <ReactMarkdown>{node.position_on_free_will}</ReactMarkdown>
                    </div>
                  </div>
                </PanelCard>
              )}

              {ancientSources.length > 0 && (
                <CollapsiblePanelCard
                  title={`${t('kg.nodeDetail.ancientSources')} (${ancientSources.length})`}
                  icon={BookOpen}
                  defaultOpen
                >
                  <div className="space-y-2.5">
                    {ancientSources.map((source, index) => (
                      <ReferenceRow
                        key={`${source}-${index}`}
                        index={index + 1}
                        text={source}
                      />
                    ))}
                  </div>
                </CollapsiblePanelCard>
              )}

              {modernScholarship.length > 0 && (
                <CollapsiblePanelCard
                  title={`${t('kg.nodeDetail.modernScholarship')} (${modernScholarship.length})`}
                  icon={Users}
                  defaultOpen
                >
                  <div className="space-y-2.5">
                    {modernScholarship.map((source, index) => (
                      <ReferenceRow
                        key={`${index}-${typeof source === 'string' ? source : JSON.stringify(source)}`}
                        index={index + 1}
                        text={formatScholarshipItem(source)}
                      />
                    ))}
                  </div>
                </CollapsiblePanelCard>
              )}

              {relationships.length > 0 && (
                <CollapsiblePanelCard
                  title={`${t('kg.nodeDetail.relationships')} (${relationships.length})`}
                  icon={GitBranch}
                  defaultOpen
                >
                  <div className="space-y-2.5">
                    {relationships.map((rel, index) => (
                      <button
                        key={`${rel.id}-${index}`}
                        type="button"
                        onClick={() => onNavigateToNode && onNavigateToNode(rel.id)}
                        className="group flex w-full items-start gap-3 border-t border-stone-200 px-0 py-3 text-left transition-colors first:border-t-0 hover:bg-orange-50/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-orange-700"
                      >
                        <span
                          className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full"
                          style={{ backgroundColor: getTypePresentation(rel.type).color }}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <ArrowRight
                              className={[
                                'h-3.5 w-3.5 shrink-0 text-orange-700',
                                rel.direction === 'incoming' ? 'rotate-180' : '',
                              ].join(' ')}
                            />
                            <span className="font-body text-[10px] font-semibold uppercase tracking-[0.13em] text-orange-800">
                              {formatRelationLabel(rel.relation)}
                            </span>
                          </div>
                          <p className="mt-1.5 font-body text-sm font-semibold text-stone-800 transition-colors group-hover:text-orange-900">
                            {rel.label}
                          </p>
                          <p className="mt-1 font-body text-xs text-stone-500">
                            {getTypePresentation(rel.type).label}
                          </p>
                        </div>
                        <ExternalLink className="mt-1 h-4 w-4 shrink-0 text-stone-400 transition-colors group-hover:text-orange-700" />
                      </button>
                    ))}
                  </div>
                </CollapsiblePanelCard>
              )}

              <PanelCard
                title={t('kg.nodeDetail.actions')}
                icon={GitBranch}
              >
                <div className="flex flex-wrap gap-2.5">
                  {node.type === 'work' && (
                    <>
                      {checkingText ? (
                        <ActionButton disabled icon={FileText} variant="ghost">
                          {t('kg.nodeDetail.checking')}
                        </ActionButton>
                      ) : linkedTextId ? (
                        <ActionButton
                          icon={FileText}
                          variant="primary"
                          onClick={() => navigate(`/texts/${linkedTextId}`)}
                        >
                          {t('kg.nodeDetail.openText')}
                        </ActionButton>
                      ) : (
                        <ActionButton disabled icon={FileText} variant="ghost">
                          {t('kg.nodeDetail.textNotAvailable')}
                        </ActionButton>
                      )}
                    </>
                  )}

                  {citationReady ? (
                    <ActionButton
                      icon={copiedCitation ? Check : Copy}
                      variant={copiedCitation ? 'success' : 'primary'}
                      onClick={() => void copyCitation()}
                    >
                      {copiedCitation ? t('kg.nodeDetail.copied') : t('kg.nodeDetail.copyCitation')}
                    </ActionButton>
                  ) : (
                    <ActionButton disabled icon={Copy} variant="ghost">
                      {t('kg.nodeDetail.citationUnavailable', 'Citation unavailable until detail and frozen archive are verified')}
                    </ActionButton>
                  )}

                  {onNavigateToNode && (
                    <ActionButton
                      icon={GitBranch}
                      variant="secondary"
                      onClick={() => onNavigateToNode(node.id)}
                    >
                      {t('kg.nodeDetail.viewConnections')}
                    </ActionButton>
                  )}

                  <ActionButton
                    as="a"
                    href="https://doi.org/10.5281/zenodo.17379489"
                    target="_blank"
                    rel="noopener noreferrer"
                    icon={ExternalLink}
                    variant="ghost"
                  >
                    {t('kg.nodeDetail.viewDatabase')}
                  </ActionButton>
                </div>
              </PanelCard>

              {copiedCitation && (
                <div className="border-l-2 border-lime-700 bg-lime-50/60 px-4 py-3">
                  <div className="flex items-center gap-2 font-body text-xs font-semibold uppercase tracking-[0.14em] text-lime-900">
                    <Check className="h-3.5 w-3.5" />
                    {t('kg.nodeDetail.copied')}
                  </div>
                  <p className="mt-3 break-words border-t border-lime-200 pt-3 font-mono text-xs leading-6 text-stone-700">
                    {generateCitation()}
                  </p>
                </div>
              )}

              {citationError && (
                <p role="alert" className="border-l-2 border-red-700 pl-3 font-body text-sm leading-6 text-red-800">
                  {t('kg.nodeDetail.copyCitationError', 'The citation could not be copied. Check clipboard permission and try again.')}
                </p>
              )}

              <PanelCard
                title="Metadata"
                icon={Hash}
              >
                <dl className="font-body text-sm text-stone-700">
                  <div className="border-t border-stone-200 py-3 first:border-t-0">
                    <dt className="text-[10px] font-semibold uppercase tracking-[0.13em] text-stone-500">
                      {t('kg.nodeDetail.nodeId')}
                    </dt>
                    <dd><code className="mt-2 block break-all font-mono text-xs text-stone-700">
                      {node.id}
                    </code></dd>
                  </div>

                  {node.category && (
                    <div className="border-t border-stone-200 py-3">
                      <dt className="text-[10px] font-semibold uppercase tracking-[0.13em] text-stone-500">
                        {t('kg.nodeDetail.category')}
                      </dt>
                      <dd className="mt-1 text-stone-800">
                        {node.category}
                      </dd>
                    </div>
                  )}
                  {scholarlyMetadata.map((row) => (
                    <div key={row.label} className="border-t border-stone-200 py-3">
                      <dt className="text-[10px] font-semibold uppercase tracking-[0.13em] text-stone-500">{row.label}</dt>
                      <dd className="mt-1 break-words text-stone-800">{row.value}</dd>
                    </div>
                  ))}
                </dl>
              </PanelCard>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
});

function PanelCard({
  title,
  icon: Icon,
  accentColor,
  children,
}: {
  title: string;
  icon: typeof Sparkles;
  accentColor?: string;
  children: import('react').ReactNode;
}) {
  return (
    <section className="border-t border-stone-300 py-5 first:border-t-0">
      <div className="mb-4 flex items-center gap-2 font-body text-[10px] font-semibold uppercase tracking-[0.15em] text-stone-500">
        <Icon
          className="h-3.5 w-3.5"
          style={{ color: accentColor ?? '#9a3412' }}
        />
        {title}
      </div>
      {children}
    </section>
  );
}

function CollapsiblePanelCard({
  title,
  icon: Icon,
  defaultOpen = false,
  children,
}: {
  title: string;
  icon: typeof Sparkles;
  defaultOpen?: boolean;
  children: import('react').ReactNode;
}) {
  return (
    <section className="border-t border-stone-300 py-5 first:border-t-0">
      <details className="group" open={defaultOpen}>
        <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 font-body text-[10px] font-semibold uppercase tracking-[0.15em] text-stone-500 transition-colors hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700">
          <Icon className="h-3.5 w-3.5 text-orange-800" />
          <span>{title}</span>
          <span className="ml-auto text-stone-400 transition-transform group-open:rotate-180">
            ▼
          </span>
        </summary>
        <div className="mt-4">
          {children}
        </div>
      </details>
    </section>
  );
}

function ReferenceRow({
  index,
  text,
}: {
  index: number;
  text: string;
}) {
  return (
    <div className="flex items-start gap-3 border-t border-stone-200 py-3 first:border-t-0">
      <span className="inline-flex h-7 min-w-7 items-center justify-center border border-stone-300 bg-[#fffdf9] px-2 font-body text-[10px] font-semibold text-stone-500">
        {index}
      </span>
      <p className="min-w-0 flex-1 break-words font-reader text-sm leading-6 text-stone-700">
        {text}
      </p>
    </div>
  );
}

function ActionButton({
  as = 'button',
  href,
  target,
  rel,
  onClick,
  icon: Icon,
  variant,
  disabled = false,
  children,
}: {
  as?: 'button' | 'a';
  href?: string;
  target?: string;
  rel?: string;
  onClick?: () => void;
  icon: typeof Sparkles;
  variant: 'primary' | 'secondary' | 'ghost' | 'success';
  disabled?: boolean;
  children: import('react').ReactNode;
}) {
  const className = [
    'inline-flex min-h-11 items-center gap-2 border px-3.5 py-2.5 font-body text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700 focus-visible:ring-offset-2 focus-visible:ring-offset-[#fcf9f4]',
    disabled
      ? 'cursor-not-allowed border-stone-200 bg-stone-100 text-stone-400'
      : variant === 'primary'
        ? 'border-orange-800 bg-orange-800 text-[#fffaf1] hover:bg-orange-900'
        : variant === 'secondary'
          ? 'border-stone-400 bg-[#fffdf9] text-stone-800 hover:border-orange-700 hover:text-orange-800'
          : variant === 'success'
            ? 'border-lime-700 bg-lime-50 text-lime-900 hover:bg-lime-100'
            : 'border-stone-300 bg-transparent text-stone-600 hover:border-stone-500 hover:text-stone-900',
  ].join(' ');

  if (as === 'a') {
    return (
      <a
        href={href}
        target={target}
        rel={rel}
        className={className}
      >
        <Icon className="h-4 w-4" />
        {children}
      </a>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={className}
    >
      <Icon className="h-4 w-4" />
      {children}
    </button>
  );
}

export default NodeDetailPanel;
