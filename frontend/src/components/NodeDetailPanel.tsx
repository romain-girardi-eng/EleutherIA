import {
  AlertTriangle,
  BookOpen,
  Check,
  ChevronDown,
  Copy,
  ExternalLink,
  FileText,
  GitBranch,
  LoaderCircle,
  Quote,
  RefreshCw,
  ScrollText,
  Users,
  X,
  type LucideIcon,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { AnimatePresence, motion, useDragControls, useReducedMotion, type PanInfo } from 'framer-motion';
import {
  memo,
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import type { KGNode } from '../types';
import {
  buildNodeCitation,
  isNodeCitationEligible,
  type FrozenCitationArchive,
} from './nodeCitation';
import { RelationsSection } from './nodeDetail/RelationsSection';
import {
  detectTextLanguage,
  displayMetadataValue,
  humanize,
  isPrimaryTextBody,
  modernScholarshipOf,
  recordStatus,
  sourceDebts,
  typeColor,
  type RecordStatus,
  type RelatedNode,
} from './nodeDetail/nodeDetailModel';

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

const EMPTY_RELATIONS: RelatedNode[] = [];
const REFERENCE_PREVIEW = 6;
const EASE_OUT_QUART = [0.25, 1, 0.5, 1] as const;

const MARKDOWN_CLASS = [
  'prose prose-stone max-w-[65ch] font-reader text-[1.02rem]',
  'prose-headings:font-display prose-headings:font-medium prose-headings:text-stone-950',
  'prose-p:text-stone-800 prose-p:leading-[1.7]',
  'prose-strong:text-stone-950',
  'prose-em:text-stone-800',
  'prose-li:text-stone-800',
  'prose-ul:my-4 prose-ol:my-4',
  'prose-blockquote:border-l-orange-700 prose-blockquote:text-stone-700',
  'prose-code:text-stone-900 prose-code:before:content-none prose-code:after:content-none',
  'prose-a:text-orange-800 prose-a:underline-offset-4',
].join(' ');

const NodeDetailPanel = memo(function NodeDetailPanel(props: NodeDetailPanelProps) {
  const reduceMotion = useReducedMotion() ?? false;
  const { node, mobileHalf = false } = props;
  const initial = reduceMotion
    ? { opacity: 0 }
    : mobileHalf ? { y: '100%' } : { x: '100%' };
  const settled = mobileHalf ? { y: 0, opacity: 1 } : { x: 0, opacity: 1 };

  return (
    <AnimatePresence>
      {node && (
        <motion.aside
          key={mobileHalf ? 'dossier-sheet' : 'dossier-rail'}
          initial={initial}
          animate={settled}
          exit={initial}
          transition={{ duration: reduceMotion ? 0.12 : 0.32, ease: EASE_OUT_QUART }}
          aria-labelledby="node-detail-title"
          aria-busy={props.detailState?.loading || undefined}
          className={
            mobileHalf
              ? 'fixed inset-x-0 bottom-0 z-50 text-stone-900'
              : 'fixed inset-y-12 right-0 z-50 w-full overflow-hidden border-l border-t-[3px] border-l-stone-300 border-t-orange-800 bg-[#fcf9f4] text-stone-900 shadow-[-24px_0_70px_rgba(72,52,36,0.16)] sm:w-[27rem] xl:w-[30rem]'
          }
        >
          <DossierBody {...props} node={node} reduceMotion={reduceMotion} />
        </motion.aside>
      )}
    </AnimatePresence>
  );
});

function DossierBody({
  node,
  onClose,
  onNavigateToNode,
  relationships = EMPTY_RELATIONS,
  mobileHalf = false,
  workspaceChromeOffset = false,
  detailState,
  onRetryDetail,
  releaseId,
  reduceMotion,
}: NodeDetailPanelProps & { node: KGNode; reduceMotion: boolean }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const titleRef = useRef<HTMLHeadingElement | null>(null);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [expandedSheet, setExpandedSheet] = useState(false);
  const dragControls = useDragControls();
  const sectionPrefix = useId();
  const nodeId = node.id;
  const nodeType = node.type;

  // Parents pass fresh closures on every render; routing through a ref keeps
  // the memoized relation list from re-rendering with them.
  const navigateRef = useRef(onNavigateToNode);
  const closeRef = useRef(onClose);
  useLayoutEffect(() => {
    navigateRef.current = onNavigateToNode;
    closeRef.current = onClose;
  });
  const hasNavigate = Boolean(onNavigateToNode);
  const stableNavigate = useCallback((id: string) => navigateRef.current?.(id), []);

  useEffect(() => {
    const previous = document.activeElement;
    const root = rootRef.current;
    return () => {
      const active = document.activeElement;
      const focusWasInside = !active || active === document.body || Boolean(root?.contains(active));
      if (focusWasInside && previous instanceof HTMLElement && previous.isConnected) {
        previous.focus({ preventScroll: true });
      }
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
    titleRef.current?.focus({ preventScroll: true });
  }, [nodeId]);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape' || event.defaultPrevented) return;
      const target = event.target;
      const root = rootRef.current;
      const editableOutside = target instanceof HTMLElement
        && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
        && !root?.contains(target);
      if (editableOutside) return;
      event.preventDefault();
      closeRef.current();
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, []);

  const [linkedText, setLinkedText] = useState<{ nodeId: string; workId: string | null } | null>(null);
  useEffect(() => {
    if (nodeType !== 'work') return;
    let cancelled = false;
    apiClient.getWork(nodeId)
      .then((work) => {
        if (!cancelled) setLinkedText({ nodeId, workId: work ? work.work_id : null });
      })
      .catch(() => {
        if (!cancelled) setLinkedText({ nodeId, workId: null });
      });
    return () => {
      cancelled = true;
    };
  }, [nodeId, nodeType]);
  const checkingText = nodeType === 'work' && linkedText?.nodeId !== nodeId;
  const linkedTextId = linkedText?.nodeId === nodeId ? linkedText.workId : null;

  const metadata = node.metadata ?? {};
  const debts = useMemo(() => sourceDebts(node), [node]);
  const status = useMemo(() => recordStatus(node, debts), [node, debts]);
  const ancientSources = node.ancient_sources ?? [];
  const modernScholarship = useMemo(() => modernScholarshipOf(node), [node]);
  const typeLabel = t(`kg.nodeDetail.types.${node.type}`, { defaultValue: humanize(node.type) });
  const accent = typeColor(node.type);
  const primaryText = isPrimaryTextBody(node);
  const textLang = primaryText ? detectTextLanguage(node) : undefined;
  const locus = typeof metadata.canonical_locus === 'string'
    ? metadata.canonical_locus
    : typeof metadata.cts_urn === 'string' ? metadata.cts_urn : null;

  const facts = [
    node.dates ? { key: 'dates', label: t('kg.nodeDetail.facts.dates', 'Dates'), value: node.dates } : null,
    node.period ? { key: 'period', label: t('kg.nodeDetail.facts.period', 'Period'), value: node.period } : null,
    node.school ? { key: 'school', label: t('kg.nodeDetail.facts.school', 'School'), value: node.school } : null,
  ].filter((fact): fact is { key: string; label: string; value: string } => fact !== null);

  const yes = t('kg.nodeDetail.yes', 'Yes');
  const no = t('kg.nodeDetail.no', 'No');
  const recordRows = [
    ['nodeId', node.id],
    ['category', node.category],
    ['citability', metadata.citability],
    ['citationVerdict', debts.length ? undefined : metadata.citation_verdict],
    ['citationVerified', debts.length ? undefined : metadata.citation_verified],
    ['provenanceStatus', metadata.provenance_status],
    ['provenanceNote', metadata.provenance_note],
    ['canonicalLocus', metadata.canonical_locus],
    ['ctsUrn', metadata.cts_urn],
    ['sourceLocator', metadata.source_locator],
    ['publicationId', metadata.publication_id],
    ['passageId', metadata.passage_id],
    ['workId', metadata.work_id],
    ['release', releaseId],
  ].map(([key, value]) => ({ key: String(key), value: displayMetadataValue(value, yes, no) }))
    .filter((row): row is { key: string; value: string } => row.value !== null);

  const citationReady = Boolean(
    releaseId
    && FROZEN_CITATION_ARCHIVE
    && FROZEN_CITATION_ARCHIVE.releaseId === releaseId
    && debts.length === 0
    && isNodeCitationEligible(node)
    && node.description !== undefined
    && !detailState?.loading
    && !detailState?.error,
  );

  const sectionId = (name: string) => `${sectionPrefix}-${name}`;
  const jumpTo = (name: string) => {
    document.getElementById(sectionId(name))?.scrollIntoView({
      behavior: reduceMotion ? 'auto' : 'smooth',
      block: 'start',
    });
  };
  const jumps = [
    relationships.length > 0 ? { name: 'relations', label: t('kg.nodeDetail.count.relations', { count: relationships.length, defaultValue: '{{count}} relations' }) } : null,
    ancientSources.length > 0 ? { name: 'ancient', label: t('kg.nodeDetail.count.ancient', { count: ancientSources.length, defaultValue: '{{count}} ancient sources' }) } : null,
    modernScholarship.length > 0 ? { name: 'modern', label: t('kg.nodeDetail.count.modern', { count: modernScholarship.length, defaultValue: '{{count}} modern references' }) } : null,
  ].filter((jump): jump is { name: string; label: string } => jump !== null);

  const onSheetDragEnd = (_event: PointerEvent | MouseEvent | TouchEvent, info: PanInfo) => {
    const pull = info.offset.y + info.velocity.y * 0.2;
    if (pull < -60) setExpandedSheet(true);
    else if (pull > 60) {
      if (expandedSheet) setExpandedSheet(false);
      else closeRef.current();
    }
  };

  const body = (
    <div ref={rootRef} className="flex h-full flex-col">
      <header
        className={[
          'relative shrink-0 border-b border-stone-300 bg-[#fcf9f4] px-5 pb-3 sm:px-6',
          mobileHalf ? 'pt-1' : workspaceChromeOffset ? 'pt-[4.5rem]' : 'pt-4',
        ].join(' ')}
      >
        {mobileHalf && (
          <button
            type="button"
            onPointerDown={(event) => dragControls.start(event)}
            onClick={() => setExpandedSheet((value) => !value)}
            aria-expanded={expandedSheet}
            aria-label={expandedSheet
              ? t('kg.nodeDetail.collapseSheet', 'Collapse the record')
              : t('kg.nodeDetail.expandSheet', 'Expand the record')}
            className="mx-auto flex h-7 w-24 touch-none items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
          >
            <span className="h-1.5 w-11 rounded-full bg-stone-300" aria-hidden="true" />
          </button>
        )}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-body text-[10px] font-semibold uppercase tracking-[0.16em]">
              <span className="inline-flex items-center gap-1.5" style={{ color: accent }}>
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: accent }} aria-hidden="true" />
                {typeLabel}
              </span>
              {node.category && <span className="font-medium text-stone-500">{node.category}</span>}
            </div>
            <h2
              id="node-detail-title"
              ref={titleRef}
              tabIndex={-1}
              className={[
                'mt-2 font-display font-medium leading-[1.12] text-stone-950 [overflow-wrap:anywhere] focus:outline-none',
                mobileHalf ? 'text-[1.45rem]' : 'text-[1.7rem] sm:text-[1.9rem]',
              ].join(' ')}
            >
              {node.label}
            </h2>
            {(node.greek_term || node.latin_term || node.english_term) && (
              <p className="mt-1.5 font-reader text-[1.02rem] leading-snug text-stone-700">
                {node.greek_term && <span lang="grc" className="text-stone-900">{node.greek_term}</span>}
                {node.greek_term && node.latin_term && <span className="text-stone-400" aria-hidden="true"> · </span>}
                {node.latin_term && <span lang="la" className="italic">{node.latin_term}</span>}
                {node.english_term && (
                  <span className="block text-sm text-stone-500">{node.english_term}</span>
                )}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={() => closeRef.current()}
            className="-mr-2 inline-flex h-11 w-11 shrink-0 items-center justify-center text-stone-500 transition-colors hover:bg-stone-200/50 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700"
            aria-label={t('kg.nodeDetail.close', 'Close record')}
            title={t('kg.nodeDetail.closeHint', 'Close (Esc)')}
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {(facts.length > 0 || locus) && (
          <dl className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 font-body text-[13px] leading-snug">
            {facts.map((fact) => (
              <div key={fact.key} className="min-w-0">
                <dt className="text-[10px] font-semibold uppercase tracking-[0.12em] text-stone-500">{fact.label}</dt>
                <dd className="text-stone-800">{fact.value}</dd>
              </div>
            ))}
            {locus && (
              <div className="min-w-0 basis-full">
                <dt className="text-[10px] font-semibold uppercase tracking-[0.12em] text-stone-500">{t('kg.nodeDetail.facts.locus', 'Locus')}</dt>
                <dd className="break-all font-mono text-xs text-stone-700">{locus}</dd>
              </div>
            )}
          </dl>
        )}

        <StatusLine status={status} />

        {jumps.length > 0 && (
          <nav aria-label={t('kg.nodeDetail.jumpNav', 'Sections of this record')} className="mt-2 flex flex-wrap gap-x-1 font-body text-xs">
            {jumps.map((jump, index) => (
              <span key={jump.name} className="inline-flex items-center">
                {index > 0 && <span className="px-1 text-stone-300" aria-hidden="true">·</span>}
                <button
                  type="button"
                  onClick={() => jumpTo(jump.name)}
                  className="inline-flex min-h-9 items-center text-teal-800 underline decoration-teal-700/25 underline-offset-4 hover:decoration-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
                >
                  {jump.label}
                </button>
              </span>
            ))}
          </nav>
        )}
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto overscroll-contain px-5 pb-[max(2rem,env(safe-area-inset-bottom))] sm:px-6">
        {debts.length > 0 && (
          <div role="note" className="mt-5 flex gap-3 border border-amber-300 bg-amber-50 px-3 py-3 font-body text-sm leading-6 text-amber-950">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" aria-hidden="true" />
            <div>
              <p>{t('graphRagUi.evidence.sourceFlaggedBody', 'This record can help locate a source, but must not be cited as verified evidence until its outstanding checks are resolved.')}</p>
              {debts.filter((value): value is string => typeof value === 'string').map((note, index) => <p key={index} className="mt-2">{note}</p>)}
            </div>
          </div>
        )}

        {detailState?.error && (
          <div role="alert" className="mt-5 border-l-2 border-red-700 pl-3 font-body text-sm leading-6 text-stone-700">
            <p>{t('kg.nodeDetail.detailError', 'The full record could not be loaded. The summary below is still available.')}</p>
            {onRetryDetail && (
              <button
                type="button"
                onClick={onRetryDetail}
                className="mt-1 inline-flex min-h-11 items-center gap-2 font-semibold text-red-800 underline decoration-red-300 underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-700"
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                {t('kg.nodeDetail.retryDetail', 'Try again')}
              </button>
            )}
          </div>
        )}

        <Section
          title={primaryText
            ? t('kg.nodeDetail.text', 'Text')
            : node.type === 'publication'
              ? t('kg.nodeDetail.reference', 'Reference')
              : t('kg.nodeDetail.overview', 'Overview')}
          icon={primaryText ? ScrollText : BookOpen}
        >
          {detailState?.loading && !node.description ? (
            <DescriptionSkeleton label={t('kg.nodeDetail.loadingDetail', 'Loading the full record…')} />
          ) : node.description ? (
            <ClampedText
              resetKey={nodeId}
              contentKey={node.description}
              moreLabel={t('kg.nodeDetail.readMore', 'Read more')}
              lessLabel={t('kg.nodeDetail.readLess', 'Show less')}
            >
              {primaryText ? (
                <PrimaryText text={node.description} lang={textLang} />
              ) : (
                <MarkdownBlock text={node.description} />
              )}
            </ClampedText>
          ) : (
            <p className="font-body text-sm italic text-stone-500">
              {t('kg.nodeDetail.noDescription', 'No description has been written for this record yet.')}
            </p>
          )}
          {detailState?.loading && node.description && (
            <p role="status" className="mt-3 flex items-center gap-2 font-body text-xs text-stone-500">
              <LoaderCircle className="h-3.5 w-3.5 motion-safe:animate-spin" aria-hidden="true" />
              {t('kg.nodeDetail.loadingDetail', 'Loading the full record…')}
            </p>
          )}
        </Section>

        {node.position_on_free_will && (
          <Section title={t('kg.nodeDetail.position', 'Position on free will')} icon={Quote}>
            <div className="border-l-2 border-orange-700 pl-4">
              <MarkdownBlock text={node.position_on_free_will} />
            </div>
          </Section>
        )}

        {relationships.length > 0 && (
          <Section
            id={sectionId('relations')}
            title={t('kg.nodeDetail.relationships', 'Relations')}
            count={relationships.length}
            icon={GitBranch}
          >
            <RelationsSection
              key={nodeId}
              relationships={relationships}
              onNavigate={hasNavigate ? stableNavigate : undefined}
            />
          </Section>
        )}

        {ancientSources.length > 0 && (
          <Section
            id={sectionId('ancient')}
            title={t('kg.nodeDetail.ancientSources', 'Ancient sources')}
            count={ancientSources.length}
            icon={ScrollText}
          >
            <ReferenceList key={nodeId} items={ancientSources} />
          </Section>
        )}

        {modernScholarship.length > 0 && (
          <Section
            id={sectionId('modern')}
            title={t('kg.nodeDetail.modernScholarship', 'Modern scholarship')}
            count={modernScholarship.length}
            icon={Users}
          >
            <ReferenceList key={nodeId} items={modernScholarship} />
          </Section>
        )}

        <Section title={t('kg.nodeDetail.actions', 'Actions')} icon={FileText}>
          <div className="flex flex-wrap gap-2.5">
            {node.type === 'work' && (
              checkingText ? (
                <ActionButton disabled icon={LoaderCircle} variant="ghost">
                  {t('kg.nodeDetail.checking', 'Checking…')}
                </ActionButton>
              ) : linkedTextId ? (
                <ActionButton icon={FileText} variant="primary" onClick={() => navigate(`/texts/${linkedTextId}`)}>
                  {t('kg.nodeDetail.openText', 'Open text')}
                </ActionButton>
              ) : (
                <ActionButton disabled icon={FileText} variant="ghost">
                  {t('kg.nodeDetail.textNotAvailable', 'Text not available')}
                </ActionButton>
              )
            )}
            <CitationAction
              ready={citationReady}
              build={() => (releaseId && FROZEN_CITATION_ARCHIVE
                ? buildNodeCitation(node, releaseId, FROZEN_CITATION_ARCHIVE)
                : '')}
              resetKey={nodeId}
            />
            {hasNavigate && (
              <ActionButton icon={GitBranch} variant="secondary" onClick={() => stableNavigate(nodeId)}>
                {t('kg.nodeDetail.viewConnections', 'Centre in the graph')}
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
              {t('kg.nodeDetail.viewDatabase', 'Dataset on Zenodo')}
            </ActionButton>
          </div>
        </Section>

        <details className="group mt-2 border-t border-stone-300 pt-1 font-body">
          <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-stone-500 hover:text-orange-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-700 [&::-webkit-details-marker]:hidden">
            {t('kg.nodeDetail.recordDetails', 'Record details')}
            <ChevronDown className="ml-auto h-4 w-4 transition-transform group-open:rotate-180 motion-reduce:transition-none" aria-hidden="true" />
          </summary>
          <dl className="pb-4 text-sm text-stone-700">
            {recordRows.map((row) => (
              <div key={row.key} className="grid grid-cols-[8.5rem_1fr] gap-3 border-t border-stone-200 py-2 first:border-t-0">
                <dt className="text-[11px] text-stone-500">{t(`kg.nodeDetail.fields.${row.key}`, humanize(row.key))}</dt>
                <dd className={[
                  'min-w-0 break-words text-stone-800',
                  ['nodeId', 'ctsUrn', 'release', 'workId', 'passageId', 'publicationId'].includes(row.key) ? 'break-all font-mono text-xs' : '',
                ].join(' ')}
                >
                  {row.value}
                </dd>
              </div>
            ))}
          </dl>
        </details>
      </div>
    </div>
  );

  if (!mobileHalf) return body;

  return (
    <motion.div
      drag="y"
      dragControls={dragControls}
      dragListener={false}
      dragConstraints={{ top: 0, bottom: 0 }}
      dragElastic={{ top: 0.08, bottom: 0.5 }}
      dragSnapToOrigin
      onDragEnd={onSheetDragEnd}
      initial={false}
      animate={{ height: expandedSheet ? '88svh' : '55svh' }}
      transition={{ duration: reduceMotion ? 0 : 0.28, ease: EASE_OUT_QUART }}
      className="h-[55svh] max-h-[88svh] overflow-hidden rounded-t-[1.25rem] border-t border-stone-300 bg-[#fcf9f4] shadow-[0_-20px_55px_rgba(72,52,36,0.18)]"
    >
      {body}
    </motion.div>
  );
}

function StatusLine({ status }: { status: RecordStatus }) {
  const { t } = useTranslation();
  if (!status) return null;
  const presentation = {
    flagged: { text: t('graphRagUi.evidence.sourceFlagged', 'Source verification required'), tone: 'text-amber-800', mark: 'bg-amber-600' },
    verified: { text: t('kg.nodeDetail.status.verified', 'References checked against the sources'), tone: 'text-teal-800', mark: 'bg-teal-700' },
    corrected: { text: t('kg.nodeDetail.status.corrected', 'References corrected after a source check'), tone: 'text-teal-800', mark: 'bg-teal-700' },
    pending: { text: t('kg.nodeDetail.status.pending', 'Provenance awaiting editorial review'), tone: 'text-amber-800', mark: 'bg-amber-500' },
    raw: { text: status.kind === 'raw' ? status.value : '', tone: 'text-stone-600', mark: 'bg-stone-400' },
  }[status.kind];
  return (
    <p className={`mt-2.5 flex items-center gap-2 font-body text-xs font-medium ${presentation.tone}`}>
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${presentation.mark}`} aria-hidden="true" />
      <span className="sr-only">{t('kg.nodeDetail.status.label', 'Editorial status:')} </span>
      {presentation.text}
    </p>
  );
}

function Section({
  id,
  title,
  count,
  icon: Icon,
  children,
}: {
  id?: string;
  title: string;
  count?: number;
  icon: LucideIcon;
  children: ReactNode;
}) {
  const headingId = useId();
  return (
    <section id={id} aria-labelledby={headingId} className="scroll-mt-3 border-t border-stone-300 py-5 first:border-t-0">
      <h3 id={headingId} className="mb-3 flex items-center gap-2 font-body text-[10px] font-semibold uppercase tracking-[0.15em] text-stone-500">
        <Icon className="h-3.5 w-3.5 text-orange-800" aria-hidden="true" />
        {title}
        {count !== undefined && <span className="font-medium tabular-nums text-stone-400">{count}</span>}
      </h3>
      {children}
    </section>
  );
}

const MarkdownBlock = memo(function MarkdownBlock({ text }: { text: string }) {
  return (
    <div className={MARKDOWN_CLASS}>
      <ReactMarkdown>{text}</ReactMarkdown>
    </div>
  );
});

/** Primary text is shown byte-for-byte: no Markdown, which would eat `*` and `_` sigla. */
const PrimaryText = memo(function PrimaryText({ text, lang }: { text: string; lang?: string }) {
  return (
    <div lang={lang} className="max-w-[62ch] whitespace-pre-line font-reader text-[1.08rem] leading-[1.75] text-stone-900 [hyphens:manual]">
      {text}
    </div>
  );
});

function ClampedText({
  children,
  resetKey,
  contentKey,
  moreLabel,
  lessLabel,
}: {
  children: ReactNode;
  resetKey: string;
  contentKey: string;
  moreLabel: string;
  lessLabel: string;
}) {
  const contentRef = useRef<HTMLDivElement | null>(null);
  const [expanded, setExpanded] = useState<{ key: string; open: boolean }>({ key: resetKey, open: false });
  const [overflowing, setOverflowing] = useState(false);
  const open = expanded.key === resetKey && expanded.open;
  const contentId = useId();

  useLayoutEffect(() => {
    const element = contentRef.current;
    if (!element) return;
    const measure = () => setOverflowing(element.scrollHeight > element.clientHeight + 4);
    measure();
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [resetKey, contentKey, open]);

  return (
    <div>
      <div
        id={contentId}
        ref={contentRef}
        className={open
          ? ''
          : 'max-h-[19rem] overflow-hidden [mask-image:linear-gradient(to_bottom,black_75%,transparent)]'}
      >
        {children}
      </div>
      {(overflowing || open) && (
        <button
          type="button"
          aria-expanded={open}
          aria-controls={contentId}
          onClick={() => setExpanded({ key: resetKey, open: !open })}
          className="mt-2 inline-flex min-h-11 items-center gap-1.5 font-body text-sm font-semibold text-teal-800 underline decoration-teal-700/30 underline-offset-4 hover:decoration-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
        >
          {open ? lessLabel : moreLabel}
          <ChevronDown className={`h-4 w-4 transition-transform motion-reduce:transition-none ${open ? 'rotate-180' : ''}`} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}

function DescriptionSkeleton({ label }: { label: string }) {
  return (
    <div role="status" aria-live="polite">
      <span className="sr-only">{label}</span>
      <div className="space-y-2.5 motion-safe:animate-pulse" aria-hidden="true">
        {['w-full', 'w-[94%]', 'w-[97%]', 'w-[88%]', 'w-[62%]'].map((width) => (
          <div key={width} className={`h-3.5 rounded-sm bg-stone-200/80 ${width}`} />
        ))}
      </div>
      <p className="mt-3 flex items-center gap-2 font-body text-xs text-stone-500" aria-hidden="true">
        <LoaderCircle className="h-3.5 w-3.5 motion-safe:animate-spin" />
        {label}
      </p>
    </div>
  );
}

const ReferenceList = memo(function ReferenceList({ items }: { items: ReadonlyArray<string> }) {
  const { t } = useTranslation();
  const [showAll, setShowAll] = useState(false);
  const shown = showAll ? items : items.slice(0, REFERENCE_PREVIEW);
  return (
    <>
      <ol className="divide-y divide-stone-200">
        {shown.map((text, index) => (
          <li key={`${index}-${text}`} className="flex gap-3 py-2.5">
            <span className="w-5 shrink-0 pt-0.5 text-right font-body text-[11px] tabular-nums text-stone-400">{index + 1}</span>
            <p className="min-w-0 flex-1 break-words font-reader text-[0.97rem] leading-relaxed text-stone-800">{text}</p>
          </li>
        ))}
      </ol>
      {items.length > REFERENCE_PREVIEW && (
        <button
          type="button"
          aria-expanded={showAll}
          onClick={() => setShowAll((value) => !value)}
          className="mt-1 inline-flex min-h-11 items-center font-body text-sm font-semibold text-teal-800 underline decoration-teal-700/30 underline-offset-4 hover:decoration-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-700"
        >
          {showAll
            ? t('kg.nodeDetail.showLess', 'Show less')
            : t('kg.nodeDetail.showAll', { defaultValue: 'Show all {{count}}', count: items.length })}
        </button>
      )}
    </>
  );
});

function CitationAction({
  ready,
  build,
  resetKey,
}: {
  ready: boolean;
  build: () => string;
  resetKey: string;
}) {
  const { t } = useTranslation();
  const hintId = useId();
  const [state, setState] = useState<{ key: string; kind: 'idle' | 'copied' | 'error'; text: string }>({
    key: resetKey,
    kind: 'idle',
    text: '',
  });
  const kind = state.key === resetKey ? state.kind : 'idle';

  useEffect(() => {
    if (kind !== 'copied') return;
    const timer = window.setTimeout(() => setState((current) => ({ ...current, kind: 'idle' })), 4000);
    return () => window.clearTimeout(timer);
  }, [kind]);

  if (!ready) {
    return (
      <div className="basis-full">
        <ActionButton disabled icon={Copy} variant="ghost" describedBy={hintId}>
          {t('kg.nodeDetail.citationUnavailableShort', 'Citation unavailable')}
        </ActionButton>
        <p id={hintId} className="mt-1.5 max-w-[48ch] font-body text-xs leading-5 text-stone-500">
          {t('kg.nodeDetail.citationUnavailable', 'A citation is offered only once the full record is loaded, its sources are verified and it belongs to an archived release.')}
        </p>
      </div>
    );
  }

  const copy = async () => {
    const text = build();
    try {
      await navigator.clipboard.writeText(text);
      setState({ key: resetKey, kind: 'copied', text });
    } catch {
      setState({ key: resetKey, kind: 'error', text: '' });
    }
  };

  return (
    <>
      <ActionButton
        icon={kind === 'copied' ? Check : Copy}
        variant={kind === 'copied' ? 'success' : 'primary'}
        onClick={() => void copy()}
      >
        {kind === 'copied' ? t('kg.nodeDetail.copied', 'Copied') : t('kg.nodeDetail.copyCitation', 'Copy citation')}
      </ActionButton>
      <div className="basis-full" aria-live="polite">
        {kind === 'copied' && (
          <p className="break-words border-l-2 border-lime-700 bg-lime-50/60 px-3 py-2 font-mono text-xs leading-6 text-stone-700">
            {state.text}
          </p>
        )}
        {kind === 'error' && (
          <p role="alert" className="border-l-2 border-red-700 pl-3 font-body text-sm leading-6 text-red-800">
            {t('kg.nodeDetail.copyCitationError', 'The citation could not be copied. Check clipboard permission and try again.')}
          </p>
        )}
      </div>
    </>
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
  describedBy,
  children,
}: {
  as?: 'button' | 'a';
  href?: string;
  target?: string;
  rel?: string;
  onClick?: () => void;
  icon: LucideIcon;
  variant: 'primary' | 'secondary' | 'ghost' | 'success';
  disabled?: boolean;
  describedBy?: string;
  children: ReactNode;
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
            : 'border-stone-300 bg-transparent text-stone-700 hover:border-stone-500 hover:text-stone-900',
  ].join(' ');

  if (as === 'a') {
    return (
      <a href={href} target={target} rel={rel} className={className}>
        <Icon className="h-4 w-4" aria-hidden="true" />
        {children}
      </a>
    );
  }

  return (
    <button type="button" onClick={onClick} disabled={disabled} aria-describedby={describedBy} className={className}>
      <Icon className="h-4 w-4" aria-hidden="true" />
      {children}
    </button>
  );
}

export default NodeDetailPanel;
