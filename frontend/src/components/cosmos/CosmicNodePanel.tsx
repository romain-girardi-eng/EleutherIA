/**
 * CosmicNodePanel - A sleek, glassmorphic node detail panel for the cosmic KG visualization
 *
 * Features:
 * - Glass morphism design with blur backdrop
 * - Smooth slide-in animation
 * - Compact but informative layout
 * - Navigation to related nodes
 * - Quick actions (copy, share, etc.)
 */
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  X,
  Link2,
  Clock,
  School,
  BookOpen,
  User,
  MessageSquareQuote,
  ChevronRight,
  Copy,
  ExternalLink,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import type { KGNode } from '../../types';

interface RelatedNode {
  id: string;
  label: string;
  type: string;
  relation: string;
  direction: 'incoming' | 'outgoing';
}

interface CosmicNodePanelProps {
  node: KGNode | null;
  onClose: () => void;
  onNavigateToNode?: (nodeId: string) => void;
  relationships?: RelatedNode[];
  className?: string;
}

// Node type icons and colors
const NODE_TYPE_CONFIG: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  person: { icon: User, color: '#60a5fa', label: 'Person' },
  work: { icon: BookOpen, color: '#fbbf24', label: 'Work' },
  concept: { icon: Sparkles, color: '#a78bfa', label: 'Concept' },
  argument: { icon: MessageSquareQuote, color: '#34d399', label: 'Argument' },
  debate: { icon: MessageSquareQuote, color: '#f472b6', label: 'Debate' },
  school: { icon: School, color: '#818cf8', label: 'School' },
  event: { icon: Clock, color: '#f87171', label: 'Event' },
  reformulation: { icon: Link2, color: '#2dd4bf', label: 'Reformulation' },
  quote: { icon: MessageSquareQuote, color: '#fb923c', label: 'Quote' },
};

const DEFAULT_CONFIG: { icon: LucideIcon; color: string; label: string } = { icon: Sparkles, color: '#94a3b8', label: 'Node' };

export function CosmicNodePanel({
  node,
  onClose,
  onNavigateToNode,
  relationships = [],
  className = '',
}: CosmicNodePanelProps) {
  const { t } = useTranslation();
  const [isVisible, setIsVisible] = useState(false);
  const [copied, setCopied] = useState(false);

  // Animate in when node changes
  useEffect(() => {
    if (node) {
      // Small delay for animation
      requestAnimationFrame(() => setIsVisible(true));
    } else {
      setIsVisible(false);
    }
  }, [node]);

  if (!node) return null;

  const type = (node.type || 'concept').toLowerCase();
  const config = NODE_TYPE_CONFIG[type] || DEFAULT_CONFIG;
  const Icon = config.icon;

  const handleCopyId = () => {
    navigator.clipboard.writeText(node.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Group relationships by direction
  const incoming = relationships.filter(r => r.direction === 'incoming');
  const outgoing = relationships.filter(r => r.direction === 'outgoing');

  return (
    <div
      className={`
        absolute top-4 right-4 bottom-4 w-96 max-w-[calc(100%-2rem)]
        bg-slate-900/80 backdrop-blur-xl border border-slate-700/50
        rounded-2xl shadow-2xl overflow-hidden
        transform transition-all duration-300 ease-out z-50
        ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-8 opacity-0'}
        ${className}
      `}
    >
      {/* Header with gradient */}
      <div
        className="relative px-5 py-4 border-b border-slate-700/50"
        style={{
          background: `linear-gradient(135deg, ${config.color}15 0%, transparent 50%)`,
        }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-white transition-colors"
          aria-label={t('graphUi.cosmicPanel.close')}
        >
          <X className="w-4 h-4" />
        </button>

        {/* Type badge */}
        <div className="flex items-center gap-2 mb-2">
          <span
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
            style={{
              backgroundColor: `${config.color}25`,
              color: config.color,
            }}
          >
            <Icon className="w-3.5 h-3.5" />
            {config.label}
          </span>
          {node.period && (
            <span className="flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-slate-800/50 text-slate-300">
              <Clock className="w-3 h-3" />
              {node.period}
            </span>
          )}
        </div>

        {/* Title */}
        <h2 className="text-xl font-semibold text-white pr-8 leading-tight">
          {node.label}
        </h2>

        {/* Greek label if present */}
        {node.greek_term && (
          <p className="text-sm text-slate-400 mt-1 font-serif italic">
            {node.greek_term}
          </p>
        )}

        {/* School */}
        {node.school && node.school !== 'Unknown' && (
          <div className="flex items-center gap-1.5 mt-2 text-sm text-slate-400">
            <School className="w-4 h-4" />
            {node.school}
          </div>
        )}
      </div>

      {/* Scrollable content */}
      <div className="overflow-y-auto max-h-[calc(100%-180px)] custom-scrollbar">
        {/* Description */}
        {node.description && (
          <div className="px-5 py-4 border-b border-slate-700/30">
            <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">
              {t('graphUi.cosmicPanel.description')}
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              {node.description}
            </p>
          </div>
        )}

        {/* Relationships */}
        {relationships.length > 0 && (
          <div className="px-5 py-4">
            <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-3">
              {t('graphUi.cosmicPanel.connections', { count: relationships.length })}
            </h3>

            {/* Outgoing */}
            {outgoing.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-slate-500 mb-2 flex items-center gap-1">
                  <ChevronRight className="w-3 h-3" /> {t('graphUi.cosmicPanel.outgoing')}
                </p>
                <div className="space-y-1.5">
                  {outgoing.slice(0, 10).map((rel, i) => (
                    <RelationshipItem
                      key={`out-${i}`}
                      relationship={rel}
                      onNavigate={onNavigateToNode}
                    />
                  ))}
                  {outgoing.length > 10 && (
                    <p className="text-xs text-slate-500 pl-3">
                      {t('graphUi.cosmicPanel.more', { count: outgoing.length - 10 })}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Incoming */}
            {incoming.length > 0 && (
              <div>
                <p className="text-xs text-slate-500 mb-2 flex items-center gap-1">
                  <ChevronRight className="w-3 h-3 rotate-180" /> {t('graphUi.cosmicPanel.incoming')}
                </p>
                <div className="space-y-1.5">
                  {incoming.slice(0, 10).map((rel, i) => (
                    <RelationshipItem
                      key={`in-${i}`}
                      relationship={rel}
                      onNavigate={onNavigateToNode}
                    />
                  ))}
                  {incoming.length > 10 && (
                    <p className="text-xs text-slate-500 pl-3">
                      {t('graphUi.cosmicPanel.more', { count: incoming.length - 10 })}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Metadata */}
        {(node.ancient_sources || node.dates) && (
          <div className="px-5 py-4 border-t border-slate-700/30">
            <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">
              {t('graphUi.cosmicPanel.metadata')}
            </h3>
            <div className="space-y-2 text-sm">
              {node.dates && (
                <div className="flex items-center gap-2 text-slate-400">
                  <Clock className="w-4 h-4 text-slate-500" />
                  <span>{t('graphUi.cosmicPanel.dates', { value: node.dates })}</span>
                </div>
              )}
              {node.ancient_sources && Array.isArray(node.ancient_sources) && node.ancient_sources.length > 0 && (
                <div className="flex items-start gap-2 text-slate-400">
                  <BookOpen className="w-4 h-4 text-slate-500 mt-0.5" />
                  <div>
                    <span className="block text-slate-500 text-xs mb-1">{t('graphUi.cosmicPanel.ancientSources')}</span>
                    {node.ancient_sources.slice(0, 3).map((source: string, i: number) => (
                      <span key={i} className="block text-xs">
                        {source}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer actions */}
      <div className="absolute bottom-0 left-0 right-0 px-5 py-3 bg-slate-900/90 border-t border-slate-700/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyId}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs transition-colors"
          >
            <Copy className="w-3.5 h-3.5" />
            {copied ? t('graphUi.cosmicPanel.copied') : t('graphUi.cosmicPanel.copyId')}
          </button>
        </div>

        <button
          onClick={() => {
            // Open in full view (could link to a dedicated node page)
            window.open(`/visualizer/${node.id}`, '_blank');
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/80 hover:bg-indigo-500 text-white text-xs transition-colors"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          {t('graphUi.cosmicPanel.fullView')}
        </button>
      </div>
    </div>
  );
}

// Relationship item component
function RelationshipItem({
  relationship,
  onNavigate,
}: {
  relationship: RelatedNode;
  onNavigate?: (nodeId: string) => void;
}) {
  const typeKey = relationship.type.toLowerCase();
  const config = NODE_TYPE_CONFIG[typeKey] || DEFAULT_CONFIG;
  const IconComponent = config.icon;

  return (
    <button
      onClick={() => onNavigate?.(relationship.id)}
      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/40 hover:bg-slate-800/70 transition-colors group text-left"
    >
      <span
        className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: `${config.color}20` }}
      >
        <IconComponent className="w-3.5 h-3.5" style={{ color: config.color }} />
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate group-hover:text-indigo-300 transition-colors">
          {relationship.label}
        </p>
        <p className="text-xs text-slate-500 truncate">
          {formatRelation(relationship.relation)}
        </p>
      </div>
      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 flex-shrink-0" />
    </button>
  );
}

// Format relation name for display
function formatRelation(relation: string): string {
  return relation
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .toLowerCase()
    .replace(/^\s/, '');
}

export default CosmicNodePanel;
