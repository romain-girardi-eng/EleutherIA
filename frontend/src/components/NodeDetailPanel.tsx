import { X, BookOpen, Quote, Users, GitBranch, Calendar, GraduationCap, ExternalLink, ArrowRight, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useState, useEffect, memo } from 'react';
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

// Memoized to prevent re-renders when props haven't changed
const NodeDetailPanel = memo(function NodeDetailPanel({ node, onClose, onNavigateToNode, relationships = [] }: NodeDetailPanelProps) {
  const { t } = useTranslation();
  const [copiedCitation, setCopiedCitation] = useState(false);
  const [linkedTextId, setLinkedTextId] = useState<string | null>(null);
  const [checkingText, setCheckingText] = useState(false);
  const navigate = useNavigate();

  // Check if this work node has a linked work in the ancient_works table
  useEffect(() => {
    if (node?.type === 'work' && node?.id) {
      setCheckingText(true);
      // Use the new works API - work nodes now directly reference work_id
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

  // Generate citation
  const generateCitation = () => {
    const year = new Date().getFullYear();
    return `Girardi, Romain. (${year}). "${node.label}". In *EleutherIA: Ancient Free Will Database* (Node ID: ${node.id}). https://free-will.app/node/${node.id}. DOI: 10.5281/zenodo.17379490`;
  };

  const copyCitation = () => {
    navigator.clipboard.writeText(generateCitation());
    setCopiedCitation(true);
    setTimeout(() => setCopiedCitation(false), 2000);
  };

  // Color mapping for node types
  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      person: '#0284c7',
      work: '#7dd3fc',
      concept: '#fbbf24',
      argument: '#f87171',
      debate: '#a78bfa',
      reformulation: '#34d399',
      quote: '#fb923c',
    };
    return colors[type] || '#64748b';
  };

  return (
    <>
      {/* Backdrop - visual only, doesn't close panel on click */}
      <div
        className="fixed top-20 left-0 right-0 bottom-0 bg-black bg-opacity-30 z-40 transition-opacity pointer-events-none"
      />

      {/* Sliding Panel */}
      <div className="fixed right-0 top-20 bottom-0 w-full sm:w-[28rem] bg-academic-paper shadow-2xl overflow-y-auto z-50 transform transition-transform duration-300 ease-in-out">
        {/* Header */}
        <div
          className="sticky top-0 text-white p-4 sm:p-6 flex justify-between items-start gap-4 z-10"
          style={{ backgroundColor: getTypeColor(node.type) }}
        >
          <div className="flex-1 min-w-0">
            <div className="text-xs sm:text-sm opacity-90 uppercase tracking-wide mb-1 sm:mb-2">
              {node.type}
            </div>
            <h2 className="text-xl sm:text-2xl font-serif font-bold leading-tight break-words">
              {node.label}
            </h2>
            {node.greek_term && (
              <div className="text-sm sm:text-base mt-2 sm:mt-3 font-light opacity-95 break-words">
                {node.greek_term}
              </div>
            )}
            {node.latin_term && (
              <div className="text-sm sm:text-base mt-1 font-light italic opacity-90 break-words">
                {node.latin_term}
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 rounded p-2.5 sm:p-2 flex-shrink-0 transition-colors min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Close panel"
          >
            <X className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
          {/* Quick Metadata */}
          {(node.period || node.school || node.dates) && (
            <div className="flex flex-wrap gap-2">
              {node.period && (
                <span className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 bg-primary-50 text-primary-700 rounded-full">
                  <Calendar className="w-3.5 h-3.5" />
                  {node.period}
                </span>
              )}
              {node.school && (
                <span className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 bg-primary-50 text-primary-700 rounded-full">
                  <GraduationCap className="w-3.5 h-3.5" />
                  {node.school}
                </span>
              )}
              {node.dates && (
                <span className="text-xs px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full">
                  {node.dates}
                </span>
              )}
            </div>
          )}

          {/* Description */}
          <section>
            <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3">
              {t('kg.nodeDetail.description')}
            </h3>
            <div className="prose prose-sm max-w-none text-academic-text leading-relaxed">
              <ReactMarkdown>{node.description || 'No description available.'}</ReactMarkdown>
            </div>
          </section>

          {/* Position on Free Will */}
          {node.position_on_free_will && (
            <section className="border-t border-academic-border pt-4 sm:pt-6">
              <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3">
                {t('kg.nodeDetail.position')}
              </h3>
              <div className="prose prose-sm max-w-none text-academic-text">
                <ReactMarkdown>{node.position_on_free_will}</ReactMarkdown>
              </div>
            </section>
          )}

          {/* Terminology */}
          {(node.greek_term || node.latin_term || node.english_term) && (
            <section className="border-t border-academic-border pt-4 sm:pt-6">
              <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3 flex items-center gap-2">
                <Quote className="w-4 h-4" />
                {t('kg.nodeDetail.terminology')}
              </h3>
              <dl className="space-y-3 text-sm">
                {node.greek_term && (
                  <div>
                    <dt className="text-academic-muted font-medium mb-1">{t('kg.nodeDetail.greek')}</dt>
                    <dd className="font-serif text-base text-academic-text break-words">
                      {node.greek_term}
                    </dd>
                  </div>
                )}
                {node.latin_term && (
                  <div>
                    <dt className="text-academic-muted font-medium mb-1">{t('kg.nodeDetail.latin')}</dt>
                    <dd className="font-serif text-base text-academic-text italic break-words">
                      {node.latin_term}
                    </dd>
                  </div>
                )}
                {node.english_term && (
                  <div>
                    <dt className="text-academic-muted font-medium mb-1">{t('kg.nodeDetail.english')}</dt>
                    <dd className="text-academic-text break-words">{node.english_term}</dd>
                  </div>
                )}
              </dl>
            </section>
          )}

          {/* Ancient Sources - Expandable */}
          {node.ancient_sources && node.ancient_sources.length > 0 && (
            <section className="border-t border-academic-border pt-4 sm:pt-6">
              <details className="group" open>
                <summary className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3 cursor-pointer flex items-center gap-2 hover:text-primary-600 transition-colors">
                  <BookOpen className="w-4 h-4" />
                  {t('kg.nodeDetail.ancientSources')} ({node.ancient_sources.length})
                  <span className="ml-auto text-xs group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <ul className="mt-3 space-y-2 text-xs sm:text-sm">
                  {node.ancient_sources.map((source: string, i: number) => (
                    <li
                      key={i}
                      className="pl-3 sm:pl-4 border-l-2 border-primary-200 text-academic-text py-1 break-words"
                    >
                      {source}
                    </li>
                  ))}
                </ul>
              </details>
            </section>
          )}

          {/* Modern Scholarship - Expandable */}
          {node.modern_scholarship && node.modern_scholarship.length > 0 && (
            <section className="border-t border-academic-border pt-4 sm:pt-6">
              <details className="group" open>
                <summary className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3 cursor-pointer flex items-center gap-2 hover:text-primary-600 transition-colors">
                  <Users className="w-4 h-4" />
                  {t('kg.nodeDetail.modernScholarship')} ({node.modern_scholarship.length})
                  <span className="ml-auto text-xs group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <ul className="mt-3 space-y-2 text-xs sm:text-sm">
                  {node.modern_scholarship.map((source: string | { author?: string; year?: number; title?: string; publication?: string }, i: number) => (
                    <li
                      key={i}
                      className="pl-3 sm:pl-4 border-l-2 border-primary-200 text-academic-text py-1 break-words"
                    >
                      {typeof source === 'string'
                        ? source
                        : `${source.author} (${source.year}). ${source.title}. ${source.publication}.`}
                    </li>
                  ))}
                </ul>
              </details>
            </section>
          )}

          {/* Relationships */}
          {relationships && relationships.length > 0 && (
            <section className="border-t border-academic-border pt-4 sm:pt-6">
              <details className="group" open>
                <summary className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3 cursor-pointer flex items-center gap-2 hover:text-primary-600 transition-colors">
                  <GitBranch className="w-4 h-4" />
                  {t('kg.nodeDetail.relationships')} ({relationships.length})
                  <span className="ml-auto text-xs group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <div className="mt-3 space-y-2">
                  {relationships.map((rel, i) => (
                    <button
                      key={`${rel.id}-${i}`}
                      onClick={() => onNavigateToNode && onNavigateToNode(rel.id)}
                      className="w-full text-left p-3 bg-gray-50 hover:bg-primary-50 rounded-lg transition-colors group/rel border border-gray-200 hover:border-primary-300"
                    >
                      <div className="flex items-start gap-2">
                        <div className="flex-shrink-0 mt-0.5">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: getTypeColor(rel.type) }}
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            {rel.direction === 'outgoing' ? (
                              <ArrowRight className="w-3.5 h-3.5 text-primary-600 flex-shrink-0" />
                            ) : (
                              <ArrowRight className="w-3.5 h-3.5 text-primary-600 flex-shrink-0 rotate-180" />
                            )}
                            <span className="text-xs font-medium text-primary-600 uppercase tracking-wide">
                              {rel.relation}
                            </span>
                          </div>
                          <p className="text-sm font-semibold text-gray-900 group-hover/rel:text-primary-700 transition-colors truncate">
                            {rel.label}
                          </p>
                          <p className="text-xs text-gray-500 mt-0.5">
                            {rel.type}
                          </p>
                        </div>
                        <ExternalLink className="w-4 h-4 text-gray-400 group-hover/rel:text-primary-600 transition-colors flex-shrink-0 mt-1" />
                      </div>
                    </button>
                  ))}
                </div>
              </details>
            </section>
          )}

          {/* Actions */}
          <section className="border-t border-academic-border pt-4 sm:pt-6">
            <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3 flex items-center gap-2">
              <GitBranch className="w-4 h-4" />
              {t('kg.nodeDetail.actions')}
            </h3>
            <div className="flex flex-wrap gap-2">
              {/* Open Text Button - only for work nodes with linked texts */}
              {node.type === 'work' && (
                <>
                  {checkingText ? (
                    <button
                      disabled
                      className="text-xs sm:text-sm px-3 sm:px-4 py-2 bg-gray-100 text-gray-400 rounded-lg flex items-center gap-2 cursor-not-allowed"
                      aria-label="Checking for text availability"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      {t('kg.nodeDetail.checking')}
                    </button>
                  ) : linkedTextId ? (
                    <button
                      onClick={() => navigate(`/texts/${linkedTextId}`)}
                      className="text-xs sm:text-sm px-3 sm:px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center gap-2"
                      aria-label={`Read ${node.label} in full text viewer`}
                      title={`Open ${node.label} in the text viewer`}
                    >
                      <FileText className="w-3.5 h-3.5" />
                      {t('kg.nodeDetail.openText')}
                    </button>
                  ) : (
                    <div className="text-xs sm:text-sm px-3 sm:px-4 py-2 bg-gray-50 text-gray-500 rounded-lg flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5" />
                      {t('kg.nodeDetail.textNotAvailable')}
                    </div>
                  )}
                </>
              )}
              <button
                onClick={copyCitation}
                className="text-xs sm:text-sm px-3 sm:px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <Quote className="w-3.5 h-3.5" />
                {copiedCitation ? t('kg.nodeDetail.copied') : t('kg.nodeDetail.copyCitation')}
              </button>
              {onNavigateToNode && (
                <button
                  onClick={() => onNavigateToNode(node.id)}
                  className="text-xs sm:text-sm px-3 sm:px-4 py-2 bg-primary-50 hover:bg-primary-100 text-primary-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <GitBranch className="w-3.5 h-3.5" />
                  {t('kg.nodeDetail.viewConnections')}
                </button>
              )}
              <a
                href={`https://doi.org/10.5281/zenodo.17379490`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs sm:text-sm px-3 sm:px-4 py-2 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg transition-colors flex items-center gap-2"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                {t('kg.nodeDetail.viewDatabase')}
              </a>
            </div>
          </section>

          {/* Citation Preview */}
          {copiedCitation && (
            <section className="bg-green-50 border border-green-200 rounded-lg p-3 sm:p-4">
              <h4 className="text-xs font-semibold text-green-900 mb-2">{t('kg.nodeDetail.copied')}</h4>
              <p className="text-xs text-green-800 font-mono break-words leading-relaxed">
                {generateCitation()}
              </p>
            </section>
          )}

          {/* Metadata Footer */}
          <section className="border-t border-academic-border pt-4 text-xs text-academic-muted space-y-1">
            <div>
              <span className="font-medium">{t('kg.nodeDetail.nodeId')}</span>{' '}
              <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs break-all">
                {node.id}
              </code>
            </div>
            {node.category && (
              <div>
                <span className="font-medium">{t('kg.nodeDetail.category')}</span> {node.category}
              </div>
            )}
          </section>
        </div>
      </div>
    </>
  );
}, (prevProps, nextProps) => {
  // Only re-render if node or relationships changed
  return prevProps.node?.id === nextProps.node?.id &&
         prevProps.relationships === nextProps.relationships;
});

export default NodeDetailPanel;
