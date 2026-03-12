import {
  ArrowRight,
  BookOpen,
  Calendar,
  Check,
  Copy,
  ExternalLink,
  FileText,
  GitBranch,
  GraduationCap,
  Hash,
  Languages,
  Quote,
  Sparkles,
  Users,
  X,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { memo, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../api/client';
import type { KGNode } from '../types';

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
}

function getTypePresentation(type: string) {
  const palette: Record<string, { label: string; color: string; glow: string }> = {
    person: { label: 'Thinker', color: '#4cc9f0', glow: 'rgba(76, 201, 240, 0.22)' },
    work: { label: 'Work', color: '#f4d35e', glow: 'rgba(244, 211, 94, 0.2)' },
    concept: { label: 'Concept', color: '#ff8fab', glow: 'rgba(255, 143, 171, 0.22)' },
    argument: { label: 'Argument', color: '#ff6b6b', glow: 'rgba(255, 107, 107, 0.22)' },
    debate: { label: 'Debate', color: '#b794f4', glow: 'rgba(183, 148, 244, 0.22)' },
    school: { label: 'School', color: '#2ec4b6', glow: 'rgba(46, 196, 182, 0.22)' },
    quote: { label: 'Quote', color: '#f97316', glow: 'rgba(249, 115, 22, 0.2)' },
    passage: { label: 'Passage', color: '#7dd3fc', glow: 'rgba(125, 211, 252, 0.22)' },
    publication: { label: 'Publication', color: '#14b8a6', glow: 'rgba(20, 184, 166, 0.2)' },
    event: { label: 'Event', color: '#fb7185', glow: 'rgba(251, 113, 133, 0.22)' },
    group: { label: 'Group', color: '#818cf8', glow: 'rgba(129, 140, 248, 0.22)' },
    controversy: { label: 'Controversy', color: '#ef4444', glow: 'rgba(239, 68, 68, 0.22)' },
    reformulation: { label: 'Reformulation', color: '#34d399', glow: 'rgba(52, 211, 153, 0.22)' },
  };

  return palette[type] ?? {
    label: type.replace(/_/g, ' '),
    color: '#94a3b8',
    glow: 'rgba(148, 163, 184, 0.18)',
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
    'prose prose-invert prose-sm max-w-none',
    'prose-headings:text-white prose-headings:font-semibold',
    'prose-p:text-slate-300 prose-p:leading-7',
    'prose-strong:text-slate-100',
    'prose-em:text-slate-200',
    'prose-li:text-slate-300',
    'prose-ul:my-4 prose-ol:my-4',
    'prose-blockquote:border-l-cyan-300/30 prose-blockquote:text-slate-300',
    'prose-code:text-cyan-100 prose-code:before:content-none prose-code:after:content-none',
    'prose-a:text-cyan-200',
  ].join(' ');
}

const NodeDetailPanel = memo(function NodeDetailPanel({
  node,
  onClose,
  onNavigateToNode,
  relationships = [],
}: NodeDetailPanelProps) {
  const { t } = useTranslation();
  const [copiedCitation, setCopiedCitation] = useState(false);
  const [linkedTextId, setLinkedTextId] = useState<string | null>(null);
  const [checkingText, setCheckingText] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (node?.type === 'work' && node?.id) {
      setCheckingText(true);
      apiClient.getWork(node.id)
        .then((work) => {
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
          setCheckingText(false);
        });
    } else {
      setLinkedTextId(null);
    }
  }, [node]);

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

  const quickFacts = [
    node.period
      ? {
          key: 'period',
          icon: Calendar,
          label: 'Period',
          value: node.period,
        }
      : null,
    node.school
      ? {
          key: 'school',
          icon: GraduationCap,
          label: 'School',
          value: node.school,
        }
      : null,
    node.dates
      ? {
          key: 'dates',
          icon: Hash,
          label: 'Dates',
          value: node.dates,
        }
      : null,
  ].filter(Boolean) as Array<{ key: string; icon: typeof Calendar; label: string; value: string }>;

  const statTiles = [
    { label: 'Relations', value: relationships.length.toLocaleString() },
    { label: 'Ancient', value: ancientSources.length.toLocaleString() },
    { label: 'Modern', value: modernScholarship.length.toLocaleString() },
    { label: 'Category', value: node.category || 'Core node' },
  ];

  const generateCitation = () => {
    const year = new Date().getFullYear();
    return `Girardi, Romain. (${year}). "${node.label}". In *EleutherIA: Ancient Free Will Database* (Node ID: ${node.id}). https://free-will.app/node/${node.id}. DOI: 10.5281/zenodo.17379490`;
  };

  const copyCitation = () => {
    navigator.clipboard.writeText(generateCitation());
    setCopiedCitation(true);
    setTimeout(() => setCopiedCitation(false), 2000);
  };

  return (
    <>
      <div className="fixed inset-x-0 bottom-0 top-12 z-40 bg-slate-950/46 backdrop-blur-[2px] pointer-events-none" />

      <aside className="fixed inset-y-12 right-0 z-50 w-full overflow-hidden border-l border-white/10 bg-[linear-gradient(180deg,rgba(2,6,23,0.98)_0%,rgba(2,6,23,0.94)_100%)] text-slate-100 shadow-[-24px_0_90px_rgba(2,6,23,0.55)] sm:w-[31rem] xl:w-[34rem]">
        <div className="pointer-events-none absolute inset-0">
          <div
            className="absolute inset-x-0 top-0 h-64 opacity-90"
            style={{
              background: `radial-gradient(circle at top left, ${typePresentation.glow} 0%, transparent 52%)`,
            }}
          />
          <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.02)_0%,rgba(255,255,255,0)_20%,rgba(255,255,255,0)_100%)]" />
        </div>

        <div className="relative flex h-full flex-col">
          <div className="sticky top-0 z-10 border-b border-white/8 bg-[linear-gradient(180deg,rgba(3,7,18,0.94)_0%,rgba(3,7,18,0.86)_100%)] px-5 pb-5 pt-5 backdrop-blur-2xl sm:px-6">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]"
                    style={{
                      borderColor: `${typePresentation.color}40`,
                      backgroundColor: `${typePresentation.color}18`,
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
                    <span className="inline-flex items-center rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-slate-400">
                      {node.category}
                    </span>
                  )}
                </div>

                <h2 className="mt-4 text-2xl font-semibold leading-tight text-white sm:text-[2rem]">
                  {node.label}
                </h2>

                {(node.greek_term || node.latin_term) && (
                  <div className="mt-4 space-y-1">
                    {node.greek_term && (
                      <p className="text-base font-medium text-cyan-100 break-words">
                        {node.greek_term}
                      </p>
                    )}
                    {node.latin_term && (
                      <p className="text-sm italic text-slate-300 break-words">
                        {node.latin_term}
                      </p>
                    )}
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={onClose}
                className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-slate-300 transition-colors hover:border-white/20 hover:bg-white/[0.08] hover:text-white"
                aria-label="Close panel"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {quickFacts.length > 0 && (
              <div className="mt-5 flex flex-wrap gap-2">
                {quickFacts.map((fact) => {
                  const Icon = fact.icon;

                  return (
                    <span
                      key={fact.key}
                      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-slate-200"
                    >
                      <Icon className="h-3.5 w-3.5 text-slate-400" />
                      {fact.value}
                    </span>
                  );
                })}
              </div>
            )}
          </div>

          <div className="flex-1 overflow-y-auto px-5 pb-8 pt-5 sm:px-6">
            <div className="grid grid-cols-2 gap-3">
              {statTiles.map((tile) => (
                <div
                  key={tile.label}
                  className="rounded-[20px] border border-white/8 bg-white/[0.03] px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                    {tile.label}
                  </p>
                  <p className="mt-1 text-sm font-semibold text-slate-100 break-words">
                    {tile.value}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-5 space-y-4">
              <PanelCard
                title={t('kg.nodeDetail.description')}
                icon={Sparkles}
              >
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
                  <div className="rounded-[18px] border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.03)_0%,rgba(255,255,255,0.01)_100%)] p-4">
                    <div className={markdownClassName()}>
                      <ReactMarkdown>{node.position_on_free_will}</ReactMarkdown>
                    </div>
                  </div>
                </PanelCard>
              )}

              {(node.greek_term || node.latin_term || node.english_term) && (
                <PanelCard
                  title={t('kg.nodeDetail.terminology')}
                  icon={Languages}
                >
                  <div className="grid gap-3">
                    {node.greek_term && (
                      <TerminologyCard label={t('kg.nodeDetail.greek')} value={node.greek_term} accent="text-cyan-100" />
                    )}
                    {node.latin_term && (
                      <TerminologyCard label={t('kg.nodeDetail.latin')} value={node.latin_term} accent="text-amber-100 italic" />
                    )}
                    {node.english_term && (
                      <TerminologyCard label={t('kg.nodeDetail.english')} value={node.english_term} accent="text-slate-100" />
                    )}
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
                        className="group flex w-full items-start gap-3 rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3 text-left transition-all hover:border-white/16 hover:bg-white/[0.05]"
                      >
                        <span
                          className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full"
                          style={{ backgroundColor: getTypePresentation(rel.type).color }}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <ArrowRight
                              className={[
                                'h-3.5 w-3.5 shrink-0 text-cyan-200',
                                rel.direction === 'incoming' ? 'rotate-180' : '',
                              ].join(' ')}
                            />
                            <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-cyan-100/85">
                              {formatRelationLabel(rel.relation)}
                            </span>
                          </div>
                          <p className="mt-2 text-sm font-semibold text-slate-100 transition-colors group-hover:text-white">
                            {rel.label}
                          </p>
                          <p className="mt-1 text-xs text-slate-400">
                            {getTypePresentation(rel.type).label}
                          </p>
                        </div>
                        <ExternalLink className="mt-1 h-4 w-4 shrink-0 text-slate-500 transition-colors group-hover:text-cyan-200" />
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

                  <ActionButton
                    icon={copiedCitation ? Check : Copy}
                    variant={copiedCitation ? 'success' : 'primary'}
                    onClick={copyCitation}
                  >
                    {copiedCitation ? t('kg.nodeDetail.copied') : t('kg.nodeDetail.copyCitation')}
                  </ActionButton>

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
                    href="https://doi.org/10.5281/zenodo.17379490"
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
                <div className="rounded-[22px] border border-emerald-300/18 bg-emerald-300/[0.08] p-4 shadow-[0_12px_34px_rgba(16,185,129,0.08)]">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-100/90">
                    <Check className="h-3.5 w-3.5" />
                    {t('kg.nodeDetail.copied')}
                  </div>
                  <p className="mt-3 break-words rounded-[16px] border border-white/8 bg-black/10 px-3 py-3 font-mono text-xs leading-6 text-emerald-50/90">
                    {generateCitation()}
                  </p>
                </div>
              )}

              <PanelCard
                title="Metadata"
                icon={Hash}
              >
                <div className="space-y-3 text-sm text-slate-300">
                  <div className="rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                      {t('kg.nodeDetail.nodeId')}
                    </p>
                    <code className="mt-2 block break-all rounded-[12px] bg-black/20 px-3 py-2 text-xs text-cyan-100">
                      {node.id}
                    </code>
                  </div>

                  {node.category && (
                    <div className="rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3">
                      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                        {t('kg.nodeDetail.category')}
                      </p>
                      <p className="mt-2 text-slate-100">
                        {node.category}
                      </p>
                    </div>
                  )}
                </div>
              </PanelCard>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}, (prevProps, nextProps) => {
  return prevProps.node?.id === nextProps.node?.id &&
    prevProps.relationships === nextProps.relationships;
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
    <section className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] sm:p-5">
      <div className="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
        <Icon
          className="h-3.5 w-3.5"
          style={accentColor ? { color: accentColor } : undefined}
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
    <section className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] sm:p-5">
      <details className="group" open={defaultOpen}>
        <summary className="flex cursor-pointer list-none items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 transition-colors hover:text-slate-200">
          <Icon className="h-3.5 w-3.5" />
          <span>{title}</span>
          <span className="ml-auto text-slate-500 transition-transform group-open:rotate-180">
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

function TerminologyCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className="rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </p>
      <p className={`mt-2 break-words text-base ${accent}`}>
        {value}
      </p>
    </div>
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
    <div className="flex items-start gap-3 rounded-[18px] border border-white/8 bg-[#040916]/90 px-4 py-3">
      <span className="inline-flex h-7 min-w-7 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] px-2 text-[11px] font-semibold text-slate-300">
        {index}
      </span>
      <p className="min-w-0 flex-1 text-sm leading-6 text-slate-300 break-words">
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
    'inline-flex min-h-11 items-center gap-2 rounded-full border px-4 py-2.5 text-sm font-medium transition-colors',
    disabled
      ? 'cursor-not-allowed border-white/6 bg-white/[0.03] text-slate-500'
      : variant === 'primary'
        ? 'border-cyan-300/30 bg-cyan-300/[0.12] text-cyan-50 hover:border-cyan-300/40 hover:bg-cyan-300/[0.16]'
        : variant === 'secondary'
          ? 'border-amber-300/24 bg-amber-200/[0.1] text-amber-100 hover:border-amber-300/34 hover:bg-amber-200/[0.14]'
          : variant === 'success'
            ? 'border-emerald-300/26 bg-emerald-300/[0.12] text-emerald-50 hover:border-emerald-300/36 hover:bg-emerald-300/[0.16]'
            : 'border-white/10 bg-white/[0.04] text-slate-200 hover:border-white/18 hover:bg-white/[0.08]',
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
