import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import type { SourceCitation } from '../types';
import { getGraphTypeTheme } from './graphrag/graphTheme';

export interface PassageCitationEntry {
  id?: string | null;
  ref?: string | null;
  type?: string | null;
  label?: string | null;
  layer?: string | null;
  verified?: boolean;
  confidence?: number | null;
}

interface CitationRendererProps {
  content: string;
  sources?: SourceCitation[];
  /** Structured claim-ledger entries with {ref:"P3", id:"<uuid>"} so the
   *  renderer can resolve [P3] badges to passage UUIDs. Falls back to the
   *  ``sources`` heuristic if not provided. */
  passageCitations?: PassageCitationEntry[];
  onNodeClick?: (nodeId: string) => void;
  onSourceClick?: (sourceIndex: number, source?: SourceCitation) => void;
  onPassageCitationClick?: (passageId: string) => void;
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
  passageCitations = [],
  onNodeClick,
  onSourceClick,
  onPassageCitationClick,
  className = '',
  academicMode = false,
  ancientCitationsMetadata = []
}: CitationRendererProps) {
  const navigate = useNavigate();
  const [hoveredCitation, setHoveredCitation] = useState<number | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Map "P3" → passage UUID built from the structured ledger sent by the
  // backend. The ledger is the source of truth; the sources array doesn't
  // always include the passage-typed entries that [P\d] badges refer to.
  const passageRefMap = React.useMemo(() => {
    const map = new Map<string, string>();
    for (const entry of passageCitations) {
      if (!entry?.id || !entry?.ref) continue;
      // Normalize "P3" / "p3" / "3" all to "P3".
      const raw = String(entry.ref).trim();
      const norm = /^[Pp]?\d+$/.test(raw)
        ? `P${raw.replace(/^[Pp]/, '')}`
        : raw.toUpperCase();
      map.set(norm, entry.id);
    }
    return map;
  }, [passageCitations]);

  // Resolve passage ID from a [P1] citation number
  const resolvePassageId = (pNum: number): string | null => {
    // 1. Prefer the structured backend ledger.
    const fromLedger = passageRefMap.get(`P${pNum}`);
    if (fromLedger) return fromLedger;
    // 2. Legacy heuristic — only used if the backend didn't send the ledger.
    const passageSources = sources.filter(s =>
      s.nodeType === 'Passage' ||
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(s.nodeId)
    );
    const passageSource = passageSources[pNum - 1];
    return passageSource?.nodeId || null;
  };

  const findSourceByCitationNumber = (citationNumber: number): SourceCitation | undefined =>
    sources.find((source) => source.id === citationNumber);

  const findSourceIndex = (citationNumber: number): number => {
    const sourceIndex = sources.findIndex((source) => source.id === citationNumber);
    return sourceIndex >= 0 ? sourceIndex : citationNumber - 1;
  };

  type CitationToken =
    | {
        kind: 'source' | 'numeric';
        citationNumber: number;
        label: string;
        source?: SourceCitation;
        confidence?: number;
      }
    | {
        kind: 'passage';
        citationNumber: number;
        label: string;
        passageId: string | null;
      };

  const parseCitationGroup = (innerText: string): Array<string | CitationToken> | null => {
    const tokenPattern = /Source\s+\d+|P\d+|\d+/g;
    const parts: Array<string | CitationToken> = [];
    let lastIndex = 0;
    let matched = false;
    let match: RegExpExecArray | null;

    while ((match = tokenPattern.exec(innerText)) !== null) {
      const separator = innerText.slice(lastIndex, match.index);
      if (!/^[\s,;]*$/.test(separator)) {
        return null;
      }
      if (separator) {
        parts.push(separator);
      }

      const tokenText = match[0];
      matched = true;

      if (tokenText.startsWith('Source ')) {
        const citationNumber = parseInt(tokenText.slice('Source '.length), 10);
        const source = findSourceByCitationNumber(citationNumber);
        const confidence = ancientCitationsMetadata[citationNumber - 1]?.confidence;
        parts.push({
          kind: 'source',
          citationNumber,
          label: tokenText,
          source,
          confidence,
        });
      } else if (tokenText.startsWith('P')) {
        const citationNumber = parseInt(tokenText.slice(1), 10);
        parts.push({
          kind: 'passage',
          citationNumber,
          label: tokenText,
          passageId: resolvePassageId(citationNumber),
        });
      } else {
        const citationNumber = parseInt(tokenText, 10);
        const source = findSourceByCitationNumber(citationNumber);
        const confidence = ancientCitationsMetadata[citationNumber - 1]?.confidence;
        parts.push({
          kind: 'numeric',
          citationNumber,
          label: tokenText,
          source,
          confidence,
        });
      }

      lastIndex = match.index + tokenText.length;
    }

    if (!matched) {
      return null;
    }

    const trailing = innerText.slice(lastIndex);
    if (!/^[\s,;]*$/.test(trailing)) {
      return null;
    }
    if (trailing) {
      parts.push(trailing);
    }

    return parts;
  };

  // Parse content and replace citations with interactive elements
  const parseCitations = (text: string) => {
    // Match citation groups like [1], [P1], [Source 1], [Source 1, Source 2]
    const citationPattern = /\[([^[\]]+)\]/g;

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = citationPattern.exec(text)) !== null) {
      const matchIndex = match.index;
      const matchFull = match[0];
      const matchInner = match[1];

      // Add text before citation
      if (matchIndex > lastIndex) {
        parts.push(text.substring(lastIndex, matchIndex));
      }

      const citationGroup = parseCitationGroup(matchInner);
      if (!citationGroup) {
        parts.push(matchFull);
        lastIndex = matchIndex + matchFull.length;
        continue;
      }

      parts.push(
        <span
          key={`citation-group-${matchIndex}`}
          className="inline-flex flex-wrap items-center align-middle"
        >
          <span>[</span>
          {citationGroup.map((part, groupIndex) => {
            if (typeof part === 'string') {
              return (
                <span
                  key={`citation-group-text-${matchIndex}-${groupIndex}`}
                  className="whitespace-pre"
                >
                  {part}
                </span>
              );
            }

            if (part.kind === 'passage') {
              return (
                <PassageCitationLink
                  key={`pcitation-${part.citationNumber}-${matchIndex}-${groupIndex}`}
                  citationNumber={part.citationNumber}
                  label={part.label}
                  passageId={part.passageId}
                  onClick={() => {
                    if (part.passageId && onPassageCitationClick) {
                      onPassageCitationClick(part.passageId);
                    }
                  }}
                />
              );
            }

            return (
              <CitationLink
                key={`citation-${part.citationNumber}-${matchIndex}-${groupIndex}`}
                citationNumber={part.citationNumber}
                label={part.label}
                source={part.source}
                onHover={(e, num) => handleCitationHover(e, num)}
                onLeave={() => setHoveredCitation(null)}
                onClick={() => handleCitationClick(part.citationNumber, part.source)}
                confidence={part.confidence}
                academicMode={academicMode}
              />
            );
          })}
          <span>]</span>
        </span>
      );

      lastIndex = matchIndex + matchFull.length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts;
  };

  const handleCitationHover = (e: React.MouseEvent, citationNumber: number) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltipPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 5
    });
    setHoveredCitation(citationNumber);
  };

  const handleCitationClick = (citationNumber: number, source?: SourceCitation) => {
    onSourceClick?.(findSourceIndex(citationNumber), source);

    if (!source) return;

    // Guard against invalid node IDs
    const nodeId = source.nodeId;
    if (!nodeId || nodeId === 'undefined' || nodeId.startsWith('source_')) {
      return;
    }

    // Check if nodeId is a UUID (passage ID from passage_citations/text corpus)
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

// Passage Citation Link Component (for [P1], [P2] etc.)
interface PassageCitationLinkProps {
  citationNumber: number;
  label?: string;
  passageId: string | null;
  onClick: () => void;
}

function PassageCitationLink({ citationNumber, label, passageId, onClick }: PassageCitationLinkProps) {
  const theme = getGraphTypeTheme('passage');
  return (
    <button
      type="button"
      className={`inline-flex items-center gap-0.5 align-middle ${passageId ? '' : 'cursor-default opacity-50'}`}
      onClick={passageId ? onClick : undefined}
      title={passageId ? 'Click to read passage in context' : 'Passage not available'}
      aria-label={label ?? `P${citationNumber}`}
      disabled={!passageId}
    >
      <span
        className="inline-flex min-h-5 items-center justify-center rounded-md px-1.5 py-0.5 text-[11px] font-semibold leading-none select-none transition-all duration-150 hover:brightness-90 hover:scale-110"
        style={{
          backgroundColor: theme.tint,
          color: theme.text,
          border: `1px solid ${theme.border}`,
          boxShadow: `0 1px 2px 0 ${theme.glow}`,
        }}
      >
        <svg className="mr-0.5 h-3 w-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        {label ?? `P${citationNumber}`}
      </span>
    </button>
  );
}

// Citation Link Component
interface CitationLinkProps {
  citationNumber: number;
  label?: string;
  source?: SourceCitation;
  onHover: (e: React.MouseEvent, num: number) => void;
  onLeave: () => void;
  onClick: () => void;
  confidence?: number;
  academicMode?: boolean;
}

function CitationLink({
  citationNumber,
  label,
  source,
  onHover,
  onLeave,
  onClick,
  confidence,
  academicMode,
}: CitationLinkProps) {
  const theme = getGraphTypeTheme(source?.nodeType);

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
    <button
      type="button"
      className={`inline-flex items-center gap-0.5 align-middle ${source ? 'cursor-pointer' : 'cursor-default opacity-50'}`}
      onMouseEnter={(e) => onHover(e, citationNumber)}
      onMouseLeave={onLeave}
      onClick={onClick}
      aria-label={source ? `${label ?? citationNumber}: ${source.nodeLabel}` : label ?? `${citationNumber}`}
      disabled={!source}
    >
      <span
        className="inline-flex min-h-5 items-center justify-center rounded-md px-1.5 py-0.5 text-[11px] font-semibold leading-none select-none transition-all duration-150 hover:brightness-90 hover:scale-110"
        style={{
          backgroundColor: theme.tint,
          color: theme.text,
          border: `1px solid ${theme.border}`,
          boxShadow: `0 1px 2px 0 ${theme.glow}`,
        }}
      >
        {label ?? citationNumber}
      </span>
      {academicMode && confidence !== undefined && (
        <span
          className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-semibold border ${getConfidenceBadgeColor(confidence)}`}
          title={`Confidence: ${(confidence * 100).toFixed(0)}%`}
        >
          {getConfidenceLabel(confidence)}
        </span>
      )}
    </button>
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

    const theme = getGraphTypeTheme(citation.nodeType);

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
        <div className="flex rounded-lg shadow-xl mb-2 max-w-xs overflow-hidden border border-stone-200">
          {/* Type-colored accent strip */}
          <div className="w-1 flex-shrink-0" style={{ backgroundColor: theme.color }} />
          <div className="bg-stone-50 text-stone-800 text-xs px-3 py-2.5 flex-1">
            <div className="flex items-center gap-1.5 mb-1">
              <span
                className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold"
                style={{
                  backgroundColor: theme.tint,
                  color: theme.text,
                  border: `1px solid ${theme.border}`,
                }}
              >
                {theme.label}
              </span>
              <span className="font-semibold text-stone-900 truncate">
                {citation.nodeLabel}
              </span>
            </div>
            <div className="flex items-center gap-2 text-stone-500">
              {citation.metadata?.author && (
                <span>{citation.metadata.author}</span>
              )}
              {citation.metadata?.period && (
                <span>{citation.metadata.period}</span>
              )}
              {citation.metadata?.confidence && (
                <span>{(citation.metadata.confidence * 100).toFixed(0)}%</span>
              )}
            </div>
            <div className="text-[10px] text-stone-400 mt-1">Click to view</div>
          </div>
        </div>
        {/* SVG caret */}
        <svg className="mx-auto -mt-2" width="12" height="6" viewBox="0 0 12 6">
          <path d="M0 0 L6 6 L12 0" fill="#FAFAF9" stroke="#D6D3D1" strokeWidth="1" />
        </svg>
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

    // Check if nodeId is a UUID (passage ID from passage_citations/text corpus)
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

  const getNodeTypeStyle = (type: string | undefined) => {
    const theme = getGraphTypeTheme(type);
    return {
      backgroundColor: theme.tint,
      color: theme.text,
      border: `1px solid ${theme.border}`,
    };
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
                <span
                  className="inline-flex items-center justify-center w-6 h-6 text-xs font-bold rounded"
                  style={getNodeTypeStyle(source.nodeType)}
                >
                  {source.id}
                </span>
              </div>

              <div className="flex-grow min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                    style={getNodeTypeStyle(source.nodeType)}
                  >
                    {getGraphTypeTheme(source.nodeType).label}
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
