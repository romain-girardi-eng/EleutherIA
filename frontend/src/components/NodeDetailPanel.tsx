import { X, BookOpen, Quote, Users, GitBranch, Calendar, GraduationCap, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useState } from 'react';
import type { KGNode } from '../types';

interface NodeDetailPanelProps {
  node: KGNode | null;
  onClose: () => void;
  onNavigateToNode?: (nodeId: string) => void;
}

export default function NodeDetailPanel({ node, onClose, onNavigateToNode }: NodeDetailPanelProps) {
  const [copiedCitation, setCopiedCitation] = useState(false);

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
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-30 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Sliding Panel */}
      <div className="fixed right-0 top-0 h-screen w-full sm:w-[28rem] bg-academic-paper shadow-2xl overflow-y-auto z-50 transform transition-transform duration-300 ease-in-out">
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
            className="text-white hover:bg-white hover:bg-opacity-20 rounded p-1.5 sm:p-2 flex-shrink-0 transition-colors"
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
              Description
            </h3>
            <div className="prose prose-sm max-w-none text-academic-text leading-relaxed">
              <ReactMarkdown>{node.description || 'No description available.'}</ReactMarkdown>
            </div>
          </section>

          {/* Position on Free Will */}
          {node.position_on_free_will && (
            <section className="border-t border-academic-border pt-4 sm:pt-6">
              <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3">
                Position on Free Will
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
                Terminology
              </h3>
              <dl className="space-y-3 text-sm">
                {node.greek_term && (
                  <div>
                    <dt className="text-academic-muted font-medium mb-1">Greek</dt>
                    <dd className="font-serif text-base text-academic-text break-words">
                      {node.greek_term}
                    </dd>
                  </div>
                )}
                {node.latin_term && (
                  <div>
                    <dt className="text-academic-muted font-medium mb-1">Latin</dt>
                    <dd className="font-serif text-base text-academic-text italic break-words">
                      {node.latin_term}
                    </dd>
                  </div>
                )}
                {node.english_term && (
                  <div>
                    <dt className="text-academic-muted font-medium mb-1">English</dt>
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
                  Ancient Sources ({node.ancient_sources.length})
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
                  Modern Scholarship ({node.modern_scholarship.length})
                  <span className="ml-auto text-xs group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <ul className="mt-3 space-y-2 text-xs sm:text-sm">
                  {node.modern_scholarship.map((source: string, i: number) => (
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

          {/* Actions */}
          <section className="border-t border-academic-border pt-4 sm:pt-6">
            <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wide mb-3 flex items-center gap-2">
              <GitBranch className="w-4 h-4" />
              Actions
            </h3>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={copyCitation}
                className="text-xs sm:text-sm px-3 sm:px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <Quote className="w-3.5 h-3.5" />
                {copiedCitation ? 'Copied!' : 'Copy Citation'}
              </button>
              {onNavigateToNode && (
                <button
                  onClick={() => onNavigateToNode(node.id)}
                  className="text-xs sm:text-sm px-3 sm:px-4 py-2 bg-primary-50 hover:bg-primary-100 text-primary-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <GitBranch className="w-3.5 h-3.5" />
                  View Connections
                </button>
              )}
              <a
                href={`https://doi.org/10.5281/zenodo.17379490`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs sm:text-sm px-3 sm:px-4 py-2 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg transition-colors flex items-center gap-2"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                View Database
              </a>
            </div>
          </section>

          {/* Citation Preview */}
          {copiedCitation && (
            <section className="bg-green-50 border border-green-200 rounded-lg p-3 sm:p-4">
              <h4 className="text-xs font-semibold text-green-900 mb-2">Citation Copied!</h4>
              <p className="text-xs text-green-800 font-mono break-words leading-relaxed">
                {generateCitation()}
              </p>
            </section>
          )}

          {/* Metadata Footer */}
          <section className="border-t border-academic-border pt-4 text-xs text-academic-muted space-y-1">
            <div>
              <span className="font-medium">Node ID:</span>{' '}
              <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs break-all">
                {node.id}
              </code>
            </div>
            {node.category && (
              <div>
                <span className="font-medium">Category:</span> {node.category}
              </div>
            )}
          </section>
        </div>
      </div>
    </>
  );
}
