import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import type { SourceCitation } from '../types';

interface CitationRendererProps {
  content: string;
  sources?: SourceCitation[];
  onNodeClick?: (nodeId: string) => void;
  className?: string;
  academicMode?: boolean; // Show enhanced confidence badges
  ancientCitationsMetadata?: Array<{
    citation_text: string;
    confidence: number;
    cts_urn?: string;
  }>;
}

export function CitationRenderer({
  content,
  sources = [],
  onNodeClick,
  className = '',
  academicMode = false,
  ancientCitationsMetadata = []
}: CitationRendererProps) {
  const navigate = useNavigate();
  const [hoveredCitation, setHoveredCitation] = useState<number | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Parse content and replace citations with interactive elements
  const parseCitations = (text: string) => {
    // Regular expression to match [1], [2], [3] etc.
    const citationPattern = /\[(\d+)\]/g;

    const parts: (string | React.ReactElement)[] = [];
    let lastIndex = 0;
    let match;

    while ((match = citationPattern.exec(text)) !== null) {
      // Add text before citation
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const citationNumber = parseInt(match[1]);
      const source = sources.find(s => s.id === citationNumber);

      // Find confidence score if in academic mode
      const metadata = ancientCitationsMetadata[citationNumber - 1];
      const confidence = metadata?.confidence;

      // Create clickable citation element
      parts.push(
        <CitationLink
          key={`citation-${citationNumber}-${match.index}`}
          citationNumber={citationNumber}
          source={source}
          onHover={(e, num) => handleCitationHover(e, num)}
          onLeave={() => setHoveredCitation(null)}
          onClick={() => handleCitationClick(source)}
          confidence={confidence}
          academicMode={academicMode}
        />
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts;
  };

  const handleCitationHover = (e: React.MouseEvent, citationNumber: number) => {
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    setTooltipPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 5
    });
    setHoveredCitation(citationNumber);
  };

  const handleCitationClick = (source?: SourceCitation) => {
    if (!source) return;

    // Guard against invalid node IDs
    const nodeId = source.nodeId;
    if (!nodeId || nodeId === 'undefined' || nodeId.startsWith('source_')) {
      console.warn('Invalid node ID in citation:', nodeId);
      return;
    }

    // Check if nodeId is a UUID (passage ID from text_embeddings)
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (uuidPattern.test(nodeId) || nodeId.startsWith('passage_')) {
      // This is a passage reference - check if we have workId in metadata to navigate
      const workId = (source.metadata as { workId?: string })?.workId;
      if (workId) {
        navigate(`/texts/${workId}`);
      } else {
        console.info('Citation is a passage reference without workId:', nodeId);
      }
      return;
    }

    if (onNodeClick) {
      onNodeClick(nodeId);
    } else {
      // Navigate to node detail page
      navigate(`/node/${nodeId}`);
    }
  };

  // Helper function to extract text from React children recursively
  const extractText = (children: React.ReactNode): string => {
    if (children === null || children === undefined) return '';
    if (typeof children === 'string') return children;
    if (typeof children === 'number') return String(children);
    if (Array.isArray(children)) {
      return children.map(extractText).join('');
    }
    if (React.isValidElement(children)) {
      // Extract text from element's children prop
      const props = children.props as { children?: React.ReactNode };
      return extractText(props.children);
    }
    return '';
  };

  // Process content based on whether it's markdown or plain text
  const renderContent = () => {
    if (content.includes('#') || content.includes('**') || content.includes('*')) {
      // It's markdown - use ReactMarkdown with custom renderer
      return (
        <ReactMarkdown
          components={{
            p: ({ children }) => <p>{parseCitations(extractText(children))}</p>,
            li: ({ children }) => <li>{parseCitations(extractText(children))}</li>,
            td: ({ children }) => <td>{parseCitations(extractText(children))}</td>,
          }}
        >
          {content}
        </ReactMarkdown>
      );
    } else {
      // Plain text - just parse citations
      return <div className={className}>{parseCitations(content)}</div>;
    }
  };

  return (
    <>
      {renderContent()}

      {/* Citation Tooltip */}
      {hoveredCitation !== null && (
        <CitationTooltip
          ref={tooltipRef}
          citation={sources.find(s => s.id === hoveredCitation)}
          position={tooltipPosition}
        />
      )}
    </>
  );
}

// Citation Link Component
interface CitationLinkProps {
  citationNumber: number;
  source?: SourceCitation;
  onHover: (e: React.MouseEvent, num: number) => void;
  onLeave: () => void;
  onClick: () => void;
  confidence?: number;
  academicMode?: boolean;
}

function CitationLink({
  citationNumber,
  source,
  onHover,
  onLeave,
  onClick,
  confidence,
  academicMode
}: CitationLinkProps) {
  const getConfidenceBadgeColor = (conf: number) => {
    if (conf >= 0.9) return 'bg-green-100 text-green-800 border-green-300';
    if (conf >= 0.7) return 'bg-blue-100 text-blue-800 border-blue-300';
    if (conf >= 0.5) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  const getConfidenceLabel = (conf: number) => {
    if (conf >= 0.9) return 'Very High';
    if (conf >= 0.7) return 'High';
    if (conf >= 0.5) return 'Medium';
    return 'Low';
  };

  return (
    <span
      className="inline-flex items-center cursor-pointer group"
      onMouseEnter={(e) => onHover(e, citationNumber)}
      onMouseLeave={onLeave}
      onClick={onClick}
    >
      <span className="text-primary-600 hover:text-primary-800 font-medium transition-colors">
        [{citationNumber}]
      </span>
      {source && (
        <span className="ml-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
          <svg className="w-3 h-3 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </span>
      )}
      {academicMode && confidence !== undefined && (
        <span
          className={`ml-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-semibold border ${getConfidenceBadgeColor(confidence)}`}
          title={`Confidence: ${(confidence * 100).toFixed(0)}%`}
        >
          {getConfidenceLabel(confidence)}
        </span>
      )}
    </span>
  );
}

// Citation Tooltip Component
interface CitationTooltipProps {
  citation?: SourceCitation;
  position: { x: number; y: number };
}

const CitationTooltip = React.forwardRef<HTMLDivElement, CitationTooltipProps>(
  ({ citation, position }, ref) => {
    if (!citation) return null;

    return (
      <div
        ref={ref}
        className="fixed z-50 pointer-events-none"
        style={{
          left: position.x,
          top: position.y,
          transform: 'translate(-50%, -100%)'
        }}
      >
        <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 max-w-xs shadow-xl mb-1">
          <div className="font-semibold mb-1">
            [{citation.id}] {citation.nodeLabel}
          </div>
          <div className="text-gray-300">
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-700 text-gray-200 mr-1">
              {citation.nodeType || 'Unknown'}
            </span>
            {citation.metadata?.author && (
              <span className="text-gray-400">by {citation.metadata.author}</span>
            )}
            {citation.metadata?.period && (
              <span className="text-gray-400 ml-1">({citation.metadata.period})</span>
            )}
          </div>
          {citation.metadata?.confidence && (
            <div className="text-gray-400 mt-1">
              Confidence: {(citation.metadata.confidence * 100).toFixed(0)}%
            </div>
          )}
          <div className="text-[10px] text-gray-500 mt-1">Click to view details</div>
        </div>
        <div className="w-3 h-3 bg-gray-900 transform rotate-45 mx-auto -mt-1.5"></div>
      </div>
    );
  }
);

CitationTooltip.displayName = 'CitationTooltip';

// Sources Panel Component - displays all citations at the bottom of an answer
export function SourcesPanel({
  sources,
  evidenceMap,
  onNodeClick,
  className = ''
}: {
  sources: SourceCitation[];
  evidenceMap?: Record<string, { nodePath?: string[] }>;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [expandedSource] = useState<number | null>(null);

  const handleSourceClick = (source: SourceCitation) => {
    // Guard against invalid node IDs
    const nodeId = source.nodeId;
    if (!nodeId || nodeId === 'undefined' || nodeId.startsWith('source_')) {
      console.warn('Invalid node ID in source:', nodeId);
      return;
    }

    // Check if nodeId is a UUID (passage ID from text_embeddings)
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (uuidPattern.test(nodeId) || nodeId.startsWith('passage_')) {
      // This is a passage reference - check if we have workId in metadata to navigate
      const workId = (source.metadata as { workId?: string })?.workId;
      if (workId) {
        navigate(`/texts/${workId}`);
      } else {
        console.info('Source is a passage reference without workId:', nodeId);
      }
      return;
    }

    if (onNodeClick) {
      onNodeClick(nodeId);
    } else {
      navigate(`/node/${nodeId}`);
    }
  };

  const getNodeTypeColor = (type: string | undefined) => {
    if (!type) return 'bg-gray-100 text-gray-800 border-gray-200';
    switch (type.toLowerCase()) {
      case 'person': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'concept': return 'bg-green-100 text-green-800 border-green-200';
      case 'argument': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'work': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'quote': return 'bg-rose-100 text-rose-800 border-rose-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (!sources || sources.length === 0) return null;

  return (
    <div className={`border-t border-academic-border pt-4 mt-4 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        {t('graphrag.sources')} ({sources.length})
      </h3>

      <div className="space-y-2">
        {sources.map((source) => (
          <div
            key={source.id}
            className="group cursor-pointer"
            onClick={() => handleSourceClick(source)}
          >
            <div className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-all">
              <div className="flex-shrink-0 mt-0.5">
                <span className="inline-flex items-center justify-center w-6 h-6 text-xs font-bold bg-primary-100 text-primary-700 rounded">
                  {source.id}
                </span>
              </div>

              <div className="flex-grow min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getNodeTypeColor(source.nodeType)}`}>
                    {source.nodeType || 'Unknown'}
                  </span>
                  <span className="font-medium text-gray-900 group-hover:text-primary-700 transition-colors">
                    {source.nodeLabel}
                  </span>
                </div>

                {source.metadata && (
                  <div className="text-xs text-gray-600 flex items-center gap-3">
                    {source.metadata.author && (
                      <span>by {source.metadata.author}</span>
                    )}
                    {source.metadata.period && (
                      <span>{source.metadata.period}</span>
                    )}
                    {source.metadata.school && (
                      <span className="italic">{source.metadata.school}</span>
                    )}
                    {source.metadata.confidence && (
                      <span className="text-gray-400">
                        • {(source.metadata.confidence * 100).toFixed(0)}% confidence
                      </span>
                    )}
                  </div>
                )}

                {expandedSource === source.id && source.content && (
                  <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-700">
                    {source.content}
                  </div>
                )}
              </div>

              <div className="flex-shrink-0">
                <svg className="w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </div>
            </div>

            {evidenceMap?.[source.id.toString()]?.nodePath && (
              <div className="ml-9 mt-1 text-xs text-gray-500">
                Path: {evidenceMap[source.id.toString()].nodePath!.join(' → ')}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
