import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { CitationPreview } from '../../../components/ui/citation-preview';
import { ThinkingProcessCompact } from '../../../components/graphrag/ThinkingProcessPanel';
import { ArgumentMapper } from '../../../components/ArgumentMapper';
import { ConceptEvolutionTimeline } from '../../../components/ConceptEvolutionTimeline';
import { CitationGenerator } from '../../../components/CitationGenerator';
import { AnswerQualityMetrics } from '../../../components/AnswerQualityMetrics';
import { WorkTextLink } from '../../../components/WorkTextLink';
import { CitationRenderer, SourcesPanel } from '../../../components/CitationRenderer';
import type { GraphRAGChatMessage } from '../../../types';

interface MessageBubbleProps {
  message: GraphRAGChatMessage;
  onNodeClick: (nodeId: string) => void;
}

export function MessageBubble({ message, onNodeClick }: MessageBubbleProps) {
  const [showCitations, setShowCitations] = useState(false);
  const [showAllAncient, setShowAllAncient] = useState(false);
  const [showAllModern, setShowAllModern] = useState(false);
  const [showReasoningPath, setShowReasoningPath] = useState(false);
  const [showQualityMetrics, setShowQualityMetrics] = useState(false);
  const [showCitationGenerator, setShowCitationGenerator] = useState(false);
  const [showArgumentMap, setShowArgumentMap] = useState(false);
  const [showConceptEvolution, setShowConceptEvolution] = useState(false);

  return (
    <div className={`${message.role === 'user' ? 'ml-auto max-w-[85%] lg:max-w-2xl' : 'mr-auto max-w-[95%] lg:max-w-full'} animate-in fade-in-0 slide-in-from-bottom-2 duration-500`}>
      <div
        className={`rounded-xl p-4 sm:p-5 lg:p-6 shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 ${
          message.role === 'user'
            ? 'bg-gradient-to-br from-gray-900/95 to-gray-800/95 text-white backdrop-blur-xl'
            : 'bg-white/80 backdrop-blur-xl border border-gray-200/50'
        }`}
      >
        {message.role === 'user' ? (
          <p className="text-base sm:text-lg break-words leading-relaxed">{message.content}</p>
        ) : (
          <div className="space-y-3">
            {/* Service indicator badge */}
            {message.graphrag_response?.service && (
              <ServiceBadge message={message} />
            )}

            {/* Answer content */}
            {message.graphrag_response?.sources ? (
              <div className="markdown-content prose prose-sm max-w-none overflow-x-auto">
                <CitationRenderer
                  content={message.content}
                  sources={message.graphrag_response.sources}
                  onNodeClick={onNodeClick}
                />
              </div>
            ) : (
              <div className="markdown-content prose prose-sm max-w-none overflow-x-auto">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            )}

            {/* Sources Panel */}
            {message.graphrag_response?.sources && message.graphrag_response.sources.length > 0 && (
              <SourcesPanel
                sources={message.graphrag_response.sources}
                evidenceMap={message.graphrag_response.evidenceMap}
                onNodeClick={onNodeClick}
              />
            )}

            {/* Thinking Process */}
            {message.thinking_process && (
              <ThinkingProcessCompact thinking={message.thinking_process} />
            )}

            {/* Reasoning Path */}
            {message.reasoning_path && (
              <ReasoningPathSection
                reasoningPath={message.reasoning_path}
                showReasoningPath={showReasoningPath}
                setShowReasoningPath={setShowReasoningPath}
                onNodeClick={onNodeClick}
              />
            )}

            {/* Citations */}
            {message.citations && (
              <CitationsSection
                citations={message.citations}
                citationTexts={message.citationTexts}
                showCitations={showCitations}
                setShowCitations={setShowCitations}
                showAllAncient={showAllAncient}
                setShowAllAncient={setShowAllAncient}
                showAllModern={showAllModern}
                setShowAllModern={setShowAllModern}
              />
            )}

            {/* Advanced Visualizations */}
            {message.graphrag_response && (
              <AdvancedVisualizationsSection
                message={message}
                showQualityMetrics={showQualityMetrics}
                setShowQualityMetrics={setShowQualityMetrics}
                showCitationGenerator={showCitationGenerator}
                setShowCitationGenerator={setShowCitationGenerator}
                showArgumentMap={showArgumentMap}
                setShowArgumentMap={setShowArgumentMap}
                showConceptEvolution={showConceptEvolution}
                setShowConceptEvolution={setShowConceptEvolution}
              />
            )}
          </div>
        )}

        <div className="text-xs mt-2 opacity-70">
          {typeof message.timestamp === 'string'
            ? new Date(message.timestamp).toLocaleTimeString()
            : message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

// Sub-components

function ServiceBadge({ message }: { message: GraphRAGChatMessage }) {
  return (
    <div className="flex items-center gap-2 mb-2">
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
        message.graphrag_response?.service?.includes('HiRAG')
          ? 'bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-800 border border-purple-200'
          : 'bg-gray-100 text-gray-700 border border-gray-200'
      }`}>
        <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        {message.graphrag_response?.service}
      </span>
      {message.graphrag_response?.hierarchy_stats && (
        <span className="text-xs text-gray-500">
          L0:{message.graphrag_response.hierarchy_stats.level_0_used} | L1:{message.graphrag_response.hierarchy_stats.level_1_used} | L2:{message.graphrag_response.hierarchy_stats.level_2_used}
        </span>
      )}
    </div>
  );
}

interface ReasoningPathSectionProps {
  reasoningPath: GraphRAGChatMessage['reasoning_path'];
  showReasoningPath: boolean;
  setShowReasoningPath: (show: boolean) => void;
  onNodeClick: (nodeId: string) => void;
}

function ReasoningPathSection({ reasoningPath, showReasoningPath, setShowReasoningPath, onNodeClick }: ReasoningPathSectionProps) {
  if (!reasoningPath) return null;

  return (
    <div className="border-t border-academic-border pt-3">
      <button
        onClick={() => setShowReasoningPath(!showReasoningPath)}
        className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
      >
        {showReasoningPath ? '▼' : '▶'} View Knowledge Graph Path ({reasoningPath.total_nodes} nodes)
      </button>

      {showReasoningPath && (
        <div className="mt-3 space-y-3 text-xs sm:text-sm">
          {/* Starting Nodes */}
          {reasoningPath.starting_nodes.length > 0 && (
            <NodeList
              title="Starting Points"
              nodes={reasoningPath.starting_nodes}
              variant="primary"
              onNodeClick={onNodeClick}
            />
          )}

          {/* Expanded Nodes */}
          {reasoningPath.expanded_nodes.length > 0 && (
            <NodeList
              title="Related Nodes"
              nodes={reasoningPath.expanded_nodes}
              variant="secondary"
              onNodeClick={onNodeClick}
              maxHeight="max-h-60"
            />
          )}
        </div>
      )}
    </div>
  );
}

interface NodeListProps {
  title: string;
  nodes: Array<{ id: string; label: string; type: string; reason?: string }>;
  variant: 'primary' | 'secondary';
  onNodeClick: (nodeId: string) => void;
  maxHeight?: string;
}

function NodeList({ title, nodes, variant, onNodeClick, maxHeight }: NodeListProps) {
  const isPrimary = variant === 'primary';
  const bgClass = isPrimary ? 'bg-blue-50 hover:bg-blue-100 border-blue-200' : 'bg-gray-50 hover:bg-gray-100 border-gray-200';
  const badgeClass = isPrimary ? 'bg-blue-200 text-blue-800' : 'bg-gray-200 text-gray-800';
  const textClass = isPrimary ? 'text-blue-900' : 'text-gray-900';
  const subTextClass = isPrimary ? 'text-blue-700' : 'text-gray-700';

  return (
    <div>
      <h4 className="font-semibold mb-2">{title} ({nodes.length}):</h4>
      <div className={`space-y-2 ${maxHeight ? `${maxHeight} overflow-y-auto` : ''}`}>
        {nodes.map((node, i) => (
          <button
            key={i}
            onClick={() => onNodeClick(node.id)}
            className={`w-full text-left p-2 rounded border transition-colors ${bgClass}`}
          >
            <div className="flex items-start gap-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${badgeClass}`}>
                {node.type}
              </span>
              <div className="flex-1">
                <div className="flex items-center justify-between gap-2">
                  <div className={`font-semibold ${textClass}`}>{node.label}</div>
                  <WorkTextLink
                    nodeId={node.id}
                    nodeType={node.type}
                    nodeLabel={node.label}
                    compact={true}
                  />
                </div>
                {node.reason && (
                  <div className={`text-xs mt-0.5 ${subTextClass}`}>{node.reason}</div>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

interface CitationsSectionProps {
  citations: NonNullable<GraphRAGChatMessage['citations']>;
  citationTexts?: GraphRAGChatMessage['citationTexts'];
  showCitations: boolean;
  setShowCitations: (show: boolean) => void;
  showAllAncient: boolean;
  setShowAllAncient: (show: boolean) => void;
  showAllModern: boolean;
  setShowAllModern: (show: boolean) => void;
}

function CitationsSection({
  citations,
  citationTexts,
  showCitations,
  setShowCitations,
  showAllAncient,
  setShowAllAncient,
  showAllModern,
  setShowAllModern,
}: CitationsSectionProps) {
  const totalCount = citations.ancient_sources.length + citations.modern_scholarship.length;

  return (
    <div className="border-t border-academic-border pt-3 mt-3">
      <button
        onClick={() => setShowCitations(!showCitations)}
        className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700"
      >
        {showCitations ? '▼' : '▶'} View Citations ({totalCount})
      </button>

      {showCitations && (
        <div className="mt-3 space-y-3 text-xs sm:text-sm">
          {citations.ancient_sources.length > 0 && (
            <CitationList
              title="Ancient Sources"
              sources={citations.ancient_sources}
              type="ancient"
              citationTexts={citationTexts}
              showAll={showAllAncient}
              setShowAll={setShowAllAncient}
              initialLimit={5}
            />
          )}

          {citations.modern_scholarship.length > 0 && (
            <CitationList
              title="Modern Scholarship"
              sources={citations.modern_scholarship}
              type="modern"
              showAll={showAllModern}
              setShowAll={setShowAllModern}
              initialLimit={3}
            />
          )}
        </div>
      )}
    </div>
  );
}

interface CitationListProps {
  title: string;
  sources: string[];
  type: 'ancient' | 'modern';
  citationTexts?: GraphRAGChatMessage['citationTexts'];
  showAll: boolean;
  setShowAll: (show: boolean) => void;
  initialLimit: number;
}

function CitationList({ title, sources, type, citationTexts, showAll, setShowAll, initialLimit }: CitationListProps) {
  const displayedSources = showAll ? sources : sources.slice(0, initialLimit);

  return (
    <div>
      <h4 className="font-semibold mb-2">{title} ({sources.length}):</h4>
      <ul className="list-disc list-inside space-y-1.5 text-academic-muted pl-2">
        {displayedSources.map((source, i) => (
          <li key={i} className="citation break-words">
            <CitationPreview
              citation={source}
              type={type}
              sourceText={citationTexts?.[source]}
            >
              {source}
            </CitationPreview>
          </li>
        ))}
      </ul>
      {sources.length > initialLimit && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-2 text-xs text-primary-600 hover:text-primary-700 font-medium"
        >
          {showAll ? '▲ Show less' : `▼ Show all ${sources.length} sources`}
        </button>
      )}
    </div>
  );
}

interface AdvancedVisualizationsSectionProps {
  message: GraphRAGChatMessage;
  showQualityMetrics: boolean;
  setShowQualityMetrics: (show: boolean) => void;
  showCitationGenerator: boolean;
  setShowCitationGenerator: (show: boolean) => void;
  showArgumentMap: boolean;
  setShowArgumentMap: (show: boolean) => void;
  showConceptEvolution: boolean;
  setShowConceptEvolution: (show: boolean) => void;
}

function AdvancedVisualizationsSection({
  message,
  showQualityMetrics,
  setShowQualityMetrics,
  showCitationGenerator,
  setShowCitationGenerator,
  showArgumentMap,
  setShowArgumentMap,
  showConceptEvolution,
  setShowConceptEvolution,
}: AdvancedVisualizationsSectionProps) {
  const response = message.graphrag_response;
  if (!response) return null;

  return (
    <div className="space-y-4 mt-6">
      {/* Quality Metrics */}
      {response.quality_metrics && (
        <CollapsibleSection
          title="Answer Quality Metrics"
          subtitle={`Confidence: ${response.quality_metrics.overallQuality}%`}
          isOpen={showQualityMetrics}
          onToggle={() => setShowQualityMetrics(!showQualityMetrics)}
        >
          <AnswerQualityMetrics metrics={response.quality_metrics} />
        </CollapsibleSection>
      )}

      {/* Citation Generator */}
      {message.citations && (
        <CollapsibleSection
          title="Export Citations (APA, MLA, Chicago, BibTeX)"
          isOpen={showCitationGenerator}
          onToggle={() => setShowCitationGenerator(!showCitationGenerator)}
        >
          <CitationGenerator
            citations={[
              ...message.citations.ancient_sources.map((source, i) => ({
                id: `ancient-${i}`,
                text: source,
                source: 'Ancient Source',
              })),
              ...message.citations.modern_scholarship.map((source, i) => ({
                id: `modern-${i}`,
                text: source,
                source: 'Modern Scholarship',
              })),
            ]}
          />
        </CollapsibleSection>
      )}

      {/* Argument Mapper */}
      {response.argument_mapping && (
        <CollapsibleSection
          title="Argument Structure Map"
          isOpen={showArgumentMap}
          onToggle={() => setShowArgumentMap(!showArgumentMap)}
        >
          <ArgumentMapper argument={response.argument_mapping} />
        </CollapsibleSection>
      )}

      {/* Concept Evolution */}
      {response.concept_evolution && (
        <CollapsibleSection
          title="Concept Evolution Timeline"
          isOpen={showConceptEvolution}
          onToggle={() => setShowConceptEvolution(!showConceptEvolution)}
        >
          <ConceptEvolutionTimeline evolution={response.concept_evolution} />
        </CollapsibleSection>
      )}
    </div>
  );
}

interface CollapsibleSectionProps {
  title: string;
  subtitle?: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function CollapsibleSection({ title, subtitle, isOpen, onToggle, children }: CollapsibleSectionProps) {
  return (
    <div className="border-t border-academic-border pt-4">
      <button
        onClick={onToggle}
        className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-2"
      >
        {isOpen ? '▼' : '▶'} {title}
        {subtitle && <span className="text-xs text-gray-500">({subtitle})</span>}
      </button>
      {isOpen && <div className="mt-4">{children}</div>}
    </div>
  );
}
